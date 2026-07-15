#!/usr/bin/env python3
"""Validate generated semantic-recovery benchmark manifests."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULT_DIR = ROOT / "results" / "semantic_recovery"

MANIFEST = RESULT_DIR / "semantic_benchmark_manifest.csv"
VARIANTS = RESULT_DIR / "semantic_benchmark_variants.csv"
SUMMARY = RESULT_DIR / "semantic_benchmark_summary.md"

MANIFEST_FIELDS = [
    "case_id",
    "family",
    "operator",
    "expression",
    "input_buses",
    "output_buses",
    "input_widths",
    "output_widths",
    "signedness",
    "truncation",
    "extension_mode",
    "constants",
    "control_inputs",
    "source_rtl",
    "source_blif",
    "exact_blif_available",
    "expected_rtl_cost",
    "ground_truth_region",
    "ground_truth_boundary",
    "generation_seed",
    "schema_version",
]

VARIANT_FIELDS = [
    "case_id",
    "flow",
    "source_blif",
    "variant_blif",
    "status",
    "abc_command",
    "runtime_seconds",
    "message",
]

REQUIRED_FAMILIES = {"arithmetic", "control", "boolean", "comparison", "bitmanip"}
REQUIRED_WIDTHS = {2, 3, 4, 6, 8, 12, 16}
VALID_VARIANT_STATUSES = {
    "generated",
    "skipped_rtl_only",
    "skipped_variant_too_large",
    "skipped_no_abc",
    "failed",
}


def read_rows(path: Path, expected_fields: list[str]) -> tuple[list[dict[str, str]], list[str]]:
    problems: list[str] = []
    if not path.exists():
        return [], [f"{path.relative_to(ROOT)} is missing"]
    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        if reader.fieldnames != expected_fields:
            problems.append(
                f"{path.relative_to(ROOT)} has unstable header {reader.fieldnames}; expected {expected_fields}"
            )
        return list(reader), problems


def check_json_field(row: dict[str, str], field: str, problems: list[str]) -> object | None:
    try:
        return json.loads(row[field])
    except (json.JSONDecodeError, KeyError) as exc:
        problems.append(f"{row.get('case_id', '<unknown>')}: invalid JSON field {field}: {exc}")
        return None


def validate_manifest(rows: list[dict[str, str]]) -> list[str]:
    problems: list[str] = []
    ids: set[str] = set()
    families: set[str] = set()
    widths: set[int] = set()
    exact_blif_count = 0
    for row in rows:
        case_id = row["case_id"]
        if case_id in ids:
            problems.append(f"duplicate case_id {case_id}")
        ids.add(case_id)
        families.add(row["family"])
        input_widths = check_json_field(row, "input_widths", problems)
        check_json_field(row, "output_widths", problems)
        check_json_field(row, "ground_truth_region", problems)
        boundary = check_json_field(row, "ground_truth_boundary", problems)
        if isinstance(input_widths, dict):
            widths.update(int(width) for width in input_widths.values())
        rtl = ROOT / row["source_rtl"]
        if not rtl.exists():
            problems.append(f"{case_id}: source_rtl does not exist: {row['source_rtl']}")
        exact = row["exact_blif_available"]
        if exact not in {"true", "false"}:
            problems.append(f"{case_id}: exact_blif_available must be true/false")
        if exact == "true":
            exact_blif_count += 1
            source_blif = ROOT / row["source_blif"]
            if not source_blif.exists():
                problems.append(f"{case_id}: source_blif does not exist: {row['source_blif']}")
        if isinstance(boundary, dict):
            if not boundary.get("flat_inputs") or not boundary.get("flat_outputs"):
                problems.append(f"{case_id}: ground_truth_boundary lacks flat inputs/outputs")
    missing_families = REQUIRED_FAMILIES - families
    if missing_families:
        problems.append(f"missing semantic families: {sorted(missing_families)}")
    missing_widths = REQUIRED_WIDTHS - widths
    if missing_widths:
        problems.append(f"missing requested widths: {sorted(missing_widths)}")
    if exact_blif_count == 0:
        problems.append("no exact source BLIF cases generated")
    return problems


def validate_variants(rows: list[dict[str, str]], case_ids: set[str]) -> list[str]:
    problems: list[str] = []
    for row in rows:
        case_id = row["case_id"]
        if case_id not in case_ids:
            problems.append(f"variant references unknown case_id {case_id}")
        if row["status"] not in VALID_VARIANT_STATUSES:
            problems.append(f"{case_id}/{row['flow']}: invalid status {row['status']}")
        if row["status"] == "generated":
            path = ROOT / row["variant_blif"]
            if not path.exists():
                problems.append(f"{case_id}/{row['flow']}: generated variant missing {row['variant_blif']}")
        try:
            float(row["runtime_seconds"])
        except ValueError:
            problems.append(f"{case_id}/{row['flow']}: runtime_seconds is not numeric")
    return problems


def main() -> int:
    problems: list[str] = []
    manifest_rows, header_problems = read_rows(MANIFEST, MANIFEST_FIELDS)
    problems.extend(header_problems)
    variant_rows, header_problems = read_rows(VARIANTS, VARIANT_FIELDS)
    problems.extend(header_problems)
    if SUMMARY.exists() is False:
        problems.append(f"{SUMMARY.relative_to(ROOT)} is missing")
    if manifest_rows:
        problems.extend(validate_manifest(manifest_rows))
    if variant_rows and manifest_rows:
        problems.extend(validate_variants(variant_rows, {row["case_id"] for row in manifest_rows}))
    if problems:
        print("Semantic benchmark check: FAILED")
        for problem in problems:
            print(f"  - {problem}")
        return 1
    print("Semantic benchmark check: OK")
    print(f"  cases: {len(manifest_rows)}")
    print(f"  variant rows: {len(variant_rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
