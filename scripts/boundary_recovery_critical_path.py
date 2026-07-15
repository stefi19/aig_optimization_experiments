#!/usr/bin/env python3
"""Estimate critical-path unresolved nodes enclosed by recovered regions."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "results" / "boundary_recovery" / "boundary_recovery_cases.csv"
CRITICAL = ROOT / "results" / "critical_path_mapping.csv"
OUT = ROOT / "results" / "boundary_recovery" / "critical_path_region_recovery.csv"
MD = ROOT / "results" / "boundary_recovery" / "critical_path_region_summary.md"


def split_nodes(value: object) -> set[str]:
    return {item for item in str(value or "").split(";") if item}


def build_rows(cases: list[dict[str, str]], critical: list[dict[str, str]]) -> list[dict[str, object]]:
    rows = []
    successful = [row for row in cases if str(row.get("recovery_success", "")).lower() == "true"]
    unresolved = [row for row in critical if row.get("mapping_category") == "unresolved"]
    for case in successful:
        region = split_nodes(case.get("region_nodes"))
        crit = [
            row for row in critical
            if row.get("benchmark") == case["benchmark"] and row.get("optimization") == case["optimization"]
        ]
        unresolved_case = [
            row for row in unresolved
            if row.get("benchmark") == case["benchmark"] and row.get("optimization") == case["optimization"]
        ]
        in_region = [row for row in crit if row.get("optimized_node") in region]
        unresolved_in_region = [row for row in unresolved_case if row.get("optimized_node") in region]
        rows.append(
            {
                "benchmark": case["benchmark"],
                "coi_name": case["coi_name"],
                "optimization": case["optimization"],
                "anchor_mode": case["anchor_mode"],
                "critical_path_nodes_in_coi": len(region & {row.get("optimized_node") for row in crit}),
                "critical_path_nodes_in_extended_region": len(in_region),
                "previously_unresolved_nodes_enclosed": len(unresolved_in_region),
                "region_level_recovery_rate": (len(unresolved_in_region) / len(unresolved_case)) if len(unresolved_case) else 0.0,
                "interpretation": "enclosed by a formally anchored recovered region; not direct node equivalence",
            }
        )
    return rows


def write_summary(rows: list[dict[str, object]]) -> None:
    total = sum(int(row.get("previously_unresolved_nodes_enclosed", 0)) for row in rows)
    lines = [
        "# Critical-Path Region Recovery Summary",
        "",
        "This analysis asks whether unresolved critical-path nodes fall inside formally anchored recovered regions. It does not reclassify those nodes as direct correspondences.",
        "",
        f"- Previously unresolved critical-path nodes enclosed: {total}",
        "",
    ]
    if not rows:
        lines.append("No successful recovered regions were available for critical-path enclosure analysis.")
    else:
        lines.append(markdown_table(rows))
    MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    columns = [
        "benchmark",
        "coi_name",
        "optimization",
        "anchor_mode",
        "critical_path_nodes_in_coi",
        "critical_path_nodes_in_extended_region",
        "previously_unresolved_nodes_enclosed",
        "region_level_recovery_rate",
        "interpretation",
    ]
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def markdown_table(rows: list[dict[str, object]]) -> str:
    columns = list(rows[0])
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join(["---"] * len(columns)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(col, "")) for col in columns) + " |")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, default=CASES)
    parser.add_argument("--critical-path", type=Path, default=CRITICAL)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.cases.exists():
        raise SystemExit(f"missing boundary cases: {args.cases}")
    cases = read_csv(args.cases)
    critical = read_csv(args.critical_path) if args.critical_path.exists() else []
    rows = build_rows(cases, critical)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    write_csv(OUT, rows)
    write_summary(rows)
    print(f"Wrote critical-path region rows to {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
