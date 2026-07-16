"""Simulation helpers for direct semantic candidates."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass

from analyze_blif_matches import BlifNetwork, parse_blif
from functional_signal_utils import FeaturePatternSet, evaluate_network
from semantic_ast import SemanticExpr
from semantic_patterns import SemanticPattern


SEMANTIC_SIMULATION_SCHEMA_VERSION = "semantic_candidate_simulation_v1"


@dataclass(frozen=True)
class RegionIo:
    input_buses: list[dict[str, object]]
    output_bus: dict[str, object]


def scalar_values_from_bus_assignment(net: BlifNetwork, input_buses: list[dict[str, object]], assignment: dict[str, int]) -> dict[str, int]:
    values = {name: 0 for name in net.inputs}
    for bus in input_buses:
        bus_value = int(assignment.get(str(bus["name"]), 0))
        for idx, node in enumerate(bus.get("ordered_member_nodes", [])):
            values[str(node)] = (bus_value >> idx) & 1
    return values


def gate_output_value(net: BlifNetwork, input_buses: list[dict[str, object]], output_bus: dict[str, object], assignment: dict[str, int]) -> int:
    values = scalar_values_from_bus_assignment(net, input_buses, assignment)
    pattern = FeaturePatternSet(values=values, mask=1, pattern_count=1, mode="single", evidence_level="single_pattern", seed=0, active_support=tuple(net.inputs))
    evaluated = evaluate_network(net, pattern)
    result = 0
    for idx, node in enumerate(output_bus.get("ordered_member_nodes", [])):
        if str(node) in evaluated and evaluated[str(node)].value & 1:
            result |= 1 << idx
    return result


def simulate_candidate(
    *,
    blif_path,
    input_buses: list[dict[str, object]],
    output_bus: dict[str, object],
    expr: SemanticExpr,
    patterns: list[SemanticPattern],
) -> dict[str, str]:
    start = time.perf_counter()
    net = parse_blif(blif_path)
    mismatches = []
    for pattern in patterns:
        gate = gate_output_value(net, input_buses, output_bus, pattern.input_assignment)
        candidate = expr.eval(pattern.input_assignment)
        if gate != candidate:
            mismatches.append({
                "pattern_id": pattern.pattern_id,
                "assignment": pattern.input_assignment,
                "gate_output": gate,
                "candidate_output": candidate,
                "difference": gate ^ candidate,
            })
            break
    checked = len(patterns)
    mismatch_count = len(mismatches)
    match_count = checked - mismatch_count
    return {
        "sample_count": str(checked),
        "sample_matches": str(match_count),
        "sample_mismatches": str(mismatch_count),
        "sample_match_rate": f"{match_count / max(1, checked):.6f}",
        "first_mismatch_pattern": json.dumps(mismatches[0] if mismatches else {}, sort_keys=True, separators=(",", ":")),
        "mismatch_output_bits": "" if not mismatches else str(mismatches[0]["difference"]),
        "simulation_runtime": f"{time.perf_counter() - start:.6f}",
        "simulation_status": "simulation_match" if not mismatches else "simulation_mismatch",
        "simulation_evidence_level": "sampled_estimate",
        "schema_version": SEMANTIC_SIMULATION_SCHEMA_VERSION,
    }
