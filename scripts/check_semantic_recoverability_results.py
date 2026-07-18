#!/usr/bin/env python3
"""Strict checker for semantic recoverability frontier results."""

from __future__ import annotations

import argparse
import csv
import sys
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "semantic_recoverability_frontier"


REQUIRED = {
    "experiment_manifest.csv": {"run_id", "git_head", "mode", "deterministic_seed", "source_blind_primary", "schema_version"},
    "environment_provenance.csv": {"tool", "version", "path", "status", "schema_version"},
    "benchmark_sources_licenses.csv": {"benchmark", "design_family", "split", "source_type", "license", "schema_version"},
    "benchmark_split.csv": {"benchmark", "design_family", "split", "manual_tuning_allowed", "schema_version"},
    "ground_truth_boundary_manifest.csv": {"boundary_id", "benchmark", "operator_type", "source_support", "eligible_for_blind_evaluation", "fingerprint", "schema_version"},
    "leakage_audit_results.csv": {"row_id", "oracle_mode", "forbidden_fields_present", "leakage_status", "schema_version"},
    "synthesis_trajectories.csv": {"trajectory_id", "benchmark", "split", "pass_sequence", "checkpoint_count", "realized_checkpoint_count", "schema_version"},
    "checkpoint_hashes.csv": {"trajectory_id", "checkpoint_id", "checkpoint_index", "sha256", "artifact_status", "artifact_exists", "parse_status", "schema_version"},
    "checkpoint_cec_results.csv": {"trajectory_id", "checkpoint_id", "checkpoint_index", "cec_status", "schema_version"},
    "checkpoint_structural_metrics.csv": {"trajectory_id", "checkpoint_id", "checkpoint_index", "node_count", "level_count", "schema_version"},
    "blind_candidate_predictions.csv": {"prediction_id", "checkpoint_id", "candidate_signal", "source_blind", "schema_version"},
    "blind_recovery_results.csv": {"result_id", "boundary_id", "checkpoint_id", "method", "oracle_mode", "recovery_level", "recovered", "timeout", "failure_reason", "schema_version"},
    "oracle_ladder_results.csv": {"result_id", "boundary_id", "checkpoint_id", "method", "oracle_mode", "recovery_level", "recovered", "decomposition_status", "solver_result", "timeout", "schema_version"},
    "decomposition_proof_results.csv": {"result_id", "boundary_id", "checkpoint_id", "oracle_mode", "formal_status", "solver_result", "counterexample_reproduced", "timeout", "schema_version"},
    "decomposition_counterexamples.csv": {"counterexample_id", "checkpoint_id", "boundary_id", "counterexample_reproduced", "schema_version"},
    "residual_selection_iterations.csv": {"checkpoint_id", "boundary_id", "residual_set", "search_status", "minimum_status", "residual_lower_bound", "residual_upper_bound", "schema_version"},
    "residual_bounds.csv": {"checkpoint_id", "boundary_id", "minimum_status", "residual_lower_bound", "residual_upper_bound", "best_residual_set", "schema_version"},
    "window_locality_results.csv": {"checkpoint_id", "boundary_id", "window_level", "classification", "decomposition_status", "global_cec_status", "schema_version"},
    "recoverability_transitions.csv": {"boundary_id", "trajectory_id", "method", "transition", "schema_version"},
    "method_specific_frontiers.csv": {"boundary_id", "trajectory_id", "method", "first_loss_checkpoint", "last_success_checkpoint", "non_monotonic", "recoverable_fraction", "schema_version"},
    "pass_level_deltas.csv": {"trajectory_id", "boundary_id", "method", "pass_name", "transition_class", "causal_claim", "schema_version"},
    "pass_ablations.csv": {"ablation_id", "changed_pass", "causal_claim", "schema_version"},
    "boundary_durability_results.csv": {"boundary_id", "trajectory_id", "insertion_checkpoint", "suffix_checkpoint", "boundary_survives_suffix", "global_cec_status", "schema_version"},
    "optimisation_tradeoffs.csv": {"trajectory_id", "checkpoint_id", "node_count", "depth", "recoverable_boundary_fraction", "oracle_recoverable_fraction", "schema_version"},
    "controlled_results.csv": {"benchmark", "boundaries", "trajectories", "checkpoints", "blind_recovered_rows", "oracle_recovered_rows", "schema_version"},
    "development_results.csv": {"benchmark", "boundaries", "trajectories", "checkpoints", "blind_recovered_rows", "oracle_recovered_rows", "failure_summary", "schema_version"},
    "heldout_results.csv": {"benchmark", "boundaries", "trajectories", "checkpoints", "blind_recovered_rows", "oracle_recovered_rows", "failure_summary", "schema_version"},
    "failure_taxonomy.csv": {"benchmark_group", "method", "oracle_mode", "failure_reason", "count", "schema_version"},
    "runtime_timeout_summary.csv": {"stage", "queries", "timeouts", "total_runtime_s", "max_runtime_s", "schema_version"},
}

BLIND_FORBIDDEN = {"operator_type", "source_support", "source_location", "oracle_divisor_id", "boundary_type", "ground_truth_expression"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=OUT)
    parser.add_argument("--allow-no-abc", action="store_true")
    args = parser.parse_args()
    errors: list[str] = []
    tables = {}
    for name, required in REQUIRED.items():
        path = args.output_dir / name
        if not path.exists():
            errors.append(f"missing required file: {name}")
            continue
        rows = _read(path)
        tables[name] = rows
        header = set(rows[0].keys()) if rows else set(_header(path))
        missing = required - header
        if missing:
            errors.append(f"{name} missing columns: {sorted(missing)}")
    if errors:
        return _finish(errors)

    _check_unique(tables["checkpoint_hashes.csv"], ("checkpoint_id",), "checkpoint_hashes.csv", errors)
    _check_unique(tables["blind_recovery_results.csv"], ("result_id",), "blind_recovery_results.csv", errors)
    _check_unique(tables["oracle_ladder_results.csv"], ("result_id",), "oracle_ladder_results.csv", errors)

    cec_by_cp = {r["checkpoint_id"]: r for r in tables["checkpoint_cec_results.csv"]}
    for row in tables["checkpoint_hashes.csv"]:
        cec = cec_by_cp.get(row["checkpoint_id"])
        if cec is None:
            errors.append(f"checkpoint without CEC evidence: {row['checkpoint_id']}")
        elif cec["cec_status"] != "equivalent" and not args.allow_no_abc:
            errors.append(f"non-equivalent checkpoint included: {row['checkpoint_id']} {cec['cec_status']}")
        artifact_exists = row["artifact_exists"] == "true"
        if cec and cec["cec_status"] == "equivalent":
            if row["artifact_status"] != "materialized" or not artifact_exists or row["parse_status"] != "parse_valid" or not row["sha256"]:
                errors.append(f"equivalent checkpoint lacks materialized parse-valid artifact: {row['checkpoint_id']}")
        if row["artifact_status"] == "materialized" and (not artifact_exists or row["parse_status"] != "parse_valid"):
            errors.append(f"materialized checkpoint is not parse-valid: {row['checkpoint_id']}")
        if row["artifact_status"] != "materialized" and row["sha256"]:
            errors.append(f"unrealized checkpoint has nonempty hash: {row['checkpoint_id']}")
        if row["artifact_status"] == "materialized" and not row["sha256"]:
            errors.append(f"materialized checkpoint missing hash: {row['checkpoint_id']}")
        if artifact_exists:
            artifact_path = _resolve_artifact_path(args.output_dir, row["blif_path"])
            if not artifact_path.exists():
                errors.append(f"checkpoint claims existing artifact but file is missing: {row['checkpoint_id']}")

    unrealized = {
        row["checkpoint_id"]
        for row in tables["checkpoint_hashes.csv"]
        if row["artifact_status"] != "materialized" or row["artifact_exists"] != "true" or row["parse_status"] != "parse_valid"
    }
    non_equivalent = {cp for cp, row in cec_by_cp.items() if row["cec_status"] != "equivalent"}
    unavailable_for_analysis = unrealized | non_equivalent
    for table_name in (
        "blind_candidate_predictions.csv",
        "blind_recovery_results.csv",
        "oracle_ladder_results.csv",
        "decomposition_proof_results.csv",
        "decomposition_counterexamples.csv",
        "residual_selection_iterations.csv",
        "residual_bounds.csv",
        "window_locality_results.csv",
        "optimisation_tradeoffs.csv",
    ):
        for row in tables[table_name]:
            if row["checkpoint_id"] in unavailable_for_analysis:
                errors.append(f"{table_name} includes unrealized or non-equivalent checkpoint: {row['checkpoint_id']}")
    for row in tables["boundary_durability_results.csv"]:
        if row["insertion_checkpoint"] in unavailable_for_analysis or row["suffix_checkpoint"] in unavailable_for_analysis:
            errors.append(f"durability row includes unrealized or non-equivalent checkpoint: {row['boundary_id']}")

    trajectory_counts: dict[str, dict[str, int]] = {}
    for row in tables["checkpoint_hashes.csv"]:
        data = trajectory_counts.setdefault(row["trajectory_id"], {"planned": 0, "realized": 0})
        data["planned"] += 1
        if row["artifact_status"] == "materialized" and row["artifact_exists"] == "true" and row["parse_status"] == "parse_valid":
            data["realized"] += 1
    for row in tables["synthesis_trajectories.csv"]:
        counts = trajectory_counts.get(row["trajectory_id"], {"planned": 0, "realized": 0})
        if int(row["checkpoint_count"]) != counts["planned"]:
            errors.append(f"trajectory planned checkpoint count mismatch: {row['trajectory_id']}")
        if int(row["realized_checkpoint_count"]) != counts["realized"]:
            errors.append(f"trajectory realized checkpoint count mismatch: {row['trajectory_id']}")

    for row in tables["blind_candidate_predictions.csv"]:
        if row["source_blind"] != "true":
            errors.append(f"blind prediction not marked source_blind: {row['prediction_id']}")
        forbidden = BLIND_FORBIDDEN & set(row)
        if forbidden:
            errors.append(f"blind prediction contains forbidden columns: {sorted(forbidden)}")

    for row in tables["leakage_audit_results.csv"]:
        if row["oracle_mode"] == "blind" and row["leakage_status"] != "pass":
            errors.append(f"leakage audit failed for {row['row_id']}")

    for row in tables["blind_recovery_results.csv"]:
        if row["oracle_mode"] != "blind":
            errors.append(f"blind table contains non-blind row: {row['result_id']}")
        if row["timeout"] == "true" and row["recovered"] == "true":
            errors.append(f"timeout counted as blind recovery: {row['result_id']}")
        if row["recovery_level"].startswith(("R5", "R6", "R7")):
            errors.append(f"oracle recovery level appears in blind row: {row['result_id']}")

    for row in tables["oracle_ladder_results.csv"]:
        if row["oracle_mode"] == "blind":
            errors.append(f"oracle table contains blind row: {row['result_id']}")
        if row["solver_result"] == "sat" and row["recovered"] == "true":
            errors.append(f"SAT decomposition counted as recovery: {row['result_id']}")
        if row["timeout"] == "true" and row["recovered"] == "true":
            errors.append(f"timeout counted as oracle recovery: {row['result_id']}")
        if row["recovery_level"] == "R8_non_local_global_factorisation" and row["recovered"] == "true":
            errors.append(f"whole-design/non-local factorisation counted as local recovery: {row['result_id']}")

    for row in tables["residual_bounds.csv"]:
        if row["minimum_status"] == "exact_minimum" and row["residual_lower_bound"] != row["residual_upper_bound"]:
            errors.append(f"exact residual minimum lacks matching lower/upper bound: {row['checkpoint_id']} {row['boundary_id']}")
        if row["minimum_status"] != "exact_minimum" and row["residual_upper_bound"] and row["residual_lower_bound"] == row["residual_upper_bound"]:
            errors.append(f"best-found residual width labelled like exact minimum: {row['checkpoint_id']} {row['boundary_id']}")

    for row in tables["window_locality_results.csv"]:
        if row["window_level"] == "whole_design_output_frontier" and row["classification"] != "whole_design_diagnostic_not_local_success":
            errors.append(f"whole-design window not diagnostic-only: {row['checkpoint_id']} {row['boundary_id']}")

    for row in tables["pass_level_deltas.csv"]:
        if row["transition_class"] != "unchanged" and row["causal_claim"] != "not_claimed_controlled_ablation_required":
            errors.append(f"causal pass wording without controlled ablation: {row['trajectory_id']} {row['pass_name']}")

    for row in tables["boundary_durability_results.csv"]:
        if not row["suffix_checkpoint"]:
            errors.append(f"survival claim without suffix checkpoint: {row['boundary_id']}")
        if row["boundary_survives_suffix"] == "true" and row["global_cec_status"] != "equivalent":
            errors.append(f"durability success without global CEC: {row['boundary_id']}")

    raw_failures = Counter((r["split"], r["method"], r["oracle_mode"], r["failure_reason"]) for table in ("blind_recovery_results.csv", "oracle_ladder_results.csv") for r in tables[table] if r["failure_reason"])
    tax_failures = Counter((r["benchmark_group"], r["method"], r["oracle_mode"], r["failure_reason"]) for r in tables["failure_taxonomy.csv"] for _ in range(int(r["count"])))
    if raw_failures != tax_failures:
        errors.append("failure taxonomy totals do not match raw rows")

    summary = (args.output_dir / "final_supported_claims_summary.md").read_text(encoding="utf-8") if (args.output_dir / "final_supported_claims_summary.md").exists() else ""
    blind_true = sum(r["recovered"] == "true" for r in tables["blind_recovery_results.csv"])
    oracle_true = sum(r["recovered"] == "true" for r in tables["oracle_ladder_results.csv"])
    if f"blind recovered rows: {blind_true} / {len(tables['blind_recovery_results.csv'])}" not in summary:
        errors.append("summary blind total inconsistent with raw rows")
    if f"oracle recovered rows: {oracle_true} / {len(tables['oracle_ladder_results.csv'])}" not in summary:
        errors.append("summary oracle total inconsistent with raw rows")

    if not args.allow_no_abc and (not tables["development_results.csv"] or not tables["heldout_results.csv"] or not tables["controlled_results.csv"]):
        errors.append("controlled/development/held-out summaries must all be present")

    return _finish(errors)


def _read(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _header(path: Path) -> list[str]:
    with path.open(newline="", encoding="utf-8") as fh:
        return next(csv.reader(fh), [])


def _check_unique(rows: list[dict[str, str]], keys: tuple[str, ...], table: str, errors: list[str]) -> None:
    seen: set[tuple[str, ...]] = set()
    for row in rows:
        key = tuple(row[k] for k in keys)
        if key in seen:
            errors.append(f"duplicate key in {table}: {key}")
        seen.add(key)


def _finish(errors: list[str]) -> int:
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print("Semantic recoverability frontier results validated")
    return 0


def _resolve_artifact_path(output_dir: Path, blif_path: str) -> Path:
    path = Path(blif_path)
    if path.is_absolute():
        return path
    candidate = ROOT / path
    if candidate.exists():
        return candidate
    return output_dir / path


if __name__ == "__main__":
    raise SystemExit(main())
