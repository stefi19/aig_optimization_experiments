"""Source-blind counterpart placement attempts for evidence advancement."""

from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path

from analyze_blif_matches import BlifNetwork, BlifNode, parse_blif
from formal_locality_barriers import all_assignments, scalar_eval_exact, structural_supports, vector_eval
from necessity_first_rewrites import validate_rewritten_graph, write_network


SCHEMA = "evidence_advancement_v1"


@dataclass(frozen=True)
class SourceBlindPlacementResult:
    target_id: str
    candidate_source_window: tuple[str, ...]
    selection_features: dict[str, object]
    semantic_counterpart_status: str
    rewrite_artifact: str
    rewrite_emitted: bool
    graph_active: bool
    global_cec_status: str
    promotion: str
    blocker: str
    source_blind: bool
    source_vs_rewrite_cec: str
    rewrite_vs_optimized_cec: str

    def row(self) -> dict[str, str]:
        return {
            "target_id": self.target_id,
            "candidate_source_window": json.dumps(self.candidate_source_window),
            "selection_features": json.dumps(self.selection_features, sort_keys=True),
            "semantic_counterpart_status": self.semantic_counterpart_status,
            "rewrite_artifact": self.rewrite_artifact,
            "rewrite_emitted": str(self.rewrite_emitted).lower(),
            "graph_active": str(self.graph_active).lower(),
            "global_cec_status": self.global_cec_status,
            "promotion": self.promotion,
            "blocker": self.blocker,
            "source_blind": str(self.source_blind).lower(),
            "source_vs_rewrite_cec": self.source_vs_rewrite_cec,
            "rewrite_vs_optimized_cec": self.rewrite_vs_optimized_cec,
            "schema_version": SCHEMA,
        }


@dataclass(frozen=True)
class SourceBlindWindowExpressionResult:
    target_id: str
    candidate_source_window: tuple[str, ...]
    expression_language: str
    expression: str
    selection_features: dict[str, object]
    semantic_counterpart_status: str
    rewrite_artifact: str
    rewrite_emitted: bool
    graph_active: bool
    global_cec_status: str
    promotion: str
    blocker: str
    source_blind: bool
    leakage_audit: str
    source_vs_rewrite_cec: str
    rewrite_vs_optimized_cec: str

    def row(self) -> dict[str, str]:
        return {
            "target_id": self.target_id,
            "candidate_source_window": json.dumps(self.candidate_source_window),
            "expression_language": self.expression_language,
            "expression": self.expression,
            "selection_features": json.dumps(self.selection_features, sort_keys=True),
            "semantic_counterpart_status": self.semantic_counterpart_status,
            "rewrite_artifact": self.rewrite_artifact,
            "rewrite_emitted": str(self.rewrite_emitted).lower(),
            "graph_active": str(self.graph_active).lower(),
            "global_cec_status": self.global_cec_status,
            "promotion": self.promotion,
            "blocker": self.blocker,
            "source_blind": str(self.source_blind).lower(),
            "leakage_audit": self.leakage_audit,
            "source_vs_rewrite_cec": self.source_vs_rewrite_cec,
            "rewrite_vs_optimized_cec": self.rewrite_vs_optimized_cec,
            "schema_version": SCHEMA,
        }


def attempt_source_blind_counterpart_placement(
    *,
    target_id: str,
    semantic_counterpart_status: str,
    source_path: Path,
    optimized_path: Path,
    optimized_target_node: str,
    output_path: Path,
    root: Path,
    abc_path: Path | None,
    max_support_inputs: int = 6,
) -> SourceBlindPlacementResult:
    source = parse_blif(source_path)
    optimized = parse_blif(optimized_path)
    if source.inputs != optimized.inputs or source.outputs != optimized.outputs:
        return _result(target_id, (), {}, semantic_counterpart_status, output_path, False, False, "not_claimed", "primary_interface_mismatch", "not_run", "not_run", root)
    if optimized_target_node not in {node.output for node in optimized.nodes} | set(optimized.outputs):
        return _result(target_id, (), {}, semantic_counterpart_status, output_path, False, False, "not_claimed", "optimized_target_missing", "not_run", "not_run", root)
    if optimized_target_node in optimized.outputs and len(optimized.outputs) == 1:
        return _result(target_id, (), {}, semantic_counterpart_status, output_path, False, False, "not_claimed", "whole_design_replacement_rejected", "not_run", "not_run", root)

    target_vector = _bit_vector(optimized, optimized_target_node)
    support_by_node = structural_supports(source)
    candidates = []
    for node_name in _source_candidate_nodes(source):
        support = tuple(name for name in sorted(support_by_node.get(node_name, ())) if name in source.inputs)
        if len(support) > max_support_inputs:
            continue
        try:
            vector = _bit_vector(source, node_name)
        except KeyError:
            continue
        if vector == target_vector:
            candidates.append((node_name, support))
    if not candidates:
        features = {"searched_source_nodes": len(_source_candidate_nodes(source)), "max_support_inputs": max_support_inputs}
        return _result(target_id, (), features, semantic_counterpart_status, output_path, False, False, "not_claimed", "no_exact_source_counterpart_node_under_bound", "not_run", "not_run", root)

    source_node, support = sorted(candidates, key=lambda item: (len(item[1]), item[0]))[0]
    table = _truth_table(source, source_node, support)
    new_node = BlifNode(output=optimized_target_node, inputs=list(support), cover=_cover_from_table(table, len(support)))
    old_node = next((node for node in optimized.nodes if node.output == optimized_target_node), None)
    if old_node is None:
        return _result(target_id, (source_node,), {"selected_support": support}, semantic_counterpart_status, output_path, False, False, "not_claimed", "target_driver_count_not_one", "not_run", "not_run", root)

    graph_active_candidate = (tuple(old_node.inputs), tuple(old_node.cover)) != (tuple(new_node.inputs), tuple(new_node.cover)) and not _is_direct_bypass(new_node)
    if not graph_active_candidate:
        blocker = "direct_bypass" if _is_direct_bypass(new_node) else "identical_driver"
        return _result(target_id, (source_node,), _features(source, optimized, source_node, support, target_vector), semantic_counterpart_status, output_path, False, False, "not_claimed", blocker, "not_run", "not_run", root)

    _emit_replacement(optimized, optimized_target_node, new_node, output_path)
    validation = validate_rewritten_graph(output_path, optimized_target_node)
    if validation != "valid":
        if output_path.exists():
            output_path.unlink()
        return _result(target_id, (source_node,), _features(source, optimized, source_node, support, target_vector), semantic_counterpart_status, output_path, False, False, "not_claimed", validation, "not_run", "not_run", root)

    source_cec = _abc_cec(abc_path, source_path, output_path)
    rewrite_cec = _abc_cec(abc_path, output_path, optimized_path)
    promoted = source_cec == "equivalent" and rewrite_cec == "equivalent"
    blocker = "" if promoted else _cec_blocker(source_cec, rewrite_cec)
    return _result(
        target_id,
        (source_node,),
        _features(source, optimized, source_node, support, target_vector),
        semantic_counterpart_status,
        output_path,
        True,
        promoted,
        "equivalent" if promoted else "not_claimed",
        blocker,
        source_cec,
        rewrite_cec,
        root,
    )


def attempt_source_blind_window_expression_placement(
    *,
    target_id: str,
    semantic_counterpart_status: str,
    source_path: Path,
    optimized_path: Path,
    optimized_target_node: str,
    output_path: Path,
    root: Path,
    abc_path: Path | None,
    max_support_inputs: int = 6,
    max_candidate_signals: int = 64,
) -> SourceBlindWindowExpressionResult:
    source = parse_blif(source_path)
    optimized = parse_blif(optimized_path)
    if source.inputs != optimized.inputs or source.outputs != optimized.outputs:
        return _window_result(target_id, (), "", "", {}, semantic_counterpart_status, output_path, False, False, "not_claimed", "primary_interface_mismatch", "not_run", "not_run", root)
    if optimized_target_node not in {node.output for node in optimized.nodes} | set(optimized.outputs):
        return _window_result(target_id, (), "", "", {}, semantic_counterpart_status, output_path, False, False, "not_claimed", "optimized_target_missing", "not_run", "not_run", root)
    if optimized_target_node in optimized.outputs and len(optimized.outputs) == 1:
        return _window_result(target_id, (), "", "", {}, semantic_counterpart_status, output_path, False, False, "not_claimed", "whole_design_replacement_rejected", "not_run", "not_run", root)

    target_vector = _bit_vector(optimized, optimized_target_node)
    candidates = _expression_candidates(source, max_support_inputs, max_candidate_signals)
    match = _find_expression_match(target_vector, candidates, max_support_inputs)
    features: dict[str, object] = {
        "candidate_signals": len(candidates),
        "max_candidate_signals": max_candidate_signals,
        "max_support_inputs": max_support_inputs,
        "target_truth_table_hash": _hash_vector(target_vector),
        "search_order": ("not", "binary", "mux"),
        "candidate_source": "source_graph_signals_only",
    }
    if match is None:
        return _window_result(target_id, (), "bounded_source_expression", "", features, semantic_counterpart_status, output_path, False, False, "not_claimed", "no_source_window_expression_under_bound", "not_run", "not_run", root)

    support = match["support"]
    table = _truth_table_from_vector(source, target_vector, support)
    if table is None:
        return _window_result(target_id, match["window"], match["language"], match["expression"], features | {"selected_support": support}, semantic_counterpart_status, output_path, False, False, "not_claimed", "selected_expression_not_functional_over_support", "not_run", "not_run", root)
    new_node = BlifNode(output=optimized_target_node, inputs=list(support), cover=_cover_from_table(table, len(support)))
    old_node = next((node for node in optimized.nodes if node.output == optimized_target_node), None)
    if old_node is None:
        return _window_result(target_id, match["window"], match["language"], match["expression"], features | {"selected_support": support}, semantic_counterpart_status, output_path, False, False, "not_claimed", "target_driver_count_not_one", "not_run", "not_run", root)

    graph_active_candidate = (tuple(old_node.inputs), tuple(old_node.cover)) != (tuple(new_node.inputs), tuple(new_node.cover)) and not _is_direct_bypass(new_node)
    features = features | {
        "selected_support": support,
        "selected_window_width": len(match["window"]),
        "selection_policy": "first_exact_vector_match_in_bounded_language",
    }
    if not graph_active_candidate:
        blocker = "direct_bypass" if _is_direct_bypass(new_node) else "identical_driver"
        return _window_result(target_id, match["window"], match["language"], match["expression"], features, semantic_counterpart_status, output_path, False, False, "not_claimed", blocker, "not_run", "not_run", root)

    _emit_replacement(optimized, optimized_target_node, new_node, output_path, model="source_blind_window_expression_placement")
    validation = validate_rewritten_graph(output_path, optimized_target_node)
    if validation != "valid":
        if output_path.exists():
            output_path.unlink()
        return _window_result(target_id, match["window"], match["language"], match["expression"], features, semantic_counterpart_status, output_path, False, False, "not_claimed", validation, "not_run", "not_run", root)

    source_cec = _abc_cec(abc_path, source_path, output_path)
    rewrite_cec = _abc_cec(abc_path, output_path, optimized_path)
    promoted = source_cec == "equivalent" and rewrite_cec == "equivalent"
    blocker = "" if promoted else _cec_blocker(source_cec, rewrite_cec)
    return _window_result(
        target_id,
        match["window"],
        match["language"],
        match["expression"],
        features,
        semantic_counterpart_status,
        output_path,
        True,
        promoted,
        "equivalent" if promoted else "not_claimed",
        blocker,
        source_cec,
        rewrite_cec,
        root,
    )


def _source_candidate_nodes(net: BlifNetwork) -> tuple[str, ...]:
    return tuple(dict.fromkeys([node.output for node in net.nodes] + list(net.outputs)))


def _bit_vector(net: BlifNetwork, node: str) -> tuple[int, ...]:
    return tuple(vector_eval(net, (node,), assignment)[0] for assignment in all_assignments(tuple(net.inputs)))


def _truth_table(net: BlifNetwork, node: str, support: tuple[str, ...]) -> dict[tuple[int, ...], int]:
    table: dict[tuple[int, ...], int] = {}
    for assignment in all_assignments(tuple(net.inputs)):
        values = scalar_eval_exact(net, assignment)
        key = tuple(int(values[name]) & 1 for name in support)
        value = int(values[node]) & 1
        if key in table and table[key] != value:
            raise ValueError(f"{node} is not functional over declared support")
        table[key] = value
    return table


def _truth_table_from_vector(net: BlifNetwork, vector: tuple[int, ...], support: tuple[str, ...]) -> dict[tuple[int, ...], int] | None:
    table: dict[tuple[int, ...], int] = {}
    for assignment, value in zip(all_assignments(tuple(net.inputs)), vector, strict=True):
        key = tuple(int(assignment[name]) & 1 for name in support)
        if key in table and table[key] != value:
            return None
        table[key] = value
    return table


def _cover_from_table(table: dict[tuple[int, ...], int], width: int) -> list[str]:
    if width == 0:
        return ["1"] if table.get(tuple(), 0) else []
    return ["".join(str(bit) for bit in key) + " 1" for key, value in sorted(table.items()) if value]


def _emit_replacement(net: BlifNetwork, target: str, replacement: BlifNode, output_path: Path, *, model: str = "source_blind_counterpart_placement") -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    rewritten = [replacement if node.output == target else node for node in net.nodes]
    write_network(BlifNetwork(list(net.inputs), list(net.outputs), rewritten), output_path, model=model)


def _features(source: BlifNetwork, optimized: BlifNetwork, source_node: str, support: tuple[str, ...], target_vector: tuple[int, ...]) -> dict[str, object]:
    source_fanout = sum(source_node in node.inputs for node in source.nodes)
    return {
        "source_node": source_node,
        "source_support": support,
        "source_fanout": source_fanout,
        "optimized_outputs": tuple(optimized.outputs),
        "truth_table_hash": hashlib.sha256(json.dumps(target_vector).encode("ascii")).hexdigest()[:16],
        "selection_policy": "min_support_then_name",
    }


def _is_direct_bypass(node: BlifNode) -> bool:
    return len(node.inputs) == 1 and node.cover in (["1 1"], ["0 1"])


def _expression_candidates(net: BlifNetwork, max_support_inputs: int, max_candidate_signals: int) -> list[dict[str, object]]:
    support_by_node = structural_supports(net)
    candidates = []
    for signal in _source_candidate_nodes(net) + tuple(net.inputs):
        support = (signal,) if signal in net.inputs else tuple(name for name in sorted(support_by_node.get(signal, ())) if name in net.inputs)
        if len(support) > max_support_inputs:
            continue
        try:
            vector = _bit_vector(net, signal)
        except KeyError:
            continue
        candidates.append({"name": signal, "support": support, "vector": vector})
    deduped = list({candidate["name"]: candidate for candidate in candidates}.values())
    return sorted(deduped, key=lambda item: (len(item["support"]), str(item["name"])))[:max_candidate_signals]


def _find_expression_match(target_vector: tuple[int, ...], candidates: list[dict[str, object]], max_support_inputs: int) -> dict[str, object] | None:
    for candidate in candidates:
        vector = candidate["vector"]
        if _invert(vector) == target_vector:
            return {
                "language": "not",
                "expression": f"not({candidate['name']})",
                "window": (str(candidate["name"]),),
                "support": candidate["support"],
            }

    binary_ops = (
        ("and", lambda a, b: tuple(x & y for x, y in zip(a, b, strict=True))),
        ("or", lambda a, b: tuple(x | y for x, y in zip(a, b, strict=True))),
        ("xor", lambda a, b: tuple(x ^ y for x, y in zip(a, b, strict=True))),
        ("xnor", lambda a, b: tuple(1 ^ (x ^ y) for x, y in zip(a, b, strict=True))),
        ("nand", lambda a, b: tuple(1 - (x & y) for x, y in zip(a, b, strict=True))),
        ("nor", lambda a, b: tuple(1 - (x | y) for x, y in zip(a, b, strict=True))),
    )
    for left_index, left in enumerate(candidates):
        for right in candidates[left_index + 1 :]:
            support = _union_support(left["support"], right["support"])
            if len(support) > max_support_inputs:
                continue
            for op_name, op in binary_ops:
                if op(left["vector"], right["vector"]) == target_vector:
                    return {
                        "language": op_name,
                        "expression": f"{op_name}({left['name']},{right['name']})",
                        "window": (str(left["name"]), str(right["name"])),
                        "support": support,
                    }

    for selector in candidates:
        for when_one in candidates:
            if when_one["name"] == selector["name"]:
                continue
            for when_zero in candidates:
                names = (selector["name"], when_one["name"], when_zero["name"])
                if len(set(names)) != 3:
                    continue
                support = _union_support(selector["support"], when_one["support"], when_zero["support"])
                if len(support) > max_support_inputs:
                    continue
                vector = tuple((s & a) | ((1 - s) & b) for s, a, b in zip(selector["vector"], when_one["vector"], when_zero["vector"], strict=True))
                if vector == target_vector:
                    return {
                        "language": "mux",
                        "expression": f"mux({selector['name']},{when_one['name']},{when_zero['name']})",
                        "window": tuple(str(name) for name in names),
                        "support": support,
                    }
    return None


def _invert(vector: object) -> tuple[int, ...]:
    return tuple(1 - int(bit) for bit in vector)


def _union_support(*supports: object) -> tuple[str, ...]:
    out: list[str] = []
    for support in supports:
        for name in support:
            if name not in out:
                out.append(str(name))
    return tuple(sorted(out))


def _hash_vector(vector: tuple[int, ...]) -> str:
    return hashlib.sha256(json.dumps(vector).encode("ascii")).hexdigest()[:16]


def _abc_cec(abc_path: Path | None, left: Path, right: Path) -> str:
    if abc_path is None or not abc_path.exists():
        return "abc_unavailable"
    proc = subprocess.run([str(abc_path), "-c", f"cec {left} {right}"], text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=10, check=False)
    text = proc.stdout
    if "Networks are equivalent" in text or "Networks are equivalent after" in text:
        return "equivalent"
    if "Networks are NOT EQUIVALENT" in text or "not equivalent" in text.lower():
        return "disproved"
    return "unknown"


def _cec_blocker(source_cec: str, rewrite_cec: str) -> str:
    if source_cec != "equivalent":
        return "source_vs_rewrite_cec_" + source_cec
    if rewrite_cec != "equivalent":
        return "rewrite_vs_optimized_cec_" + rewrite_cec
    return ""


def _result(
    target_id: str,
    window: tuple[str, ...],
    features: dict[str, object],
    semantic_status: str,
    output_path: Path,
    emitted: bool,
    graph_active: bool,
    global_cec: str,
    blocker: str,
    source_cec: str,
    rewrite_cec: str,
    root: Path,
) -> SourceBlindPlacementResult:
    artifact = _display_path(output_path, root) if emitted and output_path.exists() else ""
    return SourceBlindPlacementResult(
        target_id=target_id,
        candidate_source_window=window,
        selection_features=features,
        semantic_counterpart_status=semantic_status,
        rewrite_artifact=artifact,
        rewrite_emitted=emitted,
        graph_active=graph_active,
        global_cec_status=global_cec,
        promotion="graph_active_recovery" if graph_active and global_cec == "equivalent" else ("rewrite_artifact_only" if emitted else "not_promoted"),
        blocker=blocker,
        source_blind=True,
        source_vs_rewrite_cec=source_cec,
        rewrite_vs_optimized_cec=rewrite_cec,
    )


def _window_result(
    target_id: str,
    window: tuple[str, ...],
    language: str,
    expression: str,
    features: dict[str, object],
    semantic_status: str,
    output_path: Path,
    emitted: bool,
    graph_active: bool,
    global_cec: str,
    blocker: str,
    source_cec: str,
    rewrite_cec: str,
    root: Path,
) -> SourceBlindWindowExpressionResult:
    artifact = _display_path(output_path, root) if emitted and output_path.exists() else ""
    return SourceBlindWindowExpressionResult(
        target_id=target_id,
        candidate_source_window=window,
        expression_language=language,
        expression=expression,
        selection_features=features,
        semantic_counterpart_status=semantic_status,
        rewrite_artifact=artifact,
        rewrite_emitted=emitted,
        graph_active=graph_active,
        global_cec_status=global_cec,
        promotion="graph_active_recovery" if graph_active and global_cec == "equivalent" else ("rewrite_artifact_only" if emitted else "not_promoted"),
        blocker=blocker,
        source_blind=True,
        leakage_audit="pass:aligned_pi_po_source_graph_signals_only",
        source_vs_rewrite_cec=source_cec,
        rewrite_vs_optimized_cec=rewrite_cec,
    )


def _display_path(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)
