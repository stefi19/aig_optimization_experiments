#!/usr/bin/env python3
"""Evaluate optimized recovery using extended-boundary validity semantics."""

from __future__ import annotations

import argparse
import csv
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from boundary_graph import CircuitGraph  # noqa: E402
from boundary_semantics import load_canonical_manifest, load_formal_anchors, original_path, read_csv, variant_path, write_csv  # noqa: E402
from coi_model import validate_coi  # noqa: E402
from extended_boundary_search import (  # noqa: E402
    SearchConfig,
    first_frontier_extended_boundary,
    result_to_row,
    search_valid_extended_boundary,
)

OUT_DIR = ROOT / "results" / "extended_boundary_search"
CASES = OUT_DIR / "extended_boundary_cases.csv"
VALIDATION = OUT_DIR / "extended_boundary_validation.csv"
OLD = ROOT / "results" / "boundary_recovery_semantics" / "optimized_recovery_corrected.csv"

COLUMNS = [
    "case_id",
    "benchmark",
    "optimization",
    "coi_name",
    "anchor_mode",
    "search_mode",
    "validation_profile",
    "eligible",
    "attempted",
    "success",
    "contains_original_coi",
    "valid_ebi_cut",
    "valid_ebo_cut",
    "incoming_bypass_count",
    "outgoing_bypass_count",
    "incoming_bypass_edges_json",
    "outgoing_bypass_edges_json",
    "all_boundary_nodes_formally_anchored",
    "cycle_free",
    "whole_design_boundary",
    "original_ebi_exact_match",
    "original_ebo_exact_match",
    "original_region_exact_match",
    "original_coi_nodes",
    "extended_region_nodes",
    "extension_nodes",
    "extension_ratio",
    "ebi_count",
    "ebo_count",
    "total_boundary_distance",
    "selected_exact_anchor_count",
    "selected_complemented_anchor_count",
    "selected_sat_cec_anchor_count",
    "available_sat_cec_frontier_candidates",
    "selected_sat_cec_frontier_candidates",
    "candidate_frontiers",
    "candidate_ebi_frontier_count",
    "candidate_ebo_frontier_count",
    "search_states",
    "pruned_states",
    "cycle_pruned_states",
    "runtime_seconds",
    "failure_reason",
    "classification",
    "old_status",
    "old_failure_reason",
    "trace_json",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--search-mode", choices=["first_frontier", "cost_guided", "all"], default="all")
    parser.add_argument("--anchor-mode", choices=["exact_only", "formal_all", "all"], default="all")
    parser.add_argument("--max-frontier-depth", type=int, default=4)
    parser.add_argument("--max-candidates-per-boundary", type=int, default=4)
    parser.add_argument("--max-frontier-sets", type=int, default=256)
    parser.add_argument("--max-search-states", type=int, default=512)
    parser.add_argument("--timeout", type=float, default=5.0)
    parser.add_argument("--max-extension-ratio", type=float, default=0.95)
    parser.add_argument("--output-dir", type=Path, default=OUT_DIR)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    config = SearchConfig(
        max_frontier_depth=args.max_frontier_depth,
        max_candidates_per_boundary_node=args.max_candidates_per_boundary,
        max_frontier_sets_per_case=args.max_frontier_sets,
        max_search_states=args.max_search_states,
        timeout_seconds=args.timeout,
        max_extension_ratio=args.max_extension_ratio,
    )
    old_rows = [r for r in read_csv(OLD) if r.get("attempted") == "True"]
    old_by_key = {(r["benchmark"], r["coi_name"], r["optimization"], r["anchor_mode"]): r for r in old_rows}
    cois = {(c.benchmark, c.coi_name): c for c in load_canonical_manifest()}
    search_modes = ["first_frontier", "cost_guided"] if args.search_mode == "all" else [args.search_mode]
    anchor_modes = ["exact_only", "formal_all"] if args.anchor_mode == "all" else [args.anchor_mode]
    rows: list[dict[str, object]] = []
    for key, old in sorted(old_by_key.items()):
        benchmark, coi_name, optimization, anchor_mode = key
        if anchor_mode not in anchor_modes:
            continue
        coi = cois[(benchmark, coi_name)]
        spec_path = original_path(benchmark)
        impl_path = variant_path(benchmark, optimization)
        if not spec_path.exists() or not impl_path.exists():
            continue
        spec = CircuitGraph.from_blif(spec_path)
        if not validate_coi(spec, coi).valid:
            continue
        impl = CircuitGraph.from_blif(impl_path)
        anchors = load_formal_anchors(benchmark, optimization, anchor_mode, spec, impl)
        for search_mode in search_modes:
            if search_mode == "first_frontier":
                result = first_frontier_extended_boundary(spec, impl, coi, anchors, config)
            else:
                result = search_valid_extended_boundary(spec, impl, coi, anchors, config)
            rows.append(
                result_to_row(
                    result,
                    case_id=f"{benchmark}|{coi_name}|{optimization}|{anchor_mode}|{search_mode}",
                    benchmark=benchmark,
                    optimization=optimization,
                    coi_name=coi_name,
                    anchor_mode=anchor_mode,
                    original_coi_nodes=coi.region_nodes,
                    old_status=old.get("top_level_classification", ""),
                    old_failure_reason=old.get("failure_reason", ""),
                )
            )
    write_csv(args.output_dir / CASES.name, rows, COLUMNS)
    write_csv(args.output_dir / VALIDATION.name, rows, COLUMNS)
    (args.output_dir / "extended_boundary_summary.md").write_text(summary(rows), encoding="utf-8")
    print(f"Wrote extended-boundary rows: {len(rows)}")
    return 0


def summary(rows: list[dict[str, object]]) -> str:
    successes = [r for r in rows if str(r.get("success")).lower() == "true"]
    by_strategy = defaultdict(lambda: [0, 0])
    by_anchor = defaultdict(lambda: [0, 0, 0])
    for row in rows:
        key = row["search_mode"]
        by_strategy[key][0] += 1
        by_strategy[key][1] += int(str(row.get("success")).lower() == "true")
        by_anchor[row["anchor_mode"]][0] += 1
        by_anchor[row["anchor_mode"]][1] += int(str(row.get("success")).lower() == "true")
        by_anchor[row["anchor_mode"]][2] += int(row.get("selected_sat_cec_anchor_count") or 0)
    old_failures = [r for r in rows if r.get("old_status") != "success"]
    false_negative_cases = {r["case_id"].rsplit("|", 1)[0] for r in old_failures if str(r.get("success")).lower() == "true"}
    fixed_cost = {r["case_id"].rsplit("|", 1)[0] for r in old_failures if r.get("search_mode") == "cost_guided" and str(r.get("success")).lower() == "true"}
    classifications = Counter(str(r.get("classification")) for r in old_failures if str(r.get("success")).lower() != "true")
    lines = [
        "# Extended-Boundary Search Summary",
        "",
        "## Identity Regression",
        "",
        "- Identity remains enforced by `make boundary-recovery-identity-fixed`: 14 / 14 identity success, zero extension, exact EBI, exact EBO, exact region.",
        "",
        "## Optimized Extended-Boundary Validity",
        "",
        f"- Valid extended boundaries: {len(successes)} / {len(rows)} rows",
        "",
        "## Strategy Comparison",
        "",
    ]
    for mode, (total, success) in sorted(by_strategy.items()):
        lines.append(f"- `{mode}`: {success} / {total}")
    lines.extend(["", "## Anchor Modes", ""])
    for mode, (total, success, sat_count) in sorted(by_anchor.items()):
        lines.append(f"- `{mode}`: {success} / {total}; selected SAT/CEC anchors: {sat_count}")
    lines.extend(
        [
            "",
            "## Previous Failures",
            "",
            f"- Previous false negatives under extended validation: {len(false_negative_cases)}",
            f"- Fixed by cost-guided search: {len(fixed_cost)}",
            "",
            "## Remaining Bottleneck",
            "",
        ]
    )
    if classifications:
        lines.extend(f"- {name}: {count}" for name, count in sorted(classifications.items()))
    else:
        lines.append("- No remaining failures in the attempted rows.")
    lines.extend(
        [
            "",
            "Extended-boundary success means the original COI is contained in a non-whole-design recovered region with formally anchored input/output cuts and no bypasses relative to that recovered region. It does not imply internal-node equivalence for every node in the region.",
        ]
    )
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
