#!/usr/bin/env python3
"""Run exact identity recovery under repaired canonical COI semantics."""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from boundary_graph import CircuitGraph  # noqa: E402
from boundary_semantics import (  # noqa: E402
    SEMANTICS_DIR,
    identity_anchor_map,
    join_nodes,
    load_canonical_manifest,
    original_path,
    recover_semantic_boundary,
    write_csv,
)
from coi_model import validate_coi  # noqa: E402

OUT = SEMANTICS_DIR / "identity_exact_match_results.csv"
FAIL = SEMANTICS_DIR / "identity_failure_details.csv"
SUMMARY = SEMANTICS_DIR / "identity_summary.md"

COLS = [
    "case_id",
    "benchmark",
    "coi_name",
    "eligible",
    "executable",
    "structurally_valid",
    "attempted",
    "algorithmic_success",
    "top_level_classification",
    "boundary_extension_ratio",
    "ebi_exact_match",
    "ebo_exact_match",
    "region_exact_match",
    "missing_ebi_nodes",
    "extra_ebi_nodes",
    "missing_ebo_nodes",
    "extra_ebo_nodes",
    "missing_region_nodes",
    "extra_region_nodes",
    "failure_reason",
]


def main() -> int:
    rows = []
    for coi in load_canonical_manifest():
        path = original_path(coi.benchmark)
        case_id = f"{coi.benchmark}|{coi.coi_name}|identity_exact"
        if not path.exists():
            rows.append(base_row(case_id, coi, False, False, False, False, False, "infrastructure_skip", "missing_spec_circuit"))
            continue
        graph = CircuitGraph.from_blif(path)
        validation = validate_coi(graph, coi)
        if not validation.valid:
            rows.append(base_row(case_id, coi, True, True, False, False, False, "invalid_coi", ";".join(validation.errors)))
            continue
        result = recover_semantic_boundary(graph, coi, identity_anchor_map(graph))
        rows.append(
            {
                **base_row(case_id, coi, True, True, True, True, result.success, "success" if result.success else "algorithmic_failure", result.failure_reason),
                "boundary_extension_ratio": result.boundary_extension_ratio,
                "ebi_exact_match": result.ebi_exact_match,
                "ebo_exact_match": result.ebo_exact_match,
                "region_exact_match": result.region_exact_match,
                "missing_ebi_nodes": join_nodes(result.missing_ebi_nodes),
                "extra_ebi_nodes": join_nodes(result.extra_ebi_nodes),
                "missing_ebo_nodes": join_nodes(result.missing_ebo_nodes),
                "extra_ebo_nodes": join_nodes(result.extra_ebo_nodes),
                "missing_region_nodes": join_nodes(result.missing_region_nodes),
                "extra_region_nodes": join_nodes(result.extra_region_nodes),
            }
        )
    write_csv(OUT, rows, COLS)
    failures = [row for row in rows if row["top_level_classification"] != "success"]
    write_csv(FAIL, failures, COLS)
    SUMMARY.write_text(summary(rows), encoding="utf-8")
    success = sum(str(row["top_level_classification"]) == "success" for row in rows)
    print(f"Fixed identity recovery: {success}/{len(rows)} successful")
    if failures:
        print("Identity gate failed")
        return 1
    return 0


def base_row(case_id, coi, eligible, executable, valid, attempted, success, classification, reason):
    return {
        "case_id": case_id,
        "benchmark": coi.benchmark,
        "coi_name": coi.coi_name,
        "eligible": eligible,
        "executable": executable,
        "structurally_valid": valid,
        "attempted": attempted,
        "algorithmic_success": success,
        "top_level_classification": classification,
        "boundary_extension_ratio": "",
        "ebi_exact_match": False,
        "ebo_exact_match": False,
        "region_exact_match": False,
        "missing_ebi_nodes": "",
        "extra_ebi_nodes": "",
        "missing_ebo_nodes": "",
        "extra_ebo_nodes": "",
        "missing_region_nodes": "",
        "extra_region_nodes": "",
        "failure_reason": reason,
    }


def summary(rows):
    n = len(rows)
    success = sum(row["top_level_classification"] == "success" for row in rows)
    zero = sum(row["top_level_classification"] == "success" and float(row["boundary_extension_ratio"]) == 0.0 for row in rows)
    ebi = sum(str(row["ebi_exact_match"]).lower() == "true" for row in rows)
    ebo = sum(str(row["ebo_exact_match"]).lower() == "true" for row in rows)
    region = sum(str(row["region_exact_match"]).lower() == "true" for row in rows)
    reasons = Counter(row["failure_reason"] for row in rows if row["top_level_classification"] != "success")
    lines = [
        "# Fixed Identity Boundary-Recovery Summary",
        "",
        f"- Eligible valid identity cases: {n}",
        f"- Successes: {success}",
        f"- Zero-extension cases: {zero}",
        f"- Exact EBI matches: {ebi}",
        f"- Exact EBO matches: {ebo}",
        f"- Exact region matches: {region}",
        "",
        "## Failure Reasons",
        "",
    ]
    if reasons:
        lines.extend(f"- {reason}: {count}" for reason, count in sorted(reasons.items()))
    else:
        lines.append("No identity failures.")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
