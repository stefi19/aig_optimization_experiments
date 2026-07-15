"""Execution helpers for repaired boundary-recovery semantics."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path

from boundary_anchor_map import Anchor, AnchorMap, load_anchor_map
from boundary_graph import CircuitGraph
from boundary_recovery import compute_boundary_metrics, first_equivalent_cut_tfi, first_equivalent_cut_tfo
from coi_model import (
    BOUNDARY_MEMBERSHIP_CONVENTION,
    COI_SCHEMA_VERSION,
    CanonicalCoi,
    canonical_dict,
    extract_region_from_boundaries,
    validate_coi,
)


ROOT = Path(__file__).resolve().parent
SEMANTICS_DIR = ROOT / "results" / "boundary_recovery_semantics"
MICRO_DIR = ROOT / "benchmarks" / "boundary_recovery_micro"
MICRO_COIS = ROOT / "benchmarks" / "coi_specs" / "boundary_recovery_micro_cois.json"
CANONICAL_MANIFEST = SEMANTICS_DIR / "coi_canonical_manifest.json"
OPTIMIZATIONS = ["balance", "rewrite", "resyn2", "dc2"]


@dataclass(frozen=True)
class SemanticRecovery:
    success: bool
    ebi: tuple[str, ...]
    ebo: tuple[str, ...]
    region: tuple[str, ...]
    failure_reason: str
    ebi_exact_match: bool
    ebo_exact_match: bool
    region_exact_match: bool
    boundary_extension_ratio: float
    missing_ebi_nodes: tuple[str, ...]
    extra_ebi_nodes: tuple[str, ...]
    missing_ebo_nodes: tuple[str, ...]
    extra_ebo_nodes: tuple[str, ...]
    missing_region_nodes: tuple[str, ...]
    extra_region_nodes: tuple[str, ...]


def original_path(benchmark: str) -> Path:
    micro = MICRO_DIR / f"{benchmark}.blif"
    if micro.exists():
        return micro
    return ROOT / "variants" / f"{benchmark}_original.blif"


def variant_path(benchmark: str, optimization: str) -> Path:
    if optimization in {"identity", "original"}:
        return original_path(benchmark)
    return ROOT / "variants" / f"{benchmark}_{optimization}.blif"


def load_canonical_manifest(path: Path = CANONICAL_MANIFEST) -> list[CanonicalCoi]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    rows = raw.get("cois", raw if isinstance(raw, list) else [])
    return [
        CanonicalCoi(
            benchmark=row["benchmark"],
            optimization=row.get("optimization", "*"),
            coi_name=row["coi_name"],
            region_nodes=tuple(row["region_nodes"]),
            boundary_inputs=tuple(row["boundary_inputs"]),
            boundary_outputs=tuple(row["boundary_outputs"]),
            source=row.get("source", "automatically_derived"),
            coi_schema_version=row.get("coi_schema_version", COI_SCHEMA_VERSION),
            boundary_membership_convention=row.get("boundary_membership_convention", BOUNDARY_MEMBERSHIP_CONVENTION),
            generation_method=row.get("generation_method", "canonical_derivation"),
            original_manifest_status=row.get("original_manifest_status", ""),
            repair_notes=row.get("repair_notes", ""),
        )
        for row in rows
    ]


def write_canonical_manifest(cois: list[CanonicalCoi], path: Path = CANONICAL_MANIFEST) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"cois": [canonical_dict(coi) for coi in cois]}, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def identity_anchor_map(graph: CircuitGraph) -> AnchorMap:
    return AnchorMap(
        [
            Anchor(
                spec_node=node,
                impl_node=node,
                polarity="same",
                mapping_category="exact_signature_match",
                evidence_level="formal_exhaustive",
                proof_mode="identity",
                source_result_file="identity",
                confidence_or_status="formal_identity",
            )
            for node in sorted(graph.nodes)
        ]
    )


def load_formal_anchors(benchmark: str, optimization: str, mode: str, spec: CircuitGraph, impl: CircuitGraph) -> AnchorMap:
    if mode == "identity_exact":
        return identity_anchor_map(spec)
    return load_anchor_map(
        benchmark,
        optimization,
        mode,
        results_dir=ROOT / "results",
        spec_inputs=spec.inputs,
        impl_inputs=impl.inputs,
        spec_outputs=spec.outputs,
        impl_outputs=impl.outputs,
    )


def recover_semantic_boundary(graph: CircuitGraph, coi: CanonicalCoi, anchors: AnchorMap) -> SemanticRecovery:
    validation = validate_coi(graph, coi)
    if not validation.valid:
        return empty_recovery("invalid_coi:" + ";".join(validation.errors))
    ebi, _, ebi_fail = first_equivalent_cut_tfi(graph, list(coi.boundary_inputs), anchors)
    ebo, _, ebo_fail = first_equivalent_cut_tfo(graph, list(coi.boundary_outputs), anchors)
    if ebi_fail:
        return empty_recovery("no_ebi_frontier:" + ";".join(ebi_fail))
    if ebo_fail:
        return empty_recovery("no_ebo_frontier:" + ";".join(ebo_fail))
    extracted = extract_region_from_boundaries(graph, ebi, ebo, required_nodes=set(coi.region_nodes))
    ebi_set = set(ebi)
    ebo_set = set(ebo)
    region_set = set(extracted.region_nodes)
    expected_ebi = set(coi.boundary_inputs)
    expected_ebo = set(coi.boundary_outputs)
    expected_region = set(coi.region_nodes)
    ebi_exact = ebi_set == expected_ebi
    ebo_exact = ebo_set == expected_ebo
    region_exact = region_set == expected_region
    success = ebi_exact and ebo_exact and region_exact and not extracted.bypass_edges
    extension_den = max(1, len(expected_ebi | expected_ebo | expected_region))
    extension_num = len((ebi_set | ebo_set | region_set) - (expected_ebi | expected_ebo | expected_region))
    reasons = []
    if not ebi_exact:
        reasons.append("ebi_mismatch")
    if not ebo_exact:
        reasons.append("ebo_mismatch")
    if not region_exact:
        reasons.append("region_mismatch")
    if extracted.bypass_edges:
        reasons.append("bypass_edges")
    return SemanticRecovery(
        success=success,
        ebi=tuple(sorted(ebi_set)),
        ebo=tuple(sorted(ebo_set)),
        region=tuple(sorted(region_set)),
        failure_reason="valid" if success else ";".join(reasons),
        ebi_exact_match=ebi_exact,
        ebo_exact_match=ebo_exact,
        region_exact_match=region_exact,
        boundary_extension_ratio=extension_num / extension_den,
        missing_ebi_nodes=tuple(sorted(expected_ebi - ebi_set)),
        extra_ebi_nodes=tuple(sorted(ebi_set - expected_ebi)),
        missing_ebo_nodes=tuple(sorted(expected_ebo - ebo_set)),
        extra_ebo_nodes=tuple(sorted(ebo_set - expected_ebo)),
        missing_region_nodes=tuple(sorted(expected_region - region_set)),
        extra_region_nodes=tuple(sorted(region_set - expected_region)),
    )


def empty_recovery(reason: str) -> SemanticRecovery:
    return SemanticRecovery(
        success=False,
        ebi=tuple(),
        ebo=tuple(),
        region=tuple(),
        failure_reason=reason,
        ebi_exact_match=False,
        ebo_exact_match=False,
        region_exact_match=False,
        boundary_extension_ratio=0.0,
        missing_ebi_nodes=tuple(),
        extra_ebi_nodes=tuple(),
        missing_ebo_nodes=tuple(),
        extra_ebo_nodes=tuple(),
        missing_region_nodes=tuple(),
        extra_region_nodes=tuple(),
    )


def write_csv(path: Path, rows: list[dict[str, object]], columns: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if columns is None:
        columns = sorted({key for row in rows for key in row}) if rows else []
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({col: row.get(col, "") for col in columns})


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def join_nodes(nodes: tuple[str, ...] | list[str] | set[str]) -> str:
    return ";".join(sorted(nodes))
