"""Bounded anchored-cut enumeration for materialized correspondence."""

from __future__ import annotations

import itertools
from collections import deque
from dataclasses import dataclass

from boundary_anchor_map import Anchor
from boundary_graph import CircuitGraph


GLOBAL_FORMAL_CATEGORIES = {
    "exact_signature_match",
    "complemented_equivalence",
    "sat_cec_proven_equivalent",
}


@dataclass(frozen=True)
class AnchoredCut:
    cut_id: str
    target_impl_node: str
    cut_size: int
    impl_leaf_nodes: tuple[str, ...]
    spec_leaf_nodes: tuple[str, ...]
    leaf_mapping_categories: tuple[str, ...]
    leaf_polarities: tuple[str, ...]
    all_leaves_globally_formal: bool
    cut_depth: int
    cut_support_size: int
    estimated_truth_table_cost: int
    cut_rank: int
    validation_status: str = "candidate"
    failure_reason: str = ""


def invert_anchor_map(anchors: list[Anchor]) -> dict[str, Anchor]:
    """Return the preferred globally formal spec anchor for each impl node."""

    best: dict[str, Anchor] = {}
    for anchor in anchors:
        if anchor.equivalence_scope != "global":
            continue
        if anchor.mapping_category not in GLOBAL_FORMAL_CATEGORIES:
            continue
        if anchor.evidence_level not in {"formal_exhaustive", "formal_cec"}:
            continue
        current = best.get(anchor.impl_node)
        if current is None or _anchor_key(anchor) < _anchor_key(current):
            best[anchor.impl_node] = anchor
    return best


def enumerate_anchored_cuts(
    graph: CircuitGraph,
    target_impl_node: str,
    inverse_anchors: dict[str, Anchor],
    *,
    max_cut_size: int = 3,
    max_depth: int = 4,
    max_cuts: int = 64,
) -> list[AnchoredCut]:
    if target_impl_node not in graph.nodes:
        return []
    if target_impl_node in inverse_anchors:
        return []
    reachable = _reachable_anchored_leaves(graph, target_impl_node, inverse_anchors, max_depth)
    if not reachable:
        return []
    candidates: list[AnchoredCut] = []
    seen_leaf_sets: set[tuple[str, ...]] = set()
    ordered = sorted(reachable, key=lambda item: (item[1], item[0]))
    for size in range(1, max_cut_size + 1):
        for combo in itertools.combinations(ordered, size):
            impl_leaves = tuple(sorted(node for node, _ in combo))
            if impl_leaves in seen_leaf_sets:
                continue
            seen_leaf_sets.add(impl_leaves)
            anchors = [inverse_anchors[node] for node in impl_leaves]
            cut_depth = max(distance for _, distance in combo)
            support = set().union(*(set(graph.transitive_fanin([node])) & set(graph.inputs) for node in impl_leaves))
            candidates.append(
                AnchoredCut(
                    cut_id=f"{target_impl_node}|cut{len(candidates)+1}",
                    target_impl_node=target_impl_node,
                    cut_size=len(impl_leaves),
                    impl_leaf_nodes=impl_leaves,
                    spec_leaf_nodes=tuple(anchor.spec_node for anchor in anchors),
                    leaf_mapping_categories=tuple(anchor.mapping_category for anchor in anchors),
                    leaf_polarities=tuple(anchor.polarity for anchor in anchors),
                    all_leaves_globally_formal=True,
                    cut_depth=cut_depth,
                    cut_support_size=len(support),
                    estimated_truth_table_cost=1 << len(impl_leaves),
                    cut_rank=0,
                )
            )
            if len(candidates) >= max_cuts:
                break
        if len(candidates) >= max_cuts:
            break
    ranked = sorted(candidates, key=lambda c: (c.cut_size, c.cut_depth, c.estimated_truth_table_cost, c.impl_leaf_nodes))[:max_cuts]
    return [cut.__class__(**{**cut.__dict__, "cut_rank": idx}) for idx, cut in enumerate(ranked, start=1)]


def cut_to_row(cut: AnchoredCut, *, case_id: str, benchmark: str, optimization: str, coi_name: str) -> dict[str, object]:
    return {
        "case_id": case_id,
        "benchmark": benchmark,
        "optimization": optimization,
        "coi_name": coi_name,
        "cut_id": cut.cut_id,
        "target_impl_node": cut.target_impl_node,
        "cut_size": cut.cut_size,
        "impl_leaf_nodes": ";".join(cut.impl_leaf_nodes),
        "spec_leaf_nodes": ";".join(cut.spec_leaf_nodes),
        "leaf_mapping_categories": ";".join(cut.leaf_mapping_categories),
        "leaf_polarities": ";".join(cut.leaf_polarities),
        "all_leaves_globally_formal": cut.all_leaves_globally_formal,
        "cut_depth": cut.cut_depth,
        "cut_support_size": cut.cut_support_size,
        "estimated_truth_table_cost": cut.estimated_truth_table_cost,
        "cut_rank": cut.cut_rank,
        "validation_status": cut.validation_status,
        "failure_reason": cut.failure_reason,
    }


def _reachable_anchored_leaves(
    graph: CircuitGraph,
    target: str,
    inverse_anchors: dict[str, Anchor],
    max_depth: int,
) -> list[tuple[str, int]]:
    queue: deque[tuple[str, int]] = deque([(fanin, 1) for fanin in sorted(graph.fanins.get(target, ()))])
    seen: set[str] = set()
    leaves: dict[str, int] = {}
    while queue:
        node, distance = queue.popleft()
        if node in seen or distance > max_depth:
            continue
        seen.add(node)
        if node in inverse_anchors:
            leaves[node] = min(distance, leaves.get(node, distance))
            continue
        for fanin in sorted(graph.fanins.get(node, ())):
            queue.append((fanin, distance + 1))
    return sorted(leaves.items(), key=lambda item: (item[1], item[0]))


def _anchor_key(anchor: Anchor) -> tuple[object, ...]:
    priority = {
        "exact_signature_match": 0,
        "sat_cec_proven_equivalent": 1,
        "complemented_equivalence": 2,
    }
    return (priority.get(anchor.mapping_category, 99), 0 if anchor.polarity == "same" else 1, anchor.spec_node)
