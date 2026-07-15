#!/usr/bin/env python3
"""Validate boundary-recovery diagnosis output schemas."""

from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED = {
    "results/boundary_recovery_diagnosis/boundary_failure_taxonomy.csv": {
        "case_id",
        "failure_stage",
        "failure_reason",
        "last_successful_stage",
        "recovery_success",
    },
    "results/boundary_recovery_diagnosis/boundary_identity_baseline.csv": {
        "case_id",
        "optimization",
        "recovery_success",
        "boundary_extension_ratio",
    },
    "results/boundary_recovery_diagnosis/boundary_anchor_coverage.csv": {
        "global_anchor_density",
        "coi_anchor_density",
        "formal_all_added_relevant_anchors",
    },
    "results/boundary_recovery_diagnosis/boundary_anchor_mode_differential.csv": {
        "success_delta",
        "differential_classification",
        "selected_sat_cec_anchor_count",
    },
    "results/boundary_recovery_diagnosis/boundary_diagnosis_summary.md": set(),
}


def header(path: Path) -> set[str]:
    with path.open(newline="", encoding="utf-8") as fh:
        return set(next(csv.reader(fh), []))


def main() -> int:
    problems = []
    for rel, required in REQUIRED.items():
        path = ROOT / rel
        if not path.exists():
            problems.append(f"{rel}: missing")
            continue
        if path.suffix == ".csv":
            missing = required - header(path)
            if missing:
                problems.append(f"{rel}: missing columns {', '.join(sorted(missing))}")
    if problems:
        print("Boundary diagnosis result check: STALE")
        for problem in problems:
            print(f"  - {problem}")
        return 1
    print("Boundary diagnosis result check: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
