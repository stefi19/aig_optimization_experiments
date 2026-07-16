"""Exact target-function extraction over small anchored cuts."""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass

from analyze_blif_matches import BlifNetwork, eval_cover
from contextual_error_metrics import PatternSet, evaluate_network, exact_patterns


@dataclass(frozen=True)
class CutFunction:
    cut_id: str
    target_impl_node: str
    truth_table: tuple[int, ...]
    truth_table_hash: str
    support_leaf_order: tuple[str, ...]
    local_cone_nodes: tuple[str, ...]
    local_cone_size: int
    extraction_backend: str
    extraction_status: str
    failure_reason: str
    runtime_seconds: float


def extract_cut_truth_table(
    impl_net: BlifNetwork,
    *,
    target_impl_node: str,
    cut_id: str,
    impl_leaf_nodes: tuple[str, ...],
    exact_input_limit: int = 12,
) -> CutFunction:
    """Extract ``target`` as a deterministic truth table over cut leaves.

    This is exact over all primary-input assignments when the implementation
    circuit is within ``exact_input_limit``.  If one cut-leaf assignment maps to
    two target values, hidden support remains and the cut is rejected.
    """

    start = time.perf_counter()
    if len(impl_net.inputs) > exact_input_limit:
        return _failed(cut_id, target_impl_node, impl_leaf_nodes, start, "support_too_large_without_sampling")
    node_names = {node.output for node in impl_net.nodes} | set(impl_net.inputs) | set(impl_net.outputs)
    missing = [node for node in [target_impl_node, *impl_leaf_nodes] if node not in node_names]
    if missing:
        return _failed(cut_id, target_impl_node, impl_leaf_nodes, start, "missing_node:" + ";".join(sorted(missing)))
    patterns = exact_patterns(list(impl_net.inputs))
    values = evaluate_network(impl_net, patterns)
    if target_impl_node not in values:
        return _failed(cut_id, target_impl_node, impl_leaf_nodes, start, "missing_target_value")
    missing_values = [node for node in impl_leaf_nodes if node not in values]
    if missing_values:
        return _failed(cut_id, target_impl_node, impl_leaf_nodes, start, "missing_leaf_value:" + ";".join(missing_values))
    table: list[int | None] = [None] * (1 << len(impl_leaf_nodes))
    for pattern_index in range(patterns.pattern_count):
        leaf_index = 0
        for bit, leaf in enumerate(impl_leaf_nodes):
            if (values[leaf] >> pattern_index) & 1:
                leaf_index |= 1 << bit
        target_bit = (values[target_impl_node] >> pattern_index) & 1
        previous = table[leaf_index]
        if previous is not None and previous != target_bit:
            return _failed(cut_id, target_impl_node, impl_leaf_nodes, start, "hidden_support")
        table[leaf_index] = target_bit
    completed = tuple(0 if bit is None else int(bit) for bit in table)
    digest = hashlib.sha256("".join(str(bit) for bit in completed).encode("ascii")).hexdigest()[:16]
    local = _local_cone_nodes(impl_net, target_impl_node, set(impl_leaf_nodes))
    return CutFunction(
        cut_id=cut_id,
        target_impl_node=target_impl_node,
        truth_table=completed,
        truth_table_hash=digest,
        support_leaf_order=impl_leaf_nodes,
        local_cone_nodes=tuple(sorted(local)),
        local_cone_size=len(local),
        extraction_backend="truth_table_exhaustive",
        extraction_status="extracted",
        failure_reason="",
        runtime_seconds=time.perf_counter() - start,
    )


def evaluate_blif_node(net: BlifNetwork, node_name: str, patterns: PatternSet) -> int | None:
    values = dict(patterns.values)
    for node in net.nodes:
        values[node.output] = eval_cover(node, values, patterns.mask)
    return values.get(node_name)


def cut_function_to_row(fn: CutFunction, *, case_id: str, benchmark: str, optimization: str, coi_name: str) -> dict[str, object]:
    return {
        "case_id": case_id,
        "benchmark": benchmark,
        "optimization": optimization,
        "coi_name": coi_name,
        "cut_id": fn.cut_id,
        "target_impl_node": fn.target_impl_node,
        "truth_table": "".join(str(bit) for bit in fn.truth_table),
        "truth_table_hash": fn.truth_table_hash,
        "support_leaf_order": ";".join(fn.support_leaf_order),
        "local_cone_nodes": ";".join(fn.local_cone_nodes),
        "local_cone_size": fn.local_cone_size,
        "extraction_backend": fn.extraction_backend,
        "extraction_status": fn.extraction_status,
        "failure_reason": fn.failure_reason,
        "runtime_seconds": f"{fn.runtime_seconds:.6f}",
    }


def _failed(cut_id: str, target: str, leaves: tuple[str, ...], start: float, reason: str) -> CutFunction:
    return CutFunction(
        cut_id=cut_id,
        target_impl_node=target,
        truth_table=tuple(),
        truth_table_hash="",
        support_leaf_order=leaves,
        local_cone_nodes=tuple(),
        local_cone_size=0,
        extraction_backend="truth_table_exhaustive",
        extraction_status="failed",
        failure_reason=reason,
        runtime_seconds=time.perf_counter() - start,
    )


def _local_cone_nodes(net: BlifNetwork, target: str, leaves: set[str]) -> set[str]:
    by_output = {node.output: node for node in net.nodes}
    out: set[str] = set()

    def visit(node_name: str) -> None:
        if node_name in leaves or node_name not in by_output or node_name in out:
            return
        out.add(node_name)
        for fanin in by_output[node_name].inputs:
            visit(fanin)

    visit(target)
    return out
