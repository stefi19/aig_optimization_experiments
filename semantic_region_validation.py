"""Validation helpers for canonical semantic regions."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass

from boundary_graph import CircuitGraph
from coi_model import derive_boundary_inputs, derive_boundary_outputs
from semantic_region import non_input_logic_nodes


@dataclass(frozen=True)
class SemanticRegionValidation:
    region_id: str
    valid: bool
    errors: tuple[str, ...]
    warnings: tuple[str, ...]
    derived_bi: tuple[str, ...]
    derived_bo: tuple[str, ...]
    missing_region_nodes: tuple[str, ...]
    extra_region_nodes: tuple[str, ...]
    missing_bi: tuple[str, ...]
    extra_bi: tuple[str, ...]
    missing_bo: tuple[str, ...]
    extra_bo: tuple[str, ...]
    incoming_bypass_edges: tuple[str, ...]
    outgoing_bypass_edges: tuple[str, ...]
    whole_design_region: bool
    region_fraction_of_design: float

    def to_csv_row(self) -> dict[str, str]:
        data = asdict(self)
        row: dict[str, str] = {}
        for field in SEMANTIC_REGION_VALIDATION_FIELDS:
            value = data[field]
            if isinstance(value, tuple):
                row[field] = json.dumps(list(value), sort_keys=True, separators=(",", ":"))
            elif isinstance(value, bool):
                row[field] = str(value).lower()
            else:
                row[field] = str(value)
        return row


SEMANTIC_REGION_VALIDATION_FIELDS = [
    "region_id",
    "valid",
    "errors",
    "warnings",
    "derived_bi",
    "derived_bo",
    "missing_region_nodes",
    "extra_region_nodes",
    "missing_bi",
    "extra_bi",
    "missing_bo",
    "extra_bo",
    "incoming_bypass_edges",
    "outgoing_bypass_edges",
    "whole_design_region",
    "region_fraction_of_design",
]


def validate_semantic_region(
    graph: CircuitGraph,
    *,
    region_id: str,
    region_nodes: tuple[str, ...] | list[str],
    boundary_inputs: tuple[str, ...] | list[str],
    boundary_outputs: tuple[str, ...] | list[str],
    observable_outputs: tuple[str, ...] | list[str],
    expected_region_nodes: tuple[str, ...] | list[str] = (),
    expected_benchmark: str = "",
    actual_benchmark: str = "",
    expected_optimization: str = "",
    actual_optimization: str = "",
) -> SemanticRegionValidation:
    region = set(region_nodes)
    bi = set(boundary_inputs)
    bo = set(boundary_outputs)
    expected_region = set(expected_region_nodes)
    errors: list[str] = []
    warnings: list[str] = []

    if expected_benchmark and actual_benchmark and expected_benchmark != actual_benchmark:
        errors.append("benchmark_mismatch")
    if expected_optimization and actual_optimization and expected_optimization != actual_optimization:
        errors.append("optimization_mismatch")
    if not region:
        errors.append("empty_region")

    known = set(graph.nodes)
    missing_region = tuple(sorted(node for node in region if node not in known))
    missing_bi_nodes = tuple(sorted(node for node in bi if node not in known))
    missing_bo_nodes = tuple(sorted(node for node in bo if node not in known))
    errors.extend(f"missing_region_node:{node}" for node in missing_region)
    errors.extend(f"missing_boundary_input_node:{node}" for node in missing_bi_nodes)
    errors.extend(f"missing_boundary_output_node:{node}" for node in missing_bo_nodes)

    if bi & region:
        errors.extend(f"boundary_input_inside_region:{node}" for node in sorted(bi & region))
    if not bo <= region:
        errors.extend(f"boundary_output_not_in_region:{node}" for node in sorted(bo - region))

    derived_bi = set(derive_boundary_inputs(graph, region)) if not (missing_region or missing_bi_nodes or missing_bo_nodes) else set()
    derived_bo = set(derive_boundary_outputs(graph, region)) if not (missing_region or missing_bi_nodes or missing_bo_nodes) else set()
    missing_bi = tuple(sorted(derived_bi - bi))
    extra_bi = tuple(sorted(bi - derived_bi))
    missing_bo = tuple(sorted(derived_bo - bo))
    extra_bo = tuple(sorted(bo - derived_bo))
    errors.extend(f"missing_boundary_input:{node}" for node in missing_bi)
    errors.extend(f"extra_boundary_input:{node}" for node in extra_bi)
    errors.extend(f"missing_boundary_output:{node}" for node in missing_bo)
    errors.extend(f"extra_boundary_output:{node}" for node in extra_bo)

    incoming_bypass = tuple(
        sorted(
            f"{fanin}->{node}"
            for node in region
            for fanin in graph.fanins.get(node, tuple())
            if fanin not in region and fanin not in bi
        )
    )
    outgoing_bypass = tuple(
        sorted(
            f"{node}->{fanout}"
            for node in region
            for fanout in graph.fanouts.get(node, tuple())
            if fanout not in region and node not in bo
        )
    )
    errors.extend(f"incoming_bypass:{edge}" for edge in incoming_bypass)
    errors.extend(f"outgoing_bypass:{edge}" for edge in outgoing_bypass)

    missing_observable = tuple(sorted(out for out in observable_outputs if out not in graph.outputs))
    errors.extend(f"missing_observable_output:{out}" for out in missing_observable)
    for out in observable_outputs:
        if out in graph.outputs and out not in graph.transitive_fanout(list(region)) and out not in region:
            errors.append(f"observable_output_not_reachable:{out}")

    missing_expected = tuple(sorted(expected_region - region))
    extra_expected = tuple(sorted(region - expected_region)) if expected_region else tuple()
    if missing_expected:
        errors.extend(f"missing_expected_region_node:{node}" for node in missing_expected)

    logic_nodes = non_input_logic_nodes(graph)
    whole = bool(region) and region >= logic_nodes
    if whole:
        warnings.append("whole_design_region")
    fraction = len(region) / max(1, len(logic_nodes))

    return SemanticRegionValidation(
        region_id=region_id,
        valid=not errors,
        errors=tuple(errors),
        warnings=tuple(warnings),
        derived_bi=tuple(sorted(derived_bi)),
        derived_bo=tuple(sorted(derived_bo)),
        missing_region_nodes=missing_region,
        extra_region_nodes=extra_expected,
        missing_bi=missing_bi,
        extra_bi=extra_bi,
        missing_bo=missing_bo,
        extra_bo=extra_bo,
        incoming_bypass_edges=incoming_bypass,
        outgoing_bypass_edges=outgoing_bypass,
        whole_design_region=whole,
        region_fraction_of_design=round(fraction, 6),
    )
