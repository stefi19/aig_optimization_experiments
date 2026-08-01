#!/usr/bin/env python3
"""Validate formal locality-barrier certificate artifacts."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from formal_locality_barriers import prove_interface_sufficiency  # noqa: E402


DEFAULT_OUT = ROOT / "results" / "formal_locality_barriers"

REQUIRED = {
    "experiment_manifest.csv": {"git_head", "config_hash", "source_blind"},
    "environment.csv": {"tool", "version", "status"},
    "baseline_metrics.csv": {"metric", "value"},
    "frozen_configuration.csv": {"config_path", "config_hash", "deterministic_seed", "maximum_interface_width"},
    "target_provenance.csv": {"analysis_target_id", "target_id", "source_path", "optimized_path", "optimized_target_vector", "provenance_status"},
    "pi_alignment_validation.csv": {"analysis_target_id", "target_id", "status", "pi_alignment_hash"},
    "candidate_universes.csv": {"universe_id", "target_id", "universe_hash", "signals", "source_hash", "optimized_hash", "diagnostic_only"},
    "signal_evaluations.csv": {"analysis_target_id", "target_id", "assignment_count", "evaluation_backend", "evaluation_table_hash"},
    "input_interface_candidates.csv": {"target_id", "universe_id", "iteration", "candidate_interface", "solver_status"},
    "input_hitting_set_iterations.csv": {"target_id", "universe_id", "candidate_interface", "lower_bound", "solver_status", "counterexamples_after"},
    "input_counterexamples.csv": {"counterexample_id", "target_id", "universe_id", "assignment_a_path", "assignment_b_path", "difference_set", "counterexample_reproduced"},
    "input_difference_sets.csv": {"counterexample_id", "difference_set", "difference_set_width", "difference_set_hash"},
    "input_exact_minimum_certificates.csv": {"certificate_id", "target_id", "source_path", "optimized_path", "target_vector", "tested_interface", "proved_lower_bound", "best_upper_bound", "exact_minimum_status", "solver_status", "classification", "diagnostic_only", "source_blind"},
    "input_lower_bound_certificates.csv": {"certificate_id", "target_id", "counterexample_ids", "proved_lower_bound", "exact_minimum_status", "solver_status", "classification", "timeout"},
    "whole_design_diagnostics.csv": {"analysis_target_id", "status", "classification"},
    "optimized_region_expansions.csv": {"analysis_target_id", "target_id", "optimized_radius", "region_size", "candidate_outputs"},
    "source_window_expansions.csv": {"analysis_target_id", "target_id", "source_window_radius", "source_window_size", "frontier_outputs"},
    "output_interface_candidates.csv": {"analysis_target_id", "solver_status", "counterexample_reproduced", "classification"},
    "output_counterexamples.csv": {"counterexample_id", "analysis_target_id", "assignment_a_path", "assignment_b_path", "counterexample_reproduced"},
    "output_difference_sets.csv": {"counterexample_id", "analysis_target_id", "difference_set", "difference_set_width"},
    "output_hitting_set_iterations.csv": {"analysis_target_id", "target_id", "iteration", "solver_status", "classification"},
    "output_lower_bound_certificates.csv": {"analysis_target_id", "target_id", "proved_lower_bound", "best_upper_bound", "classification"},
    "output_exact_minimum_certificates.csv": {"analysis_target_id", "solver_status", "exact_minimum_status", "classification"},
    "target_utility_proofs.csv": {"analysis_target_id", "target_influence_status", "witness_available", "solver_backend"},
    "algorithm_gap_classifications.csv": {"analysis_target_id", "gap_status", "certificate_classification", "source_blind"},
    "algorithm_repairs.csv": {"analysis_target_id", "target_id", "repair_action", "repair_status", "rerun_status"},
    "certificate_guided_transplant_attempts.csv": {"analysis_target_id", "attempted", "graph_active", "source_cec_status", "cross_cec_status", "new_recovered_boundary"},
    "global_cec.csv": {"analysis_target_id", "target_id", "scope", "status", "claimed_global"},
    "boundary_recovery.csv": {"analysis_target_id", "target_id", "status", "graph_active", "new_recovered_boundary"},
    "critical_path_mapping.csv": {"analysis_target_id", "target_id", "status", "mapped_points"},
    "durability.csv": {"analysis_target_id", "target_id", "status", "strategy", "survived"},
    "controlled_results.csv": {"case_id", "expected_minimum", "exhaustive_minimum", "z3_status", "z3_counterexamples_reproduced"},
    "development_results.csv": {"analysis_target_id", "target_id", "failure_group", "strongest_classification", "compact_interface_found", "provenance_failure"},
    "heldout_results.csv": {"split", "targets", "compact_interfaces", "provenance_failures"},
    "baselines.csv": {"baseline", "targets", "successes", "evidence_scope"},
    "ablations.csv": {"ablation", "targets", "successes", "timeouts"},
    "failure_taxonomy.csv": {"failure_group", "classification", "count"},
    "runtime_timeout_summary.csv": {"stage", "queries", "timeouts"},
    "supported_claims.csv": {"claim", "supported", "evidence_file"},
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
        with path.open(newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            fieldnames = reader.fieldnames or []
            rows = list(reader)
        tables[name] = rows
        missing = required - set(fieldnames)
        if missing:
            errors.append(f"{name} missing columns: {sorted(missing)}")
    if errors:
        return _fail(errors)

    abc_available = any(r["tool"] == "abc" and r["status"] == "available" for r in tables["environment.csv"])
    universe_by_id = {r["universe_id"]: r for r in tables["candidate_universes.csv"]}
    cex_by_id = {r["counterexample_id"]: r for r in tables["input_counterexamples.csv"]}
    diff_by_id = {r["counterexample_id"]: r for r in tables["input_difference_sets.csv"]}

    dev = tables["development_results.csv"]
    full_real_run = bool(dev)
    if full_real_run and len(dev) != 56:
        errors.append(f"expected 56 previous real failures, saw {len(dev)}")
    input_count = sum(r["failure_group"] == "no_globally_anchored_cut" for r in dev)
    output_count = sum(r["failure_group"] == "no_relevant_source_consumer_window_under_bounds" for r in dev)
    if full_real_run and input_count != 36:
        errors.append(f"expected 36 input-interface failures, saw {input_count}")
    if full_real_run and output_count != 20:
        errors.append(f"expected 20 output-interface failures, saw {output_count}")

    for row in tables["candidate_universes.csv"]:
        if not row["universe_hash"]:
            errors.append(f"missing universe hash: {row['universe_id']}")
        try:
            json.loads(row["signals"])
        except json.JSONDecodeError:
            errors.append(f"universe signals are not JSON: {row['universe_id']}")

    for row in tables["input_counterexamples.csv"]:
        if row["counterexample_reproduced"] != "true":
            errors.append(f"counterexample not concretely reproduced: {row['counterexample_id']}")
        if row["counterexample_id"] not in diff_by_id:
            errors.append(f"missing difference-set row: {row['counterexample_id']}")
        for side in ("assignment_a_path", "assignment_b_path"):
            if not (args.output_dir / row[side]).exists():
                errors.append(f"missing counterexample assignment file: {row[side]}")

    for row in tables["input_difference_sets.csv"]:
        diff = json.loads(row["difference_set"])
        if int(row["difference_set_width"]) != len(diff):
            errors.append(f"difference-set width mismatch: {row['counterexample_id']}")
        if not diff:
            matching = cex_by_id.get(row["counterexample_id"], {})
            if matching and matching["counterexample_reproduced"] != "true":
                errors.append(f"empty difference set without replayable target pair: {row['counterexample_id']}")

    for row in tables["input_exact_minimum_certificates.csv"]:
        if row["source_blind"] != "true":
            errors.append(f"exact certificate is not source blind: {row['certificate_id']}")
        if row["solver_status"] != "unsat":
            errors.append(f"exact certificate lacks UNSAT sufficiency: {row['certificate_id']}")
        if row["exact_minimum_status"] != "exact_minimum":
            errors.append(f"exact certificate has wrong exact status: {row['certificate_id']}")
        if row["best_upper_bound"] == "":
            errors.append(f"exact certificate lacks upper bound: {row['certificate_id']}")
        elif int(row["best_upper_bound"]) != len(json.loads(row["tested_interface"])):
            errors.append(f"upper bound does not match interface width: {row['certificate_id']}")
        if int(row["proved_lower_bound"]) != len(json.loads(row["tested_interface"])):
            errors.append(f"exact minimum does not exclude smaller interfaces: {row['certificate_id']}")
        if row["diagnostic_only"] == "true" and row["classification"] != "global_diagnostic_not_local_success":
            errors.append(f"whole-PI diagnostic counted as local exact success: {row['certificate_id']}")
        _rerun_small_sufficiency(row, errors)

    for row in tables["input_lower_bound_certificates.csv"]:
        if row["exact_minimum_status"] == "exact_minimum":
            errors.append(f"exact minimum stored in lower-bound table: {row['certificate_id']}")
        if row["timeout"] == "true" and row["classification"] not in {"unresolved_timeout", "search_budget_exhaustion"}:
            errors.append(f"timeout labelled as disproval: {row['certificate_id']}")
        for cid in json.loads(row["counterexample_ids"] or "[]"):
            if cid not in cex_by_id:
                errors.append(f"lower-bound certificate references missing counterexample: {cid}")

    for row in tables["whole_design_diagnostics.csv"]:
        if row["classification"] != "global_diagnostic_not_local_success":
            errors.append(f"whole-design diagnostic has wrong classification: {row['analysis_target_id']}")

    for row in tables["output_interface_candidates.csv"]:
        if row["solver_status"] == "sat" and row["counterexample_reproduced"] != "true":
            errors.append(f"output-interface SAT row lacks reproduced cex: {row['analysis_target_id']}")

    for row in tables["output_counterexamples.csv"]:
        if row["counterexample_reproduced"] != "true":
            errors.append(f"output counterexample not concretely reproduced: {row['counterexample_id']}")
        for side in ("assignment_a_path", "assignment_b_path"):
            if not (args.output_dir / row[side]).exists():
                errors.append(f"missing output counterexample assignment file: {row[side]}")

    for row in tables["output_difference_sets.csv"]:
        diff = json.loads(row["difference_set"])
        if int(row["difference_set_width"]) != len(diff):
            errors.append(f"output difference-set width mismatch: {row['counterexample_id']}")

    for row in tables["target_utility_proofs.csv"]:
        if row["target_influence_status"] == "influential" and row["witness_available"] != "true":
            errors.append(f"target utility claimed without witness: {row['analysis_target_id']}")

    for row in tables["algorithm_gap_classifications.csv"]:
        if row["source_blind"] != "true":
            errors.append(f"algorithm-gap row not source blind: {row['analysis_target_id']}")
        if row["gap_status"] == "proved_algorithm_gap" and "compact_exact" not in row["certificate_classification"]:
            errors.append(f"algorithm gap without compact exact certificate: {row['analysis_target_id']}")

    for row in tables["certificate_guided_transplant_attempts.csv"]:
        if row["new_recovered_boundary"] == "true":
            if row["graph_active"] != "true":
                errors.append(f"boundary counted without graph activity: {row['analysis_target_id']}")
            if row["source_cec_status"] != "equivalent" or row["cross_cec_status"] != "equivalent":
                errors.append(f"boundary counted without both global CEC scopes: {row['analysis_target_id']}")
            if not abc_available:
                errors.append(f"no-ABC run contains accepted global claim: {row['analysis_target_id']}")

    for row in tables["global_cec.csv"]:
        if row["claimed_global"] == "true" and row["status"] != "equivalent":
            errors.append(f"global CEC claim without equivalent status: {row['analysis_target_id']} {row['scope']}")
        if row["claimed_global"] == "true" and not abc_available:
            errors.append(f"global CEC claim emitted without ABC: {row['analysis_target_id']}")

    for row in tables["controlled_results.csv"]:
        if row["expected_minimum"] != row["exhaustive_minimum"]:
            errors.append(f"controlled exact minimum mismatch: {row['case_id']}")
        if row["z3_status"] != "unsat":
            errors.append(f"controlled final proof not UNSAT: {row['case_id']}")
        if row["z3_counterexamples_reproduced"] != "true":
            errors.append(f"controlled counterexample replay failed: {row['case_id']}")

    taxonomy_total = sum(int(r["count"]) for r in tables["failure_taxonomy.csv"])
    if taxonomy_total != len(dev):
        errors.append(f"summary/raw count mismatch: taxonomy={taxonomy_total} development={len(dev)}")
    for row in tables["supported_claims.csv"]:
        if full_real_run and row["claim"] == "all_56_previous_failures_audited" and row["supported"] != "true":
            errors.append("supported claims table does not support 56-row audit")

    if errors:
        return _fail(errors)
    print(
        "Formal locality-barrier results validated: "
        f"{len(dev)} real targets, "
        f"{len(tables['input_exact_minimum_certificates.csv'])} exact input minima, "
        f"{len(tables['input_lower_bound_certificates.csv'])} lower/diagnostic certificates, "
        f"{len(tables['input_counterexamples.csv'])} replayed counterexamples"
    )
    return 0


def _rerun_small_sufficiency(row: dict[str, str], errors: list[str]) -> None:
    source = ROOT / row["source_path"]
    optimized = ROOT / row["optimized_path"]
    if not source.exists() or not optimized.exists():
        source = Path(row["source_path"])
        optimized = Path(row["optimized_path"])
    if not source.exists() or not optimized.exists():
        errors.append(f"cannot replay exact certificate paths: {row['certificate_id']}")
        return
    proof = prove_interface_sufficiency(
        source_path=source,
        optimized_path=optimized,
        interface=tuple(json.loads(row["tested_interface"])),
        target_vector=tuple(json.loads(row["target_vector"])),
    )
    if proof.status != "unsat":
        errors.append(f"replayed sufficiency is not UNSAT: {row['certificate_id']} -> {proof.status}")


def _fail(errors: list[str]) -> int:
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
