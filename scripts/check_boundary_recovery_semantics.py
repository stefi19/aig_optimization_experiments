#!/usr/bin/env python3
"""Validate repaired boundary-recovery semantics outputs and identity gate."""

from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEM = ROOT / "results" / "boundary_recovery_semantics"

REQUIRED = {
    "coi_repair_audit.csv": {"final_valid", "repair_action", "reason"},
    "coi_canonical_manifest.json": set(),
    "circuit_availability.csv": {"eligibility_status", "skip_reason"},
    "identity_exact_match_results.csv": {"top_level_classification", "ebi_exact_match", "ebo_exact_match", "region_exact_match"},
    "optimized_recovery_corrected.csv": {"attempted", "top_level_classification", "failure_reason"},
    "critical_path_coi_validation.csv": {"coi_valid", "invalid_reason", "segment_size"},
    "boundary_semantics_summary.md": set(),
}


def main() -> int:
    problems = []
    for name, cols in REQUIRED.items():
        path = SEM / name
        if not path.exists():
            problems.append(f"{name}: missing")
            continue
        if path.suffix == ".csv":
            with path.open(newline="", encoding="utf-8") as fh:
                header = set(next(csv.reader(fh), []))
            missing = cols - header
            if missing:
                problems.append(f"{name}: missing columns {', '.join(sorted(missing))}")
    identity = read_csv(SEM / "identity_exact_match_results.csv") if (SEM / "identity_exact_match_results.csv").exists() else []
    for row in identity:
        if row.get("top_level_classification") != "success":
            problems.append(f"identity failure: {row.get('case_id')} {row.get('failure_reason')}")
        if row.get("boundary_extension_ratio") not in {"0.0", "0"}:
            problems.append(f"nonzero identity extension: {row.get('case_id')}")
        for col in ["ebi_exact_match", "ebo_exact_match", "region_exact_match"]:
            if row.get(col) != "True":
                problems.append(f"identity {col} false: {row.get('case_id')}")
    if problems:
        print("Boundary semantics result check: STALE")
        for problem in problems:
            print(f"  - {problem}")
        return 1
    print("Boundary semantics result check: OK")
    return 0


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


if __name__ == "__main__":
    raise SystemExit(main())
