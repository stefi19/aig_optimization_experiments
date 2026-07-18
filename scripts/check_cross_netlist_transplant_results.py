#!/usr/bin/env python3
"""Validate cross-netlist cut transplantation evidence."""

from __future__ import annotations

import argparse
import csv
import sys
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "results" / "cross_netlist_cut_transplantation"

REQUIRED = {
    "experiment_manifest.csv": {"git_head", "source_blind", "schema_version"},
    "environment.csv": {"tool", "version", "status"},
    "benchmark_split.csv": {"benchmark", "split", "source_blind", "heldout_locked_before_execution"},
    "target_candidates.csv": {"target_id", "candidate_id", "target_origin", "selected_for_attempt", "source_blind"},
    "region_pair_candidates.csv": {"candidate_id", "optimized_region", "source_region", "region_pair_status", "fingerprint"},
    "source_optimized_cuts.csv": {"candidate_id", "source_input_cut", "optimized_input_cut", "source_output_cut", "optimized_output_cut", "cut_status"},
    "input_adapter_queries.csv": {"adapter_id", "candidate_id", "existence_status", "solver_result", "proof_status", "counterexample_reproduced"},
    "input_adapter_counterexamples.csv": {"adapter_id", "candidate_id", "counterexample_reproduced"},
    "relational_interface_candidates.csv": {"candidate_id", "relational_mode", "proof_status"},
    "latent_interface_proofs.csv": {"candidate_id", "formal_status", "solver_result", "counterexample_reproduced"},
    "optimized_region_clones.csv": {"candidate_id", "region_clone_status", "cloned_target", "target_influence_status"},
    "output_adapter_queries.csv": {"adapter_id", "candidate_id", "existence_status", "solver_result", "proof_status", "counterexample_reproduced"},
    "output_adapter_counterexamples.csv": {"adapter_id", "candidate_id", "counterexample_reproduced"},
    "adapter_implementations.csv": {"adapter_id", "candidate_id", "adapter_kind", "implementation_status"},
    "adapter_proofs.csv": {"adapter_id", "candidate_id", "adapter_kind", "formal_status", "solver_result", "formal_evidence_level"},
    "graph_rewrite_plans.csv": {"attempt_id", "candidate_id", "rewrite_status", "whole_design_transplant"},
    "local_proof.csv": {"attempt_id", "candidate_id", "formal_status", "solver_result", "formal_evidence_level", "counterexample_reproduced"},
    "global_cec.csv": {"attempt_id", "candidate_id", "cec_scope", "abc_available", "cec_status"},
    "target_equivalence.csv": {"attempt_id", "candidate_id", "formal_status", "solver_result", "formal_evidence_level", "counterexample_reproduced"},
    "activity_validation.csv": {"attempt_id", "candidate_id", "graph_active", "functional_influence", "eout_depends_on_bi", "acceptance_status"},
    "boundary_recovery.csv": {"attempt_id", "candidate_id", "usable_frontier_anchor", "selected_anchor", "new_recovered_boundary", "graph_active", "global_cec_status"},
    "critical_path_utility.csv": {"attempt_id", "newly_resolved_critical_path_target", "mapping_evidence"},
    "durability.csv": {"attempt_id", "candidate_id", "strategy", "cec_status", "target_counterpart_present", "graph_active", "usable_boundary"},
    "oracle_diagnostics.csv": {"target_id", "oracle_mode", "localized_blocker", "source_blind_result_file_finalized_before_join"},
    "gaussian_baseline.csv": {"adapter_id", "backend", "linearity_status", "proof_status"},
    "baselines.csv": {"baseline", "benchmark_group", "attempted", "new_boundaries"},
    "ablations.csv": {"ablation", "attempted", "new_boundaries"},
    "controlled_results.csv": {"benchmark", "expected_outcome", "final_status", "input_adapter_status", "output_adapter_status", "source_cec_status", "cross_cec_status"},
    "development_results.csv": {"target_id", "source_failure_group", "candidate_status", "failure_stage", "failure_reason", "new_recovered_boundary"},
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
    for name, cols in REQUIRED.items():
        path = args.output_dir / name
        if not path.exists():
            errors.append(f"missing required file: {name}")
            continue
        with path.open(newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            rows = list(reader)
        tables[name] = rows
        missing = cols - set(reader.fieldnames or [])
        if missing:
            errors.append(f"{name} missing columns: {sorted(missing)}")
    if errors:
        return _fail(errors)

    abc_available = any(row["tool"] == "abc" and row["status"] == "available" for row in tables["environment.csv"])
    _unique(tables["region_pair_candidates.csv"], "candidate_id", "region_pair_candidates.csv", errors)
    _unique(tables["graph_rewrite_plans.csv"], "attempt_id", "graph_rewrite_plans.csv", errors)

    for table in ("benchmark_split.csv", "target_candidates.csv"):
        for row in tables[table]:
            if row.get("source_blind") != "true":
                errors.append(f"{table} contains non-blind inference row: {row.get('candidate_id', row.get('benchmark'))}")
    for row in tables["oracle_diagnostics.csv"]:
        if row["source_blind_result_file_finalized_before_join"] != "true":
            errors.append(f"oracle joined before blind result finalization: {row['target_id']}")

    for table in ("input_adapter_queries.csv", "output_adapter_queries.csv"):
        for row in tables[table]:
            if row["counterexample_available"] == "true" and row["counterexample_reproduced"] != "true":
                errors.append(f"{table} unreproduced counterexample: {row['adapter_id']}")
            if row["timeout"] == "true" and row["proof_status"] == "proven":
                errors.append(f"{table} timeout accepted as proof: {row['adapter_id']}")
    for table in ("input_adapter_counterexamples.csv", "output_adapter_counterexamples.csv"):
        for row in tables[table]:
            if row["counterexample_reproduced"] != "true":
                errors.append(f"{table} counterexample not reproduced: {row['adapter_id']}")

    local = {row["attempt_id"]: row for row in tables["local_proof.csv"]}
    target = {row["attempt_id"]: row for row in tables["target_equivalence.csv"]}
    activity = {row["attempt_id"]: row for row in tables["activity_validation.csv"]}
    graph = {row["attempt_id"]: row for row in tables["graph_rewrite_plans.csv"]}
    cec = {(row["attempt_id"], row["cec_scope"]): row for row in tables["global_cec.csv"]}
    boundaries = {row["attempt_id"]: row for row in tables["boundary_recovery.csv"]}

    accepted = [row for row in tables["controlled_results.csv"] if row["final_status"] == "accepted"]
    positive = [row for row in tables["controlled_results.csv"] if row["expected_outcome"].startswith("positive")]
    negative_accepted = [row for row in tables["controlled_results.csv"] if row["expected_outcome"].startswith("negative") and row["final_status"] == "accepted"]
    if negative_accepted:
        errors.extend(f"negative control accepted: {row['benchmark']}" for row in negative_accepted)
    if abc_available and not accepted and not args.allow_no_abc:
        errors.append("no controlled transplants accepted despite ABC availability")
    if len(accepted) != len(positive) and abc_available:
        errors.append(f"expected all positive controlled transplants to pass, saw {len(accepted)}/{len(positive)}")

    for row in accepted:
        aid = f"{row['benchmark']}__xplant__rewrite"
        if row["input_adapter_status"] != "adapter_exists" or row["output_adapter_status"] != "adapter_exists":
            errors.append(f"accepted without both adapters: {row['benchmark']}")
        if graph.get(aid, {}).get("rewrite_status") != "valid":
            errors.append(f"accepted without valid graph rewrite: {aid}")
        if graph.get(aid, {}).get("whole_design_transplant") == "true":
            errors.append(f"accepted whole-design transplant: {aid}")
        if local.get(aid, {}).get("formal_status") != "equivalent":
            errors.append(f"accepted without local equivalence proof: {aid}")
        if target.get(aid, {}).get("formal_status") != "proven_counterpart_equivalent":
            errors.append(f"accepted without target equivalence proof: {aid}")
        act = activity.get(aid, {})
        if act.get("graph_active") != "true" or act.get("functional_influence") != "true" or act.get("eout_depends_on_bi") != "true":
            errors.append(f"accepted without graph-active dependent Eout: {aid}")
        if abc_available:
            if cec.get((aid, "S_vs_Sprime"), {}).get("cec_status") != "equivalent":
                errors.append(f"accepted without S-vs-Sprime CEC: {aid}")
            if cec.get((aid, "Sprime_vs_I"), {}).get("cec_status") != "equivalent":
                errors.append(f"accepted without Sprime-vs-I CEC: {aid}")
        b = boundaries.get(aid, {})
        if b.get("new_recovered_boundary") != "true" or b.get("selected_anchor") != "true" or b.get("graph_active") != "true":
            errors.append(f"accepted without boundary recovery row: {aid}")

    for row in tables["boundary_recovery.csv"]:
        if row["new_recovered_boundary"] != "true":
            continue
        aid = row["attempt_id"]
        act = activity.get(aid, {})
        if row["usable_frontier_anchor"] != "true" or row["selected_anchor"] != "true" or row["graph_active"] != "true":
            errors.append(f"boundary counted without selected graph-active anchor: {aid}")
        if act.get("eout_depends_on_bi") != "true":
            errors.append(f"boundary counted although output adapter ignores cloned region: {aid}")
        if abc_available and (
            cec.get((aid, "S_vs_Sprime"), {}).get("cec_status") != "equivalent"
            or cec.get((aid, "Sprime_vs_I"), {}).get("cec_status") != "equivalent"
        ):
            errors.append(f"boundary counted without both global CEC proofs: {aid}")

    for row in tables["critical_path_utility.csv"]:
        if row["newly_resolved_critical_path_target"] == "true" and row["mapping_evidence"] != "formal_transplant_and_global_cec":
            errors.append(f"critical-path claim lacks formal transplant evidence: {row['attempt_id']}")
    for row in tables["durability.csv"]:
        if row["usable_boundary"] == "true" and not (
            row["cec_status"] == "equivalent" and row["target_counterpart_present"] == "true" and row["graph_active"] == "true"
        ):
            errors.append(f"durability claim without equivalent active checkpoint: {row['candidate_id']} {row['strategy']}")
    for row in tables["gaussian_baseline.csv"]:
        if row["backend"] != "gf2_linear_relational_baseline":
            errors.append(f"unexpected GF2 backend label: {row['adapter_id']}")
        if row["proof_status"] == "proved" and row["linearity_status"] != "proved_affine":
            errors.append(f"GF2 proof without affine linearity proof: {row['adapter_id']}")
        if row["linearity_status"] == "rejected_nonlinear" and row["proof_status"] == "proved":
            errors.append(f"nonlinear adapter accepted by GF2 baseline: {row['adapter_id']}")

    development = tables["development_results.csv"]
    failures = Counter(row["source_failure_group"] for row in development)
    if development and failures.get("no_globally_anchored_cut", 0) != 36:
        errors.append(f"expected 36 no_globally_anchored_cut revisits, saw {failures.get('no_globally_anchored_cut', 0)}")
    if development and failures.get("no_relevant_source_consumer_window_under_bounds", 0) != 20:
        errors.append(f"expected 20 no_relevant_source_consumer_window_under_bounds revisits, saw {failures.get('no_relevant_source_consumer_window_under_bounds', 0)}")
    for row in development:
        if row["new_recovered_boundary"] == "true":
            errors.append(f"real result unexpectedly claims a recovered boundary without committed proof stack: {row['target_id']}")
        if not row["failure_stage"] or not row["failure_reason"]:
            errors.append(f"real revisit lacks failure taxonomy: {row['target_id']}")

    if errors:
        return _fail(errors)

    print(
        "Cross-netlist cut transplantation results validated: "
        f"{len(tables['target_candidates.csv'])} targets, "
        f"{len(positive)} positive controls, "
        f"{len(accepted)} controlled accepted, "
        f"{len(development)} real failures revisited, "
        f"{sum(r['new_recovered_boundary'] == 'true' for r in development)} real boundaries"
    )
    return 0


def _unique(rows: list[dict[str, str]], key: str, table: str, errors: list[str]) -> None:
    seen: set[str] = set()
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
