#!/usr/bin/env python3
"""Validate Phase 3 semantic bus/dependency outputs."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULT = ROOT / "results" / "semantic_recovery"

EXPECTED = {
    "semantic_bus_hypotheses.csv": [
        "bus_hypothesis_id",
        "region_id",
        "inference_mode",
        "used_ground_truth_for_generation",
        "used_ground_truth_for_evaluation",
        "direction",
        "role",
        "member_nodes",
        "ordered_member_nodes",
        "width",
        "bit_order",
        "signedness_hypothesis",
        "grouping_score",
        "ordering_score",
        "role_score",
        "evidence_sources",
        "feature_values",
        "ambiguity_count",
        "ground_truth_bus_name_if_known",
        "ground_truth_match",
        "rank",
        "schema_version",
    ],
    "semantic_bus_best_hypotheses.csv": None,
    "semantic_bus_evaluation.csv": [
        "region_id",
        "case_id",
        "optimization",
        "source_type",
        "inference_mode",
        "feature_mode",
        "direction",
        "ground_truth_bus_count",
        "hypothesis_count",
        "top_1_bus_match",
        "top_3_bus_match",
        "top_5_bus_match",
        "exact_bus_partition_match",
        "exact_ordered_bus_match",
        "bus_membership_precision",
        "bus_membership_recall",
        "bit_order_accuracy",
        "reversed_order_rate",
        "control_input_accuracy",
        "data_operand_accuracy",
        "output_bus_accuracy",
        "mean_ground_truth_rank",
        "mrr",
    ],
    "semantic_input_roles.csv": [
        "region_id",
        "case_id",
        "optimization",
        "source_type",
        "node",
        "predicted_role",
        "ground_truth_role",
        "role_score",
        "correct",
        "inference_mode",
    ],
    "semantic_bit_order_evaluation.csv": [
        "region_id",
        "case_id",
        "optimization",
        "source_type",
        "direction",
        "bus_hypothesis_id",
        "ground_truth_bus_name",
        "exact_ordered_bus_match",
        "unordered_bus_membership_match",
        "reversed_order_match",
        "partial_match",
        "ordering_method",
        "ordering_score",
        "ordering_ambiguity",
    ],
    "semantic_dependency_features.csv": [
        "region_id",
        "case_id",
        "optimization",
        "source_type",
        "input_count",
        "output_count",
        "structural_coverage",
        "simulation_coverage",
        "boolean_difference_coverage",
        "formal_dependency_coverage",
        "dependency_density",
        "row_density_mean",
        "column_density_mean",
        "lower_triangularity",
        "upper_triangularity",
        "diagonal_concentration",
        "bandwidth",
        "minimum_dependency_slope",
        "maximum_dependency_slope",
        "carry_progression_score",
        "multiplier_diagonal_score",
        "operand_symmetry_score",
        "output_prefix_dependency_score",
        "selectivity_change_score",
        "single_output_control_score",
        "high_bit_priority_score",
        "locality_score",
        "regularity_score",
        "simulation_evidence_level",
        "boolean_difference_evidence_level",
        "pattern_count",
        "seed",
        "runtime_seconds",
        "schema_version",
    ],
    "semantic_dependency_by_optimization.csv": [
        "optimization",
        "eligible_rows",
        "complete_dependency_matrices",
        "mean_dependency_density",
        "mean_diagonal_concentration",
        "mean_lower_triangularity",
        "mean_bandwidth",
        "mean_runtime_seconds",
    ],
    "semantic_family_rankings.csv": [
        "region_id",
        "case_id",
        "optimization",
        "source_type",
        "candidate_family",
        "family_score",
        "feature_contributions",
        "rank",
        "ground_truth_family",
        "ground_truth_rank",
    ],
    "semantic_family_evaluation.csv": ["scope", "group", "rows", "top_1_family_accuracy", "top_3_family_accuracy", "mrr"],
    "semantic_family_confusion_matrix.csv": ["ground_truth_family", "predicted_family", "count"],
    "semantic_bus_ablation.csv": [
        "feature_mode",
        "region_rows",
        "direction_rows",
        "top_1_bus_match_rate",
        "top_3_bus_match_rate",
        "top_5_bus_match_rate",
        "mean_membership_precision",
        "mean_membership_recall",
        "mean_bit_order_accuracy",
        "mean_mrr",
        "runtime_seconds",
    ],
    "semantic_family_ablation.csv": [
        "feature_mode",
        "ranked_regions",
        "top_1_family_accuracy",
        "top_3_family_accuracy",
        "mrr",
        "runtime_seconds",
    ],
    "semantic_bus_dependency_failures.csv": ["region_id", "case_id", "optimization", "source_type", "stage", "reason"],
}
EXPECTED["semantic_bus_best_hypotheses.csv"] = EXPECTED["semantic_bus_hypotheses.csv"]


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def fail(message: str) -> int:
    print(f"ERROR: {message}", file=sys.stderr)
    return 1


def main() -> int:
    for name, fields in EXPECTED.items():
        path = RESULT / name
        if not path.exists():
            return fail(f"missing {path}")
        with path.open(newline="", encoding="utf-8") as fh:
            reader = csv.reader(fh)
            header = next(reader, [])
        if header != fields:
            return fail(f"{name} header mismatch: {header}")

    hypotheses = read_rows(RESULT / "semantic_bus_hypotheses.csv")
    if not hypotheses:
        return fail("semantic_bus_hypotheses.csv has no rows")
    bad_generation = [
        row for row in hypotheses
        if row["inference_mode"] == "inferred_bus_mode" and row["used_ground_truth_for_generation"] != "false"
    ]
    if bad_generation:
        return fail("inferred bus rows use ground truth for generation")

    features = read_rows(RESULT / "semantic_dependency_features.csv")
    if not features:
        return fail("semantic_dependency_features.csv has no rows")
    if any(row["simulation_evidence_level"] == "formal_exhaustive" for row in features):
        return fail("sampled simulation dependency was labeled formal")

    matrices_path = RESULT / "semantic_dependency_matrices.json"
    if not matrices_path.exists():
        return fail(f"missing {matrices_path}")
    matrices = json.loads(matrices_path.read_text(encoding="utf-8"))
    if len(matrices) != len(features):
        return fail("dependency matrix count does not match feature rows")

    summary = RESULT / "semantic_bus_dependency_summary.md"
    if not summary.exists():
        return fail("missing semantic_bus_dependency_summary.md")
    text = summary.read_text(encoding="utf-8").lower()
    if "does not synthesize expressions" not in text or "not formal proof" not in text:
        return fail("summary is missing non-recovery or sampled-evidence caveats")
    print("Semantic bus/dependency results validated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
