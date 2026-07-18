#!/usr/bin/env python3
"""Cross-check exhaustive semantic proof and Z3 region miters."""

from __future__ import annotations

import argparse
import csv
import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from blind_semantic_cegis import read_csv_rows  # noqa: E402
from scripts.run_blind_semantic_cegis import OUT, buses_from_blind_rows  # noqa: E402
from semantic_ast import expr_from_tree  # noqa: E402
from semantic_formal_validation import FormalValidationConfig, validate_candidate_exhaustive  # noqa: E402
from semantic_region import write_csv  # noqa: E402
from semantic_region_pipeline import RESULT_DIR  # noqa: E402
from semantic_z3_validation import validate_candidate_z3  # noqa: E402

CROSSCHECK_FIELDS = [
    "candidate_id",
    "region_id",
    "case_id",
    "optimization",
    "output_width",
    "input_scalar_bits",
    "exhaustive_status",
    "z3_status",
    "verdict_agreement",
    "z3_counterexample_available",
    "z3_counterexample_reproduced",
    "exhaustive_runtime",
    "z3_runtime",
    "z3_version",
    "unsupported_reason",
    "schema_version",
]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-candidates-per-region", type=int, default=8)
    parser.add_argument("--max-scalar-bits", type=int, default=10)
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    if not (OUT / "blind_bus_hypotheses.csv").exists() or not (OUT / "parametric_candidates.csv").exists():
        print("Run make blind-semantic-cegis-all first", file=sys.stderr)
        return 1
    regions = {r["region_id"]: r for r in read_csv_rows(RESULT_DIR / "semantic_regions.csv") if r["eligible"] == "true"}
    buses = buses_from_blind_rows(read_csv_rows(OUT / "blind_bus_hypotheses.csv"))
    candidates = read_csv_rows(OUT / "parametric_candidates.csv")
    by_region: dict[str, list[dict[str, str]]] = {}
    for candidate in candidates:
        by_region.setdefault(candidate["region_id"], []).append(candidate)
    rows: list[dict[str, str]] = []
    for region_id, region_candidates in sorted(by_region.items()):
        region = regions.get(region_id)
        if not region or not region["impl_circuit_path"]:
            continue
        input_buses = buses.get((region_id, "input"), [])
        output_buses = buses.get((region_id, "output"), [])
        if not input_buses or not output_buses:
            continue
        scalar_bits = sum(int(bus["width"]) for bus in input_buses)
        if scalar_bits > args.max_scalar_bits:
            continue
        for candidate in region_candidates[: args.max_candidates_per_region]:
            expr = expr_from_tree(json.loads(candidate["expression_json"]))
            exhaustive = validate_candidate_exhaustive(
                blif_path=ROOT / region["impl_circuit_path"],
                input_buses=input_buses,
                output_bus=output_buses[0],
                expr=expr,
                config=FormalValidationConfig(max_scalar_bits=args.max_scalar_bits, timeout_seconds=10.0),
            )
            z3_result = validate_candidate_z3(
                blif_path=ROOT / region["impl_circuit_path"],
                input_buses=input_buses,
                output_bus=output_buses[0],
                expr=expr,
                timeout_ms=5000,
            )
            agreement = _same_verdict(exhaustive["formal_status"], z3_result["formal_status"])
            rows.append(
                {
                    "candidate_id": candidate["candidate_id"],
                    "region_id": region_id,
                    "case_id": region["case_id"],
                    "optimization": region["optimization"],
                    "output_width": candidate["width_constraints"].split("=")[-1],
                    "input_scalar_bits": str(scalar_bits),
                    "exhaustive_status": exhaustive["formal_status"],
                    "z3_status": z3_result["formal_status"],
                    "verdict_agreement": str(agreement).lower(),
                    "z3_counterexample_available": z3_result["counterexample_available"],
                    "z3_counterexample_reproduced": z3_result["counterexample_reproduced"],
                    "exhaustive_runtime": exhaustive["formal_runtime"],
                    "z3_runtime": z3_result["proof_runtime"],
                    "z3_version": z3_result["z3_version"],
                    "unsupported_reason": z3_result["unsupported_reason"],
                    "schema_version": "z3_exhaustive_crosscheck_v1",
                }
            )
    write_csv(rows, OUT / "z3_exhaustive_crosscheck.csv", CROSSCHECK_FIELDS)
    checked = len(rows)
    agreements = sum(1 for row in rows if row["verdict_agreement"] == "true")
    cex = [row for row in rows if row["z3_counterexample_available"] == "true"]
    reproduced = sum(1 for row in cex if row["z3_counterexample_reproduced"] == "true")
    runtimes = [float(row["z3_runtime"]) for row in rows if row["z3_runtime"]]
    summary = (
        "# Z3 vs Exhaustive Semantic Cross-Check\n\n"
        f"- Cases checked: {checked}\n"
        f"- Agreement count: {agreements}\n"
        f"- Agreement rate: {agreements / max(1, checked):.6f}\n"
        f"- Proven equivalent by Z3: {sum(1 for row in rows if row['z3_status'] == 'formally_verified_region')}\n"
        f"- Disproven by Z3: {sum(1 for row in rows if row['z3_status'] == 'disproven')}\n"
        f"- Validated counterexamples: {reproduced}/{len(cex)}\n"
        f"- Encoding failures/timeouts: {sum(1 for row in rows if row['z3_status'] in {'unsupported', 'timeout'})}\n"
        f"- Z3 runtime min/median/max: {_runtime_summary(runtimes)}\n"
    )
    (OUT / "z3_exhaustive_crosscheck_summary.md").write_text(summary, encoding="utf-8")
    if checked and agreements != checked:
        print("Z3/exhaustive disagreement detected", file=sys.stderr)
        return 1
    if len(cex) != reproduced:
        print("Z3 counterexample reproduction failure", file=sys.stderr)
        return 1
    print(f"Z3/exhaustive cross-check passed: {agreements}/{checked}")
    return 0


def _same_verdict(left: str, right: str) -> bool:
    equivalent = {"formally_verified_region"}
    disproven = {"disproven"}
    return (left in equivalent and right in equivalent) or (left in disproven and right in disproven)


def _runtime_summary(values: list[float]) -> str:
    if not values:
        return "n/a"
    return f"{min(values):.6f}/{statistics.median(values):.6f}/{max(values):.6f}"


if __name__ == "__main__":
    raise SystemExit(main())
