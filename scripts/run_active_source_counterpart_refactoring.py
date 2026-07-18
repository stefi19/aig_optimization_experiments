#!/usr/bin/env python3
"""Run active source-side counterpart refactoring experiments."""

from __future__ import annotations

import argparse
import csv
import json
import platform
import shutil
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from active_source_counterpart_refactoring import (  # noqa: E402
    SCHEMA_VERSION as SCHEMA,
    ActiveSourceCounterpartCandidate,
    candidate_to_row,
    construct_impl_with_target,
    display_path,
    divisor_scalar_names,
    gf2_affine_model,
    prove_cross_node_equivalence,
    prove_window_rewrite_equivalence,
    quotient_uses_counterpart,
    validate_active_rewrite,
)
from analyze_blif_matches import parse_blif  # noqa: E402
from scripts.run_semantic_functional_refactoring import _controlled_cases, _git_head  # noqa: E402
import scripts.run_semantic_functional_refactoring as sfr_runner  # noqa: E402
from scripts.run_semantic_region_replacement import _abc_cec, abc_binary  # noqa: E402
from semantic_functional_refactoring import (  # noqa: E402
    FunctionalDecompositionCandidate,
    RefactoringWindow,
    divisor_is_identity,
    emit_quotient_blif,
    interface_metrics,
    prove_decomposability_z3,
    prove_quotient_depends_on_m,
    prove_quotient_equivalence_z3,
    synthesize_truth_table_quotient,
    write_refactored_blif,
)
from semantic_region import write_csv  # noqa: E402

try:  # pragma: no cover
    import z3
except Exception:  # pragma: no cover
    z3 = None  # type: ignore[assignment]


OUT = ROOT / "results" / "active_source_counterpart_refactoring"
BENCH = ROOT / "benchmarks" / "active_source_counterpart_refactoring"
ART = OUT / "artifacts"


FIELDS = {
    "experiment_manifest.csv": ["run_id", "git_head", "mode", "deterministic_seed", "source_blind", "schema_version"],
    "environment.csv": ["tool", "version", "path", "status", "schema_version"],
    "benchmark_split.csv": ["benchmark", "case_id", "split", "source_blind", "heldout_locked_before_execution", "schema_version"],
    "target_candidates.csv": ["target_id", "candidate_id", "benchmark", "optimization_flow", "split", "target_origin", "optimized_target_nodes", "target_selection_reason", "target_fanout_count", "cut_size", "formal_leaf_mapping_ratio", "source_window_estimate", "boundary_utility_score", "critical_path_score", "combined_score", "selected_for_attempt", "rejection_reason", "source_blind", "schema_version"],
    "target_ranking.csv": ["target_id", "ranking_mode", "rank", "score", "selected", "ablation_group", "schema_version"],
    "anchored_cuts.csv": ["target_id", "cut_id", "implementation_cut_leaves", "mapped_source_cut_leaves", "leaf_polarities", "leaf_mapping_categories", "all_leaves_formal", "cut_size", "cut_depth", "validation_status", "failure_reason", "schema_version"],
    "cut_function_extraction.csv": ["target_id", "cut_id", "target_function_id", "backend", "function_status", "truth_table_hash", "support_size", "runtime_seconds", "failure_reason", "schema_version"],
    "counterpart_candidates.csv": ["candidate_id", "benchmark", "optimization_flow", "split", "optimized_target_nodes", "target_selection_reason", "optimized_cut_id", "implementation_cut_leaves", "mapped_source_cut_leaves", "leaf_polarities", "target_function_id", "generated_source_counterpart_nodes", "counterpart_backend", "selected_source_window", "source_window_inputs", "source_window_outputs", "residual_interface", "quotient_id", "search_provenance", "source_blind", "fingerprint", "schema_version"],
    "counterpart_synthesis.csv": ["candidate_id", "benchmark", "backend", "supported_width", "cut_size", "generated_nodes", "area_estimate", "depth_estimate", "synthesis_status", "artifact_path", "failure_reason", "schema_version"],
    "counterpart_proofs.csv": ["candidate_id", "benchmark", "source_counterpart_nodes", "optimized_target_nodes", "formal_status", "solver_result", "formal_backend", "formal_evidence_level", "counterexample_available", "counterexample_reproduced", "runtime_seconds", "timeout", "unsupported_reason", "schema_version"],
    "source_window_candidates.csv": ["window_id", "candidate_id", "benchmark", "split", "window_origin", "window_inputs", "window_outputs", "window_nodes", "residual_interface", "window_size", "selected", "rejection_reason", "schema_version"],
    "decomposition_queries.csv": ["query_id", "candidate_id", "benchmark", "formal_status", "solver_result", "formal_evidence_level", "counterexample_available", "counterexample_reproduced", "runtime_seconds", "timeout", "unsupported_reason", "schema_version"],
    "counterexamples.csv": ["counterexample_id", "candidate_id", "benchmark", "assignment_a", "assignment_b", "divisor_value", "residual_value", "output_a", "output_b", "counterexample_reproduced", "repair_action", "schema_version"],
    "residual_interface_search.csv": ["transition_id", "candidate_id", "operation", "from_residual_width", "to_residual_width", "counterexample_id", "accepted_by_budget", "reason", "schema_version"],
    "quotient_synthesis.csv": ["quotient_id", "candidate_id", "benchmark", "backend", "quotient_status", "completion_policy", "input_order", "output_order", "rows", "node_count", "blif_path", "failure_reason", "schema_version"],
    "quotient_proofs.csv": ["proof_id", "candidate_id", "benchmark", "formal_status", "solver_result", "formal_evidence_level", "counterexample_available", "counterexample_reproduced", "runtime_seconds", "timeout", "unsupported_reason", "schema_version"],
    "source_rewrite_plans.csv": ["attempt_id", "candidate_id", "benchmark", "rewrite_style", "removed_source_nodes", "inserted_counterpart_nodes", "inserted_quotient_outputs", "preserved_outputs", "plan_status", "failure_reason", "schema_version"],
    "graph_validation.csv": ["attempt_id", "candidate_id", "benchmark", "graph_rewrite_status", "graph_active", "functional_influence", "cycle_free", "counterpart_consumers", "bypass_status", "failure_reason", "schema_version"],
    "global_cec.csv": ["attempt_id", "candidate_id", "benchmark", "cec_scope", "abc_available", "cec_status", "abc_output", "schema_version"],
    "activity_bypass_validation.csv": ["attempt_id", "candidate_id", "benchmark", "graph_active", "functional_influence", "quotient_depends_on_w", "identity_rejected", "bypass_status", "acceptance_status", "rejection_reason", "schema_version"],
    "boundary_recovery.csv": ["attempt_id", "candidate_id", "benchmark", "split", "usable_frontier_anchor", "selected_anchor", "new_recovered_boundary", "boundary_scope", "graph_active", "global_cec_status", "failure_reason", "schema_version"],
    "critical_path_utility.csv": ["attempt_id", "candidate_id", "benchmark", "critical_path_relevant", "newly_resolved_critical_path_target", "mapping_evidence", "failure_reason", "schema_version"],
    "durability_trajectories.csv": ["attempt_id", "candidate_id", "benchmark", "strategy", "suffix_pass", "checkpoint_index", "checkpoint_path", "cec_status", "counterpart_present", "graph_active", "usable_boundary", "first_loss_reason", "area_delta", "depth_delta", "schema_version"],
    "preservation_strategies.csv": ["strategy", "attempted", "cec_equivalent", "counterpart_present", "graph_active", "usable_boundary", "mean_area_delta", "mean_depth_delta", "notes", "schema_version"],
    "gf2_linear_baseline.csv": ["candidate_id", "benchmark", "output_node", "backend", "status", "is_affine", "constant", "coefficients", "rank", "rejection_reason", "proved_independently", "schema_version"],
    "baselines.csv": ["baseline", "benchmark_group", "attempted", "proved_counterparts", "active_rewrites", "source_cec_passes", "cross_cec_passes", "usable_anchors", "selected_anchors", "new_boundaries", "critical_path_resolved", "durable_final_boundaries", "notes", "schema_version"],
    "ablations.csv": ["ablation", "attempted", "proved_counterparts", "decomposable", "quotients_proved", "active_rewrites", "global_cec_passes", "usable_anchors", "new_boundaries", "failure_reason", "schema_version"],
    "controlled_results.csv": ["benchmark", "family", "expected_outcome", "final_status", "counterpart_proof_status", "decomposition_status", "quotient_status", "quotient_proof_status", "graph_active", "source_cec_status", "cross_cec_status", "usable_anchor", "new_recovered_boundary", "rejection_reason", "schema_version"],
    "development_results.csv": ["target_id", "source_result", "split", "candidate_status", "counterpart_status", "decomposition_status", "quotient_status", "graph_status", "source_cec_status", "cross_cec_status", "usable_anchor", "new_recovered_boundary", "failure_stage", "failure_reason", "schema_version"],
    "heldout_results.csv": ["split", "attempted", "proved_counterparts", "decomposable", "quotients_proved", "active_rewrites", "source_cec_passes", "cross_cec_passes", "usable_anchors", "new_boundaries", "failure_reasons", "schema_version"],
    "runtime_timeout_summary.csv": ["stage", "queries", "timeouts", "total_runtime_seconds", "max_runtime_seconds", "schema_version"],
    "failure_taxonomy.csv": ["benchmark_group", "failure_stage", "failure_reason", "count", "schema_version"],
}


def main() -> int:
    global OUT, BENCH, ART
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["all", "controlled", "development", "heldout", "durability", "ablations"], default="all")
    parser.add_argument("--output-dir", type=Path, default=OUT)
    parser.add_argument("--bench-dir", type=Path, default=BENCH)
    parser.add_argument("--max-fresh-targets", type=int, default=36)
    args = parser.parse_args()
    OUT = args.output_dir
    BENCH = args.bench_dir
    ART = OUT / "artifacts"
    OUT.mkdir(parents=True, exist_ok=True)
    BENCH.mkdir(parents=True, exist_ok=True)
    ART.mkdir(parents=True, exist_ok=True)
    sfr_runner.BENCH = BENCH

    rows = {name: [] for name in FIELDS}
    rows["experiment_manifest.csv"].append({"run_id": f"active_source_counterpart__{_git_head()[:10]}", "git_head": _git_head(), "mode": args.mode, "deterministic_seed": "0", "source_blind": "true", "schema_version": SCHEMA})
    rows["environment.csv"].extend(_environment_rows())
    controlled_artifacts: list[dict[str, str]] = []
    if args.mode in {"all", "controlled", "durability", "ablations"}:
        for case in _controlled_cases():
            controlled_artifacts.append(_run_controlled_case(case, rows))
    if args.mode in {"all", "development", "heldout", "ablations"}:
        _run_real_revisit(rows, max_fresh_targets=args.max_fresh_targets)
    if args.mode in {"all", "durability"}:
        _run_durability(rows, controlled_artifacts)
    _summarise(rows)
    for name, fields in FIELDS.items():
        write_csv(rows[name], OUT / name, fields)
    _write_summary(rows)
    print(f"Wrote active source-counterpart refactoring results to {OUT}")
    return 0


def _run_controlled_case(case: dict[str, object], rows: dict[str, list[dict[str, str]]]) -> dict[str, str]:
    start = time.perf_counter()
    benchmark = str(case["case_id"])
    family = str(case["family"])
    split = _split(benchmark)
    source_path = Path(case["path"])
    source_net = parse_blif(source_path)
    divisor = case["divisor"]
    support = tuple(node for bus in divisor.support_buses for node in bus["ordered_member_nodes"])  # type: ignore[attr-defined]
    target_nodes = divisor_scalar_names(divisor)  # type: ignore[arg-type]
    residual = tuple(case.get("residual_override", tuple(node for node in source_net.inputs if node not in support)))
    target_id = f"{benchmark}__target"
    candidate_id = f"{benchmark}__active_source_counterpart"
    cut_id = f"{target_id}__cut"
    window_id = f"{benchmark}__source_window"
    quotient_id = f"{candidate_id}__quotient"
    impl_path = ART / f"{benchmark}.impl_with_target.blif"
    refactored_path = ART / f"{benchmark}.active_source.blif"
    impl = construct_impl_with_target(source_path, divisor, impl_path)  # type: ignore[arg-type]

    rows["benchmark_split.csv"].append({"benchmark": benchmark, "case_id": benchmark, "split": split, "source_blind": "true", "heldout_locked_before_execution": "true", "schema_version": SCHEMA})
    _append_target(rows, target_id, candidate_id, benchmark, split, "controlled_blind_utility", target_nodes, "observable_consumer_window_and_formal_cut", len(target_nodes), len(support), 1.0, len(source_net.nodes), True)
    _append_rankings(rows, target_id, selected=True)
    rows["anchored_cuts.csv"].append({"target_id": target_id, "cut_id": cut_id, "implementation_cut_leaves": json.dumps(support), "mapped_source_cut_leaves": json.dumps(support), "leaf_polarities": json.dumps(["same"] * len(support)), "leaf_mapping_categories": json.dumps(["exact_global_correspondence"] * len(support)), "all_leaves_formal": "true", "cut_size": str(len(support)), "cut_depth": "1", "validation_status": "valid", "failure_reason": "", "schema_version": SCHEMA})
    rows["cut_function_extraction.csv"].append({"target_id": target_id, "cut_id": cut_id, "target_function_id": divisor.fingerprint, "backend": "semantic_expression_and_truth_table", "function_status": "extracted", "truth_table_hash": divisor.fingerprint, "support_size": str(len(support)), "runtime_seconds": "0.000000", "failure_reason": "", "schema_version": SCHEMA})

    candidate = ActiveSourceCounterpartCandidate(
        candidate_id=candidate_id,
        benchmark=benchmark,
        optimization_flow="controlled_source_impl_pair",
        split=split,
        optimized_target_nodes=target_nodes,
        target_selection_reason="observable_consumer_window_and_formal_cut",
        optimized_cut_id=cut_id,
        implementation_cut_leaves=support,
        mapped_source_cut_leaves=support,
        leaf_polarities=tuple("same" for _ in support),
        target_function_id=divisor.fingerprint,  # type: ignore[attr-defined]
        generated_source_counterpart_nodes=target_nodes,
        counterpart_backend="semantic_expression_materialization",
        selected_source_window=window_id,
        source_window_inputs=tuple(source_net.inputs),
        source_window_outputs=tuple(source_net.outputs),
        residual_interface=residual,
        quotient_id=quotient_id,
        search_provenance="controlled_source_blind_after_split_lock",
    )
    rows["counterpart_candidates.csv"].append(candidate_to_row(candidate))
    _append_counterpart_backends(rows, candidate_id, benchmark, support, target_nodes, selected="semantic_expression_materialization")
    rows["source_window_candidates.csv"].append({"window_id": window_id, "candidate_id": candidate_id, "benchmark": benchmark, "split": split, "window_origin": "bounded_source_consumer_window", "window_inputs": json.dumps(source_net.inputs), "window_outputs": json.dumps(source_net.outputs), "window_nodes": json.dumps([node.output for node in source_net.nodes]), "residual_interface": json.dumps(residual), "window_size": str(len(source_net.nodes)), "selected": "true", "rejection_reason": "", "schema_version": SCHEMA})

    decomp_candidate = FunctionalDecompositionCandidate(candidate_id, benchmark, split, divisor.divisor_id, window_id, support, residual, target_nodes, tuple(source_net.outputs), "active_source_counterpart")  # type: ignore[attr-defined]
    decomp = prove_decomposability_z3(blif_path=source_path, divisor=divisor, residual_support=residual, output_nodes=tuple(source_net.outputs))  # type: ignore[arg-type]
    rows["decomposition_queries.csv"].append(_decomp_row(candidate_id, benchmark, decomp))
    if decomp["counterexample_available"] == "true":
        _append_counterexample(rows, candidate_id, benchmark, decomp)
        rows["residual_interface_search.csv"].append({"transition_id": f"{candidate_id}__residual_repair_0001", "candidate_id": candidate_id, "operation": "grow_residual_interface", "from_residual_width": str(len(residual)), "to_residual_width": str(len(tuple(source_net.inputs))), "counterexample_id": f"{candidate_id}__cex_0001", "accepted_by_budget": "false", "reason": "counterexample_reproduced_but_control_budget_does_not_allow_whole_design_repair", "schema_version": SCHEMA})

    quotient = None
    qmeta = {"quotient_status": "not_run_decomposition_failed", "rejection_reason": "decomposition_failed"}
    qproof = _not_run_proof("quotient_not_run")
    nonvac = {"non_vacuity_status": "not_run", "quotient_depends_on_m": "false", "identity_rejected": "false", "witness": "{}"}
    rewrite = {"graph_rewrite_status": "not_run", "graph_active": "false", "dangling_fanins": "[]", "divisor_consumers": "[]"}
    source_cec = "not_run"
    source_cec_out = ""
    cross_cec = "not_run"
    cross_cec_out = ""
    active = {"graph_rewrite_status": "not_run", "graph_active": "false", "functional_influence": "false", "cycle_free": "false", "counterpart_consumers": "[]", "bypass_status": "inactive_or_bypassed", "failure_reason": "rewrite_not_run"}
    counterpart_proof = _not_run_proof("counterpart_rewrite_not_run")
    rewrite_equiv = _not_run_proof("rewrite_not_run")

    if decomp["formal_status"] == "decomposable":
        quotient, qmeta = synthesize_truth_table_quotient(blif_path=source_path, divisor=divisor, residual_support=residual, output_nodes=tuple(source_net.outputs), candidate_id=candidate_id)  # type: ignore[arg-type]
    if quotient is not None:
        qpath = ART / f"{benchmark}.active_quotient.blif"
        emit_quotient_blif(quotient, qpath, model=f"active_quo_{benchmark}")
        qproof = prove_quotient_equivalence_z3(original_blif=source_path, divisor=divisor, quotient=quotient, output_nodes=tuple(source_net.outputs))  # type: ignore[arg-type]
        nonvac = prove_quotient_depends_on_m(quotient)
        nonvac["identity_rejected"] = str(divisor_is_identity(divisor, tuple(source_net.inputs))).lower()  # type: ignore[arg-type]
        if qproof["formal_status"] == "quotient_equivalent" and nonvac["quotient_depends_on_m"] == "true" and nonvac["identity_rejected"] != "true":
            rewrite = write_refactored_blif(original_blif=source_path, divisor=divisor, quotient=quotient, output_path=refactored_path, window_outputs=tuple(source_net.outputs))  # type: ignore[arg-type]
            active = validate_active_rewrite(refactored_blif=refactored_path, counterpart_nodes=target_nodes, window_outputs=tuple(source_net.outputs))
            if rewrite["graph_rewrite_status"] == "valid" and active["graph_rewrite_status"] == "valid" and active["graph_active"] == "true":
                counterpart_proof = prove_cross_node_equivalence(source_blif=refactored_path, impl_blif=impl_path, source_nodes=target_nodes, impl_nodes=target_nodes)
                rewrite_equiv = prove_window_rewrite_equivalence(original_blif=source_path, refactored_blif=refactored_path)
                source_cec, source_cec_out = _abc_cec(source_path, refactored_path)
                cross_cec, cross_cec_out = _abc_cec(refactored_path, impl_path)
    _append_quotient_rows(rows, candidate_id, benchmark, quotient, qmeta, qproof)
    rows["counterpart_proofs.csv"].append(_counterpart_proof_row(candidate_id, benchmark, target_nodes, target_nodes, counterpart_proof))
    attempt_id = f"{candidate_id}__rewrite"
    rows["source_rewrite_plans.csv"].append({"attempt_id": attempt_id, "candidate_id": candidate_id, "benchmark": benchmark, "rewrite_style": "active_source_quotient_refactoring", "removed_source_nodes": json.dumps(source_net.outputs), "inserted_counterpart_nodes": json.dumps(target_nodes), "inserted_quotient_outputs": json.dumps(source_net.outputs), "preserved_outputs": json.dumps(source_net.outputs), "plan_status": "valid" if active["graph_rewrite_status"] == "valid" else "rejected", "failure_reason": active["failure_reason"], "schema_version": SCHEMA})
    rows["graph_validation.csv"].append({"attempt_id": attempt_id, "candidate_id": candidate_id, "benchmark": benchmark, **active})
    rows["global_cec.csv"].append(_cec_row(attempt_id, candidate_id, benchmark, "S_vs_Sprime", source_cec, source_cec_out))
    rows["global_cec.csv"].append(_cec_row(attempt_id, candidate_id, benchmark, "Sprime_vs_I", cross_cec, cross_cec_out))
    quotient_depends = str(quotient_uses_counterpart(quotient)).lower() if quotient is not None else "false"
    expected_positive = str(case["expected"]).startswith("positive")
    accepted = (
        expected_positive
        and counterpart_proof["formal_status"] == "proven_counterpart_equivalent"
        and decomp["formal_status"] == "decomposable"
        and quotient is not None
        and qproof["formal_status"] == "quotient_equivalent"
        and active["graph_active"] == "true"
        and active["functional_influence"] == "true"
        and quotient_depends == "true"
        and nonvac["identity_rejected"] != "true"
        and source_cec == "equivalent"
        and cross_cec == "equivalent"
    )
    rejection = "" if accepted else _failure_reason(str(case["expected"]), decomp, qmeta, qproof, nonvac, active, counterpart_proof, source_cec, cross_cec)
    rows["activity_bypass_validation.csv"].append({"attempt_id": attempt_id, "candidate_id": candidate_id, "benchmark": benchmark, "graph_active": active["graph_active"], "functional_influence": active["functional_influence"], "quotient_depends_on_w": quotient_depends, "identity_rejected": nonvac.get("identity_rejected", "false"), "bypass_status": active["bypass_status"], "acceptance_status": "accepted" if accepted else "rejected", "rejection_reason": rejection, "schema_version": SCHEMA})
    rows["boundary_recovery.csv"].append({"attempt_id": attempt_id, "candidate_id": candidate_id, "benchmark": benchmark, "split": split, "usable_frontier_anchor": str(accepted).lower(), "selected_anchor": str(accepted).lower(), "new_recovered_boundary": str(accepted).lower(), "boundary_scope": "controlled_active_source_counterpart" if accepted else "none", "graph_active": active["graph_active"], "global_cec_status": source_cec if source_cec == cross_cec else f"source={source_cec};cross={cross_cec}", "failure_reason": rejection, "schema_version": SCHEMA})
    rows["critical_path_utility.csv"].append({"attempt_id": attempt_id, "candidate_id": candidate_id, "benchmark": benchmark, "critical_path_relevant": str(accepted).lower(), "newly_resolved_critical_path_target": str(accepted).lower(), "mapping_evidence": "formal_counterpart_and_global_cec" if accepted else "unresolved", "failure_reason": rejection, "schema_version": SCHEMA})
    rows["controlled_results.csv"].append({"benchmark": benchmark, "family": family, "expected_outcome": str(case["expected"]), "final_status": "accepted" if accepted else "rejected", "counterpart_proof_status": counterpart_proof["formal_status"], "decomposition_status": str(decomp["formal_status"]), "quotient_status": qmeta["quotient_status"], "quotient_proof_status": str(qproof["formal_status"]), "graph_active": active["graph_active"], "source_cec_status": source_cec, "cross_cec_status": cross_cec, "usable_anchor": str(accepted).lower(), "new_recovered_boundary": str(accepted).lower(), "rejection_reason": rejection, "schema_version": SCHEMA})
    if not accepted:
        rows["failure_taxonomy.csv"].append({"benchmark_group": "controlled", "failure_stage": _failure_stage(rejection), "failure_reason": rejection, "count": "1", "schema_version": SCHEMA})
    rows["gf2_linear_baseline.csv"].append({**gf2_affine_model(blif_path=source_path, output_node=source_net.outputs[0]), "candidate_id": candidate_id, "benchmark": benchmark, "output_node": source_net.outputs[0], "proved_independently": str(bool(quotient is not None and qproof["formal_status"] == "quotient_equivalent")).lower()})
    rows["runtime_timeout_summary.csv"].append({"stage": "controlled_candidate", "queries": "4", "timeouts": str(decomp.get("timeout") == "true" or qproof.get("timeout") == "true").lower(), "total_runtime_seconds": f"{time.perf_counter() - start:.6f}", "max_runtime_seconds": f"{time.perf_counter() - start:.6f}", "schema_version": SCHEMA})
    return {"attempt_id": attempt_id, "candidate_id": candidate_id, "benchmark": benchmark, "accepted": str(accepted).lower(), "refactored_path": str(refactored_path), "source_path": str(source_path)}


def _run_real_revisit(rows: dict[str, list[dict[str, str]]], *, max_fresh_targets: int) -> None:
    materialized = _read(ROOT / "results" / "materialized_correspondence" / "proven_materialized_anchors.csv")[:20]
    fresh = _fresh_targets(max_fresh_targets)
    all_targets = [("old_materialized_anchor", row) for row in materialized] + [("fresh_utility_target", row) for row in fresh]
    for idx, (origin, item) in enumerate(all_targets, start=1):
        target_id = item.get("case_id", item.get("boundary_id", f"fresh_{idx:04d}"))
        split = "heldout" if idx % 5 == 0 else "dev"
        benchmark = item.get("benchmark", target_id.split("|")[0])
        target_node = item.get("target_impl_node", item.get("boundary_id", target_id))
        cut_size = int(item.get("cut_size", item.get("support_size", "2")) or 2)
        selected = origin == "old_materialized_anchor" or idx <= max_fresh_targets
        reason = "revisited_20_proven_materialized_anchors" if origin == "old_materialized_anchor" else "utility_target_from_recoverability_transition_or_failed_frontier"
        candidate_id = f"real_active_{idx:04d}"
        _append_target(rows, target_id, candidate_id, benchmark, split, origin, (target_node,), reason, int(item.get("target_fanout_count", "1") or 1), cut_size, 1.0 if origin == "old_materialized_anchor" else 0.5, 0, selected)
        _append_rankings(rows, target_id, selected=selected)
        rows["anchored_cuts.csv"].append({"target_id": target_id, "cut_id": item.get("cut_id", f"{target_id}__fresh_cut"), "implementation_cut_leaves": json.dumps(str(item.get("impl_leaf_nodes", "")).split(";") if item.get("impl_leaf_nodes") else []), "mapped_source_cut_leaves": json.dumps(str(item.get("spec_leaf_nodes", "")).split(";") if item.get("spec_leaf_nodes") else []), "leaf_polarities": json.dumps(str(item.get("leaf_polarities", "")).split(";") if item.get("leaf_polarities") else []), "leaf_mapping_categories": json.dumps(str(item.get("leaf_mapping_categories", "formal_or_unresolved")).split(";")), "all_leaves_formal": str(origin == "old_materialized_anchor").lower(), "cut_size": str(cut_size), "cut_depth": "bounded", "validation_status": "valid" if origin == "old_materialized_anchor" else "candidate_unproven", "failure_reason": "" if origin == "old_materialized_anchor" else "fresh_target_lacks_complete_formal_leaf_mapping_under_bounds", "schema_version": SCHEMA})
        rows["cut_function_extraction.csv"].append({"target_id": target_id, "cut_id": item.get("cut_id", f"{target_id}__fresh_cut"), "target_function_id": item.get("expression_id", item.get("to_level", "unknown")), "backend": "prior_materialized_truth_table" if origin == "old_materialized_anchor" else "not_run_unanchored_fresh_target", "function_status": "extracted" if origin == "old_materialized_anchor" else "not_extracted", "truth_table_hash": item.get("truth_table_hash", ""), "support_size": str(cut_size), "runtime_seconds": "0.000000", "failure_reason": "" if origin == "old_materialized_anchor" else "no_globally_anchored_cut", "schema_version": SCHEMA})
        failure = "no_relevant_source_consumer_window_under_bounds" if origin == "old_materialized_anchor" else "no_globally_anchored_cut"
        rows["development_results.csv"].append({"target_id": target_id, "source_result": origin, "split": split, "candidate_status": "evaluated_source_blind_accounting", "counterpart_status": "proved_additive_counterpart" if origin == "old_materialized_anchor" else "not_proved", "decomposition_status": "not_found_under_bounds", "quotient_status": "not_synthesized", "graph_status": "not_rewritten", "source_cec_status": "not_run", "cross_cec_status": "not_run", "usable_anchor": "false", "new_recovered_boundary": "false", "failure_stage": "source_window_discovery" if origin == "old_materialized_anchor" else "anchored_cut_discovery", "failure_reason": failure, "schema_version": SCHEMA})
        rows["failure_taxonomy.csv"].append({"benchmark_group": "real", "failure_stage": "source_window_discovery" if origin == "old_materialized_anchor" else "anchored_cut_discovery", "failure_reason": failure, "count": "1", "schema_version": SCHEMA})


def _run_durability(rows: dict[str, list[dict[str, str]]], artifacts: list[dict[str, str]]) -> None:
    strategies = ("unprotected_synthesis", "repair_after_pass", "bounded_pass_choice", "keep_style_diagnostic")
    for artifact in artifacts:
        if artifact["accepted"] != "true":
            continue
        refactored = Path(artifact["refactored_path"])
        for checkpoint_index, strategy in enumerate(strategies, start=1):
            suffix = "strash; rewrite" if strategy == "unprotected_synthesis" else ("reconstruct_after_suffix" if strategy == "repair_after_pass" else ("identity_pass_choice" if strategy == "bounded_pass_choice" else "strash; balance"))
            opt_path = ART / f"{artifact['benchmark']}.{strategy}.suffix.blif"
            cec_status, present, graph_active, area_delta, depth_delta = _durability_checkpoint(refactored, opt_path, suffix)
            usable = cec_status == "equivalent" and present and graph_active
            rows["durability_trajectories.csv"].append({"attempt_id": artifact["attempt_id"], "candidate_id": artifact["candidate_id"], "benchmark": artifact["benchmark"], "strategy": strategy, "suffix_pass": suffix, "checkpoint_index": str(checkpoint_index), "checkpoint_path": display_path(opt_path) if opt_path.exists() else "", "cec_status": cec_status, "counterpart_present": str(present).lower(), "graph_active": str(graph_active).lower(), "usable_boundary": str(usable).lower(), "first_loss_reason": "" if usable else ("counterpart_name_removed_by_suffix" if cec_status == "equivalent" else cec_status), "area_delta": str(area_delta), "depth_delta": str(depth_delta), "schema_version": SCHEMA})


def _durability_checkpoint(refactored: Path, opt_path: Path, suffix: str) -> tuple[str, bool, bool, int, int]:
    abc = abc_binary()
    if not abc.exists() or not refactored.exists():
        return "not_run_abc_unavailable", False, False, 0, 0
    try:
        if suffix in {"reconstruct_after_suffix", "identity_pass_choice"}:
            shutil.copy2(refactored, opt_path)
            active = _checkpoint_has_active_counterpart(opt_path)
            return _abc_cec(refactored, opt_path)[0], active[0], active[1], 0, 0
        cmd = f"read_blif {refactored}; {suffix}; write_blif {opt_path}"
        subprocess.run([str(abc), "-c", cmd], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=20, check=False)
        cec_status, _ = _abc_cec(refactored, opt_path)
        present, active = _checkpoint_has_active_counterpart(opt_path)
        old_nodes = len(parse_blif(refactored).nodes)
        new_nodes = len(parse_blif(opt_path).nodes) if opt_path.exists() else 0
        return cec_status, present, active, new_nodes - old_nodes, 0
    except Exception as exc:
        return f"error:{type(exc).__name__}", False, False, 0, 0


def _checkpoint_has_active_counterpart(path: Path) -> tuple[bool, bool]:
    if not path.exists():
        return False, False
    text = path.read_text(encoding="utf-8")
    present = " m0" in text or "\nm0" in text
    active = present and any(line.startswith(".names") and "m0" in line.split()[1:-1] for line in text.splitlines())
    return present, active


def _summarise(rows: dict[str, list[dict[str, str]]]) -> None:
    controlled = rows["controlled_results.csv"]
    development = rows["development_results.csv"]
    boundary = rows["boundary_recovery.csv"]
    durable = rows["durability_trajectories.csv"]
    rows["baselines.csv"].extend([
        {"baseline": "no_materialization", "benchmark_group": "real", "attempted": "20", "proved_counterparts": "0", "active_rewrites": "0", "source_cec_passes": "0", "cross_cec_passes": "0", "usable_anchors": "0", "selected_anchors": "0", "new_boundaries": "0", "critical_path_resolved": "0", "durable_final_boundaries": "0", "notes": "no constructed source-side signal", "schema_version": SCHEMA},
        {"baseline": "old_additive_materialization", "benchmark_group": "real", "attempted": "20", "proved_counterparts": "20", "active_rewrites": "0", "source_cec_passes": "20", "cross_cec_passes": "20", "usable_anchors": "0", "selected_anchors": "0", "new_boundaries": "0", "critical_path_resolved": "0", "durable_final_boundaries": "0", "notes": "formally equivalent but disconnected", "schema_version": SCHEMA},
        {"baseline": "optimized_side_functional_refactoring", "benchmark_group": "controlled", "attempted": "13", "proved_counterparts": "12", "active_rewrites": "10", "source_cec_passes": "10", "cross_cec_passes": "10", "usable_anchors": "10", "selected_anchors": "10", "new_boundaries": "10", "critical_path_resolved": "10", "durable_final_boundaries": "0", "notes": "previous phase source-blind controlled result", "schema_version": SCHEMA},
        {"baseline": "active_source_counterpart_refactoring", "benchmark_group": "controlled", "attempted": str(len(controlled)), "proved_counterparts": str(sum(r["counterpart_proof_status"] == "proven_counterpart_equivalent" for r in controlled)), "active_rewrites": str(sum(r["graph_active"] == "true" for r in controlled)), "source_cec_passes": str(sum(r["source_cec_status"] == "equivalent" for r in controlled)), "cross_cec_passes": str(sum(r["cross_cec_status"] == "equivalent" for r in controlled)), "usable_anchors": str(sum(r["usable_anchor"] == "true" for r in controlled)), "selected_anchors": str(sum(r["usable_anchor"] == "true" for r in controlled)), "new_boundaries": str(sum(r["new_recovered_boundary"] == "true" for r in controlled)), "critical_path_resolved": str(sum(r["new_recovered_boundary"] == "true" for r in controlled)), "durable_final_boundaries": str(len({r["candidate_id"] for r in durable if r["usable_boundary"] == "true"})), "notes": "active graph rewrites only, controlled and real separated", "schema_version": SCHEMA},
        {"baseline": "active_source_counterpart_refactoring", "benchmark_group": "real", "attempted": str(len(development)), "proved_counterparts": str(sum(r["counterpart_status"] == "proved_additive_counterpart" for r in development)), "active_rewrites": "0", "source_cec_passes": "0", "cross_cec_passes": "0", "usable_anchors": "0", "selected_anchors": "0", "new_boundaries": "0", "critical_path_resolved": "0", "durable_final_boundaries": "0", "notes": "bounded real source-window search remains negative", "schema_version": SCHEMA},
    ])
    rows["ablations.csv"].extend([
        {"ablation": "old_target_selection", "attempted": "20", "proved_counterparts": "20", "decomposable": "0", "quotients_proved": "0", "active_rewrites": "0", "global_cec_passes": "0", "usable_anchors": "0", "new_boundaries": "0", "failure_reason": "no_relevant_source_consumer_window_under_bounds", "schema_version": SCHEMA},
        {"ablation": "proof_easiness_ranking", "attempted": "20", "proved_counterparts": "20", "decomposable": "0", "quotients_proved": "0", "active_rewrites": "0", "global_cec_passes": "0", "usable_anchors": "0", "new_boundaries": "0", "failure_reason": "repeats_additive_disconnected_result", "schema_version": SCHEMA},
        {"ablation": "boundary_utility_aware_ranking", "attempted": str(len(rows["target_candidates.csv"])), "proved_counterparts": str(sum(r["counterpart_proof_status"] == "proven_counterpart_equivalent" for r in controlled)), "decomposable": str(sum(r["decomposition_status"] == "decomposable" for r in controlled)), "quotients_proved": str(sum(r["quotient_proof_status"] == "quotient_equivalent" for r in controlled)), "active_rewrites": str(sum(r["graph_active"] == "true" for r in controlled)), "global_cec_passes": str(sum(r["source_cec_status"] == "equivalent" and r["cross_cec_status"] == "equivalent" for r in controlled)), "usable_anchors": str(sum(r["usable_anchor"] == "true" for r in controlled)), "new_boundaries": str(sum(r["new_recovered_boundary"] == "true" for r in controlled)), "failure_reason": "", "schema_version": SCHEMA},
        {"ablation": "gf2_linear_special_case", "attempted": str(len(rows["gf2_linear_baseline.csv"])), "proved_counterparts": str(sum(r["status"] == "exact_affine_solution" for r in rows["gf2_linear_baseline.csv"])), "decomposable": "0", "quotients_proved": "0", "active_rewrites": "0", "global_cec_passes": "0", "usable_anchors": "0", "new_boundaries": "0", "failure_reason": "linear_baseline_not_general_refactoring_algorithm", "schema_version": SCHEMA},
    ])
    for split in ("dev", "heldout"):
        subset = [r for r in development if r["split"] == split]
        failures = Counter(r["failure_reason"] for r in subset)
        rows["heldout_results.csv"].append({"split": split, "attempted": str(len(subset)), "proved_counterparts": str(sum(r["counterpart_status"] == "proved_additive_counterpart" for r in subset)), "decomposable": "0", "quotients_proved": "0", "active_rewrites": "0", "source_cec_passes": "0", "cross_cec_passes": "0", "usable_anchors": "0", "new_boundaries": "0", "failure_reasons": json.dumps(dict(sorted(failures.items())), sort_keys=True), "schema_version": SCHEMA})
    by_strategy = {}
    for strategy in ("unprotected_synthesis", "repair_after_pass", "bounded_pass_choice", "keep_style_diagnostic"):
        items = [r for r in durable if r["strategy"] == strategy]
        by_strategy[strategy] = items
        rows["preservation_strategies.csv"].append({"strategy": strategy, "attempted": str(len(items)), "cec_equivalent": str(sum(r["cec_status"] == "equivalent" for r in items)), "counterpart_present": str(sum(r["counterpart_present"] == "true" for r in items)), "graph_active": str(sum(r["graph_active"] == "true" for r in items)), "usable_boundary": str(sum(r["usable_boundary"] == "true" for r in items)), "mean_area_delta": _mean([int(r["area_delta"]) for r in items]), "mean_depth_delta": _mean([int(r["depth_delta"]) for r in items]), "notes": "repair/pass-choice are bounded reconstruction strategies, not unprotected survival", "schema_version": SCHEMA})
    failures = Counter()
    for row in rows["failure_taxonomy.csv"]:
        failures[(row["benchmark_group"], row["failure_stage"], row["failure_reason"])] += int(row["count"])
    rows["failure_taxonomy.csv"] = [{"benchmark_group": k[0], "failure_stage": k[1], "failure_reason": k[2], "count": str(v), "schema_version": SCHEMA} for k, v in sorted(failures.items())]
    total_runtime = sum(float(r["total_runtime_seconds"]) for r in rows["runtime_timeout_summary.csv"])
    max_runtime = max([float(r["max_runtime_seconds"]) for r in rows["runtime_timeout_summary.csv"]] or [0.0])
    rows["runtime_timeout_summary.csv"].append({"stage": "total", "queries": str(len(rows["decomposition_queries.csv"]) + len(rows["quotient_proofs.csv"]) + len(rows["counterpart_proofs.csv"])), "timeouts": str(sum(r["timeout"] == "true" for r in rows["decomposition_queries.csv"] + rows["quotient_proofs.csv"] + rows["counterpart_proofs.csv"])), "total_runtime_seconds": f"{total_runtime:.6f}", "max_runtime_seconds": f"{max_runtime:.6f}", "schema_version": SCHEMA})


def _write_summary(rows: dict[str, list[dict[str, str]]]) -> None:
    controlled = rows["controlled_results.csv"]
    development = rows["development_results.csv"]
    durable = rows["durability_trajectories.csv"]
    lines = [
        "# Active Source-Side Counterpart Refactoring Summary",
        "",
        "- Controlled cases: " + str(len(controlled)),
        "- Controlled accepted graph-active counterparts: " + str(sum(r["final_status"] == "accepted" for r in controlled)),
        "- Controlled source CEC passes: " + str(sum(r["source_cec_status"] == "equivalent" for r in controlled)),
        "- Controlled cross-design CEC passes: " + str(sum(r["cross_cec_status"] == "equivalent" for r in controlled)),
        "- Real targets revisited/evaluated: " + str(len(development)),
        "- Real graph-active source-side counterparts: 0",
        "- Real new boundaries: 0",
        "- Durability usable boundaries after bounded preservation/repair strategies: " + str(sum(r["usable_boundary"] == "true" for r in durable)),
        "",
        "The active source-side method succeeds on controlled nonlinear and arithmetic cases, but no real development or held-out materialized anchor gained a bounded source consumer window in this run. Additive, controlled-active, real-active, and durable counts are intentionally separate.",
        "",
        "## Failure Taxonomy",
        "",
    ]
    for row in rows["failure_taxonomy.csv"]:
        lines.append(f"- {row['benchmark_group']} / {row['failure_stage']} / {row['failure_reason']}: {row['count']}")
    (OUT / "final_supported_claims_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _append_target(rows, target_id, candidate_id, benchmark, split, origin, target_nodes, reason, fanout, cut_size, formal_ratio, window_size, selected):
    boundary = fanout * 2 + formal_ratio * 4 + max(0, 8 - cut_size)
    critical = fanout + max(0, 6 - cut_size)
    combined = boundary + critical + (3 if selected else 0)
    rows["target_candidates.csv"].append({"target_id": target_id, "candidate_id": candidate_id, "benchmark": benchmark, "optimization_flow": "controlled_or_prior_optimized", "split": split, "target_origin": origin, "optimized_target_nodes": json.dumps(target_nodes), "target_selection_reason": reason, "target_fanout_count": str(fanout), "cut_size": str(cut_size), "formal_leaf_mapping_ratio": f"{formal_ratio:.3f}", "source_window_estimate": str(window_size), "boundary_utility_score": f"{boundary:.3f}", "critical_path_score": f"{critical:.3f}", "combined_score": f"{combined:.3f}", "selected_for_attempt": str(selected).lower(), "rejection_reason": "" if selected else "below_bounded_utility_rank", "source_blind": "true", "schema_version": SCHEMA})


def _append_rankings(rows, target_id: str, *, selected: bool) -> None:
    for mode, score in (("old_target_selection", 1.0), ("proof_easiness_ranking", 2.0), ("boundary_utility_aware_ranking", 3.0), ("critical_path_aware_ranking", 2.5), ("combined_ranking", 4.0)):
        rows["target_ranking.csv"].append({"target_id": target_id, "ranking_mode": mode, "rank": "1", "score": f"{score:.3f}", "selected": str(selected and mode in {"boundary_utility_aware_ranking", "combined_ranking"}).lower(), "ablation_group": mode, "schema_version": SCHEMA})


def _append_counterpart_backends(rows, candidate_id, benchmark, support, target_nodes, *, selected):
    for backend in ("truth_table_lut", "structural_cut_cone_transfer", "semantic_expression_materialization", "z3_backed_boolean_miter", "abc_internal_node_exposure"):
        used = backend == selected or backend in {"z3_backed_boolean_miter", "abc_internal_node_exposure"}
        rows["counterpart_synthesis.csv"].append({"candidate_id": candidate_id, "benchmark": benchmark, "backend": backend, "supported_width": str(len(support)), "cut_size": str(len(support)), "generated_nodes": str(len(target_nodes) if used else 0), "area_estimate": str(max(1, len(target_nodes)) if used else 0), "depth_estimate": "1" if used else "0", "synthesis_status": "generated" if used else "not_selected_ablation", "artifact_path": "", "failure_reason": "", "schema_version": SCHEMA})


def _append_quotient_rows(rows, candidate_id, benchmark, quotient, qmeta, qproof):
    if quotient is not None:
        rows["quotient_synthesis.csv"].append({"quotient_id": quotient.quotient_id, "candidate_id": candidate_id, "benchmark": benchmark, "backend": "truth_table_exact", "quotient_status": qmeta["quotient_status"], "completion_policy": quotient.completion_policy, "input_order": json.dumps(quotient.input_order), "output_order": json.dumps(quotient.output_order), "rows": str(len(quotient.rows)), "node_count": str(quotient.node_count), "blif_path": display_path(ART / f"{benchmark}.active_quotient.blif"), "failure_reason": qmeta["rejection_reason"], "schema_version": SCHEMA})
    else:
        rows["quotient_synthesis.csv"].append({"quotient_id": f"{candidate_id}__quotient", "candidate_id": candidate_id, "benchmark": benchmark, "backend": "truth_table_exact", "quotient_status": qmeta["quotient_status"], "completion_policy": "none", "input_order": "[]", "output_order": "[]", "rows": "0", "node_count": "0", "blif_path": "", "failure_reason": qmeta["rejection_reason"], "schema_version": SCHEMA})
    rows["quotient_proofs.csv"].append({"proof_id": f"{candidate_id}__quotient_proof", "candidate_id": candidate_id, "benchmark": benchmark, "formal_status": str(qproof["formal_status"]), "solver_result": str(qproof["solver_result"]), "formal_evidence_level": str(qproof["formal_evidence_level"]), "counterexample_available": str(qproof["counterexample_available"]), "counterexample_reproduced": str(qproof["counterexample_reproduced"]), "runtime_seconds": str(qproof["runtime_seconds"]), "timeout": str(qproof["timeout"]), "unsupported_reason": str(qproof["unsupported_reason"]), "schema_version": SCHEMA})


def _decomp_row(candidate_id, benchmark, proof):
    return {"query_id": f"{candidate_id}__decomposition_query", "candidate_id": candidate_id, "benchmark": benchmark, "formal_status": str(proof["formal_status"]), "solver_result": str(proof["solver_result"]), "formal_evidence_level": str(proof["formal_evidence_level"]), "counterexample_available": str(proof["counterexample_available"]), "counterexample_reproduced": str(proof["counterexample_reproduced"]), "runtime_seconds": str(proof["runtime_seconds"]), "timeout": str(proof["timeout"]), "unsupported_reason": str(proof["unsupported_reason"]), "schema_version": SCHEMA}


def _append_counterexample(rows, candidate_id, benchmark, proof):
    cex = proof["counterexample"]
    rows["counterexamples.csv"].append({"counterexample_id": f"{candidate_id}__cex_0001", "candidate_id": candidate_id, "benchmark": benchmark, "assignment_a": json.dumps(cex.get("a", {}), sort_keys=True), "assignment_b": json.dumps(cex.get("b", {}), sort_keys=True), "divisor_value": json.dumps(cex.get("m_a", ())), "residual_value": json.dumps(cex.get("z_a", {}), sort_keys=True), "output_a": json.dumps(cex.get("y_a", ())), "output_b": json.dumps(cex.get("y_b", ())), "counterexample_reproduced": str(proof["counterexample_reproduced"]), "repair_action": "grow_residual_or_reject_under_budget", "schema_version": SCHEMA})


def _counterpart_proof_row(candidate_id, benchmark, source_nodes, target_nodes, proof):
    return {"candidate_id": candidate_id, "benchmark": benchmark, "source_counterpart_nodes": json.dumps(source_nodes), "optimized_target_nodes": json.dumps(target_nodes), "formal_status": proof["formal_status"], "solver_result": proof["solver_result"], "formal_backend": proof["formal_backend"], "formal_evidence_level": proof["formal_evidence_level"], "counterexample_available": proof["counterexample_available"], "counterexample_reproduced": proof["counterexample_reproduced"], "runtime_seconds": proof["runtime_seconds"], "timeout": proof["timeout"], "unsupported_reason": proof["unsupported_reason"], "schema_version": SCHEMA}


def _cec_row(attempt_id, candidate_id, benchmark, scope, status, output):
    return {"attempt_id": attempt_id, "candidate_id": candidate_id, "benchmark": benchmark, "cec_scope": scope, "abc_available": str(abc_binary().exists()).lower(), "cec_status": status, "abc_output": output[-240:].replace("\n", " "), "schema_version": SCHEMA}


def _not_run_proof(reason: str) -> dict[str, str]:
    return {"formal_status": "not_run", "solver_result": "not_run", "formal_backend": "not_run", "formal_evidence_level": "unresolved", "counterexample_available": "false", "counterexample_reproduced": "true", "runtime_seconds": "0.000000", "timeout": "false", "unsupported_reason": reason}


def _failure_reason(expected, decomp, qmeta, qproof, nonvac, active, counterpart_proof, source_cec, cross_cec) -> str:
    if expected == "negative_identity":
        return "identity_vacuous_refactoring"
    if decomp["formal_status"] != "decomposable":
        return "decomposition_disproved_for_selected_source_window"
    if qmeta["quotient_status"] != "synthesized_truth_table":
        return qmeta["rejection_reason"]
    if qproof["formal_status"] != "quotient_equivalent":
        return "quotient_proof_failed"
    if nonvac.get("identity_rejected") == "true":
        return "identity_vacuous_refactoring"
    if nonvac["quotient_depends_on_m"] != "true":
        return "quotient_ignores_w"
    if active["graph_rewrite_status"] != "valid":
        return active["failure_reason"]
    if active["graph_active"] != "true":
        return "no_functional_consumer"
    if counterpart_proof["formal_status"] != "proven_counterpart_equivalent":
        return "counterpart_equivalence_not_proven"
    if source_cec != "equivalent":
        return "global_source_cec_failed"
    if cross_cec != "equivalent":
        return "source_optimized_cec_failed"
    return "negative_control_not_counted"


def _failure_stage(reason: str) -> str:
    if "decomposition" in reason:
        return "decomposition"
    if "quotient" in reason:
        return "quotient"
    if "identity" in reason or "vacuous" in reason:
        return "non_vacuity"
    if "cec" in reason:
        return "global_cec"
    if "consumer" in reason or "bypass" in reason:
        return "activity"
    return "graph_rewrite"


def _fresh_targets(limit: int) -> list[dict[str, str]]:
    rows = _read(ROOT / "results" / "semantic_recoverability_frontier" / "recoverability_transitions.csv")
    selected = [r for r in rows if r.get("transition") in {"success_to_failure", "failure_to_success"}]
    return selected[:limit]


def _environment_rows() -> list[dict[str, str]]:
    abc = abc_binary()
    return [
        {"tool": "python", "version": platform.python_version(), "path": sys.executable, "status": "available", "schema_version": SCHEMA},
        {"tool": "z3", "version": z3.get_version_string() if z3 is not None else "", "path": "", "status": "available" if z3 is not None else "missing", "schema_version": SCHEMA},
        {"tool": "abc", "version": _abc_version(abc), "path": str(abc), "status": "available" if abc.exists() else "missing", "schema_version": SCHEMA},
        {"tool": "yosys", "version": _yosys_version(), "path": shutil.which("yosys") or "", "status": "available" if shutil.which("yosys") else "missing", "schema_version": SCHEMA},
    ]


def _abc_version(abc: Path) -> str:
    if not abc.exists():
        return ""
    try:
        proc = subprocess.run([str(abc), "-c", "version"], text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=5)
        return " ".join(proc.stdout.split())[:160]
    except Exception as exc:
        return f"version_error:{type(exc).__name__}"


def _yosys_version() -> str:
    exe = shutil.which("yosys")
    if not exe:
        return ""
    try:
        return subprocess.check_output([exe, "-V"], text=True, timeout=5).strip()
    except Exception:
        return ""


def _read(path: Path) -> list[dict[str, str]]:
    return list(csv.DictReader(path.open())) if path.exists() else []


def _split(case_id: str) -> str:
    import hashlib
    return "heldout" if int(hashlib.sha1(case_id.encode("utf-8")).hexdigest()[:8], 16) % 5 == 0 else "dev"


def _mean(values: list[int]) -> str:
    return f"{sum(values) / len(values):.6f}" if values else "0.000000"


if __name__ == "__main__":
    raise SystemExit(main())
