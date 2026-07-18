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
}


def read(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        return reader.fieldnames or [], list(reader)


def main() -> int:
    problems: list[str] = []
    for filename, expected in EXPECTED.items():
        path = OUT / filename
        if not path.exists():
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
    if problems:
        print("\n".join(problems), file=sys.stderr)
        return 1
    print("Blind semantic CEGIS result checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
