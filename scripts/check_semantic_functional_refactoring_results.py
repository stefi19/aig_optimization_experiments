#!/usr/bin/env python3
"""Check semantic functional refactoring result consistency."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "results" / "semantic_functional_refactoring"

REQUIRED = {
    "experiment_manifest.csv": {"run_id", "git_head", "source_blind"},
    "environment.csv": {"tool", "version", "status"},
    "benchmark_split.csv": {"benchmark", "split", "source_blind", "manually_tuned"},
    "divisor_candidates.csv": {"divisor_id", "origin", "source_blind", "fingerprint"},
    "window_candidates.csv": {"window_id", "window_outputs", "source_blind"},
    "decomposition_candidates.csv": {"candidate_id", "divisor_id", "window_id", "split"},
    "decomposability_queries.csv": {"candidate_id", "formal_status", "solver_result", "counterexample_reproduced", "timeout"},
    "counterexamples.csv": {"candidate_id", "assignment_a", "assignment_b", "counterexample_reproduced"},
    "repair_transitions.csv": {"from_candidate_id", "to_candidate_id", "operation", "counterexample_id"},
    "quotient_synthesis.csv": {"candidate_id", "quotient_status", "completion_policy", "rows"},
    "quotient_proofs.csv": {"candidate_id", "formal_status", "solver_result", "counterexample_reproduced"},
    "non_vacuity_proofs.csv": {"candidate_id", "non_vacuity_status", "quotient_depends_on_m", "identity_rejected"},
    "graph_rewrites.csv": {"attempt_id", "candidate_id", "graph_rewrite_status", "graph_active", "divisor_consumers"},
    "global_abc_cec.csv": {"attempt_id", "candidate_id", "global_cec_status", "abc_available"},
    "resynthesis_survival.csv": {"attempt_id", "semantic_boundary_survives", "resynthesis_status"},
    "boundary_restoration.csv": {"attempt_id", "candidate_id", "split", "restored_boundary", "global_cec_status"},
    "controlled_experiments.csv": {"benchmark", "expected_outcome", "final_status", "restored_boundary", "global_cec_status"},
    "development_experiments.csv": {"seed_id", "split", "failure_stage", "failure_reason"},
    "heldout_experiments.csv": {"split", "attempted", "restored_boundaries"},
    "baselines.csv": {"baseline", "benchmark_group", "restored_boundaries"},
    "ablations.csv": {"ablation", "attempted", "restored_boundaries"},
    "runtime.csv": {"stage", "queries", "timeouts"},
    "failure_taxonomy.csv": {"benchmark_group", "failure_stage", "failure_reason", "count"},
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--allow-no-abc", action="store_true")
    args = parser.parse_args()
    tables: dict[str, list[dict[str, str]]] = {}
    errors: list[str] = []
    for name, columns in REQUIRED.items():
        path = args.output_dir / name
        if not path.exists():
            errors.append(f"missing required file: {path}")
            continue
        reader = csv.DictReader(path.open())
        rows = list(reader)
        tables[name] = rows
        missing = columns - set(reader.fieldnames or [])
        if missing:
            errors.append(f"{name} missing columns: {sorted(missing)}")
    if errors:
        return _fail(errors)

    _unique(tables["decomposition_candidates.csv"], "candidate_id", "decomposition_candidates.csv", errors)
    _unique(tables["graph_rewrites.csv"], "attempt_id", "graph_rewrites.csv", errors)
    decomp = {row["candidate_id"]: row for row in tables["decomposability_queries.csv"]}
    quotient = {row["candidate_id"]: row for row in tables["quotient_synthesis.csv"]}
    qproof = {row["candidate_id"]: row for row in tables["quotient_proofs.csv"]}
    nonvac = {row["candidate_id"]: row for row in tables["non_vacuity_proofs.csv"]}
    rewrite = {row["attempt_id"]: row for row in tables["graph_rewrites.csv"]}
    cec = {row["attempt_id"]: row for row in tables["global_abc_cec.csv"]}
    survival = {row["attempt_id"]: row for row in tables["resynthesis_survival.csv"]}

    for row in tables["benchmark_split.csv"]:
        if row["source_blind"] != "true":
            errors.append(f"non-blind split row: {row['benchmark']}")
        if row["manually_tuned"] != "false":
            errors.append(f"manually tuned split row: {row['benchmark']}")
    for row in tables["divisor_candidates.csv"]:
        if row["source_blind"] != "true":
            errors.append(f"non-blind divisor: {row['divisor_id']}")
    for row in tables["decomposability_queries.csv"]:
        if row["timeout"] == "true" and row["formal_status"] in {"decomposable", "non_decomposable"}:
            errors.append(f"timeout recorded as formal result: {row['candidate_id']}")
    for row in tables["counterexamples.csv"]:
        if row["counterexample_reproduced"] != "true":
            errors.append(f"unreproduced decomposition counterexample: {row['candidate_id']}")

    for row in tables["boundary_restoration.csv"]:
        if row["restored_boundary"] != "true":
            continue
        attempt = row["attempt_id"]
        candidate_id = row["candidate_id"]
        if decomp.get(candidate_id, {}).get("formal_status") != "decomposable" or decomp[candidate_id]["solver_result"] != "unsat":
            errors.append(f"restored boundary lacks UNSAT decomposability proof: {candidate_id}")
        if quotient.get(candidate_id, {}).get("quotient_status") != "synthesized_truth_table":
            errors.append(f"restored boundary lacks synthesized quotient: {candidate_id}")
        if qproof.get(candidate_id, {}).get("formal_status") != "quotient_equivalent" or qproof[candidate_id]["solver_result"] != "unsat":
            errors.append(f"restored boundary lacks independent quotient proof: {candidate_id}")
        if nonvac.get(candidate_id, {}).get("quotient_depends_on_m") != "true" or nonvac[candidate_id]["identity_rejected"] == "true":
            errors.append(f"restored boundary is vacuous or identity: {candidate_id}")
        if rewrite.get(attempt, {}).get("graph_rewrite_status") != "valid" or rewrite[attempt]["graph_active"] != "true" or rewrite[attempt]["divisor_consumers"] in {"[]", ""}:
            errors.append(f"restored boundary lacks graph-active divisor consumers: {attempt}")
        if cec.get(attempt, {}).get("global_cec_status") != "equivalent":
            errors.append(f"restored boundary lacks ABC global CEC: {attempt}")
        if survival.get(attempt, {}).get("semantic_boundary_survives") != "true":
            errors.append(f"restored boundary lacks resynthesis survival evidence: {attempt}")

    positives = [row for row in tables["controlled_experiments.csv"] if row["expected_outcome"].startswith("positive")]
    accepted = [row for row in positives if row["final_status"] == "accepted"]
    abc_available = any(row["tool"] == "abc" and row["status"] == "available" for row in tables["environment.csv"])
    if not accepted and not (args.allow_no_abc and not abc_available):
        errors.append("no controlled positive functional refactoring accepted")
    for row in accepted:
        if row["global_cec_status"] != "equivalent" or row["graph_active"] != "true" or row["restored_boundary"] != "true":
            errors.append(f"accepted controlled refactoring lacks proof stack: {row['benchmark']}")
    for row in tables["controlled_experiments.csv"]:
        if row["expected_outcome"].startswith("negative") and row["final_status"] == "accepted":
            errors.append(f"negative control accepted: {row['benchmark']}")
    for row in tables["development_experiments.csv"]:
        if not row["failure_reason"]:
            errors.append(f"real/development row lacks failure reason: {row['seed_id']}")
    for row in tables["heldout_experiments.csv"]:
        if row["split"] == "heldout" and int(row["restored_boundaries"]) != 0:
            # This checker permits a future positive only if raw boundary rows
            # back it.  The current committed result is zero.
            raw = sum(1 for b in tables["boundary_restoration.csv"] if b["split"] == "heldout" and b["restored_boundary"] == "true")
            if raw != int(row["restored_boundaries"]):
                errors.append("heldout summary/restored raw mismatch")

    restored_raw = sum(1 for row in tables["boundary_restoration.csv"] if row["restored_boundary"] == "true")
    controlled_restored = sum(1 for row in tables["controlled_experiments.csv"] if row["restored_boundary"] == "true")
    if restored_raw != controlled_restored:
        errors.append(f"controlled/restoration mismatch: raw={restored_raw} controlled={controlled_restored}")
    if errors:
        return _fail(errors)
    print(
        "Semantic functional refactoring results validated: "
        f"{len(tables['divisor_candidates.csv'])} divisors, "
        f"{len(tables['window_candidates.csv'])} windows, "
        f"{len(accepted)} controlled accepted refactorings, {restored_raw} restored controlled boundaries"
    )
    return 0


def _unique(rows: list[dict[str, str]], key: str, table: str, errors: list[str]) -> None:
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
