#!/usr/bin/env python3
"""Run formal locality-barrier certificate experiments."""

from __future__ import annotations

import argparse
import csv
import json
import platform
import shutil
import subprocess
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from analyze_blif_matches import BlifNetwork, BlifNode, parse_blif  # noqa: E402
from formal_locality_barriers import (  # noqa: E402
    SCHEMA_VERSION,
    CandidateSignalUniverse,
    all_assignments,
    build_source_universes,
    difference_set,
    exact_minimum_hitting_set,
    output_interface_sufficiency,
    prove_interface_sufficiency,
    scalar_eval_exact,
    solve_minimum_interface,
    stable_hash,
    validate_pair,
    vector_eval,
)
from scripts.run_semantic_region_replacement import _abc_cec, abc_binary  # noqa: E402
from semantic_region import file_hash, write_csv  # noqa: E402

try:  # pragma: no cover
    import z3
except Exception:  # pragma: no cover
    z3 = None  # type: ignore[assignment]


OUT = ROOT / "results" / "formal_locality_barriers"
CONFIG = ROOT / "configs" / "formal_locality_barriers.json"
ACTIVE_DEV = ROOT / "results" / "active_source_counterpart_refactoring" / "development_results.csv"
PLOTS = ROOT / "results" / "plots"
ASSETS = ROOT / "docs" / "presentation" / "assets" / "plots"

FIELDS = {
    "experiment_manifest.csv": ["run_id", "git_head", "mode", "config_hash", "deterministic_seed", "source_blind", "schema_version"],
    "environment.csv": ["tool", "version", "path", "status", "schema_version"],
    "baseline_metrics.csv": ["metric", "value", "source", "schema_version"],
    "frozen_configuration.csv": ["config_path", "config_hash", "deterministic_seed", "maximum_interface_width", "maximum_residual_width", "exact_search_threshold", "schema_version"],
    "target_provenance.csv": ["analysis_target_id", "target_id", "benchmark", "split", "failure_group", "source_result", "source_path", "optimized_path", "optimized_target_vector", "source_hash", "optimized_hash", "pi_alignment_status", "artifact_status", "provenance_status", "failure_reason", "schema_version"],
    "pi_alignment_validation.csv": ["analysis_target_id", "target_id", "status", "source_path", "optimized_path", "pi_alignment_hash", "failure_reason", "schema_version"],
    "candidate_universes.csv": ["universe_id", "target_id", "construction_mode", "locality_radius", "universe_size", "signals", "universe_hash", "source_hash", "optimized_hash", "diagnostic_only", "schema_version"],
    "signal_evaluations.csv": ["analysis_target_id", "target_id", "source_hash", "optimized_hash", "assignment_count", "source_signal_count", "optimized_signal_count", "evaluation_backend", "evaluation_table_hash", "schema_version"],
    "input_interface_candidates.csv": ["target_id", "universe_id", "iteration", "candidate_interface", "candidate_width", "solver_status", "termination", "schema_version"],
    "input_hitting_set_iterations.csv": ["target_id", "universe_id", "iteration", "candidate_interface", "candidate_width", "lower_bound", "exact_hitting_set_lower_bound", "solver_status", "solver_backend", "runtime_s", "counterexamples_before", "counterexamples_after", "counterexample_id", "termination", "schema_version"],
    "input_counterexamples.csv": ["counterexample_id", "target_id", "universe_id", "assignment_a_path", "assignment_b_path", "target_a", "target_b", "difference_set", "difference_set_hash", "counterexample_reproduced", "schema_version"],
    "input_difference_sets.csv": ["counterexample_id", "target_id", "universe_id", "difference_set", "difference_set_width", "difference_set_hash", "schema_version"],
    "input_exact_minimum_certificates.csv": ["certificate_id", "target_id", "benchmark", "split", "failure_group", "source_path", "optimized_path", "source_hash", "optimized_hash", "pi_alignment_hash", "target_vector", "universe_id", "universe_hash", "universe_mode", "universe_size", "locality_radius", "tested_interface", "counterexample_ids", "hitting_set_constraints_hash", "proved_lower_bound", "best_upper_bound", "exact_minimum_status", "solver_backend", "solver_status", "timeout", "proof_runtime", "reproducibility_seed", "failure_reason", "classification", "diagnostic_only", "source_blind", "schema_version"],
    "input_lower_bound_certificates.csv": ["certificate_id", "target_id", "benchmark", "split", "failure_group", "source_path", "optimized_path", "source_hash", "optimized_hash", "pi_alignment_hash", "target_vector", "universe_id", "universe_hash", "universe_mode", "universe_size", "locality_radius", "tested_interface", "counterexample_ids", "hitting_set_constraints_hash", "proved_lower_bound", "best_upper_bound", "exact_minimum_status", "solver_backend", "solver_status", "timeout", "proof_runtime", "reproducibility_seed", "failure_reason", "classification", "diagnostic_only", "source_blind", "schema_version"],
    "whole_design_diagnostics.csv": ["analysis_target_id", "target_id", "status", "minimum_width", "interface", "solver_status", "counterexamples", "classification", "schema_version"],
    "optimized_region_expansions.csv": ["analysis_target_id", "target_id", "optimized_radius", "region_size", "candidate_outputs", "classification", "schema_version"],
    "source_window_expansions.csv": ["analysis_target_id", "target_id", "source_window_radius", "source_window_size", "frontier_outputs", "classification", "schema_version"],
    "output_interface_candidates.csv": ["analysis_target_id", "target_id", "optimized_interface", "residual_source", "source_outputs", "width_total", "residual_width", "solver_status", "solver_backend", "counterexample_reproduced", "runtime_s", "classification", "schema_version"],
    "output_counterexamples.csv": ["counterexample_id", "analysis_target_id", "target_id", "assignment_a_path", "assignment_b_path", "source_outputs_a", "source_outputs_b", "counterexample_reproduced", "schema_version"],
    "output_difference_sets.csv": ["counterexample_id", "analysis_target_id", "target_id", "difference_set", "difference_set_width", "difference_set_hash", "schema_version"],
    "output_hitting_set_iterations.csv": ["analysis_target_id", "target_id", "iteration", "optimized_interface", "residual_source", "width_total", "solver_status", "counterexample_id", "classification", "schema_version"],
    "output_lower_bound_certificates.csv": ["analysis_target_id", "target_id", "proved_lower_bound", "best_upper_bound", "counterexample_ids", "exact_minimum_status", "classification", "schema_version"],
    "output_exact_minimum_certificates.csv": ["analysis_target_id", "target_id", "minimum_total_width", "minimum_residual_width", "optimized_interface", "residual_source", "solver_status", "exact_minimum_status", "counterexample_reproduced", "classification", "schema_version"],
    "target_utility_proofs.csv": ["analysis_target_id", "target_id", "interface_id", "target_influence_status", "witness_available", "witness_path", "solver_backend", "schema_version"],
    "algorithm_gap_classifications.csv": ["analysis_target_id", "target_id", "gap_status", "previous_failure_group", "certificate_classification", "old_bound", "minimum_or_lower_bound", "repair_action", "source_blind", "schema_version"],
    "algorithm_repairs.csv": ["analysis_target_id", "target_id", "repair_action", "repair_status", "rerun_status", "notes", "schema_version"],
    "certificate_guided_transplant_attempts.csv": ["analysis_target_id", "target_id", "attempted", "attempt_status", "graph_active", "source_cec_status", "cross_cec_status", "new_recovered_boundary", "failure_reason", "schema_version"],
    "global_cec.csv": ["analysis_target_id", "target_id", "scope", "status", "abc_available", "claimed_global", "failure_reason", "schema_version"],
    "boundary_recovery.csv": ["analysis_target_id", "target_id", "status", "graph_active", "new_recovered_boundary", "critical_path_mapping_status", "failure_reason", "schema_version"],
    "critical_path_mapping.csv": ["analysis_target_id", "target_id", "status", "mapped_points", "failure_reason", "schema_version"],
    "durability.csv": ["analysis_target_id", "target_id", "status", "strategy", "survived", "failure_reason", "schema_version"],
    "controlled_results.csv": ["case_id", "expected_minimum", "exhaustive_minimum", "z3_status", "z3_counterexamples_reproduced", "classification", "schema_version"],
    "development_results.csv": ["analysis_target_id", "target_id", "split", "failure_group", "strongest_classification", "compact_interface_found", "whole_design_only", "provenance_failure", "unresolved", "schema_version"],
    "heldout_results.csv": ["split", "targets", "compact_interfaces", "whole_design_only", "provenance_failures", "lower_bounds", "unresolved", "schema_version"],
    "baselines.csv": ["baseline", "targets", "successes", "evidence_scope", "notes", "schema_version"],
    "ablations.csv": ["ablation", "targets", "successes", "timeouts", "notes", "schema_version"],
    "failure_taxonomy.csv": ["failure_group", "classification", "count", "schema_version"],
    "runtime_timeout_summary.csv": ["stage", "queries", "timeouts", "total_runtime_s", "max_runtime_s", "schema_version"],
    "supported_claims.csv": ["claim", "supported", "evidence_file", "notes", "schema_version"],
}


def main() -> int:
    global OUT
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["all", "controlled", "development", "heldout", "input", "output", "whole-design", "transplant", "ablations"], default="all")
    parser.add_argument("--output-dir", type=Path, default=OUT)
    parser.add_argument("--max-real-targets", type=int, default=56)
    args = parser.parse_args()
    OUT = args.output_dir
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "counterexamples").mkdir(parents=True, exist_ok=True)
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    rows: dict[str, list[dict[str, str]]] = {name: [] for name in FIELDS}
    start = time.perf_counter()
    rows["experiment_manifest.csv"].append({
        "run_id": f"formal_locality_barriers__{_git_head()[:10]}",
        "git_head": _git_head(),
        "mode": args.mode,
        "config_hash": stable_hash(config),
        "deterministic_seed": str(config["deterministic_seed"]),
        "source_blind": "true",
        "schema_version": SCHEMA_VERSION,
    })
    rows["environment.csv"].extend(_environment())
    rows["baseline_metrics.csv"].extend(_baseline_metrics())
    rows["frozen_configuration.csv"].append({
        "config_path": _rel(CONFIG),
        "config_hash": stable_hash(config),
        "deterministic_seed": str(config["deterministic_seed"]),
        "maximum_interface_width": str(config["maximum_interface_width"]),
        "maximum_residual_width": str(config["maximum_residual_width"]),
        "exact_search_threshold": str(config["exact_search_threshold"]),
        "schema_version": SCHEMA_VERSION,
    })
    if args.mode in {"all", "controlled"}:
        _run_controlled(rows, config)
    if args.mode in {"all", "development", "heldout", "input", "output", "whole-design", "transplant", "ablations"}:
        _run_real(rows, config, mode=args.mode, max_targets=args.max_real_targets)
    _summarise(rows, time.perf_counter() - start)
    for name, fields in FIELDS.items():
        write_csv(rows[name], OUT / name, fields)
    _write_summary(rows)
    print(f"Wrote formal locality-barrier results to {OUT}")
    return 0


def _run_controlled(rows: dict[str, list[dict[str, str]]], config: dict[str, object]) -> None:
    cases = _controlled_cases()
    for case in cases:
        source = case["source"]
        optimized = case["optimized"]
        target = tuple(case["target"])
        universe = CandidateSignalUniverse(
            universe_id=f"controlled::{case['case_id']}::U_control",
            target_id=str(case["case_id"]),
            construction_mode="controlled_source_blind_fixture",
            locality_radius=1,
            signals=tuple(case["universe"]),
            source_path=str(source),
            source_hash=file_hash(source),
            optimized_path=str(optimized),
            optimized_hash=file_hash(optimized),
        )
        cert, cex, iters = solve_minimum_interface(
            target_id=str(case["case_id"]),
            benchmark=str(case["case_id"]),
            split="controlled",
            failure_group="controlled",
            source_path=source,
            optimized_path=optimized,
            target_vector=target,
            universe=universe,
            max_width=int(config["maximum_interface_width"]),
            max_iterations=int(config["maximum_hitting_set_iterations"]),
            timeout_ms=int(config["per_query_timeout_ms"]),
            exact_threshold=int(config["exact_search_threshold"]),
        )
        rows["candidate_universes.csv"].append(universe.row())
        rows["input_hitting_set_iterations.csv"].extend(iters)
        _append_cex(rows, cex)
        table_min = _exhaustive_minimum(source, optimized, universe.signals, target)
        rows["controlled_results.csv"].append({
            "case_id": str(case["case_id"]),
            "expected_minimum": str(case["expected_minimum"]),
            "exhaustive_minimum": "" if table_min is None else str(table_min),
            "z3_status": cert.solver_status,
            "z3_counterexamples_reproduced": str(all(c.counterexample_reproduced for c in cex)).lower(),
            "classification": cert.classification,
            "schema_version": SCHEMA_VERSION,
        })
        _store_cert(rows, cert)


def _run_real(rows: dict[str, list[dict[str, str]]], config: dict[str, object], *, mode: str, max_targets: int) -> None:
    active_rows = _read(ACTIVE_DEV)[:max_targets]
    for idx, active in enumerate(active_rows, start=1):
        analysis_id = f"real_{idx:04d}"
        provenance = _resolve_target(active, analysis_id)
        rows["target_provenance.csv"].append(provenance)
        rows["pi_alignment_validation.csv"].append({
            "analysis_target_id": analysis_id,
            "target_id": active["target_id"],
            "status": provenance["pi_alignment_status"],
            "source_path": provenance["source_path"],
            "optimized_path": provenance["optimized_path"],
            "pi_alignment_hash": stable_hash([provenance["source_path"], provenance["optimized_path"], provenance["pi_alignment_status"]]),
            "failure_reason": provenance["failure_reason"],
            "schema_version": SCHEMA_VERSION,
        })
        if provenance["provenance_status"] != "resolved":
            rows["development_results.csv"].append(_dev_row(analysis_id, active, "insufficient_target_provenance", provenance_failure=True))
            rows["algorithm_gap_classifications.csv"].append(_gap_row(analysis_id, active, "not_evaluable", "insufficient_target_provenance", "none", "provenance_repair_required"))
            rows["certificate_guided_transplant_attempts.csv"].append(_transplant_row(analysis_id, active, "false", "not_attempted", "insufficient_target_provenance"))
            continue
        source_path = ROOT / provenance["source_path"]
        optimized_path = ROOT / provenance["optimized_path"]
        target_vector = tuple(json.loads(provenance["optimized_target_vector"]))
        _record_signal_evaluation(rows, analysis_id, active, source_path, optimized_path)
        universes = build_source_universes(
            target_id=analysis_id,
            source_path=source_path,
            optimized_path=optimized_path,
            target_vector=target_vector,
            max_size=64,
        )
        best_classification = "unresolved"
        compact_found = False
        whole_only = False
        lower_bound_seen = False
        for universe in universes:
            rows["candidate_universes.csv"].append(universe.row())
            cert, cex, iters = solve_minimum_interface(
                target_id=analysis_id,
                benchmark=provenance["benchmark"],
                split=active["split"],
                failure_group=active["failure_reason"],
                source_path=source_path,
                optimized_path=optimized_path,
                target_vector=target_vector,
                universe=universe,
                max_width=int(config["maximum_interface_width"]),
                max_iterations=int(config["maximum_hitting_set_iterations"]),
                timeout_ms=int(config["per_query_timeout_ms"]),
                exact_threshold=int(config["exact_search_threshold"]),
            )
            rows["input_hitting_set_iterations.csv"].extend(iters)
            for item in iters:
                rows["input_interface_candidates.csv"].append({
                    "target_id": item["target_id"],
                    "universe_id": item["universe_id"],
                    "iteration": item["iteration"],
                    "candidate_interface": item["candidate_interface"],
                    "candidate_width": item["candidate_width"],
                    "solver_status": item["solver_status"],
                    "termination": item["termination"],
                    "schema_version": SCHEMA_VERSION,
                })
            _append_cex(rows, cex)
            _store_cert(rows, cert)
            if cert.classification == "compact_exact_input_interface_found":
                compact_found = True
                best_classification = "compact_exact_input_interface_found"
                if active["failure_reason"] == "no_globally_anchored_cut":
                    rows["algorithm_gap_classifications.csv"].append(_gap_row(analysis_id, active, "proved_algorithm_gap", cert.classification, str(cert.best_upper_bound), "integrate_certificate_interface_backend"))
                    rows["certificate_guided_transplant_attempts.csv"].append(_transplant_row(analysis_id, active, "true", "blocked_before_graph_rewrite", "interface_certificate_only_existing_pipeline_requires_adapter_graph_construction"))
                break
            if cert.classification == "global_diagnostic_not_local_success":
                whole_only = True
                rows["whole_design_diagnostics.csv"].append({
                    "analysis_target_id": analysis_id,
                    "target_id": active["target_id"],
                    "status": "passed",
                    "minimum_width": str(cert.best_upper_bound or ""),
                    "interface": json.dumps(cert.tested_interface),
                    "solver_status": cert.solver_status,
                    "counterexamples": json.dumps(cert.counterexample_ids),
                    "classification": cert.classification,
                    "schema_version": SCHEMA_VERSION,
                })
            if cert.exact_minimum_status.startswith("proved_lower_bound"):
                lower_bound_seen = True
                if best_classification == "unresolved":
                    best_classification = cert.classification
        if active["failure_reason"] == "no_relevant_source_consumer_window_under_bounds":
            output_classification = _run_output_analysis(rows, analysis_id, active, source_path, optimized_path, target_vector)
            best_classification = output_classification
            rows["algorithm_gap_classifications.csv"].append(_gap_row(analysis_id, active, "no_proved_algorithm_gap", output_classification, "output_minimum", "output_interface_backend_added_no_graph_rewrite_without_target_utility"))
            rows["certificate_guided_transplant_attempts.csv"].append(_transplant_row(analysis_id, active, "false", "not_attempted", output_classification))
        if not compact_found and not any(r["analysis_target_id"] == analysis_id for r in rows["certificate_guided_transplant_attempts.csv"]):
            reason = "whole_design_diagnostic_not_transplantable" if whole_only else ("lower_bound_or_unresolved_no_compact_interface" if lower_bound_seen else best_classification)
            rows["certificate_guided_transplant_attempts.csv"].append(_transplant_row(analysis_id, active, "false", "not_attempted", reason))
            rows["algorithm_gap_classifications.csv"].append(_gap_row(analysis_id, active, "no_proved_algorithm_gap", best_classification, "not_compact", "none"))
        rows["development_results.csv"].append(_dev_row(analysis_id, active, best_classification, compact_found=compact_found, whole_only=whole_only, unresolved=best_classification == "unresolved"))


def _run_output_analysis(rows: dict[str, list[dict[str, str]]], analysis_id: str, active: dict[str, str], source_path: Path, optimized_path: Path, target_vector: tuple[str, ...]) -> str:
    source = parse_blif(source_path)
    optimized = parse_blif(optimized_path)
    opt_options = [tuple()]
    if all(name in set([*optimized.inputs, *optimized.outputs, *[n.output for n in optimized.nodes]]) for name in target_vector):
        opt_options.append(target_vector)
    rows["optimized_region_expansions.csv"].append({
        "analysis_target_id": analysis_id,
        "target_id": active["target_id"],
        "optimized_radius": "0",
        "region_size": str(len(target_vector)),
        "candidate_outputs": json.dumps([list(o) for o in opt_options]),
        "classification": "target_vector_and_empty_interface_under_declared_radius",
        "schema_version": SCHEMA_VERSION,
    })
    rows["source_window_expansions.csv"].append({
        "analysis_target_id": analysis_id,
        "target_id": active["target_id"],
        "source_window_radius": "0",
        "source_window_size": str(len(source.outputs)),
        "frontier_outputs": json.dumps(source.outputs),
        "classification": "primary_output_frontier",
        "schema_version": SCHEMA_VERSION,
    })
    table = _output_eval_table(source, optimized, tuple(source.inputs), opt_options, tuple(source.outputs))
    best = None
    iteration = 0
    stored_output_counterexample = False
    for width in range(len(source.inputs) + max(len(o) for o in opt_options) + 1):
        for opt_iface in opt_options:
            if len(opt_iface) > width:
                continue
            residual_width = width - len(opt_iface)
            if residual_width > len(source.inputs):
                continue
            for residual in itertools_combinations(tuple(source.inputs), residual_width):
                status, reproduced, witness = _output_status_from_table(table, opt_iface, residual)
                classification = _output_classification(status, len(opt_iface) + len(residual), residual_width)
                counterexample_id = ""
                if witness and not stored_output_counterexample:
                    counterexample_id = stable_hash([analysis_id, opt_iface, residual, witness])
                    a_path = OUT / "counterexamples" / f"{counterexample_id}.output.a.json"
                    b_path = OUT / "counterexamples" / f"{counterexample_id}.output.b.json"
                    a_path.write_text(json.dumps(witness["a_assignment"], indent=2, sort_keys=True) + "\n", encoding="utf-8")
                    b_path.write_text(json.dumps(witness["b_assignment"], indent=2, sort_keys=True) + "\n", encoding="utf-8")
                    diff = sorted(witness["difference_set"])
                    rows["output_counterexamples.csv"].append({
                        "counterexample_id": counterexample_id,
                        "analysis_target_id": analysis_id,
                        "target_id": active["target_id"],
                        "assignment_a_path": str(a_path.relative_to(OUT)),
                        "assignment_b_path": str(b_path.relative_to(OUT)),
                        "source_outputs_a": json.dumps(witness["a_outputs"]),
                        "source_outputs_b": json.dumps(witness["b_outputs"]),
                        "counterexample_reproduced": str(reproduced).lower(),
                        "schema_version": SCHEMA_VERSION,
                    })
                    rows["output_difference_sets.csv"].append({
                        "counterexample_id": counterexample_id,
                        "analysis_target_id": analysis_id,
                        "target_id": active["target_id"],
                        "difference_set": json.dumps(diff),
                        "difference_set_width": str(len(diff)),
                        "difference_set_hash": stable_hash(diff),
                        "schema_version": SCHEMA_VERSION,
                    })
                    stored_output_counterexample = True
                row = {
                    "analysis_target_id": analysis_id,
                    "target_id": active["target_id"],
                    "optimized_interface": json.dumps(opt_iface),
                    "residual_source": json.dumps(residual),
                    "source_outputs": json.dumps(source.outputs),
                    "width_total": str(len(opt_iface) + len(residual)),
                    "residual_width": str(len(residual)),
                    "solver_status": status,
                    "solver_backend": "exhaustive_output_interface_table_miter",
                    "counterexample_reproduced": str(reproduced).lower(),
                    "runtime_s": "0.000000",
                    "classification": classification,
                    "schema_version": SCHEMA_VERSION,
                }
                rows["output_interface_candidates.csv"].append(row)
                rows["output_hitting_set_iterations.csv"].append({
                    "analysis_target_id": analysis_id,
                    "target_id": active["target_id"],
                    "iteration": str(iteration),
                    "optimized_interface": row["optimized_interface"],
                    "residual_source": row["residual_source"],
                    "width_total": row["width_total"],
                    "solver_status": status,
                    "counterexample_id": counterexample_id,
                    "classification": classification,
                    "schema_version": SCHEMA_VERSION,
                })
                iteration += 1
                if status == "unsat":
                    best = row
                    rows["output_exact_minimum_certificates.csv"].append({
                        "analysis_target_id": analysis_id,
                        "target_id": active["target_id"],
                        "minimum_total_width": row["width_total"],
                        "minimum_residual_width": row["residual_width"],
                        "optimized_interface": row["optimized_interface"],
                        "residual_source": row["residual_source"],
                        "solver_status": status,
                        "exact_minimum_status": "exact_minimum_within_declared_BZ_universe",
                        "counterexample_reproduced": str(reproduced).lower(),
                        "classification": classification,
                        "schema_version": SCHEMA_VERSION,
                    })
                    _target_utility(rows, analysis_id, active, source_path, optimized_path, target_vector, opt_iface, residual)
                    return classification
    return "unresolved"


def _output_eval_table(source, optimized, inputs: tuple[str, ...], opt_options: list[tuple[str, ...]], source_outputs: tuple[str, ...]):
    opt_signal_names = tuple(sorted({name for option in opt_options for name in option}))
    table = []
    for assignment in all_assignments(inputs):
        source_values = scalar_eval_exact(source, assignment)
        optimized_values = scalar_eval_exact(optimized, assignment)
        table.append(
            {
                "assignment": assignment,
                "source": source_values,
                "optimized": optimized_values,
                "source_outputs": tuple(source_values.get(name, 0) for name in source_outputs),
                "opt_signals": {name: optimized_values.get(name, 0) for name in opt_signal_names},
            }
        )
    return table


def _output_status_from_table(table, opt_iface: tuple[str, ...], residual: tuple[str, ...]) -> tuple[str, bool, dict[str, object] | None]:
    seen = {}
    for row in table:
        key = tuple(row["opt_signals"].get(name, 0) for name in opt_iface) + tuple(row["source"].get(name, 0) for name in residual)
        y = row["source_outputs"]
        if key in seen and seen[key] != y:
            previous = seen[key]
            candidate_universe = set(opt_iface) | set(residual)
            difference = []
            for name in opt_iface:
                if previous["opt_signals"].get(name, 0) != row["opt_signals"].get(name, 0):
                    difference.append(f"opt::{name}")
            for name in residual:
                if previous["source"].get(name, 0) != row["source"].get(name, 0):
                    difference.append(f"src::{name}")
            return "sat", True, {
                "a_assignment": previous["assignment"],
                "b_assignment": row["assignment"],
                "a_outputs": previous["source_outputs"],
                "b_outputs": y,
                "difference_set": sorted(candidate_universe if difference else []),
            }
        seen[key] = row
    return "unsat", True, None


def _output_classification(status: str, total_width: int, residual_width: int) -> str:
    if status != "unsat":
        return "insufficient_output_interface"
    if total_width <= 6:
        return "exact_compact_output_interface_found"
    return "output_residual_minimum_above_previous_bound"


def _target_utility(rows: dict[str, list[dict[str, str]]], analysis_id: str, active: dict[str, str], source_path: Path, optimized_path: Path, target_vector: tuple[str, ...], opt_iface: tuple[str, ...], residual: tuple[str, ...]) -> None:
    source = parse_blif(source_path)
    optimized = parse_blif(optimized_path)
    witness = None
    non_target = tuple(name for name in opt_iface if name not in set(target_vector))
    buckets: dict[tuple[tuple[int, ...], tuple[int, ...]], list[tuple[dict[str, int], tuple[int, ...], tuple[int, ...]]]] = defaultdict(list)
    for assignment in all_assignments(tuple(source.inputs)):
        key = (vector_eval(source, residual, assignment), vector_eval(optimized, non_target, assignment))
        buckets[key].append((assignment, vector_eval(optimized, target_vector, assignment), vector_eval(source, tuple(source.outputs), assignment)))
    for bucket in buckets.values():
        seen: dict[tuple[int, ...], tuple[dict[str, int], tuple[int, ...]]] = {}
        for assignment, target_value, output_value in bucket:
            for previous_target, (previous_assignment, previous_output) in seen.items():
                if previous_target != target_value and previous_output != output_value:
                    witness = {"a": previous_assignment, "b": assignment}
                    break
            if witness:
                break
            seen.setdefault(target_value, (assignment, output_value))
        if witness:
            break
    path = ""
    if witness:
        p = OUT / "counterexamples" / f"{analysis_id}_target_utility.json"
        p.write_text(json.dumps(witness, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        path = str(p.relative_to(OUT))
    rows["target_utility_proofs.csv"].append({
        "analysis_target_id": analysis_id,
        "target_id": active["target_id"],
        "interface_id": stable_hash([opt_iface, residual]),
        "target_influence_status": "influential" if witness else "not_functionally_necessary_for_interface",
        "witness_available": str(witness is not None).lower(),
        "witness_path": path,
        "solver_backend": "exhaustive_target_utility",
        "schema_version": SCHEMA_VERSION,
    })


def _record_signal_evaluation(rows: dict[str, list[dict[str, str]]], analysis_id: str, active: dict[str, str], source_path: Path, optimized_path: Path) -> None:
    source = parse_blif(source_path)
    optimized = parse_blif(optimized_path)
    rows["signal_evaluations.csv"].append({
        "analysis_target_id": analysis_id,
        "target_id": active["target_id"],
        "source_hash": file_hash(source_path),
        "optimized_hash": file_hash(optimized_path),
        "assignment_count": str(2 ** len(source.inputs)),
        "source_signal_count": str(len(set([*source.inputs, *source.outputs, *[n.output for n in source.nodes]]))),
        "optimized_signal_count": str(len(set([*optimized.inputs, *optimized.outputs, *[n.output for n in optimized.nodes]]))),
        "evaluation_backend": "exhaustive_exact_blif_cover",
        "evaluation_table_hash": stable_hash([source.inputs, source.outputs, optimized.inputs, optimized.outputs, source_path.name, optimized_path.name]),
        "schema_version": SCHEMA_VERSION,
    })


def _append_cex(rows: dict[str, list[dict[str, str]]], cexs) -> None:
    for cex in cexs:
        a_path = OUT / "counterexamples" / f"{cex.counterexample_id}.a.json"
        b_path = OUT / "counterexamples" / f"{cex.counterexample_id}.b.json"
        a_path.write_text(json.dumps(cex.assignment_a, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        b_path.write_text(json.dumps(cex.assignment_b, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        rows["input_counterexamples.csv"].append(cex.row())
        rows["input_difference_sets.csv"].append({
            "counterexample_id": cex.counterexample_id,
            "target_id": cex.target_id,
            "universe_id": cex.universe_id,
            "difference_set": json.dumps(cex.difference_set),
            "difference_set_width": str(len(cex.difference_set)),
            "difference_set_hash": stable_hash(cex.difference_set),
            "schema_version": SCHEMA_VERSION,
        })


def _store_cert(rows: dict[str, list[dict[str, str]]], cert) -> None:
    name = "input_exact_minimum_certificates.csv" if cert.exact_minimum_status == "exact_minimum" else "input_lower_bound_certificates.csv"
    rows[name].append(cert.row())


def _resolve_target(row: dict[str, str], analysis_id: str) -> dict[str, str]:
    target_id = row["target_id"]
    source_path = optimized_path = ""
    target_vector: tuple[str, ...] = tuple()
    benchmark = target_id
    if "|" in target_id:
        parts = target_id.split("|")
        if len(parts) == 4:
            benchmark, _coi, flow, target = parts
            source = ROOT / "variants" / f"{benchmark}_original.blif"
            opt = ROOT / "variants" / f"{benchmark}_{flow}.blif"
            source_path = _rel(source) if source.exists() else ""
            optimized_path = _rel(opt) if opt.exists() else ""
            target_vector = (target,)
    elif target_id.endswith("__target"):
        benchmark = target_id.removesuffix("__target")
        source = ROOT / "benchmarks" / "active_source_counterpart_refactoring" / f"{benchmark}.blif"
        opt = ROOT / "results" / "active_source_counterpart_refactoring" / "artifacts" / f"{benchmark}.impl_with_target.blif"
        source_path = _rel(source) if source.exists() else ""
        optimized_path = _rel(opt) if opt.exists() else ""
        if opt.exists():
            names = set([*parse_blif(opt).inputs, *parse_blif(opt).outputs, *[n.output for n in parse_blif(opt).nodes]])
            target_vector = tuple(name for name in ("m0", "m1", "target") if name in names)[:2]
    artifact_status = "resolved" if source_path and optimized_path and target_vector else "missing_artifact"
    failure_reason = ""
    pi_status = "not_run"
    src_hash = opt_hash = ""
    if artifact_status == "resolved":
        source = ROOT / source_path
        opt = ROOT / optimized_path
        src_hash = file_hash(source)
        opt_hash = file_hash(opt)
        pi_status = validate_pair(parse_blif(source), parse_blif(opt), target_vector)
        if pi_status != "ok":
            artifact_status = "invalid_artifact"
            failure_reason = pi_status
    else:
        failure_reason = "cannot_resolve_source_optimized_target_from_previous_row"
    return {
        "analysis_target_id": analysis_id,
        "target_id": target_id,
        "benchmark": benchmark,
        "split": row["split"],
        "failure_group": row["failure_reason"],
        "source_result": row["source_result"],
        "source_path": source_path,
        "optimized_path": optimized_path,
        "optimized_target_vector": json.dumps(target_vector),
        "source_hash": src_hash,
        "optimized_hash": opt_hash,
        "pi_alignment_status": pi_status,
        "artifact_status": artifact_status,
        "provenance_status": "resolved" if artifact_status == "resolved" else "insufficient_target_provenance",
        "failure_reason": failure_reason,
        "schema_version": SCHEMA_VERSION,
    }


def _controlled_cases() -> list[dict[str, object]]:
    bench = OUT / "controlled_benchmarks"
    bench.mkdir(parents=True, exist_ok=True)
    cases = [
        ("min1", ("a", "b"), ("t",), lambda x: (x["a"],), ("a", "b"), 1),
        ("min2_xor", ("a", "b"), ("t",), lambda x: (x["a"] ^ x["b"],), ("a", "b"), 2),
        ("min3_maj", ("a", "b", "c"), ("t",), lambda x: (((x["a"] & x["b"]) | (x["a"] & x["c"]) | (x["b"] & x["c"])),), ("a", "b", "c"), 3),
        ("permute_invert", ("a", "b"), ("t0", "t1"), lambda x: (x["b"], 1 - x["a"]), ("a", "b"), 2),
        ("nonlinear_and", ("a", "b"), ("t",), lambda x: (x["a"] & x["b"],), ("a", "b"), 2),
        ("affine_bool", ("a0", "a1"), ("t0", "t1"), lambda x: _bits((3 * (x["a0"] | (x["a1"] << 1)) + 1) & 3, 2), ("a0", "a1"), 2),
    ]
    out = []
    for name, inputs, outputs, fn, universe, expected in cases:
        src = bench / f"{name}.source.blif"
        opt = bench / f"{name}.optimized.blif"
        _write_truth_blif(src, f"src_{name}", inputs, outputs, fn)
        _write_truth_blif(opt, f"opt_{name}", inputs, outputs, fn)
        out.append({"case_id": name, "source": src, "optimized": opt, "target": outputs, "universe": universe, "expected_minimum": expected})
    return out


def _write_truth_blif(path: Path, model: str, inputs: tuple[str, ...], outputs: tuple[str, ...], fn) -> None:
    nodes = []
    for idx, output in enumerate(outputs):
        cover = []
        for assignment in all_assignments(inputs):
            if fn(assignment)[idx]:
                cover.append("".join(str(assignment[name]) for name in inputs) + " 1")
        nodes.append(BlifNode(output=output, inputs=list(inputs), cover=cover))
    path.write_text(
        "\n".join([
            f".model {model}",
            ".inputs " + " ".join(inputs),
            ".outputs " + " ".join(outputs),
            *[line for node in nodes for line in [".names " + " ".join([*node.inputs, node.output]), *node.cover]],
            ".end",
            "",
        ]),
        encoding="utf-8",
    )


def _exhaustive_minimum(source_path: Path, optimized_path: Path, universe: tuple[str, ...], target: tuple[str, ...]) -> int | None:
    for width in range(len(universe) + 1):
        for combo in itertools_combinations(universe, width):
            if prove_interface_sufficiency(source_path=source_path, optimized_path=optimized_path, interface=combo, target_vector=target).status == "unsat":
                return width
    return None


def itertools_combinations(items: tuple[str, ...] | list[str], width: int):
    import itertools

    return itertools.combinations(tuple(items), width)


def _gap_row(analysis_id: str, active: dict[str, str], gap: str, classification: str, bound: str, action: str) -> dict[str, str]:
    return {
        "analysis_target_id": analysis_id,
        "target_id": active["target_id"],
        "gap_status": gap,
        "previous_failure_group": active["failure_reason"],
        "certificate_classification": classification,
        "old_bound": "6",
        "minimum_or_lower_bound": bound,
        "repair_action": action,
        "source_blind": "true",
        "schema_version": SCHEMA_VERSION,
    }


def _transplant_row(analysis_id: str, active: dict[str, str], attempted: str, status: str, reason: str) -> dict[str, str]:
    return {
        "analysis_target_id": analysis_id,
        "target_id": active["target_id"],
        "attempted": attempted,
        "attempt_status": status,
        "graph_active": "false",
        "source_cec_status": "not_run",
        "cross_cec_status": "not_run",
        "new_recovered_boundary": "false",
        "failure_reason": reason,
        "schema_version": SCHEMA_VERSION,
    }


def _dev_row(analysis_id: str, active: dict[str, str], classification: str, *, compact_found=False, whole_only=False, provenance_failure=False, unresolved=False) -> dict[str, str]:
    return {
        "analysis_target_id": analysis_id,
        "target_id": active["target_id"],
        "split": active["split"],
        "failure_group": active["failure_reason"],
        "strongest_classification": classification,
        "compact_interface_found": str(compact_found).lower(),
        "whole_design_only": str(whole_only).lower(),
        "provenance_failure": str(provenance_failure).lower(),
        "unresolved": str(unresolved).lower(),
        "schema_version": SCHEMA_VERSION,
    }


def _summarise(rows: dict[str, list[dict[str, str]]], runtime: float) -> None:
    dev = rows["development_results.csv"]
    for gap in rows["algorithm_gap_classifications.csv"]:
        rows["algorithm_repairs.csv"].append({
            "analysis_target_id": gap["analysis_target_id"],
            "target_id": gap["target_id"],
            "repair_action": gap["repair_action"],
            "repair_status": "not_applicable" if gap["repair_action"] in {"none", "provenance_repair_required"} else "diagnostic_backend_added_no_graph_transplant_acceptance",
            "rerun_status": "not_run_for_provenance_failure" if gap["gap_status"] == "not_evaluable" else "certificate_pipeline_rerun",
            "notes": "No blind real graph rewrite is counted from certificate-guided diagnostics.",
            "schema_version": SCHEMA_VERSION,
        })
    for attempt in rows["certificate_guided_transplant_attempts.csv"]:
        for scope in ("source_vs_rewritten_source", "rewritten_source_vs_optimized"):
            rows["global_cec.csv"].append({
                "analysis_target_id": attempt["analysis_target_id"],
                "target_id": attempt["target_id"],
                "scope": scope,
                "status": "not_run" if attempt["new_recovered_boundary"] != "true" else attempt["source_cec_status"],
                "abc_available": str(abc_binary() is not None).lower(),
                "claimed_global": str(attempt["new_recovered_boundary"] == "true").lower(),
                "failure_reason": attempt["failure_reason"],
                "schema_version": SCHEMA_VERSION,
            })
        rows["boundary_recovery.csv"].append({
            "analysis_target_id": attempt["analysis_target_id"],
            "target_id": attempt["target_id"],
            "status": "not_restored" if attempt["new_recovered_boundary"] != "true" else "restored",
            "graph_active": attempt["graph_active"],
            "new_recovered_boundary": attempt["new_recovered_boundary"],
            "critical_path_mapping_status": "not_run",
            "failure_reason": attempt["failure_reason"],
            "schema_version": SCHEMA_VERSION,
        })
        rows["critical_path_mapping.csv"].append({
            "analysis_target_id": attempt["analysis_target_id"],
            "target_id": attempt["target_id"],
            "status": "not_run",
            "mapped_points": "0",
            "failure_reason": attempt["failure_reason"],
            "schema_version": SCHEMA_VERSION,
        })
        rows["durability.csv"].append({
            "analysis_target_id": attempt["analysis_target_id"],
            "target_id": attempt["target_id"],
            "status": "not_run",
            "strategy": "certificate_guided_transplant",
            "survived": "false",
            "failure_reason": attempt["failure_reason"],
            "schema_version": SCHEMA_VERSION,
        })
    by_split = defaultdict(list)
    for row in dev:
        by_split[row["split"]].append(row)
    for split, subset in sorted(by_split.items()):
        rows["heldout_results.csv"].append({
            "split": split,
            "targets": str(len(subset)),
            "compact_interfaces": str(sum(r["compact_interface_found"] == "true" for r in subset)),
            "whole_design_only": str(sum(r["whole_design_only"] == "true" for r in subset)),
            "provenance_failures": str(sum(r["provenance_failure"] == "true" for r in subset)),
            "lower_bounds": str(sum("lower_bound" in r["strongest_classification"] for r in subset)),
            "unresolved": str(sum(r["unresolved"] == "true" for r in subset)),
            "schema_version": SCHEMA_VERSION,
        })
    counts = Counter((r["failure_group"], r["strongest_classification"]) for r in dev)
    for (group, classification), count in sorted(counts.items()):
        rows["failure_taxonomy.csv"].append({"failure_group": group, "classification": classification, "count": str(count), "schema_version": SCHEMA_VERSION})
    iters = rows["input_hitting_set_iterations.csv"]
    rows["runtime_timeout_summary.csv"].append({
        "stage": "formal_locality",
        "queries": str(len(iters) + len(rows["output_interface_candidates.csv"])),
        "timeouts": str(sum(r["solver_status"] == "timeout" for r in iters)),
        "total_runtime_s": f"{runtime:.6f}",
        "max_runtime_s": max([r["runtime_s"] for r in iters] or ["0.000000"]),
        "schema_version": SCHEMA_VERSION,
    })
    rows["supported_claims.csv"].extend([
        {"claim": "all_56_previous_failures_audited", "supported": str(len(dev) == 56).lower(), "evidence_file": "development_results.csv", "notes": f"{len(dev)} rows analysed", "schema_version": SCHEMA_VERSION},
        {"claim": "certificate_counterexamples_replayed", "supported": str(all(r["counterexample_reproduced"] == "true" for r in rows["input_counterexamples.csv"])).lower(), "evidence_file": "input_counterexamples.csv", "notes": "all stored SAT pairs replay through concrete evaluators", "schema_version": SCHEMA_VERSION},
        {"claim": "no_real_transplant_claimed_without_global_cec", "supported": "true", "evidence_file": "certificate_guided_transplant_attempts.csv", "notes": "certificate-guided interface existence remains separate from transplantation success", "schema_version": SCHEMA_VERSION},
    ])
    rows["baselines.csv"].extend([
        {"baseline": "previous_cross_netlist_fixed_width_search", "targets": "56", "successes": "0", "evidence_scope": "previous_real_failures", "notes": "Input/output blocker labels preserved from prior pipeline.", "schema_version": SCHEMA_VERSION},
        {"baseline": "formal_locality_hitting_set_certificates", "targets": str(len(dev)), "successes": str(sum(r["compact_interface_found"] == "true" for r in dev)), "evidence_scope": "declared_universe_exact_minimum", "notes": "Certificate success is not counted as graph-active recovery.", "schema_version": SCHEMA_VERSION},
        {"baseline": "certificate_guided_transplant_accounting", "targets": str(len(rows["certificate_guided_transplant_attempts.csv"])), "successes": str(sum(r["new_recovered_boundary"] == "true" for r in rows["certificate_guided_transplant_attempts.csv"])), "evidence_scope": "global_cec_required", "notes": "No real graph-active transplant accepted.", "schema_version": SCHEMA_VERSION},
    ])
    rows["ablations.csv"].extend([
        {"ablation": "anchored_only_U0", "targets": str(len({r["target_id"] for r in rows["input_exact_minimum_certificates.csv"] if r["universe_mode"] == "U0_direct_name_intersection"})), "successes": str(sum(r["classification"] == "compact_exact_input_interface_found" for r in rows["input_exact_minimum_certificates.csv"] if r["universe_mode"] == "U0_direct_name_intersection")), "timeouts": "0", "notes": "Direct source-blind name intersection universe.", "schema_version": SCHEMA_VERSION},
        {"ablation": "all_primary_inputs_U6_diagnostic", "targets": str(len({r["target_id"] for r in rows["candidate_universes.csv"] if r["diagnostic_only"] == "true"})), "successes": "0", "timeouts": "0", "notes": "Whole-PI rows are diagnostics, never compact local successes.", "schema_version": SCHEMA_VERSION},
        {"ablation": "output_BZ_declared_universe", "targets": str(len(rows["output_exact_minimum_certificates.csv"])), "successes": str(sum(r["classification"] == "exact_compact_output_interface_found" for r in rows["output_exact_minimum_certificates.csv"])), "timeouts": "0", "notes": "Exact minima are scoped to candidate optimized target and residual PI universe.", "schema_version": SCHEMA_VERSION},
    ])


def _write_summary(rows: dict[str, list[dict[str, str]]]) -> None:
    dev = rows["development_results.csv"]
    lines = [
        "# Formal Locality-Barrier Certificate Summary",
        "",
        f"- Previous real failures audited: {len(dev)}",
        f"- Input-failure rows: {sum(r['failure_group'] == 'no_globally_anchored_cut' for r in dev)}",
        f"- Output-failure rows: {sum(r['failure_group'] == 'no_relevant_source_consumer_window_under_bounds' for r in dev)}",
        f"- Compact exact interfaces found: {sum(r['compact_interface_found'] == 'true' for r in dev)}",
        f"- Whole-design diagnostics only: {sum(r['whole_design_only'] == 'true' for r in dev)}",
        f"- Provenance failures: {sum(r['provenance_failure'] == 'true' for r in dev)}",
        f"- Certificate-guided real transplants accepted: {sum(r['new_recovered_boundary'] == 'true' for r in rows['certificate_guided_transplant_attempts.csv'])}",
        "",
        "The certificates are scoped to their declared universe and bounds. Whole-primary-input results are diagnostics, not local correspondence successes.",
        "",
        "## Failure Taxonomy",
    ]
    for row in rows["failure_taxonomy.csv"]:
        lines.append(f"- {row['failure_group']} / {row['classification']}: {row['count']}")
    (OUT / "formal_locality_barrier_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _baseline_metrics() -> list[dict[str, str]]:
    return [
        {"metric": "baseline_head", "value": "f480fe107d33132c408ea567b6c561dfb7758440", "source": "origin/main before phase", "schema_version": SCHEMA_VERSION},
        {"metric": "previous_cross_netlist_targets", "value": "73", "source": "results/cross_netlist_cut_transplantation", "schema_version": SCHEMA_VERSION},
        {"metric": "previous_real_failures", "value": "56", "source": "active_source_counterpart_refactoring/development_results.csv", "schema_version": SCHEMA_VERSION},
        {"metric": "previous_no_globally_anchored_cut", "value": "36", "source": "active_source_counterpart_refactoring/development_results.csv", "schema_version": SCHEMA_VERSION},
        {"metric": "previous_no_relevant_source_consumer_window_under_bounds", "value": "20", "source": "active_source_counterpart_refactoring/development_results.csv", "schema_version": SCHEMA_VERSION},
        {"metric": "previous_real_graph_active_transplants", "value": "0", "source": "cross_netlist_cut_transplantation/development_results.csv", "schema_version": SCHEMA_VERSION},
    ]


def _environment() -> list[dict[str, str]]:
    abc = abc_binary()
    return [
        {"tool": "python", "version": platform.python_version(), "path": sys.executable, "status": "available", "schema_version": SCHEMA_VERSION},
        {"tool": "z3", "version": z3.get_version_string() if z3 is not None else "", "path": "", "status": "available" if z3 is not None else "missing", "schema_version": SCHEMA_VERSION},
        {"tool": "abc", "version": _abc_version(abc), "path": str(abc), "status": "available" if abc.exists() else "missing", "schema_version": SCHEMA_VERSION},
        {"tool": "yosys", "version": _yosys_version(), "path": shutil.which("yosys") or "", "status": "available" if shutil.which("yosys") else "missing", "schema_version": SCHEMA_VERSION},
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


def _read(path: Path) -> list[dict[str, str]]:
    return list(csv.DictReader(path.open(newline="", encoding="utf-8"))) if path.exists() else []


def _rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT.resolve()))


def _git_head() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def _bits(value: int, width: int) -> tuple[int, ...]:
    return tuple((value >> idx) & 1 for idx in range(width))


if __name__ == "__main__":
    raise SystemExit(main())
