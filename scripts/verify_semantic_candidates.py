#!/usr/bin/env python3
"""Formally verify simulation-surviving direct semantic candidates."""

from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from semantic_direct_recovery import FORMAL_FIELDS, expr_from_candidate_row, load_bus_hypotheses, load_region_rows, read_csv
from semantic_formal_validation import FormalValidationConfig, validate_candidate_exhaustive
from semantic_region import write_csv
from semantic_region_pipeline import RESULT_DIR


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-formal-calls", type=int, default=12)
    parser.add_argument("--formal-timeout", type=float, default=10.0)
    parser.add_argument("--max-formal-scalar-bits", type=int, default=12)
    parser.add_argument("--output-dir", default=str(RESULT_DIR))
    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    regions = load_region_rows(RESULT_DIR)
    buses = load_bus_hypotheses(RESULT_DIR)
    candidates = {row["candidate_id"]: row for row in read_csv(out_dir / "semantic_direct_candidates.csv")}
    sim = {row["candidate_id"]: row for row in read_csv(out_dir / "semantic_candidate_simulation.csv")}
    rankings = read_csv(out_dir / "semantic_candidate_rankings.csv")
    by_region: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rankings:
        if sim.get(row["candidate_id"], {}).get("simulation_status") == "simulation_match":
            by_region[row["region_id"]].append(row)

    formal_rows = []
    config = FormalValidationConfig(max_scalar_bits=args.max_formal_scalar_bits, timeout_seconds=args.formal_timeout)
    for region_id, rows in sorted(by_region.items()):
        region = regions[region_id]
        input_buses = buses.get((region_id, "input"), [])
        output_buses = buses.get((region_id, "output"), [])
        for row in sorted(rows, key=lambda r: int(r["rank_after_simulation"]))[: args.max_formal_calls]:
            candidate = candidates[row["candidate_id"]]
            expr = expr_from_candidate_row(candidate)
            result = validate_candidate_exhaustive(blif_path=ROOT / region["impl_circuit_path"], input_buses=input_buses, output_bus=output_buses[0], expr=expr, config=config)
            formal_rows.append({"candidate_id": row["candidate_id"], "region_id": region_id, **result})
    write_csv(formal_rows, out_dir / "semantic_formal_results.csv", FORMAL_FIELDS)
    print(f"Formally checked {len(formal_rows)} direct semantic candidates")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
