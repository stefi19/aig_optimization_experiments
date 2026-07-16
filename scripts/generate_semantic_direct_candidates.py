#!/usr/bin/env python3
"""Generate bounded typed direct-template semantic candidates."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from semantic_direct_recovery import (
    DIRECT_CANDIDATE_FIELDS,
    fixed_family_order,
    load_bus_hypotheses,
    load_family_rankings,
    load_manifest,
    load_region_rows,
    oracle_family_order,
)
from semantic_grammar import GrammarConfig, generate_direct_candidates
from semantic_region import write_csv
from semantic_region_pipeline import RESULT_DIR


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--region-source", action="append", dest="region_sources")
    parser.add_argument("--family-order-mode", choices=["fixed_order", "dependency_ranked", "oracle_family"], default="dependency_ranked")
    parser.add_argument("--max-bus-hypotheses", type=int, default=12)
    parser.add_argument("--max-candidates", type=int, default=96)
    parser.add_argument("--max-candidates-per-family", type=int, default=24)
    parser.add_argument("--max-shift-amount", type=int, default=4)
    parser.add_argument("--output-dir", default=str(RESULT_DIR))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    out_dir = Path(args.output_dir)
    regions = load_region_rows(RESULT_DIR)
    manifest = load_manifest(RESULT_DIR)
    buses = load_bus_hypotheses(RESULT_DIR, max_rank=args.max_bus_hypotheses)
    dependency_orders = load_family_rankings(RESULT_DIR)
    rows = []
    failures = []
    for region_id, region in sorted(regions.items()):
        if args.region_sources and region["source_type"] not in set(args.region_sources):
            continue
        input_buses = buses.get((region_id, "input"), [])
        output_buses = buses.get((region_id, "output"), [])
        if not input_buses or not output_buses:
            failures.append({"region_id": region_id, "case_id": region["case_id"], "optimization": region["optimization"], "source_type": region["source_type"], "stage": "candidate_generation", "failure_reason": "missing_bus_hypothesis"})
            continue
        output_bus = output_buses[0]
        if args.family_order_mode == "fixed_order":
            family_order = fixed_family_order()
        elif args.family_order_mode == "oracle_family":
            family_order = oracle_family_order(region)
        else:
            family_order = dependency_orders.get(region_id, fixed_family_order())
        constants = json.loads(manifest[region["case_id"]].get("constants", "{}") or "{}")
        config = GrammarConfig(max_candidates_per_family=args.max_candidates_per_family, max_total_candidates_per_region=args.max_candidates, max_shift_amount=args.max_shift_amount)
        generated = generate_direct_candidates(input_buses=input_buses, output_width=int(output_bus["width"]), manifest_constants={k: int(v) for k, v in constants.items()}, family_order=family_order, config=config)
        if not generated:
            failures.append({"region_id": region_id, "case_id": region["case_id"], "optimization": region["optimization"], "source_type": region["source_type"], "stage": "candidate_generation", "failure_reason": "no_direct_template"})
            continue
        ground_truth_rank = next((idx for idx, family in enumerate(family_order, start=1) if family.startswith(region["family"]) or region["family"] in family), 0)
        for rank, (grammar_family, expr) in enumerate(generated, start=1):
            fields = expr.to_csv_fields()
            candidate_id = f"{region_id}__cand_{rank:04d}"
            rows.append({
                "candidate_id": candidate_id,
                "region_id": region_id,
                "case_id": region["case_id"],
                "family": region["family"],
                "operator": region["operator"],
                "optimization": region["optimization"],
                "source_type": region["source_type"],
                "family_order_mode": args.family_order_mode,
                "grammar_family": grammar_family,
                "candidate_rank": str(rank),
                "ground_truth_family_rank": str(ground_truth_rank),
                "first_attempted_family": family_order[0] if family_order else "",
                "families_attempted": json.dumps(family_order, separators=(",", ":")),
                "input_bus_count": str(len(input_buses)),
                "output_width": str(output_bus["width"]),
                "expression_id": fields["expression_id"],
                "expression_operator": fields["operator"],
                "operands": fields["operands"],
                "input_types": fields["input_types"],
                "output_type": fields["output_type"],
                "width": fields["width"],
                "signedness": fields["signedness"],
                "extension_mode": fields["extension_mode"],
                "truncation_mode": fields["truncation_mode"],
                "slice_range": fields["slice_range"],
                "constant_value": fields["constant_value"],
                "expression_depth": fields["expression_depth"],
                "canonical_form": fields["canonical_form"],
                "rtl_text": fields["rtl_text"],
                "rtl_cost": fields["rtl_cost"],
                "expression_json": fields["expression_json"],
                "schema_version": fields["schema_version"],
            })
    write_csv(rows, out_dir / "semantic_direct_candidates.csv", DIRECT_CANDIDATE_FIELDS)
    write_csv(failures, out_dir / "semantic_direct_failure_analysis.csv", ["region_id", "case_id", "optimization", "source_type", "stage", "failure_reason"])
    print(f"Wrote {len(rows)} direct semantic candidates")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
