#!/usr/bin/env python3
"""Validate necessity-first target discovery artifacts."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "results" / "necessity_first_target_discovery"

REQUIRED = {
    "experiment_manifest.csv": {"git_head", "config_hash", "source_blind"},
    "environment.csv": {"tool", "version", "status"},
    "dataset_classification.csv": {"benchmark_id", "dataset_class", "split"},
    "benchmark_sources_licenses.csv": {"benchmark_id", "source_license", "redistributable"},
    "target_provenance.csv": {"stable_target_id", "dataset_class", "source_file", "optimized_artifact", "optimized_target_node", "source_optimized_cec_status", "source_blind", "artifact_availability"},
    "pi_alignment.csv": {"stable_target_id", "status", "pi_alignment_hash"},
    "source_optimized_cec.csv": {"stable_target_id", "cec_status", "cec_backend"},
    "raw_target_candidates.csv": {"stable_target_id", "optimized_target_node", "rank", "source_blind"},
    "structural_observability.csv": {"stable_target_id", "has_structural_output_path", "evidence_level"},
    "nonconstant_proofs.csv": {"stable_target_id", "status", "evidence_level"},
    "forced_observability_proofs.csv": {"stable_target_id", "status", "witness_assignment", "counterexample_reproduced", "evidence_level"},
    "reachable_necessity_proofs.csv": {"stable_target_id", "status", "witness_a", "witness_b", "counterexample_reproduced", "evidence_level"},
    "target_utility_by_frontier.csv": {"stable_target_id", "classification", "frontier_radius"},
    "target_ranking.csv": {"stable_target_id", "rank", "score", "source_blind"},
    "leakage_audit.csv": {"field", "blind_selection_access", "status"},
    "eligible_target_manifest.csv": {"stable_target_id", "eligibility_status", "eligibility_stage", "reason"},
    "formal_locality_results.csv": {"stable_target_id", "solver_status", "exact_minimum_status", "compact_interface"},
    "adapter_proofs.csv": {"stable_target_id", "proof_status", "reason"},
    "graph_rewrites.csv": {"stable_target_id", "rewrite_emitted", "graph_active", "status"},
    "global_cec.csv": {"stable_target_id", "scope", "status", "claimed_global"},
    "boundary_recovery.csv": {"stable_target_id", "status", "new_boundary"},
    "critical_path_utility.csv": {"stable_target_id", "status", "mapped_targets"},
    "durability.csv": {"stable_target_id", "status", "survived"},
    "controlled_results.csv": {"case_id", "expected_status", "checker_status"},
    "standard_netlist_results.csv": {"benchmark_id", "targets", "eligible_targets"},
    "external_rtl_development_results.csv": {"split", "designs", "eligible_targets", "status"},
    "external_rtl_heldout_results.csv": {"split", "designs", "eligible_targets", "status"},
    "historical_selector_baseline.csv": {"selector", "rows", "eligible"},
    "ablations.csv": {"ablation", "raw_candidates", "eligible_after_filter"},
    "runtime_timeouts.csv": {"stage", "queries", "timeouts"},
    "failure_taxonomy.csv": {"category", "count"},
    "corrected_scientific_claims.csv": {"claim", "supported", "evidence_file"},
}

FORBIDDEN_BLIND_FIELDS = {
    "operator_type",
    "source_hierarchy",
    "source_boundary_id",
    "ground_truth_bus_grouping",
    "expected_optimized_correspondence",
    "known_successful_target",
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--allow-no-abc", action="store_true")
    args = parser.parse_args()
    errors: list[str] = []
    tables: dict[str, list[dict[str, str]]] = {}
    for name, required in REQUIRED.items():
        path = args.output_dir / name
        if not path.exists():
            errors.append(f"missing required file: {name}")
            continue
        with path.open(newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            rows = list(reader)
        missing = required - set(reader.fieldnames or [])
        if missing:
            errors.append(f"{name} missing columns {sorted(missing)}")
        tables[name] = rows
    if errors:
        return _fail(errors)

    provenance = {row["stable_target_id"]: row for row in tables["target_provenance.csv"]}
    pi = {row["stable_target_id"]: row for row in tables["pi_alignment.csv"]}
    cec = {row["stable_target_id"]: row for row in tables["source_optimized_cec.csv"]}
    nonconst = {row["stable_target_id"]: row for row in tables["nonconstant_proofs.csv"]}
    forced = {row["stable_target_id"]: row for row in tables["forced_observability_proofs.csv"]}
    necessity = {row["stable_target_id"]: row for row in tables["reachable_necessity_proofs.csv"]}
    structural = {row["stable_target_id"]: row for row in tables["structural_observability.csv"]}

    if not provenance:
        errors.append("no target provenance rows emitted")

    for row in tables["target_provenance.csv"]:
        sid = row["stable_target_id"]
        if row["source_blind"] != "true":
            errors.append(f"target provenance is not source blind: {sid}")
        for rel_field in ("source_file", "optimized_artifact"):
            if row[rel_field] and not (ROOT / row[rel_field]).exists():
                errors.append(f"artifact missing for {sid}: {row[rel_field]}")
        if row["artifact_availability"] == "available" and (not row["source_file"] or not row["optimized_artifact"]):
            errors.append(f"available target lacks artifacts: {sid}")
        if row["source_optimized_cec_status"] != "equivalent":
            errors.append(f"provenance-complete target lacks equivalent CEC: {sid}")
        if sid not in pi or pi[sid]["status"] != "aligned":
            errors.append(f"target lacks aligned PI/PO status: {sid}")
        if sid not in cec or cec[sid]["cec_status"] != "equivalent":
            errors.append(f"target lacks source/optimized CEC row: {sid}")

    for row in tables["leakage_audit.csv"]:
        if row["field"] in FORBIDDEN_BLIND_FIELDS and row["blind_selection_access"] != "false":
            errors.append(f"forbidden ground-truth field reaches blind selection: {row['field']}")

    for row in tables["forced_observability_proofs.csv"]:
        if row["status"] == "forced_observable":
            if row["counterexample_reproduced"] != "true" or not json.loads(row["witness_assignment"] or "{}"):
                errors.append(f"forced-observable target lacks reproduced witness: {row['stable_target_id']}")
        if row["evidence_level"] == "structural_only":
            errors.append(f"forced-observability row downgraded to structural evidence: {row['stable_target_id']}")

    for row in tables["reachable_necessity_proofs.csv"]:
        if row["status"] == "reachable_necessary":
            if row["counterexample_reproduced"] != "true" or not json.loads(row["witness_a"] or "{}") or not json.loads(row["witness_b"] or "{}"):
                errors.append(f"reachable-necessary target lacks reproduced pair: {row['stable_target_id']}")

    eligible = [row for row in tables["eligible_target_manifest.csv"] if row["eligibility_status"] == "eligible_target_necessary"]
    for row in eligible:
        sid = row["stable_target_id"]
        if nonconst.get(sid, {}).get("status") != "nonconstant":
            errors.append(f"eligible target is constant or unsupported: {sid}")
        if structural.get(sid, {}).get("has_structural_output_path") != "true":
            errors.append(f"eligible target lacks structural output path: {sid}")
        if forced.get(sid, {}).get("status") != "forced_observable":
            errors.append(f"eligible target lacks forced observability: {sid}")
        if necessity.get(sid, {}).get("status") != "reachable_necessary":
            errors.append(f"eligible target lacks reachable necessity: {sid}")

    locality_ids = {row["stable_target_id"] for row in tables["formal_locality_results.csv"]}
    for row in eligible:
        if row["stable_target_id"] not in locality_ids:
            errors.append(f"eligible target skipped locality analysis: {row['stable_target_id']}")

    for row in tables["graph_rewrites.csv"]:
        if row["rewrite_emitted"] == "true" and not row["rewrite_artifact"]:
            errors.append(f"rewrite emitted without artifact: {row['stable_target_id']}")
        if row["status"] != "not_attempted" and row["rewrite_emitted"] != "true":
            errors.append(f"graph rewrite counted without emitted artifact: {row['stable_target_id']}")

    abc_available = any(row["tool"] == "abc" and row["status"] == "available" for row in tables["environment.csv"])
    for row in tables["global_cec.csv"]:
        if row["claimed_global"] == "true" and row["status"] != "equivalent":
            errors.append(f"global claim without equivalent CEC: {row['stable_target_id']} {row['scope']}")
        if row["claimed_global"] == "true" and not abc_available:
            errors.append(f"global claim emitted in no-ABC mode: {row['stable_target_id']}")

    for row in tables["boundary_recovery.csv"]:
        if row["new_boundary"] == "true":
            rewrite = next((r for r in tables["graph_rewrites.csv"] if r["stable_target_id"] == row["stable_target_id"]), {})
            if rewrite.get("graph_active") != "true":
                errors.append(f"boundary counted without graph-active rewrite: {row['stable_target_id']}")

    dataset_classes = Counter(row["dataset_class"] for row in tables["dataset_classification.csv"])
    if dataset_classes.get("generated_research_benchmark", 0) == 0:
        errors.append("generated benchmark class missing")
    for row in tables["external_rtl_development_results.csv"] + tables["external_rtl_heldout_results.csv"]:
        if row["status"] == "available" and int(row["designs"]) == 0:
            errors.append("external RTL marked available with zero designs")

    for row in tables["corrected_scientific_claims.csv"]:
        if row["supported"] != "true":
            errors.append(f"unsupported corrected claim: {row['claim']}")

    taxonomy = {row["category"]: int(row["count"]) for row in tables["failure_taxonomy.csv"]}
    if taxonomy.get("target_necessary_eligible", 0) != len(eligible):
        errors.append("taxonomy/eligible mismatch")
    if taxonomy.get("actual_graph_rewrites", 0) != sum(row["rewrite_emitted"] == "true" for row in tables["graph_rewrites.csv"]):
        errors.append("taxonomy/graph rewrite mismatch")

    if errors:
        return _fail(errors)
    print(
        "Necessity-first target results validated: "
        f"{len(tables['raw_target_candidates.csv'])} raw targets, "
        f"{len(eligible)} eligible target-necessary, "
        f"{sum(row['compact_interface'] == 'true' for row in tables['formal_locality_results.csv'])} compact interfaces, "
        f"{sum(row['rewrite_emitted'] == 'true' for row in tables['graph_rewrites.csv'])} graph rewrites"
    )
    return 0


def _fail(errors: list[str]) -> int:
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
