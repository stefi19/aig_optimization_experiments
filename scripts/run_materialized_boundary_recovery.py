#!/usr/bin/env python3
"""Compare boundary recovery with and without proven materialized anchors."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from boundary_anchor_map import load_anchor_map  # noqa: E402
from boundary_graph import CircuitGraph  # noqa: E402
from boundary_semantics import load_canonical_manifest, original_path, variant_path, write_csv  # noqa: E402
from extended_boundary_search import SearchConfig, result_to_row, search_valid_extended_boundary  # noqa: E402

OUT = ROOT / "results" / "materialized_correspondence"
EXTENDED = ROOT / "results" / "extended_boundary_search" / "extended_boundary_cases.csv"

COLUMNS = [
    "case_id",
    "anchor_mode",
    "search_mode",
    "baseline_success",
    "materialized_success",
    "proven_materialized_anchor_count",
    "usable_materialized_anchor_count",
    "selected_materialized_anchor_count",
    "boundary_valid",
    "contains_original_coi",
    "valid_ebi_cut",
    "valid_ebo_cut",
    "incoming_bypass_count",
    "outgoing_bypass_count",
    "cycle_free",
    "whole_design_boundary",
    "extension_node_count",
    "extension_ratio",
    "runtime_seconds",
    "failure_reason",
    "benchmark",
    "optimization",
    "coi_name",
    "newly_recovered_boundary",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--search-mode", default="cost_guided", choices=["cost_guided"])
    parser.add_argument("--output-dir", type=Path, default=OUT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    baseline = _baseline_failures(EXTENDED)
    cois = {(c.benchmark, c.coi_name): c for c in load_canonical_manifest()}
    proven = _read_rows(args.output_dir / "proven_materialized_anchors.csv")
    proven_by_key: dict[tuple[str, str], list[dict[str, str]]] = {}
    for row in proven:
        proven_by_key.setdefault((row["benchmark"], row["optimization"]), []).append(row)
    rows = []
    usage = []
    for old in baseline:
        coi = cois[(old["benchmark"], old["coi_name"])]
        spec_path = original_path(coi.benchmark)
        impl_path = variant_path(coi.benchmark, old["optimization"])
        spec = CircuitGraph.from_blif(spec_path)
        impl = CircuitGraph.from_blif(impl_path)
        anchors = load_anchor_map(
            coi.benchmark,
            old["optimization"],
            "formal_plus_materialized",
            results_dir=ROOT / "results",
            spec_inputs=spec.inputs,
            impl_inputs=impl.inputs,
            spec_outputs=spec.outputs,
            impl_outputs=impl.outputs,
        )
        result = search_valid_extended_boundary(spec, impl, coi, anchors, SearchConfig())
        selected = [
            anchors.selected_for(node)
            for node in [*result.ebi, *result.ebo]
            if anchors.selected_for(node) and anchors.selected_for(node).mapping_category == "formal_materialized_anchor"
        ]
        key = (old["benchmark"], old["optimization"])
        proven_count = len(proven_by_key.get(key, []))
        row = {
            "case_id": f"{old['benchmark']}|{old['coi_name']}|{old['optimization']}|formal_plus_materialized|cost_guided",
            "anchor_mode": "formal_plus_materialized",
            "search_mode": "cost_guided",
            "baseline_success": old["success"],
            "materialized_success": result.success,
            "proven_materialized_anchor_count": proven_count,
            "usable_materialized_anchor_count": 0,
            "selected_materialized_anchor_count": len(selected),
            "boundary_valid": result.success,
            "contains_original_coi": result.contains_original_coi,
            "valid_ebi_cut": result.valid_ebi_cut,
            "valid_ebo_cut": result.valid_ebo_cut,
            "incoming_bypass_count": len(result.incoming_bypass_edges),
            "outgoing_bypass_count": len(result.outgoing_bypass_edges),
            "cycle_free": result.cycle_free,
            "whole_design_boundary": result.whole_design_boundary,
            "extension_node_count": len(result.extension_nodes),
            "extension_ratio": result.extension_ratio,
            "runtime_seconds": f"{result.runtime_seconds:.6f}",
            "failure_reason": result.failure_reason,
            "benchmark": old["benchmark"],
            "optimization": old["optimization"],
            "coi_name": old["coi_name"],
            "newly_recovered_boundary": str(old["success"]).lower() != "true" and result.success,
        }
        rows.append(row)
        for anchor in proven_by_key.get(key, []):
            usage.append(
                {
                    "case_id": row["case_id"],
                    "benchmark": old["benchmark"],
                    "optimization": old["optimization"],
                    "coi_name": old["coi_name"],
                    "materialized_spec_node": anchor["materialized_spec_node"],
                    "target_impl_node": anchor["target_impl_node"],
                    "usable_for_boundary": False,
                    "selected_by_boundary": False,
                    "usage_reason": "additive_materialized_wire_is_not_reconnected_to_original_boundary_graph",
                }
            )
    write_csv(args.output_dir / "materialized_boundary_recovery.csv", rows, COLUMNS)
    write_csv(args.output_dir / "materialized_anchor_usage.csv", usage)
    print(f"Wrote materialized boundary recovery rows: {len(rows)}")
    return 0


def _baseline_failures(path: Path) -> list[dict[str, str]]:
    rows = _read_rows(path)
    return [
        row
        for row in rows
        if row.get("anchor_mode") == "formal_all"
        and row.get("search_mode") == "cost_guided"
        and str(row.get("success")).lower() != "true"
    ]


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


if __name__ == "__main__":
    raise SystemExit(main())
