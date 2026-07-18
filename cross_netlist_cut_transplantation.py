"""Bounded cross-netlist cut transplantation.

The utilities here implement a small exact BLIF-level transplantation model:

    AS,Zin -> Ein -> AI -> cloned RI -> BI,Zout -> Eout -> BS

The implementation is intentionally bounded and proof-carrying.  It is not a
general ECO engine, but every accepted construction is graph-active and checked
against the original and optimized primary-output behavior.
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable, Iterable

from analyze_blif_matches import BlifNetwork, BlifNode, parse_blif
from active_source_counterpart_refactoring import prove_cross_node_equivalence, stable_hash
from semantic_functional_refactoring import eval_outputs, scalar_eval


SCHEMA_VERSION = "cross_netlist_cut_transplantation_v1"
Assignment = dict[str, int]
VectorFn = Callable[[Assignment], tuple[int, ...]]


@dataclass(frozen=True)
class CrossNetlistTransplantCandidate:
    candidate_id: str
    benchmark: str
    optimization_flow: str
    split: str
    optimized_target: str
    target_selection_reason: str
    optimized_region: tuple[str, ...]
    source_region: tuple[str, ...]
    optimized_input_cut: tuple[str, ...]
    source_input_cut: tuple[str, ...]
    optimized_output_cut: tuple[str, ...]
    source_output_cut: tuple[str, ...]
    input_residuals: tuple[str, ...]
    output_residuals: tuple[str, ...]
    input_adapter_id: str
    output_adapter_id: str
    target_polarity: str
    cloned_region_nodes: tuple[str, ...]
    parent_search_state: str
    proposal_operator: str
    counterexample_history: tuple[str, ...]
    proof_statuses: dict[str, str]
    graph_rewrite_status: str
    activity_status: str
    boundary_utility: str
    critical_path_utility: str
    durability_status: str
    area_delta: int
    depth_delta: int
    runtime_seconds: float
    rejection_reason: str
    source_blind: bool = True
    oracle_mode: str = "blind"
    schema_version: str = SCHEMA_VERSION

    @property
    def fingerprint(self) -> str:
        payload = asdict(self)
        payload.pop("runtime_seconds", None)
        return stable_hash(payload)

    def to_row(self) -> dict[str, str]:
        data = asdict(self)
        data["fingerprint"] = self.fingerprint
        return {key: _csv(value) for key, value in data.items()}


@dataclass(frozen=True)
class AdapterSynthesisResult:
    adapter_id: str
    adapter_kind: str
    mode: str
    input_order: tuple[str, ...]
    output_order: tuple[str, ...]
    rows: tuple[tuple[str, str], ...]
    existence_status: str
    solver_result: str
    proof_status: str
    counterexample: dict[str, object]
    counterexample_reproduced: bool
    backend: str
    runtime_seconds: float
    rejection_reason: str
    schema_version: str = SCHEMA_VERSION

    @property
    def output_width(self) -> int:
        return len(self.output_order)


def synthesize_exact_adapter(
    *,
    adapter_id: str,
    adapter_kind: str,
    mode: str,
    primary_inputs: tuple[str, ...],
    interface_inputs: tuple[str, ...],
    output_order: tuple[str, ...],
    output_fn: VectorFn,
    interface_fn: Callable[[Assignment], tuple[int, ...]] | None = None,
    max_inputs: int = 10,
) -> AdapterSynthesisResult:
    start = time.perf_counter()
    if len(interface_inputs) > max_inputs:
        return AdapterSynthesisResult(adapter_id, adapter_kind, mode, interface_inputs, output_order, tuple(), "unsupported", "not_run", "not_proven", {}, True, "truth_table_exact", time.perf_counter() - start, "interface_width_exceeds_bound")
    mapping: dict[tuple[int, ...], tuple[int, ...]] = {}
    for assignment in all_assignments(primary_inputs):
        key = tuple(interface_fn(assignment) if interface_fn else tuple(assignment.get(name, 0) for name in interface_inputs))
        value = tuple(int(bit) & 1 for bit in output_fn(assignment))
        if key in mapping and mapping[key] != value:
            cex = {"a": dict(assignment), "interface": key, "old": mapping[key], "new": value}
            return AdapterSynthesisResult(adapter_id, adapter_kind, mode, interface_inputs, output_order, tuple(), "insufficient_interface", "sat", "disproven", cex, True, "truth_table_exact", time.perf_counter() - start, "two_copy_counterexample")
        mapping[key] = value
    rows = tuple(sorted((bits_to_string(key), bits_to_string(value)) for key, value in mapping.items()))
    return AdapterSynthesisResult(adapter_id, adapter_kind, mode, interface_inputs, output_order, rows, "adapter_exists", "unsat", "proven", {}, True, "truth_table_exact", time.perf_counter() - start, "")


def emit_adapter_blif_nodes(adapter: AdapterSynthesisResult, *, output_prefix: str = "") -> list[BlifNode]:
    nodes: list[BlifNode] = []
    table = {key: value for key, value in adapter.rows}
    for out_idx, output in enumerate(adapter.output_order):
        cover = [key + " 1" for key, value in table.items() if value[out_idx] == "1"]
        nodes.append(BlifNode(output=f"{output_prefix}{output}", inputs=list(adapter.input_order), cover=cover))
    return nodes


def write_truth_blif(path: Path, model: str, inputs: tuple[str, ...], outputs: tuple[str, ...], fn: VectorFn) -> None:
    nodes: list[BlifNode] = []
    for out_idx, output in enumerate(outputs):
        cover = []
        for assignment in all_assignments(inputs):
            if fn(assignment)[out_idx]:
                cover.append("".join(str(assignment[name]) for name in inputs) + " 1")
        nodes.append(BlifNode(output=output, inputs=list(inputs), cover=cover))
    write_network(BlifNetwork(list(inputs), list(outputs), nodes), path, model=model)


def build_region_net(
    *,
    path: Path,
    model: str,
    ai: tuple[str, ...],
    bi: tuple[str, ...],
    target: str,
    target_fn: VectorFn,
    bi_fn: VectorFn,
) -> None:
    target_cover = []
    bi_covers = [[] for _ in bi]
    for assignment in all_assignments(ai):
        if target_fn(assignment)[0]:
            target_cover.append("".join(str(assignment[name]) for name in ai) + " 1")
        for idx, bit in enumerate(bi_fn(assignment)):
            if bit:
                bi_covers[idx].append("".join(str(assignment[name]) for name in ai) + " 1")
    nodes = [BlifNode(output=target, inputs=list(ai), cover=target_cover)]
    for idx, output in enumerate(bi):
        nodes.append(BlifNode(output=output, inputs=[target, *ai], cover=_lift_bi_cover(ai, target, bi_covers[idx], target_fn)))
    write_network(BlifNetwork(list(ai), list(bi), nodes), path, model=model)


def build_implementation_with_region(
    *,
    impl_path: Path,
    primary_inputs: tuple[str, ...],
    source_outputs: tuple[str, ...],
    input_adapter: AdapterSynthesisResult,
    region_path: Path,
    output_adapter: AdapterSynthesisResult,
    model: str,
) -> None:
    region = parse_blif(region_path)
    nodes: list[BlifNode] = []
    nodes.extend(emit_adapter_blif_nodes(input_adapter))
    nodes.extend(region.nodes)
    nodes.extend(emit_adapter_blif_nodes(output_adapter))
    write_network(BlifNetwork(list(primary_inputs), list(source_outputs), nodes), impl_path, model=model)


def transplant_region_into_source(
    *,
    source_path: Path,
    region_path: Path,
    input_adapter: AdapterSynthesisResult,
    output_adapter: AdapterSynthesisResult,
    output_path: Path,
    clone_prefix: str = "xri_",
) -> dict[str, str]:
    source = parse_blif(source_path)
    region = parse_blif(region_path)
    input_nodes = emit_adapter_blif_nodes(input_adapter, output_prefix=clone_prefix)
    ai_map = {name: f"{clone_prefix}{name}" for name in region.inputs}
    clone_map = {node.output: f"{clone_prefix}{node.output}" for node in region.nodes}
    region_nodes: list[BlifNode] = []
    for node in region.nodes:
        inputs = [clone_map.get(fanin, ai_map.get(fanin, fanin)) for fanin in node.inputs]
        region_nodes.append(BlifNode(output=clone_map[node.output], inputs=inputs, cover=list(node.cover)))
    bi_map = {name: clone_map.get(name, f"{clone_prefix}{name}") for name in region.outputs}
    eout_inputs = [bi_map.get(name, name) for name in output_adapter.input_order]
    eout_nodes = []
    for node in emit_adapter_blif_nodes(output_adapter):
        remapped = [bi_map.get(fanin, fanin) for fanin in node.inputs]
        eout_nodes.append(BlifNode(output=node.output, inputs=remapped, cover=node.cover))
    removed_outputs = set(output_adapter.output_order)
    preserved_nodes = [node for node in source.nodes if node.output not in removed_outputs]
    net = BlifNetwork(list(source.inputs), list(source.outputs), [*preserved_nodes, *input_nodes, *region_nodes, *eout_nodes])
    write_network(net, output_path, model="cross_netlist_transplant")
    return validate_transplant_graph(output_path, target_node=f"{clone_prefix}t", bi_nodes=tuple(bi_map.values()), source_outputs=tuple(source.outputs), removed_source_nodes=tuple(removed_outputs))


def validate_transplant_graph(path: Path, *, target_node: str, bi_nodes: tuple[str, ...], source_outputs: tuple[str, ...], removed_source_nodes: tuple[str, ...]) -> dict[str, str]:
    if not path.exists():
        return _graph_row("invalid_missing_transplant", False, False, False, "missing_transplant")
    net = parse_blif(path)
    driven = [node.output for node in net.nodes]
    if len(driven) != len(set(driven)):
        return _graph_row("invalid_multiple_driver", False, False, False, "multiple_driver")
    known = set(net.inputs) | set(driven)
    dangling = sorted({fanin for node in net.nodes for fanin in node.inputs} - known)
    if dangling:
        return _graph_row("invalid_dangling_net", False, False, False, "dangling_net:" + ";".join(dangling))
    if has_cycle(net):
        return _graph_row("invalid_cycle", False, False, False, "cycle")
    if target_node not in known:
        return _graph_row("invalid_missing_cloned_target", False, False, True, "missing_cloned_target")
    target_consumers = [node.output for node in net.nodes if target_node in node.inputs]
    bi_consumers = [node.output for node in net.nodes if any(bi in node.inputs for bi in bi_nodes)]
    active = bool(target_consumers) and bool(bi_consumers)
    outputs_replaced = bool(set(removed_source_nodes) & set(source_outputs))
    return _graph_row("valid", active, active and outputs_replaced, True, "", sorted(set(target_consumers + bi_consumers)))


def prove_primary_output_equivalence(left: Path, right: Path, *, exact_input_limit: int = 12) -> dict[str, str]:
    start = time.perf_counter()
    lnet, rnet = parse_blif(left), parse_blif(right)
    if lnet.inputs != rnet.inputs or lnet.outputs != rnet.outputs:
        return _proof_row("alignment_failure", "not_run", "exhaustive_output_miter", start, "primary_interface_mismatch")
    if len(lnet.inputs) > exact_input_limit:
        return _proof_row("unsupported", "not_run", "exhaustive_output_miter", start, "support_too_large")
    for assignment in all_assignments(tuple(lnet.inputs)):
        if eval_outputs(lnet, tuple(lnet.outputs), assignment) != eval_outputs(rnet, tuple(rnet.outputs), assignment):
            return _proof_row("disproven", "sat_exhaustive", "exhaustive_output_miter", start, "output_mismatch", {"assignment": assignment}, True)
    return _proof_row("equivalent", "unsat_exhaustive", "exhaustive_output_miter", start, "")


def target_influences_output(region_path: Path, *, target: str, output_nodes: tuple[str, ...]) -> dict[str, str]:
    net = parse_blif(region_path)
    fanouts = {node.output: set() for node in net.nodes}
    for node in net.nodes:
        for fanin in node.inputs:
            fanouts.setdefault(fanin, set()).add(node.output)
    seen = set()
    stack = [target]
    while stack:
        node = stack.pop()
        for fanout in sorted(fanouts.get(node, ())):
            if fanout not in seen:
                seen.add(fanout)
                stack.append(fanout)
    influenced = sorted(set(output_nodes) & seen)
    return {"target_influence_status": "influences_bi" if influenced else "target_not_influential", "influenced_outputs": json.dumps(influenced), "schema_version": SCHEMA_VERSION}


def adapter_depends_on_inputs(adapter: AdapterSynthesisResult, required_prefixes: tuple[str, ...]) -> bool:
    if not adapter.rows:
        return False
    width = len(adapter.input_order)
    table = {key: value for key, value in adapter.rows}
    required_indices = [idx for idx, name in enumerate(adapter.input_order) if any(name.startswith(prefix) for prefix in required_prefixes)]
    for idx in required_indices:
        for key, value in table.items():
            flipped = list(key)
            flipped[idx] = "1" if key[idx] == "0" else "0"
            if table.get("".join(flipped), value) != value:
                return True
    return False


def gf2_affine_adapter(adapter: AdapterSynthesisResult) -> dict[str, str]:
    if adapter.existence_status != "adapter_exists" or not adapter.rows:
        return {"adapter_id": adapter.adapter_id, "backend": "gf2_linear_relational_baseline", "linearity_status": "not_run", "matrix_rows": "0", "matrix_cols": "0", "rank": "0", "nullity": "0", "solution": "{}", "proof_status": "not_proven", "rejection_reason": "adapter_not_available", "schema_version": SCHEMA_VERSION}
    table = {key: value for key, value in adapter.rows}
    width = len(adapter.input_order)
    constants = table.get("0" * width, "0" * adapter.output_width)
    coeffs: list[list[int]] = []
    for out_idx in range(adapter.output_width):
        row = []
        for in_idx in range(width):
            key = ["0"] * width
            key[in_idx] = "1"
            row.append(int(table.get("".join(key), constants)[out_idx]) ^ int(constants[out_idx]))
        coeffs.append(row)
    for key, value in table.items():
        for out_idx in range(adapter.output_width):
            pred = int(constants[out_idx])
            for in_idx, bit in enumerate(key):
                pred ^= coeffs[out_idx][in_idx] & int(bit)
            if pred != int(value[out_idx]):
                return {"adapter_id": adapter.adapter_id, "backend": "gf2_linear_relational_baseline", "linearity_status": "rejected_nonlinear", "matrix_rows": str(adapter.output_width), "matrix_cols": str(width), "rank": str(_rank_gf2(coeffs)), "nullity": str(max(0, width - _rank_gf2(coeffs))), "solution": json.dumps({"constant": constants, "coefficients": coeffs}, sort_keys=True), "proof_status": "disproven_nonlinear", "rejection_reason": "nonlinear_counterexample", "schema_version": SCHEMA_VERSION}
    rank = _rank_gf2(coeffs)
    return {"adapter_id": adapter.adapter_id, "backend": "gf2_linear_relational_baseline", "linearity_status": "proved_affine", "matrix_rows": str(adapter.output_width), "matrix_cols": str(width), "rank": str(rank), "nullity": str(max(0, width - rank)), "solution": json.dumps({"constant": constants, "coefficients": coeffs}, sort_keys=True), "proof_status": "proved", "rejection_reason": "", "schema_version": SCHEMA_VERSION}


def write_network(net: BlifNetwork, path: Path, *, model: str = "network") -> None:
    lines = [f".model {model}", ".inputs " + " ".join(net.inputs), ".outputs " + " ".join(net.outputs)]
    for node in net.nodes:
        lines.append(".names " + " ".join([*node.inputs, node.output]))
        lines.extend(node.cover)
    lines.append(".end")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def all_assignments(inputs: tuple[str, ...]) -> Iterable[Assignment]:
    for value in range(1 << len(inputs)):
        yield {name: (value >> idx) & 1 for idx, name in enumerate(inputs)}


def bits_to_string(bits: Iterable[int]) -> str:
    return "".join(str(int(bit)) for bit in bits)


def has_cycle(net: BlifNetwork) -> bool:
    fanins = {node.output: tuple(node.inputs) for node in net.nodes}
    visiting: set[str] = set()
    visited: set[str] = set()

    def dfs(node: str) -> bool:
        if node in visited or node in net.inputs:
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


def _lift_bi_cover(ai: tuple[str, ...], target: str, cover: list[str], target_fn: VectorFn) -> list[str]:
    lifted = []
    for assignment in all_assignments(ai):
        pattern = "".join(str(assignment[name]) for name in ai)
        if f"{pattern} 1" not in cover:
            continue
        tbit = target_fn(assignment)[0]
        lifted.append(str(tbit) + pattern + " 1")
    return lifted


def _rank_gf2(matrix: list[list[int]]) -> int:
    rows = [row[:] for row in matrix if any(row)]
    if not rows:
        return 0
    rank = 0
    col = 0
    width = len(rows[0])
    while col < width and rank < len(rows):
        pivot = next((idx for idx in range(rank, len(rows)) if rows[idx][col]), None)
        if pivot is None:
            col += 1
            continue
        rows[rank], rows[pivot] = rows[pivot], rows[rank]
        for idx in range(len(rows)):
            if idx != rank and rows[idx][col]:
                rows[idx] = [a ^ b for a, b in zip(rows[idx], rows[rank])]
        rank += 1
        col += 1
    return rank


def _proof_row(status: str, solver_result: str, backend: str, start: float, reason: str, counterexample: dict[str, object] | None = None, reproduced: bool = False) -> dict[str, str]:
    return {
        "formal_status": status,
        "solver_result": solver_result,
        "formal_backend": backend,
        "formal_evidence_level": "formal_exhaustive" if status in {"equivalent", "disproven"} else "unresolved",
        "counterexample_available": str(counterexample is not None).lower(),
        "counterexample": json.dumps(counterexample or {}, sort_keys=True),
        "counterexample_reproduced": str(reproduced or counterexample is None).lower(),
        "runtime_seconds": f"{time.perf_counter() - start:.6f}",
        "timeout": "false",
        "unsupported_reason": reason,
        "schema_version": SCHEMA_VERSION,
    }


def _graph_row(status: str, active: bool, influence: bool, cycle_free: bool, reason: str, consumers: list[str] | None = None) -> dict[str, str]:
    return {
        "graph_rewrite_status": status,
        "graph_active": str(active).lower(),
        "functional_influence": str(influence).lower(),
        "cycle_free": str(cycle_free).lower(),
        "target_consumers": json.dumps(consumers or [], sort_keys=True),
        "bypass_status": "no_bypass_detected" if active and influence else "inactive_or_bypassed",
        "failure_reason": reason,
        "schema_version": SCHEMA_VERSION,
    }


def _csv(value: object) -> str:
    if isinstance(value, (tuple, list, dict)):
        return json.dumps(value, sort_keys=True)
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, float):
        return f"{value:.6f}"
    return str(value)
