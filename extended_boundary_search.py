"""Extended-boundary validation and bounded anchored-cut search.

Identity recovery still requires exact BI/EBO/region equality.  This module is
for optimized implementations, where a valid recovered boundary may enclose the
original COI plus additional nodes.
"""

from __future__ import annotations

import itertools
import json
import time
from collections import deque
from dataclasses import dataclass

from boundary_anchor_map import AnchorMap
from boundary_graph import CircuitGraph
from boundary_recovery import detect_mapped_boundary_cycles, first_equivalent_cut_tfi, first_equivalent_cut_tfo
from coi_model import CanonicalCoi, derive_boundary_inputs, derive_boundary_outputs, extract_region_from_boundaries


@dataclass(frozen=True)
class SearchConfig:
    max_frontier_depth: int = 4
    max_candidates_per_boundary_node: int = 4
    max_frontier_sets_per_case: int = 256
    max_search_states: int = 512
    timeout_seconds: float = 5.0
    max_extension_ratio: float = 0.95
    max_extended_region_nodes: int = 1000000
    allow_whole_design_boundary: bool = False


@dataclass(frozen=True)
class FrontierCandidate:
    root: str
    node: str
    distance: int
    direction: str


@dataclass(frozen=True)
class ExtendedBoundaryResult:
    success: bool
    search_mode: str
    validation_profile: str
    ebi: tuple[str, ...]
    ebo: tuple[str, ...]
    region: tuple[str, ...]
    contains_original_coi: bool
    valid_ebi_cut: bool
    valid_ebo_cut: bool
    incoming_bypass_edges: tuple[tuple[str, str], ...]
    outgoing_bypass_edges: tuple[tuple[str, str], ...]
    all_boundary_nodes_formally_anchored: bool
    cycle_free: bool
    whole_design_boundary: bool
    original_ebi_exact_match: bool
    original_ebo_exact_match: bool
    original_region_exact_match: bool
    extension_nodes: tuple[str, ...]
    extension_ratio: float
    total_boundary_distance: int
    selected_exact_anchor_count: int
    selected_complemented_anchor_count: int
    selected_sat_cec_anchor_count: int
    available_sat_cec_frontier_candidates: int
    selected_sat_cec_frontier_candidates: int
    candidate_frontiers: int
    candidate_ebi_frontier_count: int
    candidate_ebo_frontier_count: int
    search_states: int
    pruned_states: int
    cycle_pruned_states: int
    alternative_anchor_states_explored: int
    runtime_seconds: float
    failure_reason: str
    classification: str
    trace_json: str


def enumerate_anchored_tfi_frontiers(
    graph: CircuitGraph,
    roots: tuple[str, ...] | list[str],
    anchors: AnchorMap,
    config: SearchConfig,
) -> dict[str, list[FrontierCandidate]]:
    return _enumerate_frontiers(graph, roots, anchors, config, "fanin")


def enumerate_anchored_tfo_frontiers(
    graph: CircuitGraph,
    roots: tuple[str, ...] | list[str],
    anchors: AnchorMap,
    config: SearchConfig,
) -> dict[str, list[FrontierCandidate]]:
    return _enumerate_frontiers(graph, roots, anchors, config, "fanout")


def _enumerate_frontiers(
    graph: CircuitGraph,
    roots: tuple[str, ...] | list[str],
    anchors: AnchorMap,
    config: SearchConfig,
    direction: str,
) -> dict[str, list[FrontierCandidate]]:
    neighbors = graph.fanins if direction == "fanin" else graph.fanouts
    out: dict[str, list[FrontierCandidate]] = {}
    for root in sorted(roots):
        queue: deque[tuple[str, int]] = deque([(root, 0)])
        seen: set[str] = set()
        candidates: list[FrontierCandidate] = []
        while queue and len(candidates) < config.max_candidates_per_boundary_node:
            node, distance = queue.popleft()
            if node in seen or distance > config.max_frontier_depth:
                continue
            seen.add(node)
            if anchors.has_anchor(node):
                candidates.append(FrontierCandidate(root=root, node=node, distance=distance, direction=direction))
            for nxt in sorted(neighbors.get(node, tuple())):
                queue.append((nxt, distance + 1))
        out[root] = candidates
    return out


def first_frontier_extended_boundary(
    graph: CircuitGraph,
    impl_graph: CircuitGraph,
    coi: CanonicalCoi,
    anchors: AnchorMap,
    config: SearchConfig | None = None,
) -> ExtendedBoundaryResult:
    start = time.perf_counter()
    config = config or SearchConfig()
    ebi, ebi_dist, ebi_fail = first_equivalent_cut_tfi(graph, list(coi.boundary_inputs), anchors)
    ebo, ebo_dist, ebo_fail = first_equivalent_cut_tfo(graph, list(coi.boundary_outputs), anchors)
    distances = {**ebi_dist, **ebo_dist}
    trace = {
        "ebi_failures": ebi_fail,
        "ebo_failures": ebo_fail,
        "selected_ebi": sorted(ebi),
        "selected_ebo": sorted(ebo),
    }
    if ebi_fail or ebo_fail:
        return _empty_result(
            "first_frontier",
            time.perf_counter() - start,
            "no_anchored_frontier",
            "still_no_valid_formal_boundary",
            trace,
        )
    return validate_extended_boundary(
        graph,
        impl_graph,
        coi,
        anchors,
        ebi,
        ebo,
        distances,
        "first_frontier",
        config,
        runtime_seconds=time.perf_counter() - start,
        candidate_frontiers=len(ebi) + len(ebo),
        search_states=1,
        trace=trace,
    )


def search_valid_extended_boundary(
    graph: CircuitGraph,
    impl_graph: CircuitGraph,
    coi: CanonicalCoi,
    anchors: AnchorMap,
    config: SearchConfig | None = None,
) -> ExtendedBoundaryResult:
    start = time.perf_counter()
    config = config or SearchConfig()
    ebi_by_root = enumerate_anchored_tfi_frontiers(graph, coi.boundary_inputs, anchors, config)
    ebo_by_root = enumerate_anchored_tfo_frontiers(graph, coi.boundary_outputs, anchors, config)
    if any(not vals for vals in ebi_by_root.values()) or any(not vals for vals in ebo_by_root.values()):
        return _empty_result(
            "cost_guided",
            time.perf_counter() - start,
            "no_anchored_frontier",
            "still_no_valid_formal_boundary",
            {"ebi_candidates": _frontier_trace(ebi_by_root), "ebo_candidates": _frontier_trace(ebo_by_root)},
        )

    ebi_combos = _bounded_product(list(ebi_by_root.values()), config.max_frontier_sets_per_case)
    ebo_combos = _bounded_product(list(ebo_by_root.values()), config.max_frontier_sets_per_case)
    candidates: list[tuple[tuple[object, ...], int, ExtendedBoundaryResult]] = []
    best_invalid: ExtendedBoundaryResult | None = None
    states = 0
    pruned = 0
    cycle_pruned = 0
    candidate_limit = config.max_frontier_sets_per_case
    for ebi_choice in ebi_combos:
        for ebo_choice in ebo_combos:
            if states >= config.max_search_states or len(candidates) >= candidate_limit:
                pruned += 1
                continue
            if time.perf_counter() - start > config.timeout_seconds:
                pruned += 1
                continue
            states += 1
            ebi = {c.node for c in ebi_choice}
            ebo = {c.node for c in ebo_choice}
            distances: dict[str, int] = {}
            for candidate in [*ebi_choice, *ebo_choice]:
                distances[candidate.node] = min(candidate.distance, distances.get(candidate.node, candidate.distance))
            conflicts = detect_mapped_boundary_cycles(impl_graph, ebi, ebo, anchors)
            if conflicts:
                cycle_pruned += 1
            result = validate_extended_boundary(
                graph,
                impl_graph,
                coi,
                anchors,
                ebi,
                ebo,
                distances,
                "cost_guided",
                config,
                runtime_seconds=time.perf_counter() - start,
                candidate_frontiers=sum(len(v) for v in ebi_by_root.values()) + sum(len(v) for v in ebo_by_root.values()),
                candidate_ebi_frontier_count=sum(len(v) for v in ebi_by_root.values()),
                candidate_ebo_frontier_count=sum(len(v) for v in ebo_by_root.values()),
                search_states=states,
                pruned_states=pruned,
                cycle_pruned_states=cycle_pruned,
                alternative_anchor_states_explored=states,
                trace={"ebi_candidates": _frontier_trace(ebi_by_root), "ebo_candidates": _frontier_trace(ebo_by_root)},
            )
            if result.success:
                candidates.append((_cost_key(result), states, result))
            elif best_invalid is None or _invalid_key(result) < _invalid_key(best_invalid):
                best_invalid = result

    if candidates:
        return sorted(candidates, key=lambda item: (item[0], item[1]))[0][2]
    if best_invalid is not None:
        return best_invalid
    return _empty_result(
        "cost_guided",
        time.perf_counter() - start,
        "search_budget_exhausted",
        "search_budget_exhausted",
        {"ebi_candidates": _frontier_trace(ebi_by_root), "ebo_candidates": _frontier_trace(ebo_by_root)},
    )


def validate_extended_boundary(
    graph: CircuitGraph,
    impl_graph: CircuitGraph,
    coi: CanonicalCoi,
    anchors: AnchorMap,
    ebi: set[str],
    ebo: set[str],
    distances: dict[str, int],
    search_mode: str,
    config: SearchConfig,
    *,
    runtime_seconds: float,
    candidate_frontiers: int,
    candidate_ebi_frontier_count: int | None = None,
    candidate_ebo_frontier_count: int | None = None,
    search_states: int = 0,
    pruned_states: int = 0,
    cycle_pruned_states: int = 0,
    alternative_anchor_states_explored: int = 0,
    trace: dict[str, object] | None = None,
) -> ExtendedBoundaryResult:
    extracted = extract_region_from_boundaries(graph, ebi, ebo, required_nodes=set(coi.region_nodes))
    region = set(extracted.region_nodes)
    original = set(coi.region_nodes)
    extension_nodes = tuple(sorted(region - original))
    incoming = _incoming_bypass_edges(graph, region, ebi)
    outgoing = _outgoing_bypass_edges(graph, region, ebo)
    derived_bi = set(derive_boundary_inputs(graph, region)) if region else set()
    derived_bo = set(derive_boundary_outputs(graph, region)) if region else set()
    valid_ebi = bool(ebi) and not incoming and derived_bi == ebi
    valid_ebo = bool(ebo) and not outgoing and derived_bo == ebo
    contains = original <= region
    all_anchored = all(anchors.has_anchor(node) for node in ebi | ebo)
    conflicts = detect_mapped_boundary_cycles(impl_graph, ebi, ebo, anchors)
    non_inputs = {node for node in graph.nodes if node not in graph.inputs}
    whole_design = bool(region) and region >= non_inputs
    denominator = max(1, len(non_inputs) - len(original))
    extension_ratio = max(0.0, len(extension_nodes) / denominator)
    within_extension_limit = (
        len(region) <= config.max_extended_region_nodes
        and extension_ratio <= config.max_extension_ratio
        and (config.allow_whole_design_boundary or not whole_design)
    )
    success = (
        bool(region)
        and contains
        and valid_ebi
        and valid_ebo
        and all_anchored
        and not conflicts
        and within_extension_limit
    )
    reasons: list[str] = []
    if not region:
        reasons.append("extended_region_empty")
    if not contains:
        reasons.append("missing_original_coi_nodes")
    if not valid_ebi:
        reasons.append("invalid_ebi_cut")
    if not valid_ebo:
        reasons.append("invalid_ebo_cut")
    if incoming:
        reasons.append("incoming_bypass")
    if outgoing:
        reasons.append("outgoing_bypass")
    if not all_anchored:
        reasons.append("missing_formal_boundary_anchor")
    if conflicts:
        reasons.append("cycle")
    if whole_design and not config.allow_whole_design_boundary:
        reasons.append("whole_design_candidate")
    if extension_ratio > config.max_extension_ratio or len(region) > config.max_extended_region_nodes:
        reasons.append("extension_limit_exceeded")
    anchor_counts = _anchor_counts(anchors, ebi | ebo)
    sat_candidates = _sat_cec_candidates(anchors, set().union(derived_bi, derived_bo, ebi, ebo))
    selected_sat = anchor_counts["sat_cec_proven_equivalent"]
    trace_data = {
        **(trace or {}),
        "incoming_bypass_edges": incoming,
        "outgoing_bypass_edges": outgoing,
        "cycle_conflicts": conflicts,
        "derived_bi": sorted(derived_bi),
        "derived_bo": sorted(derived_bo),
        "missing_original_coi_nodes": sorted(original - region),
    }
    return ExtendedBoundaryResult(
        success=success,
        search_mode=search_mode,
        validation_profile="optimized_extended",
        ebi=tuple(sorted(ebi)),
        ebo=tuple(sorted(ebo)),
        region=tuple(sorted(region)),
        contains_original_coi=contains,
        valid_ebi_cut=valid_ebi,
        valid_ebo_cut=valid_ebo,
        incoming_bypass_edges=tuple(incoming),
        outgoing_bypass_edges=tuple(outgoing),
        all_boundary_nodes_formally_anchored=all_anchored,
        cycle_free=not conflicts,
        whole_design_boundary=whole_design,
        original_ebi_exact_match=set(coi.boundary_inputs) == ebi,
        original_ebo_exact_match=set(coi.boundary_outputs) == ebo,
        original_region_exact_match=original == region,
        extension_nodes=extension_nodes,
        extension_ratio=extension_ratio,
        total_boundary_distance=sum(distances.get(node, 0) for node in ebi | ebo),
        selected_exact_anchor_count=anchor_counts["exact_signature_match"],
        selected_complemented_anchor_count=anchor_counts["complemented_equivalence"],
        selected_sat_cec_anchor_count=selected_sat,
        available_sat_cec_frontier_candidates=sat_candidates,
        selected_sat_cec_frontier_candidates=selected_sat,
        candidate_frontiers=candidate_frontiers,
        candidate_ebi_frontier_count=candidate_ebi_frontier_count if candidate_ebi_frontier_count is not None else len(ebi),
        candidate_ebo_frontier_count=candidate_ebo_frontier_count if candidate_ebo_frontier_count is not None else len(ebo),
        search_states=search_states,
        pruned_states=pruned_states,
        cycle_pruned_states=cycle_pruned_states,
        alternative_anchor_states_explored=alternative_anchor_states_explored,
        runtime_seconds=runtime_seconds,
        failure_reason="valid" if success else ";".join(reasons),
        classification=_classification(success, reasons, search_mode),
        trace_json=json.dumps(trace_data, sort_keys=True),
    )


def result_to_row(
    result: ExtendedBoundaryResult,
    *,
    case_id: str,
    benchmark: str,
    optimization: str,
    coi_name: str,
    anchor_mode: str,
    original_coi_nodes: tuple[str, ...] | list[str] = (),
    old_status: str = "",
    old_failure_reason: str = "",
) -> dict[str, object]:
    return {
        "case_id": case_id,
        "benchmark": benchmark,
        "optimization": optimization,
        "coi_name": coi_name,
        "anchor_mode": anchor_mode,
        "search_mode": result.search_mode,
        "validation_profile": result.validation_profile,
        "eligible": True,
        "attempted": True,
        "success": result.success,
        "contains_original_coi": result.contains_original_coi,
        "valid_ebi_cut": result.valid_ebi_cut,
        "valid_ebo_cut": result.valid_ebo_cut,
        "incoming_bypass_count": len(result.incoming_bypass_edges),
        "outgoing_bypass_count": len(result.outgoing_bypass_edges),
        "incoming_bypass_edges_json": json.dumps(result.incoming_bypass_edges),
        "outgoing_bypass_edges_json": json.dumps(result.outgoing_bypass_edges),
        "all_boundary_nodes_formally_anchored": result.all_boundary_nodes_formally_anchored,
        "cycle_free": result.cycle_free,
        "whole_design_boundary": result.whole_design_boundary,
        "original_ebi_exact_match": result.original_ebi_exact_match,
        "original_ebo_exact_match": result.original_ebo_exact_match,
        "original_region_exact_match": result.original_region_exact_match,
        "original_coi_nodes": ";".join(sorted(original_coi_nodes)),
        "extended_region_nodes": ";".join(result.region),
        "extension_nodes": ";".join(result.extension_nodes),
        "extension_ratio": result.extension_ratio,
        "ebi_count": len(result.ebi),
        "ebo_count": len(result.ebo),
        "total_boundary_distance": result.total_boundary_distance,
        "selected_exact_anchor_count": result.selected_exact_anchor_count,
        "selected_complemented_anchor_count": result.selected_complemented_anchor_count,
        "selected_sat_cec_anchor_count": result.selected_sat_cec_anchor_count,
        "available_sat_cec_frontier_candidates": result.available_sat_cec_frontier_candidates,
        "selected_sat_cec_frontier_candidates": result.selected_sat_cec_frontier_candidates,
        "candidate_frontiers": result.candidate_frontiers,
        "candidate_ebi_frontier_count": result.candidate_ebi_frontier_count,
        "candidate_ebo_frontier_count": result.candidate_ebo_frontier_count,
        "search_states": result.search_states,
        "pruned_states": result.pruned_states,
        "cycle_pruned_states": result.cycle_pruned_states,
        "alternative_anchor_states_explored": result.alternative_anchor_states_explored,
        "runtime_seconds": f"{result.runtime_seconds:.6f}",
        "failure_reason": result.failure_reason,
        "classification": result.classification,
        "old_status": old_status,
        "old_failure_reason": old_failure_reason,
        "trace_json": result.trace_json,
    }


def _bounded_product(groups: list[list[FrontierCandidate]], limit: int) -> list[tuple[FrontierCandidate, ...]]:
    ordered_groups = [sorted(g, key=lambda c: (c.distance, c.node)) for g in groups]
    combos = itertools.product(*ordered_groups)
    return sorted(itertools.islice(combos, limit), key=lambda combo: (sum(c.distance for c in combo), tuple(c.node for c in combo)))


def _incoming_bypass_edges(graph: CircuitGraph, region: set[str], ebi: set[str]) -> tuple[tuple[str, str], ...]:
    return tuple(sorted((fanin, node) for node in region for fanin in graph.fanins.get(node, tuple()) if fanin not in region and fanin not in ebi))


def _outgoing_bypass_edges(graph: CircuitGraph, region: set[str], ebo: set[str]) -> tuple[tuple[str, str], ...]:
    return tuple(sorted((node, fanout) for node in region for fanout in graph.fanouts.get(node, tuple()) if fanout not in region and node not in ebo))


def _anchor_counts(anchors: AnchorMap, nodes: set[str]) -> dict[str, int]:
    counts = {"exact_signature_match": 0, "complemented_equivalence": 0, "sat_cec_proven_equivalent": 0}
    for node in nodes:
        anchor = anchors.selected_for(node)
        if anchor and anchor.mapping_category in counts:
            counts[anchor.mapping_category] += 1
    return counts


def _sat_cec_candidates(anchors: AnchorMap, nodes: set[str]) -> int:
    return sum(1 for node in nodes for anchor in anchors.candidates_for(node) if anchor.mapping_category == "sat_cec_proven_equivalent")


def _cost_key(result: ExtendedBoundaryResult) -> tuple[object, ...]:
    return (
        len(result.extension_nodes),
        result.total_boundary_distance,
        len(result.ebi) + len(result.ebo),
        result.selected_complemented_anchor_count,
        result.ebi,
        result.ebo,
    )


def _invalid_key(result: ExtendedBoundaryResult) -> tuple[object, ...]:
    return (
        0 if result.contains_original_coi else 1,
        len(result.incoming_bypass_edges) + len(result.outgoing_bypass_edges),
        len(result.extension_nodes),
        result.failure_reason,
    )


def _classification(success: bool, reasons: list[str], search_mode: str) -> str:
    if success and search_mode == "first_frontier":
        return "previously_false_negative_due_to_strict_equality"
    if success:
        return "fixed_by_cost_guided_search"
    if "cycle" in reasons:
        return "blocked_by_cycle"
    if "extension_limit_exceeded" in reasons or "whole_design_candidate" in reasons:
        return "blocked_by_extension_limit"
    if "missing_formal_boundary_anchor" in reasons or "invalid_ebi_cut" in reasons or "invalid_ebo_cut" in reasons:
        return "blocked_by_missing_relevant_anchors"
    return "still_no_valid_formal_boundary"


def _frontier_trace(frontiers: dict[str, list[FrontierCandidate]]) -> dict[str, list[dict[str, object]]]:
    return {
        root: [{"node": c.node, "distance": c.distance, "direction": c.direction} for c in candidates]
        for root, candidates in sorted(frontiers.items())
    }


def _empty_result(search_mode: str, runtime: float, reason: str, classification: str, trace: dict[str, object]) -> ExtendedBoundaryResult:
    return ExtendedBoundaryResult(
        success=False,
        search_mode=search_mode,
        validation_profile="optimized_extended",
        ebi=tuple(),
        ebo=tuple(),
        region=tuple(),
        contains_original_coi=False,
        valid_ebi_cut=False,
        valid_ebo_cut=False,
        incoming_bypass_edges=tuple(),
        outgoing_bypass_edges=tuple(),
        all_boundary_nodes_formally_anchored=False,
        cycle_free=True,
        whole_design_boundary=False,
        original_ebi_exact_match=False,
        original_ebo_exact_match=False,
        original_region_exact_match=False,
        extension_nodes=tuple(),
        extension_ratio=0.0,
        total_boundary_distance=0,
        selected_exact_anchor_count=0,
        selected_complemented_anchor_count=0,
        selected_sat_cec_anchor_count=0,
        available_sat_cec_frontier_candidates=0,
        selected_sat_cec_frontier_candidates=0,
        candidate_frontiers=0,
        candidate_ebi_frontier_count=0,
        candidate_ebo_frontier_count=0,
        search_states=0,
        pruned_states=0,
        cycle_pruned_states=0,
        alternative_anchor_states_explored=0,
        runtime_seconds=runtime,
        failure_reason=reason,
        classification=classification,
        trace_json=json.dumps(trace, sort_keys=True),
    )
