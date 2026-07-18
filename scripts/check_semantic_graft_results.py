#!/usr/bin/env python3
"""Validate semantic graft evidence categories."""

from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "semantic_grafting"


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def main() -> int:
    path = OUT / "semantic_graft_funnel.csv"
    if not path.exists():
        print("missing semantic_graft_funnel.csv", file=sys.stderr)
        return 1
    problems = []
    for row in rows(path):
        if row["accepted"] == "true" and row["global_cec_status"] != "passed":
            problems.append(f"{row['graft_id']}: accepted without global CEC")
        if row["accepted"] != "true" and row["boundary_utility"] == "usable_frontier":
            problems.append(f"{row['graft_id']}: disconnected/unaccepted row labelled usable")
    attempts = OUT / "graft_placement_attempts.csv"
    if attempts.exists():
        with attempts.open(newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                if row["acceptance_status"] == "accepted" and row["graph_active"] != "true":
                    problems.append(f"{row['attempt_id']}: accepted without graph_active")
                if row["acceptance_status"] == "accepted" and row["global_cec_status"] not in {"passed", "not_applicable_contextual_scope"}:
                    problems.append(f"{row['attempt_id']}: accepted without required proof status")
    if problems:
        print("\n".join(problems), file=sys.stderr)
        return 1
    print("Semantic graft result checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
