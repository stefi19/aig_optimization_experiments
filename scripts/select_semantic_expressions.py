#!/usr/bin/env python3
"""Select best formally verified direct semantic expressions and summarize results."""

from __future__ import annotations

import json
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from problem_a_cost import expression_cost, reduction_rate
from semantic_direct_recovery import BEST_FIELDS, RECOVERY_FIELDS, VERIFIED_FIELDS, classify_verified_expression, expr_from_candidate_row, load_bus_hypotheses, load_region_rows, read_csv
from semantic_region import write_csv
from semantic_region_pipeline import RESULT_DIR
from semantic_rtl_emitter import emit_candidate_module


def summarize_scope(scope: str, group: str, regions: list[dict[str, str]], candidates: list[dict[str, str]], sim: list[dict[str, str]], formal: list[dict[str, str]], verified: list[dict[str, str]]) -> dict[str, str]:
    region_ids = {row["region_id"] for row in regions}
    cand = [row for row in candidates if row["region_id"] in region_ids]
    sim_rows = [row for row in sim if row["region_id"] in region_ids]
    formal_rows = [row for row in formal if row["region_id"] in region_ids]
    ver = [row for row in verified if row["region_id"] in region_ids]
    recovered_regions = {row["region_id"] for row in ver}
    exact = {row["region_id"] for row in ver if row["classification"] == "exact_syntactic_match"}
    canonical = {row["region_id"] for row in ver if row["classification"] == "canonical_syntactic_match"}
    alt = {row["region_id"] for row in ver if row["classification"] == "formally_equivalent_alternative"}
    costs = [float(row["candidate_rtl_cost"]) for row in ver]
    reductions = [float(row["reduction_rate"]) for row in ver]
    return {
        "scope": scope,
        "group": group,
        "eligible_regions": str(len(region_ids)),
        "regions_with_direct_candidates": str(len({row["region_id"] for row in cand})),
        "generated_candidates": str(len(cand)),
        "canonical_candidates": str(len({row["canonical_form"] for row in cand})),
        "simulation_checked": str(len(sim_rows)),
        "simulation_survivors": str(sum(1 for row in sim_rows if row["simulation_status"] == "simulation_match")),
        "formal_checks": str(len(formal_rows)),
        "verified_candidates": str(len(ver)),
        "recovered_regions": str(len(recovered_regions)),
        "formal_recovery_rate": f"{len(recovered_regions) / max(1, len(region_ids)):.6f}",
        "exact_syntactic_recovery_rate": f"{len(exact) / max(1, len(region_ids)):.6f}",
        "canonical_syntactic_recovery_rate": f"{len(canonical) / max(1, len(region_ids)):.6f}",
        "equivalent_alternative_rate": f"{len(alt) / max(1, len(region_ids)):.6f}",
        "mean_verified_rtl_cost": f"{statistics.mean(costs):.6f}" if costs else "0.000000",
        "median_verified_rtl_cost": f"{statistics.median(costs):.6f}" if costs else "0.000000",
        "mean_reduction_rate": f"{statistics.mean(reductions):.6f}" if reductions else "0.000000",
        "cases_above_70_reduction": str(sum(1 for row in ver if row["reduction_rate_ge_70"] == "true")),
    }


def main() -> int:
    regions = load_region_rows(RESULT_DIR)
    buses = load_bus_hypotheses(RESULT_DIR)
    candidates = {row["candidate_id"]: row for row in read_csv(RESULT_DIR / "semantic_direct_candidates.csv")}
    sim = read_csv(RESULT_DIR / "semantic_candidate_simulation.csv")
    formal = read_csv(RESULT_DIR / "semantic_formal_results.csv")
    verified_rows = []
    for row in formal:
        if row["formal_status"] != "formally_verified_region" or row["formal_evidence_level"] != "formal_exhaustive":
            continue
        candidate = candidates[row["candidate_id"]]
        region = regions[candidate["region_id"]]
        expr = expr_from_candidate_row(candidate)
        input_gate_count = max(1, len(json.loads(region["region_nodes"])))
        cost = expression_cost(expr)
        reduction = reduction_rate(cost, input_gate_count)
        verified_rows.append({
            "candidate_id": row["candidate_id"],
            "region_id": row["region_id"],
            "case_id": candidate["case_id"],
            "family": candidate["family"],
            "operator": candidate["operator"],
            "optimization": candidate["optimization"],
            "source_type": candidate["source_type"],
            "grammar_family": candidate["grammar_family"],
            "classification": classify_verified_expression(candidate, region),
            "proof_scope": row["proof_scope"],
            "canonical_form": candidate["canonical_form"],
            "rtl_text": candidate["rtl_text"],
            "candidate_rtl_cost": str(cost),
            "input_gate_count": str(input_gate_count),
            "reduction_rate": f"{reduction:.6f}",
            "reduction_rate_ge_70": str(reduction >= 70.0).lower(),
            "formal_runtime": row["formal_runtime"],
        })
    by_region: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in verified_rows:
        by_region[row["region_id"]].append(row)
    best_rows = []
    for region_id, rows in sorted(by_region.items()):
        ordered = sorted(rows, key=lambda row: (0 if row["proof_scope"] == "region" else 1, int(row["candidate_rtl_cost"]), int(candidates[row["candidate_id"]]["expression_depth"]), float(row["formal_runtime"]), row["canonical_form"]))
        best_rows.append({**ordered[0], "selection_rank": "1"})

    region_list = list(regions.values())
    summary = [summarize_scope("overall", "all", region_list, list(candidates.values()), sim, formal, verified_rows)]
    for scope in ("family", "operator", "optimization", "source_type"):
        grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
        for row in region_list:
            grouped[row[scope]].append(row)
        for group, rows in sorted(grouped.items()):
            summary.append(summarize_scope(scope, group, rows, list(candidates.values()), sim, formal, verified_rows))

    write_csv(verified_rows, RESULT_DIR / "semantic_verified_candidates.csv", VERIFIED_FIELDS)
    write_csv(best_rows, RESULT_DIR / "semantic_best_verified_expressions.csv", BEST_FIELDS)
    write_csv(summary, RESULT_DIR / "semantic_ground_truth_recovery.csv", RECOVERY_FIELDS)
    write_csv([row for row in summary if row["scope"] == "source_type" and row["group"] == "whole_output_cone"], RESULT_DIR / "semantic_output_cone_recovery.csv", RECOVERY_FIELDS)
    write_csv([row for row in summary if row["scope"] == "operator"], RESULT_DIR / "semantic_direct_recovery_by_operator.csv", RECOVERY_FIELDS)
    write_csv([row for row in summary if row["scope"] == "optimization"], RESULT_DIR / "semantic_direct_recovery_by_optimization.csv", RECOVERY_FIELDS)

    verified_dir = RESULT_DIR / "verified_rtl"
    verified_dir.mkdir(parents=True, exist_ok=True)
    chunks = ["// Compact sample of formally verified direct semantic expressions.\n"]
    for idx, row in enumerate(best_rows[:50]):
        region_id = row["region_id"]
        expr = expr_from_candidate_row(candidates[row["candidate_id"]])
        input_buses = buses.get((region_id, "input"), [])
        output_bus = buses.get((region_id, "output"), [{}])[0]
        chunks.append(emit_candidate_module(module_name=f"verified_direct_{idx:03d}", input_buses=input_buses, output_bus=output_bus, expr=expr))
    (verified_dir / "selected_verified_expressions.v").write_text("\n".join(chunks), encoding="utf-8")

    overall = summary[0]
    text = f"""# Direct Semantic Template Recovery Summary

This phase recovers only expressions contained in the bounded direct-template grammar. Parameterized coefficient solving and CEGIS refinement remain future work.

Every accepted expression below is `formally_verified_region` using exhaustive region truth-table comparison. Sampled simulation is used only as a filter and is not formal proof. Region equivalence is not labeled global equivalence.

## Candidate Funnel

- Eligible regions: {overall['eligible_regions']}
- Regions with direct candidates: {overall['regions_with_direct_candidates']}
- Generated candidates: {overall['generated_candidates']}
- Canonical candidates: {overall['canonical_candidates']}
- Simulation checked: {overall['simulation_checked']}
- Simulation survivors: {overall['simulation_survivors']}
- Formal checks: {overall['formal_checks']}
- Verified candidates: {overall['verified_candidates']}
- Recovered regions: {overall['recovered_regions']}

## Recovery

- Formal recovery rate: {overall['formal_recovery_rate']}
- Exact syntactic recovery rate: {overall['exact_syntactic_recovery_rate']}
- Canonical syntactic recovery rate: {overall['canonical_syntactic_recovery_rate']}
- Equivalent-alternative rate: {overall['equivalent_alternative_rate']}

## Problem-A-Inspired RTL Cost

- Mean verified RTL cost: {overall['mean_verified_rtl_cost']}
- Median verified RTL cost: {overall['median_verified_rtl_cost']}
- Mean reduction rate: {overall['mean_reduction_rate']}
- Cases above 70% reduction: {overall['cases_above_70_reduction']}
"""
    (RESULT_DIR / "semantic_direct_recovery_summary.md").write_text(text, encoding="utf-8")
    print(f"Selected {len(best_rows)} best verified semantic expressions")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
