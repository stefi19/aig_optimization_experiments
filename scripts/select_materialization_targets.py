#!/usr/bin/env python3
"""Select unmatched optimized-side targets for anchored-cut materialization."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from anchored_cut_enumeration import invert_anchor_map  # noqa: E402
from boundary_anchor_map import load_anchor_map  # noqa: E402
from boundary_graph import CircuitGraph  # noqa: E402
from boundary_semantics import original_path, variant_path, write_csv  # noqa: E402
from materialization_targets import select_targets_from_extended_failures, target_to_row  # noqa: E402

OUT = ROOT / "results" / "materialized_correspondence"
EXTENDED = ROOT / "results" / "extended_boundary_search" / "extended_boundary_cases.csv"

COLUMNS = [
    "case_id",
    "benchmark",
    "optimization",
    "coi_name",
    "target_impl_node",
    "target_role",
    "distance_to_failed_frontier",
    "target_level",
    "target_fanin_count",
    "target_fanout_count",
    "target_support_size",
    "selection_reason",
    "target_rank",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-targets-per-case", type=int, default=16)
    parser.add_argument("--output-dir", type=Path, default=OUT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    keys = _failed_keys(EXTENDED)
    impl_graphs: dict[tuple[str, str], CircuitGraph] = {}
    inverse_nodes: dict[tuple[str, str], set[str]] = {}
    for benchmark, optimization in sorted(keys):
        spec_path = original_path(benchmark)
        impl_path = variant_path(benchmark, optimization)
        if not spec_path.exists() or not impl_path.exists():
            continue
        spec = CircuitGraph.from_blif(spec_path)
        impl = CircuitGraph.from_blif(impl_path)
        anchors = load_anchor_map(
            benchmark,
            optimization,
            "formal_all",
            results_dir=ROOT / "results",
            spec_inputs=spec.inputs,
            impl_inputs=impl.inputs,
            spec_outputs=spec.outputs,
            impl_outputs=impl.outputs,
        )
        impl_graphs[(benchmark, optimization)] = impl
        inverse_nodes[(benchmark, optimization)] = set(invert_anchor_map(anchors.anchors))
    targets = select_targets_from_extended_failures(
        EXTENDED,
        impl_graphs,
        inverse_nodes,
        max_targets_per_case=args.max_targets_per_case,
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(args.output_dir / "materialization_targets.csv", [target_to_row(t) for t in targets], COLUMNS)
    print(f"Wrote materialization targets: {len(targets)}")
    return 0


def _failed_keys(path: Path) -> set[tuple[str, str]]:
    with path.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    return {
        (r["benchmark"], r["optimization"])
        for r in rows
        if r.get("anchor_mode") == "formal_all"
        and r.get("search_mode") == "cost_guided"
        and str(r.get("success")).lower() != "true"
    }


if __name__ == "__main__":
    raise SystemExit(main())
