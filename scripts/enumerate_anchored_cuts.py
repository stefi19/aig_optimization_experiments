#!/usr/bin/env python3
"""Enumerate small optimized-side cuts whose leaves have formal anchors."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from anchored_cut_enumeration import cut_to_row, enumerate_anchored_cuts, invert_anchor_map  # noqa: E402
from boundary_anchor_map import load_anchor_map  # noqa: E402
from boundary_graph import CircuitGraph  # noqa: E402
from boundary_semantics import original_path, variant_path, write_csv  # noqa: E402

OUT = ROOT / "results" / "materialized_correspondence"

COLUMNS = [
    "case_id",
    "benchmark",
    "optimization",
    "coi_name",
    "cut_id",
    "target_impl_node",
    "cut_size",
    "impl_leaf_nodes",
    "spec_leaf_nodes",
    "leaf_mapping_categories",
    "leaf_polarities",
    "all_leaves_globally_formal",
    "cut_depth",
    "cut_support_size",
    "estimated_truth_table_cost",
    "cut_rank",
    "validation_status",
    "failure_reason",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-cut-size", type=int, default=3)
    parser.add_argument("--max-target-distance", type=int, default=4)
    parser.add_argument("--max-cuts-per-target", type=int, default=64)
    parser.add_argument("--output-dir", type=Path, default=OUT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    target_rows = _read_rows(args.output_dir / "materialization_targets.csv")
    rows: list[dict[str, object]] = []
    cache: dict[tuple[str, str], tuple[CircuitGraph, dict[str, object]]] = {}
    for target in target_rows:
        key = (target["benchmark"], target["optimization"])
        if key not in cache:
            spec_path = original_path(target["benchmark"])
            impl_path = variant_path(target["benchmark"], target["optimization"])
            spec = CircuitGraph.from_blif(spec_path)
            impl = CircuitGraph.from_blif(impl_path)
            anchors = load_anchor_map(
                target["benchmark"],
                target["optimization"],
                "formal_all",
                results_dir=ROOT / "results",
                spec_inputs=spec.inputs,
                impl_inputs=impl.inputs,
                spec_outputs=spec.outputs,
                impl_outputs=impl.outputs,
            )
            cache[key] = (impl, invert_anchor_map(anchors.anchors))
        impl, inverse = cache[key]
        cuts = enumerate_anchored_cuts(
            impl,
            target["target_impl_node"],
            inverse,
            max_cut_size=args.max_cut_size,
            max_depth=args.max_target_distance,
            max_cuts=args.max_cuts_per_target,
        )
        for cut in cuts:
            rows.append(cut_to_row(cut, case_id=target["case_id"], benchmark=target["benchmark"], optimization=target["optimization"], coi_name=target["coi_name"]))
    write_csv(args.output_dir / "anchored_cut_candidates.csv", rows, COLUMNS)
    write_csv(args.output_dir / "anchored_cut_validation.csv", rows, COLUMNS)
    print(f"Wrote anchored cut candidates: {len(rows)}")
    return 0


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


if __name__ == "__main__":
    raise SystemExit(main())
