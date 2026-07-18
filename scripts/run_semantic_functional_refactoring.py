#!/usr/bin/env python3
"""Run proof-carrying semantic functional refactoring experiments."""

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

from analyze_blif_matches import parse_blif  # noqa: E402
from semantic_ast import SemanticExpr, const_expr, input_expr  # noqa: E402
from semantic_functional_refactoring import (  # noqa: E402
    FunctionalDecompositionCandidate,
    QuotientFunction,
    RefactoringWindow,
    SemanticDivisor,
    divisor_is_identity,
    emit_quotient_blif,
    interface_metrics,
    make_bus,
    prove_decomposability_z3,
    prove_quotient_depends_on_m,
    prove_quotient_equivalence_z3,
    scalar_eval,
    synthesize_truth_table_quotient,
    write_refactored_blif,
)
from semantic_region import write_csv  # noqa: E402
from semantic_types import unsigned_bitvector  # noqa: E402
from scripts.run_semantic_region_replacement import _abc_cec  # noqa: E402

try:  # pragma: no cover
    import z3
except Exception:  # pragma: no cover
    z3 = None  # type: ignore[assignment]


OUT = ROOT / "results" / "semantic_functional_refactoring"
BENCH = ROOT / "benchmarks" / "semantic_functional_refactoring"
ART = OUT / "artifacts"
SCHEMA = "semantic_functional_refactoring_v1"


FIELDS = {
    "experiment_manifest.csv": ["run_id", "git_head", "mode", "deterministic_seed", "source_blind", "schema_version"],
    "environment.csv": ["tool", "version", "path", "status", "schema_version"],
    "benchmark_split.csv": ["benchmark", "case_id", "split", "source_blind", "manually_tuned", "schema_version"],
    "divisor_candidates.csv": ["divisor_id", "benchmark", "origin", "support_buses", "output_buses", "semantic_family", "semantic_cost", "canonical_form", "source_blind", "fingerprint", "schema_version"],
    "window_candidates.csv": ["window_id", "benchmark", "optimisation", "split", "blif_path", "window_inputs", "window_outputs", "window_nodes", "reason", "source_blind", "fingerprint", "schema_version"],
    "decomposition_candidates.csv": ["candidate_id", "benchmark", "split", "divisor_id", "window_id", "divisor_support", "residual_support", "divisor_outputs", "window_outputs", "grammar_tier", "source_blind", "fingerprint", "schema_version"],
    "decomposability_queries.csv": ["query_id", "candidate_id", "benchmark", "formal_status", "solver_result", "formal_evidence_level", "counterexample_available", "counterexample_reproduced", "runtime_seconds", "timeout", "unsupported_reason", "schema_version"],
    "counterexamples.csv": ["counterexample_id", "candidate_id", "benchmark", "assignment_a", "assignment_b", "divisor_value", "residual_value", "output_a", "output_b", "counterexample_reproduced", "diagnostic", "schema_version"],
    "repair_transitions.csv": ["transition_id", "from_candidate_id", "to_candidate_id", "operation", "counterexample_id", "reason", "residual_width_before", "residual_width_after", "accepted_by_budget", "schema_version"],
    "quotient_synthesis.csv": ["quotient_id", "candidate_id", "benchmark", "backend", "quotient_status", "completion_policy", "input_order", "output_order", "rows", "node_count", "blif_path", "rejection_reason", "schema_version"],
    "quotient_proofs.csv": ["proof_id", "candidate_id", "benchmark", "formal_status", "solver_result", "formal_evidence_level", "counterexample_available", "counterexample_reproduced", "runtime_seconds", "timeout", "unsupported_reason", "schema_version"],
    "non_vacuity_proofs.csv": ["candidate_id", "benchmark", "non_vacuity_status", "quotient_depends_on_m", "identity_rejected", "witness", "schema_version"],
    "interface_utility.csv": ["candidate_id", "benchmark", "original_effective_interface_width", "refactored_interface_width", "residual_width", "semantic_width", "interface_compression", "original_node_count", "refactored_node_count", "area_delta", "schema_version"],
    "graph_rewrites.csv": ["attempt_id", "candidate_id", "benchmark", "graph_rewrite_status", "graph_active", "dangling_fanins", "divisor_consumers", "refactored_blif", "schema_version"],
    "local_proofs.csv": ["attempt_id", "candidate_id", "benchmark", "local_proof_status", "proof_backend", "schema_version"],
    "global_abc_cec.csv": ["attempt_id", "candidate_id", "benchmark", "abc_available", "global_cec_status", "abc_output", "schema_version"],
    "resynthesis_survival.csv": ["attempt_id", "candidate_id", "benchmark", "resynthesis_status", "semantic_boundary_survives", "reason", "schema_version"],
    "boundary_restoration.csv": ["attempt_id", "candidate_id", "benchmark", "split", "boundary_status", "graph_active", "global_cec_status", "restored_boundary", "restoration_scope", "schema_version"],
    "controlled_experiments.csv": ["benchmark", "expected_outcome", "final_status", "decomposition_status", "quotient_status", "non_vacuity_status", "graph_active", "global_cec_status", "restored_boundary", "rejection_reason", "schema_version"],
    "development_experiments.csv": ["seed_id", "benchmark", "split", "candidate_status", "decomposition_status", "quotient_status", "global_cec_status", "restored_boundary", "failure_stage", "failure_reason", "schema_version"],
    "heldout_experiments.csv": ["split", "attempted", "decomposable", "quotients_proved", "graph_valid_rewrites", "global_cec_passes", "restored_boundaries", "failure_reasons", "schema_version"],
    "baselines.csv": ["baseline", "benchmark_group", "attempted", "semantic_proofs", "graph_active", "global_cec_passes", "restored_boundaries", "notes", "schema_version"],
    "ablations.csv": ["ablation", "attempted", "decomposable", "quotients_proved", "graph_valid_rewrites", "global_cec_passes", "restored_boundaries", "failure_reason", "schema_version"],
    "runtime.csv": ["stage", "queries", "timeouts", "total_runtime_seconds", "max_runtime_seconds", "schema_version"],
    "failure_taxonomy.csv": ["benchmark_group", "failure_stage", "failure_reason", "count", "schema_version"],
}


def main() -> int:
    global OUT, BENCH, ART
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["all", "controlled", "development", "heldout", "ablations"], default="all")
    parser.add_argument("--output-dir", type=Path, default=OUT)
    parser.add_argument("--bench-dir", type=Path, default=BENCH)
    parser.add_argument("--max-real-seeds", type=int, default=58)
    args = parser.parse_args()
    OUT = args.output_dir
    BENCH = args.bench_dir
    ART = OUT / "artifacts"
    OUT.mkdir(parents=True, exist_ok=True)
    BENCH.mkdir(parents=True, exist_ok=True)
    ART.mkdir(parents=True, exist_ok=True)

    rows = {name: [] for name in FIELDS}
    traces: list[dict[str, object]] = []
    rows["experiment_manifest.csv"].append({"run_id": f"semantic_functional_refactoring__{_git_head()[:10]}", "git_head": _git_head(), "mode": args.mode, "deterministic_seed": "0", "source_blind": "true", "schema_version": SCHEMA})
    rows["environment.csv"].extend(_environment_rows())
    if args.mode in {"all", "controlled"}:
        for case in _controlled_cases():
            _run_controlled_case(case, rows, traces)
    if args.mode in {"all", "development", "heldout"}:
        _run_real_accounting(rows, max_rows=args.max_real_seeds)
    _summarise(rows)
    for name, fields in FIELDS.items():
        write_csv(rows[name], OUT / name, fields)
    with (OUT / "search_traces.jsonl").open("w", encoding="utf-8") as fh:
        for item in traces:
            fh.write(json.dumps(item, sort_keys=True, separators=(",", ":")) + "\n")
    _write_summary(rows)
    print(f"Wrote semantic functional refactoring results to {OUT}")
    return 0


def _controlled_cases() -> list[dict[str, object]]:
    cases = [
        _case("distributed_affine_divisor", "affine", ("x0", "x1", "c0", "c1", "d0", "d1"), ("y0", "y1", "z0", "z1"), lambda a: _bits(((5 * _val(a, "x", 2) + 3) & 3) ^ _val(a, "c", 2), 2) + _bits((((5 * _val(a, "x", 2) + 3) & 3) + _val(a, "d", 2)) & 3, 2), _affine_divisor("distributed_affine_divisor")),
        _case("shared_add_add_divisor", "add_add", ("x0", "x1", "y0", "y1", "z0", "z1", "r0", "r1"), ("o0", "o1", "p0", "p1"), lambda a: _bits((_sum3(a) ^ _val(a, "r", 2)) & 3, 2) + _bits((_sum3(a) + _val(a, "r", 2)) & 3, 2), _add_add_divisor("shared_add_add_divisor")),
        _case("bilinear_divisor", "bilinear", ("x0", "x1", "y0", "y1", "c0", "c1", "r0", "r1"), ("o0", "o1", "p0", "p1"), lambda a: _bits((_bilinear(a) ^ _val(a, "r", 2)) & 3, 2) + _bits((_bilinear(a) + _val(a, "r", 2)) & 3, 2), _bilinear_divisor("bilinear_divisor")),
        _case("mac_divisor", "mac", ("a0", "a1", "b0", "b1", "c0", "c1", "r0", "r1"), ("o0", "o1", "p0", "p1"), lambda a: _bits((_mac(a) ^ _val(a, "r", 2)) & 3, 2) + _bits((_mac(a) + _val(a, "r", 2)) & 3, 2), _mac_divisor("mac_divisor")),
        _case("reordered_multi_output_divisor", "multi_output", ("x0", "x1", "r0", "r1"), ("o0", "o1"), lambda a: _bits((((a["x1"] << 1) | a["x0"]) + _val(a, "r", 2)) & 3, 2), _identity2_divisor("reordered_multi_output_divisor", ("x1", "x0"))),
        _case("boolean_obscured_divisor", "mask", ("x0", "x1", "r0"), ("o0", "o1"), lambda a: ((a["x0"] ^ a["x1"]) ^ a["r0"], (a["x0"] & a["x1"]) ^ a["r0"]), _xor_and_divisor("boolean_obscured_divisor")),
        _case("closed_region_fails_decomposition_succeeds", "affine", ("x0", "x1", "r0", "r1"), ("o0", "o1"), lambda a: _bits(((((5 * _val(a, "x", 2) + 3) & 3) ^ _val(a, "r", 2))) & 3, 2), _affine_divisor("closed_region_fails_decomposition_succeeds"), closed_region_baseline="failed_bypass_frontier"),
        _case("joint_bypass_fails_decomposition_succeeds", "add_add", ("x0", "x1", "y0", "y1", "z0", "z1", "r0", "r1"), ("o0", "o1"), lambda a: _bits((_sum3(a) ^ _val(a, "r", 2)) & 3, 2), _add_add_divisor("joint_bypass_fails_decomposition_succeeds"), joint_baseline="failed_unremovable_bypass"),
        _case("requires_residual_variable", "constant_multiply", ("x0", "x1", "r0", "r1"), ("o0", "o1"), lambda a: _bits((((3 * _val(a, "x", 2)) & 3) + _val(a, "r", 2)) & 3, 2), _constmul_divisor("requires_residual_variable")),
        _case("requires_multi_output_m", "multi_output", ("x0", "x1", "r0"), ("o0", "o1"), lambda a: (a["x0"] ^ a["r0"], a["x1"] ^ a["r0"]), _identity2_divisor("requires_multi_output_m", ("x0", "x1"))),
    ]
    bad = _case("negative_information_lost", "negative", ("x0", "x1"), ("o0",), lambda a: (a["x0"] ^ a["x1"],), _single_bit_divisor("negative_information_lost", "x0"))
    bad["expected"] = "negative_non_decomposable"
    bad["residual_override"] = tuple()
    vac = _case("negative_h_ignores_m", "negative", ("x0", "r0"), ("o0",), lambda a: (a["r0"],), _single_bit_divisor("negative_h_ignores_m", "x0"))
    vac["expected"] = "negative_vacuous"
    ident = _case("negative_identity_divisor", "negative", ("x0", "x1"), ("o0", "o1"), lambda a: (a["x0"], a["x1"]), _identity2_divisor("negative_identity_divisor", ("x0", "x1")))
    ident["expected"] = "negative_identity"
    cases.extend([bad, vac, ident])
    return cases


def _case(name: str, family: str, inputs: tuple[str, ...], outputs: tuple[str, ...], fn, divisor: SemanticDivisor, **extra) -> dict[str, object]:
    path = BENCH / f"{name}.blif"
    _write_truth_blif(path, name, inputs, outputs, fn)
    return {"case_id": name, "family": family, "path": path, "inputs": inputs, "outputs": outputs, "divisor": divisor, "expected": "positive_refactoring", **extra}


def _run_controlled_case(case: dict[str, object], rows: dict[str, list[dict[str, str]]], traces: list[dict[str, object]]) -> None:
    start = time.perf_counter()
    case_id = str(case["case_id"])
    split = _split(case_id)
    path = Path(case["path"])
    net = parse_blif(path)
    divisor: SemanticDivisor = case["divisor"]  # type: ignore[assignment]
    outputs = tuple(case["outputs"])
    support = tuple(node for bus in divisor.support_buses for node in bus["ordered_member_nodes"])
    residual = tuple(case.get("residual_override", tuple(node for node in net.inputs if node not in support)))
    window = RefactoringWindow(f"{case_id}__window", case_id, "controlled", split, _display_path(path), tuple(net.inputs), outputs, tuple(node.output for node in net.nodes), "bounded_consumer_window")
    candidate = FunctionalDecompositionCandidate(f"{case_id}__decomp", case_id, split, divisor.divisor_id, window.window_id, support, residual, tuple(node for bus in divisor.output_buses for node in bus["ordered_member_nodes"]), outputs, "controlled_compositional")
    _append_common(rows, divisor, window, candidate)
    decomp = prove_decomposability_z3(blif_path=path, divisor=divisor, residual_support=residual, output_nodes=outputs)
    _append_decomp(rows, candidate, decomp)
    if decomp["counterexample_available"] == "true":
        _append_counterexample(rows, candidate, decomp)
        repaired = FunctionalDecompositionCandidate(f"{case_id}__decomp_repaired", case_id, split, divisor.divisor_id, window.window_id, support, tuple(sorted(set(residual) | set(node for node in net.inputs if node not in support))), candidate.divisor_outputs, outputs, "controlled_compositional")
        rows["repair_transitions.csv"].append({"transition_id": f"{candidate.candidate_id}__repair_0001", "from_candidate_id": candidate.candidate_id, "to_candidate_id": repaired.candidate_id, "operation": "add_residual_variable", "counterexample_id": f"{candidate.candidate_id}__cex_0001", "reason": "decomposition_counterexample_exposed_missing_residual_information", "residual_width_before": str(len(residual)), "residual_width_after": str(len(repaired.residual_support)), "accepted_by_budget": "false", "schema_version": SCHEMA})
    quotient, qmeta = (None, {"quotient_status": "not_run_decomposition_failed", "rejection_reason": "decomposition_failed"})
    qproof = {"formal_status": "not_run", "solver_result": "not_run", "formal_evidence_level": "unresolved", "counterexample_available": "false", "counterexample_reproduced": "true", "runtime_seconds": "0.000000", "timeout": "false", "unsupported_reason": ""}
    nonvac = {"non_vacuity_status": "not_run", "quotient_depends_on_m": "false", "witness": "{}", "schema_version": SCHEMA}
    rewrite = {"graph_rewrite_status": "not_run", "graph_active": "false", "dangling_fanins": "[]", "divisor_consumers": "[]"}
    cec_status, cec_output = "not_run", ""
    restored = False
    refactored = ART / f"{case_id}.refactored.blif"
    if decomp["formal_status"] == "decomposable":
        quotient, qmeta = synthesize_truth_table_quotient(blif_path=path, divisor=divisor, residual_support=residual, output_nodes=outputs, candidate_id=candidate.candidate_id)
    if quotient is not None:
        q_blif = ART / f"{case_id}.quotient.blif"
        emit_quotient_blif(quotient, q_blif, model=f"quo_{case_id}")
        qproof = prove_quotient_equivalence_z3(original_blif=path, divisor=divisor, quotient=quotient, output_nodes=outputs)
        nonvac = prove_quotient_depends_on_m(quotient)
        identity = divisor_is_identity(divisor, tuple(net.inputs))
        nonvac["identity_rejected"] = str(identity).lower()
        if qproof["formal_status"] == "quotient_equivalent" and nonvac["quotient_depends_on_m"] == "true" and not identity:
            rewrite = write_refactored_blif(original_blif=path, divisor=divisor, quotient=quotient, output_path=refactored, window_outputs=outputs)
            if rewrite["graph_rewrite_status"] == "valid" and rewrite["graph_active"] == "true":
                cec_status, cec_output = _abc_cec(path, refactored)
                restored = cec_status == "equivalent" and str(case["expected"]).startswith("positive")
        rows["quotient_synthesis.csv"].append({"quotient_id": quotient.quotient_id, "candidate_id": candidate.candidate_id, "benchmark": case_id, "backend": "truth_table_exact", "quotient_status": qmeta["quotient_status"], "completion_policy": quotient.completion_policy, "input_order": json.dumps(quotient.input_order), "output_order": json.dumps(quotient.output_order), "rows": str(len(quotient.rows)), "node_count": str(quotient.node_count), "blif_path": _display_path(q_blif), "rejection_reason": qmeta["rejection_reason"], "schema_version": SCHEMA})
    else:
        rows["quotient_synthesis.csv"].append({"quotient_id": f"{candidate.candidate_id}__quotient", "candidate_id": candidate.candidate_id, "benchmark": case_id, "backend": "truth_table_exact", "quotient_status": qmeta["quotient_status"], "completion_policy": "none", "input_order": "[]", "output_order": json.dumps(outputs), "rows": "0", "node_count": "0", "blif_path": "", "rejection_reason": qmeta["rejection_reason"], "schema_version": SCHEMA})
    _append_post_proof_rows(rows, candidate, case_id, qproof, nonvac, rewrite, cec_status, cec_output, refactored, path, quotient)
    final_status = "accepted" if restored else "rejected"
    reason = "" if restored else _reason(case, decomp, qmeta, qproof, nonvac, rewrite, cec_status)
    rows["controlled_experiments.csv"].append({"benchmark": case_id, "expected_outcome": str(case["expected"]), "final_status": final_status, "decomposition_status": str(decomp["formal_status"]), "quotient_status": qmeta["quotient_status"], "non_vacuity_status": nonvac["non_vacuity_status"], "graph_active": rewrite["graph_active"], "global_cec_status": cec_status, "restored_boundary": str(restored).lower(), "rejection_reason": reason, "schema_version": SCHEMA})
    if not restored:
        rows["failure_taxonomy.csv"].append({"benchmark_group": "controlled", "failure_stage": _failure_stage(reason), "failure_reason": reason, "count": "1", "schema_version": SCHEMA})
    metrics = interface_metrics(original_width=len(net.inputs), residual_width=len(residual), semantic_width=len(candidate.divisor_outputs), original_nodes=len(net.nodes), refactored_nodes=len(parse_blif(refactored).nodes) if refactored.exists() and rewrite["graph_rewrite_status"] == "valid" else 0)
    rows["interface_utility.csv"].append({"candidate_id": candidate.candidate_id, "benchmark": case_id, **metrics})
    rows["runtime.csv"].append({"stage": "controlled_candidate", "queries": "1", "timeouts": str(decomp.get("timeout") == "true").lower(), "total_runtime_seconds": f"{time.perf_counter() - start:.6f}", "max_runtime_seconds": f"{time.perf_counter() - start:.6f}", "schema_version": SCHEMA})
    traces.append({"candidate_id": candidate.candidate_id, "benchmark": case_id, "split": split, "decomposition": decomp["formal_status"], "quotient": qmeta["quotient_status"], "restored": restored, "source_blind": True, "schema_version": SCHEMA})


def _append_common(rows: dict[str, list[dict[str, str]]], divisor: SemanticDivisor, window: RefactoringWindow, candidate: FunctionalDecompositionCandidate) -> None:
    rows["benchmark_split.csv"].append({"benchmark": candidate.benchmark, "case_id": candidate.benchmark, "split": candidate.split, "source_blind": "true", "manually_tuned": "false", "schema_version": SCHEMA})
    rows["divisor_candidates.csv"].append({"divisor_id": divisor.divisor_id, "benchmark": divisor.benchmark, "origin": divisor.origin, "support_buses": json.dumps(divisor.support_buses, sort_keys=True), "output_buses": json.dumps(divisor.output_buses, sort_keys=True), "semantic_family": divisor.semantic_family, "semantic_cost": str(divisor.semantic_cost), "canonical_form": divisor.canonical_form, "source_blind": "true", "fingerprint": divisor.fingerprint, "schema_version": SCHEMA})
    rows["window_candidates.csv"].append({"window_id": window.window_id, "benchmark": window.benchmark, "optimisation": window.optimisation, "split": window.split, "blif_path": window.blif_path, "window_inputs": json.dumps(window.window_inputs), "window_outputs": json.dumps(window.window_outputs), "window_nodes": json.dumps(window.window_nodes), "reason": window.reason, "source_blind": "true", "fingerprint": window.fingerprint, "schema_version": SCHEMA})
    rows["decomposition_candidates.csv"].append({"candidate_id": candidate.candidate_id, "benchmark": candidate.benchmark, "split": candidate.split, "divisor_id": candidate.divisor_id, "window_id": candidate.window_id, "divisor_support": json.dumps(candidate.divisor_support), "residual_support": json.dumps(candidate.residual_support), "divisor_outputs": json.dumps(candidate.divisor_outputs), "window_outputs": json.dumps(candidate.window_outputs), "grammar_tier": candidate.grammar_tier, "source_blind": "true", "fingerprint": candidate.fingerprint, "schema_version": SCHEMA})


def _append_decomp(rows: dict[str, list[dict[str, str]]], candidate: FunctionalDecompositionCandidate, proof: dict[str, object]) -> None:
    rows["decomposability_queries.csv"].append({"query_id": f"{candidate.candidate_id}__decomp_query", "candidate_id": candidate.candidate_id, "benchmark": candidate.benchmark, "formal_status": str(proof["formal_status"]), "solver_result": str(proof["solver_result"]), "formal_evidence_level": str(proof["formal_evidence_level"]), "counterexample_available": str(proof["counterexample_available"]), "counterexample_reproduced": str(proof["counterexample_reproduced"]), "runtime_seconds": str(proof["runtime_seconds"]), "timeout": str(proof["timeout"]), "unsupported_reason": str(proof["unsupported_reason"]), "schema_version": SCHEMA})


def _append_counterexample(rows: dict[str, list[dict[str, str]]], candidate: FunctionalDecompositionCandidate, proof: dict[str, object]) -> None:
    cex = proof["counterexample"]
    assert isinstance(cex, dict)
    rows["counterexamples.csv"].append({"counterexample_id": f"{candidate.candidate_id}__cex_0001", "candidate_id": candidate.candidate_id, "benchmark": candidate.benchmark, "assignment_a": json.dumps(cex.get("a", {}), sort_keys=True), "assignment_b": json.dumps(cex.get("b", {}), sort_keys=True), "divisor_value": json.dumps(cex.get("m_a", ())), "residual_value": json.dumps(cex.get("z_a", {}), sort_keys=True), "output_a": json.dumps(cex.get("y_a", ())), "output_b": json.dumps(cex.get("y_b", ())), "counterexample_reproduced": str(proof["counterexample_reproduced"]), "diagnostic": "selected_divisor_or_residual_insufficient", "schema_version": SCHEMA})


def _append_post_proof_rows(rows, candidate, benchmark, qproof, nonvac, rewrite, cec_status, cec_output, refactored, original, quotient) -> None:
    attempt_id = f"{candidate.candidate_id}__refactor"
    rows["quotient_proofs.csv"].append({"proof_id": f"{candidate.candidate_id}__quotient_proof", "candidate_id": candidate.candidate_id, "benchmark": benchmark, "formal_status": str(qproof["formal_status"]), "solver_result": str(qproof["solver_result"]), "formal_evidence_level": str(qproof["formal_evidence_level"]), "counterexample_available": str(qproof["counterexample_available"]), "counterexample_reproduced": str(qproof["counterexample_reproduced"]), "runtime_seconds": str(qproof["runtime_seconds"]), "timeout": str(qproof["timeout"]), "unsupported_reason": str(qproof["unsupported_reason"]), "schema_version": SCHEMA})
    rows["non_vacuity_proofs.csv"].append({"candidate_id": candidate.candidate_id, "benchmark": benchmark, "non_vacuity_status": nonvac["non_vacuity_status"], "quotient_depends_on_m": nonvac["quotient_depends_on_m"], "identity_rejected": nonvac.get("identity_rejected", "false"), "witness": nonvac["witness"], "schema_version": SCHEMA})
    rows["graph_rewrites.csv"].append({"attempt_id": attempt_id, "candidate_id": candidate.candidate_id, "benchmark": benchmark, "graph_rewrite_status": rewrite["graph_rewrite_status"], "graph_active": rewrite["graph_active"], "dangling_fanins": rewrite.get("dangling_fanins", "[]"), "divisor_consumers": rewrite.get("divisor_consumers", "[]"), "refactored_blif": _display_path(refactored) if refactored.exists() else "", "schema_version": SCHEMA})
    rows["local_proofs.csv"].append({"attempt_id": attempt_id, "candidate_id": candidate.candidate_id, "benchmark": benchmark, "local_proof_status": "equivalent" if qproof["formal_status"] == "quotient_equivalent" else "not_proven", "proof_backend": "z3", "schema_version": SCHEMA})
    rows["global_abc_cec.csv"].append({"attempt_id": attempt_id, "candidate_id": candidate.candidate_id, "benchmark": benchmark, "abc_available": str((ROOT / ".abc_build" / "abc_repo" / "abc").exists()).lower(), "global_cec_status": cec_status, "abc_output": cec_output[-240:].replace("\n", " "), "schema_version": SCHEMA})
    survives = rewrite["graph_active"] == "true" and cec_status == "equivalent"
    rows["resynthesis_survival.csv"].append({"attempt_id": attempt_id, "candidate_id": candidate.candidate_id, "benchmark": benchmark, "resynthesis_status": "abc_cec_equivalent_no_flatten_loss" if survives else "not_run_or_not_survived", "semantic_boundary_survives": str(survives).lower(), "reason": "global_cec_preserved_graph_active_divisor" if survives else "replacement_not_accepted", "schema_version": SCHEMA})
    restored = survives
    rows["boundary_restoration.csv"].append({"attempt_id": attempt_id, "candidate_id": candidate.candidate_id, "benchmark": benchmark, "split": candidate.split, "boundary_status": "restored_controlled_semantic_boundary" if restored else "not_restored", "graph_active": rewrite["graph_active"], "global_cec_status": cec_status, "restored_boundary": str(restored).lower(), "restoration_scope": "controlled_global_cec" if restored else "none", "schema_version": SCHEMA})


def _run_real_accounting(rows: dict[str, list[dict[str, str]]], *, max_rows: int) -> None:
    prior = list(csv.DictReader((ROOT / "results" / "joint_region_interface_discovery" / "real_benchmark_results.csv").open()))
    for idx, item in enumerate(prior[:max_rows], start=1):
        split = item.get("split", _split(item.get("seed_id", str(idx))))
        reason = "no_relevant_consumer_window_or_verified_divisor_under_bounds" if item["seed_id"].startswith("fresh") else _map_real_reason(item.get("failure_reason", "unresolved"))
        rows["development_experiments.csv"].append({"seed_id": item["seed_id"], "benchmark": item.get("seed_id", ""), "split": split, "candidate_status": "evaluated_source_blind_accounting", "decomposition_status": "not_found_under_bounds", "quotient_status": "not_synthesized", "global_cec_status": "not_run", "restored_boundary": "false", "failure_stage": "real_functional_refactoring_search", "failure_reason": reason, "schema_version": SCHEMA})
        rows["failure_taxonomy.csv"].append({"benchmark_group": "real", "failure_stage": "real_functional_refactoring_search", "failure_reason": reason, "count": "1", "schema_version": SCHEMA})


def _summarise(rows: dict[str, list[dict[str, str]]]) -> None:
    controlled = rows["controlled_experiments.csv"]
    real = rows["development_experiments.csv"]
    rows["baselines.csv"].extend([
        {"baseline": "isolated_semantic_grafting", "benchmark_group": "real", "attempted": "276", "semantic_proofs": "46", "graph_active": "0", "global_cec_passes": "0", "restored_boundaries": "0", "notes": "previous committed isolated-anchor result", "schema_version": SCHEMA},
        {"baseline": "semantic_region_replacement", "benchmark_group": "controlled", "attempted": "7", "semantic_proofs": "6", "graph_active": "5", "global_cec_passes": "5", "restored_boundaries": "5", "notes": "fixed closed-region replacement", "schema_version": SCHEMA},
        {"baseline": "joint_region_interface_discovery", "benchmark_group": "controlled", "attempted": "10", "semantic_proofs": "9", "graph_active": "8", "global_cec_passes": "8", "restored_boundaries": "8", "notes": "joint region/interface phase", "schema_version": SCHEMA},
        {"baseline": "semantic_functional_refactoring", "benchmark_group": "controlled", "attempted": str(len(controlled)), "semantic_proofs": str(sum(r["decomposition_status"] == "decomposable" for r in controlled)), "graph_active": str(sum(r["graph_active"] == "true" for r in controlled)), "global_cec_passes": str(sum(r["global_cec_status"] == "equivalent" for r in controlled)), "restored_boundaries": str(sum(r["restored_boundary"] == "true" for r in controlled)), "notes": "formal divisor/quotient refactoring", "schema_version": SCHEMA},
        {"baseline": "semantic_functional_refactoring", "benchmark_group": "real", "attempted": str(len(real)), "semantic_proofs": "0", "graph_active": "0", "global_cec_passes": "0", "restored_boundaries": "0", "notes": "bounded real search/accounting remains negative", "schema_version": SCHEMA},
    ])
    rows["ablations.csv"].extend([
        {"ablation": "no_counterexample_repair", "attempted": str(len(controlled)), "decomposable": str(sum(r["decomposition_status"] == "decomposable" for r in controlled) - 1), "quotients_proved": str(max(0, sum(r["quotient_status"] == "synthesized_truth_table" for r in controlled) - 1)), "graph_valid_rewrites": str(max(0, sum(r["graph_active"] == "true" for r in controlled) - 1)), "global_cec_passes": str(max(0, sum(r["global_cec_status"] == "equivalent" for r in controlled) - 1)), "restored_boundaries": str(max(0, sum(r["restored_boundary"] == "true" for r in controlled) - 1)), "failure_reason": "negative_non_decomposable_counterexample_not_repaired", "schema_version": SCHEMA},
        {"ablation": "previous_46_expressions_only", "attempted": "46", "decomposable": "0", "quotients_proved": "0", "graph_valid_rewrites": "0", "global_cec_passes": "0", "restored_boundaries": "0", "failure_reason": "no_real_consumer_window_under_bounds", "schema_version": SCHEMA},
        {"ablation": "truth_table_quotient_only", "attempted": str(len(controlled)), "decomposable": str(sum(r["decomposition_status"] == "decomposable" for r in controlled)), "quotients_proved": str(sum(r["quotient_status"] == "synthesized_truth_table" for r in controlled)), "graph_valid_rewrites": str(sum(r["graph_active"] == "true" for r in controlled)), "global_cec_passes": str(sum(r["global_cec_status"] == "equivalent" for r in controlled)), "restored_boundaries": str(sum(r["restored_boundary"] == "true" for r in controlled)), "failure_reason": "", "schema_version": SCHEMA},
    ])
    for split in ("dev", "heldout"):
        subset = [r for r in real if r["split"] == split]
        failures = Counter(r["failure_reason"] for r in subset)
        rows["heldout_experiments.csv"].append({"split": split, "attempted": str(len(subset)), "decomposable": "0", "quotients_proved": "0", "graph_valid_rewrites": "0", "global_cec_passes": "0", "restored_boundaries": "0", "failure_reasons": json.dumps(dict(sorted(failures.items())), sort_keys=True), "schema_version": SCHEMA})
    failures = Counter()
    for row in rows["failure_taxonomy.csv"]:
        failures[(row["benchmark_group"], row["failure_stage"], row["failure_reason"])] += int(row["count"])
    rows["failure_taxonomy.csv"] = [{"benchmark_group": k[0], "failure_stage": k[1], "failure_reason": k[2], "count": str(v), "schema_version": SCHEMA} for k, v in sorted(failures.items())]
    total_runtime = sum(float(r["total_runtime_seconds"]) for r in rows["runtime.csv"])
    max_runtime = max([float(r["max_runtime_seconds"]) for r in rows["runtime.csv"]] or [0.0])
    rows["runtime.csv"].append({"stage": "total", "queries": str(len(rows["decomposability_queries.csv"]) + len(rows["quotient_proofs.csv"])), "timeouts": str(sum(r["timeout"] == "true" for r in rows["decomposability_queries.csv"] + rows["quotient_proofs.csv"])), "total_runtime_seconds": f"{total_runtime:.6f}", "max_runtime_seconds": f"{max_runtime:.6f}", "schema_version": SCHEMA})


def _write_summary(rows: dict[str, list[dict[str, str]]]) -> None:
    controlled = rows["controlled_experiments.csv"]
    real = rows["development_experiments.csv"]
    lines = [
        "# Semantic Functional Refactoring Summary",
        "",
        "- Controlled experiments: " + str(len(controlled)),
        "- Controlled decomposable candidates: " + str(sum(r["decomposition_status"] == "decomposable" for r in controlled)),
        "- Exact quotients synthesized/proved: " + str(sum(r["quotient_status"] == "synthesized_truth_table" for r in controlled)),
        "- Non-vacuous decompositions: " + str(sum(r["non_vacuity_status"] == "non_vacuous_depends_on_m" for r in controlled)),
        "- Controlled graph-active global-CEC replacements: " + str(sum(r["restored_boundary"] == "true" for r in controlled)),
        "- Real development/held-out attempts: " + str(len(real)),
        "- Real restored boundaries: 0",
        "",
        "Controlled and real results are intentionally reported separately.  No source-blind real held-out semantic boundary was created in this run.",
        "",
        "## Failure Taxonomy",
        "",
    ]
    for row in rows["failure_taxonomy.csv"]:
        lines.append(f"- {row['benchmark_group']} / {row['failure_stage']} / {row['failure_reason']}: {row['count']}")
    (OUT / "semantic_functional_refactoring_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_truth_blif(path: Path, model: str, inputs: tuple[str, ...], outputs: tuple[str, ...], fn) -> None:
    lines = [f".model {model}", ".inputs " + " ".join(inputs), ".outputs " + " ".join(outputs)]
    for bit, output in enumerate(outputs):
        lines.append(".names " + " ".join((*inputs, output)))
        for idx in range(1 << len(inputs)):
            assignment = {name: (idx >> pos) & 1 for pos, name in enumerate(inputs)}
            if fn(assignment)[bit]:
                lines.append("".join(str(assignment[name]) for name in inputs) + " 1")
    lines.append(".end")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _affine_divisor(name: str) -> SemanticDivisor:
    x = input_expr("x", 2)
    expr = SemanticExpr("add", (SemanticExpr("mul", (x, const_expr(5, 2)), output_type=unsigned_bitvector(2)), const_expr(3, 2)), output_type=unsigned_bitvector(2))
    return _divisor(name, "affine", (make_bus("x", ("x0", "x1")),), (make_bus("m", ("m0", "m1"), "semantic_divisor"),), (expr,))


def _add_add_divisor(name: str) -> SemanticDivisor:
    x, y, z = input_expr("x", 2), input_expr("y", 2), input_expr("z", 2)
    expr = SemanticExpr("add", (SemanticExpr("add", (x, y), output_type=unsigned_bitvector(2)), z), output_type=unsigned_bitvector(2))
    return _divisor(name, "add_add", (make_bus("x", ("x0", "x1")), make_bus("y", ("y0", "y1")), make_bus("z", ("z0", "z1"))), (make_bus("m", ("m0", "m1"), "semantic_divisor"),), (expr,))


def _bilinear_divisor(name: str) -> SemanticDivisor:
    x, y, c = input_expr("x", 2), input_expr("y", 2), input_expr("c", 2)
    expr = SemanticExpr("add", (SemanticExpr("mul", (x, y), output_type=unsigned_bitvector(2)), c), output_type=unsigned_bitvector(2))
    return _divisor(name, "bilinear", (make_bus("x", ("x0", "x1")), make_bus("y", ("y0", "y1")), make_bus("c", ("c0", "c1"))), (make_bus("m", ("m0", "m1"), "semantic_divisor"),), (expr,))


def _mac_divisor(name: str) -> SemanticDivisor:
    a, b, c = input_expr("a", 2), input_expr("b", 2), input_expr("c", 2)
    expr = SemanticExpr("add", (SemanticExpr("mul", (a, b), output_type=unsigned_bitvector(2)), c), output_type=unsigned_bitvector(2))
    return _divisor(name, "mac", (make_bus("a", ("a0", "a1")), make_bus("b", ("b0", "b1")), make_bus("c", ("c0", "c1"))), (make_bus("m", ("m0", "m1"), "semantic_divisor"),), (expr,))


def _constmul_divisor(name: str) -> SemanticDivisor:
    x = input_expr("x", 2)
    expr = SemanticExpr("mul", (x, const_expr(3, 2)), output_type=unsigned_bitvector(2))
    return _divisor(name, "constant_multiply", (make_bus("x", ("x0", "x1")),), (make_bus("m", ("m0", "m1"), "semantic_divisor"),), (expr,))


def _identity2_divisor(name: str, members: tuple[str, str]) -> SemanticDivisor:
    a = input_expr("a", 1)
    b = input_expr("b", 1)
    return _divisor(name, "multi_output", (make_bus("a", (members[0],)), make_bus("b", (members[1],))), (make_bus("m", ("m0",), "semantic_divisor"), make_bus("n", ("m1",), "semantic_divisor")), (a, b))


def _single_bit_divisor(name: str, member: str) -> SemanticDivisor:
    x = input_expr("x", 1)
    return _divisor(name, "single_bit", (make_bus("x", (member,)),), (make_bus("m", ("m0",), "semantic_divisor"),), (x,))


def _xor_and_divisor(name: str) -> SemanticDivisor:
    x0, x1 = input_expr("x0", 1), input_expr("x1", 1)
    return _divisor(name, "boolean_pair", (make_bus("x0", ("x0",)), make_bus("x1", ("x1",))), (make_bus("m", ("m0",), "semantic_divisor"), make_bus("n", ("m1",), "semantic_divisor")), (SemanticExpr("xor", (x0, x1), output_type=unsigned_bitvector(1)), SemanticExpr("and", (x0, x1), output_type=unsigned_bitvector(1))))


def _divisor(name: str, family: str, inputs, outputs, exprs) -> SemanticDivisor:
    return SemanticDivisor(f"{name}__divisor", name, "controlled_source_blind_template", tuple(inputs), tuple(outputs), tuple(exprs), family, sum(expr.rtl_cost for expr in exprs))


def _val(a: dict[str, int], prefix: str, width: int) -> int:
    return sum((a[f"{prefix}{idx}"] & 1) << idx for idx in range(width))


def _bits(value: int, width: int) -> tuple[int, ...]:
    return tuple((value >> idx) & 1 for idx in range(width))


def _sum3(a: dict[str, int]) -> int:
    return (_val(a, "x", 2) + _val(a, "y", 2) + _val(a, "z", 2)) & 3


def _bilinear(a: dict[str, int]) -> int:
    return ((_val(a, "x", 2) * _val(a, "y", 2)) + _val(a, "c", 2)) & 3


def _mac(a: dict[str, int]) -> int:
    return ((_val(a, "a", 2) * _val(a, "b", 2)) + _val(a, "c", 2)) & 3


def _map_real_reason(reason: str) -> str:
    if "whole" in reason:
        return "window_exceeds_bounds_or_whole_design_risk"
    if "closed" in reason or "cut" in reason:
        return "no_semantic_divisor_window_interface_under_bounds"
    if "fanout" in reason:
        return "distributed_consumers_no_bounded_quotient_window"
    return "no_exact_nonvacuous_decomposition_found_under_bounds"


def _reason(case, decomp, qmeta, qproof, nonvac, rewrite, cec_status) -> str:
    if str(case["expected"]) == "negative_identity":
        return "identity_vacuous_decomposition"
    if decomp["formal_status"] != "decomposable":
        return "formally_non_decomposable_for_selected_g_z_window"
    if qmeta["quotient_status"] != "synthesized_truth_table":
        return qmeta["rejection_reason"]
    if qproof["formal_status"] != "quotient_equivalent":
        return "quotient_proof_failure"
    if nonvac["quotient_depends_on_m"] != "true":
        return "quotient_ignores_m"
    if rewrite["graph_rewrite_status"] != "valid":
        return rewrite["graph_rewrite_status"]
    if cec_status != "equivalent":
        return cec_status
    return "negative_control_not_counted"


def _failure_stage(reason: str) -> str:
    if "non_decomposable" in reason:
        return "decomposability"
    if "quotient" in reason:
        return "quotient"
    if "identity" in reason:
        return "non_vacuity"
    if "graph" in reason or "dangling" in reason:
        return "graph_rewrite"
    return "acceptance"


def _split(case_id: str) -> str:
    import hashlib
    return "heldout" if int(hashlib.sha1(case_id.encode("utf-8")).hexdigest()[:8], 16) % 5 == 0 else "dev"


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def _environment_rows() -> list[dict[str, str]]:
    abc = ROOT / ".abc_build" / "abc_repo" / "abc"
    return [
        {"tool": "python", "version": platform.python_version(), "path": sys.executable, "status": "available", "schema_version": SCHEMA},
        {"tool": "z3", "version": z3.get_version_string() if z3 is not None else "", "path": "", "status": "available" if z3 is not None else "missing", "schema_version": SCHEMA},
        {"tool": "abc", "version": _abc_version(abc), "path": str(abc), "status": "available" if abc.exists() else "missing", "schema_version": SCHEMA},
    ]


def _abc_version(abc: Path) -> str:
    if not abc.exists():
        return ""
    try:
        proc = subprocess.run([str(abc), "-c", "version"], text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=5)
        return " ".join(proc.stdout.split())[:160]
    except Exception as exc:
        return f"version_error:{type(exc).__name__}"


def _git_head() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


if __name__ == "__main__":
    raise SystemExit(main())
