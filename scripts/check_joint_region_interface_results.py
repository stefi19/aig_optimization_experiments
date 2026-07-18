#!/usr/bin/env python3
"""Validate joint region/interface discovery result consistency."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "results" / "joint_region_interface_discovery"

REQUIRED = {
    "experiment_manifest.csv": {"run_id", "git_head", "source_blind"},
    "environment.csv": {"tool", "version", "path", "status"},
    "candidate_state_summary.csv": {"candidate_id", "source_blind", "fingerprint", "closure_status"},
    "search_transitions.csv": {"transition_id", "from_candidate_id", "to_candidate_id", "operation", "counterexample_id"},
    "counterexample_diagnostics.csv": {"counterexample_id", "counterexample_reproduced", "influenced_next_candidate", "source_blind"},
    "proof_results.csv": {"candidate_id", "formal_status", "formal_evidence_level", "solver_result"},
    "emitted_module_validation.csv": {"candidate_id", "ast_vs_blif_status"},
    "graph_rewrite_validation.csv": {"attempt_id", "candidate_id", "graph_rewrite_status", "graph_active"},
    "global_cec_results.csv": {"attempt_id", "implementation_global_cec", "abc_available"},
    "boundary_restoration_results.csv": {"attempt_id", "candidate_id", "newly_recovered_boundary", "boundary_validation_status"},
    "controlled_benchmark_results.csv": {"benchmark", "expected_outcome", "final_status", "global_cec", "restored_boundary"},
    "real_benchmark_results.csv": {"seed_id", "split", "failure_stage", "failure_reason"},
    "heldout_results.csv": {"split", "attempted"},
    "failure_taxonomy.csv": {"benchmark_group", "failure_stage", "failure_reason", "count"},
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--allow-no-abc", action="store_true", help="Permit zero accepted controlled replacements only when ABC is unavailable.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    out_dir = args.output_dir
    errors: list[str] = []
    tables = {}
    for name, cols in REQUIRED.items():
        path = out_dir / name
        if not path.exists():
            errors.append(f"missing required result: {path}")
            continue
        reader = csv.DictReader(path.open())
        rows = list(reader)
        tables[name] = rows
        missing = cols - set(reader.fieldnames or [])
        if missing:
            errors.append(f"{name} missing columns: {sorted(missing)}")
    if errors:
        return _fail(errors)

    _check_unique(tables["candidate_state_summary.csv"], "candidate_id", "candidate_state_summary.csv", errors)
    _check_unique(tables["search_transitions.csv"], "transition_id", "search_transitions.csv", errors)

    candidates = {row["candidate_id"]: row for row in tables["candidate_state_summary.csv"]}
    proofs = {row["candidate_id"]: row for row in tables["proof_results.csv"]}
    rewrites = {row["attempt_id"]: row for row in tables["graph_rewrite_validation.csv"]}
    cecs = {row["attempt_id"]: row for row in tables["global_cec_results.csv"]}

    for row in tables["candidate_state_summary.csv"]:
        if row["source_blind"] != "true":
            errors.append(f"non-blind candidate state: {row['candidate_id']}")
    for row in tables["counterexample_diagnostics.csv"]:
        if row["counterexample_reproduced"] != "true":
            errors.append(f"unreproduced counterexample: {row['counterexample_id']}")
        if row["influenced_next_candidate"] != "true":
            errors.append(f"counterexample did not influence next candidate: {row['counterexample_id']}")
        if row["source_blind"] != "true":
            errors.append(f"non-blind diagnostic: {row['counterexample_id']}")

    for row in tables["boundary_restoration_results.csv"]:
        attempt = row["attempt_id"]
        if row["newly_recovered_boundary"] != "true":
            continue
        rewrite = rewrites.get(attempt)
        cec = cecs.get(attempt)
        proof = proofs.get(row["candidate_id"])
        if not rewrite or rewrite["graph_rewrite_status"] != "valid" or rewrite["graph_active"] != "true":
            errors.append(f"restored boundary lacks graph-active valid rewrite: {attempt}")
        if not cec or cec["implementation_global_cec"] != "equivalent":
            errors.append(f"restored boundary lacks equivalent global CEC: {attempt}")
        if not cec or cec["abc_available"] != "true":
            errors.append(f"restored boundary records ABC unavailable: {attempt}")
        if not proof or proof["formal_status"] != "formally_verified_region" or proof["formal_evidence_level"] != "formal_smt":
            errors.append(f"restored boundary lacks formal SMT region proof: {attempt}")

    positives = [row for row in tables["controlled_benchmark_results.csv"] if row["expected_outcome"].startswith("positive")]
    accepted = [row for row in positives if row["final_status"] == "accepted"]
    abc_available = any(row.get("tool") == "abc" and row.get("status") == "available" for row in tables["environment.csv"])
    if not accepted and not (args.allow_no_abc and not abc_available):
        errors.append("no controlled positive joint replacement accepted")
    for row in accepted:
        if row["global_cec"] != "equivalent" or row["graph_active_replacement"] != "true" or row["restored_boundary"] != "true":
            errors.append(f"accepted controlled case is missing proof stack: {row['benchmark']}")
        attempt = next((attempt_id for attempt_id, cec in cecs.items() if cec.get("benchmark") == row["benchmark"] and cec.get("implementation_global_cec") == row["global_cec"]), "")
        if cecs.get(attempt, {}).get("abc_available") != "true":
            errors.append(f"accepted controlled case records ABC unavailable: {row['benchmark']}")

    for row in tables["controlled_benchmark_results.csv"]:
        if row["expected_outcome"].startswith("negative") and row["final_status"] == "accepted":
            errors.append(f"negative control accepted: {row['benchmark']}")

    restored = sum(1 for row in tables["boundary_restoration_results.csv"] if row["newly_recovered_boundary"] == "true")
    controlled_restored = sum(1 for row in tables["controlled_benchmark_results.csv"] if row["restored_boundary"] == "true")
    if restored != controlled_restored:
        errors.append(f"restored boundary count mismatch: boundary={restored} controlled={controlled_restored}")

    for row in tables["real_benchmark_results.csv"]:
        if not row["failure_reason"]:
            errors.append(f"real row lacks failure reason: {row['seed_id']}")

    if errors:
        return _fail(errors)
    print(
        "Joint region/interface results validated: "
        f"{len(candidates)} candidate states, {len(tables['search_transitions.csv'])} transitions, "
        f"{len(accepted)} controlled accepted replacements, {restored} restored boundaries"
    )
    return 0


def _check_unique(rows: list[dict[str, str]], key: str, table: str, errors: list[str]) -> None:
    seen = set()
    for row in rows:
        value = row[key]
        if value in seen:
            errors.append(f"duplicate {key} in {table}: {value}")
        seen.add(value)


def _fail(errors: list[str]) -> int:
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
