#!/usr/bin/env python3
"""Validate historical provenance/eligibility correction artifacts."""

from __future__ import annotations

import argparse
import csv
import sys
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "results" / "provenance_eligibility_audit"

REQUIRED = {
    "historical_denominator_audit.csv": {"historical_result_file", "historical_row_id", "target_id", "source_artifact_available", "optimized_artifact_available", "target_node_available", "current_eligibility", "corrected_denominator_category", "correction_reason"},
    "historical_denominator_summary.csv": {"denominator", "historical_rows", "corrected_category", "eligible_rows"},
    "claim_audit.csv": {"file", "line", "matched_claim", "corrected_status"},
    "provenance_reconstruction.csv": {"target_id", "source_artifact", "optimized_artifact", "reconstruction_status", "proof_status", "reason"},
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    errors: list[str] = []
    tables: dict[str, list[dict[str, str]]] = {}
    for name, required in REQUIRED.items():
        path = args.output_dir / name
        if not path.exists():
            errors.append(f"missing required file: {name}")
            continue
        with path.open(newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            rows = list(reader)
        missing = required - set(reader.fieldnames or [])
        if missing:
            errors.append(f"{name} missing columns {sorted(missing)}")
        tables[name] = rows
    if errors:
        return _fail(errors)

    audit = tables["historical_denominator_audit.csv"]
    if not audit:
        errors.append("historical audit is empty")
    files = Counter(row["historical_result_file"] for row in audit)
    if files.get("results/active_source_counterpart_refactoring/development_results.csv") != 56:
        errors.append("active-source 56-row denominator missing or changed")
    if files.get("results/cross_netlist_cut_transplantation/development_results.csv") != 56:
        errors.append("cross-netlist 56-row denominator missing or changed")
    if files.get("results/semantic_grafting/semantic_graft_funnel.csv") != 46:
        errors.append("semantic graft 46-row denominator missing or changed")

    recon = tables["provenance_reconstruction.csv"]
    recon_counts = Counter(row["reconstruction_status"] for row in recon)
    if recon_counts.get("missing_optimized_artifact", 0) != 36:
        errors.append(f"expected 36 missing optimized-artifact historical rows, saw {recon_counts.get('missing_optimized_artifact', 0)}")
    if recon_counts.get("provenance_reconstructed_exact", 0) != 20:
        errors.append(f"expected 20 exact reconstructed output-side rows, saw {recon_counts.get('provenance_reconstructed_exact', 0)}")

    for row in audit:
        if row["current_eligibility"] == "eligible" and (
            row["source_artifact_available"] != "true"
            or row["optimized_artifact_available"] != "true"
            or row["target_node_available"] != "true"
            or row["cec_status"] != "equivalent"
        ):
            errors.append(f"eligible row without complete provenance/proof: {row['historical_row_id']}")
        if row["current_eligibility"] == "ineligible" and not row["correction_reason"]:
            errors.append(f"ineligible row lacks correction reason: {row['historical_row_id']}")

    summary_total = sum(int(row["historical_rows"]) for row in tables["historical_denominator_summary.csv"])
    if summary_total != len(audit):
        errors.append(f"summary/raw denominator mismatch: {summary_total} != {len(audit)}")

    if errors:
        return _fail(errors)
    print(
        "Provenance eligibility audit validated: "
        f"{len(audit)} historical rows, "
        f"{recon_counts.get('missing_optimized_artifact', 0)} provenance-incomplete, "
        f"{recon_counts.get('provenance_reconstructed_exact', 0)} reconstructed diagnostics"
    )
    return 0


def _fail(errors: list[str]) -> int:
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
