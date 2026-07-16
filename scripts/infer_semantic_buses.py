#!/usr/bin/env python3
"""Infer semantic bus hypotheses from Phase 2 scalar interfaces."""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from boundary_graph import CircuitGraph
from semantic_bus_inference import (
    SEMANTIC_BIT_ORDER_FIELDS,
    SEMANTIC_BUS_EVALUATION_FIELDS,
    SEMANTIC_BUS_HYPOTHESIS_FIELDS,
    SEMANTIC_INPUT_ROLE_FIELDS,
    annotate_ground_truth_matches,
    bit_order_rows,
    evaluate_hypotheses,
    ground_truth_hypotheses,
    infer_bus_hypotheses,
)
from semantic_interface import BusGroundTruth
from semantic_region import write_csv
from semantic_region_pipeline import RESULT_DIR, read_csv


def load_bus_rows() -> dict[str, list[BusGroundTruth]]:
    rows: dict[str, list[BusGroundTruth]] = defaultdict(list)
    for row in read_csv(RESULT_DIR / "semantic_bus_ground_truth.csv"):
        rows[row["case_id"]].append(
            BusGroundTruth(
                case_id=row["case_id"],
                bus_name=row["bus_name"],
                direction=row["direction"],
                width=int(row["width"]),
                signedness=row["signedness"],
                declared_msb=int(row["declared_msb"]),
                declared_lsb=int(row["declared_lsb"]),
                bit_order=row["bit_order"],
                member_signal_names=tuple(json.loads(row["member_signal_names"])),
                member_canonical_node_ids=tuple(json.loads(row["member_canonical_node_ids"])),
                role=row["role"],
                mode=row["mode"],
            )
        )
    return rows


def load_scalar_nodes() -> dict[tuple[str, str], tuple[str, ...]]:
    grouped: dict[tuple[str, str], list[tuple[int, str]]] = defaultdict(list)
    for row in read_csv(RESULT_DIR / "semantic_scalar_interfaces.csv"):
        grouped[(row["region_id"], row["direction"])].append((int(row["interface_position"]), row["raw_node_name"]))
    return {key: tuple(name for _, name in sorted(values)) for key, values in grouped.items()}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inference-mode", choices=["ground_truth_bus_mode", "inferred_bus_mode"], default="inferred_bus_mode")
    parser.add_argument("--feature-mode", default="full_combined")
    parser.add_argument("--region-source", action="append", dest="region_sources")
    parser.add_argument("--max-bus-hypotheses", type=int, default=12)
    args = parser.parse_args()

    regions = [row for row in read_csv(RESULT_DIR / "semantic_regions.csv") if row["eligible"] == "true"]
    if args.region_sources:
        regions = [row for row in regions if row["source_type"] in set(args.region_sources)]
    bus_by_case = load_bus_rows()
    scalar_by_region = load_scalar_nodes()
    all_hypotheses = []
    best_rows = []
    eval_rows = []
    role_rows = []
    order_rows = []
    failures = []
    for region in regions:
        graph = None
        if region["impl_circuit_path"]:
            graph = CircuitGraph.from_blif(ROOT / region["impl_circuit_path"])
        bus_rows = bus_by_case[region["case_id"]]
        for direction in ("input", "output"):
            scalar_nodes = scalar_by_region.get((region["region_id"], direction), tuple())
            if not scalar_nodes:
                failures.append({
                    "region_id": region["region_id"],
                    "case_id": region["case_id"],
                    "optimization": region["optimization"],
                    "source_type": region["source_type"],
                    "stage": "bus_inference",
                    "reason": f"missing_{direction}_scalar_interface",
                })
                continue
            if args.inference_mode == "ground_truth_bus_mode":
                hypotheses = ground_truth_hypotheses(
                    region_id=region["region_id"],
                    direction=direction,
                    bus_rows=bus_rows,
                    available_nodes=scalar_nodes,
                    case_id=region["case_id"],
                )
            else:
                hypotheses = infer_bus_hypotheses(
                    region_id=region["region_id"],
                    direction=direction,
                    nodes=scalar_nodes,
                    graph=graph,
                    feature_mode=args.feature_mode,
                    max_bus_hypotheses=args.max_bus_hypotheses,
                )
                hypotheses = annotate_ground_truth_matches(hypotheses, bus_rows)
            all_hypotheses.extend(h.to_csv_row() for h in hypotheses)
            best_rows.extend(h.to_csv_row() for h in hypotheses if h.rank == 1)
            eval_rows.append(
                evaluate_hypotheses(
                    region_row=region,
                    direction=direction,
                    hypotheses=hypotheses,
                    bus_rows=bus_rows,
                    scalar_nodes=scalar_nodes,
                    feature_mode=args.feature_mode,
                )
            )
            order_rows.extend(bit_order_rows(region_row=region, direction=direction, hypotheses=hypotheses, bus_rows=bus_rows, scalar_nodes=scalar_nodes))
            if direction == "input":
                truth_role = {
                    node: bus.role
                    for bus in bus_rows
                    if bus.direction == "input"
                    for node in bus.member_signal_names
                }
                for hyp in hypotheses:
                    for node in hyp.member_nodes:
                        role_rows.append({
                            "region_id": region["region_id"],
                            "case_id": region["case_id"],
                            "optimization": region["optimization"],
                            "source_type": region["source_type"],
                            "node": node,
                            "predicted_role": hyp.role,
                            "ground_truth_role": truth_role.get(node, "unknown"),
                            "role_score": f"{hyp.role_score:.6f}",
                            "correct": str(hyp.role == truth_role.get(node, "") or (hyp.role in {"control", "selector"} and truth_role.get(node) in {"control", "selector"})).lower(),
                            "inference_mode": args.inference_mode,
                        })

    write_csv(all_hypotheses, RESULT_DIR / "semantic_bus_hypotheses.csv", SEMANTIC_BUS_HYPOTHESIS_FIELDS)
    write_csv(best_rows, RESULT_DIR / "semantic_bus_best_hypotheses.csv", SEMANTIC_BUS_HYPOTHESIS_FIELDS)
    write_csv(eval_rows, RESULT_DIR / "semantic_bus_evaluation.csv", SEMANTIC_BUS_EVALUATION_FIELDS)
    write_csv(role_rows, RESULT_DIR / "semantic_input_roles.csv", SEMANTIC_INPUT_ROLE_FIELDS)
    write_csv(order_rows, RESULT_DIR / "semantic_bit_order_evaluation.csv", SEMANTIC_BIT_ORDER_FIELDS)
    write_csv(failures, RESULT_DIR / "semantic_bus_dependency_failures.csv", ["region_id", "case_id", "optimization", "source_type", "stage", "reason"])
    print(f"Wrote {len(all_hypotheses)} semantic bus hypotheses for {len(regions)} regions")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
