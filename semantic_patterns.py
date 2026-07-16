"""Deterministic semantic input-pattern generation."""

from __future__ import annotations

import json
import random
from dataclasses import dataclass

from functional_signal_utils import stable_seed
from semantic_types import mask, to_signed


@dataclass(frozen=True)
class SemanticPattern:
    pattern_id: str
    pattern_family: str
    seed: int
    input_assignment: dict[str, int]

    def to_csv_json(self) -> str:
        return json.dumps(self.input_assignment, sort_keys=True, separators=(",", ":"))


def boundary_values(width: int, signed: bool) -> list[int]:
    values = [0, 1, mask(width), 0xAAAAAAAA & mask(width), 0x55555555 & mask(width)]
    for idx in range(width):
        values.append(1 << idx)
        values.append(mask(width) ^ (1 << idx))
    if signed and width > 1:
        values.extend([(1 << (width - 1)), (1 << (width - 1)) - 1])
    return sorted(set(v & mask(width) for v in values))


def generate_semantic_patterns(
    buses: list[dict[str, object]],
    *,
    seed: int = 20260716,
    random_count: int = 16,
    max_patterns: int = 96,
) -> list[SemanticPattern]:
    if not buses:
        return []
    patterns: list[SemanticPattern] = []

    def add(family: str, assignment: dict[str, int]) -> None:
        if len(patterns) >= max_patterns:
            return
        patterns.append(SemanticPattern(f"p{len(patterns):04d}", family, seed, {bus["name"]: int(assignment.get(str(bus["name"]), 0)) & mask(int(bus["width"])) for bus in buses}))

    add("all_zero", {})
    add("all_one", {str(bus["name"]): mask(int(bus["width"])) for bus in buses})
    for bus in buses:
        width = int(bus["width"])
        signed = bool(bus.get("signed", False))
        for value in boundary_values(width, signed)[: min(12, 2 * width + 4)]:
            assignment = {str(other["name"]): 0 for other in buses}
            assignment[str(bus["name"])] = value
            add("walking_boundary", assignment)
    if any(str(bus.get("role", "")) in {"selector", "control"} for bus in buses):
        controls = [bus for bus in buses if str(bus.get("role", "")) in {"selector", "control"} and int(bus["width"]) <= 2]
        for ctrl in controls:
            for value in range(1 << int(ctrl["width"])):
                assignment = {str(bus["name"]): 1 if str(bus.get("role", "")) == "data_operand" else 0 for bus in buses}
                assignment[str(ctrl["name"])] = value
                add("control_selector", assignment)
    rng = random.Random(stable_seed(seed, "semantic_patterns"))
    for _ in range(random_count):
        add("deterministic_random", {str(bus["name"]): rng.getrandbits(int(bus["width"])) & mask(int(bus["width"])) for bus in buses})
    return patterns[:max_patterns]


def exhaustive_bus_assignments(buses: list[dict[str, object]], max_scalar_bits: int = 12) -> tuple[list[dict[str, int]], str]:
    total_bits = sum(int(bus["width"]) for bus in buses)
    if total_bits > max_scalar_bits:
        return [], "support_too_large_for_exhaustive_formal"
    assignments: list[dict[str, int]] = []
    offsets: dict[str, tuple[int, int]] = {}
    offset = 0
    for bus in buses:
        offsets[str(bus["name"])] = (offset, int(bus["width"]))
        offset += int(bus["width"])
    for pattern in range(1 << total_bits):
        row = {}
        for name, (start, width) in offsets.items():
            row[name] = (pattern >> start) & mask(width)
        assignments.append(row)
    return assignments, "formal_exhaustive"
