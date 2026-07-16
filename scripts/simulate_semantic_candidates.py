#!/usr/bin/env python3
"""Simulate direct semantic candidates with deterministic semantic patterns."""

from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from semantic_direct_recovery import RANKING_FIELDS, SIMULATION_FIELDS, candidate_sort_key, expr_from_candidate_row, load_bus_hypotheses, load_region_rows, read_csv
from semantic_patterns import generate_semantic_patterns
from semantic_region import write_csv
from semantic_region_pipeline import RESULT_DIR
from semantic_simulation import simulate_candidate


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--simulation-filter-mode", choices=["no_simulation_filter", "basic_patterns", "semantic_patterns", "semantic_plus_random"], default="semantic_patterns")
    parser.add_argument("--candidate-ranking-mode", choices=["cost_first", "dependency_first", "hybrid"], default="hybrid")
    parser.add_argument("--output-dir", default=str(RESULT_DIR))
    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    regions = load_region_rows(RESULT_DIR)
    buses = load_bus_hypotheses(RESULT_DIR)
    candidates = read_csv(out_dir / "semantic_direct_candidates.csv")
    sim_rows = []
    ranking_inputs = []
    for candidate in candidates:
        region = regions[candidate["region_id"]]
        input_buses = buses.get((candidate["region_id"], "input"), [])
        output_buses = buses.get((candidate["region_id"], "output"), [])
        if not input_buses or not output_buses or not region["impl_circuit_path"]:
            continue
        random_count = 0 if args.simulation_filter_mode == "basic_patterns" else 16
        patterns = generate_semantic_patterns(input_buses, random_count=random_count, max_patterns=64 if args.simulation_filter_mode != "semantic_plus_random" else 96)
        expr = expr_from_candidate_row(candidate)
        result = simulate_candidate(blif_path=ROOT / region["impl_circuit_path"], input_buses=input_buses, output_bus=output_buses[0], expr=expr, patterns=patterns)
        sim = {"candidate_id": candidate["candidate_id"], "region_id": candidate["region_id"], "simulation_filter_mode": args.simulation_filter_mode, **result}
        sim_rows.append({field: sim[field] for field in SIMULATION_FIELDS})
        merged = {**candidate, **sim}
        ranking_inputs.append(merged)

    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in ranking_inputs:
        grouped[row["region_id"]].append(row)
    ranking_rows = []
    for region_id, rows in sorted(grouped.items()):
        if args.candidate_ranking_mode == "cost_first":
            ordered = sorted(rows, key=lambda row: (int(row["rtl_cost"]), int(row["expression_depth"]), int(row["candidate_rank"])))
        elif args.candidate_ranking_mode == "dependency_first":
            ordered = sorted(rows, key=lambda row: (int(row["candidate_rank"]), int(row["rtl_cost"]), row["candidate_id"]))
        else:
            ordered = sorted(rows, key=candidate_sort_key)
        for rank, row in enumerate(ordered, start=1):
            ranking_rows.append({
                "candidate_id": row["candidate_id"],
                "region_id": region_id,
                "candidate_ranking_mode": args.candidate_ranking_mode,
                "rank_after_simulation": str(rank),
                "ranking_score": row["sample_match_rate"],
                "simulation_status": row["simulation_status"],
                "sample_match_rate": row["sample_match_rate"],
                "grammar_family": row["grammar_family"],
                "expression_depth": row["expression_depth"],
                "rtl_cost": row["rtl_cost"],
            })
    write_csv(sim_rows, out_dir / "semantic_candidate_simulation.csv", SIMULATION_FIELDS)
    write_csv(ranking_rows, out_dir / "semantic_candidate_rankings.csv", RANKING_FIELDS)
    print(f"Simulated {len(sim_rows)} direct semantic candidates")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
