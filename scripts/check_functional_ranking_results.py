#!/usr/bin/env python3
"""Validate functional-ranking result schemas."""

from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED = {
    "results/cofactor_sensitivity/cofactor_sensitivity_features.csv": {
        "benchmark",
        "optimization",
        "original_node",
        "optimized_node",
        "candidate_rank",
        "sat_status",
        "formal_label",
        "cofactor_consistency_score",
        "max_cofactor_error",
        "sensitivity_cosine_similarity",
        "boolean_difference_similarity",
        "functional_feature_evidence_level",
        "baseline",
        "full_combined",
    },
    "results/ranking_ablation/ranking_ablation_overall.csv": {
        "ranking_mode",
        "precision_at_1",
        "precision_at_5",
        "mean_reciprocal_rank",
        "sat_cec_calls_per_verified_recovery",
    },
    "results/ranking_ablation/critical_path_enhanced_ranking.csv": {
        "benchmark",
        "optimization",
        "optimized_node",
        "mapped_original_node",
        "mapping_category",
        "ranking_mode",
        "baseline_rank",
        "enhanced_rank",
        "functional_feature_evidence_level",
    },
}


def header(path: Path) -> set[str]:
    with path.open(newline="", encoding="utf-8") as fh:
        return set(next(csv.reader(fh), []))


def main() -> int:
    problems = []
    for rel_path, required in REQUIRED.items():
        path = ROOT / rel_path
        if not path.exists():
            problems.append(f"{rel_path}: missing")
            continue
        missing = sorted(required - header(path))
        if missing:
            problems.append(f"{rel_path}: missing columns {', '.join(missing)}")
    if problems:
        print("Functional ranking result check: STALE")
        for problem in problems:
            print(f"  - {problem}")
        return 1
    print("Functional ranking result check: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
