"""Graph-active rewrite synthesis for necessity-first compact interfaces."""

from __future__ import annotations

import hashlib
import json
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

from analyze_blif_matches import BlifNetwork, BlifNode, parse_blif
from formal_locality_barriers import all_assignments, scalar_eval_exact, vector_eval
from necessity_first_targets import all_signal_names, structural_path_to_output


SCHEMA_VERSION = "necessity_first_targets_v1"


@dataclass(frozen=True)
class RewriteSynthesisResult:
    stable_target_id: str
    optimized_target_node: str
    tested_interface: tuple[str, ...]
    truth_table_hash: str
    onset_size: int
    total_rows: int
    rewrite_artifact: str
    rewrite_emitted: bool
    graph_active: bool
    graph_validation_status: str
    blocker: str
    cec_source_status: str
    cec_rewrite_vs_optimized_status: str
    abc_available: bool
    runtime_seconds: float

    @property
    def new_boundary(self) -> bool:
        return self.rewrite_emitted and self.graph_active and self.cec_source_status == "equivalent" and self.cec_rewrite_vs_optimized_status == "equivalent"


@dataclass(frozen=True)
class FrontierExpansionResult:
    stable_target_id: str
    base_target_node: str
    expansion_radius: int
    replaced_nodes: tuple[str, ...]
    frontier_outputs: tuple[str, ...]
    interface_inputs: tuple[str, ...]
    residual_inputs: tuple[str, ...]
    truth_table_hashes: dict[str, str]
    rewrite_artifact: str
    rewrite_emitted: bool
    graph_active: bool
    graph_validation_status: str
    global_cec_status: str
    promotion: str
    blocker: str
    cec_source_status: str
    cec_rewrite_vs_optimized_status: str

    @property
    def new_boundary(self) -> bool:
        return self.rewrite_emitted and self.graph_active and self.global_cec_status == "equivalent"


def synthesize_compact_interface_rewrite(
    *,
    stable_target_id: str,
    source_path: Path,
    optimized_path: Path,
    optimized_target_node: str,
    tested_interface: tuple[str, ...],
    output_path: Path,
    root: Path,
    abc_path: Path,
) -> RewriteSynthesisResult:
    start = time.perf_counter()
    source = parse_blif(source_path)
    optimized = parse_blif(optimized_path)
    blocker = _preflight(source, optimized, optimized_target_node, tested_interface)
    if blocker:
        return _result(stable_target_id, optimized_target_node, tested_interface, "", 0, 0, output_path, False, False, "not_emitted", blocker, "not_run", "not_run", abc_path.exists(), start, root)

    table, conflict = _target_table(source, optimized, tested_interface, optimized_target_node)
    if conflict:
        return _result(stable_target_id, optimized_target_node, tested_interface, "", 0, 0, output_path, False, False, "not_emitted", conflict, "not_run", "not_run", abc_path.exists(), start, root)

    new_node = BlifNode(output=optimized_target_node, inputs=list(tested_interface), cover=_cover_from_table(table, len(tested_interface)))
    validation, graph_active, emitted, inactive_reason = _emit_rewrite(optimized, optimized_target_node, [new_node], output_path)
    if validation != "valid":
        return _result(stable_target_id, optimized_target_node, tested_interface, _hash_table(table), _onset(table), len(table), output_path, emitted, False, validation, validation, "not_run", "not_run", abc_path.exists(), start, root)

    source_cec, _ = _abc_cec(abc_path, source_path, output_path)
    rewrite_cec, _ = _abc_cec(abc_path, output_path, optimized_path)
    blocker = "" if graph_active and source_cec == "equivalent" and rewrite_cec == "equivalent" else _blocker(graph_active, source_cec, rewrite_cec, inactive_reason)
    return _result(stable_target_id, optimized_target_node, tested_interface, _hash_table(table), _onset(table), len(table), output_path, True, graph_active, validation, blocker, source_cec, rewrite_cec, abc_path.exists(), start, root)


def synthesize_fanout_frontier_rewrite(
    *,
    stable_target_id: str,
    source_path: Path,
    optimized_path: Path,
    optimized_target_node: str,
    tested_interface: tuple[str, ...],
    output_path: Path,
    root: Path,
    abc_path: Path,
    base_rewrite: RewriteSynthesisResult,
    expansion_radius: int = 1,
    max_replacement_outputs: int = 2,
    max_truth_table_inputs: int = 6,
) -> FrontierExpansionResult:
    if not (base_rewrite.rewrite_emitted and not base_rewrite.graph_active):
        return _frontier_result(
            stable_target_id,
            optimized_target_node,
            expansion_radius,
            tuple(),
            tuple(),
            tested_interface,
            tuple(),
            {},
            output_path,
            False,
            False,
            "not_run",
            "not_claimed",
            "not_attempted",
            "precondition_single_rewrite_already_graph_active_or_not_emitted",
            "not_run",
            "not_run",
            root,
        )
    if base_rewrite.cec_source_status != "equivalent" or base_rewrite.cec_rewrite_vs_optimized_status != "equivalent":
        return _frontier_result(
            stable_target_id,
            optimized_target_node,
            expansion_radius,
            tuple(),
            tuple(),
            tested_interface,
            tuple(),
            {},
            output_path,
            False,
            False,
            "not_run",
            "not_claimed",
            "not_attempted",
            "precondition_single_rewrite_not_cec_equivalent",
            base_rewrite.cec_source_status,
            base_rewrite.cec_rewrite_vs_optimized_status,
            root,
        )
    source = parse_blif(source_path)
    optimized = parse_blif(optimized_path)
    blocker = _preflight(source, optimized, optimized_target_node, tested_interface)
    if blocker:
        return _frontier_result(stable_target_id, optimized_target_node, expansion_radius, tuple(), tuple(), tested_interface, tuple(), {}, output_path, False, False, "not_emitted", "not_claimed", "not_attempted", blocker, "not_run", "not_run", root)
    if expansion_radius != 1:
        return _frontier_result(stable_target_id, optimized_target_node, expansion_radius, tuple(), tuple(), tested_interface, tuple(), {}, output_path, False, False, "not_emitted", "not_claimed", "not_attempted", "unsupported_expansion_radius", "not_run", "not_run", root)

    consumers = _candidate_frontier_consumers(optimized, optimized_target_node, max_replacement_outputs)
    if not consumers:
        return _frontier_result(stable_target_id, optimized_target_node, expansion_radius, tuple(), tuple(), tested_interface, tuple(), {}, output_path, False, False, "not_emitted", "not_claimed", "not_attempted", "no_non_output_fanout_consumer_under_bound", "not_run", "not_run", root)

    best_blocker = "no_valid_frontier_candidate"
    for frontier_outputs in consumers:
        replaced_nodes = (optimized_target_node, *frontier_outputs)
        if set(frontier_outputs) >= set(optimized.outputs):
            best_blocker = "whole_design_frontier_rejected"
            continue
        residual_inputs = _frontier_residual_inputs(optimized, set(replaced_nodes), tested_interface)
        rewrite_inputs = tuple(dict.fromkeys((*tested_interface, *residual_inputs)))
        if len(rewrite_inputs) > max_truth_table_inputs:
            best_blocker = "frontier_truth_table_input_bound_exceeded"
            continue
        target_table, conflict = _target_table(source, optimized, tested_interface, optimized_target_node)
        if conflict:
            best_blocker = conflict
            continue
        frontier_tables, conflict = _multi_output_tables(source, optimized, rewrite_inputs, frontier_outputs)
        if conflict:
            best_blocker = conflict
            continue
        new_nodes = [
            BlifNode(output=optimized_target_node, inputs=list(tested_interface), cover=_cover_from_table(target_table, len(tested_interface))),
            *[
                BlifNode(output=name, inputs=list(rewrite_inputs), cover=_cover_from_table(frontier_tables[name], len(rewrite_inputs)))
                for name in frontier_outputs
            ],
        ]
        validation, graph_active, emitted, inactive_reason = _emit_rewrite(optimized, optimized_target_node, new_nodes, output_path)
        hashes = {optimized_target_node: _hash_table(target_table), **{name: _hash_table(frontier_tables[name]) for name in frontier_outputs}}
        if validation != "valid":
            best_blocker = validation
            continue
        source_cec, _ = _abc_cec(abc_path, source_path, output_path)
        rewrite_cec, _ = _abc_cec(abc_path, output_path, optimized_path)
        global_cec = "equivalent" if source_cec == "equivalent" and rewrite_cec == "equivalent" else "not_claimed"
        blocker = "" if graph_active and global_cec == "equivalent" else _blocker(graph_active, source_cec, rewrite_cec, inactive_reason)
        promotion = "graph_active_cec_recovery" if not blocker else "frontier_rewrite_not_promoted"
        return _frontier_result(stable_target_id, optimized_target_node, expansion_radius, replaced_nodes, frontier_outputs, tested_interface, residual_inputs, hashes, output_path, emitted, graph_active, validation, global_cec, promotion, blocker, source_cec, rewrite_cec, root)
    if output_path.exists():
        output_path.unlink()
    return _frontier_result(stable_target_id, optimized_target_node, expansion_radius, tuple(), tuple(), tested_interface, tuple(), {}, output_path, False, False, "not_emitted", "not_claimed", "not_attempted", best_blocker, "not_run", "not_run", root)


def _preflight(source: BlifNetwork, optimized: BlifNetwork, target: str, interface: tuple[str, ...]) -> str:
    if source.inputs != optimized.inputs or source.outputs != optimized.outputs:
        return "primary_interface_mismatch"
    opt_names = set(all_signal_names(optimized))
    if target not in opt_names:
        return "target_missing"
    missing = [name for name in interface if name not in opt_names]
    if missing:
        return "interface_signal_missing_in_optimized:" + ",".join(missing)
    drivers = [node for node in optimized.nodes if node.output == target]
    if len(drivers) != 1:
        return "target_driver_count_not_one"
    return ""


def _target_table(source: BlifNetwork, optimized: BlifNetwork, interface: tuple[str, ...], target: str) -> tuple[dict[tuple[int, ...], int], str]:
    table: dict[tuple[int, ...], int] = {}
    for assignment in all_assignments(tuple(source.inputs)):
        source_values = scalar_eval_exact(source, assignment)
        key = tuple(int(source_values[name]) & 1 for name in interface)
        value = vector_eval(optimized, (target,), assignment)[0]
        if key in table and table[key] != value:
            return {}, "interface_not_functional_for_target"
        table[key] = value
    return table, ""


def _cover_from_table(table: dict[tuple[int, ...], int], width: int) -> list[str]:
    if width == 0:
        return ["1"] if table.get(tuple(), 0) else []
    return ["".join(str(bit) for bit in key) + " 1" for key, value in sorted(table.items()) if value]


def _emit_rewrite(net: BlifNetwork, target: str, new_nodes: list[BlifNode], output_path: Path) -> tuple[str, bool, bool, str]:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    replacements = {node.output: node for node in new_nodes}
    old_nodes: dict[str, BlifNode] = {}
    rewritten: list[BlifNode] = []
    for node in net.nodes:
        if node.output in replacements:
            old_nodes[node.output] = node
            rewritten.append(replacements[node.output])
        else:
            rewritten.append(node)
    if set(old_nodes) != set(replacements):
        return "target_driver_not_replaced", False, False, "target_driver_not_replaced"
    write_network(BlifNetwork(list(net.inputs), list(net.outputs), rewritten), output_path, model="necessity_first_rewrite")
    validation = validate_rewritten_graph(output_path, target)
    inactive_reasons = [_inactive_reason(old_nodes[node.output], node) for node in new_nodes]
    graph_active = validation == "valid" and any(reason == "" for reason in inactive_reasons)
    reason = "" if graph_active else _combined_inactive_reason(inactive_reasons)
    return validation, graph_active, output_path.exists(), reason


def validate_rewritten_graph(path: Path, target: str) -> str:
    if not path.exists():
        return "missing_rewrite_artifact"
    net = parse_blif(path)
    driven = [node.output for node in net.nodes]
    if len(driven) != len(set(driven)):
        return "duplicate_driver"
    known = set(net.inputs) | set(driven)
    dangling = sorted({fanin for node in net.nodes for fanin in node.inputs} - known)
    if dangling:
        return "dangling_fanin:" + ",".join(dangling)
    if _has_cycle(net):
        return "cycle"
    if target not in known:
        return "target_missing_after_rewrite"
    if not structural_path_to_output(net, target):
        return "target_not_output_reachable"
    return "valid"


def write_network(net: BlifNetwork, path: Path, *, model: str) -> None:
    lines = [f".model {model}", ".inputs " + " ".join(net.inputs), ".outputs " + " ".join(net.outputs)]
    for node in net.nodes:
        lines.append(".names " + " ".join([*node.inputs, node.output]))
        lines.extend(node.cover)
    lines.append(".end")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _has_cycle(net: BlifNetwork) -> bool:
    fanins = {node.output: tuple(node.inputs) for node in net.nodes}
    visiting: set[str] = set()
    visited: set[str] = set()

    def dfs(node: str) -> bool:
        if node in net.inputs or node in visited:
            return False
        if node in visiting:
            return True
        visiting.add(node)
        for fanin in fanins.get(node, ()):
            if dfs(fanin):
                return True
        visiting.remove(node)
        visited.add(node)
        return False

    return any(dfs(node.output) for node in net.nodes)


def _is_direct_bypass(node: BlifNode) -> bool:
    if len(node.inputs) != 1:
        return False
    return node.cover in (["1 1"], ["0 1"])


def _inactive_reason(old_node: BlifNode, new_node: BlifNode) -> str:
    if (tuple(old_node.inputs), tuple(old_node.cover)) == (tuple(new_node.inputs), tuple(new_node.cover)):
        return "identical_driver"
    if _is_direct_bypass(new_node):
        return "direct_bypass"
    return ""


def _combined_inactive_reason(reasons: list[str]) -> str:
    nonempty = [reason for reason in reasons if reason]
    if not nonempty:
        return "non_active_equivalent"
    unique = tuple(dict.fromkeys(nonempty))
    return unique[0] if len(unique) == 1 else "non_active_equivalent"


def _candidate_frontier_consumers(net: BlifNetwork, target: str, max_outputs: int) -> list[tuple[str, ...]]:
    consumers = [node.output for node in net.nodes if target in node.inputs]
    consumers = sorted(dict.fromkeys(consumers))
    candidates: list[tuple[str, ...]] = []
    for size in range(min(max_outputs, len(consumers)), 0, -1):
        if size == 1:
            candidates.extend((consumer,) for consumer in consumers)
        elif size == 2:
            candidates.extend((left, right) for idx, left in enumerate(consumers) for right in consumers[idx + 1 :])
    return candidates


def _frontier_residual_inputs(net: BlifNetwork, replaced: set[str], interface: tuple[str, ...]) -> tuple[str, ...]:
    interface_set = set(interface)
    residual: list[str] = []
    for node in net.nodes:
        if node.output not in replaced:
            continue
        for fanin in node.inputs:
            if fanin not in replaced and fanin not in interface_set:
                residual.append(fanin)
    return tuple(dict.fromkeys(residual))


def _multi_output_tables(source: BlifNetwork, optimized: BlifNetwork, inputs: tuple[str, ...], outputs: tuple[str, ...]) -> tuple[dict[str, dict[tuple[int, ...], int]], str]:
    tables: dict[str, dict[tuple[int, ...], int]] = {output: {} for output in outputs}
    for assignment in all_assignments(tuple(source.inputs)):
        values = scalar_eval_exact(optimized, assignment)
        missing = [name for name in (*inputs, *outputs) if name not in values]
        if missing:
            return {}, "frontier_signal_missing:" + ",".join(sorted(set(missing)))
        key = tuple(int(values[name]) & 1 for name in inputs)
        for output in outputs:
            value = int(values[output]) & 1
            table = tables[output]
            if key in table and table[key] != value:
                return {}, "frontier_interface_not_functional"
            table[key] = value
    return tables, ""


def _abc_cec(abc_path: Path, left: Path, right: Path) -> tuple[str, str]:
    if not abc_path.exists():
        return "abc_unavailable", ""
    proc = subprocess.run([str(abc_path), "-c", f"cec {left} {right}"], text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=10, check=False)
    text = proc.stdout
    if "Networks are equivalent" in text or "Networks are equivalent after" in text:
        return "equivalent", text
    if "Networks are NOT EQUIVALENT" in text or "not equivalent" in text.lower():
        return "disproved", text
    return "unknown", text


def _result(
    stable_target_id: str,
    target: str,
    interface: tuple[str, ...],
    table_hash: str,
    onset: int,
    total: int,
    output_path: Path,
    emitted: bool,
    active: bool,
    validation: str,
    blocker: str,
    source_cec: str,
    rewrite_cec: str,
    abc_available: bool,
    start: float,
    root: Path,
) -> RewriteSynthesisResult:
    artifact = _display_path(output_path, root) if emitted and output_path.exists() else ""
    return RewriteSynthesisResult(
        stable_target_id=stable_target_id,
        optimized_target_node=target,
        tested_interface=interface,
        truth_table_hash=table_hash,
        onset_size=onset,
        total_rows=total,
        rewrite_artifact=artifact,
        rewrite_emitted=emitted,
        graph_active=active,
        graph_validation_status=validation,
        blocker=blocker,
        cec_source_status=source_cec,
        cec_rewrite_vs_optimized_status=rewrite_cec,
        abc_available=abc_available,
        runtime_seconds=time.perf_counter() - start,
    )


def _hash_table(table: dict[tuple[int, ...], int]) -> str:
    payload = [("".join(str(bit) for bit in key), value) for key, value in sorted(table.items())]
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("ascii")).hexdigest()[:16]


def _onset(table: dict[tuple[int, ...], int]) -> int:
    return sum(1 for value in table.values() if value)


def _blocker(graph_active: bool, source_cec: str, rewrite_cec: str, inactive_reason: str = "") -> str:
    if not graph_active:
        return inactive_reason or "non_active_equivalent"
    if source_cec != "equivalent":
        return "source_vs_rewrite_cec_" + source_cec
    if rewrite_cec != "equivalent":
        return "rewrite_vs_optimized_cec_" + rewrite_cec
    return ""


def _frontier_result(
    stable_target_id: str,
    target: str,
    expansion_radius: int,
    replaced_nodes: tuple[str, ...],
    frontier_outputs: tuple[str, ...],
    interface_inputs: tuple[str, ...],
    residual_inputs: tuple[str, ...],
    hashes: dict[str, str],
    output_path: Path,
    emitted: bool,
    active: bool,
    validation: str,
    global_cec: str,
    promotion: str,
    blocker: str,
    source_cec: str,
    rewrite_cec: str,
    root: Path,
) -> FrontierExpansionResult:
    artifact = _display_path(output_path, root) if emitted and output_path.exists() else ""
    return FrontierExpansionResult(
        stable_target_id=stable_target_id,
        base_target_node=target,
        expansion_radius=expansion_radius,
        replaced_nodes=replaced_nodes,
        frontier_outputs=frontier_outputs,
        interface_inputs=interface_inputs,
        residual_inputs=residual_inputs,
        truth_table_hashes=hashes,
        rewrite_artifact=artifact,
        rewrite_emitted=emitted,
        graph_active=active,
        graph_validation_status=validation,
        global_cec_status=global_cec,
        promotion=promotion,
        blocker=blocker,
        cec_source_status=source_cec,
        cec_rewrite_vs_optimized_status=rewrite_cec,
    )


def _display_path(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)
