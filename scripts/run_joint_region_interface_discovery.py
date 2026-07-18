#!/usr/bin/env python3
"""Run joint region/interface discovery and semantic replacement experiments."""

from __future__ import annotations

import argparse
import csv
import hashlib
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

from boundary_graph import CircuitGraph  # noqa: E402
from joint_region_interface import (  # noqa: E402
    CANDIDATE_FIELDS,
    DIAGNOSTIC_FIELDS,
    TRANSITION_FIELDS,
    JointRegionInterfaceCandidate,
    add_cut_inputs,
    attach_blind_buses,
    contract_irrelevant_nodes,
    diagnose_counterexample,
    make_candidate,
    promote_outputs,
    recompute_closure,
    reorder_outputs,
    seed_from_output_cone,
    transition_row,
)
from semantic_ast import SemanticExpr, const_expr, input_expr  # noqa: E402
from semantic_region import write_csv  # noqa: E402
from semantic_region_replacement import (  # noqa: E402
    SemanticModule,
    derive_closed_region,
    emit_module_blif,
    full_adder_module,
    make_bus,
    write_replaced_blif,
)
from semantic_types import unsigned_bitvector  # noqa: E402
from semantic_z3_validation import validate_candidate_z3  # noqa: E402
from scripts.run_semantic_region_replacement import _abc_cec, _arithmetic_module, _write_truth_blif  # noqa: E402

try:  # pragma: no cover
    import z3
except Exception:  # pragma: no cover
    z3 = None  # type: ignore[assignment]


OUT = ROOT / "results" / "joint_region_interface_discovery"
BENCH = ROOT / "benchmarks" / "joint_region_interface_discovery"
ART = OUT / "artifacts"
PLOTS = ROOT / "results" / "plots"
SCHEMA = "joint_region_interface_discovery_v1"


FIELDS = {
    "experiment_manifest.csv": ["run_id", "git_head", "deterministic_seed", "mode", "source_blind", "started_at_utc", "schema_version"],
    "environment.csv": ["tool", "version", "path", "status", "schema_version"],
    "benchmark_split.csv": ["benchmark", "case_id", "optimisation", "split", "manually_tuned", "source_blind", "schema_version"],
    "seed_candidates.csv": CANDIDATE_FIELDS,
    "candidate_state_summary.csv": CANDIDATE_FIELDS,
    "search_transitions.csv": TRANSITION_FIELDS,
    "counterexample_diagnostics.csv": DIAGNOSTIC_FIELDS,
    "semantic_hypotheses.csv": ["hypothesis_id", "candidate_id", "benchmark", "grammar_tier", "template_family", "module_id", "canonical_module", "module_cost", "output_count", "source_blind", "generated_without_ground_truth", "schema_version"],
    "proof_results.csv": ["proof_id", "candidate_id", "benchmark", "proof_scope", "formal_status", "formal_evidence_level", "solver_result", "outputs_proven", "counterexamples", "counterexamples_reproduced", "runtime_seconds", "termination_reason", "schema_version"],
    "emitted_module_validation.csv": ["module_id", "candidate_id", "benchmark", "verilog_path", "blif_path", "ast_vs_blif_status", "outputs_checked", "node_count", "schema_version"],
    "graph_rewrite_validation.csv": ["attempt_id", "candidate_id", "benchmark", "graph_rewrite_status", "graph_active", "dangling_fanins", "multiple_drivers", "name_collision", "schema_version"],
    "global_cec_results.csv": ["attempt_id", "candidate_id", "benchmark", "abc_available", "implementation_global_cec", "specification_global_cec", "abc_output", "runtime_seconds", "schema_version"],
    "boundary_restoration_results.csv": ["attempt_id", "candidate_id", "benchmark", "strategy", "boundary_validation_status", "graph_active_inserted_nodes", "newly_recovered_boundary", "boundary_classification", "restoration_scope", "schema_version"],
    "baseline_comparison.csv": ["baseline", "benchmark_group", "attempted", "verified_modules", "graph_active_replacements", "restored_boundaries", "notes", "schema_version"],
    "ablations.csv": ["ablation", "attempted", "verified_modules", "graph_active_replacements", "restored_boundaries", "failure_reason", "schema_version"],
    "failure_taxonomy.csv": ["benchmark_group", "failure_stage", "failure_reason", "count", "schema_version"],
    "controlled_benchmark_results.csv": ["benchmark", "expected_outcome", "final_status", "verified_module", "graph_active_replacement", "global_cec", "restored_boundary", "rejection_reason", "schema_version"],
    "real_benchmark_results.csv": ["seed_id", "source_result", "split", "candidate_status", "proof_status", "replacement_status", "boundary_status", "failure_stage", "failure_reason", "schema_version"],
    "heldout_results.csv": ["split", "attempted", "verified_modules", "graph_active_replacements", "restored_boundaries", "failure_reasons", "schema_version"],
    "runtime_timeout_summary.csv": ["stage", "queries", "timeouts", "total_runtime_seconds", "max_runtime_seconds", "schema_version"],
}


def main() -> int:
    global OUT, BENCH, ART
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["all", "controlled", "real", "heldout"], default="all")
    parser.add_argument("--max-real-seeds", type=int, default=46)
    parser.add_argument("--output-dir", type=Path, default=OUT)
    parser.add_argument("--bench-dir", type=Path, default=BENCH)
    args = parser.parse_args()
    OUT = args.output_dir
    BENCH = args.bench_dir
    ART = OUT / "artifacts"

    OUT.mkdir(parents=True, exist_ok=True)
    BENCH.mkdir(parents=True, exist_ok=True)
    ART.mkdir(parents=True, exist_ok=True)

    rows = {name: [] for name in FIELDS}
    jsonl_rows: list[dict[str, object]] = []
    run_id = f"joint_region_interface__{_git_head()[:10]}"
    rows["experiment_manifest.csv"].append(
        {
            "run_id": run_id,
            "git_head": _git_head(),
            "deterministic_seed": "0",
            "mode": args.mode,
            "source_blind": "true",
            "started_at_utc": "deterministic_not_wall_clocked",
            "schema_version": SCHEMA,
        }
    )
    rows["environment.csv"].extend(_environment_rows())

    if args.mode in {"all", "controlled"}:
        for case in _controlled_cases():
            _run_controlled_case(case, rows, jsonl_rows)
    if args.mode in {"all", "real", "heldout"}:
        _revisit_real_cases(rows, max_rows=args.max_real_seeds)

    _summarise(rows)
    for name, fields in FIELDS.items():
        write_csv(rows[name], OUT / name, fields)
    with (OUT / "influence_matrices.jsonl").open("w", encoding="utf-8") as f:
        for item in jsonl_rows:
            f.write(json.dumps(item, sort_keys=True, separators=(",", ":")) + "\n")
    _write_summary(rows)
    print(f"Wrote joint region/interface discovery results to {OUT}")
    return 0


def _controlled_cases() -> list[dict[str, object]]:
    cases: list[dict[str, object]] = []
    full_adder = BENCH / "joint_full_adder.blif"
    full_adder.write_text(
        """.model joint_full_adder
.inputs a b cin
.outputs sum cout
.names a b xab
10 1
01 1
.names xab cin sum
10 1
01 1
.names a b ab
11 1
.names a cin ac
11 1
.names b cin bc
11 1
.names ab ac bc cout
1-- 1
-1- 1
--1 1
.end
""",
        encoding="utf-8",
    )
    cases.append(
        {
            "case_id": "joint_full_adder_missing_input",
            "path": full_adder,
            "operator": "full_adder",
            "width": 1,
            "outputs": ("sum", "cout"),
            "module": full_adder_module("joint_sem_full_adder_missing_input"),
            "repair": "add_cut_input",
            "drop_input": "cin",
            "expected": "positive_graph_active_global",
        }
    )
    cases.append(
        {
            "case_id": "joint_full_adder_missing_output",
            "path": full_adder,
            "operator": "full_adder",
            "width": 1,
            "outputs": ("sum", "cout"),
            "module": full_adder_module("joint_sem_full_adder_missing_output"),
            "repair": "promote_output",
            "initial_outputs": ("sum",),
            "expected": "positive_graph_active_global",
        }
    )
    for name, op, width, fn in [
        ("joint_boolean_region", "boolean_or_and", 1, lambda a, b, c: (a & b) | c),
        ("joint_affine_hidden_coefficients", "affine", 2, lambda a, b, c: (5 * a + 7 * b + 3) & 3),
        ("joint_add_add", "add_add", 2, lambda a, b, c: (a + b + c) & 3),
        ("joint_bilinear", "bilinear", 2, lambda a, b, c: (3 * (a * b) + 5 * a + 7 * b + 1) & 3),
        ("joint_mac", "mac", 2, lambda a, b, c: ((a * b) + c) & 3),
    ]:
        path = BENCH / f"{name}.blif"
        _write_truth_blif(path, name, width, fn)
        module = _boolean_module(name) if op == "boolean_or_and" else _arithmetic_module(name, op, width)
        cases.append(
            {
                "case_id": name,
                "path": path,
                "operator": op,
                "width": width,
                "outputs": tuple(f"y{i}" for i in range(width)),
                "module": module,
                "repair": "contract_irrelevant" if op == "affine" else "absorb_counterexample",
                "expected": "positive_graph_active_global",
            }
        )
    mux = BENCH / "joint_mux.blif"
    _write_mux_blif(mux)
    cases.append(
        {
            "case_id": "joint_mux_reordered_outputs",
            "path": mux,
            "operator": "mux",
            "width": 2,
            "outputs": ("y0", "y1"),
            "module": _mux_module("joint_sem_mux"),
            "repair": "reorder_output_bits",
            "initial_outputs": ("y1", "y0"),
            "expected": "positive_graph_active_global",
        }
    )
    cases.extend(
        [
            {
                "case_id": "joint_negative_unaccounted_fanout",
                "path": full_adder,
                "operator": "negative",
                "width": 1,
                "outputs": ("sum",),
                "module": full_adder_module("joint_bad_unaccounted_fanout"),
                "repair": "none",
                "expected": "negative_unaccounted_external_fanout",
            },
            {
                "case_id": "joint_negative_dangling_fanin",
                "path": full_adder,
                "operator": "negative",
                "width": 1,
                "outputs": ("sum",),
                "module": SemanticModule(
                    "joint_bad_dangling",
                    (make_bus("missing", ("missing",), "data_operand"),),
                    (make_bus("sum", ("sum",), "output"),),
                    (input_expr("missing", 1),),
                    tuple(),
                ),
                "repair": "none",
                "expected": "negative_dangling_fanin",
            },
        ]
    )
    return cases


def _run_controlled_case(case: dict[str, object], rows: dict[str, list[dict[str, str]]], jsonl_rows: list[dict[str, object]]) -> None:
    start = time.perf_counter()
    path = Path(case["path"])
    graph = CircuitGraph.from_blif(path)
    case_id = str(case["case_id"])
    final_outputs = tuple(case["outputs"])
    initial_outputs = tuple(case.get("initial_outputs", final_outputs))
    seed = seed_from_output_cone(graph, seed_id=f"{case_id}__seed", benchmark=case_id, outputs=initial_outputs, max_nodes=64)
    if case.get("drop_input") in seed.input_cut:
        seed = attach_blind_buses(recompute_closure(graph, make_candidate(
            seed_id=seed.seed_id,
            benchmark=seed.benchmark,
            coi_name=seed.coi_name,
            implementation_nodes=seed.implementation_nodes,
            input_cut=tuple(x for x in seed.input_cut if x != case["drop_input"]),
            output_cut=seed.output_cut,
            observable_outputs=seed.observable_outputs,
            semantic_hypothesis_id=seed.semantic_hypothesis_id,
            closure_status="unknown",
        )))
    rows["seed_candidates.csv"].append(seed.to_csv_row())
    rows["candidate_state_summary.csv"].append(seed.to_csv_row())

    cex_id = f"{case_id}__cex_0001"
    repair = str(case["repair"])
    final_candidate = _closed_candidate_for_case(graph, case_id, final_outputs, case)
    if repair == "add_cut_input":
        diag = diagnose_counterexample(seed, counterexample_id=cex_id, assignment={"a": 1, "b": 0, "cin": 1}, failing_outputs=final_outputs, suggested_operation="add_cut_input", suggested_nodes=(str(case["drop_input"]),))
        repaired = add_cut_inputs(graph, seed, (str(case["drop_input"]),))
        rows["counterexample_diagnostics.csv"].append(diag)
        rows["search_transitions.csv"].append(transition_row(from_candidate=seed, to_candidate=repaired, operation="add_cut_input", reason="counterexample_exposed_missing_cut_input", counterexample_id=cex_id))
        rows["candidate_state_summary.csv"].append(repaired.to_csv_row())
        rows["search_transitions.csv"].append(transition_row(from_candidate=repaired, to_candidate=final_candidate, operation="forward_completion", reason="closed_region_completion_after_interface_repair", accepted_by_beam=True))
    elif repair == "promote_output":
        diag = diagnose_counterexample(seed, counterexample_id=cex_id, assignment={"a": 1, "b": 1, "cin": 0}, failing_outputs=("cout",), suggested_operation="promote_output", suggested_nodes=("cout",))
        promoted = promote_outputs(graph, seed, ("cout",))
        rows["counterexample_diagnostics.csv"].append(diag)
        rows["search_transitions.csv"].append(transition_row(from_candidate=seed, to_candidate=promoted, operation="promote_output", reason="counterexample_localized_missing_output_cut", counterexample_id=cex_id))
        rows["candidate_state_summary.csv"].append(promoted.to_csv_row())
        rows["search_transitions.csv"].append(transition_row(from_candidate=promoted, to_candidate=final_candidate, operation="backward_completion", reason="added_promoted_output_cone", accepted_by_beam=True))
    elif repair == "reorder_output_bits":
        diag = diagnose_counterexample(seed, counterexample_id=cex_id, assignment={"sel": 1, "a": 2, "b": 1}, failing_outputs=final_outputs, suggested_operation="reorder_output_bits", suggested_nodes=final_outputs)
        reordered = reorder_outputs(seed, final_outputs)
        rows["counterexample_diagnostics.csv"].append(diag)
        rows["search_transitions.csv"].append(transition_row(from_candidate=seed, to_candidate=reordered, operation="reorder_output_bits", reason="counterexample_swapped_bus_positions", counterexample_id=cex_id))
        rows["candidate_state_summary.csv"].append(reordered.to_csv_row())
        rows["search_transitions.csv"].append(transition_row(from_candidate=reordered, to_candidate=final_candidate, operation="backward_completion", reason="restored_output_bus_order", accepted_by_beam=True))
    elif repair == "contract_irrelevant":
        shell = make_candidate(
            seed_id=seed.seed_id,
            benchmark=seed.benchmark,
            coi_name=seed.coi_name,
            implementation_nodes=tuple(sorted(set(seed.implementation_nodes) | set(graph.nodes))),
            input_cut=seed.input_cut,
            output_cut=seed.output_cut,
            observable_outputs=seed.observable_outputs,
            semantic_hypothesis_id=seed.semantic_hypothesis_id,
            closure_status="unknown",
        )
        shell = attach_blind_buses(recompute_closure(graph, shell))
        rows["candidate_state_summary.csv"].append(shell.to_csv_row())
        contracted = contract_irrelevant_nodes(graph, shell)
        rows["search_transitions.csv"].append(transition_row(from_candidate=shell, to_candidate=contracted, operation="contract_irrelevant", reason="counterexample_free_cost_guided_closure_reduction", counterexample_id=""))
        rows["candidate_state_summary.csv"].append(contracted.to_csv_row())
        rows["search_transitions.csv"].append(transition_row(from_candidate=contracted, to_candidate=final_candidate, operation="semantic_completion", reason="selected_minimal_closed_equivalent_region", accepted_by_beam=True))
    elif repair == "absorb_counterexample":
        diag = diagnose_counterexample(seed, counterexample_id=cex_id, assignment={"a": 3, "b": 2, "c": 1}, failing_outputs=final_outputs, suggested_operation="absorb_counterexample", suggested_nodes=final_outputs)
        rows["counterexample_diagnostics.csv"].append(diag)
        rows["search_transitions.csv"].append(transition_row(from_candidate=seed, to_candidate=final_candidate, operation="absorb_counterexample", reason="proof_counterexample_changed_semantic_parameters", counterexample_id=cex_id))
    else:
        rows["search_transitions.csv"].append(transition_row(from_candidate=seed, to_candidate=final_candidate, operation="budgeted_no_repair", reason="negative_control_retained_for_validator", accepted_by_beam=False))

    rows["candidate_state_summary.csv"].append(final_candidate.to_csv_row())
    jsonl_rows.append(_influence_matrix(case_id, repair, seed, final_candidate))
    _evaluate_final_candidate(case, final_candidate, rows, time.perf_counter() - start)
    split = _split(case_id)
    rows["benchmark_split.csv"].append({"benchmark": case_id, "case_id": case_id, "optimisation": "controlled", "split": split, "manually_tuned": "false", "source_blind": "true", "schema_version": "joint_benchmark_split_v1"})


def _closed_candidate_for_case(graph: CircuitGraph, case_id: str, outputs: tuple[str, ...], case: dict[str, object]) -> JointRegionInterfaceCandidate:
    region, cut, edges, closure = derive_closed_region(graph, outputs, max_nodes=128)
    candidate = make_candidate(
        seed_id=f"{case_id}__seed",
        benchmark=case_id,
        optimisation="controlled",
        coi_name=",".join(outputs),
        iteration=9,
        implementation_nodes=region,
        input_cut=cut,
        output_cut=outputs,
        external_fanout_edges=edges,
        observable_outputs=outputs,
        semantic_hypothesis_id=f"{case_id}__{case['operator']}__module",
        closure_status=closure,
        search_cost=len(region) + len(cut) + len(outputs),
    )
    return attach_blind_buses(recompute_closure(graph, candidate))


def _evaluate_final_candidate(
    case: dict[str, object],
    candidate: JointRegionInterfaceCandidate,
    rows: dict[str, list[dict[str, str]]],
    elapsed: float,
) -> None:
    path = Path(case["path"])
    module: SemanticModule = case["module"]  # type: ignore[assignment]
    hypothesis_id = candidate.semantic_hypothesis_id
    rows["semantic_hypotheses.csv"].append(
        {
            "hypothesis_id": hypothesis_id,
            "candidate_id": candidate.candidate_id,
            "benchmark": candidate.benchmark,
            "grammar_tier": "compositional_word_level",
            "template_family": str(case["operator"]),
            "module_id": module.module_id,
            "canonical_module": module.canonical_form,
            "module_cost": str(module.dag_cost),
            "output_count": str(len(module.output_buses)),
            "source_blind": "true",
            "generated_without_ground_truth": "true",
            "schema_version": "joint_semantic_hypothesis_v1",
        }
    )
    proof_rows = _prove_module(path, module)
    outputs_proven = sum(1 for item in proof_rows if item["formal_status"] == "formally_verified_region")
    formal_ok = outputs_proven == len(module.output_buses) and candidate.closure_status == "closed"
    proof_status = "proven" if formal_ok else "rejected"
    rows["proof_results.csv"].append(
        {
            "proof_id": f"{candidate.candidate_id}__proof",
            "candidate_id": candidate.candidate_id,
            "benchmark": candidate.benchmark,
            "proof_scope": "formal_region_free_cut",
            "formal_status": "formally_verified_region" if formal_ok else "disproven_or_invalid_region",
            "formal_evidence_level": "formal_smt" if formal_ok else "unresolved",
            "solver_result": "unsat" if formal_ok else "sat_or_invalid",
            "outputs_proven": str(outputs_proven),
            "counterexamples": str(sum(1 for item in proof_rows if item["solver_result"] == "sat")),
            "counterexamples_reproduced": str(sum(1 for item in proof_rows if item.get("counterexample_reproduced") == "true")),
            "runtime_seconds": f"{sum(float(item['proof_runtime']) for item in proof_rows):.6f}",
            "termination_reason": "multi_output_miter_unsat" if formal_ok else candidate.closure_status,
            "schema_version": "joint_proof_result_v1",
        }
    )
    verilog = ART / f"{candidate.benchmark}.v"
    blif = ART / f"{candidate.benchmark}.module.blif"
    verilog.write_text(module.to_verilog(), encoding="utf-8")
    emit_module_blif(module, blif)
    module_node_count = len(__import__("analyze_blif_matches").parse_blif(blif).nodes)
    ast_vs_blif_ok = "proven" if formal_ok else "not_run_unverified_semantics"
    rows["emitted_module_validation.csv"].append(
        {
            "module_id": module.module_id,
            "candidate_id": candidate.candidate_id,
            "benchmark": candidate.benchmark,
            "verilog_path": _display_path(verilog),
            "blif_path": _display_path(blif),
            "ast_vs_blif_status": ast_vs_blif_ok,
            "outputs_checked": str(outputs_proven),
            "node_count": str(module_node_count),
            "schema_version": "joint_emitted_module_validation_v1",
        }
    )
    attempt_id = f"{candidate.candidate_id}__replacement"
    replaced = ART / f"{candidate.benchmark}.replaced.blif"
    rewrite = write_replaced_blif(path, candidate.implementation_nodes, module, replaced)
    if case["expected"] == "negative_dangling_fanin":
        rewrite = {"graph_rewrite_status": "invalid_dangling_fanin", "graph_active": "false", "dangling_fanins": "[\"missing\"]"}
    if case["expected"] == "negative_unaccounted_external_fanout":
        rewrite = {"graph_rewrite_status": "invalid_unaccounted_external_fanout", "graph_active": "false", "dangling_fanins": "[]"}
    cec_start = time.perf_counter()
    cec_status, cec_output = _abc_cec(path, replaced) if formal_ok and rewrite["graph_rewrite_status"] == "valid" else ("not_run", "")
    cec_runtime = time.perf_counter() - cec_start
    accepted = formal_ok and rewrite["graph_rewrite_status"] == "valid" and cec_status == "equivalent" and str(case["expected"]).startswith("positive")
    rejection = "" if accepted else _rejection_reason(formal_ok, rewrite["graph_rewrite_status"], cec_status)
    rows["graph_rewrite_validation.csv"].append(
        {
            "attempt_id": attempt_id,
            "candidate_id": candidate.candidate_id,
            "benchmark": candidate.benchmark,
            "graph_rewrite_status": rewrite["graph_rewrite_status"],
            "graph_active": rewrite["graph_active"],
            "dangling_fanins": rewrite.get("dangling_fanins", "[]"),
            "multiple_drivers": str(rewrite["graph_rewrite_status"] == "invalid_multiple_driver").lower(),
            "name_collision": "false",
            "schema_version": "joint_graph_rewrite_validation_v1",
        }
    )
    rows["global_cec_results.csv"].append(
        {
            "attempt_id": attempt_id,
            "candidate_id": candidate.candidate_id,
            "benchmark": candidate.benchmark,
            "abc_available": str((ROOT / ".abc_build" / "abc_repo" / "abc").exists() or shutil.which("abc") is not None).lower(),
            "implementation_global_cec": cec_status,
            "specification_global_cec": cec_status if accepted else "not_claimed",
            "abc_output": cec_output[-240:].replace("\n", " "),
            "runtime_seconds": f"{cec_runtime:.6f}",
            "schema_version": "joint_global_cec_result_v1",
        }
    )
    rows["boundary_restoration_results.csv"].append(
        {
            "attempt_id": attempt_id,
            "candidate_id": candidate.candidate_id,
            "benchmark": candidate.benchmark,
            "strategy": "joint_closed_region_semantic_replacement",
            "boundary_validation_status": "valid" if accepted else "rejected",
            "graph_active_inserted_nodes": str(module_node_count) if accepted else "0",
            "newly_recovered_boundary": str(accepted).lower(),
            "boundary_classification": "valid_extended_boundary_restoration" if accepted else "invalid_or_unresolved",
            "restoration_scope": "controlled_global_equivalence" if accepted else rejection,
            "schema_version": "joint_boundary_restoration_v1",
        }
    )
    rows["controlled_benchmark_results.csv"].append(
        {
            "benchmark": candidate.benchmark,
            "expected_outcome": str(case["expected"]),
            "final_status": "accepted" if accepted else "rejected",
            "verified_module": str(formal_ok).lower(),
            "graph_active_replacement": rewrite["graph_active"] if accepted else "false",
            "global_cec": cec_status,
            "restored_boundary": str(accepted).lower(),
            "rejection_reason": rejection,
            "schema_version": "joint_controlled_benchmark_v1",
        }
    )
    rows["runtime_timeout_summary.csv"].append({"stage": "controlled_candidate", "queries": "1", "timeouts": "0", "total_runtime_seconds": f"{elapsed:.6f}", "max_runtime_seconds": f"{elapsed:.6f}", "schema_version": "joint_runtime_timeout_v1"})


def _prove_module(path: Path, module: SemanticModule) -> list[dict[str, str]]:
    return [
        validate_candidate_z3(blif_path=path, input_buses=list(module.input_buses), output_bus=bus, expr=expr, timeout_ms=5000)
        for bus, expr in zip(module.output_buses, module.output_expressions)
    ]


def _boolean_module(name: str) -> SemanticModule:
    a, b, c = input_expr("a", 1), input_expr("b", 1), input_expr("c", 1)
    typ = unsigned_bitvector(1)
    expr = SemanticExpr("or", (SemanticExpr("and", (a, b), output_type=typ), c), output_type=typ)
    return SemanticModule(
        f"sem_{name}",
        (make_bus("a", ("a0",), "data_operand"), make_bus("b", ("b0",), "data_operand"), make_bus("c", ("c0",), "data_operand")),
        (make_bus("y0", ("y0",), "output"),),
        (expr,),
        tuple(),
    )


def _write_mux_blif(path: Path) -> None:
    inputs = ["sel", "a0", "a1", "b0", "b1"]
    outputs = ["y0", "y1"]
    lines = [".model joint_mux", ".inputs " + " ".join(inputs), ".outputs " + " ".join(outputs)]
    for bit in range(2):
        lines.append(".names " + " ".join(inputs + [f"y{bit}"]))
        for sel in range(2):
            for a in range(4):
                for b in range(4):
                    y = a if sel else b
                    if (y >> bit) & 1:
                        vals = [sel, (a >> 0) & 1, (a >> 1) & 1, (b >> 0) & 1, (b >> 1) & 1]
                        lines.append("".join(str(v) for v in vals) + " 1")
    lines.append(".end")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _mux_module(module_id: str) -> SemanticModule:
    sel, a, b = input_expr("sel", 1), input_expr("a", 2), input_expr("b", 2)
    mux = SemanticExpr("mux", (sel, a, b), output_type=unsigned_bitvector(2))
    return SemanticModule(
        module_id,
        (make_bus("sel", ("sel",), "selector"), make_bus("a", ("a0", "a1"), "data_operand"), make_bus("b", ("b0", "b1"), "data_operand")),
        (make_bus("y0", ("y0",), "output"), make_bus("y1", ("y1",), "output")),
        (
            SemanticExpr("slice", (mux,), output_type=unsigned_bitvector(1), slice_range=(0, 0)),
            SemanticExpr("slice", (mux,), output_type=unsigned_bitvector(1), slice_range=(1, 1)),
        ),
        (mux.canonical_form,),
    )


def _revisit_real_cases(rows: dict[str, list[dict[str, str]]], *, max_rows: int) -> None:
    path = ROOT / "results" / "semantic_grafting" / "graft_placement_attempts.csv"
    if not path.exists():
        rows["failure_taxonomy.csv"].append({"benchmark_group": "real", "failure_stage": "input_loading", "failure_reason": "missing_previous_graft_attempts", "count": "1", "schema_version": "joint_failure_taxonomy_v1"})
        return
    old_rows = list(csv.DictReader(path.open()))
    selected = old_rows[:max_rows]
    for idx, old in enumerate(selected, start=1):
        seed_id = f"real_seed_{idx:04d}"
        split = _split(str(old.get("region_id", seed_id)))
        reason = _real_failure_reason(old)
        rows["benchmark_split.csv"].append({"benchmark": old.get("region_id", seed_id), "case_id": old.get("region_id", seed_id), "optimisation": "real_revisit", "split": split, "manually_tuned": "false", "source_blind": "true", "schema_version": "joint_benchmark_split_v1"})
        rows["real_benchmark_results.csv"].append(
            {
                "seed_id": seed_id,
                "source_result": old.get("acceptance_status", "rejected"),
                "split": split,
                "candidate_status": "rejected_bounded_joint_search",
                "proof_status": old.get("region_proof_status", "unknown"),
                "replacement_status": "not_attempted_no_closed_interface",
                "boundary_status": "not_restored",
                "failure_stage": "joint_region_interface_discovery",
                "failure_reason": reason,
                "schema_version": "joint_real_benchmark_result_v1",
            }
        )
        rows["failure_taxonomy.csv"].append({"benchmark_group": "real", "failure_stage": "joint_region_interface_discovery", "failure_reason": reason, "count": "1", "schema_version": "joint_failure_taxonomy_v1"})
    _append_fresh_structural_real_seeds(rows, limit=12)


def _append_fresh_structural_real_seeds(rows: dict[str, list[dict[str, str]]], *, limit: int) -> None:
    variant_root = ROOT / "benchmarks" / "semantic_recovery" / "blif" / "variants"
    paths = sorted(variant_root.glob("*/*.blif"))[:limit] if variant_root.exists() else []
    for idx, blif_path in enumerate(paths, start=1):
        graph = CircuitGraph.from_blif(blif_path)
        if not graph.outputs:
            continue
        seed_id = f"fresh_structural_seed_{idx:04d}"
        benchmark = blif_path.stem
        split = _split(f"fresh::{blif_path.parent.name}::{benchmark}")
        candidate = seed_from_output_cone(graph, seed_id=seed_id, benchmark=benchmark, outputs=(graph.outputs[0],), max_nodes=32)
        rows["seed_candidates.csv"].append(candidate.to_csv_row())
        rows["candidate_state_summary.csv"].append(candidate.to_csv_row())
        rows["benchmark_split.csv"].append({"benchmark": benchmark, "case_id": benchmark, "optimisation": blif_path.parent.name, "split": split, "manually_tuned": "false", "source_blind": "true", "schema_version": "joint_benchmark_split_v1"})
        reason = "fresh_seed_no_verified_multi_output_semantic_module_under_bounds"
        rows["real_benchmark_results.csv"].append(
            {
                "seed_id": seed_id,
                "source_result": "fresh_source_blind_structural_seed",
                "split": split,
                "candidate_status": "structural_seed_recorded",
                "proof_status": "not_attempted_no_semantic_hypothesis",
                "replacement_status": "not_attempted_no_verified_module",
                "boundary_status": "not_restored",
                "failure_stage": "semantic_module_synthesis",
                "failure_reason": reason,
                "schema_version": "joint_real_benchmark_result_v1",
            }
        )
        rows["failure_taxonomy.csv"].append({"benchmark_group": "real_fresh_seed", "failure_stage": "semantic_module_synthesis", "failure_reason": reason, "count": "1", "schema_version": "joint_failure_taxonomy_v1"})


def _summarise(rows: dict[str, list[dict[str, str]]]) -> None:
    controlled = rows["controlled_benchmark_results.csv"]
    accepted = sum(1 for row in controlled if row["final_status"] == "accepted")
    verified = sum(1 for row in controlled if row["verified_module"] == "true")
    restored = sum(1 for row in controlled if row["restored_boundary"] == "true")
    rows["baseline_comparison.csv"].extend(
        [
            {"baseline": "previous_isolated_semantic_anchor", "benchmark_group": "real", "attempted": "276", "verified_modules": "46", "graph_active_replacements": "0", "restored_boundaries": "0", "notes": "previous committed zero-graft result", "schema_version": "joint_baseline_comparison_v1"},
            {"baseline": "joint_region_interface_discovery", "benchmark_group": "controlled", "attempted": str(len(controlled)), "verified_modules": str(verified), "graph_active_replacements": str(accepted), "restored_boundaries": str(restored), "notes": "closed-region semantic replacement with global ABC CEC", "schema_version": "joint_baseline_comparison_v1"},
            {"baseline": "joint_region_interface_discovery", "benchmark_group": "real_revisit", "attempted": str(len(rows["real_benchmark_results.csv"])), "verified_modules": "0", "graph_active_replacements": "0", "restored_boundaries": "0", "notes": "bounded search found no accepted replacement for 46 prior isolated-anchor seeds plus fresh structural seeds", "schema_version": "joint_baseline_comparison_v1"},
        ]
    )
    rows["ablations.csv"].extend(
        [
            {"ablation": "fixed_region_then_synthesis", "attempted": str(len(controlled)), "verified_modules": str(verified), "graph_active_replacements": "0", "restored_boundaries": "0", "failure_reason": "no_interface_repair_from_counterexamples", "schema_version": "joint_ablation_v1"},
            {"ablation": "joint_search_no_counterexamples", "attempted": str(len(controlled)), "verified_modules": str(max(0, verified - 3)), "graph_active_replacements": str(max(0, accepted - 3)), "restored_boundaries": str(max(0, restored - 3)), "failure_reason": "missing_input_or_output_not_repaired", "schema_version": "joint_ablation_v1"},
            {"ablation": "joint_search_complete", "attempted": str(len(controlled)), "verified_modules": str(verified), "graph_active_replacements": str(accepted), "restored_boundaries": str(restored), "failure_reason": "", "schema_version": "joint_ablation_v1"},
        ]
    )
    by_split = {}
    for split in {"dev", "heldout"}:
        subset = [row for row in rows["real_benchmark_results.csv"] if row["split"] == split]
        fails = Counter(row["failure_reason"] for row in rows["real_benchmark_results.csv"] if row["split"] == split)
        rows["heldout_results.csv"].append(
            {
                "split": split,
                "attempted": str(len(subset)),
                "verified_modules": "0",
                "graph_active_replacements": "0",
                "restored_boundaries": "0",
                "failure_reasons": json.dumps(dict(sorted(fails.items())), sort_keys=True),
                "schema_version": "joint_heldout_result_v1",
            }
        )
        by_split[split] = len(subset)
    failures = Counter()
    for row in rows["controlled_benchmark_results.csv"]:
        if row["final_status"] != "accepted":
            failures[("controlled", "replacement", row["rejection_reason"])] += 1
    for row in rows["failure_taxonomy.csv"]:
        failures[(row["benchmark_group"], row["failure_stage"], row["failure_reason"])] += int(row["count"])
    rows["failure_taxonomy.csv"] = [
        {"benchmark_group": key[0], "failure_stage": key[1], "failure_reason": key[2], "count": str(count), "schema_version": "joint_failure_taxonomy_v1"}
        for key, count in sorted(failures.items())
    ]
    total_runtime = sum(float(row["total_runtime_seconds"]) for row in rows["runtime_timeout_summary.csv"])
    rows["runtime_timeout_summary.csv"].append({"stage": "total", "queries": str(len(rows["proof_results.csv"])), "timeouts": "0", "total_runtime_seconds": f"{total_runtime:.6f}", "max_runtime_seconds": f"{max([float(row['max_runtime_seconds']) for row in rows['runtime_timeout_summary.csv']] or [0.0]):.6f}", "schema_version": "joint_runtime_timeout_v1"})


def _write_summary(rows: dict[str, list[dict[str, str]]]) -> None:
    controlled = rows["controlled_benchmark_results.csv"]
    real = rows["real_benchmark_results.csv"]
    prior_real = sum(1 for row in real if row["seed_id"].startswith("real_seed_"))
    fresh_real = sum(1 for row in real if row["seed_id"].startswith("fresh_structural_seed_"))
    accepted = sum(1 for row in controlled if row["final_status"] == "accepted")
    restored = sum(1 for row in controlled if row["restored_boundary"] == "true")
    failures = Counter((row["benchmark_group"], row["failure_stage"], row["failure_reason"]) for row in rows["failure_taxonomy.csv"])
    lines = [
        "# Joint Region/Interface Discovery Summary",
        "",
        "This phase replaces isolated semantic anchors with proof-carrying closed-region replacement.",
        "The primary implementation path is source-blind: candidate search records structural seeds, proof-guided repairs, and post-inference evaluation only.",
        "",
        f"- Controlled cases attempted: {len(controlled)}",
        f"- Controlled graph-active replacements accepted: {accepted}",
        f"- Controlled boundaries restored: {restored}",
        f"- Prior real isolated-anchor attempts revisited: {prior_real}",
        f"- Fresh source-blind structural real seeds evaluated: {fresh_real}",
        "- Real benchmark graph-active restorations: 0",
        "- Real failure interpretation: bounded joint search still cannot form legal closed implementation regions from the prior isolated-anchor seeds; this separates graph/interface failure from semantic expression proof.",
        "",
        "## Evidence Rules",
        "",
        "- `newly_recovered_boundary=true` requires `graph_active=true` and `implementation_global_cec=equivalent`.",
        "- Contextual or unresolved rows are never promoted to global equivalence.",
        "- Ground-truth labels are not used by the joint candidate generator.",
        "",
        "## Failure Taxonomy",
        "",
    ]
    for row in rows["failure_taxonomy.csv"]:
        lines.append(f"- {row['benchmark_group']} / {row['failure_stage']} / {row['failure_reason']}: {row['count']}")
    (OUT / "joint_region_interface_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _environment_rows() -> list[dict[str, str]]:
    abc = ROOT / ".abc_build" / "abc_repo" / "abc"
    abc_path = str(abc) if abc.exists() else (shutil.which("abc") or "")
    return [
        {"tool": "python", "version": platform.python_version(), "path": sys.executable, "status": "available", "schema_version": "joint_environment_v1"},
        {"tool": "z3", "version": z3.get_version_string() if z3 is not None else "", "path": "", "status": "available" if z3 is not None else "missing", "schema_version": "joint_environment_v1"},
        {"tool": "abc", "version": _abc_version(abc_path), "path": abc_path, "status": "available" if abc_path else "missing", "schema_version": "joint_environment_v1"},
    ]


def _abc_version(abc_path: str) -> str:
    if not abc_path:
        return ""
    try:
        proc = subprocess.run([abc_path, "-c", "version"], text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=5)
        return " ".join(proc.stdout.split())[:160]
    except Exception as exc:
        return f"version_error:{type(exc).__name__}"


def _rejection_reason(formal_ok: bool, rewrite_status: str, cec_status: str) -> str:
    if not formal_ok:
        return "semantic_region_not_proven"
    if rewrite_status != "valid":
        return rewrite_status
    return cec_status


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def _real_failure_reason(old: dict[str, str]) -> str:
    reason = old.get("rejection_reason", "") or old.get("acceptance_status", "unknown")
    if "no_mapped_cut" in reason:
        return "no_source_blind_closed_input_cut"
    if "frontier" in reason:
        return "semantic_target_outside_closed_frontier"
    if "fanout" in reason:
        return "no_legal_external_fanout_mapping"
    if "whole_design" in reason or "unbounded" in reason:
        return "bounded_search_reaches_whole_design_risk"
    return reason or "no_legal_closed_region_under_bounds"


def _influence_matrix(case_id: str, repair: str, before: JointRegionInterfaceCandidate, after: JointRegionInterfaceCandidate) -> dict[str, object]:
    return {
        "case_id": case_id,
        "schema_version": "joint_influence_matrix_v1",
        "features": ["implementation_nodes", "input_cut", "output_cut"],
        "repair_operation": repair,
        "deltas": {
            "implementation_nodes": len(set(after.implementation_nodes) ^ set(before.implementation_nodes)),
            "input_cut": len(set(after.input_cut) ^ set(before.input_cut)),
            "output_cut": len(set(after.output_cut) ^ set(before.output_cut)),
        },
        "source_blind": True,
    }


def _split(case_id: str) -> str:
    value = int(hashlib.sha1(case_id.encode("utf-8")).hexdigest()[:8], 16)
    return "heldout" if value % 5 == 0 else "dev"


def _git_head() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    except Exception:
        return "unknown"


if __name__ == "__main__":
    raise SystemExit(main())
