#!/usr/bin/env python3
"""Validate blind semantic CEGIS result schemas and evidence labels."""

from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "blind_semantic_cegis"

EXPECTED = {
    "leakage_audit.csv": ["component", "field", "inference_time_access", "ground_truth_derived", "risk_level", "evidence", "blind_replacement", "schema_version"],
    "blind_bus_hypotheses.csv": ["bus_hypothesis_id", "region_id", "direction", "rank", "role", "member_nodes", "ordered_member_nodes", "width", "bit_order", "signedness_hypothesis", "grouping_score", "ordering_score", "evidence_sources", "used_ground_truth_for_generation", "schema_version"],
    "parametric_candidates.csv": ["candidate_id", "region_id", "template_family", "symbolic_parameters", "parameter_domains", "width_constraints", "signedness_constraints", "expression_depth", "search_cost", "canonical_form", "rtl_text", "inference_evidence", "generated_without_ground_truth", "expression_json", "schema_version"],
    "cegis_iterations.csv": ["candidate_id", "region_id", "iteration", "examples_before", "examples_after", "candidate_parameters", "candidate_expression", "solver_status", "counterexample_assignment", "output_difference", "synthesis_runtime", "verification_runtime", "final_proof_status", "termination_reason", "schema_version"],
    "formal_proofs.csv": ["candidate_id", "region_id", "formal_backend", "proof_scope", "formal_status", "formal_evidence_level", "solver_result", "counterexample_available", "counterexample_assignment", "proof_runtime", "timeout", "unsupported_reason", "schema_version"],
    "z3_exhaustive_crosscheck.csv": ["candidate_id", "region_id", "case_id", "optimization", "output_width", "input_scalar_bits", "exhaustive_status", "z3_status", "verdict_agreement", "z3_counterexample_available", "z3_counterexample_reproduced", "exhaustive_runtime", "z3_runtime", "z3_version", "unsupported_reason", "schema_version"],
    "z3_cegis_iterations.csv": ["mode", "candidate_id", "region_id", "case_id", "operator", "width", "iteration", "examples_before", "examples_after", "template_family", "candidate_expression", "synthesis_result", "verification_result", "counterexample_assignment", "counterexample_reproduced", "synthesis_runtime", "verification_runtime", "cumulative_runtime", "termination_reason", "proof_backend", "proof_scope", "evidence_level", "schema_version"],
    "z3_formal_proofs.csv": ["mode", "candidate_id", "region_id", "case_id", "operator", "width", "formal_backend", "proof_scope", "formal_status", "formal_evidence_level", "solver_result", "counterexample_available", "counterexample_assignment", "proof_runtime", "timeout", "unsupported_reason", "schema_version"],
    "z3_blind_oracle_comparison.csv": ["mode", "unique_cases_attempted", "unique_cases_recovered", "regions_attempted", "regions_recovered", "width_12_or_16_attempted", "width_12_or_16_recovered", "iterations", "counterexamples", "timeouts", "schema_version"],
    "z3_recovery_by_width.csv": ["mode", "width", "regions_attempted", "regions_recovered", "iterations", "counterexamples", "schema_version"],
    "z3_recovery_by_operator.csv": ["mode", "operator", "regions_attempted", "regions_recovered", "iterations", "counterexamples", "schema_version"],
}
OPTIONAL = {"z3_exhaustive_crosscheck.csv", "z3_cegis_iterations.csv", "z3_formal_proofs.csv", "z3_blind_oracle_comparison.csv", "z3_recovery_by_width.csv", "z3_recovery_by_operator.csv"}


def read(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        return reader.fieldnames or [], list(reader)


def main() -> int:
    problems: list[str] = []
    for filename, expected in EXPECTED.items():
        path = OUT / filename
        if not path.exists():
            if filename in OPTIONAL:
                continue
            problems.append(f"missing {filename}")
            continue
        header, rows = read(path)
        if header != expected:
            problems.append(f"{filename}: schema mismatch {header}")
        if filename == "blind_bus_hypotheses.csv":
            bad = [r for r in rows if r["used_ground_truth_for_generation"] != "false"]
            if bad:
                problems.append("blind bus hypotheses used ground truth")
        if filename == "formal_proofs.csv":
            for row in rows:
                if row["formal_status"] in {"timeout", "unsupported", "error"} and row["formal_evidence_level"].startswith("formal"):
                    problems.append("timeout/unsupported proof labelled formal")
        if filename == "z3_exhaustive_crosscheck.csv":
            bad = [r for r in rows if r["verdict_agreement"] != "true"]
            if bad:
                problems.append("Z3/exhaustive crosscheck contains disagreements")
            bad_cex = [r for r in rows if r["z3_counterexample_available"] == "true" and r["z3_counterexample_reproduced"] != "true"]
            if bad_cex:
                problems.append("Z3 crosscheck has unreproduced counterexamples")
        if filename == "z3_cegis_iterations.csv":
            bad = [r for r in rows if r["verification_result"] == "sat" and (r["counterexample_reproduced"] != "true" or int(r["examples_after"]) <= int(r["examples_before"]))]
            if bad:
                problems.append("Z3 CEGIS has SAT counterexamples that were not reproduced/refined")
        if filename == "z3_formal_proofs.csv":
            bad = [r for r in rows if r["formal_status"] == "formally_verified_region" and r["formal_evidence_level"] != "formal_smt"]
            if bad:
                problems.append("Z3 proofs accepted without formal_smt evidence")
    if problems:
        print("\n".join(problems), file=sys.stderr)
        return 1
    print("Blind semantic CEGIS result checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
