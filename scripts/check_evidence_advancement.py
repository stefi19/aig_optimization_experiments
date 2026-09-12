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

sys.path.insert(0, str(ROOT))

from analyze_blif_matches import BlifNetwork, parse_blif  # noqa: E402
from formal_locality_barriers import all_assignments, scalar_eval_exact, structural_supports, vector_eval  # noqa: E402
from necessity_first_rewrites import validate_rewritten_graph  # noqa: E402
from semantic_region import file_hash  # noqa: E402


def main() -> int:
    errors: list[str] = []
    placement = _rows("source_blind_counterpart_placement.csv", errors)
    window_expression = _rows("source_blind_window_expression_placement.csv", errors)
    counterpart = _rows("source_blind_counterpart_inference.csv", errors)
    rewrites = _rows("compact_interface_rewrite_attempts.csv", errors)
    grammar = _rows("grammar_completeness_certificates.csv", errors)
    rtl = _rows("rtl_corpus_manifest.csv", errors)
    odc = _rows("odc_placement_accounting.csv", errors)
    locality = _rows("locality_proof_objects.csv", errors)
    summary = _rows("evidence_advancement_summary.csv", errors)

    _check_schema(placement + window_expression + counterpart + rewrites + grammar + rtl + odc + locality + summary, errors)
    _check_source_blind_placement(placement, errors, "source-blind exact-node placement")
    _check_source_blind_window_expression(window_expression, errors)
    _check_counterpart(counterpart, window_expression, errors)
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


def _check_source_blind_placement(rows: list[dict[str, str]], errors: list[str], label: str) -> None:
    if len(rows) != 56:
        errors.append(f"{label} denominator drifted: {len(rows)} != 56")
    attempted = [r for r in rows if r.get("semantic_counterpart_status", "").startswith("proved_")]
    if len(attempted) != 20:
        errors.append(f"{label} attempted semantic rows drifted: {len(attempted)} != 20")
    for row in rows:
        target = row.get("target_id")
        if row.get("source_blind") != "true":
            errors.append(f"{label} row is not source-blind: {target}")
        if row.get("promotion") == "graph_active_recovery":
            if row.get("rewrite_emitted") != "true" or row.get("graph_active") != "true":
                errors.append(f"{label} promotion lacks emitted graph-active rewrite: {target}")
            if row.get("global_cec_status") != "equivalent":
                errors.append(f"{label} promotion lacks global CEC: {target}")
            if row.get("source_vs_rewrite_cec") != "equivalent" or row.get("rewrite_vs_optimized_cec") != "equivalent":
                errors.append(f"{label} promotion lacks both CEC scopes: {target}")
            artifact = ROOT / row.get("rewrite_artifact", "")
            if not row.get("rewrite_artifact") or not artifact.exists():
                errors.append(f"{label} promotion artifact missing: {target}")
        if row.get("graph_active") == "true" and row.get("global_cec_status") != "equivalent":
            errors.append(f"{label} graph-active row lacks global CEC: {target}")
        if row.get("rewrite_emitted") == "true" and not row.get("rewrite_artifact"):
            errors.append(f"{label} rewrite emitted without artifact: {target}")


def _check_source_blind_window_expression(rows: list[dict[str, str]], errors: list[str]) -> None:
    _check_source_blind_placement(rows, errors, "source-blind window-expression placement")
    for row in rows:
        target = row.get("target_id")
        if row.get("leakage_audit") != "pass:aligned_pi_po_source_graph_signals_only":
            errors.append(f"source-blind window-expression leakage audit failed: {target}")
        if row.get("promotion") == "graph_active_recovery":
            if not row.get("expression_language") or not row.get("expression"):
                errors.append(f"source-blind window-expression promotion lacks expression: {target}")
            if row.get("blocker"):
                errors.append(f"source-blind window-expression promoted row still has blocker: {target}")
        if row.get("expression"):
            _check_source_blind_expression_witness(row, errors)


def _check_source_blind_expression_witness(row: dict[str, str], errors: list[str]) -> None:
    target = row.get("target_id", "")
    parsed = _parse_target_id(target)
    if parsed is None:
        errors.append(f"source-blind expression row has unparseable target id: {target}")
        return
    benchmark, _region, flow, target_node = parsed
    source_path = ROOT / "variants" / f"{benchmark}_original.blif"
    optimized_path = ROOT / "variants" / f"{benchmark}_{flow}.blif"
    if not source_path.exists() or not optimized_path.exists():
        errors.append(f"source-blind expression witness lacks replay BLIFs: {target}")
        return

    try:
        window = tuple(json.loads(row.get("candidate_source_window", "[]")))
        features = json.loads(row.get("selection_features", "{}"))
    except json.JSONDecodeError as exc:
        errors.append(f"source-blind expression witness has invalid JSON metadata for {target}: {exc}")
        return
    if not isinstance(features, dict):
        errors.append(f"source-blind expression witness features are not a JSON object: {target}")
        return
    if features.get("candidate_source") != "source_graph_signals_only":
        errors.append(f"source-blind expression witness is not source-graph-only: {target}")
    if features.get("selection_policy") != "first_exact_vector_match_in_bounded_language":
        errors.append(f"source-blind expression witness has unexpected selection policy: {target}")
    try:
        selected_window_width = int(features.get("selected_window_width", len(window)))
    except (TypeError, ValueError):
        errors.append(f"source-blind expression witness has invalid window-width metadata: {target}")
        selected_window_width = -1
    if selected_window_width != len(window):
        errors.append(f"source-blind expression witness window-width metadata mismatch: {target}")

    try:
        source = parse_blif(source_path)
        optimized = parse_blif(optimized_path)
        expr = _parse_expression(row.get("expression", ""))
        if expr is None:
            errors.append(f"source-blind expression witness has unparsable expression: {target}")
            return
        op_name, args = expr
        if op_name != row.get("expression_language"):
            errors.append(f"source-blind expression language mismatch for {target}: {op_name} != {row.get('expression_language')}")
        if tuple(args) != window:
            errors.append(f"source-blind expression window does not match expression args: {target}")
        allowed_signals = set(source.inputs) | set(source.outputs) | {node.output for node in source.nodes}
        unknown = [arg for arg in args if arg not in allowed_signals]
        if unknown:
            errors.append(f"source-blind expression uses non-source signals for {target}: {unknown}")
            return
        if target_node not in ({node.output for node in optimized.nodes} | set(optimized.outputs)):
            errors.append(f"source-blind expression target missing in optimized BLIF: {target}")
            return
        target_vector = _bit_vector(optimized, target_node)
        expression_vector = _evaluate_source_expression(source, op_name, args)
    except (KeyError, ValueError, TypeError) as exc:
        errors.append(f"source-blind expression witness replay failed for {target}: {exc}")
        return

    if expression_vector != target_vector:
        errors.append(f"source-blind expression witness does not reproduce optimized target vector: {target}")
    expected_hash = _hash_vector(target_vector)
    if features.get("target_truth_table_hash") != expected_hash:
        errors.append(f"source-blind expression target hash mismatch for {target}")

    support = _expression_support(source, args)
    selected_support = tuple(features.get("selected_support", ()))
    if selected_support != support:
        errors.append(f"source-blind expression selected support mismatch for {target}: {selected_support} != {support}")
    try:
        max_support = int(features.get("max_support_inputs", "0"))
    except (TypeError, ValueError):
        errors.append(f"source-blind expression witness has invalid support-bound metadata: {target}")
        max_support = 0
    if max_support <= 0 or len(support) > max_support:
        errors.append(f"source-blind expression support exceeds declared bound for {target}: {len(support)} > {max_support}")
    if _truth_table_from_vector(source, target_vector, support) is None:
        errors.append(f"source-blind expression target is not functional over selected support: {target}")


def _parse_target_id(target_id: str) -> tuple[str, str, str, str] | None:
    parts = target_id.split("|")
    if len(parts) != 4:
        return None
    return parts[0], parts[1], parts[2], parts[3]


def _parse_expression(expression: str) -> tuple[str, list[str]] | None:
    if not expression.endswith(")") or "(" not in expression:
        return None
    op_name, rest = expression.split("(", 1)
    args = rest[:-1].split(",") if rest[:-1] else []
    expected_arity = {"not": 1, "and": 2, "or": 2, "xor": 2, "xnor": 2, "nand": 2, "nor": 2, "mux": 3}
    if op_name not in expected_arity or len(args) != expected_arity[op_name] or any(not arg for arg in args):
        return None
    return op_name, args


def _bit_vector(net: BlifNetwork, node: str) -> tuple[int, ...]:
    return tuple(vector_eval(net, (node,), assignment)[0] for assignment in all_assignments(tuple(net.inputs)))


def _evaluate_source_expression(net: BlifNetwork, op_name: str, args: list[str]) -> tuple[int, ...]:
    vectors = [_bit_vector(net, arg) for arg in args]
    if op_name == "not":
        return tuple(1 - bit for bit in vectors[0])
    if op_name == "and":
        return tuple(a & b for a, b in zip(vectors[0], vectors[1], strict=True))
    if op_name == "or":
        return tuple(a | b for a, b in zip(vectors[0], vectors[1], strict=True))
    if op_name == "xor":
        return tuple(a ^ b for a, b in zip(vectors[0], vectors[1], strict=True))
    if op_name == "xnor":
        return tuple(1 ^ (a ^ b) for a, b in zip(vectors[0], vectors[1], strict=True))
    if op_name == "nand":
        return tuple(1 - (a & b) for a, b in zip(vectors[0], vectors[1], strict=True))
    if op_name == "nor":
        return tuple(1 - (a | b) for a, b in zip(vectors[0], vectors[1], strict=True))
    if op_name == "mux":
        return tuple((s & a) | ((1 - s) & b) for s, a, b in zip(vectors[0], vectors[1], vectors[2], strict=True))
    raise ValueError(f"unsupported expression operator: {op_name}")


def _expression_support(net: BlifNetwork, args: list[str]) -> tuple[str, ...]:
    support_by_node = structural_supports(net)
    out: list[str] = []
    for arg in args:
        support = (arg,) if arg in net.inputs else tuple(name for name in sorted(support_by_node.get(arg, ())) if name in net.inputs)
        for name in support:
            if name not in out:
                out.append(name)
    return tuple(sorted(out))


def _truth_table_from_vector(net: BlifNetwork, vector: tuple[int, ...], support: tuple[str, ...]) -> dict[tuple[int, ...], int] | None:
    table: dict[tuple[int, ...], int] = {}
    for assignment, value in zip(all_assignments(tuple(net.inputs)), vector, strict=True):
        values = scalar_eval_exact(net, assignment)
        key = tuple(int(values[name]) & 1 for name in support)
        if key in table and table[key] != value:
            return None
        table[key] = value
    return table


def _hash_vector(vector: tuple[int, ...]) -> str:
    return hashlib.sha256(json.dumps(vector).encode("ascii")).hexdigest()[:16]


def _check_counterpart(rows: list[dict[str, str]], placement: list[dict[str, str]], errors: list[str]) -> None:
    if len(rows) != 56:
        errors.append(f"source-blind counterpart denominator drifted: {len(rows)} != 56")
    semantic = [r for r in rows if r.get("semantic_counterpart_inferred") == "true"]
    semantic_only = [r for r in rows if r.get("promoted_evidence_level") == "semantic_counterpart_only"]
    graph_active = [r for r in rows if r.get("graph_active_recovery") == "true"]
    if len(semantic) != 20:
        errors.append(f"source-blind semantic count drifted: {len(semantic)} != 20")
    if len(semantic_only) + len(graph_active) != 20:
        errors.append(f"source-blind semantic rows are not partitioned into semantic-only and graph-active: {len(semantic_only)} + {len(graph_active)} != 20")
    if graph_active:
        bad = [r for r in graph_active if r.get("promoted_evidence_level") != "graph_active_recovery"]
        if bad:
            errors.append("graph-active counterpart rows are not labeled graph_active_recovery")
    if len(rows) == len(placement):
        for row, placed in zip(rows, placement, strict=True):
            if row.get("target_id") != placed.get("target_id"):
                errors.append(f"source-blind inference/placement target order mismatch: {row.get('target_id')} != {placed.get('target_id')}")
            if (row.get("graph_active_recovery") == "true") != (placed.get("promotion") == "graph_active_recovery"):
                errors.append(f"source-blind inference does not derive graph-active status from placement: {row.get('target_id')}")


def _check_rewrites(rows: list[dict[str, str]], errors: list[str]) -> None:
    if len(rows) != 48:
        errors.append(f"compact-interface rewrite denominator drifted: {len(rows)} != 48")
    graph_rewrites = _source_index(
        "results/necessity_first_target_discovery/graph_rewrites.csv", "stable_target_id", errors
    )
    provenance = _source_index(
        "results/necessity_first_target_discovery/target_provenance.csv", "stable_target_id", errors
    )
    boundary = _source_index(
        "results/necessity_first_target_discovery/boundary_recovery.csv", "stable_target_id", errors
    )
    cec_rows = _source_rows("results/necessity_first_target_discovery/global_cec.csv", errors)
    cec: dict[str, dict[str, str]] = {}
    for cec_row in cec_rows:
        cec.setdefault(cec_row.get("stable_target_id", ""), {})[cec_row.get("scope", "")] = cec_row.get("status", "")
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
        _check_compact_rewrite_sources(row, graph_rewrites, provenance, boundary, cec, errors)
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


def _check_compact_rewrite_sources(
    row: dict[str, str],
    graph_rewrites: dict[str, dict[str, str]],
    provenance: dict[str, dict[str, str]],
    boundary: dict[str, dict[str, str]],
    cec: dict[str, dict[str, str]],
    errors: list[str],
) -> None:
    sid = row.get("stable_target_id", "")
    graph = graph_rewrites.get(sid)
    prov = provenance.get(sid)
    boundary_row = boundary.get(sid)
    cec_scopes = cec.get(sid, {})
    if graph is None:
        errors.append(f"compact rewrite row lacks source graph-rewrite accounting: {sid}")
        return
    if prov is None:
        errors.append(f"compact rewrite row lacks target provenance: {sid}")
    if boundary_row is None:
        errors.append(f"compact rewrite row lacks boundary recovery accounting: {sid}")

    for key in ("rewrite_emitted", "graph_active", "rewrite_artifact"):
        if row.get(key) != graph.get(key):
            errors.append(f"compact rewrite row disagrees with graph_rewrites.{key}: {sid}")
    if boundary_row is not None and row.get("new_boundary") != boundary_row.get("new_boundary"):
        errors.append(f"compact rewrite row disagrees with boundary recovery: {sid}")
    if row.get("source_vs_rewrite_cec") != cec_scopes.get("S_vs_Sprime", "not_run"):
        errors.append(f"compact rewrite row disagrees with S_vs_Sprime CEC: {sid}")
    if row.get("rewrite_vs_optimized_cec") != cec_scopes.get("Sprime_vs_I", "not_run"):
        errors.append(f"compact rewrite row disagrees with Sprime_vs_I CEC: {sid}")

    if prov is not None:
        source_path = ROOT / prov.get("source_file", "")
        optimized_path = ROOT / prov.get("optimized_artifact", "")
        if not source_path.exists():
            errors.append(f"compact rewrite provenance source file missing: {sid}")
        elif file_hash(source_path) != prov.get("source_artifact_hash", ""):
            errors.append(f"compact rewrite provenance source hash mismatch: {sid}")
        if not optimized_path.exists():
            errors.append(f"compact rewrite provenance optimized artifact missing: {sid}")
        elif file_hash(optimized_path) != prov.get("optimized_artifact_hash", ""):
            errors.append(f"compact rewrite provenance optimized artifact hash mismatch: {sid}")
        if prov.get("source_optimized_cec_status") != "equivalent":
            errors.append(f"compact rewrite provenance lacks source/optimized CEC: {sid}")

    if row.get("rewrite_artifact"):
        artifact = ROOT / row.get("rewrite_artifact", "")
        if artifact.exists() and prov is not None:
            target = prov.get("optimized_target_node", "")
            actual_status = validate_rewritten_graph(artifact, target)
            if actual_status != graph.get("status"):
                errors.append(f"compact rewrite artifact graph validation mismatch: {sid} {actual_status} != {graph.get('status')}")
            if row.get("rewrite_emitted") == "true" and actual_status != "valid":
                errors.append(f"compact rewrite emitted artifact is not valid: {sid} {actual_status}")


def _check_grammar(rows: list[dict[str, str]], errors: list[str]) -> None:
    grouped = {
        (row.get("mode", ""), row.get("operator", "")): row
        for row in _source_rows("results/blind_semantic_cegis/z3_recovery_by_operator.csv", errors)
    }
    proofs_by_group: dict[tuple[str, str], list[dict[str, str]]] = {}
    for proof in _source_rows("results/blind_semantic_cegis/z3_formal_proofs.csv", errors):
        if proof.get("formal_status") == "formally_verified_region":
            proofs_by_group.setdefault((proof.get("mode", ""), proof.get("operator", "")), []).append(proof)

    expected_complete = {("blind", "sign_extend"), ("blind", "zero_extend"), ("oracle_bus", "sign_extend"), ("oracle_bus", "zero_extend")}
    complete = {(r.get("mode", ""), r.get("operator", "")) for r in rows if r.get("bounded_grammar_complete_for_attempted_rows") == "true"}
    if complete != expected_complete:
        errors.append(f"bounded grammar complete groups drifted: {sorted(complete)} != {sorted(expected_complete)}")
    for row in rows:
        key = (row.get("mode", ""), row.get("operator", ""))
        grouped_row = grouped.get(key)
        if grouped_row is None:
            errors.append(f"grammar row lacks grouped Z3 recovery source: {key}")
            continue
        for field in ("regions_attempted", "regions_recovered"):
            if row.get(field) != grouped_row.get(field):
                errors.append(f"grammar row disagrees with grouped Z3 {field}: {key}")
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
        proof_rows = proofs_by_group.get(key, [])
        if int(row.get("proof_row_count", "0")) != len(proof_rows):
            errors.append(f"grammar proof row count mismatch for {row.get('mode')}:{row.get('operator')}")
        if row.get("proof_hash") != _hash_rows(proof_rows):
            errors.append(f"grammar proof hash mismatch for {row.get('mode')}:{row.get('operator')}")
        if len(proof_rows) != recovered:
            errors.append(f"grammar recovered count is not backed by proof rows for {row.get('mode')}:{row.get('operator')}")
        for proof in proof_rows:
            if proof.get("formal_backend") != "z3" or proof.get("formal_evidence_level") != "formal_smt" or proof.get("solver_result") != "unsat":
                errors.append(f"grammar proof row is not accepted Z3 SMT evidence: {proof.get('candidate_id')}")
        if is_complete:
            proof_region_ids = {proof.get("region_id", "") for proof in proof_rows}
            if len(proof_region_ids) != attempted:
                errors.append(f"complete grammar group lacks one proof per attempted region: {row.get('mode')}:{row.get('operator')}")


def _check_rtl(rows: list[dict[str, str]], errors: list[str]) -> None:
    if len(rows) != 3:
        errors.append(f"RTL corpus manifest drifted: {len(rows)} != 3")
    expected_designs = {"rtl_affine4", "rtl_mux_arith4", "rtl_popcount4"}
    design_ids = [row.get("design_id", "") for row in rows]
    if set(design_ids) != expected_designs:
        errors.append(f"RTL corpus design set drifted: {sorted(design_ids)} != {sorted(expected_designs)}")
    if len(design_ids) != len(set(design_ids)):
        errors.append("RTL corpus manifest contains duplicate design ids")
    for row in rows:
        design_id = row.get("design_id", "")
        if row.get("redistributable") != "true" or row.get("license") != "CC0-1.0":
            errors.append(f"RTL corpus row is not redistributable CC0: {design_id}")
        rtl_path = ROOT / row.get("rtl_path", "")
        if not rtl_path.exists():
            errors.append(f"RTL source missing: {row.get('rtl_path')}")
            continue
        rtl_text = rtl_path.read_text(encoding="utf-8")
        if not rtl_text.startswith("// SPDX-License-Identifier: CC0-1.0\n"):
            errors.append(f"RTL source lacks CC0 SPDX header: {row.get('rtl_path')}")
        if f"module {design_id}(" not in rtl_text:
            errors.append(f"RTL source module declaration does not match design id: {design_id}")
        if "endmodule" not in rtl_text:
            errors.append(f"RTL source lacks endmodule: {design_id}")
        if _sha256(rtl_path) != row.get("rtl_sha256"):
            errors.append(f"RTL hash mismatch: {row.get('rtl_path')}")
        try:
            metadata = json.loads(row.get("source_location_metadata", "{}"))
        except json.JSONDecodeError as exc:
            errors.append(f"RTL source-location metadata is invalid JSON for {design_id}: {exc}")
            metadata = {}
        if (
            metadata.get("module") != design_id
            or metadata.get("source") != row.get("rtl_path")
            or metadata.get("generator") != "build_evidence_advancement.py"
        ):
            errors.append(f"RTL source-location metadata mismatch: {design_id}")
        status = row.get("lowering_status")
        if status == "lowered_blif":
            lowered = ROOT / row.get("lowered_blif", "")
            if not lowered.exists():
                errors.append(f"lowered BLIF missing for {design_id}")
            if row.get("evidence_level") != "rtl_lowered_with_tool":
                errors.append(f"lowered RTL row has wrong evidence level: {design_id}")
            if not row.get("yosys_path") or row.get("yosys_version") in {"", "unavailable"}:
                errors.append(f"lowered RTL row lacks Yosys provenance: {design_id}")
            if lowered.exists():
                try:
                    parse_blif(lowered)
                except Exception as exc:  # pragma: no cover - defensive around optional Yosys output
                    errors.append(f"lowered BLIF does not parse for {design_id}: {exc}")
        elif status == "tool_missing":
            if row.get("lowered_blif"):
                errors.append(f"tool-missing RTL row has lowered BLIF: {design_id}")
            if row.get("evidence_level") != "rtl_corpus_pinned":
                errors.append(f"tool-missing RTL row has wrong evidence level: {design_id}")
            if row.get("yosys_path") or row.get("yosys_version") != "unavailable":
                errors.append(f"tool-missing RTL row claims Yosys provenance: {design_id}")
        else:
            errors.append(f"unexpected RTL lowering status for {design_id}: {status}")


def _check_odc(rows: list[dict[str, str]], errors: list[str]) -> None:
    if len(rows) != 10:
        errors.append(f"ODC anchor accounting denominator drifted: {len(rows)} != 10")
    anchors = _source_index("results/odc_anchor_generation/odc_proven_anchors.csv", "case_id", errors)
    boundary_cases = _source_rows("results/odc_anchor_generation/odc_boundary_recovery_cases.csv", errors)
    selected_cases: dict[tuple[str, str], dict[str, str]] = {}
    for case in boundary_cases:
        if case.get("anchor_mode") == "formal_plus_odc":
            selected_cases[(case.get("benchmark", ""), case.get("optimization", ""))] = case
    seen_case_ids: set[str] = set()
    for row in rows:
        case_id = row.get("case_id", "")
        if case_id in seen_case_ids:
            errors.append(f"duplicate ODC accounting row: {case_id}")
        seen_case_ids.add(case_id)
        anchor = anchors.get(case_id)
        if anchor is None:
            errors.append(f"ODC accounting row lacks proven-anchor source: {case_id}")
        else:
            _check_odc_anchor_source(row, anchor, errors)
        selected_case = selected_cases.get((row.get("benchmark", ""), row.get("optimization", "")))
        if selected_case is None:
            errors.append(f"ODC accounting row lacks selected boundary case: {case_id}")
        else:
            _check_odc_boundary_source(row, selected_case, errors)
        if row.get("graph_active") == "true" and row.get("global_cec_status") != "equivalent":
            errors.append(f"ODC graph-active row lacks global CEC: {case_id}")
    graph_active = [r for r in rows if r.get("graph_active") == "true"]
    if len(graph_active) != 0:
        errors.append(f"ODC graph-active placement count drifted from current claim: {len(graph_active)} != 0")


def _check_odc_anchor_source(row: dict[str, str], anchor: dict[str, str], errors: list[str]) -> None:
    case_id = row.get("case_id", "")
    for field in ("benchmark", "optimization", "proof_status", "evidence_level"):
        if row.get(field) != anchor.get(field):
            errors.append(f"ODC accounting row disagrees with proven anchor {field}: {case_id}")
    if row.get("proof_status") != "proven_odc_valid":
        errors.append(f"ODC row is not a proven contextual anchor: {case_id}")
    if anchor.get("mapping_category") != "formal_odc_valid_anchor":
        errors.append(f"ODC proven anchor has wrong mapping category: {case_id}")
    if anchor.get("equivalence_scope") != "contextual":
        errors.append(f"ODC proven anchor is not contextual scope: {case_id}")
    if anchor.get("sat_result") != "verified_equivalent":
        errors.append(f"ODC proven anchor lacks verified contextual equivalence: {case_id}")
    source_result = ROOT / anchor.get("source_result_file", "")
    if not anchor.get("source_result_file") or not source_result.exists():
        errors.append(f"ODC proven anchor source result file missing: {case_id}")


def _check_odc_boundary_source(row: dict[str, str], case: dict[str, str], errors: list[str]) -> None:
    case_id = row.get("case_id", "")
    success = case.get("success") == "True"
    expected_promotion = "boundary_candidate_requires_graph_cec" if success else "contextual_anchor_only"
    if row.get("placement_attempted") != "true":
        errors.append(f"ODC accounting row was not marked attempted: {case_id}")
    if row.get("boundary_success") != str(success).lower():
        errors.append(f"ODC accounting row disagrees with selected boundary success: {case_id}")
    if row.get("blocker") != case.get("classification", ""):
        errors.append(f"ODC accounting row disagrees with selected boundary blocker: {case_id}")
    if row.get("promotion") != expected_promotion:
        errors.append(f"ODC accounting row has wrong contextual promotion: {case_id}")
    if success and case.get("boundary_contextual_validation_status") != "boundary_contextually_valid":
        errors.append(f"successful ODC boundary case lacks contextual validation: {case_id}")
    if success and case.get("boundary_contextual_proof_status") != "proven_odc_valid":
        errors.append(f"successful ODC boundary case lacks contextual proof: {case_id}")
    if row.get("graph_active") != "false" or row.get("global_cec_status") != "not_claimed":
        errors.append(f"ODC contextual accounting overclaims graph-active/global evidence: {case_id}")


def _check_locality(rows: list[dict[str, str]], errors: list[str]) -> None:
    if len(rows) != 57:
        errors.append(f"locality proof-object count drifted: {len(rows)} != 57")
    expected = _expected_locality_proof_sources(errors)
    actual_ids = [row.get("proof_id", "") for row in rows]
    if len(actual_ids) != len(set(actual_ids)):
        errors.append("duplicate locality proof ids in evidence table")
    expected_ids = set(expected)
    actual_id_set = set(actual_ids)
    missing = sorted(expected_ids - actual_id_set)
    extra = sorted(actual_id_set - expected_ids)
    if missing:
        errors.append(f"missing expected locality proof objects: {missing}")
    if extra:
        errors.append(f"unexpected locality proof objects: {extra}")
    for row in rows:
        proof_id = row.get("proof_id", "")
        if row.get("machine_checkable") != "true":
            errors.append(f"proof-object row is not machine-checkable: {proof_id}")
        path = ROOT / row.get("proof_object_path", "")
        if not path.exists():
            errors.append(f"proof object missing: {row.get('proof_object_path')}")
            continue
        if _sha256(path) != row.get("proof_object_sha256"):
            errors.append(f"proof-object hash mismatch: {proof_id}")
        try:
            proof = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"proof-object JSON parse failed: {proof_id}: {exc}")
            continue
        if proof.get("schema_version") != SCHEMA or proof.get("proof_id") != proof_id:
            errors.append(f"proof-object identity mismatch: {proof_id}")
        expected_source = expected.get(proof_id)
        if expected_source is not None:
            _check_locality_proof_source(row, proof, expected_source, errors)
        try:
            width = int(row.get("tested_interface_width", "0"))
        except ValueError:
            errors.append(f"proof-object row has invalid interface width: {proof_id}")
            width = -1
        if len(proof.get("tested_interface", [])) != width:
            errors.append(f"proof-object tested interface width mismatch: {proof_id}")
        try:
            proved_lower_bound = int(row.get("proved_lower_bound", "0"))
            best_upper_bound = int(row.get("best_upper_bound", "0"))
        except ValueError:
            errors.append(f"proof-object row has invalid bound metadata: {proof_id}")
            proved_lower_bound = best_upper_bound = -1
        if proved_lower_bound != width or best_upper_bound != width:
            errors.append(f"proof-object row is not exact-minimum width-tight: {proof_id}")
        if proof.get("solver_status") != "unsat" or proof.get("exact_minimum_status") != "exact_minimum":
            errors.append(f"proof-object lacks exact-minimum UNSAT certificate metadata: {proof_id}")


def _expected_locality_proof_sources(errors: list[str]) -> dict[str, dict[str, object]]:
    expected: dict[str, dict[str, object]] = {}
    for source_family, rel_path, id_col in [
        ("necessity_first_targets", "results/necessity_first_target_discovery/formal_locality_results.csv", "stable_target_id"),
        ("formal_locality_barriers", "results/formal_locality_barriers/input_exact_minimum_certificates.csv", "certificate_id"),
    ]:
        for source_row in _source_rows(rel_path, errors):
            if source_family == "necessity_first_targets" and source_row.get("compact_interface") != "true":
                continue
            if source_row.get("exact_minimum_status") != "exact_minimum" or source_row.get("solver_status") != "unsat":
                continue
            proof_id = _stable_id(source_family, source_row[id_col], source_row.get("tested_interface", ""))
            expected[proof_id] = {
                "source_family": source_family,
                "source_table": rel_path,
                "source_row": source_row,
                "target_id": source_row.get("stable_target_id") or source_row.get("target_id"),
            }
    return expected


def _check_locality_proof_source(row: dict[str, str], proof: dict[str, object], expected: dict[str, object], errors: list[str]) -> None:
    proof_id = row.get("proof_id", "")
    source_row = expected["source_row"]
    if row.get("source_family") != expected["source_family"] or proof.get("source_family") != expected["source_family"]:
        errors.append(f"proof-object source family mismatch: {proof_id}")
    if row.get("source_table") != expected["source_table"] or proof.get("source_table") != expected["source_table"]:
        errors.append(f"proof-object source table mismatch: {proof_id}")
    if row.get("target_id") != expected["target_id"] or proof.get("target_id") != expected["target_id"]:
        errors.append(f"proof-object target mismatch: {proof_id}")
    if proof.get("source_row_hash") != _hash_rows([source_row]):
        errors.append(f"proof-object source row hash mismatch: {proof_id}")
    if proof.get("predicate") != "no_smaller_interface_suffices_and_listed_interface_suffices":
        errors.append(f"proof-object predicate mismatch: {proof_id}")
    tested_interface = json.loads(source_row["tested_interface"])
    if proof.get("tested_interface") != tested_interface:
        errors.append(f"proof-object tested interface disagrees with source row: {proof_id}")
    if int(source_row["proved_lower_bound"]) != int(row.get("proved_lower_bound", "-1")):
        errors.append(f"proof-object proved lower bound disagrees with source row: {proof_id}")
    if int(source_row["best_upper_bound"]) != int(row.get("best_upper_bound", "-1")):
        errors.append(f"proof-object best upper bound disagrees with source row: {proof_id}")


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


def _source_rows(rel_path: str, errors: list[str]) -> list[dict[str, str]]:
    path = ROOT / rel_path
    if not path.exists():
        errors.append(f"missing source table: {rel_path}")
        return []
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


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


def _stable_id(*parts: object) -> str:
    return hashlib.sha256(json.dumps(parts, sort_keys=True).encode("utf-8")).hexdigest()[:16]


if __name__ == "__main__":
    raise SystemExit(main())
