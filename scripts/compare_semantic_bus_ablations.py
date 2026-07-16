#!/usr/bin/env python3
"""Compare lightweight bus-inference and family-ranking feature ablations."""

from __future__ import annotations

import json
import sys
import time
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from boundary_graph import CircuitGraph
from semantic_bus_inference import (
    aggregate_metrics,
    annotate_ground_truth_matches,
    evaluate_hypotheses,
    infer_bus_hypotheses,
)
from semantic_family_ranking import evaluation_rows, rank_region_family
from semantic_interface import BusGroundTruth
from semantic_region import write_csv
from semantic_region_pipeline import RESULT_DIR, read_csv


BUS_ABLATION_FIELDS = [
    "feature_mode",
    "region_rows",
    "direction_rows",
    "top_1_bus_match_rate",
    "top_3_bus_match_rate",
    "top_5_bus_match_rate",
    "mean_membership_precision",
    "mean_membership_recall",
    "mean_bit_order_accuracy",
    "mean_mrr",
    "runtime_seconds",
]

FAMILY_ABLATION_FIELDS = [
    "feature_mode",
    "ranked_regions",
    "top_1_family_accuracy",
    "top_3_family_accuracy",
    "mrr",
    "runtime_seconds",
]

FEATURE_MODES = (
    "names_only",
    "structure_only",
    "names_plus_structure",
    "full_combined",
)


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


def bool_rate(rows: list[dict[str, str]], field: str) -> float:
    return sum(1 for row in rows if row[field] == "true") / max(1, len(rows))


def run_bus_mode(
    mode: str,
    regions: list[dict[str, str]],
    bus_by_case: dict[str, list[BusGroundTruth]],
    scalar_by_region: dict[tuple[str, str], tuple[str, ...]],
) -> tuple[list[dict[str, str]], float]:
    start = time.perf_counter()
    rows: list[dict[str, str]] = []
    graph_cache: dict[str, CircuitGraph] = {}
    for region in regions:
        path = region["impl_circuit_path"]
        graph = graph_cache.get(path)
        if graph is None and path:
            graph = CircuitGraph.from_blif(ROOT / path)
            graph_cache[path] = graph
        for direction in ("input", "output"):
            scalar_nodes = scalar_by_region.get((region["region_id"], direction), tuple())
            if not scalar_nodes:
                continue
            hypotheses = infer_bus_hypotheses(
                region_id=region["region_id"],
                direction=direction,
                nodes=scalar_nodes,
                graph=graph,
                feature_mode=mode,
                max_bus_hypotheses=12,
            )
            hypotheses = annotate_ground_truth_matches(hypotheses, bus_by_case[region["case_id"]])
            rows.append(
                evaluate_hypotheses(
                    region_row=region,
                    direction=direction,
                    hypotheses=hypotheses,
                    bus_rows=bus_by_case[region["case_id"]],
                    scalar_nodes=scalar_nodes,
                    feature_mode=mode,
                )
            )
    return rows, time.perf_counter() - start


def write_summary(bus_rows: list[dict[str, str]], family_rows: list[dict[str, str]]) -> None:
    main_bus = next((row for row in bus_rows if row["feature_mode"] == "full_combined"), bus_rows[-1])
    main_family = next((row for row in family_rows if row["feature_mode"] == "full_combined"), family_rows[-1])
    text = f"""# Semantic Bus Inference and Dependency Geometry Summary

This phase infers bus hypotheses and dependency geometry from canonical scalar
interfaces. It does not synthesize expressions, solve coefficients, run CEGIS,
or claim high-level RTL operation recovery.

## Bus Inference

- Inference mode: inferred bus mode.
- Ground truth used for generation: false.
- Ground truth used for evaluation: true.
- Evaluated region rows: {main_bus['region_rows']}
- Direction rows: {main_bus['direction_rows']}
- Top-1 bus match rate: {main_bus['top_1_bus_match_rate']}
- Top-3 bus match rate: {main_bus['top_3_bus_match_rate']}
- Top-5 bus match rate: {main_bus['top_5_bus_match_rate']}
- Mean membership precision: {main_bus['mean_membership_precision']}
- Mean membership recall: {main_bus['mean_membership_recall']}
- Mean bit-order accuracy: {main_bus['mean_bit_order_accuracy']}
- Mean reciprocal rank: {main_bus['mean_mrr']}

## Dependency Geometry

Dependency matrices are structural plus sampled simulation estimates and bounded
Boolean-difference estimates where available. Sampled dependency values are
heuristic evidence, not formal proof.

## Family Ranking

Family ranking is a transparent, broad classifier over dependency geometry. It
is not operator recovery.

- Ranked regions: {main_family['ranked_regions']}
- Top-1 family accuracy: {main_family['top_1_family_accuracy']}
- Top-3 family accuracy: {main_family['top_3_family_accuracy']}
- MRR: {main_family['mrr']}

## Ablations

| Feature mode | Bus top-1 | Bus MRR | Family top-1 | Family MRR |
| --- | ---: | ---: | ---: | ---: |
"""
    family_by_mode = {row["feature_mode"]: row for row in family_rows}
    for row in bus_rows:
        fam = family_by_mode.get(row["feature_mode"], {})
        text += f"| {row['feature_mode']} | {row['top_1_bus_match_rate']} | {row['mean_mrr']} | {fam.get('top_1_family_accuracy', '0.000000')} | {fam.get('mrr', '0.000000')} |\n"
    text += "\nThe next phase should use these inferred groups to build dependency matrices suitable for expression-family-specific recovery, still with formal validation separated from heuristic ranking.\n"
    (RESULT_DIR / "semantic_bus_dependency_summary.md").write_text(text, encoding="utf-8")


def main() -> int:
    regions = [row for row in read_csv(RESULT_DIR / "semantic_regions.csv") if row["eligible"] == "true"]
    bus_by_case = load_bus_rows()
    scalar_by_region = load_scalar_nodes()
    dependency_features = {row["region_id"]: row for row in read_csv(RESULT_DIR / "semantic_dependency_features.csv")}
    region_by_id = {row["region_id"]: row for row in regions}

    bus_ablation_rows = []
    family_ablation_rows = []
    for mode in FEATURE_MODES:
        eval_rows_for_mode, bus_runtime = run_bus_mode(mode, regions, bus_by_case, scalar_by_region)
        bus_ablation_rows.append(
            {
                "feature_mode": mode,
                "region_rows": str(len(regions)),
                "direction_rows": str(len(eval_rows_for_mode)),
                "top_1_bus_match_rate": f"{bool_rate(eval_rows_for_mode, 'top_1_bus_match'):.6f}",
                "top_3_bus_match_rate": f"{bool_rate(eval_rows_for_mode, 'top_3_bus_match'):.6f}",
                "top_5_bus_match_rate": f"{bool_rate(eval_rows_for_mode, 'top_5_bus_match'):.6f}",
                "mean_membership_precision": f"{aggregate_metrics(eval_rows_for_mode, 'bus_membership_precision'):.6f}",
                "mean_membership_recall": f"{aggregate_metrics(eval_rows_for_mode, 'bus_membership_recall'):.6f}",
                "mean_bit_order_accuracy": f"{aggregate_metrics(eval_rows_for_mode, 'bit_order_accuracy'):.6f}",
                "mean_mrr": f"{aggregate_metrics(eval_rows_for_mode, 'mrr'):.6f}",
                "runtime_seconds": f"{bus_runtime:.6f}",
            }
        )

        family_start = time.perf_counter()
        bus_eval_by_region: dict[str, list[dict[str, str]]] = defaultdict(list)
        for row in eval_rows_for_mode:
            bus_eval_by_region[row["region_id"]].append(row)
        ranking_rows: list[dict[str, str]] = []
        for region_id, feature in sorted(dependency_features.items()):
            region = region_by_id.get(region_id)
            if region:
                ranking_rows.extend(rank_region_family(region, feature, bus_eval_by_region.get(region_id, [])))
        overall = next(row for row in evaluation_rows(ranking_rows, region_by_id) if row["scope"] == "overall")
        family_ablation_rows.append(
            {
                "feature_mode": mode,
                "ranked_regions": overall["rows"],
                "top_1_family_accuracy": overall["top_1_family_accuracy"],
                "top_3_family_accuracy": overall["top_3_family_accuracy"],
                "mrr": overall["mrr"],
                "runtime_seconds": f"{time.perf_counter() - family_start:.6f}",
            }
        )

    write_csv(bus_ablation_rows, RESULT_DIR / "semantic_bus_ablation.csv", BUS_ABLATION_FIELDS)
    write_csv(family_ablation_rows, RESULT_DIR / "semantic_family_ablation.csv", FAMILY_ABLATION_FIELDS)
    write_summary(bus_ablation_rows, family_ablation_rows)
    print("Wrote semantic bus and family ablation summaries")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
