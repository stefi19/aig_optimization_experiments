#!/usr/bin/env python3
"""Validate Phase 4 direct semantic recovery outputs."""

from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULT = ROOT / "results" / "semantic_recovery"

EXPECTED = {
    "semantic_direct_candidates.csv": ["candidate_id", "region_id", "case_id", "family", "operator", "optimization", "source_type", "family_order_mode", "grammar_family", "candidate_rank", "ground_truth_family_rank", "first_attempted_family", "families_attempted", "input_bus_count", "output_width", "expression_id", "expression_operator", "operands", "input_types", "output_type", "width", "signedness", "extension_mode", "truncation_mode", "slice_range", "constant_value", "expression_depth", "canonical_form", "rtl_text", "rtl_cost", "expression_json", "schema_version"],
    "semantic_candidate_simulation.csv": ["candidate_id", "region_id", "simulation_filter_mode", "sample_count", "sample_matches", "sample_mismatches", "sample_match_rate", "first_mismatch_pattern", "mismatch_output_bits", "simulation_runtime", "simulation_status", "simulation_evidence_level", "schema_version"],
    "semantic_candidate_rankings.csv": ["candidate_id", "region_id", "candidate_ranking_mode", "rank_after_simulation", "ranking_score", "simulation_status", "sample_match_rate", "grammar_family", "expression_depth", "rtl_cost"],
    "semantic_formal_results.csv": ["candidate_id", "region_id", "formal_status", "proof_scope", "formal_evidence_level", "formal_patterns", "counterexample_available", "counterexample_assignment", "counterexample_output_difference", "counterexample_source", "formal_runtime", "formal_skip_reason", "schema_version"],
    "semantic_verified_candidates.csv": ["candidate_id", "region_id", "case_id", "family", "operator", "optimization", "source_type", "grammar_family", "classification", "proof_scope", "canonical_form", "rtl_text", "candidate_rtl_cost", "input_gate_count", "reduction_rate", "reduction_rate_ge_70", "formal_runtime"],
    "semantic_best_verified_expressions.csv": ["candidate_id", "region_id", "case_id", "family", "operator", "optimization", "source_type", "grammar_family", "classification", "proof_scope", "canonical_form", "rtl_text", "candidate_rtl_cost", "input_gate_count", "reduction_rate", "reduction_rate_ge_70", "formal_runtime", "selection_rank"],
    "semantic_ground_truth_recovery.csv": ["scope", "group", "eligible_regions", "regions_with_direct_candidates", "generated_candidates", "canonical_candidates", "simulation_checked", "simulation_survivors", "formal_checks", "verified_candidates", "recovered_regions", "formal_recovery_rate", "exact_syntactic_recovery_rate", "canonical_syntactic_recovery_rate", "equivalent_alternative_rate", "mean_verified_rtl_cost", "median_verified_rtl_cost", "mean_reduction_rate", "cases_above_70_reduction"],
    "semantic_output_cone_recovery.csv": None,
    "semantic_direct_recovery_by_operator.csv": None,
    "semantic_direct_recovery_by_optimization.csv": None,
    "semantic_dependency_ranking_ablation.csv": ["family_order_mode", "eligible_regions", "generated_candidates", "formal_checks", "recovered_regions", "formal_recovery_rate", "formal_calls_per_recovery", "note"],
    "semantic_simulation_filter_ablation.csv": ["simulation_filter_mode", "simulation_checked", "formal_calls", "false_survivors", "verified_candidates", "recovered_regions", "note"],
    "semantic_direct_failure_analysis.csv": ["region_id", "case_id", "optimization", "source_type", "stage", "failure_reason"],
}
EXPECTED["semantic_output_cone_recovery.csv"] = EXPECTED["semantic_ground_truth_recovery.csv"]
EXPECTED["semantic_direct_recovery_by_operator.csv"] = EXPECTED["semantic_ground_truth_recovery.csv"]
EXPECTED["semantic_direct_recovery_by_optimization.csv"] = EXPECTED["semantic_ground_truth_recovery.csv"]


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
            return fail(f"missing {name}")
        with path.open(newline="", encoding="utf-8") as fh:
            header = next(csv.reader(fh), [])
        if header != fields:
            return fail(f"{name} header mismatch")
    verified = read_rows(RESULT / "semantic_verified_candidates.csv")
    formal = {row["candidate_id"]: row for row in read_rows(RESULT / "semantic_formal_results.csv")}
    for row in verified:
        proof = formal.get(row["candidate_id"])
        if not proof or proof["formal_status"] != "formally_verified_region":
            return fail("verified candidate without region proof")
        if proof["proof_scope"] != "region" or proof["formal_evidence_level"] != "formal_exhaustive":
            return fail("verified candidate proof scope/evidence is unsound")
    sim = read_rows(RESULT / "semantic_candidate_simulation.csv")
    if any(row["simulation_evidence_level"] == "formal_exhaustive" for row in sim):
        return fail("sampled simulation labeled formal")
    summary = (RESULT / "semantic_direct_recovery_summary.md").read_text(encoding="utf-8")
    if "Sampled simulation is used only as a filter" not in summary or "Region equivalence is not labeled global equivalence" not in summary:
        return fail("summary missing evidence caveats")
    rtl = RESULT / "verified_rtl" / "selected_verified_expressions.v"
    if verified and not rtl.exists():
        return fail("missing verified RTL sample")
    print("Semantic direct recovery results validated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
