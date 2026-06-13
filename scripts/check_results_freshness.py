#!/usr/bin/env python3
"""
Check whether checked-in/generated result CSVs match the current analysis schema.

This is intentionally lightweight: it only reads CSV headers and a few metadata
fields.  If it reports stale files, re-run `python3 analyze_blif_matches.py`
after generating variants.
"""

from __future__ import annotations

import csv
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

sys.path.insert(0, str(ROOT))
from analyze_blif_matches import infer_benchmark_family


REQUIRED_COLUMNS = {
    "results/summary_metrics.csv": {
        "benchmark",
        "optimization",
        "simulation_mode",
        "pattern_count",
        "is_formal_exact_mode",
        "has_internal_nodes",
        "signature_match_on_patterns",
        "formal_truth_table_matches",
        "preserved_signature_fraction",
        "optimized_signature_coverage",
        "disappeared_fraction",
        "novel_fraction",
    },
    "results/top_candidates.csv": {
        "benchmark",
        "optimization",
        "optimized_node",
        "original_candidate",
        "is_exact_signature_match",
        "signature_match_on_patterns",
        "formal_truth_table_match",
        "pattern_count",
        "is_formal_exact_mode",
    },
}


def read_header(path: Path) -> list[str]:
    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.reader(fh)
        return next(reader, [])


def check_required_columns(rel_path: str, required: set[str]) -> list[str]:
    path = ROOT / rel_path
    if not path.exists():
        return [f"{rel_path}: missing file"]

    header = set(read_header(path))
    missing = sorted(required - header)
    if missing:
        return [
            f"{rel_path}: missing current-schema column(s): {', '.join(missing)}"
        ]
    return []


def check_family_metadata() -> list[str]:
    rel_path = "results/summary_metrics.csv"
    path = ROOT / rel_path
    if not path.exists():
        return []

    problems: list[str] = []
    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            benchmark = row.get("benchmark", "")
            recorded = row.get("benchmark_family", "")
            expected = infer_benchmark_family(benchmark)
            if recorded == "unknown" and expected != "unknown":
                problems.append(
                    f"{rel_path}: stale benchmark_family for {benchmark!r} "
                    f"(recorded unknown, current code infers {expected!r})"
                )
                if len(problems) >= 5:
                    problems.append(
                        f"{rel_path}: more stale benchmark_family rows omitted"
                    )
                    break
    return problems


def main() -> int:
    problems: list[str] = []
    for rel_path, required in REQUIRED_COLUMNS.items():
        problems.extend(check_required_columns(rel_path, required))
    problems.extend(check_family_metadata())

    if problems:
        print("Result freshness check: STALE")
        for problem in problems:
            print(f"  - {problem}")
        print("\nRegenerate with:")
        print("  python3 analyze_blif_matches.py")
        print("  python3 select_sat_candidates.py")
        return 1

    print("Result freshness check: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
