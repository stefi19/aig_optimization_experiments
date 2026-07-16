#!/usr/bin/env python3
"""Rank broad semantic families from inferred buses and dependency geometry."""

from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from semantic_family_ranking import (
    SEMANTIC_FAMILY_EVALUATION_FIELDS,
    SEMANTIC_FAMILY_RANKING_FIELDS,
    confusion_matrix,
    evaluation_rows,
    rank_region_family,
)
from semantic_region import write_csv
from semantic_region_pipeline import RESULT_DIR, read_csv


CONFUSION_FIELDS = ["ground_truth_family", "predicted_family", "count"]


def main() -> int:
    regions = {row["region_id"]: row for row in read_csv(RESULT_DIR / "semantic_regions.csv") if row["eligible"] == "true"}
    features = read_csv(RESULT_DIR / "semantic_dependency_features.csv")
    bus_eval: dict[str, list[dict[str, str]]] = {}
    for row in read_csv(RESULT_DIR / "semantic_bus_evaluation.csv"):
        bus_eval.setdefault(row["region_id"], []).append(row)

    ranking_rows: list[dict[str, str]] = []
    for feature in sorted(features, key=lambda row: row["region_id"]):
        region = regions.get(feature["region_id"])
        if not region:
            continue
        ranking_rows.extend(rank_region_family(region, feature, bus_eval.get(feature["region_id"], [])))

    eval_rows = evaluation_rows(ranking_rows, regions)
    confusion_rows = [
        {"ground_truth_family": truth, "predicted_family": pred, "count": str(count)}
        for (truth, pred), count in sorted(confusion_matrix(ranking_rows).items())
    ]
    write_csv(ranking_rows, RESULT_DIR / "semantic_family_rankings.csv", SEMANTIC_FAMILY_RANKING_FIELDS)
    write_csv(eval_rows, RESULT_DIR / "semantic_family_evaluation.csv", SEMANTIC_FAMILY_EVALUATION_FIELDS)
    write_csv(confusion_rows, RESULT_DIR / "semantic_family_confusion_matrix.csv", CONFUSION_FIELDS)
    print(f"Wrote {len(ranking_rows)} semantic family ranking rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
