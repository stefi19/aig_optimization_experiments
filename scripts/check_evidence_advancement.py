#!/usr/bin/env python3
"""Validate evidence-advancement artifacts and their evidence-level boundaries."""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "evidence_advancement"
SCHEMA = "evidence_advancement_v1"


def main() -> int:
    errors: list[str] = []
    counterpart = _rows("source_blind_counterpart_inference.csv", errors)
    rewrites = _rows("compact_interface_rewrite_attempts.csv", errors)
    grammar = _rows("grammar_completeness_certificates.csv", errors)
    rtl = _rows("rtl_corpus_manifest.csv", errors)
    odc = _rows("odc_placement_accounting.csv", errors)
    locality = _rows("locality_proof_objects.csv", errors)
    summary = _rows("evidence_advancement_summary.csv", errors)

    _check_schema(counterpart + rewrites + grammar + rtl + odc + locality + summary, errors)
    _check_counterpart(counterpart, errors)
    _check_rewrites(rewrites, errors)
    _check_grammar(grammar, errors)
    _check_rtl(rtl, errors)
    _check_odc(odc, errors)
    _check_locality(locality, errors)
    _check_summary(summary, counterpart, rewrites, grammar, rtl, odc, locality, errors)

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("Evidence advancement artifacts validated")
    return 0


def _check_schema(rows: list[dict[str, str]], errors: list[str]) -> None:
    for row in rows:
        if row.get("schema_version") != SCHEMA:
            errors.append(f"schema drift in row: {row}")


def _check_counterpart(rows: list[dict[str, str]], errors: list[str]) -> None:
    if len(rows) != 56:
        errors.append(f"source-blind counterpart denominator drifted: {len(rows)} != 56")
    semantic_only = [r for r in rows if r.get("promoted_evidence_level") == "semantic_counterpart_only"]
    graph_active = [r for r in rows if r.get("graph_active_recovery") == "true"]
    if len(semantic_only) != 20:
        errors.append(f"source-blind semantic-only count drifted: {len(semantic_only)} != 20")
    if graph_active:
        bad = [r for r in graph_active if r.get("promoted_evidence_level") != "graph_active_recovery"]
        if bad:
            errors.append("graph-active counterpart rows are not labeled graph_active_recovery")
    if len(graph_active) != 0:
        errors.append(f"source-blind graph-active count drifted from the honest current value: {len(graph_active)} != 0")


def _check_rewrites(rows: list[dict[str, str]], errors: list[str]) -> None:
    if len(rows) != 48:
        errors.append(f"compact-interface rewrite denominator drifted: {len(rows)} != 48")
    compact = [r for r in rows if r.get("compact_interface") == "true"]
    emitted = [r for r in rows if r.get("rewrite_emitted") == "true"]
    graph_active = [r for r in rows if r.get("graph_active") == "true"]
    new_boundary = [r for r in rows if r.get("new_boundary") == "true"]
    if len(compact) != 31:
        errors.append(f"compact exact-interface count drifted: {len(compact)} != 31")
    if len(emitted) != 31:
        errors.append(f"rewrite artifact emission count drifted: {len(emitted)} != 31")
    if len(graph_active) != 22:
        errors.append(f"graph-active rewrite count drifted: {len(graph_active)} != 22")
    if len(new_boundary) != 22:
        errors.append(f"CEC-backed new-boundary count drifted: {len(new_boundary)} != 22")
    for row in rows:
        if row.get("compact_interface") == "true" and row.get("rewrite_emitted") != "true":
            errors.append(f"compact row did not emit a rewrite artifact: {row.get('stable_target_id')}")
        if row.get("rewrite_emitted") == "true":
            artifact = ROOT / row.get("rewrite_artifact", "")
            if not row.get("rewrite_artifact") or not artifact.exists():
                errors.append(f"emitted rewrite artifact missing: {row.get('stable_target_id')}")
        if row.get("new_boundary") == "true":
            if row.get("graph_active") != "true" or row.get("rewrite_emitted") != "true":
                errors.append(f"new-boundary row lacks emitted graph-active rewrite: {row.get('stable_target_id')}")
            if row.get("source_vs_rewrite_cec") != "equivalent" or row.get("rewrite_vs_optimized_cec") != "equivalent":
                errors.append(f"new-boundary row lacks both CEC scopes: {row.get('stable_target_id')}")
            if row.get("promotion") != "graph_active_cec_recovery":
                errors.append(f"new-boundary row has wrong promotion: {row.get('stable_target_id')}")
        if row.get("rewrite_emitted") != "true" and row.get("global_cec_status") != "not_claimed":
            errors.append(f"non-emitted rewrite row claims CEC status: {row.get('stable_target_id')}")


def _check_grammar(rows: list[dict[str, str]], errors: list[str]) -> None:
    expected_complete = {("blind", "sign_extend"), ("blind", "zero_extend"), ("oracle_bus", "sign_extend"), ("oracle_bus", "zero_extend")}
    complete = {(r.get("mode", ""), r.get("operator", "")) for r in rows if r.get("bounded_grammar_complete_for_attempted_rows") == "true"}
    if complete != expected_complete:
        errors.append(f"bounded grammar complete groups drifted: {sorted(complete)} != {sorted(expected_complete)}")
    for row in rows:
        attempted = int(row.get("regions_attempted", "0"))
        recovered = int(row.get("regions_recovered", "0"))
        is_complete = row.get("bounded_grammar_complete_for_attempted_rows") == "true"
        if is_complete != (attempted > 0 and attempted == recovered):
            errors.append(f"grammar completeness mismatch for {row.get('mode')}:{row.get('operator')}")
        if row.get("claim_scope") != "attempted_region_rows_only":
            errors.append(f"grammar completeness overclaims scope for {row.get('mode')}:{row.get('operator')}")
        if not is_complete and not row.get("limitation"):
            errors.append(f"incomplete grammar row lacks limitation for {row.get('mode')}:{row.get('operator')}")
        if row.get("proof_backend") != "z3" or not row.get("proof_hash"):
            errors.append(f"grammar row lacks Z3 proof hash for {row.get('mode')}:{row.get('operator')}")


def _check_rtl(rows: list[dict[str, str]], errors: list[str]) -> None:
    if len(rows) != 3:
        errors.append(f"RTL corpus manifest drifted: {len(rows)} != 3")
    for row in rows:
        if row.get("redistributable") != "true" or row.get("license") != "CC0-1.0":
            errors.append(f"RTL corpus row is not redistributable CC0: {row.get('design_id')}")
        rtl_path = ROOT / row.get("rtl_path", "")
        if not rtl_path.exists():
            errors.append(f"RTL source missing: {row.get('rtl_path')}")
            continue
        if _sha256(rtl_path) != row.get("rtl_sha256"):
            errors.append(f"RTL hash mismatch: {row.get('rtl_path')}")
        metadata = json.loads(row.get("source_location_metadata", "{}"))
        if metadata.get("module") != row.get("design_id") or metadata.get("source") != row.get("rtl_path"):
            errors.append(f"RTL source-location metadata mismatch: {row.get('design_id')}")
        status = row.get("lowering_status")
        if status == "lowered_blif":
            lowered = ROOT / row.get("lowered_blif", "")
            if not lowered.exists():
                errors.append(f"lowered BLIF missing for {row.get('design_id')}")
            if row.get("evidence_level") != "rtl_lowered_with_tool":
                errors.append(f"lowered RTL row has wrong evidence level: {row.get('design_id')}")
        elif status == "tool_missing":
            if row.get("lowered_blif"):
                errors.append(f"tool-missing RTL row has lowered BLIF: {row.get('design_id')}")
            if row.get("evidence_level") != "rtl_corpus_pinned":
                errors.append(f"tool-missing RTL row has wrong evidence level: {row.get('design_id')}")
        else:
            errors.append(f"unexpected RTL lowering status for {row.get('design_id')}: {status}")


def _check_odc(rows: list[dict[str, str]], errors: list[str]) -> None:
    if len(rows) != 10:
        errors.append(f"ODC anchor accounting denominator drifted: {len(rows)} != 10")
    for row in rows:
        if row.get("proof_status") != "proven_odc_valid":
            errors.append(f"ODC row is not a proven contextual anchor: {row.get('case_id')}")
        if row.get("graph_active") == "true" and row.get("global_cec_status") != "equivalent":
            errors.append(f"ODC graph-active row lacks global CEC: {row.get('case_id')}")
    graph_active = [r for r in rows if r.get("graph_active") == "true"]
    if len(graph_active) != 0:
        errors.append(f"ODC graph-active placement count drifted from current claim: {len(graph_active)} != 0")


def _check_locality(rows: list[dict[str, str]], errors: list[str]) -> None:
    if len(rows) != 57:
        errors.append(f"locality proof-object count drifted: {len(rows)} != 57")
    source_tables = {
        "results/necessity_first_target_discovery/formal_locality_results.csv": _source_index(
            "results/necessity_first_target_discovery/formal_locality_results.csv", "stable_target_id", errors
        ),
        "results/formal_locality_barriers/input_exact_minimum_certificates.csv": _source_index(
            "results/formal_locality_barriers/input_exact_minimum_certificates.csv", "target_id", errors
        ),
    }
    for row in rows:
        if row.get("machine_checkable") != "true":
            errors.append(f"proof-object row is not machine-checkable: {row.get('proof_id')}")
        path = ROOT / row.get("proof_object_path", "")
        if not path.exists():
            errors.append(f"proof object missing: {row.get('proof_object_path')}")
            continue
        if _sha256(path) != row.get("proof_object_sha256"):
            errors.append(f"proof-object hash mismatch: {row.get('proof_id')}")
        proof = json.loads(path.read_text(encoding="utf-8"))
        if proof.get("schema_version") != SCHEMA or proof.get("proof_id") != row.get("proof_id"):
            errors.append(f"proof-object identity mismatch: {row.get('proof_id')}")
        width = int(row.get("tested_interface_width", "0"))
        if len(proof.get("tested_interface", [])) != width:
            errors.append(f"proof-object tested interface width mismatch: {row.get('proof_id')}")
        if int(row.get("proved_lower_bound", "0")) != width or int(row.get("best_upper_bound", "0")) != width:
            errors.append(f"proof-object row is not exact-minimum width-tight: {row.get('proof_id')}")
        if proof.get("solver_status") != "unsat" or proof.get("exact_minimum_status") != "exact_minimum":
            errors.append(f"proof-object lacks exact-minimum UNSAT certificate metadata: {row.get('proof_id')}")
        source_table = proof.get("source_table", "")
        source_key = proof.get("target_id", "")
        source_row = source_tables.get(source_table, {}).get(source_key)
        if not source_row:
            errors.append(f"proof-object source row missing: {row.get('proof_id')}")
        elif _hash_rows([source_row]) != proof.get("source_row_hash"):
            errors.append(f"proof-object source row hash mismatch: {row.get('proof_id')}")


def _check_summary(
    summary: list[dict[str, str]],
    counterpart: list[dict[str, str]],
    rewrites: list[dict[str, str]],
    grammar: list[dict[str, str]],
    rtl: list[dict[str, str]],
    odc: list[dict[str, str]],
    locality: list[dict[str, str]],
    errors: list[str],
) -> None:
    expected = {
        "source_blind_counterpart_inference": (len(counterpart), _count(counterpart, "graph_active_recovery", "true")),
        "compact_interface_graph_rewrites": (len(rewrites), _count(rewrites, "new_boundary", "true")),
        "bounded_grammar_completeness": (len(grammar), _count(grammar, "bounded_grammar_complete_for_attempted_rows", "true")),
        "pinned_rtl_corpus": (len(rtl), _count(rtl, "redistributable", "true")),
        "odc_aware_placement": (len(odc), _count(odc, "graph_active", "true")),
        "machine_checkable_locality_proofs": (len(locality), _count(locality, "machine_checkable", "true")),
    }
    actual = {r.get("direction", ""): (int(r.get("input_rows", "0")), int(r.get("promoted_rows", "0"))) for r in summary}
    if set(actual) != set(expected):
        errors.append(f"summary directions drifted: {sorted(actual)} != {sorted(expected)}")
    for direction, counts in expected.items():
        if actual.get(direction) != counts:
            errors.append(f"summary count mismatch for {direction}: {actual.get(direction)} != {counts}")


def _source_index(rel_path: str, key: str, errors: list[str]) -> dict[str, dict[str, str]]:
    path = ROOT / rel_path
    if not path.exists():
        errors.append(f"missing source table for proof objects: {rel_path}")
        return {}
    with path.open(newline="", encoding="utf-8") as fh:
        return {row[key]: row for row in csv.DictReader(fh)}


def _rows(name: str, errors: list[str]) -> list[dict[str, str]]:
    path = OUT / name
    if not path.exists():
        errors.append(f"missing evidence advancement table: {path.relative_to(ROOT)}")
        return []
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _count(rows: list[dict[str, str]], key: str, value: str) -> int:
    return sum(row.get(key) == value for row in rows)


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _hash_rows(rows: list[dict[str, str]]) -> str:
    return hashlib.sha256(json.dumps(rows, sort_keys=True).encode("utf-8")).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
