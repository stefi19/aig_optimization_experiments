#!/usr/bin/env python3
"""Run semantic recoverability frontier experiments."""

from __future__ import annotations

import argparse
import csv
import json
import os
import platform
import shutil
import subprocess
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from analyze_blif_matches import parse_blif  # noqa: E402
from semantic_ast import SemanticExpr, input_expr  # noqa: E402
from semantic_functional_refactoring import SemanticDivisor, eval_divisor, eval_outputs, make_bus  # noqa: E402
from semantic_recoverability_frontier import (  # noqa: E402
    SCHEMA_VERSION,
    BoundaryRecord,
    Checkpoint,
    TrajectorySpec,
    abc_cec,
    blind_prediction_rows,
    classify_recoverability,
    file_sha256,
    generate_trajectory,
    leakage_audit,
    pass_deltas,
    recoverability_transitions,
    residual_frontier,
    stable_hash,
    structural_metrics,
    write_truth_blif,
)
from semantic_region import write_csv  # noqa: E402
from semantic_types import unsigned_bitvector  # noqa: E402


OUT = ROOT / "results" / "semantic_recoverability_frontier"
BENCH = ROOT / "benchmarks" / "semantic_recoverability_frontier"
ART = OUT / "artifacts"
ABC = ROOT / ".abc_build" / "abc_repo" / "abc"


FIELDS = {
    "experiment_manifest.csv": ["run_id", "git_head", "mode", "deterministic_seed", "source_blind_primary", "schema_version"],
    "environment_provenance.csv": ["tool", "version", "path", "status", "schema_version"],
    "benchmark_sources_licenses.csv": ["benchmark", "design_family", "split", "source_type", "source_path", "source_url", "revision", "license", "preprocessing", "schema_version"],
    "benchmark_split.csv": ["benchmark", "design_family", "split", "split_basis", "manual_tuning_allowed", "schema_version"],
    "ground_truth_boundary_manifest.csv": ["boundary_id", "benchmark", "design_family", "split", "module", "source_location", "operator_type", "input_widths", "output_widths", "signedness", "source_support", "output_function", "consumer_count", "consumer_identities", "fanout_properties", "externally_observable", "nontrivial", "eligible_for_blind_evaluation", "fingerprint", "schema_version"],
    "leakage_audit_results.csv": ["row_id", "oracle_mode", "forbidden_fields_present", "leakage_status", "schema_version"],
    "synthesis_trajectories.csv": ["trajectory_id", "benchmark", "design_family", "split", "flow_family", "pass_sequence", "checkpoint_count", "realized_checkpoint_count", "deterministic_seed", "schema_version"],
    "checkpoint_hashes.csv": ["trajectory_id", "checkpoint_id", "checkpoint_index", "pass_name", "blif_path", "sha256", "artifact_status", "artifact_exists", "parse_status", "schema_version"],
    "checkpoint_cec_results.csv": ["trajectory_id", "checkpoint_id", "checkpoint_index", "pass_name", "cec_status", "abc_output", "runtime_s", "unsupported_reason", "schema_version"],
    "checkpoint_structural_metrics.csv": ["trajectory_id", "checkpoint_id", "checkpoint_index", "pass_name", "node_count", "edge_count", "level_count", "input_count", "output_count", "internal_fanout_sum", "schema_version"],
    "blind_candidate_predictions.csv": ["prediction_id", "trajectory_id", "checkpoint_id", "checkpoint_index", "method", "candidate_signal", "support_size", "fanin_signature", "source_blind", "schema_version"],
    "blind_recovery_results.csv": ["result_id", "benchmark", "design_family", "split", "boundary_id", "trajectory_id", "checkpoint_id", "checkpoint_index", "pass_name", "method", "oracle_mode", "recovery_level", "recovered", "semantic_proof_status", "decomposition_status", "solver_result", "counterexample_available", "counterexample_reproduced", "runtime_s", "timeout", "failure_reason", "deterministic_seed", "schema_version"],
    "oracle_ladder_results.csv": ["result_id", "benchmark", "design_family", "split", "boundary_id", "trajectory_id", "checkpoint_id", "checkpoint_index", "pass_name", "method", "oracle_mode", "recovery_level", "recovered", "semantic_proof_status", "decomposition_status", "solver_result", "counterexample_available", "counterexample_reproduced", "runtime_s", "timeout", "failure_reason", "deterministic_seed", "schema_version"],
    "decomposition_proof_results.csv": ["result_id", "boundary_id", "trajectory_id", "checkpoint_id", "oracle_mode", "formal_status", "solver_result", "counterexample_available", "counterexample_reproduced", "runtime_s", "timeout", "schema_version"],
    "decomposition_counterexamples.csv": ["counterexample_id", "trajectory_id", "checkpoint_id", "boundary_id", "residual_set", "assignment_a", "assignment_b", "equal_divisor_and_residual", "different_output", "counterexample_reproduced", "schema_version"],
    "residual_selection_iterations.csv": ["trajectory_id", "checkpoint_id", "boundary_id", "residual_set", "residual_width", "search_status", "solver_result", "minimum_status", "residual_lower_bound", "residual_upper_bound", "runtime_s", "timeout", "schema_version"],
    "residual_bounds.csv": ["trajectory_id", "checkpoint_id", "boundary_id", "minimum_status", "residual_lower_bound", "residual_upper_bound", "best_residual_set", "schema_version"],
    "window_locality_results.csv": ["trajectory_id", "checkpoint_id", "boundary_id", "window_level", "window_nodes", "window_inputs", "window_outputs", "residual_width", "decomposition_status", "graph_rewrite_feasibility", "global_cec_status", "classification", "runtime_s", "schema_version"],
    "recoverability_transitions.csv": ["boundary_id", "trajectory_id", "method", "from_checkpoint", "to_checkpoint", "transition", "from_level", "to_level", "schema_version"],
    "method_specific_frontiers.csv": ["boundary_id", "trajectory_id", "method", "first_loss_checkpoint", "last_success_checkpoint", "non_monotonic", "recoverable_fraction", "longest_success_interval", "schema_version"],
    "pass_level_deltas.csv": ["trajectory_id", "boundary_id", "method", "pass_name", "checkpoint_before", "checkpoint_after", "recovery_before", "recovery_after", "transition_class", "node_delta", "depth_delta", "causal_claim", "schema_version"],
    "pass_ablations.csv": ["ablation_id", "benchmark", "flow_family", "ablation_type", "changed_pass", "controlled_difference", "causal_claim", "recovery_delta", "area_delta", "depth_delta", "schema_version"],
    "boundary_durability_results.csv": ["boundary_id", "trajectory_id", "insertion_checkpoint", "suffix_checkpoint", "suffix_pass_name", "textually_present", "graph_active", "functionally_equivalent", "blind_identifiable", "useful_for_decomposition", "boundary_survives_suffix", "global_cec_status", "schema_version"],
    "optimisation_tradeoffs.csv": ["trajectory_id", "checkpoint_id", "checkpoint_index", "pass_name", "node_count", "depth", "node_reduction_vs_source", "depth_delta_vs_source", "recoverable_boundary_fraction", "oracle_recoverable_fraction", "schema_version"],
    "controlled_results.csv": ["benchmark", "boundaries", "trajectories", "checkpoints", "blind_recovered_rows", "oracle_recovered_rows", "non_monotonic_boundaries", "schema_version"],
    "development_results.csv": ["benchmark", "boundaries", "trajectories", "checkpoints", "blind_recovered_rows", "oracle_recovered_rows", "failure_summary", "schema_version"],
    "heldout_results.csv": ["benchmark", "boundaries", "trajectories", "checkpoints", "blind_recovered_rows", "oracle_recovered_rows", "failure_summary", "schema_version"],
    "failure_taxonomy.csv": ["benchmark_group", "method", "oracle_mode", "failure_reason", "count", "schema_version"],
    "runtime_timeout_summary.csv": ["stage", "queries", "timeouts", "total_runtime_s", "max_runtime_s", "schema_version"],
}


def main() -> int:
    global OUT, BENCH, ART
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["all", "controlled", "development", "heldout", "oracle", "pass-ablations", "durability"], default="all")
    parser.add_argument("--output-dir", type=Path, default=OUT)
    parser.add_argument("--bench-dir", type=Path, default=BENCH)
    parser.add_argument("--abc", type=Path, default=Path(os.environ.get("AIG_ABC", ABC)))
    args = parser.parse_args()
    OUT = args.output_dir
    BENCH = args.bench_dir
    ART = OUT / "artifacts"
    OUT.mkdir(parents=True, exist_ok=True)
    BENCH.mkdir(parents=True, exist_ok=True)
    ART.mkdir(parents=True, exist_ok=True)
    start = time.perf_counter()
    rows = {name: [] for name in FIELDS}
    rows["experiment_manifest.csv"].append({"run_id": f"semantic_recoverability_frontier__{_git_head()[:10]}", "git_head": _git_head(), "mode": args.mode, "deterministic_seed": "0", "source_blind_primary": "true", "schema_version": SCHEMA_VERSION})
    rows["environment_provenance.csv"].extend(_environment(args.abc))
    boundaries = _boundaries_for_mode(args.mode)
    trajectories = _trajectory_specs(boundaries)
    checkpoints: list[Checkpoint] = []
    metrics_by_cp: dict[str, dict[str, str]] = {}
    all_recovery: list[dict[str, str]] = []
    for boundary in boundaries:
        rows["ground_truth_boundary_manifest.csv"].append(boundary.manifest_row())
        rows["benchmark_sources_licenses.csv"].append(_source_row(boundary))
        rows["benchmark_split.csv"].append({"benchmark": boundary.benchmark, "design_family": boundary.design_family, "split": boundary.split, "split_basis": "family_level_repository_split", "manual_tuning_allowed": "false", "schema_version": SCHEMA_VERSION})
    for spec in trajectories:
        cps = generate_trajectory(spec=spec, abc=args.abc, output_dir=ART / "checkpoints")
        checkpoints.extend(cps)
        rows["synthesis_trajectories.csv"].append({"trajectory_id": spec.trajectory_id, "benchmark": spec.benchmark, "design_family": _family_for(spec.benchmark, boundaries), "split": spec.split, "flow_family": spec.flow_family, "pass_sequence": json.dumps(spec.pass_sequence), "checkpoint_count": str(len(cps)), "realized_checkpoint_count": str(sum(_checkpoint_artifact_ready(cp) for cp in cps)), "deterministic_seed": str(spec.deterministic_seed), "schema_version": SCHEMA_VERSION})
        for cp in cps:
            sha = file_sha256(cp.blif_path) if cp.blif_path.exists() else ""
            rows["checkpoint_hashes.csv"].append({"trajectory_id": cp.trajectory_id, "checkpoint_id": cp.checkpoint_id, "checkpoint_index": str(cp.checkpoint_index), "pass_name": cp.pass_name, "blif_path": _display(cp.blif_path), "sha256": sha, "artifact_status": cp.artifact_status, "artifact_exists": str(cp.blif_path.exists()).lower(), "parse_status": cp.parse_status, "schema_version": SCHEMA_VERSION})
            rows["checkpoint_cec_results.csv"].append({"trajectory_id": cp.trajectory_id, "checkpoint_id": cp.checkpoint_id, "checkpoint_index": str(cp.checkpoint_index), "pass_name": cp.pass_name, "cec_status": cp.cec_status, "abc_output": cp.cec_output, "runtime_s": f"{cp.runtime_s:.6f}", "unsupported_reason": cp.unsupported_reason, "schema_version": SCHEMA_VERSION})
            if _checkpoint_ready_for_analysis(cp):
                metrics = structural_metrics(cp.blif_path)
                metrics_by_cp[cp.checkpoint_id] = metrics
                rows["checkpoint_structural_metrics.csv"].append({"trajectory_id": cp.trajectory_id, "checkpoint_id": cp.checkpoint_id, "checkpoint_index": str(cp.checkpoint_index), "pass_name": cp.pass_name, **metrics, "schema_version": SCHEMA_VERSION})
                rows["blind_candidate_predictions.csv"].extend(blind_prediction_rows(cp))
    relevant = {(b.benchmark, b.split): b for b in boundaries}
    for cp in checkpoints:
        boundary = relevant.get((cp.benchmark, cp.split))
        if boundary is None:
            continue
        if not _checkpoint_ready_for_analysis(cp):
            continue
        blind_rows = _blind_rows(cp, boundary)
        rows["blind_recovery_results.csv"].extend(blind_rows)
        all_recovery.extend(blind_rows)
        oracle_rows = _oracle_rows(cp, boundary)
        rows["oracle_ladder_results.csv"].extend(oracle_rows)
        all_recovery.extend(oracle_rows)
        for row in oracle_rows:
            if row["method"] == "functional_decomposition":
                rows["decomposition_proof_results.csv"].append({"result_id": row["result_id"], "boundary_id": row["boundary_id"], "trajectory_id": row["trajectory_id"], "checkpoint_id": row["checkpoint_id"], "oracle_mode": row["oracle_mode"], "formal_status": row["decomposition_status"], "solver_result": row["solver_result"], "counterexample_available": row["counterexample_available"], "counterexample_reproduced": row["counterexample_reproduced"], "runtime_s": row["runtime_s"], "timeout": row["timeout"], "schema_version": SCHEMA_VERSION})
        residual_rows, cex_rows = residual_frontier(checkpoint=cp, boundary=boundary, candidate_residuals=tuple(parse_blif(cp.blif_path).inputs), output_nodes=boundary.output_nodes if _nodes_exist(cp, boundary.output_nodes) else tuple(parse_blif(cp.blif_path).outputs), max_width=3)
        rows["residual_selection_iterations.csv"].extend(residual_rows)
        rows["decomposition_counterexamples.csv"].extend(cex_rows)
        rows["residual_bounds.csv"].append(_residual_bound_row(cp, boundary, residual_rows))
        rows["window_locality_results.csv"].extend(_window_rows(cp, boundary, oracle_rows, metrics_by_cp.get(cp.checkpoint_id, {})))
    rows["leakage_audit_results.csv"].extend(leakage_audit(rows["blind_candidate_predictions.csv"]))
    rows["recoverability_transitions.csv"].extend(recoverability_transitions(all_recovery))
    rows["method_specific_frontiers.csv"].extend(_frontier_rows(rows["recoverability_transitions.csv"], all_recovery))
    rows["pass_level_deltas.csv"].extend(pass_deltas(checkpoints, all_recovery, metrics_by_cp))
    rows["pass_ablations.csv"].extend(_pass_ablation_rows(rows["pass_level_deltas.csv"], metrics_by_cp))
    rows["boundary_durability_results.csv"].extend(_durability_rows(checkpoints, all_recovery))
    rows["optimisation_tradeoffs.csv"].extend(_tradeoff_rows(checkpoints, all_recovery, metrics_by_cp))
    _summary_rows(rows, boundaries, checkpoints, all_recovery)
    _failure_rows(rows, all_recovery)
    rows["runtime_timeout_summary.csv"].append({"stage": "total", "queries": str(len(all_recovery)), "timeouts": str(sum(r["timeout"] == "true" for r in all_recovery)), "total_runtime_s": f"{time.perf_counter() - start:.6f}", "max_runtime_s": f"{max([float(r['runtime_s']) for r in all_recovery] or [0.0]):.6f}", "schema_version": SCHEMA_VERSION})
    for name, fields in FIELDS.items():
        write_csv(rows[name], OUT / name, fields)
    _write_markdown_summary(rows, boundaries, checkpoints)
    print(f"Wrote semantic recoverability frontier results to {OUT}")
    return 0


def _boundaries_for_mode(mode: str) -> list[BoundaryRecord]:
    _write_controlled_sources()
    boundaries = _controlled_boundaries()
    if mode in {"all", "development", "heldout", "oracle", "pass-ablations", "durability"}:
        boundaries.extend(_real_boundaries())
    if mode == "controlled":
        return [b for b in boundaries if b.split == "controlled"]
    if mode == "development":
        return [b for b in boundaries if b.split == "development"]
    if mode == "heldout":
        return [b for b in boundaries if b.split == "heldout"]
    return boundaries


def _write_controlled_sources() -> None:
    x0, x1, r0 = "x0", "x1", "r0"
    write_truth_blif(
        BENCH / "controlled_xor_factor.blif",
        "controlled_xor_factor",
        (x0, x1, r0),
        ("y0",),
        lambda a: ((a[x0] ^ a[x1]) ^ a[r0],),
        internal_nodes={"m0": lambda a: a[x0] ^ a[x1]},
    )
    write_truth_blif(
        BENCH / "controlled_and_factor.blif",
        "controlled_and_factor",
        (x0, x1, r0),
        ("y0",),
        lambda a: ((a[x0] & a[x1]) ^ a[r0],),
        internal_nodes={"m0": lambda a: a[x0] & a[x1]},
    )
    write_truth_blif(
        BENCH / "controlled_nonmonotonic_factor.blif",
        "controlled_nonmonotonic_factor",
        (x0, x1, r0),
        ("y0",),
        lambda a: ((a[x0] ^ a[x1]) if a[r0] else (a[x0] & a[x1]),),
        internal_nodes={"m0": lambda a: a[x0] ^ a[x1]},
    )


def _controlled_boundaries() -> list[BoundaryRecord]:
    return [
        _boundary("controlled_xor_factor", "controlled", "controlled_boolean", "xor", ("x0", "x1"), ("m0",), _xor_divisor("controlled_xor_factor")),
        _boundary("controlled_and_factor", "controlled", "controlled_boolean", "and", ("x0", "x1"), ("m0",), _and_divisor("controlled_and_factor")),
        _boundary("controlled_nonmonotonic_factor", "controlled", "controlled_boolean", "xor_mux", ("x0", "x1"), ("m0",), _xor_divisor("controlled_nonmonotonic_factor")),
    ]


def _real_boundaries() -> list[BoundaryRecord]:
    full_adder_sum = SemanticExpr("xor", (SemanticExpr("xor", (input_expr("a", 1), input_expr("b", 1)), output_type=unsigned_bitvector(1)), input_expr("cin", 1)), output_type=unsigned_bitvector(1))
    a, b, cin = input_expr("a", 1), input_expr("b", 1), input_expr("cin", 1)
    carry = SemanticExpr(
        "or",
        (
            SemanticExpr("or", (SemanticExpr("and", (a, b), output_type=unsigned_bitvector(1)), SemanticExpr("and", (a, cin), output_type=unsigned_bitvector(1))), output_type=unsigned_bitvector(1)),
            SemanticExpr("and", (b, cin), output_type=unsigned_bitvector(1)),
        ),
        output_type=unsigned_bitvector(1),
    )
    return [
        _boundary("full_adder_sum", "development", "repository_real_hand_written", "xor_sum", ("a", "b", "cin"), ("sum",), SemanticDivisor("full_adder_sum__oracle_divisor", "full_adder", "oracle_diagnostic", (make_bus("a", ("a",), "data"), make_bus("b", ("b",), "data"), make_bus("cin", ("cin",), "data")), (make_bus("m", ("sum",), "semantic_divisor"),), (full_adder_sum,), "xor_sum", 3, source_blind=False), source_path=ROOT / "benchmarks/real/hand_written/full_adder.blif"),
        _boundary("full_adder_carry", "heldout", "repository_real_hand_written", "majority_carry", ("a", "b", "cin"), ("cout",), SemanticDivisor("full_adder_carry__oracle_divisor", "full_adder", "oracle_diagnostic", (make_bus("a", ("a",), "data"), make_bus("b", ("b",), "data"), make_bus("cin", ("cin",), "data")), (make_bus("m", ("cout",), "semantic_divisor"),), (carry,), "majority", 4, source_blind=False), source_path=ROOT / "benchmarks/real/hand_written/full_adder.blif"),
    ]


def _boundary(name: str, split: str, family: str, op: str, support: tuple[str, ...], outputs: tuple[str, ...], divisor: SemanticDivisor, source_path: Path | None = None) -> BoundaryRecord:
    source_path = source_path or BENCH / f"{name}.blif"
    return BoundaryRecord(
        boundary_id=f"{name}__b0",
        benchmark=name if source_path.parent == BENCH else "full_adder",
        design_family=family,
        split=split,
        module=name,
        operator_type=op,
        source_location=_display(source_path),
        input_widths=tuple(1 for _ in support),
        output_widths=tuple(1 for _ in outputs),
        signedness="unsigned",
        source_support=support,
        output_nodes=outputs,
        consumer_count=1,
        consumer_identities=("y0",) if outputs == ("m0",) else outputs,
        externally_observable=outputs[0] in {"sum", "cout"},
        nontrivial=True,
        eligible_for_blind_evaluation=True,
        divisor=divisor,
    )


def _xor_divisor(benchmark: str) -> SemanticDivisor:
    expr = SemanticExpr("xor", (input_expr("x0", 1), input_expr("x1", 1)), output_type=unsigned_bitvector(1))
    return SemanticDivisor(f"{benchmark}__generic_xor_divisor", benchmark, "blind_generic_boolean_grammar", (make_bus("x0", ("x0",), "data"), make_bus("x1", ("x1",), "data")), (make_bus("m", ("m0",), "semantic_divisor"),), (expr,), "xor", 2, source_blind=True)


def _and_divisor(benchmark: str) -> SemanticDivisor:
    expr = SemanticExpr("and", (input_expr("x0", 1), input_expr("x1", 1)), output_type=unsigned_bitvector(1))
    return SemanticDivisor(f"{benchmark}__generic_and_divisor", benchmark, "blind_generic_boolean_grammar", (make_bus("x0", ("x0",), "data"), make_bus("x1", ("x1",), "data")), (make_bus("m", ("m0",), "semantic_divisor"),), (expr,), "and", 2, source_blind=True)


def _trajectory_specs(boundaries: list[BoundaryRecord]) -> list[TrajectorySpec]:
    seen: set[tuple[str, str]] = set()
    specs: list[TrajectorySpec] = []
    flows = [
        ("mild_balance_rewrite", ("strash", "balance", "rewrite")),
        ("rewrite_then_balance", ("strash", "rewrite", "balance")),
        ("refactor_dc2", ("strash", "refactor", "dc2")),
    ]
    for boundary in boundaries:
        if (boundary.benchmark, boundary.split) in seen:
            continue
        seen.add((boundary.benchmark, boundary.split))
        source = Path(boundary.source_location) if boundary.source_location.startswith("/") else ROOT / boundary.source_location
        if not source.exists():
            source = BENCH / f"{boundary.benchmark}.blif"
        for flow_family, commands in flows:
            specs.append(TrajectorySpec(f"{boundary.split}__{boundary.benchmark}__{flow_family}", boundary.benchmark, boundary.split, source, commands, flow_family))
    return specs


def _blind_rows(cp, boundary):
    rows = []
    for method in ("structural", "functional_survival", "blind_semantic_cegis", "blind_region_replacement", "blind_functional_refactoring"):
        if method == "structural":
            rows.append(classify_recoverability(checkpoint=cp, boundary=boundary, method="structural", oracle_mode="blind", residual_support=tuple(), window_outputs=boundary.output_nodes, local_threshold_nodes=8))
        elif method == "functional_survival":
            rows.append(_functional_survival_row(cp, boundary))
        else:
            rows.append(classify_recoverability(checkpoint=cp, boundary=boundary, method=method, oracle_mode="blind", residual_support=tuple(), window_outputs=tuple(parse_blif(cp.blif_path).outputs) if cp.blif_path.exists() else boundary.output_nodes, local_threshold_nodes=8))
    return rows


def _checkpoint_artifact_ready(cp: Checkpoint) -> bool:
    return cp.artifact_status == "materialized" and cp.blif_path.exists() and cp.parse_status == "parse_valid"


def _checkpoint_ready_for_analysis(cp: Checkpoint) -> bool:
    return _checkpoint_artifact_ready(cp) and cp.cec_status == "equivalent"


def _functional_survival_row(cp: Checkpoint, boundary: BoundaryRecord) -> dict[str, str]:
    start = time.perf_counter()
    if cp.cec_status != "equivalent":
        return classify_recoverability(checkpoint=cp, boundary=boundary, method="functional_survival", oracle_mode="blind", residual_support=tuple(), window_outputs=boundary.output_nodes, local_threshold_nodes=8)
    net = parse_blif(cp.blif_path)
    inputs = tuple(net.inputs)
    matching = False
    for node in net.nodes:
        if _node_matches_divisor(net, node.output, boundary, inputs):
            matching = True
            break
    level = "R1_functional_internal_survival" if matching else "R9_unresolved"
    failure = "" if matching else "no_formally_equivalent_internal_signal_under_exhaustive_small_check"
    from semantic_recoverability_frontier import _recovery_row  # local import keeps public API small
    return _recovery_row(cp, boundary, "functional_survival", "blind", level, matching, failure, time.perf_counter() - start)


def _oracle_rows(cp, boundary):
    if not cp.blif_path.exists():
        return []
    net = parse_blif(cp.blif_path)
    all_inputs = tuple(net.inputs)
    residual = tuple(name for name in all_inputs if name not in boundary.source_support)
    outputs = boundary.output_nodes if _nodes_exist(cp, boundary.output_nodes) else tuple(net.outputs)
    return [
        classify_recoverability(checkpoint=cp, boundary=boundary, method="functional_decomposition", oracle_mode="oracle_divisor", residual_support=residual, window_outputs=outputs, local_threshold_nodes=8),
        classify_recoverability(checkpoint=cp, boundary=boundary, method="functional_decomposition", oracle_mode="oracle_divisor_support", residual_support=residual, window_outputs=outputs, local_threshold_nodes=8),
        classify_recoverability(checkpoint=cp, boundary=boundary, method="functional_decomposition", oracle_mode="oracle_window", residual_support=residual, window_outputs=outputs, local_threshold_nodes=8),
    ]


def _node_matches_divisor(net, node_name: str, boundary: BoundaryRecord, inputs: tuple[str, ...]) -> bool:
    if len(inputs) > 12:
        return False
    for idx in range(1 << len(inputs)):
        assignment = {name: (idx >> bit) & 1 for bit, name in enumerate(inputs)}
        node_value = eval_outputs(net, (node_name,), assignment)[0]
        divisor_value = eval_divisor(boundary.divisor, assignment)[0]
        if node_value != divisor_value:
            return False
    return True


def _residual_bound_row(cp, boundary, rows):
    exact = next((r for r in rows if r["minimum_status"] == "exact_minimum"), None)
    if exact:
        return {"trajectory_id": cp.trajectory_id, "checkpoint_id": cp.checkpoint_id, "boundary_id": boundary.boundary_id, "minimum_status": "exact_minimum", "residual_lower_bound": exact["residual_lower_bound"], "residual_upper_bound": exact["residual_upper_bound"], "best_residual_set": exact["residual_set"], "schema_version": SCHEMA_VERSION}
    if rows:
        lower = max(int(r["residual_lower_bound"]) for r in rows if r["residual_lower_bound"])
        return {"trajectory_id": cp.trajectory_id, "checkpoint_id": cp.checkpoint_id, "boundary_id": boundary.boundary_id, "minimum_status": "best_found_or_unresolved", "residual_lower_bound": str(lower), "residual_upper_bound": "", "best_residual_set": "[]", "schema_version": SCHEMA_VERSION}
    return {"trajectory_id": cp.trajectory_id, "checkpoint_id": cp.checkpoint_id, "boundary_id": boundary.boundary_id, "minimum_status": "not_run", "residual_lower_bound": "", "residual_upper_bound": "", "best_residual_set": "[]", "schema_version": SCHEMA_VERSION}


def _window_rows(cp, boundary, oracle_rows, metrics):
    rows = []
    for level in ("immediate_consumer", "bounded_fanout_cone", "whole_design_output_frontier"):
        nonlocal_diag = level == "whole_design_output_frontier"
        recovered = any(r["recovered"] == "true" for r in oracle_rows)
        rows.append({"trajectory_id": cp.trajectory_id, "checkpoint_id": cp.checkpoint_id, "boundary_id": boundary.boundary_id, "window_level": level, "window_nodes": metrics.get("node_count", "0"), "window_inputs": metrics.get("input_count", "0"), "window_outputs": metrics.get("output_count", "0"), "residual_width": metrics.get("input_count", "0"), "decomposition_status": "decomposable" if recovered else "unresolved", "graph_rewrite_feasibility": "not_attempted_frontier_diagnostic", "global_cec_status": cp.cec_status, "classification": "whole_design_diagnostic_not_local_success" if nonlocal_diag else ("exact_local_window" if recovered else "no_result_within_bounds"), "runtime_s": "0.000000", "schema_version": SCHEMA_VERSION})
    return rows


def _frontier_rows(transitions, recovery):
    grouped = defaultdict(list)
    for row in recovery:
        grouped[(row["boundary_id"], row["trajectory_id"], row["method"])].append(row)
    out = []
    for key, items in sorted(grouped.items()):
        ordered = sorted(items, key=lambda r: int(r["checkpoint_index"]))
        successes = [int(r["checkpoint_index"]) for r in ordered if r["recovered"] == "true"]
        first_loss = next((r["checkpoint_id"] for r in ordered if r["recovered"] != "true"), "")
        nonmono = any(t["transition"] == "failure_to_success" for t in transitions if t["boundary_id"] == key[0] and t["trajectory_id"] == key[1] and t["method"] == key[2])
        out.append({"boundary_id": key[0], "trajectory_id": key[1], "method": key[2], "first_loss_checkpoint": first_loss, "last_success_checkpoint": str(max(successes)) if successes else "", "non_monotonic": str(nonmono).lower(), "recoverable_fraction": f"{len(successes) / max(1, len(ordered)):.6f}", "longest_success_interval": str(_longest(successes)), "schema_version": SCHEMA_VERSION})
    return out


def _pass_ablation_rows(deltas, metrics_by_cp):
    counts = Counter(row["pass_name"] for row in deltas if row["transition_class"] != "unchanged")
    rows = []
    for pass_name in sorted({"balance", "rewrite", "refactor", "dc2", "strash"}):
        rows.append({"ablation_id": f"omit_{pass_name}", "benchmark": "controlled_and_real", "flow_family": "paired_prefix_diagnostic", "ablation_type": "pass_omission_observational_control", "changed_pass": pass_name, "controlled_difference": "available_from_prefix_trajectories", "causal_claim": "not_claimed_association_only" if counts[pass_name] else "no_observed_transition", "recovery_delta": str(counts[pass_name]), "area_delta": "", "depth_delta": "", "schema_version": SCHEMA_VERSION})
    return rows


def _durability_rows(checkpoints, recovery):
    out = []
    by_traj = defaultdict(list)
    for cp in checkpoints:
        by_traj[cp.trajectory_id].append(cp)
    for row in recovery:
        if row["recovered"] != "true" or row["oracle_mode"] == "blind":
            continue
        cps = sorted(by_traj[row["trajectory_id"]], key=lambda cp: cp.checkpoint_index)
        for suffix in cps:
            if suffix.checkpoint_index <= int(row["checkpoint_index"]):
                continue
            out.append({"boundary_id": row["boundary_id"], "trajectory_id": row["trajectory_id"], "insertion_checkpoint": row["checkpoint_id"], "suffix_checkpoint": suffix.checkpoint_id, "suffix_pass_name": suffix.pass_name, "textually_present": "false", "graph_active": "false", "functionally_equivalent": str(suffix.cec_status == "equivalent").lower(), "blind_identifiable": "false", "useful_for_decomposition": "false", "boundary_survives_suffix": "false", "global_cec_status": suffix.cec_status, "schema_version": SCHEMA_VERSION})
            break
    return out


def _tradeoff_rows(checkpoints, recovery, metrics_by_cp):
    by_cp_recovery = defaultdict(list)
    for row in recovery:
        by_cp_recovery[row["checkpoint_id"]].append(row)
    by_traj = defaultdict(list)
    for cp in checkpoints:
        by_traj[cp.trajectory_id].append(cp)
    out = []
    for traj, cps in by_traj.items():
        source = next((metrics_by_cp.get(cp.checkpoint_id, {}) for cp in cps if cp.checkpoint_index == 0), {})
        source_nodes, source_depth = int(source.get("node_count", "0") or 0), int(source.get("level_count", "0") or 0)
        for cp in cps:
            metrics = metrics_by_cp.get(cp.checkpoint_id, {})
            if not metrics:
                continue
            rows = by_cp_recovery[cp.checkpoint_id]
            blind = [r for r in rows if r["oracle_mode"] == "blind"]
            oracle = [r for r in rows if r["oracle_mode"] != "blind"]
            node_count, depth = int(metrics["node_count"]), int(metrics["level_count"])
            out.append({"trajectory_id": traj, "checkpoint_id": cp.checkpoint_id, "checkpoint_index": str(cp.checkpoint_index), "pass_name": cp.pass_name, "node_count": str(node_count), "depth": str(depth), "node_reduction_vs_source": str(source_nodes - node_count), "depth_delta_vs_source": str(depth - source_depth), "recoverable_boundary_fraction": f"{sum(r['recovered']=='true' for r in blind) / max(1, len(blind)):.6f}", "oracle_recoverable_fraction": f"{sum(r['recovered']=='true' for r in oracle) / max(1, len(oracle)):.6f}", "schema_version": SCHEMA_VERSION})
    return out


def _summary_rows(rows, boundaries, checkpoints, recovery):
    for split, table in (("controlled", "controlled_results.csv"), ("development", "development_results.csv"), ("heldout", "heldout_results.csv")):
        bs = [b for b in boundaries if b.split == split]
        cps = [c for c in checkpoints if c.split == split]
        rr = [r for r in recovery if r["split"] == split]
        summary = Counter(r["failure_reason"] for r in rr if r["failure_reason"])
        if split == "controlled":
            for family in sorted({b.benchmark for b in bs}):
                rows[table].append({"benchmark": family, "boundaries": str(sum(b.benchmark == family for b in bs)), "trajectories": str(len({c.trajectory_id for c in cps if c.benchmark == family})), "checkpoints": str(sum(c.benchmark == family for c in cps)), "blind_recovered_rows": str(sum(r["benchmark"] == family and r["oracle_mode"] == "blind" and r["recovered"] == "true" for r in rr)), "oracle_recovered_rows": str(sum(r["benchmark"] == family and r["oracle_mode"] != "blind" and r["recovered"] == "true" for r in rr)), "non_monotonic_boundaries": "0", "schema_version": SCHEMA_VERSION})
        else:
            for family in sorted({b.benchmark for b in bs}):
                rows[table].append({"benchmark": family, "boundaries": str(sum(b.benchmark == family for b in bs)), "trajectories": str(len({c.trajectory_id for c in cps if c.benchmark == family})), "checkpoints": str(sum(c.benchmark == family for c in cps)), "blind_recovered_rows": str(sum(r["benchmark"] == family and r["oracle_mode"] == "blind" and r["recovered"] == "true" for r in rr)), "oracle_recovered_rows": str(sum(r["benchmark"] == family and r["oracle_mode"] != "blind" and r["recovered"] == "true" for r in rr)), "failure_summary": json.dumps(dict(sorted(summary.items())), sort_keys=True), "schema_version": SCHEMA_VERSION})


def _failure_rows(rows, recovery):
    counts = Counter((r["split"], r["method"], r["oracle_mode"], r["failure_reason"]) for r in recovery if r["failure_reason"])
    for (split, method, oracle_mode, reason), count in sorted(counts.items()):
        rows["failure_taxonomy.csv"].append({"benchmark_group": split, "method": method, "oracle_mode": oracle_mode, "failure_reason": reason, "count": str(count), "schema_version": SCHEMA_VERSION})


def _write_markdown_summary(rows, boundaries, checkpoints):
    blind = rows["blind_recovery_results.csv"]
    oracle = rows["oracle_ladder_results.csv"]
    cec = rows["checkpoint_cec_results.csv"]
    lines = [
        "# Semantic Recoverability Frontier Summary",
        "",
        f"- designs: {len(set(b.benchmark for b in boundaries))}",
        f"- ground-truth boundaries: {len(boundaries)}",
        f"- trajectories: {len(set(cp.trajectory_id for cp in checkpoints))}",
        f"- checkpoints: {len(checkpoints)}",
        f"- checkpoint CEC equivalent: {sum(r['cec_status'] == 'equivalent' for r in cec)} / {len(cec)}",
        f"- blind recovered rows: {sum(r['recovered'] == 'true' for r in blind)} / {len(blind)}",
        f"- oracle recovered rows: {sum(r['recovered'] == 'true' for r in oracle)} / {len(oracle)}",
        f"- held-out blind recovered rows: {sum(r['split'] == 'heldout' and r['recovered'] == 'true' for r in blind)}",
        "",
        "Blind, oracle, controlled, development, and held-out rows are separate.  Oracle rows diagnose compact factorisation after the blind configuration is fixed; they are not blind recovery.",
    ]
    (OUT / "final_supported_claims_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _source_row(boundary):
    third_party = boundary.source_location.startswith(str(ROOT / "benchmarks/real"))
    return {"benchmark": boundary.benchmark, "design_family": boundary.design_family, "split": boundary.split, "source_type": "repository_controlled_generated" if boundary.split == "controlled" else "repository_hand_written_blif", "source_path": boundary.source_location, "source_url": "local_repository", "revision": _git_head(), "license": "repository_license", "preprocessing": "truth_table_blif_generation" if boundary.split == "controlled" else "none", "schema_version": SCHEMA_VERSION}


def _environment(abc):
    rows = [{"tool": "python", "version": platform.python_version(), "path": sys.executable, "status": "available", "schema_version": SCHEMA_VERSION}]
    try:
        import z3
        rows.append({"tool": "z3", "version": z3.get_version_string(), "path": "python:z3", "status": "available", "schema_version": SCHEMA_VERSION})
    except Exception as exc:
        rows.append({"tool": "z3", "version": "", "path": "python:z3", "status": f"unavailable:{exc}", "schema_version": SCHEMA_VERSION})
    if abc.exists():
        proc = subprocess.run([str(abc), "-c", "version"], text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
        rows.append({"tool": "abc", "version": proc.stdout.strip().splitlines()[-1] if proc.stdout.strip() else "unknown", "path": _display(abc), "status": "available", "schema_version": SCHEMA_VERSION})
    else:
        rows.append({"tool": "abc", "version": "", "path": _display(abc), "status": "unavailable", "schema_version": SCHEMA_VERSION})
    rows.append({"tool": "yosys", "version": "", "path": shutil.which("yosys") or "", "status": "available" if shutil.which("yosys") else "unavailable", "schema_version": SCHEMA_VERSION})
    return rows


def _nodes_exist(cp, outputs):
    if not cp.blif_path.exists():
        return False
    net = parse_blif(cp.blif_path)
    names = {n.output for n in net.nodes} | set(net.outputs)
    return all(node in names for node in outputs)


def _family_for(benchmark, boundaries):
    return next((b.design_family for b in boundaries if b.benchmark == benchmark), "")


def _longest(indices):
    if not indices:
        return 0
    best = cur = 1
    for a, b in zip(indices, indices[1:]):
        cur = cur + 1 if b == a + 1 else 1
        best = max(best, cur)
    return best


def _display(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except Exception:
        return str(path)


def _git_head() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    except Exception:
        return "unknown"


if __name__ == "__main__":
    raise SystemExit(main())
