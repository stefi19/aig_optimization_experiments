#!/usr/bin/env python3
"""Schema and freshness checks for semantic-region Phase 2 outputs."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from semantic_interface import (
    SEMANTIC_BUS_GROUND_TRUTH_FIELDS,
    SEMANTIC_INTERFACE_ALIGNMENT_FIELDS,
    SEMANTIC_SCALAR_INTERFACE_FIELDS,
)
from semantic_region import SEMANTIC_REGION_FIELDS
from semantic_region_pipeline import BY_OPT_FIELDS, FAILURE_FIELDS, SOURCE_COMPARISON_FIELDS
from semantic_region_validation import SEMANTIC_REGION_VALIDATION_FIELDS

RESULT = ROOT / "results" / "semantic_recovery"

EXPECTED = {
    RESULT / "semantic_regions.csv": SEMANTIC_REGION_FIELDS,
    RESULT / "semantic_region_validation.csv": SEMANTIC_REGION_VALIDATION_FIELDS,
    RESULT / "semantic_scalar_interfaces.csv": SEMANTIC_SCALAR_INTERFACE_FIELDS,
    RESULT / "semantic_bus_ground_truth.csv": SEMANTIC_BUS_GROUND_TRUTH_FIELDS,
    RESULT / "semantic_interface_alignment.csv": SEMANTIC_INTERFACE_ALIGNMENT_FIELDS,
    RESULT / "semantic_region_source_comparison.csv": SOURCE_COMPARISON_FIELDS,
    RESULT / "semantic_region_by_optimization.csv": BY_OPT_FIELDS,
    RESULT / "semantic_region_failures.csv": FAILURE_FIELDS,
}


def read_rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        return list(reader.fieldnames or []), list(reader)


def main() -> int:
    problems: list[str] = []
    for path, fields in EXPECTED.items():
        if not path.exists():
            problems.append(f"missing {path.relative_to(ROOT)}")
            continue
        header, rows = read_rows(path)
        if header != fields:
            problems.append(f"{path.relative_to(ROOT)} header mismatch")
        if not rows:
            problems.append(f"{path.relative_to(ROOT)} has no rows")
    for path in [
        RESULT / "semantic_regions.json",
        RESULT / "semantic_scalar_interfaces.json",
        RESULT / "semantic_bus_ground_truth.json",
        RESULT / "regions" / "semantic_ground_truth_regions.json",
        RESULT / "regions" / "semantic_output_cone_regions.json",
    ]:
        if not path.exists():
            problems.append(f"missing {path.relative_to(ROOT)}")
            continue
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            problems.append(f"{path.relative_to(ROOT)} invalid JSON: {exc}")
    summary = RESULT / "semantic_region_summary.md"
    if not summary.exists():
        problems.append("missing semantic_region_summary.md")
    elif "does not infer or recover high-level RTL expressions" not in summary.read_text(encoding="utf-8"):
        problems.append("summary lacks no-expression-recovery caveat")
    if problems:
        print("Semantic region check: FAILED")
        for problem in problems:
            print(f"  - {problem}")
        return 1
    print("Semantic region check: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
