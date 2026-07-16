#!/usr/bin/env python3
"""Extract exact truth tables for anchored cuts."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from analyze_blif_matches import parse_blif  # noqa: E402
from boundary_semantics import variant_path, write_csv  # noqa: E402
from cut_function_extraction import cut_function_to_row, extract_cut_truth_table  # noqa: E402

OUT = ROOT / "results" / "materialized_correspondence"
COLUMNS = [
    "case_id",
    "benchmark",
    "optimization",
    "coi_name",
    "cut_id",
    "target_impl_node",
    "truth_table",
    "truth_table_hash",
    "support_leaf_order",
    "local_cone_nodes",
    "local_cone_size",
    "extraction_backend",
    "extraction_status",
    "failure_reason",
    "runtime_seconds",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--exact-input-limit", type=int, default=12)
    parser.add_argument("--output-dir", type=Path, default=OUT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    cut_rows = _read_rows(args.output_dir / "anchored_cut_candidates.csv")
    nets = {}
    rows = []
    for cut in cut_rows:
        key = (cut["benchmark"], cut["optimization"])
        if key not in nets:
            nets[key] = parse_blif(variant_path(*key))
        fn = extract_cut_truth_table(
            nets[key],
            target_impl_node=cut["target_impl_node"],
            cut_id=cut["cut_id"],
            impl_leaf_nodes=tuple(filter(None, cut["impl_leaf_nodes"].split(";"))),
            exact_input_limit=args.exact_input_limit,
        )
        rows.append(cut_function_to_row(fn, case_id=cut["case_id"], benchmark=cut["benchmark"], optimization=cut["optimization"], coi_name=cut["coi_name"]))
    write_csv(args.output_dir / "cut_function_extraction.csv", rows, COLUMNS)
    print(f"Wrote cut-function extraction rows: {len(rows)}")
    return 0


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


if __name__ == "__main__":
    raise SystemExit(main())
