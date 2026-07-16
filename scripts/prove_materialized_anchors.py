#!/usr/bin/env python3
"""Prove materialized-wire anchors by exhaustive global PI comparison."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from analyze_blif_matches import parse_blif  # noqa: E402
from boundary_semantics import original_path, variant_path, write_csv  # noqa: E402
from materialized_anchor_validation import proof_to_row, prove_materialized_anchor_exhaustive  # noqa: E402

OUT = ROOT / "results" / "materialized_correspondence"

FORMAL_COLUMNS = [
    "case_id",
    "benchmark",
    "optimization",
    "coi_name",
    "target_impl_node",
    "cut_id",
    "cut_size",
    "impl_leaf_nodes",
    "spec_leaf_nodes",
    "leaf_polarities",
    "leaf_mapping_categories",
    "truth_table_hash",
    "expression_id",
    "expression_text",
    "expression_cost",
    "added_gate_count",
    "materialized_spec_node",
    "proof_status",
    "sat_result",
    "proof_runtime_seconds",
    "formal_backend",
    "target_polarity",
    "counterexample_available",
    "counterexample_summary",
    "augmentation_preserves_original_outputs",
    "anchor_origin",
    "mapping_category",
    "evidence_level",
    "equivalence_scope",
    "usable_for_boundary",
    "selected_by_boundary",
    "source_fingerprints",
    "failure_reason",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--exact-input-limit", type=int, default=12)
    parser.add_argument("--max-formal-checks-per-case", type=int, default=256)
    parser.add_argument("--output-dir", type=Path, default=OUT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    cuts = {row["cut_id"]: row for row in _read_rows(args.output_dir / "anchored_cut_candidates.csv")}
    exprs = {row["expression_id"]: row for row in _read_rows(args.output_dir / "materialized_expression_candidates.csv")}
    wires = _read_rows(args.output_dir / "materialized_wires.csv")
    nets = {}
    per_case: dict[str, int] = {}
    rows = []
    for wire in wires:
        if wire["generation_status"] != "generated":
            continue
        count = per_case.get(wire["case_id"], 0)
        if count >= args.max_formal_checks_per_case:
            continue
        per_case[wire["case_id"]] = count + 1
        key = (wire["benchmark"], wire["optimization"])
        if key not in nets:
            nets[key] = (
                parse_blif(original_path(wire["benchmark"])),
                parse_blif(variant_path(wire["benchmark"], wire["optimization"])),
            )
        spec_net, impl_net = nets[key]
        augmented_path = ROOT / wire["augmented_spec_path"]
        augmented_net = parse_blif(augmented_path)
        proof = prove_materialized_anchor_exhaustive(
            spec_net,
            augmented_net,
            impl_net,
            spec_path=original_path(wire["benchmark"]),
            impl_path=variant_path(wire["benchmark"], wire["optimization"]),
            augmented_spec_path=augmented_path,
            materialized_wire_name=wire["materialized_wire_name"],
            target_impl_node=wire["target_impl_node"],
            target_polarity="positive",
            exact_input_limit=args.exact_input_limit,
        )
        cut = cuts[wire["cut_id"]]
        expr = exprs[wire["expression_id"]]
        source_fps = f"spec={proof.spec_fingerprint};impl={proof.impl_fingerprint};augmented={proof.augmented_spec_fingerprint}"
        accepted = proof.proof_status == "proven_materialized_anchor" and proof.augmentation_preserves_original_outputs
        row = {
            "case_id": wire["case_id"],
            "benchmark": wire["benchmark"],
            "optimization": wire["optimization"],
            "coi_name": wire["coi_name"],
            "target_impl_node": wire["target_impl_node"],
            "cut_id": wire["cut_id"],
            "cut_size": cut["cut_size"],
            "impl_leaf_nodes": cut["impl_leaf_nodes"],
            "spec_leaf_nodes": cut["spec_leaf_nodes"],
            "leaf_polarities": cut["leaf_polarities"],
            "leaf_mapping_categories": cut["leaf_mapping_categories"],
            "truth_table_hash": expr["truth_table_hash"],
            "expression_id": wire["expression_id"],
            "expression_text": expr["expression_text"],
            "expression_cost": expr["estimated_cost"],
            "added_gate_count": wire["added_gate_count"],
            "materialized_spec_node": wire["materialized_wire_name"],
            **proof_to_row(proof, case_id=wire["case_id"], benchmark=wire["benchmark"], optimization=wire["optimization"], coi_name=wire["coi_name"]),
            "anchor_origin": "materialized_wire",
            "mapping_category": "formal_materialized_anchor" if accepted else "unresolved",
            "evidence_level": "formal_exhaustive" if accepted else "unresolved",
            "equivalence_scope": "global" if accepted else "unresolved",
            "usable_for_boundary": False,
            "selected_by_boundary": False,
            "source_fingerprints": source_fps,
        }
        rows.append(row)
    write_csv(args.output_dir / "materialized_anchor_formal_results.csv", rows, FORMAL_COLUMNS)
    proven = [row for row in rows if row["proof_status"] == "proven_materialized_anchor" and row["mapping_category"] == "formal_materialized_anchor"]
    write_csv(args.output_dir / "proven_materialized_anchors.csv", proven, FORMAL_COLUMNS)
    print(f"Wrote materialized formal proof rows: {len(rows)}; proven: {len(proven)}")
    return 0


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


if __name__ == "__main__":
    raise SystemExit(main())
