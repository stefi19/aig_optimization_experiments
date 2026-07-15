#!/usr/bin/env python3
"""Validate extended-boundary result schemas and identity regression."""

from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "results" / "extended_boundary_search"

REQUIRED = {
    "extended_boundary_cases.csv": {
        "case_id",
        "anchor_mode",
        "search_mode",
        "validation_profile",
        "success",
        "contains_original_coi",
        "valid_ebi_cut",
        "valid_ebo_cut",
        "incoming_bypass_count",
        "outgoing_bypass_count",
        "all_boundary_nodes_formally_anchored",
        "cycle_free",
        "whole_design_boundary",
        "original_ebi_exact_match",
        "original_ebo_exact_match",
        "original_region_exact_match",
        "classification",
    },
    "search_strategy_comparison.csv": {"benchmark", "optimization", "anchor_mode", "search_mode", "successes", "success_rate"},
    "remaining_failure_analysis.csv": {"case_id", "old_failure_reason", "classification", "success"},
    "anchor_usage.csv": {"anchor_mode", "search_mode", "selected_sat_cec_anchor_count"},
    "search_budget_statistics.csv": {"anchor_mode", "search_mode", "total_search_states", "max_search_states"},
}


def main() -> int:
    for name, cols in REQUIRED.items():
        path = OUT_DIR / name
        if not path.exists():
            raise SystemExit(f"missing {path}")
        with path.open(newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            missing = cols - set(reader.fieldnames or [])
            if missing:
                raise SystemExit(f"{name} missing columns: {sorted(missing)}")
            rows = list(reader)
            if name == "extended_boundary_cases.csv" and not rows:
                raise SystemExit("extended_boundary_cases.csv is empty")
    identity_path = ROOT / "results" / "boundary_recovery_semantics" / "identity_exact_match_results.csv"
    with identity_path.open(newline="", encoding="utf-8") as fh:
        identity = list(csv.DictReader(fh))
    if len(identity) != 14:
        raise SystemExit(f"expected 14 identity rows, found {len(identity)}")
    for row in identity:
        if row.get("top_level_classification") != "success":
            raise SystemExit(f"identity row failed: {row.get('case_id')}")
        if row.get("boundary_extension_ratio") not in {"0", "0.0"}:
            raise SystemExit(f"identity row has nonzero extension: {row.get('case_id')}")
        for col in ["ebi_exact_match", "ebo_exact_match", "region_exact_match"]:
            if row.get(col) != "True":
                raise SystemExit(f"identity row has false {col}: {row.get('case_id')}")
    print("Extended-boundary result check: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
