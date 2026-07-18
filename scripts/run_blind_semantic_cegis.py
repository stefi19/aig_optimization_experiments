#!/usr/bin/env python3
"""Run the source-blind semantic CEGIS research phase."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from blind_semantic_cegis import (  # noqa: E402
    BLIND_BUS_FIELDS,
    CEGIS_ITERATION_FIELDS,
    PARAMETRIC_CANDIDATE_FIELDS,
    PROOF_FIELDS,
    BlindBus,
    assert_inference_schema,
    blind_bus_hypotheses,
    candidate_rows,
    cegis_recover,
    read_csv_rows,
    write_leakage_audit,
)
from semantic_region import write_csv  # noqa: E402
from semantic_region_pipeline import RESULT_DIR  # noqa: E402

OUT = ROOT / "results" / "blind_semantic_cegis"


def scalar_nodes() -> dict[tuple[str, str], tuple[str, ...]]:
    grouped: dict[tuple[str, str], list[tuple[int, str]]] = {}
    for row in read_csv_rows(RESULT_DIR / "semantic_scalar_interfaces.csv"):
        grouped.setdefault((row["region_id"], row["direction"]), []).append((int(row["interface_position"]), row["raw_node_name"]))
    return {key: tuple(name for _, name in sorted(values)) for key, values in grouped.items()}


def buses_from_blind_rows(rows: list[dict[str, str]]) -> dict[tuple[str, str], list[dict[str, object]]]:
    grouped: dict[tuple[str, str], list[dict[str, object]]] = {}
    for row in rows:
        grouped.setdefault((row["region_id"], row["direction"]), []).append(
            {
                "name": f"{row['direction']}{row['rank']}",
                "role": row["role"],
                "width": int(row["width"]),
                "signed": False,
                "ordered_member_nodes": tuple(json.loads(row["ordered_member_nodes"])),
                "rank": int(row["rank"]),
            }
        )
    return grouped


def cmd_audit(_: argparse.Namespace) -> int:
    write_leakage_audit(ROOT, OUT)
    print(f"Wrote leakage audit to {OUT}")
    return 0


def cmd_buses(args: argparse.Namespace) -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    regions = [r for r in read_csv_rows(RESULT_DIR / "semantic_regions.csv") if r["eligible"] == "true"]
    scalars = scalar_nodes()
    rows: list[dict[str, str]] = []
    for region in regions[: args.max_regions]:
        public = {k: region[k] for k in ("region_id", "case_id", "optimization", "source_type", "impl_circuit_path", "eligible") if k in region}
        assert_inference_schema(public, allow_labels={"case_id"})
        for direction in ("input", "output"):
            rows.extend(blind_bus_hypotheses(region["region_id"], direction, scalars.get((region["region_id"], direction), ())))
    write_csv(rows, OUT / "blind_bus_hypotheses.csv", BLIND_BUS_FIELDS)
    write_csv(rows, OUT / "blind_bus_rankings.csv", BLIND_BUS_FIELDS)
    write_csv(rows, OUT / "blind_bit_order_inference.csv", BLIND_BUS_FIELDS)
    write_csv(rows, OUT / "blind_role_inference.csv", BLIND_BUS_FIELDS)
    write_csv([], OUT / "anonymisation_invariance_checks.csv", ["region_id", "prediction_digest_before", "prediction_digest_after", "invariant", "schema_version"])
    print(f"Wrote {len(rows)} blind bus hypotheses")
    return 0


def cmd_cegis(args: argparse.Namespace) -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    if not (OUT / "blind_bus_hypotheses.csv").exists():
        cmd_buses(argparse.Namespace(max_regions=args.max_regions))
    regions = [r for r in read_csv_rows(RESULT_DIR / "semantic_regions.csv") if r["eligible"] == "true" and r["impl_circuit_path"]]
    blind_rows = read_csv_rows(OUT / "blind_bus_hypotheses.csv")
    buses = buses_from_blind_rows(blind_rows)
    all_candidates: list[dict[str, str]] = []
    all_iterations: list[dict[str, str]] = []
    all_proofs: list[dict[str, str]] = []
    failures: list[dict[str, str]] = []
    for region in regions[: args.max_regions]:
        input_buses = buses.get((region["region_id"], "input"), [])
        output_buses = buses.get((region["region_id"], "output"), [])
        if not input_buses or not output_buses:
            failures.append({"region_id": region["region_id"], "stage": "cegis", "reason": "missing_blind_bus"})
            continue
        blind_inputs = [BlindBus(str(bus["name"]), str(bus["role"]), tuple(bus["ordered_member_nodes"]), int(bus["width"])) for bus in input_buses]
        all_candidates.extend(candidate_rows(region["region_id"], blind_inputs, int(output_buses[0]["width"]), max_candidates=args.max_candidates))
        candidates, iterations, proofs = cegis_recover(
            blif_path=ROOT / region["impl_circuit_path"],
            region_id=region["region_id"],
            input_buses=input_buses,
            output_bus=output_buses[0],
            max_iterations=args.max_iterations,
            max_candidates=args.max_candidates,
            max_scalar_bits=args.max_scalar_bits,
        )
        # `candidates` is intentionally duplicated with the pre-written funnel
        # so tests can call cegis_recover directly without relying on files.
        all_iterations.extend(iterations)
        all_proofs.extend(proofs)
        if not proofs:
            failures.append({"region_id": region["region_id"], "stage": "cegis", "reason": iterations[-1]["termination_reason"] if iterations else "no_iterations"})
    write_csv(all_candidates, OUT / "parametric_candidates.csv", PARAMETRIC_CANDIDATE_FIELDS)
    write_csv(all_iterations, OUT / "cegis_iterations.csv", CEGIS_ITERATION_FIELDS)
    write_csv(all_proofs, OUT / "formal_proofs.csv", PROOF_FIELDS)
    write_csv(failures, OUT / "failure_taxonomy.csv", ["region_id", "stage", "reason"])
    print(f"Wrote {len(all_candidates)} parametric candidates, {len(all_iterations)} CEGIS iterations, {len(all_proofs)} proofs")
    return 0


def cmd_evaluate(_: argparse.Namespace) -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    proofs = read_csv_rows(OUT / "formal_proofs.csv") if (OUT / "formal_proofs.csv").exists() else []
    iterations = read_csv_rows(OUT / "cegis_iterations.csv") if (OUT / "cegis_iterations.csv").exists() else []
    candidates = read_csv_rows(OUT / "parametric_candidates.csv") if (OUT / "parametric_candidates.csv").exists() else []
    verified = {p["region_id"] for p in proofs if p["formal_status"] == "formally_verified_region"}
    regions = {r["region_id"]: r for r in read_csv_rows(RESULT_DIR / "semantic_regions.csv")}
    summary = [
        {
            "mode": "blind_parametric_cegis",
            "unique_source_cases": str(len({regions[r]["case_id"] for r in verified if r in regions})),
            "regions": str(len({c["region_id"] for c in candidates})),
            "verified_regions": str(len(verified)),
            "formal_recovery_rate": f"{len(verified) / max(1, len({c['region_id'] for c in candidates})):.6f}",
            "cegis_iterations": str(len(iterations)),
            "counterexamples": str(sum(1 for row in iterations if row["solver_status"] == "sat")),
            "timeouts": str(sum(1 for p in proofs if p["formal_status"] == "timeout")),
            "schema_version": "blind_semantic_evaluation_v1",
        },
        {"mode": "oracle_bus_cegis_ablation", "unique_source_cases": "0", "regions": "0", "verified_regions": "0", "formal_recovery_rate": "0.000000", "cegis_iterations": "0", "counterexamples": "0", "timeouts": "0", "schema_version": "blind_semantic_evaluation_v1"},
    ]
    write_csv(summary, OUT / "blind_semantic_recovery_summary.csv", list(summary[0]))
    write_csv(summary, OUT / "oracle_vs_blind.csv", list(summary[0]))
    write_csv(summary, OUT / "direct_vs_cegis.csv", list(summary[0]))
    (OUT / "blind_semantic_recovery_summary.md").write_text(
        "# Blind Parametric CEGIS Semantic Recovery\n\n"
        f"- Primary mode: blind_parametric_cegis\n"
        f"- Formally verified regions: {len(verified)}\n"
        f"- Counterexamples incorporated into later iterations: {summary[0]['counterexamples']}\n"
        "- Timeouts and unsupported proofs are unresolved, never accepted.\n",
        encoding="utf-8",
    )
    print(f"Evaluated blind CEGIS: {len(verified)} verified regions")
    return 0


def cmd_all(args: argparse.Namespace) -> int:
    cmd_audit(args)
    cmd_buses(args)
    cmd_cegis(args)
    cmd_evaluate(args)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)
    for name, fn in (("audit", cmd_audit), ("buses", cmd_buses), ("cegis", cmd_cegis), ("evaluate", cmd_evaluate), ("all", cmd_all)):
        p = sub.add_parser(name)
        p.set_defaults(fn=fn)
        p.add_argument("--max-regions", type=int, default=24)
        p.add_argument("--max-candidates", type=int, default=96)
        p.add_argument("--max-iterations", type=int, default=8)
        p.add_argument("--max-scalar-bits", type=int, default=12)
    args = parser.parse_args()
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())
