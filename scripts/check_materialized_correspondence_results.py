#!/usr/bin/env python3
"""Check schemas and evidence semantics for materialized correspondence outputs."""

from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "materialized_correspondence"

REQUIRED = {
    "materialization_targets.csv": {"case_id", "target_impl_node", "target_role", "selection_reason"},
    "anchored_cut_candidates.csv": {"case_id", "cut_id", "target_impl_node", "impl_leaf_nodes", "spec_leaf_nodes", "leaf_polarities"},
    "cut_function_extraction.csv": {"case_id", "cut_id", "extraction_status", "truth_table_hash", "failure_reason"},
    "materialized_expression_candidates.csv": {"case_id", "expression_id", "cut_id", "expression_text", "minimization_backend"},
    "materialized_wires.csv": {"case_id", "materialized_wire_name", "generation_status", "augmented_spec_path"},
    "materialized_anchor_formal_results.csv": {"case_id", "proof_status", "anchor_origin", "mapping_category", "evidence_level", "equivalence_scope", "augmentation_preserves_original_outputs"},
    "proven_materialized_anchors.csv": {"case_id", "proof_status", "materialized_spec_node", "target_impl_node", "mapping_category"},
    "materialized_anchor_usage.csv": {"case_id", "materialized_spec_node", "usable_for_boundary", "selected_by_boundary"},
    "materialized_boundary_recovery.csv": {"case_id", "baseline_success", "materialized_success", "selected_materialized_anchor_count", "newly_recovered_boundary"},
    "materialized_ablation_results.csv": {"ablation", "formal_checks", "proven_materialized_anchors", "new_boundary_recoveries"},
    "materialized_failure_analysis.csv": {"stage", "failure_reason", "count"},
}


def main() -> int:
    for name, columns in REQUIRED.items():
        path = OUT / name
        if not path.exists():
            raise SystemExit(f"missing {path}")
        rows, fieldnames = read_rows(path)
        missing = columns - set(fieldnames or [])
        if missing:
            raise SystemExit(f"{name} missing columns {sorted(missing)}")
        if name == "materialized_anchor_formal_results.csv":
            for row in rows:
                if row["proof_status"] == "proven_materialized_anchor":
                    if row["anchor_origin"] != "materialized_wire":
                        raise SystemExit("proven materialized anchor mislabeled as existing node")
                    if row["mapping_category"] != "formal_materialized_anchor":
                        raise SystemExit("proven materialized anchor has wrong category")
                    if row["evidence_level"] != "formal_exhaustive":
                        raise SystemExit("proven materialized anchor is not formal_exhaustive")
                    if row["equivalence_scope"] != "global":
                        raise SystemExit("proven materialized anchor is not global")
                    if row["augmentation_preserves_original_outputs"] != "True":
                        raise SystemExit("accepted materialized anchor changed original outputs")
                elif row["evidence_level"] == "formal_exhaustive" or row["mapping_category"] == "formal_materialized_anchor":
                    raise SystemExit("unproven materialized row labeled formal")
        if name == "proven_materialized_anchors.csv":
            for row in rows:
                if row["proof_status"] != "proven_materialized_anchor":
                    raise SystemExit("unproven row in proven_materialized_anchors.csv")
                if row["mapping_category"] != "formal_materialized_anchor":
                    raise SystemExit("wrong category in proven_materialized_anchors.csv")
    identity_path = ROOT / "results" / "boundary_recovery_semantics" / "identity_exact_match_results.csv"
    rows, _ = read_rows(identity_path)
    if len(rows) != 14 or any(row.get("top_level_classification") != "success" for row in rows):
        raise SystemExit("identity boundary regression is not perfect")
    summary = OUT / "materialized_correspondence_summary.md"
    text = summary.read_text(encoding="utf-8")
    for required in ["materialized anchor is not a pre-existing original node", "No sampled result is used as proof"]:
        if required not in text:
            raise SystemExit(f"summary missing evidence caveat: {required}")
    print("Materialized correspondence results validated")
    return 0


def read_rows(path: Path) -> tuple[list[dict[str, str]], list[str] | None]:
    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        return list(reader), reader.fieldnames


if __name__ == "__main__":
    raise SystemExit(main())
