"""Candidate generation for formal ODC-aware boundary anchors."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass

from boundary_anchor_map import AnchorMap
from boundary_graph import CircuitGraph
from coi_model import CanonicalCoi


@dataclass(frozen=True)
class OdcCandidate:
    case_id: str
    benchmark: str
    optimization: str
    coi_name: str
    context_mode: str
    ranking_mode: str
    boundary_side: str
    frontier_root: str
    spec_node: str
    impl_node: str
    requested_polarity: str
    candidate_rank: int
    spec_distance: int
    impl_distance: int
    support_overlap: int
    support_size_difference: int
    fanin_degree_difference: int
    fanout_degree_difference: int
    structural_score: float
    signature_similarity: float
    sampled_mismatch_rate: float
    sampled_output_error_rate: float
    simulation_filter_status: str


def identify_missing_anchor_frontiers(coi: CanonicalCoi, graph: CircuitGraph, anchors: AnchorMap, max_distance: int) -> list[tuple[str, str]]:
    roots = [(root, "ebi") for root in coi.boundary_inputs] + [(root, "ebo") for root in coi.boundary_outputs]
    missing: list[tuple[str, str]] = []
    for root, side in roots:
        if not _has_anchor_near(graph, root, side, anchors, max_distance):
            missing.append((root, side))
    return missing


def generate_odc_anchor_candidates(
    *,
    benchmark: str,
    optimization: str,
    coi: CanonicalCoi,
    spec_graph: CircuitGraph,
    impl_graph: CircuitGraph,
    anchors: AnchorMap,
    context_mode: str,
    ranking_mode: str,
    max_frontier_distance: int,
    max_spec_candidates_per_boundary: int,
    max_impl_candidates_per_spec_node: int,
    case_prefix: str,
) -> list[OdcCandidate]:
    candidates: list[OdcCandidate] = []
    for root, side in identify_missing_anchor_frontiers(coi, spec_graph, anchors, max_frontier_distance):
        spec_nodes = nearby_nodes(spec_graph, root, side, max_frontier_distance, max_spec_candidates_per_boundary)
        impl_roots = [root] if impl_graph.exists(root) else list(impl_graph.inputs)[:1]
        impl_pool: list[tuple[str, int]] = []
        for impl_root in impl_roots:
            impl_pool.extend(nearby_nodes(impl_graph, impl_root, side, max_frontier_distance, max_impl_candidates_per_spec_node))
        impl_pool = sorted(set(impl_pool), key=lambda item: (item[1], item[0]))[:max_impl_candidates_per_spec_node]
        ranked: list[OdcCandidate] = []
        for spec_node, spec_distance in spec_nodes:
            if anchors.has_anchor(spec_node):
                continue
            for impl_node, impl_distance in impl_pool:
                if impl_node in impl_graph.inputs or impl_node in impl_graph.outputs:
                    continue
                for polarity in ("positive", "inverted"):
                    ranked.append(
                        build_candidate(
                            case_id=f"{case_prefix}|{context_mode}|{ranking_mode}|{root}|{spec_node}|{impl_node}|{polarity}",
                            benchmark=benchmark,
                            optimization=optimization,
                            coi_name=coi.coi_name,
                            context_mode=context_mode,
                            ranking_mode=ranking_mode,
                            boundary_side=side,
                            frontier_root=root,
                            spec_graph=spec_graph,
                            impl_graph=impl_graph,
                            spec_node=spec_node,
                            impl_node=impl_node,
                            requested_polarity=polarity,
                            spec_distance=spec_distance,
                            impl_distance=impl_distance,
                        )
                    )
        ranked = rank_odc_anchor_candidates(ranked, ranking_mode)
        for idx, candidate in enumerate(ranked[:max_impl_candidates_per_spec_node], start=1):
            candidates.append(candidate.__class__(**{**candidate.__dict__, "candidate_rank": idx}))
    return sorted(candidates, key=lambda c: (c.benchmark, c.optimization, c.coi_name, c.context_mode, c.ranking_mode, c.candidate_rank, c.case_id))


def nearby_nodes(graph: CircuitGraph, root: str, side: str, max_distance: int, limit: int) -> list[tuple[str, int]]:
    neighbors = graph.fanins if side == "ebi" else graph.fanouts
    queue: deque[tuple[str, int]] = deque([(root, 0)])
    seen: set[str] = set()
    out: list[tuple[str, int]] = []
    while queue and len(out) < limit:
        node, distance = queue.popleft()
        if node in seen or distance > max_distance:
            continue
        seen.add(node)
        if node not in graph.inputs and node not in graph.outputs:
            out.append((node, distance))
        for nxt in sorted(neighbors.get(node, tuple())):
            queue.append((nxt, distance + 1))
    return out


def rank_odc_anchor_candidates(candidates: list[OdcCandidate], ranking_mode: str) -> list[OdcCandidate]:
    if ranking_mode == "structural_only":
        key = lambda c: (-c.structural_score, c.spec_distance + c.impl_distance, c.spec_node, c.impl_node, c.requested_polarity)
    elif ranking_mode == "simulation_only":
        key = lambda c: (c.sampled_mismatch_rate, -c.signature_similarity, c.spec_node, c.impl_node, c.requested_polarity)
    elif ranking_mode == "functional_features":
        key = lambda c: (-c.support_overlap, c.support_size_difference, c.fanin_degree_difference, c.fanout_degree_difference, c.spec_node, c.impl_node, c.requested_polarity)
    else:
        key = lambda c: (-c.structural_score, c.sampled_mismatch_rate, c.spec_distance + c.impl_distance, c.spec_node, c.impl_node, c.requested_polarity)
    return sorted(candidates, key=key)


def build_candidate(**kwargs) -> OdcCandidate:
    spec_graph: CircuitGraph = kwargs.pop("spec_graph")
    impl_graph: CircuitGraph = kwargs.pop("impl_graph")
    spec_node = kwargs["spec_node"]
    impl_node = kwargs["impl_node"]
    spec_support = set(spec_graph.transitive_fanin([spec_node])) & set(spec_graph.inputs)
    impl_support = set(impl_graph.transitive_fanin([impl_node])) & set(impl_graph.inputs)
    support_overlap = len(spec_support & impl_support)
    support_diff = abs(len(spec_support) - len(impl_support))
    fanin_diff = abs(len(spec_graph.fanins.get(spec_node, ())) - len(impl_graph.fanins.get(impl_node, ())))
    fanout_diff = abs(len(spec_graph.fanouts.get(spec_node, ())) - len(impl_graph.fanouts.get(impl_node, ())))
    distance = kwargs["spec_distance"] + kwargs["impl_distance"]
    structural_score = 1.0 / (1 + distance + support_diff + fanin_diff + fanout_diff)
    signature_similarity = support_overlap / max(1, len(spec_support | impl_support))
    mismatch = 1.0 - signature_similarity
    return OdcCandidate(
        **kwargs,
        candidate_rank=0,
        support_overlap=support_overlap,
        support_size_difference=support_diff,
        fanin_degree_difference=fanin_diff,
        fanout_degree_difference=fanout_diff,
        structural_score=structural_score,
        signature_similarity=signature_similarity,
        sampled_mismatch_rate=mismatch,
        sampled_output_error_rate=mismatch,
        simulation_filter_status="sampled_contextual_candidate",
    )


def _has_anchor_near(graph: CircuitGraph, root: str, side: str, anchors: AnchorMap, max_distance: int) -> bool:
    return any(anchors.has_anchor(node) for node, _ in nearby_nodes(graph, root, side, max_distance, max_distance + 1))
