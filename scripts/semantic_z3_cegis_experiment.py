#!/usr/bin/env python3
"""Run Z3-backed blind/oracle semantic CEGIS experiments."""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from blind_semantic_cegis import BlindBus, candidate_rows, read_csv_rows  # noqa: E402
from scripts.run_blind_semantic_cegis import OUT, buses_from_blind_rows, cmd_buses  # noqa: E402
from semantic_ast import expr_from_tree  # noqa: E402
from semantic_region import write_csv  # noqa: E402
from semantic_region_pipeline import RESULT_DIR  # noqa: E402
from semantic_simulation import gate_output_value  # noqa: E402
from semantic_z3_validation import validate_candidate_z3  # noqa: E402

ITER_FIELDS = [
    "mode", "candidate_id", "region_id", "case_id", "operator", "width", "iteration",
    "examples_before", "examples_after", "template_family", "candidate_expression",
    "synthesis_result", "verification_result", "counterexample_assignment",
    "counterexample_reproduced", "synthesis_runtime", "verification_runtime",
    "cumulative_runtime", "termination_reason", "proof_backend", "proof_scope",
    "evidence_level", "schema_version",
]
PROOF_FIELDS = [
    "mode", "candidate_id", "region_id", "case_id", "operator", "width",
    "formal_backend", "proof_scope", "formal_status", "formal_evidence_level",
    "solver_result", "counterexample_available", "counterexample_assignment",
    "proof_runtime", "timeout", "unsupported_reason", "schema_version",
]
SUMMARY_FIELDS = ["mode", "unique_cases_attempted", "unique_cases_recovered", "regions_attempted", "regions_recovered", "width_12_or_16_attempted", "width_12_or_16_recovered", "iterations", "counterexamples", "timeouts", "schema_version"]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-regions", type=int, default=80)
    parser.add_argument("--max-candidates", type=int, default=160)
    parser.add_argument("--max-iterations", type=int, default=10)
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    cmd_buses(argparse.Namespace(max_regions=10_000))
    regions = _selected_regions(args.max_regions)
    blind_buses = buses_from_blind_rows(read_csv_rows(OUT / "blind_bus_hypotheses.csv"))
    oracle_buses = _oracle_buses()
    all_iter: list[dict[str, str]] = []
    all_proofs: list[dict[str, str]] = []
    for mode, bus_map in (("blind", blind_buses), ("oracle_bus", oracle_buses)):
        for region in regions:
            input_buses = bus_map.get((region["region_id"], "input"), [])
            output_buses = bus_map.get((region["region_id"], "output"), [])
            if not input_buses or not output_buses:
                continue
            iterations, proof = _run_region(mode, region, input_buses, output_buses[0], args)
            all_iter.extend(iterations)
            if proof:
                all_proofs.append(proof)
    write_csv(all_iter, OUT / "z3_cegis_iterations.csv", ITER_FIELDS)
    write_csv(all_proofs, OUT / "z3_formal_proofs.csv", PROOF_FIELDS)
    summary = _summary(all_iter, all_proofs)
    write_csv(summary, OUT / "z3_blind_oracle_comparison.csv", SUMMARY_FIELDS)
    write_csv(_by_width(all_iter, all_proofs), OUT / "z3_recovery_by_width.csv", ["mode", "width", "regions_attempted", "regions_recovered", "iterations", "counterexamples", "schema_version"])
    write_csv(_by_operator(all_iter, all_proofs), OUT / "z3_recovery_by_operator.csv", ["mode", "operator", "regions_attempted", "regions_recovered", "iterations", "counterexamples", "schema_version"])
    (OUT / "z3_cegis_summary.md").write_text(_summary_md(summary, all_iter, all_proofs), encoding="utf-8")
    print(f"Wrote Z3 CEGIS iterations={len(all_iter)} proofs={len(all_proofs)}")
    return 0


def _selected_regions(max_regions: int) -> list[dict[str, str]]:
    manifest = {r["case_id"]: r for r in read_csv_rows(RESULT_DIR / "semantic_benchmark_manifest.csv")}
    rows = [r for r in read_csv_rows(RESULT_DIR / "semantic_regions.csv") if r["eligible"] == "true" and r["impl_circuit_path"]]
    def width(row: dict[str, str]) -> int:
        return max([int(v) for v in json.loads(manifest[row["case_id"]]["output_widths"]).values()] or [0])
    rows.sort(key=lambda r: (0 if width(r) in {12, 16} else 1, r["case_id"], r["optimization"], r["source_type"]))
    return rows[:max_regions]


def _oracle_buses() -> dict[tuple[str, str], list[dict[str, object]]]:
    scalars: dict[tuple[str, str], set[str]] = defaultdict(set)
    for row in read_csv_rows(RESULT_DIR / "semantic_scalar_interfaces.csv"):
        scalars[(row["region_id"], row["direction"])].add(row["raw_node_name"])
    by_case: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    for row in read_csv_rows(RESULT_DIR / "semantic_bus_ground_truth.csv"):
        by_case[(row["case_id"], row["direction"])].append(row)
    regions = read_csv_rows(RESULT_DIR / "semantic_regions.csv")
    result: dict[tuple[str, str], list[dict[str, object]]] = {}
    for region in regions:
        for direction in ("input", "output"):
            available = scalars.get((region["region_id"], direction), set())
            buses = []
            for bus in by_case.get((region["case_id"], direction), []):
                members = tuple(node for node in json.loads(bus["member_signal_names"]) if node in available)
                if members:
                    buses.append({"name": bus["bus_name"], "role": bus["role"], "width": len(members), "signed": bus["signedness"] == "signed", "ordered_member_nodes": members, "rank": len(buses) + 1})
            if buses:
                result[(region["region_id"], direction)] = buses
    return result


def _run_region(mode: str, region: dict[str, str], input_buses: list[dict[str, object]], output_bus: dict[str, object], args: argparse.Namespace) -> tuple[list[dict[str, str]], dict[str, str] | None]:
    blind_inputs = [BlindBus(str(b["name"]), str(b.get("role", "data_operand")), tuple(b.get("ordered_member_nodes", ())), int(b["width"]), bool(b.get("signed", False))) for b in input_buses]
    candidates = candidate_rows(region["region_id"], blind_inputs, int(output_bus["width"]), max_candidates=args.max_candidates)
    examples = [{str(b["name"]): 0 for b in input_buses}]
    rows: list[dict[str, str]] = []
    rejected: set[str] = set()
    cumulative = 0.0
    for iteration in range(1, args.max_iterations + 1):
        synth_start = time.perf_counter()
        selected = None
        for candidate in candidates:
            if candidate["candidate_id"] in rejected:
                continue
            expr = expr_from_tree(json.loads(candidate["expression_json"]))
            if all(gate_output_value(__import__("analyze_blif_matches").parse_blif(ROOT / region["impl_circuit_path"]), input_buses, output_bus, ex) == expr.eval(ex) for ex in examples):
                selected = (candidate, expr)
                break
        synth_runtime = time.perf_counter() - synth_start
        if selected is None:
            rows.append(_iter_row(mode, region, "", "", iteration, len(examples), len(examples), "", "unsat", "not_run", {}, "false", synth_runtime, 0, cumulative, "no_candidate_satisfies_examples", "unresolved"))
            return rows, None
        candidate, expr = selected
        proof = validate_candidate_z3(blif_path=ROOT / region["impl_circuit_path"], input_buses=input_buses, output_bus=output_bus, expr=expr, timeout_ms=5000)
        verify_runtime = float(proof["proof_runtime"])
        cumulative += synth_runtime + verify_runtime
        if proof["formal_status"] == "formally_verified_region":
            rows.append(_iter_row(mode, region, candidate["candidate_id"], candidate["template_family"], iteration, len(examples), len(examples), candidate["canonical_form"], "sat", "unsat", {}, "true", synth_runtime, verify_runtime, cumulative, "equivalence_proven", "formal_smt"))
            return rows, _proof_row(mode, region, candidate["candidate_id"], proof)
        if proof["formal_status"] == "disproven" and proof["counterexample_available"] == "true":
            cex = json.loads(proof["counterexample_assignment"])
            examples.append({str(k): int(v) for k, v in cex.items()})
            rejected.add(candidate["candidate_id"])
            rows.append(_iter_row(mode, region, candidate["candidate_id"], candidate["template_family"], iteration, len(examples)-1, len(examples), candidate["canonical_form"], "sat", "sat", cex, proof["counterexample_reproduced"], synth_runtime, verify_runtime, cumulative, "counterexample_added", "formal_smt"))
            continue
        rows.append(_iter_row(mode, region, candidate["candidate_id"], candidate["template_family"], iteration, len(examples), len(examples), candidate["canonical_form"], "sat", proof["solver_result"], {}, "false", synth_runtime, verify_runtime, cumulative, proof["unsupported_reason"] or "unresolved", "unresolved"))
        return rows, _proof_row(mode, region, candidate["candidate_id"], proof)
    return rows, None


def _iter_row(mode, region, cid, family, iteration, before, after, expr, synth, verify, cex, reproduced, sr, vr, cr, reason, evidence):
    return {"mode": mode, "candidate_id": cid, "region_id": region["region_id"], "case_id": region["case_id"], "operator": region["operator"], "width": _region_width(region), "iteration": str(iteration), "examples_before": str(before), "examples_after": str(after), "template_family": family, "candidate_expression": expr, "synthesis_result": synth, "verification_result": verify, "counterexample_assignment": json.dumps(cex, sort_keys=True, separators=(",", ":")), "counterexample_reproduced": reproduced, "synthesis_runtime": f"{sr:.6f}", "verification_runtime": f"{vr:.6f}", "cumulative_runtime": f"{cr:.6f}", "termination_reason": reason, "proof_backend": "z3", "proof_scope": "region", "evidence_level": evidence, "schema_version": "z3_cegis_iteration_v1"}


def _proof_row(mode, region, cid, proof):
    return {"mode": mode, "candidate_id": cid, "region_id": region["region_id"], "case_id": region["case_id"], "operator": region["operator"], "width": _region_width(region), "formal_backend": "z3", "proof_scope": proof["proof_scope"], "formal_status": proof["formal_status"], "formal_evidence_level": proof["formal_evidence_level"], "solver_result": proof["solver_result"], "counterexample_available": proof["counterexample_available"], "counterexample_assignment": proof["counterexample_assignment"], "proof_runtime": proof["proof_runtime"], "timeout": proof["timeout"], "unsupported_reason": proof["unsupported_reason"], "schema_version": "z3_cegis_proof_v1"}


def _region_width(region):
    return str(max(1, len(json.loads(region["observable_outputs"]))))


def _summary(iterations, proofs):
    rows = []
    for mode in ("blind", "oracle_bus"):
        it = [r for r in iterations if r["mode"] == mode]
        pr = [r for r in proofs if r["mode"] == mode and r["formal_status"] == "formally_verified_region"]
        attempted = {r["case_id"] for r in it}
        recovered = {r["case_id"] for r in pr}
        wide_attempted = {r["case_id"] for r in it if int(r["width"]) in {12, 16}}
        wide_recovered = {r["case_id"] for r in pr if int(r["width"]) in {12, 16}}
        rows.append({"mode": mode, "unique_cases_attempted": str(len(attempted)), "unique_cases_recovered": str(len(recovered)), "regions_attempted": str(len({r["region_id"] for r in it})), "regions_recovered": str(len({r["region_id"] for r in pr})), "width_12_or_16_attempted": str(len(wide_attempted)), "width_12_or_16_recovered": str(len(wide_recovered)), "iterations": str(len(it)), "counterexamples": str(sum(1 for r in it if r["verification_result"] == "sat")), "timeouts": str(sum(1 for r in proofs if r["mode"] == mode and r["formal_status"] == "timeout")), "schema_version": "z3_blind_oracle_summary_v1"})
    return rows


def _by_width(iterations, proofs):
    return _grouped(iterations, proofs, "width")


def _by_operator(iterations, proofs):
    return _grouped(iterations, proofs, "operator")


def _grouped(iterations, proofs, key):
    rows = []
    proof_regions = {(r["mode"], r["region_id"]) for r in proofs if r["formal_status"] == "formally_verified_region"}
    groups = sorted({(r["mode"], r[key]) for r in iterations})
    for mode, value in groups:
        it = [r for r in iterations if r["mode"] == mode and r[key] == value]
        rows.append({"mode": mode, key: value, "regions_attempted": str(len({r["region_id"] for r in it})), "regions_recovered": str(len({r["region_id"] for r in it if (mode, r["region_id"]) in proof_regions})), "iterations": str(len(it)), "counterexamples": str(sum(1 for r in it if r["verification_result"] == "sat")), "schema_version": "z3_grouped_recovery_v1"})
    return rows


def _summary_md(summary, iterations, proofs):
    return "# Z3-Backed Blind vs Oracle CEGIS\n\n" + "\n".join(f"- {r['mode']}: {r['unique_cases_recovered']}/{r['unique_cases_attempted']} unique cases recovered, {r['width_12_or_16_recovered']}/{r['width_12_or_16_attempted']} wide cases recovered" for r in summary) + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
