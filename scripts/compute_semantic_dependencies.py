#!/usr/bin/env python3
"""Compute semantic dependency matrices and geometry features."""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from semantic_dependency import (
    SEMANTIC_DEPENDENCY_BY_OPT_FIELDS,
    SEMANTIC_DEPENDENCY_FAILURE_FIELDS,
    SEMANTIC_DEPENDENCY_FEATURE_FIELDS,
    compute_dependency_matrices,
    feature_row,
    matrices_json,
)
from semantic_region import write_csv
from semantic_region_pipeline import RESULT_DIR, read_csv


def scalar_nodes() -> dict[tuple[str, str], tuple[str, ...]]:
    grouped: dict[tuple[str, str], list[tuple[int, str]]] = defaultdict(list)
    for row in read_csv(RESULT_DIR / "semantic_scalar_interfaces.csv"):
        grouped[(row["region_id"], row["direction"])].append((int(row["interface_position"]), row["raw_node_name"]))
    return {key: tuple(name for _, name in sorted(values)) for key, values in grouped.items()}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sample-count", type=int, default=128)
    parser.add_argument("--seed", type=int, default=41)
    parser.add_argument("--enable-formal-dependency", action="store_true")
    args = parser.parse_args()

    regions = [row for row in read_csv(RESULT_DIR / "semantic_regions.csv") if row["eligible"] == "true"]
    nodes = scalar_nodes()
    matrices = []
    features = []
    failures = []
    for region in regions:
        inputs = nodes.get((region["region_id"], "input"), tuple())
        outputs = nodes.get((region["region_id"], "output"), tuple())
        if not inputs or not outputs or not region["impl_circuit_path"]:
            failures.append({
                "region_id": region["region_id"],
                "case_id": region["case_id"],
                "optimization": region["optimization"],
                "source_type": region["source_type"],
                "stage": "dependency",
                "reason": "missing_interface_or_circuit",
            })
            continue
        start = time.perf_counter()
        dep = compute_dependency_matrices(
            region_id=region["region_id"],
            blif_path=ROOT / region["impl_circuit_path"],
            input_nodes=inputs,
            output_nodes=outputs,
            sample_count=args.sample_count,
            seed=args.seed,
            enable_formal_dependency=args.enable_formal_dependency,
        )
        runtime = time.perf_counter() - start
        matrices.append(dep)
        features.append(feature_row(region, dep, runtime))

    by_opt = []
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in features:
        grouped[row["optimization"]].append(row)
    for opt, rows in sorted(grouped.items()):
        by_opt.append({
            "optimization": opt,
            "eligible_rows": str(sum(1 for r in regions if r["optimization"] == opt)),
            "complete_dependency_matrices": str(len(rows)),
            "mean_dependency_density": f"{sum(float(r['dependency_density']) for r in rows) / max(1, len(rows)):.6f}",
            "mean_diagonal_concentration": f"{sum(float(r['diagonal_concentration']) for r in rows) / max(1, len(rows)):.6f}",
            "mean_lower_triangularity": f"{sum(float(r['lower_triangularity']) for r in rows) / max(1, len(rows)):.6f}",
            "mean_bandwidth": f"{sum(float(r['bandwidth']) for r in rows) / max(1, len(rows)):.6f}",
            "mean_runtime_seconds": f"{sum(float(r['runtime_seconds']) for r in rows) / max(1, len(rows)):.6f}",
        })

    (RESULT_DIR / "semantic_dependency_matrices.json").write_text(matrices_json(matrices), encoding="utf-8")
    write_csv(features, RESULT_DIR / "semantic_dependency_features.csv", SEMANTIC_DEPENDENCY_FEATURE_FIELDS)
    write_csv(by_opt, RESULT_DIR / "semantic_dependency_by_optimization.csv", SEMANTIC_DEPENDENCY_BY_OPT_FIELDS)
    if failures:
        existing = []
        path = RESULT_DIR / "semantic_bus_dependency_failures.csv"
        if path.exists():
            existing = read_csv(path)
        write_csv(existing + failures, path, SEMANTIC_DEPENDENCY_FAILURE_FIELDS)
    print(f"Wrote {len(features)} semantic dependency feature rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
