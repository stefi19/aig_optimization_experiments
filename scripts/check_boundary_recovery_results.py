#!/usr/bin/env python3
"""Validate boundary-recovery result schemas."""

from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED = {
    "results/boundary_recovery/boundary_recovery_cases.csv": {
        "benchmark",
        "coi_name",
        "optimization",
        "anchor_mode",
        "recovery_success",
        "cut_valid",
        "cycle_free",
        "boundary_extension_ratio",
        "evidence_level",
        "failure_reason",
    },
    "results/boundary_recovery/boundary_recovery_by_anchor_mode.csv": {
        "anchor_mode",
        "cases",
        "recovery_success_count",
        "recovery_success_rate",
        "mean_boundary_extension_ratio",
    },
    "results/boundary_recovery/critical_path_region_recovery.csv": {
        "benchmark",
        "coi_name",
        "optimization",
        "anchor_mode",
        "previously_unresolved_nodes_enclosed",
        "interpretation",
    },
}


def read_header(path: Path) -> set[str]:
    with path.open(newline="", encoding="utf-8") as fh:
        return set(next(csv.reader(fh), []))


def main() -> int:
    problems = []
    for rel_path, required in REQUIRED.items():
        path = ROOT / rel_path
        if not path.exists():
            problems.append(f"{rel_path}: missing")
            continue
        missing = sorted(required - read_header(path))
        if missing:
            problems.append(f"{rel_path}: missing columns {', '.join(missing)}")
    if problems:
        print("Boundary recovery result check: STALE")
        for problem in problems:
            print(f"  - {problem}")
        return 1
    print("Boundary recovery result check: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
