"""Equivalence-anchored hierarchical boundary recovery prototype."""

from __future__ import annotations

import json
import time
from collections import deque
from dataclasses import dataclass
from pathlib import Path

from boundary_anchor_map import Anchor, AnchorMap
from boundary_graph import CircuitGraph


VALIDATION_STATUSES = {
    "valid",
    "no_input_cut",
    "no_output_cut",
    "incomplete_input_cut",
    "incomplete_output_cut",
    "missing_anchor",
    "polarity_unsupported",
    "cycle_detected",
    "whole_design_boundary",
    "disconnected_region",
    "invalid_coi",
}


@dataclass(frozen=True)
class CoiSpec:
    benchmark: str
    optimization: str
    coi_name: str
    coi_internal_nodes: tuple[str, ...]
    boundary_inputs: tuple[str, ...]
    boundary_outputs: tuple[str, ...]
    source: str


@dataclass(frozen=True)
class BoundaryRecoveryResult:
    coi: CoiSpec
    extended_boundary_inputs: tuple[str, ...]
    extended_boundary_outputs: tuple[str, ...]
    region_nodes: tuple[str, ...]
    selected_anchors: dict[str, Anchor]
    validation_status: str
    failure_reason: str
    cycle_resolution_iterations: int
    cycle_conflict_count: int
    invalidated_anchor_count: int
    cycle_resolution_status: str
    runtime_seconds: float


def load_coi_specs(path: Path) -> list[CoiSpec]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    items = raw if isinstance(raw, list) else raw.get("cois", [])
    specs = []
    for item in items:
        specs.append(
            CoiSpec(
                benchmark=str(item["benchmark"]),
                optimization=str(item.get("optimization", "")),
                coi_name=str(item["coi_name"]),
                coi_internal_nodes=tuple(item.get("coi_internal_nodes", [])),
                boundary_inputs=tuple(item.get("boundary_inputs", [])),
                boundary_outputs=tuple(item.get("boundary_outputs", [])),
                source=str(item.get("source", "manual_case_study")),
            )
        )
    return specs


def validate_coi_spec(graph: CircuitGraph, coi: CoiSpec) -> tuple[bool, str]:
    if not coi.coi_internal_nodes:
        return False, "invalid_coi"
    for node in [*coi.coi_internal_nodes, *coi.boundary_inputs, *coi.boundary_outputs]:
        if not graph.exists(node):
            return False, f"missing_node:{node}"
    if not set(coi.coi_internal_nodes).isdisjoint(coi.boundary_inputs):
        return False, "invalid_boundary_input"
    if not set(coi.boundary_outputs).issubset(set(coi.coi_internal_nodes) | set(graph.nodes)):
        return False, "invalid_boundary_output"
    return True, "valid"


def first_equivalent_cut_tfi(graph: CircuitGraph, roots: list[str], anchors: AnchorMap) -> tuple[set[str], dict[str, int], list[str]]:
    cut: set[str] = set()
    distances: dict[str, int] = {}
    failures: list[str] = []
    for root in sorted(roots):
        queue: deque[tuple[str, int]] = deque([(root, 0)])
        seen: set[str] = set()
        found = False
        while queue:
            node, distance = queue.popleft()
            if node in seen:
                continue
            seen.add(node)
            if anchors.has_anchor(node):
                cut.add(node)
                distances[node] = min(distance, distances.get(node, distance))
                found = True
                break
            for fanin in sorted(graph.fanins.get(node, tuple())):
                queue.append((fanin, distance + 1))
        if not found:
            failures.append(root)
    return cut, distances, failures


def first_equivalent_cut_tfo(graph: CircuitGraph, roots: list[str], anchors: AnchorMap) -> tuple[set[str], dict[str, int], list[str]]:
    cut: set[str] = set()
    distances: dict[str, int] = {}
    failures: list[str] = []
    for root in sorted(roots):
        queue: deque[tuple[str, int]] = deque([(root, 0)])
        seen: set[str] = set()
        found = False
        while queue:
            node, distance = queue.popleft()
            if node in seen:
                continue
            seen.add(node)
            if anchors.has_anchor(node):
                cut.add(node)
                distances[node] = min(distance, distances.get(node, distance))
                found = True
                break
            for fanout in sorted(graph.fanouts.get(node, tuple())):
                queue.append((fanout, distance + 1))
        if not found:
            failures.append(root)
    return cut, distances, failures


def first_equivalent_cut_tsi(
    graph: CircuitGraph,
    outputs: set[str],
    existing_inputs: set[str],
    anchors: AnchorMap,
    blocked_outputs: set[str] | None = None,
) -> tuple[set[str], dict[str, int], list[str]]:
    """Complete input cut by walking backward from EBOs to first anchored nodes."""

    blocked = set(blocked_outputs or set())
    additions: set[str] = set()
    distances: dict[str, int] = {}
    failures: list[str] = []
    for output in sorted(outputs):
        queue: deque[tuple[str, int]] = deque([(fanin, 1) for fanin in sorted(graph.fanins.get(output, tuple()))])
        seen: set[str] = set()
        while queue:
            node, distance = queue.popleft()
            if node in seen or node in existing_inputs or node in blocked:
                continue
            seen.add(node)
            if anchors.has_anchor(node):
                additions.add(node)
                distances[node] = min(distance, distances.get(node, distance))
                continue
            fanins = graph.fanins.get(node, tuple())
            if not fanins:
                failures.append(node)
                continue
            for fanin in sorted(fanins):
                queue.append((fanin, distance + 1))
    return additions, distances, failures


def extract_region_between_cuts(graph: CircuitGraph, ebi: set[str], ebo: set[str]) -> set[str]:
    region: set[str] = set()
    stack = list(sorted(ebo))
    while stack:
        node = stack.pop()
        if node in ebi or node in region:
            continue
        region.add(node)
        for fanin in sorted(graph.fanins.get(node, tuple()), reverse=True):
            if fanin not in ebi:
                stack.append(fanin)
    return region


def validate_recovered_boundary(
    graph: CircuitGraph,
    impl_graph: CircuitGraph,
    coi: CoiSpec,
    ebi: set[str],
    ebo: set[str],
    region: set[str],
    anchors: AnchorMap,
) -> tuple[str, str, list[tuple[str, str]]]:
    if not ebi:
        return "no_input_cut", "no anchored extended boundary inputs", []
    if not ebo:
        return "no_output_cut", "no anchored extended boundary outputs", []
    for node in ebi | ebo:
        if not graph.exists(node):
            return "invalid_coi", f"boundary node {node!r} missing in specification", []
        if anchors.selected_for(node) is None:
            return "missing_anchor", f"boundary node {node!r} has no selected anchor", []
    if not set(coi.coi_internal_nodes).issubset(region | ebi):
        return "disconnected_region", "COI nodes are not enclosed by recovered region", []
    if not region:
        return "disconnected_region", "recovered region is empty", []
    if len(region) >= max(1, len([n for n in graph.nodes if n not in graph.inputs])):
        return "whole_design_boundary", "recovered region expands to nearly the whole design", []
    for output in ebo:
        if not _all_backward_paths_cut(graph, output, ebi):
            return "incomplete_input_cut", f"not every fanin path to {output!r} crosses EBI", []
    for node in coi.coi_internal_nodes:
        if not _all_forward_paths_cut(graph, node, ebo):
            return "incomplete_output_cut", f"not every fanout path from {node!r} crosses EBO", []
    conflicts = detect_mapped_boundary_cycles(impl_graph, ebi, ebo, anchors)
    if conflicts:
        return "cycle_detected", "mapped EBI anchor is in transitive fanout of mapped EBO anchor", conflicts
    return "valid", "valid", []


def _all_backward_paths_cut(graph: CircuitGraph, root: str, cut: set[str]) -> bool:
    stack = [root]
    seen: set[str] = set()
    while stack:
        node = stack.pop()
        if node in cut:
            continue
        if node in seen:
            continue
        seen.add(node)
        fanins = graph.fanins.get(node, tuple())
        if not fanins and node not in cut:
            return False
        stack.extend(fanins)
    return True


def _all_forward_paths_cut(graph: CircuitGraph, root: str, cut: set[str]) -> bool:
    stack = [root]
    seen: set[str] = set()
    while stack:
        node = stack.pop()
        if node in cut:
            continue
        if node in seen:
            continue
        seen.add(node)
        fanouts = graph.fanouts.get(node, tuple())
        if not fanouts and node not in cut:
            return False
        stack.extend(fanouts)
    return True


def detect_mapped_boundary_cycles(
    impl_graph: CircuitGraph,
    ebi: set[str],
    ebo: set[str],
    anchors: AnchorMap,
) -> list[tuple[str, str]]:
    ebi_impl = [(spec, anchors.selected_for(spec).impl_node) for spec in sorted(ebi) if anchors.selected_for(spec)]
    ebo_impl = [(spec, anchors.selected_for(spec).impl_node) for spec in sorted(ebo) if anchors.selected_for(spec)]
    conflicts: list[tuple[str, str]] = []
    for ebo_spec, ebo_node in ebo_impl:
        fanout = impl_graph.transitive_fanout([ebo_node])
        for ebi_spec, ebi_node in ebi_impl:
            if ebi_node in fanout:
                conflicts.append((ebi_spec, ebo_spec))
    return conflicts


def recover_extended_boundary(
    spec_graph: CircuitGraph,
    impl_graph: CircuitGraph,
    coi: CoiSpec,
    anchors: AnchorMap,
    *,
    max_cycle_resolution_iterations: int = 2,
) -> BoundaryRecoveryResult:
    start = time.perf_counter()
    ok, reason = validate_coi_spec(spec_graph, coi)
    if not ok:
        return BoundaryRecoveryResult(coi, tuple(), tuple(), tuple(), {}, "invalid_coi", reason, 0, 0, 0, "not_attempted", time.perf_counter() - start)

    ebi, input_distances, input_failures = first_equivalent_cut_tfi(spec_graph, list(coi.boundary_inputs), anchors)
    ebo, output_distances, output_failures = first_equivalent_cut_tfo(spec_graph, list(coi.boundary_outputs), anchors)
    if input_failures:
        return BoundaryRecoveryResult(coi, tuple(sorted(ebi)), tuple(sorted(ebo)), tuple(), {}, "no_input_cut", ",".join(input_failures), 0, 0, 0, "not_attempted", time.perf_counter() - start)
    if output_failures:
        return BoundaryRecoveryResult(coi, tuple(sorted(ebi)), tuple(sorted(ebo)), tuple(), {}, "no_output_cut", ",".join(output_failures), 0, 0, 0, "not_attempted", time.perf_counter() - start)

    additions, tsi_distances, tsi_failures = first_equivalent_cut_tsi(spec_graph, ebo, ebi, anchors, set(coi.boundary_outputs))
    ebi |= additions
    region = extract_region_between_cuts(spec_graph, ebi, ebo)
    selected = anchors.selected_anchors(ebi | ebo)
    status, failure, conflicts = validate_recovered_boundary(spec_graph, impl_graph, coi, ebi, ebo, region, anchors)
    iterations = 0
    invalidated = 0
    cycle_status = "not_needed"
    while status == "cycle_detected" and iterations < max_cycle_resolution_iterations:
        iterations += 1
        invalidated += len(conflicts)
        cycle_status = "unresolved"
        break
    if status != "cycle_detected":
        cycle_status = "cycle_free"
    return BoundaryRecoveryResult(
        coi=coi,
        extended_boundary_inputs=tuple(sorted(ebi)),
        extended_boundary_outputs=tuple(sorted(ebo)),
        region_nodes=tuple(sorted(region)),
        selected_anchors=selected,
        validation_status=status,
        failure_reason=failure if status != "valid" else "",
        cycle_resolution_iterations=iterations,
        cycle_conflict_count=len(conflicts),
        invalidated_anchor_count=invalidated,
        cycle_resolution_status=cycle_status,
        runtime_seconds=time.perf_counter() - start,
    )


def compute_boundary_metrics(
    result: BoundaryRecoveryResult,
    spec_graph: CircuitGraph,
    impl_graph: CircuitGraph,
    *,
    input_distances: dict[str, int] | None = None,
    output_distances: dict[str, int] | None = None,
) -> dict[str, object]:
    coi = result.coi
    spec_logic_nodes = [node for node in spec_graph.nodes if node not in spec_graph.inputs]
    denominator = len(spec_logic_nodes) - len(coi.coi_internal_nodes)
    extension = len(result.region_nodes) - len(coi.coi_internal_nodes)
    ratio = 0.0 if denominator <= 0 else max(0.0, min(1.0, extension / denominator))
    anchor_distances = []
    for node in [*result.extended_boundary_inputs, *result.extended_boundary_outputs]:
        d_in = min(
            [d for root in coi.boundary_inputs if (d := spec_graph.shortest_distance_to_any(root, {node}, "fanin")) is not None]
            or [0]
        )
        d_out = min(
            [d for root in coi.boundary_outputs if (d := spec_graph.shortest_distance_to_any(root, {node}, "fanout")) is not None]
            or [0]
        )
        anchor_distances.append(min(d_in, d_out))
    return {
        "spec_node_count": len(spec_logic_nodes),
        "impl_node_count": len([node for node in impl_graph.nodes if node not in impl_graph.inputs]),
        "coi_node_count": len(coi.coi_internal_nodes),
        "extended_region_node_count": len(result.region_nodes),
        "original_boundary_input_count": len(coi.boundary_inputs),
        "original_boundary_output_count": len(coi.boundary_outputs),
        "extended_boundary_input_count": len(result.extended_boundary_inputs),
        "extended_boundary_output_count": len(result.extended_boundary_outputs),
        "anchor_count": len(result.selected_anchors),
        "boundary_expansion_node_count": max(0, extension),
        "boundary_extension_ratio": ratio,
        "input_boundary_distance": max(anchor_distances) if anchor_distances else 0,
        "output_boundary_distance": max(anchor_distances) if anchor_distances else 0,
        "mean_anchor_distance": sum(anchor_distances) / len(anchor_distances) if anchor_distances else 0.0,
        "max_anchor_distance": max(anchor_distances) if anchor_distances else 0,
    }


def region_manifest(result: BoundaryRecoveryResult) -> dict[str, object]:
    return {
        "benchmark": result.coi.benchmark,
        "optimization": result.coi.optimization,
        "coi_name": result.coi.coi_name,
        "coi_internal_nodes": list(result.coi.coi_internal_nodes),
        "boundary_inputs": list(result.coi.boundary_inputs),
        "boundary_outputs": list(result.coi.boundary_outputs),
        "extended_boundary_inputs": list(result.extended_boundary_inputs),
        "extended_boundary_outputs": list(result.extended_boundary_outputs),
        "region_nodes": list(result.region_nodes),
        "validation_status": result.validation_status,
        "failure_reason": result.failure_reason,
        "anchors": [anchor.__dict__ for anchor in result.selected_anchors.values()],
    }


def write_region_dot(result: BoundaryRecoveryResult, graph: CircuitGraph, path: Path) -> None:
    lines = ["digraph recovered_region {"]
    ebi = set(result.extended_boundary_inputs)
    ebo = set(result.extended_boundary_outputs)
    region = set(result.region_nodes)
    for node in sorted(ebi | ebo | region):
        shape = "box" if node in ebi else "doublecircle" if node in ebo else "ellipse"
        lines.append(f'  "{node}" [shape={shape}];')
    for node in sorted(region | ebo):
        for fanin in graph.fanins.get(node, tuple()):
            if fanin in ebi | region:
                lines.append(f'  "{fanin}" -> "{node}";')
    lines.append("}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
