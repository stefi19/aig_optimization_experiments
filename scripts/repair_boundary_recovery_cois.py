#!/usr/bin/env python3
"""Repair and normalize boundary-recovery COIs under canonical semantics."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from boundary_graph import CircuitGraph  # noqa: E402
from boundary_recovery import load_coi_specs  # noqa: E402
from boundary_semantics import (  # noqa: E402
    CANONICAL_MANIFEST,
    MICRO_COIS,
    SEMANTICS_DIR,
    identity_anchor_map,
    original_path,
    recover_semantic_boundary,
    write_canonical_manifest,
    write_csv,
)
from coi_model import CanonicalCoi, canonical_dict, normalize_coi, validate_coi  # noqa: E402

SEED_COIS = ROOT / "benchmarks" / "coi_specs" / "boundary_recovery_seed_cois.json"
AUDIT_CSV = SEMANTICS_DIR / "coi_repair_audit.csv"
VALIDATION_CSV = SEMANTICS_DIR / "coi_validation_results.csv"

AUDIT_COLUMNS = [
    "benchmark",
    "coi_name",
    "original_valid",
    "repaired",
    "final_valid",
    "repair_action",
    "original_bi_count",
    "derived_bi_count",
    "original_bo_count",
    "derived_bo_count",
    "region_node_count",
    "reason",
]


def load_micro_cois() -> list[CanonicalCoi]:
    if not MICRO_COIS.exists():
        return []
    raw = json.loads(MICRO_COIS.read_text(encoding="utf-8"))
    cois = []
    for row in raw.get("cois", []):
        cois.append(
            CanonicalCoi(
                benchmark=row["benchmark"],
                optimization=row.get("optimization", "*"),
                coi_name=row["coi_name"],
                region_nodes=tuple(row["region_nodes"]),
                boundary_inputs=tuple(row["boundary_inputs"]),
                boundary_outputs=tuple(row["boundary_outputs"]),
                source=row.get("source", "automatically_derived"),
                generation_method=row.get("generation_method", "micro_benchmark"),
                original_manifest_status=row.get("original_manifest_status", "new_micro_case"),
                repair_notes=row.get("repair_notes", ""),
            )
        )
    return cois


def main() -> int:
    SEMANTICS_DIR.mkdir(parents=True, exist_ok=True)
    final_cois: list[CanonicalCoi] = []
    audit_rows: list[dict[str, object]] = []
    validation_rows: list[dict[str, object]] = []

    for coi in load_micro_cois():
        path = original_path(coi.benchmark)
        graph = CircuitGraph.from_blif(path)
        validation = validate_coi(graph, coi)
        recovery = recover_semantic_boundary(graph, coi, identity_anchor_map(graph))
        include = validation.valid and recovery.success
        if include:
            final_cois.append(coi)
        audit_rows.append(
            audit_row(
                coi.benchmark,
                coi.coi_name,
                validation.valid,
                False,
                include,
                "added_micro" if include else "excluded_micro",
                len(coi.boundary_inputs),
                len(validation.derived_bi),
                len(coi.boundary_outputs),
                len(validation.derived_bo),
                len(coi.region_nodes),
                "valid" if include else recovery.failure_reason,
            )
        )
        validation_rows.append(validation_row(coi, validation, include))

    for old in load_coi_specs(SEED_COIS):
        path = original_path(old.benchmark)
        if not path.exists():
            audit_rows.append(
                audit_row(
                    old.benchmark,
                    old.coi_name,
                    False,
                    False,
                    False,
                    "excluded_infrastructure_skip",
                    len(old.boundary_inputs),
                    0,
                    len(old.boundary_outputs),
                    0,
                    len(old.coi_internal_nodes),
                    "missing_spec_circuit",
                )
            )
            continue
        graph = CircuitGraph.from_blif(path)
        original = CanonicalCoi(
            benchmark=old.benchmark,
            optimization="*",
            coi_name=old.coi_name,
            region_nodes=tuple(sorted(old.coi_internal_nodes)),
            boundary_inputs=tuple(sorted(old.boundary_inputs)),
            boundary_outputs=tuple(sorted(old.boundary_outputs)),
            source=old.source,
            generation_method="legacy_manifest",
        )
        original_validation = validate_coi(graph, original)
        if any(not graph.exists(node) for node in old.coi_internal_nodes):
            reason = "missing_node"
            repaired = False
            final_valid = False
            action = "excluded_invalid_nodes"
            derived_bi: tuple[str, ...] = tuple()
            derived_bo: tuple[str, ...] = tuple()
        else:
            repaired_coi = normalize_coi(
                graph,
                benchmark=old.benchmark,
                optimization="*",
                coi_name=old.coi_name,
                region_nodes=old.coi_internal_nodes,
                source=old.source,
                generation_method="canonical_repair",
                original_manifest_status="valid" if original_validation.valid else "invalid_manual_boundary",
                repair_notes="BI/BO derived from canonical graph semantics.",
            )
            repaired_validation = validate_coi(graph, repaired_coi)
            recovery = recover_semantic_boundary(graph, repaired_coi, identity_anchor_map(graph))
            final_valid = repaired_validation.valid and recovery.success
            repaired = (set(repaired_coi.boundary_inputs) != set(old.boundary_inputs)) or (set(repaired_coi.boundary_outputs) != set(old.boundary_outputs))
            if final_valid:
                final_cois.append(repaired_coi)
                action = "repaired" if repaired else "kept"
                reason = "valid"
            else:
                action = "excluded_identity_not_exact"
                reason = recovery.failure_reason or ";".join(repaired_validation.errors)
            derived_bi = repaired_validation.derived_bi
            derived_bo = repaired_validation.derived_bo
            validation_rows.append(validation_row(repaired_coi, repaired_validation, final_valid))

        audit_rows.append(
            audit_row(
                old.benchmark,
                old.coi_name,
                original_validation.valid,
                repaired,
                final_valid,
                action,
                len(old.boundary_inputs),
                len(derived_bi),
                len(old.boundary_outputs),
                len(derived_bo),
                len(old.coi_internal_nodes),
                reason,
            )
        )

    write_canonical_manifest(final_cois, CANONICAL_MANIFEST)
    write_csv(AUDIT_CSV, audit_rows, AUDIT_COLUMNS)
    write_csv(VALIDATION_CSV, validation_rows)
    print(f"Wrote canonical manifest with {len(final_cois)} COIs")
    return 0


def audit_row(
    benchmark: str,
    coi_name: str,
    original_valid: bool,
    repaired: bool,
    final_valid: bool,
    repair_action: str,
    original_bi_count: int,
    derived_bi_count: int,
    original_bo_count: int,
    derived_bo_count: int,
    region_node_count: int,
    reason: str,
) -> dict[str, object]:
    return {
        "benchmark": benchmark,
        "coi_name": coi_name,
        "original_valid": original_valid,
        "repaired": repaired,
        "final_valid": final_valid,
        "repair_action": repair_action,
        "original_bi_count": original_bi_count,
        "derived_bi_count": derived_bi_count,
        "original_bo_count": original_bo_count,
        "derived_bo_count": derived_bo_count,
        "region_node_count": region_node_count,
        "reason": reason,
    }


def validation_row(coi: CanonicalCoi, validation, included: bool) -> dict[str, object]:
    return {
        "benchmark": coi.benchmark,
        "coi_name": coi.coi_name,
        "source": coi.source,
        "coi_schema_version": coi.coi_schema_version,
        "valid": validation.valid,
        "included_in_canonical_manifest": included,
        "errors": ";".join(validation.errors),
        "warnings": ";".join(validation.warnings),
        "derived_bi": ";".join(validation.derived_bi),
        "derived_bo": ";".join(validation.derived_bo),
        "whole_design_region": validation.whole_design_region,
    }


if __name__ == "__main__":
    raise SystemExit(main())
