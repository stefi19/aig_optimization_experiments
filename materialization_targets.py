"""Target selection for anchored-cut wire materialization experiments."""

from __future__ import annotations

import csv
import json
from collections import deque
from dataclasses import dataclass
from pathlib import Path

from boundary_anchor_map import AnchorMap
from boundary_graph import CircuitGraph


@dataclass(frozen=True)
class MaterializationTarget:
    case_id: str
    benchmark: str
    optimization: str
    coi_name: str
    target_impl_node: str
    target_role: str
    distance_to_failed_frontier: int
    target_level: int
    target_fanin_count: int
    target_fanout_count: int
    target_support_size: int
    selection_reason: str
    target_rank: int


def select_targets_from_extended_failures(
    extended_cases: Path,
    impl_graphs: dict[tuple[str, str], CircuitGraph],
    inverse_anchor_nodes: dict[tuple[str, str], set[str]],
    *,
    max_targets_per_case: int = 16,
) -> list[MaterializationTarget]:
    """Select unmatched optimized-side nodes from failed extended-boundary rows.

    The first experiment deliberately uses nodes implicated by incoming/outgoing
    bypasses.  This keeps the target set tied to a concrete boundary-recovery
    bottleneck without relying on semantic ground truth.
    """

    rows = _read_rows(extended_cases)
    targets: list[MaterializationTarget] = []
    for row in rows:
        if row.get("anchor_mode") != "formal_all" or row.get("search_mode") != "cost_guided":
            continue
        if str(row.get("success")).lower() == "true":
            continue
        graph = impl_graphs.get((row["benchmark"], row["optimization"]))
        if graph is None:
            continue
        anchored = inverse_anchor_nodes.get((row["benchmark"], row["optimization"]), set())
        candidates: list[tuple[str, str, str]] = []
        for edge in _json_edges(row.get("incoming_bypass_edges_json", "[]")):
            if len(edge) == 2:
                candidates.append((edge[1], "incoming_bypass_sink", f"incoming bypass {edge[0]}->{edge[1]}"))
                candidates.append((edge[0], "incoming_bypass_source", f"incoming bypass {edge[0]}->{edge[1]}"))
        for edge in _json_edges(row.get("outgoing_bypass_edges_json", "[]")):
            if len(edge) == 2:
                candidates.append((edge[0], "outgoing_bypass_source", f"outgoing bypass {edge[0]}->{edge[1]}"))
                candidates.append((edge[1], "outgoing_bypass_sink", f"outgoing bypass {edge[0]}->{edge[1]}"))
        if not candidates:
            trace = _load_json(row.get("trace_json", "{}"))
            for node in trace.get("derived_bi", []) + trace.get("derived_bo", []):
                candidates.append((str(node), "derived_boundary_candidate", "failed derived boundary node"))
        seen: set[str] = set()
        ranked: list[MaterializationTarget] = []
        levels = compute_levels(graph)
        for node, role, reason in candidates:
            if node in seen or not graph.exists(node) or node in graph.inputs or node in graph.outputs:
                continue
            seen.add(node)
            if node in anchored:
                continue
            support = set(graph.transitive_fanin([node])) & set(graph.inputs)
            ranked.append(
                MaterializationTarget(
                    case_id=f"{row['benchmark']}|{row['coi_name']}|{row['optimization']}|{node}",
                    benchmark=row["benchmark"],
                    optimization=row["optimization"],
                    coi_name=row["coi_name"],
                    target_impl_node=node,
                    target_role=role,
                    distance_to_failed_frontier=0,
                    target_level=levels.get(node, 0),
                    target_fanin_count=len(graph.fanins.get(node, ())),
                    target_fanout_count=len(graph.fanouts.get(node, ())),
                    target_support_size=len(support),
                    selection_reason=reason,
                    target_rank=0,
                )
            )
        ranked = sorted(ranked, key=lambda t: (t.distance_to_failed_frontier, t.target_level, t.target_fanin_count, t.target_impl_node))[:max_targets_per_case]
        for idx, target in enumerate(ranked, start=1):
            targets.append(target.__class__(**{**target.__dict__, "target_rank": idx}))
    return sorted(targets, key=lambda t: (t.benchmark, t.optimization, t.coi_name, t.target_rank, t.target_impl_node))


def compute_levels(graph: CircuitGraph) -> dict[str, int]:
    levels = {name: 0 for name in graph.inputs}
    pending = set(graph.nodes) - set(graph.inputs)
    changed = True
    while pending and changed:
        changed = False
        for node in sorted(list(pending)):
            fanins = graph.fanins.get(node, ())
            if all(fanin in levels for fanin in fanins):
                levels[node] = 1 + max((levels[fanin] for fanin in fanins), default=0)
                pending.remove(node)
                changed = True
    for node in pending:
        levels[node] = 0
    return levels


def distance_to_anchor(graph: CircuitGraph, start: str, anchored_nodes: set[str], max_depth: int) -> int | None:
    queue: deque[tuple[str, int]] = deque([(start, 0)])
    seen: set[str] = set()
    while queue:
        node, distance = queue.popleft()
        if node in seen or distance > max_depth:
            continue
        seen.add(node)
        if node in anchored_nodes:
            return distance
        for fanin in sorted(graph.fanins.get(node, ())):
            queue.append((fanin, distance + 1))
    return None


def target_to_row(target: MaterializationTarget) -> dict[str, object]:
    return dict(target.__dict__)


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _json_edges(text: str) -> list[list[str]]:
    value = _load_json(text or "[]")
    return value if isinstance(value, list) else []


def _load_json(text: str):
    try:
        return json.loads(text or "[]")
    except json.JSONDecodeError:
        return []
