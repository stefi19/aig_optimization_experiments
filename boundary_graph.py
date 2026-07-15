"""Deterministic graph utilities for BLIF boundary-recovery experiments."""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass

from analyze_blif_matches import BlifNetwork, parse_blif


@dataclass(frozen=True)
class CircuitGraph:
    """Combinational graph view of the repository's BLIF subset.

    Boundary convention used by the recovery prototype:
    - Primary inputs are graph sources.
    - `.names` outputs are logic nodes.
    - Primary outputs may be driven by internal nodes; if a PO is not a `.names`
      output it is still represented as an external sink name.
    - Boundary inputs are cut nodes outside the recovered region.
    - Boundary outputs are cut sinks included in the recovered region.
    - Inverted edges are represented only through BLIF covers; graph edges are
      signal dependencies and do not carry polarity.
    """

    inputs: tuple[str, ...]
    outputs: tuple[str, ...]
    nodes: tuple[str, ...]
    fanins: dict[str, tuple[str, ...]]
    fanouts: dict[str, tuple[str, ...]]

    @classmethod
    def from_blif(cls, path) -> "CircuitGraph":
        return cls.from_network(parse_blif(path))

    @classmethod
    def from_network(cls, net: BlifNetwork) -> "CircuitGraph":
        fanins: dict[str, tuple[str, ...]] = {name: tuple() for name in net.inputs}
        fanout_sets: dict[str, set[str]] = defaultdict(set)
        node_names = set(net.inputs)
        for node in net.nodes:
            node_names.add(node.output)
            fanins[node.output] = tuple(node.inputs)
            for fanin in node.inputs:
                fanout_sets[fanin].add(node.output)
        for output in net.outputs:
            node_names.add(output)
            fanins.setdefault(output, tuple())
        fanouts = {name: tuple(sorted(fanout_sets.get(name, set()))) for name in node_names}
        return cls(
            inputs=tuple(net.inputs),
            outputs=tuple(net.outputs),
            nodes=tuple(sorted(node_names)),
            fanins={name: tuple(fanins.get(name, tuple())) for name in sorted(node_names)},
            fanouts=fanouts,
        )

    def exists(self, node: str) -> bool:
        return node in self.fanins

    def is_primary_input(self, node: str) -> bool:
        return node in self.inputs

    def is_primary_output(self, node: str) -> bool:
        return node in self.outputs

    def transitive_fanin(self, roots: set[str] | list[str], stop_at: set[str] | None = None) -> set[str]:
        stop = set(stop_at or set())
        seen: set[str] = set()
        stack = list(sorted(roots, reverse=True))
        while stack:
            node = stack.pop()
            if node in seen:
                continue
            seen.add(node)
            if node in stop:
                continue
            for fanin in sorted(self.fanins.get(node, tuple()), reverse=True):
                stack.append(fanin)
        return seen

    def transitive_fanout(self, roots: set[str] | list[str], stop_at: set[str] | None = None) -> set[str]:
        stop = set(stop_at or set())
        seen: set[str] = set()
        stack = list(sorted(roots, reverse=True))
        while stack:
            node = stack.pop()
            if node in seen:
                continue
            seen.add(node)
            if node in stop:
                continue
            for fanout in sorted(self.fanouts.get(node, tuple()), reverse=True):
                stack.append(fanout)
        return seen

    def shortest_distance_to_any(self, start: str, targets: set[str], direction: str) -> int | None:
        if start in targets:
            return 0
        neighbors = self.fanins if direction == "fanin" else self.fanouts
        queue: deque[tuple[str, int]] = deque([(start, 0)])
        seen = {start}
        while queue:
            node, distance = queue.popleft()
            for nxt in sorted(neighbors.get(node, tuple())):
                if nxt in seen:
                    continue
                if nxt in targets:
                    return distance + 1
                seen.add(nxt)
                queue.append((nxt, distance + 1))
        return None

    def has_path(self, source: str, target: str) -> bool:
        return target in self.transitive_fanout([source])
