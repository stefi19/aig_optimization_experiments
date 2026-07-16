"""Transparent semantic-family ranking from bus and dependency features.

This module ranks broad semantic families only. It does not recover operators or
generate expressions.
"""

from __future__ import annotations

import json
from collections import Counter


FAMILY_CANDIDATES = (
    "arithmetic_add_sub",
    "arithmetic_multiply",
    "arithmetic_affine_or_mac",
    "boolean_bitwise",
    "control_mux",
    "comparison",
    "bit_manipulation",
    "unknown",
)

SEMANTIC_FAMILY_RANKING_FIELDS = [
    "region_id",
    "case_id",
    "optimization",
    "source_type",
    "candidate_family",
    "family_score",
    "feature_contributions",
    "rank",
    "ground_truth_family",
    "ground_truth_rank",
]

SEMANTIC_FAMILY_EVALUATION_FIELDS = [
    "scope",
    "group",
    "rows",
    "top_1_family_accuracy",
    "top_3_family_accuracy",
    "mrr",
]


def ground_truth_family(family: str, operator: str) -> str:
    op = operator.lower()
    if family == "control" or "mux" in op:
        return "control_mux"
    if family == "comparison":
        return "comparison"
    if family == "boolean":
        return "boolean_bitwise"
    if family == "bitmanip":
        return "bit_manipulation"
    if family == "arithmetic":
        if "multiply" in op:
            return "arithmetic_multiply"
        if "affine" in op or "mac" in op:
            return "arithmetic_affine_or_mac"
        return "arithmetic_add_sub"
    return "unknown"


def f(row: dict[str, str], key: str) -> float:
    try:
        return float(row.get(key, 0.0))
    except ValueError:
        return 0.0


def candidate_scores(feature_row: dict[str, str], bus_eval_rows: list[dict[str, str]]) -> dict[str, tuple[float, dict[str, float]]]:
    density = f(feature_row, "dependency_density")
    diagonal = f(feature_row, "diagonal_concentration")
    lower = f(feature_row, "lower_triangularity")
    bandwidth = f(feature_row, "bandwidth")
    carry = f(feature_row, "carry_progression_score")
    multiplier = f(feature_row, "multiplier_diagonal_score")
    single_output = 1.0 if int(feature_row.get("output_count", "0") or 0) == 1 else 0.0
    output_count = int(feature_row.get("output_count", "0") or 0)
    input_count = int(feature_row.get("input_count", "0") or 0)
    control_acc_signal = max((f(row, "control_input_accuracy") for row in bus_eval_rows if row["direction"] == "input"), default=0.0)
    output_bus_signal = max((f(row, "output_bus_accuracy") for row in bus_eval_rows if row["direction"] == "output"), default=0.0)

    contributions = {
        "arithmetic_add_sub": {
            "carry_progression": carry * 0.45,
            "lower_triangularity": lower * 0.25,
            "moderate_density": (1.0 - abs(density - 0.55)) * 0.20,
            "multi_output": (1.0 if output_count > 1 else 0.0) * 0.10,
        },
        "arithmetic_multiply": {
            "broad_dependency": density * 0.35,
            "multiplier_geometry": multiplier * 0.35,
            "low_diagonal": (1.0 - diagonal) * 0.15,
            "multi_output": (1.0 if output_count > 1 else 0.0) * 0.15,
        },
        "arithmetic_affine_or_mac": {
            "broad_dependency": density * 0.25,
            "carry_progression": carry * 0.25,
            "multi_input": min(1.0, input_count / 8.0) * 0.25,
            "moderate_bandwidth": (1.0 - abs(bandwidth - 0.5)) * 0.25,
        },
        "boolean_bitwise": {
            "diagonal": diagonal * 0.55,
            "locality": f(feature_row, "locality_score") * 0.25,
            "regularity": f(feature_row, "regularity_score") * 0.20,
        },
        "control_mux": {
            "control_signal": control_acc_signal * 0.35,
            "output_bus": output_bus_signal * 0.20,
            "regular_rows": f(feature_row, "regularity_score") * 0.20,
            "multi_output": (1.0 if output_count > 1 else 0.0) * 0.25,
        },
        "comparison": {
            "single_output": single_output * 0.55,
            "high_density": density * 0.25,
            "high_bit_priority": f(feature_row, "high_bit_priority_score") * 0.20,
        },
        "bit_manipulation": {
            "sparse_or_permutation": (1.0 - abs(density - 0.25)) * 0.30,
            "locality": f(feature_row, "locality_score") * 0.25,
            "diagonal_or_shift": max(diagonal, 1.0 - bandwidth) * 0.25,
            "regularity": f(feature_row, "regularity_score") * 0.20,
        },
        "unknown": {
            "fallback": 0.05,
        },
    }
    return {name: (sum(parts.values()), parts) for name, parts in contributions.items()}


def rank_region_family(
    region_row: dict[str, str],
    feature_row: dict[str, str],
    bus_eval_rows: list[dict[str, str]],
) -> list[dict[str, str]]:
    truth = ground_truth_family(region_row["family"], region_row["operator"])
    scores = candidate_scores(feature_row, bus_eval_rows)
    ordered = sorted(scores.items(), key=lambda item: (-item[1][0], item[0]))
    truth_rank = next((idx for idx, (name, _) in enumerate(ordered, start=1) if name == truth), 0)
    rows: list[dict[str, str]] = []
    for rank, (name, (score, contributions)) in enumerate(ordered, start=1):
        rows.append(
            {
                "region_id": region_row["region_id"],
                "case_id": region_row["case_id"],
                "optimization": region_row["optimization"],
                "source_type": region_row["source_type"],
                "candidate_family": name,
                "family_score": f"{score:.6f}",
                "feature_contributions": json.dumps(contributions, sort_keys=True, separators=(",", ":")),
                "rank": str(rank),
                "ground_truth_family": truth,
                "ground_truth_rank": str(truth_rank),
            }
        )
    return rows


def evaluation_rows(ranking_rows: list[dict[str, str]], region_rows_by_id: dict[str, dict[str, str]]) -> list[dict[str, str]]:
    best_by_region: dict[str, list[dict[str, str]]] = {}
    for row in ranking_rows:
        best_by_region.setdefault(row["region_id"], []).append(row)

    def summarize(scope: str, group: str, region_ids: list[str]) -> dict[str, str]:
        ranks = []
        for region_id in region_ids:
            rows = best_by_region.get(region_id, [])
            rank = int(rows[0]["ground_truth_rank"]) if rows else 0
            ranks.append(rank)
        top1 = sum(1 for rank in ranks if rank == 1) / max(1, len(ranks))
        top3 = sum(1 for rank in ranks if 1 <= rank <= 3) / max(1, len(ranks))
        mrr = sum((1.0 / rank) for rank in ranks if rank) / max(1, len(ranks))
        return {
            "scope": scope,
            "group": group,
            "rows": str(len(ranks)),
            "top_1_family_accuracy": f"{top1:.6f}",
            "top_3_family_accuracy": f"{top3:.6f}",
            "mrr": f"{mrr:.6f}",
        }

    ids = sorted(best_by_region)
    rows = [summarize("overall", "all", ids)]
    for scope in ("family", "operator", "optimization", "source_type"):
        groups: dict[str, list[str]] = {}
        for region_id in ids:
            groups.setdefault(region_rows_by_id[region_id][scope], []).append(region_id)
        for group, group_ids in sorted(groups.items()):
            rows.append(summarize(scope, group, group_ids))
    return rows


def confusion_matrix(ranking_rows: list[dict[str, str]]) -> dict[tuple[str, str], int]:
    top = [row for row in ranking_rows if row["rank"] == "1"]
    return dict(Counter((row["ground_truth_family"], row["candidate_family"]) for row in top))
