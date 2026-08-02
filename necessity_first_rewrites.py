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
    validation, graph_active, emitted = _emit_rewrite(optimized, optimized_target_node, new_node, output_path)
    if validation != "valid":
        return _result(stable_target_id, optimized_target_node, tested_interface, _hash_table(table), _onset(table), len(table), output_path, emitted, False, validation, validation, "not_run", "not_run", abc_path.exists(), start, root)

    source_cec, _ = _abc_cec(abc_path, source_path, output_path)
    rewrite_cec, _ = _abc_cec(abc_path, output_path, optimized_path)
    blocker = "" if graph_active and source_cec == "equivalent" and rewrite_cec == "equivalent" else _blocker(graph_active, source_cec, rewrite_cec)
    return _result(stable_target_id, optimized_target_node, tested_interface, _hash_table(table), _onset(table), len(table), output_path, True, graph_active, validation, blocker, source_cec, rewrite_cec, abc_path.exists(), start, root)


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


def _emit_rewrite(net: BlifNetwork, target: str, new_node: BlifNode, output_path: Path) -> tuple[str, bool, bool]:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    rewritten: list[BlifNode] = []
    replaced = False
    old_node: BlifNode | None = None
    for node in net.nodes:
        if node.output == target and not replaced:
            old_node = node
            rewritten.append(new_node)
            replaced = True
        elif node.output != target:
            rewritten.append(node)
    if not replaced or old_node is None:
        return "target_driver_not_replaced", False, False
    write_network(BlifNetwork(list(net.inputs), list(net.outputs), rewritten), output_path, model="necessity_first_rewrite")
    validation = validate_rewritten_graph(output_path, target)
    structurally_changed = (tuple(old_node.inputs), tuple(old_node.cover)) != (tuple(new_node.inputs), tuple(new_node.cover))
    bypass = _is_direct_bypass(new_node)
    return validation, validation == "valid" and structurally_changed and not bypass, output_path.exists()


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


def _blocker(graph_active: bool, source_cec: str, rewrite_cec: str) -> str:
    if not graph_active:
        return "rewrite_not_graph_active"
    if source_cec != "equivalent":
        return "source_vs_rewrite_cec_" + source_cec
    if rewrite_cec != "equivalent":
        return "rewrite_vs_optimized_cec_" + rewrite_cec
    return ""


def _display_path(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)
