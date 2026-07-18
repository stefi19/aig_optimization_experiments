#!/usr/bin/env python3
"""Strict consistency checks for active source-counterpart results."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "results" / "active_source_counterpart_refactoring"

REQUIRED = {
    "experiment_manifest.csv": {"git_head", "source_blind", "schema_version"},
    "environment.csv": {"tool", "version", "status"},
    "benchmark_split.csv": {"benchmark", "split", "source_blind", "heldout_locked_before_execution"},
    "target_candidates.csv": {"target_id", "target_origin", "selected_for_attempt", "source_blind"},
    "target_ranking.csv": {"target_id", "ranking_mode", "rank", "selected"},
    "anchored_cuts.csv": {"target_id", "cut_id", "all_leaves_formal", "validation_status"},
    "cut_function_extraction.csv": {"target_id", "function_status", "backend"},
    "counterpart_candidates.csv": {"candidate_id", "optimized_target_nodes", "generated_source_counterpart_nodes", "source_blind", "fingerprint"},
    "counterpart_synthesis.csv": {"candidate_id", "backend", "synthesis_status"},
    "counterpart_proofs.csv": {"candidate_id", "formal_status", "solver_result", "formal_evidence_level", "counterexample_reproduced", "timeout"},
    "source_window_candidates.csv": {"window_id", "candidate_id", "selected", "residual_interface"},
    "decomposition_queries.csv": {"candidate_id", "formal_status", "solver_result", "counterexample_reproduced", "timeout"},
    "counterexamples.csv": {"candidate_id", "counterexample_reproduced"},
    "residual_interface_search.csv": {"candidate_id", "operation", "accepted_by_budget"},
    "quotient_synthesis.csv": {"candidate_id", "quotient_status", "completion_policy"},
    "quotient_proofs.csv": {"candidate_id", "formal_status", "solver_result", "counterexample_reproduced", "timeout"},
    "source_rewrite_plans.csv": {"attempt_id", "candidate_id", "plan_status"},
    "graph_validation.csv": {"attempt_id", "candidate_id", "graph_rewrite_status", "graph_active", "functional_influence", "bypass_status"},
    "global_cec.csv": {"attempt_id", "candidate_id", "cec_scope", "cec_status", "abc_available"},
    "activity_bypass_validation.csv": {"attempt_id", "candidate_id", "quotient_depends_on_w", "identity_rejected", "acceptance_status"},
    "boundary_recovery.csv": {"attempt_id", "candidate_id", "usable_frontier_anchor", "selected_anchor", "new_recovered_boundary", "graph_active", "global_cec_status"},
    "critical_path_utility.csv": {"attempt_id", "newly_resolved_critical_path_target", "mapping_evidence"},
    "durability_trajectories.csv": {"candidate_id", "strategy", "cec_status", "counterpart_present", "graph_active", "usable_boundary"},
    "preservation_strategies.csv": {"strategy", "attempted", "usable_boundary"},
    "gf2_linear_baseline.csv": {"candidate_id", "backend", "status", "is_affine", "proved_independently"},
    "baselines.csv": {"baseline", "benchmark_group", "attempted", "new_boundaries"},
    "ablations.csv": {"ablation", "attempted", "new_boundaries"},
    "controlled_results.csv": {"benchmark", "expected_outcome", "final_status", "counterpart_proof_status", "graph_active", "source_cec_status", "cross_cec_status"},
    "development_results.csv": {"target_id", "split", "candidate_status", "failure_reason"},
    "heldout_results.csv": {"split", "attempted", "new_boundaries", "failure_reasons"},
    "runtime_timeout_summary.csv": {"stage", "queries", "timeouts"},
    "failure_taxonomy.csv": {"benchmark_group", "failure_stage", "failure_reason", "count"},
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--allow-no-abc", action="store_true")
    args = parser.parse_args()
    tables: dict[str, list[dict[str, str]]] = {}
    errors: list[str] = []
    for name, required in REQUIRED.items():
        path = args.output_dir / name
        if not path.exists():
            errors.append(f"missing required file: {name}")
            continue
        reader = csv.DictReader(path.open())
        rows = list(reader)
        tables[name] = rows
        missing = required - set(reader.fieldnames or [])
        if missing:
            errors.append(f"{name} missing columns: {sorted(missing)}")
    if errors:
        return _fail(errors)

    _unique(tables["counterpart_candidates.csv"], "candidate_id", "counterpart_candidates.csv", errors)
    _unique(tables["source_rewrite_plans.csv"], "attempt_id", "source_rewrite_plans.csv", errors)

    proof = {r["candidate_id"]: r for r in tables["counterpart_proofs.csv"]}
    decomp = {r["candidate_id"]: r for r in tables["decomposition_queries.csv"]}
    quotient = {r["candidate_id"]: r for r in tables["quotient_synthesis.csv"]}
    qproof = {r["candidate_id"]: r for r in tables["quotient_proofs.csv"]}
    activity = {r["attempt_id"]: r for r in tables["activity_bypass_validation.csv"]}
    graph = {r["attempt_id"]: r for r in tables["graph_validation.csv"]}
    cec = {}
    for row in tables["global_cec.csv"]:
        cec[(row["attempt_id"], row["cec_scope"])] = row

    for row in tables["benchmark_split.csv"] + tables["target_candidates.csv"] + tables["counterpart_candidates.csv"]:
        if row.get("source_blind") != "true":
            errors.append(f"non-blind row in {row}")

    for row in tables["counterpart_proofs.csv"] + tables["decomposition_queries.csv"] + tables["quotient_proofs.csv"]:
        if row["timeout"] == "true" and row["formal_status"] in {"proven_counterpart_equivalent", "decomposable", "quotient_equivalent"}:
            errors.append(f"timeout accepted as formal proof: {row['candidate_id']}")
        if row.get("counterexample_available") == "true" and row["counterexample_reproduced"] != "true":
            errors.append(f"unreproduced counterexample: {row['candidate_id']}")

    for row in tables["counterexamples.csv"]:
        if row["counterexample_reproduced"] != "true":
            errors.append(f"counterexample fixture not reproduced: {row['candidate_id']}")

    accepted = [r for r in tables["controlled_results.csv"] if r["final_status"] == "accepted"]
    positives = [r for r in tables["controlled_results.csv"] if r["expected_outcome"].startswith("positive")]
    abc_recorded_available = any(row.get("tool") == "abc" and row.get("status") == "available" for row in tables["environment.csv"])
    if not accepted and not (args.allow_no_abc and not abc_recorded_available):
        errors.append("no controlled active source-counterpart accepted")
    for row in tables["controlled_results.csv"]:
        cid = f"{row['benchmark']}__active_source_counterpart"
        aid = f"{cid}__rewrite"
        if row["expected_outcome"].startswith("negative") and row["final_status"] == "accepted":
            errors.append(f"negative control accepted: {row['benchmark']}")
        if row["final_status"] != "accepted":
            continue
        if proof.get(cid, {}).get("formal_status") != "proven_counterpart_equivalent":
            errors.append(f"accepted row lacks counterpart proof: {cid}")
        if decomp.get(cid, {}).get("formal_status") != "decomposable" or decomp[cid]["solver_result"] != "unsat":
            errors.append(f"accepted row lacks UNSAT decomposition: {cid}")
        if quotient.get(cid, {}).get("quotient_status") != "synthesized_truth_table":
            errors.append(f"accepted row lacks exact quotient: {cid}")
        if qproof.get(cid, {}).get("formal_status") != "quotient_equivalent" or qproof[cid]["solver_result"] != "unsat":
            errors.append(f"accepted row lacks quotient proof: {cid}")
        if graph.get(aid, {}).get("graph_active") != "true" or graph[aid]["functional_influence"] != "true":
            errors.append(f"accepted row lacks graph activity/influence: {aid}")
        if activity.get(aid, {}).get("quotient_depends_on_w") != "true" or activity[aid]["identity_rejected"] == "true":
            errors.append(f"accepted row is vacuous, identity, or bypassed: {aid}")
        if cec.get((aid, "S_vs_Sprime"), {}).get("abc_available") != "true":
            errors.append(f"accepted row records ABC unavailable for source CEC: {aid}")
        if cec.get((aid, "Sprime_vs_I"), {}).get("abc_available") != "true":
            errors.append(f"accepted row records ABC unavailable for cross CEC: {aid}")
        if cec.get((aid, "S_vs_Sprime"), {}).get("cec_status") != "equivalent":
            errors.append(f"accepted row lacks S-vs-S' ABC CEC: {aid}")
        if cec.get((aid, "Sprime_vs_I"), {}).get("cec_status") != "equivalent":
            errors.append(f"accepted row lacks S'-vs-I ABC CEC: {aid}")

    for row in tables["boundary_recovery.csv"]:
        if row["new_recovered_boundary"] != "true":
            continue
        aid = row["attempt_id"]
        if row["usable_frontier_anchor"] != "true" or row["selected_anchor"] != "true" or row["graph_active"] != "true":
            errors.append(f"boundary counted without selected graph-active anchor: {aid}")
        if cec.get((aid, "S_vs_Sprime"), {}).get("cec_status") != "equivalent":
            errors.append(f"boundary counted without source CEC: {aid}")
        if cec.get((aid, "Sprime_vs_I"), {}).get("cec_status") != "equivalent":
            errors.append(f"boundary counted without cross CEC: {aid}")
        if cec.get((aid, "S_vs_Sprime"), {}).get("abc_available") != "true" or cec.get((aid, "Sprime_vs_I"), {}).get("abc_available") != "true":
            errors.append(f"boundary counted with ABC unavailable evidence: {aid}")

    for row in tables["critical_path_utility.csv"]:
        if row["newly_resolved_critical_path_target"] == "true" and row["mapping_evidence"] != "formal_counterpart_and_global_cec":
            errors.append(f"critical path resolution lacks formal evidence: {row['attempt_id']}")

    for row in tables["durability_trajectories.csv"]:
        if row["usable_boundary"] == "true" and not (row["cec_status"] == "equivalent" and row["counterpart_present"] == "true" and row["graph_active"] == "true"):
            errors.append(f"durability claimed without active suffix checkpoint: {row['candidate_id']} {row['strategy']}")

    for row in tables["gf2_linear_baseline.csv"]:
        if row["backend"] != "gf2_linear_special_case":
            errors.append(f"unexpected GF2 backend label: {row['candidate_id']}")
        if row["status"] == "exact_affine_solution" and row["is_affine"] != "true":
            errors.append(f"GF2 solution without affine proof: {row['candidate_id']}")
        if row["status"] == "rejected_nonlinear" and row["is_affine"] == "true":
            errors.append(f"GF2 nonlinear rejection marked affine: {row['candidate_id']}")

    old = [r for r in tables["development_results.csv"] if r["source_result"] == "old_materialized_anchor"]
    if tables["development_results.csv"] and len(old) != 20:
        errors.append(f"expected 20 revisited materialized anchors, saw {len(old)}")
    for row in tables["development_results.csv"]:
        if not row["failure_reason"]:
            errors.append(f"real/development row lacks failure reason: {row['target_id']}")
        if row["new_recovered_boundary"] == "true":
            aid = f"{row['target_id']}__rewrite"
            if graph.get(aid, {}).get("graph_active") != "true":
                errors.append(f"real boundary claimed without graph activity: {row['target_id']}")

    raw_boundaries = sum(r["new_recovered_boundary"] == "true" for r in tables["boundary_recovery.csv"])
    controlled_boundaries = sum(r["new_recovered_boundary"] == "true" for r in tables["controlled_results.csv"])
    if raw_boundaries != controlled_boundaries:
        errors.append(f"boundary raw/controlled mismatch: {raw_boundaries} vs {controlled_boundaries}")
    if len(accepted) > len(positives):
        errors.append("accepted more controlled cases than positive controls")

    if errors:
        return _fail(errors)
    print(
        "Active source-counterpart results validated: "
        f"{len(old)} materialized anchors revisited, "
        f"{len(tables['target_candidates.csv'])} targets, "
        f"{len(accepted)} controlled active rewrites, "
        f"{sum(r['new_recovered_boundary'] == 'true' for r in tables['development_results.csv'])} real boundaries"
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
