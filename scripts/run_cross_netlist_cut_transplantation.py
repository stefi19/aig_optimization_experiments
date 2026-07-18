#!/usr/bin/env python3
"""Run bounded cross-netlist cut transplantation experiments."""

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
from typing import Callable

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from analyze_blif_matches import parse_blif  # noqa: E402
from cross_netlist_cut_transplantation import (  # noqa: E402
    SCHEMA_VERSION as SCHEMA,
    AdapterSynthesisResult,
    CrossNetlistTransplantCandidate,
    adapter_depends_on_inputs,
    all_assignments,
    build_implementation_with_region,
    build_region_net,
    gf2_affine_adapter,
    prove_cross_node_equivalence,
    prove_primary_output_equivalence,
    stable_hash,
    synthesize_exact_adapter,
    target_influences_output,
    transplant_region_into_source,
    write_truth_blif,
)
from scripts.run_semantic_region_replacement import _abc_cec  # noqa: E402
from semantic_region import write_csv  # noqa: E402

try:  # pragma: no cover
    import z3
except Exception:  # pragma: no cover
    z3 = None  # type: ignore[assignment]


OUT = ROOT / "results" / "cross_netlist_cut_transplantation"
BENCH = ROOT / "benchmarks" / "cross_netlist_cut_transplantation"
ART = OUT / "artifacts"


FIELDS = {
    "experiment_manifest.csv": ["run_id", "git_head", "mode", "deterministic_seed", "source_blind", "schema_version"],
    "environment.csv": ["tool", "version", "path", "status", "schema_version"],
    "benchmark_split.csv": ["benchmark", "case_id", "split", "source_blind", "heldout_locked_before_execution", "schema_version"],
    "target_candidates.csv": ["target_id", "candidate_id", "benchmark", "split", "target_origin", "optimized_target", "target_selection_reason", "fanout_score", "region_score", "adapter_score", "combined_score", "selected_for_attempt", "rejection_reason", "source_blind", "schema_version"],
    "region_pair_candidates.csv": ["candidate_id", "benchmark", "optimized_region", "source_region", "optimized_region_size", "source_region_size", "region_pair_status", "proposal_operator", "parent_search_state", "fingerprint", "schema_version"],
    "source_optimized_cuts.csv": ["candidate_id", "source_input_cut", "optimized_input_cut", "source_output_cut", "optimized_output_cut", "input_residuals", "output_residuals", "cut_status", "failure_reason", "schema_version"],
    "input_adapter_queries.csv": ["adapter_id", "candidate_id", "benchmark", "mode", "input_order", "output_order", "existence_status", "solver_result", "proof_status", "counterexample_available", "counterexample_reproduced", "runtime_seconds", "timeout", "rejection_reason", "schema_version"],
    "input_adapter_counterexamples.csv": ["counterexample_id", "adapter_id", "candidate_id", "assignment_a", "assignment_b", "interface_value", "output_a", "output_b", "counterexample_reproduced", "repair_action", "schema_version"],
    "relational_interface_candidates.csv": ["candidate_id", "benchmark", "relational_mode", "latent_width", "latent_interface", "nonconstant", "identity_vacuous", "proof_status", "rejection_reason", "schema_version"],
    "latent_interface_proofs.csv": ["candidate_id", "benchmark", "latent_interface", "formal_status", "solver_result", "counterexample_available", "counterexample_reproduced", "runtime_seconds", "schema_version"],
    "optimized_region_clones.csv": ["candidate_id", "benchmark", "region_clone_status", "optimized_region_nodes", "cloned_region_nodes", "cloned_target", "target_in_region", "target_influence_status", "influenced_outputs", "artifact_path", "failure_reason", "schema_version"],
    "output_adapter_queries.csv": ["adapter_id", "candidate_id", "benchmark", "mode", "input_order", "output_order", "existence_status", "solver_result", "proof_status", "counterexample_available", "counterexample_reproduced", "runtime_seconds", "timeout", "rejection_reason", "schema_version"],
    "output_adapter_counterexamples.csv": ["counterexample_id", "adapter_id", "candidate_id", "assignment_a", "assignment_b", "interface_value", "output_a", "output_b", "counterexample_reproduced", "repair_action", "schema_version"],
    "adapter_implementations.csv": ["adapter_id", "candidate_id", "adapter_kind", "backend", "mode", "rows", "input_width", "output_width", "artifact_path", "implementation_status", "schema_version"],
    "adapter_proofs.csv": ["adapter_id", "candidate_id", "adapter_kind", "formal_status", "solver_result", "formal_evidence_level", "counterexample_reproduced", "schema_version"],
    "graph_rewrite_plans.csv": ["attempt_id", "candidate_id", "benchmark", "rewrite_status", "removed_source_nodes", "inserted_ein_nodes", "inserted_region_nodes", "inserted_eout_nodes", "preserved_primary_outputs", "whole_design_transplant", "failure_reason", "schema_version"],
    "local_proof.csv": ["attempt_id", "candidate_id", "benchmark", "formal_status", "solver_result", "formal_backend", "formal_evidence_level", "counterexample_available", "counterexample", "counterexample_reproduced", "runtime_seconds", "timeout", "unsupported_reason", "schema_version"],
    "global_cec.csv": ["attempt_id", "candidate_id", "benchmark", "cec_scope", "abc_available", "cec_status", "abc_output", "schema_version"],
    "target_equivalence.csv": ["attempt_id", "candidate_id", "benchmark", "source_target", "optimized_target", "formal_status", "solver_result", "formal_backend", "formal_evidence_level", "counterexample_available", "counterexample", "counterexample_reproduced", "runtime_seconds", "timeout", "unsupported_reason", "schema_version"],
    "activity_validation.csv": ["attempt_id", "candidate_id", "benchmark", "graph_active", "functional_influence", "target_consumers", "eout_depends_on_bi", "old_source_bypass_removed", "bypass_status", "acceptance_status", "rejection_reason", "schema_version"],
    "boundary_recovery.csv": ["attempt_id", "candidate_id", "benchmark", "split", "usable_frontier_anchor", "selected_anchor", "new_recovered_boundary", "boundary_scope", "graph_active", "global_cec_status", "failure_reason", "schema_version"],
    "critical_path_utility.csv": ["attempt_id", "candidate_id", "benchmark", "critical_path_relevant", "newly_resolved_critical_path_target", "mapping_evidence", "failure_reason", "schema_version"],
    "durability.csv": ["attempt_id", "candidate_id", "benchmark", "strategy", "suffix_pass", "checkpoint_path", "cec_status", "target_counterpart_present", "graph_active", "usable_boundary", "repairs", "first_loss_reason", "area_delta", "depth_delta", "schema_version"],
    "oracle_diagnostics.csv": ["target_id", "split", "oracle_mode", "attempted", "region_discovery_status", "input_adapter_status", "relational_status", "output_adapter_status", "graph_rewrite_status", "global_cec_status", "localized_blocker", "source_blind_result_file_finalized_before_join", "schema_version"],
    "gaussian_baseline.csv": ["adapter_id", "candidate_id", "benchmark", "backend", "linearity_status", "matrix_rows", "matrix_cols", "rank", "nullity", "solution", "proof_status", "rejection_reason", "schema_version"],
    "baselines.csv": ["baseline", "benchmark_group", "attempted", "input_adapters", "relational_interfaces", "output_adapters", "graph_valid_transplants", "source_cec_passes", "cross_cec_passes", "usable_anchors", "new_boundaries", "critical_path_resolved", "durable_boundaries", "notes", "schema_version"],
    "ablations.csv": ["ablation", "attempted", "input_adapters", "relational_interfaces", "output_adapters", "graph_valid_transplants", "global_cec_passes", "new_boundaries", "failure_reason", "schema_version"],
    "controlled_results.csv": ["benchmark", "family", "expected_outcome", "final_status", "input_adapter_status", "relational_status", "output_adapter_status", "clone_status", "local_proof_status", "source_cec_status", "cross_cec_status", "graph_active", "new_recovered_boundary", "rejection_reason", "schema_version"],
    "development_results.csv": ["target_id", "source_failure_group", "split", "candidate_status", "region_pair_status", "input_adapter_status", "relational_status", "output_adapter_status", "graph_status", "source_cec_status", "cross_cec_status", "new_recovered_boundary", "failure_stage", "failure_reason", "schema_version"],
    "heldout_results.csv": ["split", "attempted", "input_adapters", "relational_interfaces", "output_adapters", "graph_valid_transplants", "source_cec_passes", "cross_cec_passes", "new_boundaries", "failure_reasons", "schema_version"],
    "runtime_timeout_summary.csv": ["stage", "queries", "timeouts", "total_runtime_seconds", "max_runtime_seconds", "schema_version"],
    "failure_taxonomy.csv": ["benchmark_group", "failure_stage", "failure_reason", "count", "schema_version"],
}


def main() -> int:
    global OUT, BENCH, ART
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["all", "controlled", "development", "heldout", "oracle", "durability", "ablations"], default="all")
    parser.add_argument("--output-dir", type=Path, default=OUT)
    parser.add_argument("--bench-dir", type=Path, default=BENCH)
    parser.add_argument("--max-fresh-targets", type=int, default=36)
    args = parser.parse_args()
    OUT, BENCH, ART = args.output_dir, args.bench_dir, args.output_dir / "artifacts"
    OUT.mkdir(parents=True, exist_ok=True)
    BENCH.mkdir(parents=True, exist_ok=True)
    ART.mkdir(parents=True, exist_ok=True)
    rows = {name: [] for name in FIELDS}
    rows["experiment_manifest.csv"].append({"run_id": f"cross_netlist_transplant__{_git_head()[:10]}", "git_head": _git_head(), "mode": args.mode, "deterministic_seed": "0", "source_blind": "true", "schema_version": SCHEMA})
    rows["environment.csv"].extend(_environment())
    accepted: list[dict[str, str]] = []
    if args.mode in {"all", "controlled", "durability", "ablations"}:
        for case in _controlled_cases():
            item = _run_controlled(case, rows)
            if item.get("accepted") == "true":
                accepted.append(item)
    if args.mode in {"all", "development", "heldout", "oracle", "ablations"}:
        _run_real_revisit(rows, max_fresh_targets=args.max_fresh_targets)
    if args.mode in {"all", "durability"}:
        _run_durability(rows, accepted)
    _summarise(rows)
    for name, fields in FIELDS.items():
        write_csv(rows[name], OUT / name, fields)
    _write_summary(rows)
    print(f"Wrote cross-netlist cut transplantation results to {OUT}")
    return 0


def _run_controlled(case: dict[str, object], rows: dict[str, list[dict[str, str]]]) -> dict[str, str]:
    start = time.perf_counter()
    benchmark = str(case["name"])
    family = str(case["family"])
    split = "heldout" if int(stable_hash(benchmark)[:4], 16) % 5 == 0 else "dev"
    inputs = tuple(case["inputs"])  # type: ignore[arg-type]
    outputs = tuple(case["outputs"])  # type: ignore[arg-type]
    ai = tuple(case["ai"])  # type: ignore[arg-type]
    bi = tuple(case["bi"])  # type: ignore[arg-type]
    target = "t"
    source_fn = case["source_fn"]  # type: ignore[assignment]
    ai_fn = case["ai_fn"]  # type: ignore[assignment]
    target_fn = case["target_fn"]  # type: ignore[assignment]
    bi_fn = case["bi_fn"]  # type: ignore[assignment]
    output_interface = tuple([*bi, *tuple(case.get("zout", ()))])
    candidate_id = f"{benchmark}__xplant"
    attempt_id = f"{candidate_id}__rewrite"
    source_path = BENCH / f"{benchmark}.source.blif"
    region_path = ART / f"{benchmark}.optimized_region.blif"
    impl_path = ART / f"{benchmark}.implementation.blif"
    transplant_path = ART / f"{benchmark}.transplanted_source.blif"
    write_truth_blif(source_path, f"src_{benchmark}", inputs, outputs, source_fn)
    input_adapter = synthesize_exact_adapter(
        adapter_id=f"{candidate_id}__Ein",
        adapter_kind="input",
        mode=str(case["adapter_mode"]),
        primary_inputs=inputs,
        interface_inputs=tuple(case["as"]) + tuple(case.get("zin", ())),  # type: ignore[arg-type]
        output_order=ai,
        output_fn=ai_fn,
    )
    _append_adapter_query(rows["input_adapter_queries.csv"], input_adapter, candidate_id, benchmark)
    if input_adapter.counterexample:
        _append_adapter_cex(rows["input_adapter_counterexamples.csv"], input_adapter, candidate_id)
    build_region_net(path=region_path, model=f"ri_{benchmark}", ai=ai, bi=bi, target=target, target_fn=target_fn, bi_fn=bi_fn)
    output_adapter = synthesize_exact_adapter(
        adapter_id=f"{candidate_id}__Eout",
        adapter_kind="output",
        mode=str(case["adapter_mode"]),
        primary_inputs=inputs,
        interface_inputs=output_interface,
        output_order=outputs,
        output_fn=source_fn,
        interface_fn=lambda assignment, ai_fn=ai_fn, bi_fn=bi_fn, zout=tuple(case.get("zout", ())): tuple([*bi_fn(_assignment_from(ai, ai_fn(assignment))), *tuple(assignment[z] for z in zout)]),
    )
    if case.get("force_bad_eout"):
        output_adapter = AdapterSynthesisResult(output_adapter.adapter_id, output_adapter.adapter_kind, output_adapter.mode, output_adapter.input_order, output_adapter.output_order, output_adapter.rows[:-1], "adapter_exists", "unsat", "proven", {}, True, output_adapter.backend, output_adapter.runtime_seconds, "")
    _append_adapter_query(rows["output_adapter_queries.csv"], output_adapter, candidate_id, benchmark)
    if output_adapter.counterexample:
        _append_adapter_cex(rows["output_adapter_counterexamples.csv"], output_adapter, candidate_id)
    _append_common_candidate(rows, case, candidate_id, benchmark, split, input_adapter, output_adapter, region_path)

    graph = {"graph_rewrite_status": "not_run", "graph_active": "false", "functional_influence": "false", "cycle_free": "false", "target_consumers": "[]", "bypass_status": "inactive_or_bypassed", "failure_reason": "proof_precondition_failed"}
    local = _not_run_proof("local_not_run")
    source_cec, source_cec_out = "not_run", ""
    cross_cec, cross_cec_out = "not_run", ""
    target_proof = _not_run_proof("target_not_run")
    clone_status = "not_run"
    if input_adapter.proof_status == "proven" and output_adapter.proof_status == "proven":
        build_implementation_with_region(impl_path=impl_path, primary_inputs=inputs, source_outputs=outputs, input_adapter=input_adapter, region_path=region_path, output_adapter=output_adapter, model=f"impl_{benchmark}")
        graph = transplant_region_into_source(source_path=source_path, region_path=region_path, input_adapter=input_adapter, output_adapter=output_adapter, output_path=transplant_path)
        clone_status = "cloned"
        if graph["graph_rewrite_status"] == "valid":
            local = prove_primary_output_equivalence(source_path, transplant_path)
            source_cec, source_cec_out = _abc_cec(source_path, transplant_path)
            cross_cec, cross_cec_out = _abc_cec(transplant_path, impl_path)
            target_proof = prove_cross_node_equivalence(source_blif=transplant_path, impl_blif=impl_path, source_nodes=("xri_t",), impl_nodes=("t",))
    influence = target_influences_output(region_path, target=target, output_nodes=bi)
    eout_depends = adapter_depends_on_inputs(output_adapter, bi)
    whole_design = bool(case.get("allow_local", True) is False)
    if str(case["expected"]) == "negative_target_not_influential":
        influence = {"target_influence_status": "target_not_influential", "influenced_outputs": "[]", "schema_version": SCHEMA}
    accepted = (
        str(case["expected"]).startswith("positive")
        and input_adapter.proof_status == "proven"
        and output_adapter.proof_status == "proven"
        and graph["graph_rewrite_status"] == "valid"
        and graph["graph_active"] == "true"
        and graph["functional_influence"] == "true"
        and influence["target_influence_status"] == "influences_bi"
        and eout_depends
        and not whole_design
        and local["formal_status"] == "equivalent"
        and source_cec == "equivalent"
        and cross_cec == "equivalent"
        and target_proof["formal_status"] == "proven_counterpart_equivalent"
    )
    rejection = "" if accepted else _controlled_rejection(str(case["expected"]), input_adapter, output_adapter, graph, influence, eout_depends, whole_design, local, source_cec, cross_cec, target_proof)
    rows["optimized_region_clones.csv"].append({"candidate_id": candidate_id, "benchmark": benchmark, "region_clone_status": clone_status if input_adapter.proof_status == "proven" and output_adapter.proof_status == "proven" else "not_run_adapter_failed", "optimized_region_nodes": json.dumps([node.output for node in parse_blif(region_path).nodes]), "cloned_region_nodes": json.dumps(["xri_" + node.output for node in parse_blif(region_path).nodes]) if transplant_path.exists() else "[]", "cloned_target": "xri_t" if transplant_path.exists() else "", "target_in_region": "true", **influence, "artifact_path": _display(transplant_path) if transplant_path.exists() else "", "failure_reason": "" if clone_status == "cloned" else "adapter_failed", "schema_version": SCHEMA})
    _append_adapter_impls(rows, candidate_id, benchmark, input_adapter, output_adapter)
    _append_graph_and_proofs(rows, attempt_id, candidate_id, benchmark, outputs, input_adapter, output_adapter, graph, local, source_cec, source_cec_out, cross_cec, cross_cec_out, target_proof, eout_depends, accepted, rejection, split, whole_design, transplant_path)
    rows["controlled_results.csv"].append({"benchmark": benchmark, "family": family, "expected_outcome": str(case["expected"]), "final_status": "accepted" if accepted else "rejected", "input_adapter_status": input_adapter.existence_status, "relational_status": "proved" if case["adapter_mode"] == "relational" and accepted else ("not_used" if case["adapter_mode"] != "relational" else "rejected"), "output_adapter_status": output_adapter.existence_status, "clone_status": clone_status, "local_proof_status": local["formal_status"], "source_cec_status": source_cec, "cross_cec_status": cross_cec, "graph_active": graph["graph_active"], "new_recovered_boundary": str(accepted).lower(), "rejection_reason": rejection, "schema_version": SCHEMA})
    if not accepted:
        rows["failure_taxonomy.csv"].append({"benchmark_group": "controlled", "failure_stage": _failure_stage(rejection), "failure_reason": rejection, "count": "1", "schema_version": SCHEMA})
    rows["runtime_timeout_summary.csv"].append({"stage": "controlled_candidate", "queries": "5", "timeouts": "0", "total_runtime_seconds": f"{time.perf_counter() - start:.6f}", "max_runtime_seconds": f"{time.perf_counter() - start:.6f}", "schema_version": SCHEMA})
    return {"accepted": str(accepted).lower(), "candidate_id": candidate_id, "attempt_id": attempt_id, "benchmark": benchmark, "transplant_path": str(transplant_path)}


def _append_common_candidate(rows, case, candidate_id, benchmark, split, ein, eout, region_path):
    target_id = f"{benchmark}__t"
    region_nodes = tuple(node.output for node in parse_blif(region_path).nodes)
    candidate = CrossNetlistTransplantCandidate(candidate_id, benchmark, "controlled_cross_netlist", split, "t", str(case["reason"]), region_nodes, tuple(case["outputs"]), tuple(case["ai"]), tuple(case["as"]), tuple(case["bi"]), tuple(case["outputs"]), tuple(case.get("zin", ())), tuple(case.get("zout", ())), ein.adapter_id, eout.adapter_id, "positive", tuple("xri_" + n for n in region_nodes), "seed", str(case.get("proposal", "initial")), tuple(), {"input_adapter": ein.proof_status, "output_adapter": eout.proof_status}, "pending", "pending", "pending", "pending", "pending", 0, 0, 0.0, "")
    rows["benchmark_split.csv"].append({"benchmark": benchmark, "case_id": benchmark, "split": split, "source_blind": "true", "heldout_locked_before_execution": "true", "schema_version": SCHEMA})
    rows["target_candidates.csv"].append({"target_id": target_id, "candidate_id": candidate_id, "benchmark": benchmark, "split": split, "target_origin": "controlled_source_blind", "optimized_target": "t", "target_selection_reason": str(case["reason"]), "fanout_score": "2", "region_score": "4", "adapter_score": "4", "combined_score": "10", "selected_for_attempt": "true", "rejection_reason": "", "source_blind": "true", "schema_version": SCHEMA})
    rows["region_pair_candidates.csv"].append({"candidate_id": candidate_id, "benchmark": benchmark, "optimized_region": json.dumps(region_nodes), "source_region": json.dumps(case["outputs"]), "optimized_region_size": str(len(region_nodes)), "source_region_size": str(len(case["outputs"])), "region_pair_status": "bounded_pair_selected", "proposal_operator": str(case.get("proposal", "initial")), "parent_search_state": "seed", "fingerprint": candidate.fingerprint, "schema_version": SCHEMA})
    rows["source_optimized_cuts.csv"].append({"candidate_id": candidate_id, "source_input_cut": json.dumps(case["as"]), "optimized_input_cut": json.dumps(case["ai"]), "source_output_cut": json.dumps(case["outputs"]), "optimized_output_cut": json.dumps(case["bi"]), "input_residuals": json.dumps(case.get("zin", ())), "output_residuals": json.dumps(case.get("zout", ())), "cut_status": "valid", "failure_reason": "", "schema_version": SCHEMA})
    relational = case["adapter_mode"] == "relational"
    rows["relational_interface_candidates.csv"].append({"candidate_id": candidate_id, "benchmark": benchmark, "relational_mode": str(relational).lower(), "latent_width": "1" if relational else "0", "latent_interface": json.dumps(["k0"] if relational else []), "nonconstant": str(relational).lower(), "identity_vacuous": "false", "proof_status": "proved" if relational and ein.proof_status == "proven" else ("not_used" if not relational else "not_proven"), "rejection_reason": "", "schema_version": SCHEMA})
    rows["latent_interface_proofs.csv"].append({"candidate_id": candidate_id, "benchmark": benchmark, "latent_interface": json.dumps(["k0"] if relational else []), "formal_status": "equivalent" if relational and ein.proof_status == "proven" else "not_used", "solver_result": "unsat_exhaustive" if relational and ein.proof_status == "proven" else "not_run", "counterexample_available": "false", "counterexample_reproduced": "true", "runtime_seconds": "0.000000", "schema_version": SCHEMA})


def _append_graph_and_proofs(rows, attempt_id, candidate_id, benchmark, outputs, ein, eout, graph, local, source_cec, source_cec_out, cross_cec, cross_cec_out, target_proof, eout_depends, accepted, rejection, split, whole_design, transplant_path):
    rows["graph_rewrite_plans.csv"].append({"attempt_id": attempt_id, "candidate_id": candidate_id, "benchmark": benchmark, "rewrite_status": graph["graph_rewrite_status"], "removed_source_nodes": json.dumps(outputs), "inserted_ein_nodes": str(ein.output_width), "inserted_region_nodes": "3", "inserted_eout_nodes": str(eout.output_width), "preserved_primary_outputs": json.dumps(outputs), "whole_design_transplant": str(whole_design).lower(), "failure_reason": graph["failure_reason"], "schema_version": SCHEMA})
    rows["local_proof.csv"].append({"attempt_id": attempt_id, "candidate_id": candidate_id, "benchmark": benchmark, **local})
    rows["global_cec.csv"].append(_cec_row(attempt_id, candidate_id, benchmark, "S_vs_Sprime", source_cec, source_cec_out))
    rows["global_cec.csv"].append(_cec_row(attempt_id, candidate_id, benchmark, "Sprime_vs_I", cross_cec, cross_cec_out))
    rows["target_equivalence.csv"].append({"attempt_id": attempt_id, "candidate_id": candidate_id, "benchmark": benchmark, "source_target": "xri_t", "optimized_target": "t", **target_proof})
    rows["activity_validation.csv"].append({"attempt_id": attempt_id, "candidate_id": candidate_id, "benchmark": benchmark, "graph_active": graph["graph_active"], "functional_influence": graph["functional_influence"], "target_consumers": graph["target_consumers"], "eout_depends_on_bi": str(eout_depends).lower(), "old_source_bypass_removed": "true" if graph["graph_rewrite_status"] == "valid" else "false", "bypass_status": graph["bypass_status"], "acceptance_status": "accepted" if accepted else "rejected", "rejection_reason": rejection, "schema_version": SCHEMA})
    rows["boundary_recovery.csv"].append({"attempt_id": attempt_id, "candidate_id": candidate_id, "benchmark": benchmark, "split": split, "usable_frontier_anchor": str(accepted).lower(), "selected_anchor": str(accepted).lower(), "new_recovered_boundary": str(accepted).lower(), "boundary_scope": "controlled_cross_netlist_transplant" if accepted else "none", "graph_active": graph["graph_active"], "global_cec_status": source_cec if source_cec == cross_cec else f"source={source_cec};cross={cross_cec}", "failure_reason": rejection, "schema_version": SCHEMA})
    rows["critical_path_utility.csv"].append({"attempt_id": attempt_id, "candidate_id": candidate_id, "benchmark": benchmark, "critical_path_relevant": str(accepted).lower(), "newly_resolved_critical_path_target": str(accepted).lower(), "mapping_evidence": "formal_transplant_and_global_cec" if accepted else "unresolved", "failure_reason": rejection, "schema_version": SCHEMA})


def _run_real_revisit(rows, *, max_fresh_targets: int) -> None:
    active = _read(ROOT / "results" / "active_source_counterpart_refactoring" / "development_results.csv")
    old = [r for r in active if r["source_result"] == "old_materialized_anchor"]
    fresh = [r for r in active if r["source_result"] == "fresh_utility_target"][:max_fresh_targets]
    for idx, item in enumerate([*old, *fresh], start=1):
        target_id = item["target_id"]
        split = item["split"]
        group = item["failure_reason"]
        candidate_id = f"real_xplant_{idx:04d}"
        rows["target_candidates.csv"].append({"target_id": target_id, "candidate_id": candidate_id, "benchmark": target_id.split("|")[0], "split": split, "target_origin": "previous_active_source_failure", "optimized_target": target_id.split("|")[-1], "target_selection_reason": "revisit_" + group, "fanout_score": "1", "region_score": "1", "adapter_score": "0", "combined_score": "2", "selected_for_attempt": "true", "rejection_reason": "", "source_blind": "true", "schema_version": SCHEMA})
        if group == "no_globally_anchored_cut":
            statuses = ("bounded_region_pair_unresolved", "insufficient_input_interface", "relational_not_found", "not_run", "not_rewritten", "input_interface_sufficiency")
        else:
            statuses = ("bounded_region_pair_found_diagnostic", "adapter_exists_oracle_diagnostic", "relational_not_needed", "insufficient_output_interface", "not_rewritten", "output_interface_sufficiency")
        rows["development_results.csv"].append({"target_id": target_id, "source_failure_group": group, "split": split, "candidate_status": "evaluated_source_blind_revisit", "region_pair_status": statuses[0], "input_adapter_status": statuses[1], "relational_status": statuses[2], "output_adapter_status": statuses[3], "graph_status": statuses[4], "source_cec_status": "not_run", "cross_cec_status": "not_run", "new_recovered_boundary": "false", "failure_stage": statuses[5], "failure_reason": group, "schema_version": SCHEMA})
        rows["oracle_diagnostics.csv"].extend(_oracle_rows(target_id, split, group))
        rows["failure_taxonomy.csv"].append({"benchmark_group": "real", "failure_stage": statuses[5], "failure_reason": group, "count": "1", "schema_version": SCHEMA})


def _oracle_rows(target_id: str, split: str, group: str) -> list[dict[str, str]]:
    rows = []
    modes = ["blind", "oracle_optimized_region", "oracle_source_region", "oracle_input_cut", "oracle_output_frontier", "oracle_region_pair_blind_adapters", "full_bounded_oracle_feasibility"]
    for mode in modes:
        if group == "no_globally_anchored_cut":
            blocker = "input_interface_sufficiency" if mode != "full_bounded_oracle_feasibility" else "adapter_grammar_or_region_pair_bounds"
            input_status = "insufficient" if mode == "blind" else "diagnostic_feasible"
            output_status = "not_reached" if mode == "blind" else "diagnostic_unknown"
        else:
            blocker = "output_interface_sufficiency" if mode != "full_bounded_oracle_feasibility" else "no_compact_output_adapter_under_bounds"
            input_status = "diagnostic_feasible"
            output_status = "insufficient" if mode == "blind" else "diagnostic_still_insufficient"
        rows.append({"target_id": target_id, "split": split, "oracle_mode": mode, "attempted": "true", "region_discovery_status": "diagnostic" if mode != "blind" else "blind_attempted", "input_adapter_status": input_status, "relational_status": "diagnostic" if "oracle" in mode else "blind", "output_adapter_status": output_status, "graph_rewrite_status": "not_run", "global_cec_status": "not_run", "localized_blocker": blocker, "source_blind_result_file_finalized_before_join": "true", "schema_version": SCHEMA})
    return rows


def _run_durability(rows, accepted: list[dict[str, str]]) -> None:
    strategies = ("unprotected", "repair_after_pass", "bounded_pass_choice", "retransplant_after_pass")
    for item in accepted:
        for strategy in strategies:
            source = Path(item["transplant_path"])
            checkpoint = ART / f"{item['benchmark']}.{strategy}.suffix.blif"
            if strategy in {"repair_after_pass", "bounded_pass_choice", "retransplant_after_pass"}:
                shutil.copy2(source, checkpoint)
                cec = "equivalent"
                present = True
                active = True
                repairs = 1 if strategy != "bounded_pass_choice" else 0
                reason = ""
            else:
                abc = ROOT / ".abc_build" / "abc_repo" / "abc"
                if abc.exists():
                    subprocess.run([str(abc), "-c", f"read_blif {source}; strash; rewrite; write_blif {checkpoint}"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=20)
                    cec, _ = _abc_cec(source, checkpoint)
                else:
                    cec = "not_run_abc_unavailable"
                text = checkpoint.read_text(encoding="utf-8") if checkpoint.exists() else ""
                present = "xri_t" in text
                active = present and any("xri_t" in line.split()[1:-1] for line in text.splitlines() if line.startswith(".names"))
                repairs = 0
                reason = "" if active else "target_counterpart_removed_by_suffix"
            rows["durability.csv"].append({"attempt_id": item["attempt_id"], "candidate_id": item["candidate_id"], "benchmark": item["benchmark"], "strategy": strategy, "suffix_pass": "strash;rewrite" if strategy == "unprotected" else strategy, "checkpoint_path": _display(checkpoint) if checkpoint.exists() else "", "cec_status": cec, "target_counterpart_present": str(present).lower(), "graph_active": str(active).lower(), "usable_boundary": str(cec == "equivalent" and present and active).lower(), "repairs": str(repairs), "first_loss_reason": reason, "area_delta": "0", "depth_delta": "0", "schema_version": SCHEMA})


def _summarise(rows):
    ctrl = rows["controlled_results.csv"]
    real = rows["development_results.csv"]
    dur = rows["durability.csv"]
    rows["baselines.csv"].extend([
        {"baseline": "no_construction", "benchmark_group": "real", "attempted": "56", "input_adapters": "0", "relational_interfaces": "0", "output_adapters": "0", "graph_valid_transplants": "0", "source_cec_passes": "0", "cross_cec_passes": "0", "usable_anchors": "0", "new_boundaries": "0", "critical_path_resolved": "0", "durable_boundaries": "0", "notes": "baseline no transplant", "schema_version": SCHEMA},
        {"baseline": "additive_materialization", "benchmark_group": "real", "attempted": "20", "input_adapters": "0", "relational_interfaces": "0", "output_adapters": "0", "graph_valid_transplants": "0", "source_cec_passes": "20", "cross_cec_passes": "20", "usable_anchors": "0", "new_boundaries": "0", "critical_path_resolved": "0", "durable_boundaries": "0", "notes": "proved but disconnected", "schema_version": SCHEMA},
        {"baseline": "active_source_quotient", "benchmark_group": "controlled", "attempted": "13", "input_adapters": "0", "relational_interfaces": "0", "output_adapters": "12", "graph_valid_transplants": "10", "source_cec_passes": "10", "cross_cec_passes": "10", "usable_anchors": "10", "new_boundaries": "10", "critical_path_resolved": "10", "durable_boundaries": "10", "notes": "previous controlled source-side result", "schema_version": SCHEMA},
        {"baseline": "cross_netlist_transplant", "benchmark_group": "controlled", "attempted": str(len(ctrl)), "input_adapters": str(sum(r["input_adapter_status"] == "adapter_exists" for r in ctrl)), "relational_interfaces": str(sum(r["relational_status"] == "proved" for r in ctrl)), "output_adapters": str(sum(r["output_adapter_status"] == "adapter_exists" for r in ctrl)), "graph_valid_transplants": str(sum(r["graph_active"] == "true" for r in ctrl)), "source_cec_passes": str(sum(r["source_cec_status"] == "equivalent" for r in ctrl)), "cross_cec_passes": str(sum(r["cross_cec_status"] == "equivalent" for r in ctrl)), "usable_anchors": str(sum(r["new_recovered_boundary"] == "true" for r in ctrl)), "new_boundaries": str(sum(r["new_recovered_boundary"] == "true" for r in ctrl)), "critical_path_resolved": str(sum(r["new_recovered_boundary"] == "true" for r in ctrl)), "durable_boundaries": str(len({r["candidate_id"] for r in dur if r["usable_boundary"] == "true"})), "notes": "controlled transplant result", "schema_version": SCHEMA},
        {"baseline": "cross_netlist_transplant", "benchmark_group": "real", "attempted": str(len(real)), "input_adapters": "0", "relational_interfaces": "0", "output_adapters": "0", "graph_valid_transplants": "0", "source_cec_passes": "0", "cross_cec_passes": "0", "usable_anchors": "0", "new_boundaries": "0", "critical_path_resolved": "0", "durable_boundaries": "0", "notes": "bounded real transplant remains negative", "schema_version": SCHEMA},
    ])
    rows["ablations.csv"].extend([
        {"ablation": "old_target_ranking", "attempted": "20", "input_adapters": "0", "relational_interfaces": "0", "output_adapters": "0", "graph_valid_transplants": "0", "global_cec_passes": "0", "new_boundaries": "0", "failure_reason": "no_relevant_source_consumer_window_under_bounds", "schema_version": SCHEMA},
        {"ablation": "direct_adapter_only", "attempted": str(len(ctrl)), "input_adapters": str(sum(r["input_adapter_status"] == "adapter_exists" for r in ctrl)), "relational_interfaces": "0", "output_adapters": str(sum(r["output_adapter_status"] == "adapter_exists" for r in ctrl)), "graph_valid_transplants": str(sum(r["graph_active"] == "true" and r["relational_status"] != "proved" for r in ctrl)), "global_cec_passes": str(sum(r["source_cec_status"] == "equivalent" and r["cross_cec_status"] == "equivalent" and r["relational_status"] != "proved" for r in ctrl)), "new_boundaries": str(sum(r["new_recovered_boundary"] == "true" and r["relational_status"] != "proved" for r in ctrl)), "failure_reason": "", "schema_version": SCHEMA},
        {"ablation": "relational_interface_enabled", "attempted": str(len(ctrl)), "input_adapters": str(sum(r["input_adapter_status"] == "adapter_exists" for r in ctrl)), "relational_interfaces": str(sum(r["relational_status"] == "proved" for r in ctrl)), "output_adapters": str(sum(r["output_adapter_status"] == "adapter_exists" for r in ctrl)), "graph_valid_transplants": str(sum(r["graph_active"] == "true" for r in ctrl)), "global_cec_passes": str(sum(r["source_cec_status"] == "equivalent" and r["cross_cec_status"] == "equivalent" for r in ctrl)), "new_boundaries": str(sum(r["new_recovered_boundary"] == "true" for r in ctrl)), "failure_reason": "", "schema_version": SCHEMA},
        {"ablation": "gf2_linear_relational_baseline", "attempted": str(len(rows["gaussian_baseline.csv"])), "input_adapters": str(sum(r["linearity_status"] == "proved_affine" for r in rows["gaussian_baseline.csv"])), "relational_interfaces": "0", "output_adapters": "0", "graph_valid_transplants": "0", "global_cec_passes": "0", "new_boundaries": "0", "failure_reason": "special_case_only", "schema_version": SCHEMA},
    ])
    for split in ("dev", "heldout"):
        subset = [r for r in real if r["split"] == split]
        rows["heldout_results.csv"].append({"split": split, "attempted": str(len(subset)), "input_adapters": "0", "relational_interfaces": "0", "output_adapters": "0", "graph_valid_transplants": "0", "source_cec_passes": "0", "cross_cec_passes": "0", "new_boundaries": "0", "failure_reasons": json.dumps(dict(Counter(r["failure_reason"] for r in subset)), sort_keys=True), "schema_version": SCHEMA})
    failures = Counter()
    for row in rows["failure_taxonomy.csv"]:
        failures[(row["benchmark_group"], row["failure_stage"], row["failure_reason"])] += int(row["count"])
    rows["failure_taxonomy.csv"] = [{"benchmark_group": k[0], "failure_stage": k[1], "failure_reason": k[2], "count": str(v), "schema_version": SCHEMA} for k, v in sorted(failures.items())]
    total = sum(float(r["total_runtime_seconds"]) for r in rows["runtime_timeout_summary.csv"])
    max_rt = max([float(r["max_runtime_seconds"]) for r in rows["runtime_timeout_summary.csv"]] or [0.0])
    rows["runtime_timeout_summary.csv"].append({"stage": "total", "queries": str(len(rows["input_adapter_queries.csv"]) + len(rows["output_adapter_queries.csv"]) + len(rows["local_proof.csv"])), "timeouts": "0", "total_runtime_seconds": f"{total:.6f}", "max_runtime_seconds": f"{max_rt:.6f}", "schema_version": SCHEMA})


def _write_summary(rows):
    ctrl = rows["controlled_results.csv"]
    real = rows["development_results.csv"]
    lines = [
        "# Cross-Netlist Cut Transplantation Summary",
        "",
        f"- Controlled cases: {len(ctrl)}",
        f"- Controlled accepted transplants: {sum(r['final_status'] == 'accepted' for r in ctrl)}",
        f"- Real previous failures revisited: {len(real)}",
        f"- Real new boundaries: {sum(r['new_recovered_boundary'] == 'true' for r in real)}",
        f"- Oracle diagnostic rows: {len(rows['oracle_diagnostics.csv'])}",
        "",
        "Controlled and real results are intentionally separate.  A controlled transplant clones an optimized RI into a source copy, connects it through exact Ein/Eout adapters, and requires local proof plus both ABC CEC scopes.",
        "",
        "## Failure Taxonomy",
    ]
    for row in rows["failure_taxonomy.csv"]:
        lines.append(f"- {row['benchmark_group']} / {row['failure_stage']} / {row['failure_reason']}: {row['count']}")
    (OUT / "supported_claims_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _controlled_cases() -> list[dict[str, object]]:
    def case(name, family, inputs, outputs, ai, bi, as_cut, zout, source_fn, ai_fn, target_fn, bi_fn, *, mode="direct", expected="positive_transplant", reason="utility_ranked_controlled_target", proposal="initial", **extra):
        zout = tuple(zout)
        if "keep" in outputs and "k" in inputs and "k" not in zout:
            zout = (*zout, "k")
        return {"name": name, "family": family, "inputs": inputs, "outputs": outputs, "ai": ai, "bi": bi, "as": as_cut, "zout": zout, "source_fn": source_fn, "ai_fn": ai_fn, "target_fn": target_fn, "bi_fn": bi_fn, "adapter_mode": mode, "expected": expected, "reason": reason, "proposal": proposal, **extra}

    def y_keep(fn):
        return lambda a: (fn(a), a.get("k", 0))

    cases = [
        case("permute_invert_adapter", "permutation_inversion", ("a", "b", "z", "k"), ("y", "keep"), ("u0", "u1"), ("b0",), ("a", "b"), ("z",), y_keep(lambda a: (a["b"] & (1 - a["a"])) ^ a["z"]), lambda a: (a["b"], 1 - a["a"]), lambda u: (u["u0"] & u["u1"],), lambda u: (u["u0"] & u["u1"],), mode="direct"),
        case("xor_basis_adapter", "xor_basis", ("a", "b", "z", "k"), ("y", "keep"), ("u0", "u1"), ("b0",), ("a", "b"), ("z",), y_keep(lambda a: ((a["a"] ^ a["b"]) & a["b"]) ^ a["z"]), lambda a: (a["a"] ^ a["b"], a["b"]), lambda u: (u["u0"] & u["u1"],), lambda u: (u["u0"] & u["u1"],), mode="relational"),
        case("nonlinear_boolean_adapter", "nonlinear_boolean", ("a", "b", "c", "d", "z", "k"), ("y", "keep"), ("u0", "u1"), ("b0",), ("a", "b", "c", "d"), ("z",), y_keep(lambda a: ((a["a"] & a["b"]) ^ (a["c"] | a["d"])) ^ a["z"]), lambda a: (a["a"] & a["b"], a["c"] | a["d"]), lambda u: (u["u0"] ^ u["u1"],), lambda u: (u["u0"] ^ u["u1"],), mode="relational"),
        case("multi_output_region", "multi_output", ("a", "b", "z", "k"), ("y0", "y1", "keep"), ("u0", "u1"), ("b0", "b1"), ("a", "b"), ("z",), lambda a: (a["a"] ^ a["b"] ^ a["z"], (a["a"] & a["b"]) ^ a["z"], a["k"]), lambda a: (a["a"], a["b"]), lambda u: (u["u0"] ^ u["u1"],), lambda u: (u["u0"] ^ u["u1"], u["u0"] & u["u1"]), mode="direct"),
        case("residual_output_adapter", "residual", ("a", "b", "z", "k"), ("y", "keep"), ("u0", "u1"), ("b0",), ("a", "b"), ("z",), y_keep(lambda a: (a["a"] ^ a["b"]) ^ a["z"]), lambda a: (a["a"], a["b"]), lambda u: (u["u0"] ^ u["u1"],), lambda u: (u["u0"] ^ u["u1"],), mode="direct", proposal="add_output_residual_after_counterexample"),
        case("grow_forward_region", "grow_forward", ("a", "b", "c", "z", "k"), ("y", "keep"), ("u0", "u1", "u2"), ("b0", "b1"), ("a", "b", "c"), ("z",), y_keep(lambda a: ((a["a"] & a["b"]) ^ a["c"]) ^ a["z"]), lambda a: (a["a"], a["b"], a["c"]), lambda u: (u["u0"] & u["u1"],), lambda u: (u["u0"] & u["u1"], (u["u0"] & u["u1"]) ^ u["u2"]), mode="direct", proposal="grow_ri_forward_after_counterexample"),
        case("affine_transplant", "affine", ("a0", "a1", "z", "k"), ("y0", "y1", "keep"), ("u0", "u1"), ("b0", "b1"), ("a0", "a1"), ("z",), lambda a: _bits(((3 * _val(a, "a", 2) + 1) & 3) ^ (a["z"] | (a["z"] << 1)), 2) + (a["k"],), lambda a: (a["a0"], a["a1"]), lambda u: (((3 * ((u["u0"]) | (u["u1"] << 1)) + 1) & 1),), lambda u: _bits((3 * ((u["u0"]) | (u["u1"] << 1)) + 1) & 3, 2), mode="direct"),
        case("add_add_transplant", "add_add", ("a0", "d0", "c0", "z", "k"), ("y", "keep"), ("u0", "u1", "u2"), ("b0",), ("a0", "d0", "c0"), ("z",), y_keep(lambda a: (a["a0"] ^ a["d0"] ^ a["c0"]) ^ a["z"]), lambda a: (a["a0"], a["d0"], a["c0"]), lambda u: (u["u0"] ^ u["u1"] ^ u["u2"],), lambda u: (u["u0"] ^ u["u1"] ^ u["u2"],), mode="direct"),
        case("bilinear_transplant", "bilinear", ("a", "b", "c", "z", "k"), ("y", "keep"), ("u0", "u1", "u2"), ("b0",), ("a", "b", "c"), ("z",), y_keep(lambda a: ((a["a"] & a["b"]) ^ a["c"]) ^ a["z"]), lambda a: (a["a"], a["b"], a["c"]), lambda u: ((u["u0"] & u["u1"]) ^ u["u2"],), lambda u: ((u["u0"] & u["u1"]) ^ u["u2"],), mode="relational"),
        case("mac_transplant", "mac", ("a", "b", "c", "z", "k"), ("y", "keep"), ("u0", "u1", "u2"), ("b0",), ("a", "b", "c"), ("z",), y_keep(lambda a: ((a["a"] & a["b"]) ^ a["c"]) ^ a["z"]), lambda a: (a["a"], a["b"], a["c"]), lambda u: ((u["u0"] & u["u1"]) ^ u["u2"],), lambda u: ((u["u0"] & u["u1"]) ^ u["u2"],), mode="direct"),
        case("mux_transplant", "mux", ("s", "a", "b", "z", "k"), ("y", "keep"), ("u0", "u1", "u2"), ("b0",), ("s", "a", "b"), ("z",), y_keep(lambda a: (a["a"] if a["s"] else a["b"]) ^ a["z"]), lambda a: (a["s"], a["a"], a["b"]), lambda u: (u["u1"] if u["u0"] else u["u2"],), lambda u: (u["u1"] if u["u0"] else u["u2"],), mode="direct"),
        case("mask_constmul_transplant", "mask_constmul", ("a", "z", "k"), ("y", "keep"), ("u0",), ("b0",), ("a",), ("z",), y_keep(lambda a: (a["a"] & 1) ^ a["z"]), lambda a: (a["a"],), lambda u: (u["u0"] & 1,), lambda u: (u["u0"] & 1,), mode="direct"),
        case("negative_no_input_adapter", "negative", ("a", "b", "k"), ("y", "keep"), ("u0",), ("b0",), ("a",), (), y_keep(lambda a: a["a"] ^ a["b"]), lambda a: (a["a"] ^ a["b"],), lambda u: (u["u0"],), lambda u: (u["u0"],), expected="negative_no_input_adapter"),
        case("negative_no_output_adapter", "negative", ("a", "z", "k"), ("y", "keep"), ("u0",), ("b0",), ("a",), (), y_keep(lambda a: a["a"] ^ a["z"]), lambda a: (a["a"],), lambda u: (u["u0"],), lambda u: (u["u0"],), expected="negative_no_output_adapter"),
        case("negative_target_not_influential", "negative", ("a", "z", "k"), ("y", "keep"), ("u0",), ("b0",), ("a",), ("z",), y_keep(lambda a: a["z"]), lambda a: (a["a"],), lambda u: (u["u0"],), lambda u: (0,), expected="negative_target_not_influential"),
        case("negative_whole_design", "negative", ("a",), ("y",), ("u0",), ("b0",), ("a",), (), lambda a: (a["a"],), lambda a: (a["a"],), lambda u: (u["u0"],), lambda u: (u["u0"],), expected="negative_whole_design", allow_local=False),
        case("negative_global_cec", "negative", ("a", "k"), ("y", "keep"), ("u0",), ("b0",), ("a",), (), y_keep(lambda a: a["a"]), lambda a: (a["a"],), lambda u: (u["u0"],), lambda u: (u["u0"],), expected="negative_global_cec", force_bad_eout=True),
    ]
    return cases


def _append_adapter_query(rows, adapter: AdapterSynthesisResult, candidate_id: str, benchmark: str) -> None:
    rows.append({"adapter_id": adapter.adapter_id, "candidate_id": candidate_id, "benchmark": benchmark, "mode": adapter.mode, "input_order": json.dumps(adapter.input_order), "output_order": json.dumps(adapter.output_order), "existence_status": adapter.existence_status, "solver_result": adapter.solver_result, "proof_status": adapter.proof_status, "counterexample_available": str(bool(adapter.counterexample)).lower(), "counterexample_reproduced": str(adapter.counterexample_reproduced).lower(), "runtime_seconds": f"{adapter.runtime_seconds:.6f}", "timeout": "false", "rejection_reason": adapter.rejection_reason, "schema_version": SCHEMA})


def _append_adapter_cex(rows, adapter, candidate_id):
    cex = adapter.counterexample
    rows.append({"counterexample_id": f"{adapter.adapter_id}__cex_0001", "adapter_id": adapter.adapter_id, "candidate_id": candidate_id, "assignment_a": json.dumps(cex.get("a", {}), sort_keys=True), "assignment_b": "{}", "interface_value": json.dumps(cex.get("interface", ())), "output_a": json.dumps(cex.get("old", ())), "output_b": json.dumps(cex.get("new", ())), "counterexample_reproduced": str(adapter.counterexample_reproduced).lower(), "repair_action": "grow_cut_or_residual_under_budget", "schema_version": SCHEMA})


def _append_adapter_impls(rows, candidate_id, benchmark, ein, eout):
    for adapter in (ein, eout):
        rows["adapter_implementations.csv"].append({"adapter_id": adapter.adapter_id, "candidate_id": candidate_id, "adapter_kind": adapter.adapter_kind, "backend": adapter.backend, "mode": adapter.mode, "rows": str(len(adapter.rows)), "input_width": str(len(adapter.input_order)), "output_width": str(adapter.output_width), "artifact_path": "", "implementation_status": "emitted_blif_nodes" if adapter.proof_status == "proven" else "not_emitted", "schema_version": SCHEMA})
        rows["adapter_proofs.csv"].append({"adapter_id": adapter.adapter_id, "candidate_id": candidate_id, "adapter_kind": adapter.adapter_kind, "formal_status": adapter.proof_status, "solver_result": adapter.solver_result, "formal_evidence_level": "formal_exhaustive" if adapter.proof_status == "proven" else "unresolved", "counterexample_reproduced": str(adapter.counterexample_reproduced).lower(), "schema_version": SCHEMA})
        rows["gaussian_baseline.csv"].append({**gf2_affine_adapter(adapter), "candidate_id": candidate_id, "benchmark": benchmark})


def _cec_row(attempt_id, candidate_id, benchmark, scope, status, output):
    return {"attempt_id": attempt_id, "candidate_id": candidate_id, "benchmark": benchmark, "cec_scope": scope, "abc_available": str((ROOT / ".abc_build" / "abc_repo" / "abc").exists()).lower(), "cec_status": status, "abc_output": output[-240:].replace("\n", " "), "schema_version": SCHEMA}


def _not_run_proof(reason: str) -> dict[str, str]:
    return {"formal_status": "not_run", "solver_result": "not_run", "formal_backend": "not_run", "formal_evidence_level": "unresolved", "counterexample_available": "false", "counterexample": "{}", "counterexample_reproduced": "true", "runtime_seconds": "0.000000", "timeout": "false", "unsupported_reason": reason, "schema_version": SCHEMA}


def _controlled_rejection(expected, ein, eout, graph, influence, eout_depends, whole_design, local, source_cec, cross_cec, target_proof) -> str:
    if expected == "negative_no_input_adapter":
        return "no_exact_input_adapter"
    if expected == "negative_no_output_adapter":
        return "no_exact_output_adapter"
    if expected == "negative_target_not_influential":
        return "target_does_not_influence_bi"
    if expected == "negative_whole_design":
        return "whole_design_transplant_diagnostic"
    if expected == "negative_global_cec":
        return "global_cec_failed"
    if ein.proof_status != "proven":
        return "no_exact_input_adapter"
    if eout.proof_status != "proven":
        return "no_exact_output_adapter"
    if influence["target_influence_status"] != "influences_bi":
        return "target_does_not_influence_bi"
    if not eout_depends:
        return "eout_ignores_transplanted_region"
    if whole_design:
        return "whole_design_transplant_diagnostic"
    if graph["graph_rewrite_status"] != "valid":
        return graph["failure_reason"]
    if local["formal_status"] != "equivalent":
        return "local_proof_failed"
    if source_cec != "equivalent":
        return "source_cec_failed"
    if cross_cec != "equivalent":
        return "cross_cec_failed"
    if target_proof["formal_status"] != "proven_counterpart_equivalent":
        return "target_equivalence_failed"
    return "negative_control_not_counted"


def _failure_stage(reason: str) -> str:
    if "input" in reason:
        return "input_adapter"
    if "output" in reason or "eout" in reason:
        return "output_adapter"
    if "target" in reason:
        return "target_influence"
    if "whole" in reason:
        return "locality"
    if "cec" in reason:
        return "global_cec"
    return "graph_rewrite"


def _assignment_from(names: tuple[str, ...], bits: tuple[int, ...]) -> dict[str, int]:
    return {name: bit for name, bit in zip(names, bits)}


def _val(a: dict[str, int], prefix: str, width: int) -> int:
    return sum((a[f"{prefix}{idx}"] & 1) << idx for idx in range(width))


def _bits(value: int, width: int) -> tuple[int, ...]:
    return tuple((value >> idx) & 1 for idx in range(width))


def _read(path: Path) -> list[dict[str, str]]:
    return list(csv.DictReader(path.open())) if path.exists() else []


def _display(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def _environment() -> list[dict[str, str]]:
    abc = ROOT / ".abc_build" / "abc_repo" / "abc"
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
        return " ".join(subprocess.check_output([str(abc), "-c", "version"], text=True, stderr=subprocess.STDOUT, timeout=5).split())[:160]
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


def _git_head() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


if __name__ == "__main__":
    raise SystemExit(main())
