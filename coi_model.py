"""Canonical COI semantics for boundary-recovery experiments.

Convention, schema version ``coi_schema_v1``:

``R``
    Internal region nodes.
``BI``
    Nodes outside ``R`` with at least one fanout into ``R``.
``BO``
    Nodes inside ``R`` that either have a fanout outside ``R`` or are primary
    outputs.

Boundary inputs are not members of ``R``. Boundary outputs are members of
``R``.  All derivation is graph based; node names are never interpreted
semantically.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass

from boundary_graph import CircuitGraph


COI_SCHEMA_VERSION = "coi_schema_v1"
BOUNDARY_MEMBERSHIP_CONVENTION = "BI outside R; BO subset of R"


@dataclass(frozen=True)
class CanonicalCoi:
    benchmark: str
    optimization: str
    coi_name: str
    region_nodes: tuple[str, ...]
    boundary_inputs: tuple[str, ...]
    boundary_outputs: tuple[str, ...]
    source: str
    coi_schema_version: str = COI_SCHEMA_VERSION
    boundary_membership_convention: str = BOUNDARY_MEMBERSHIP_CONVENTION
    generation_method: str = "canonical_derivation"
    original_manifest_status: str = ""
    repair_notes: str = ""


@dataclass(frozen=True)
class CoiValidationResult:
    valid: bool
    errors: tuple[str, ...]
    warnings: tuple[str, ...]
    derived_bi: tuple[str, ...]
    derived_bo: tuple[str, ...]
    missing_bi: tuple[str, ...]
    extra_bi: tuple[str, ...]
    missing_bo: tuple[str, ...]
    extra_bo: tuple[str, ...]
    unexpected_external_in_edges: tuple[str, ...]
    unexpected_external_out_edges: tuple[str, ...]
    disconnected_region_components: tuple[str, ...]
    whole_design_region: bool


@dataclass(frozen=True)
class ExtractedRegion:
    region_nodes: tuple[str, ...]
    region_edges: tuple[tuple[str, str], ...]
    unexpected_nodes: tuple[str, ...]
    missing_required_nodes: tuple[str, ...]
    bypass_edges: tuple[tuple[str, str], ...]


def derive_boundary_inputs(graph: CircuitGraph, region_nodes: set[str] | list[str] | tuple[str, ...]) -> tuple[str, ...]:
    region = set(region_nodes)
    return tuple(
        sorted(
            fanin
            for node in region
            for fanin in graph.fanins.get(node, tuple())
            if fanin not in region
        )
    )


def derive_boundary_outputs(graph: CircuitGraph, region_nodes: set[str] | list[str] | tuple[str, ...]) -> tuple[str, ...]:
    region = set(region_nodes)
    outputs = set(graph.outputs)
    return tuple(
        sorted(
            node
            for node in region
            if node in outputs or any(fanout not in region for fanout in graph.fanouts.get(node, tuple()))
        )
    )


def normalize_coi(
    graph: CircuitGraph,
    *,
    benchmark: str,
    optimization: str,
    coi_name: str,
    region_nodes: set[str] | list[str] | tuple[str, ...],
    source: str,
    generation_method: str = "canonical_derivation",
    original_manifest_status: str = "",
    repair_notes: str = "",
) -> CanonicalCoi:
    region = tuple(sorted(set(region_nodes)))
    return CanonicalCoi(
        benchmark=benchmark,
        optimization=optimization,
        coi_name=coi_name,
        region_nodes=region,
        boundary_inputs=derive_boundary_inputs(graph, region),
        boundary_outputs=derive_boundary_outputs(graph, region),
        source=source,
        generation_method=generation_method,
        original_manifest_status=original_manifest_status,
        repair_notes=repair_notes,
    )


def validate_coi(graph: CircuitGraph, coi: CanonicalCoi, *, require_connected: bool = True) -> CoiValidationResult:
    errors: list[str] = []
    warnings: list[str] = []
    region = set(coi.region_nodes)
    bi = set(coi.boundary_inputs)
    bo = set(coi.boundary_outputs)
    missing_nodes = sorted(node for node in region | bi | bo if not graph.exists(node))
    if missing_nodes:
        errors.extend(f"missing_node:{node}" for node in missing_nodes)
    if not region:
        errors.append("empty_region")
    if bi & region:
        errors.extend(f"boundary_input_inside_region:{node}" for node in sorted(bi & region))
    if not bo <= region:
        errors.extend(f"boundary_output_membership_error:{node}" for node in sorted(bo - region))

    derived_bi = set(derive_boundary_inputs(graph, region)) if not missing_nodes else set()
    derived_bo = set(derive_boundary_outputs(graph, region)) if not missing_nodes else set()
    missing_bi = tuple(sorted(derived_bi - bi))
    extra_bi = tuple(sorted(bi - derived_bi))
    missing_bo = tuple(sorted(derived_bo - bo))
    extra_bo = tuple(sorted(bo - derived_bo))
    errors.extend(f"missing_boundary_input:{node}" for node in missing_bi)
    errors.extend(f"extra_boundary_input:{node}" for node in extra_bi)
    errors.extend(f"missing_boundary_output:{node}" for node in missing_bo)
    errors.extend(f"extra_boundary_output:{node}" for node in extra_bo)

    unexpected_in = tuple(
        sorted(
            f"{fanin}->{node}"
            for node in region
            for fanin in graph.fanins.get(node, tuple())
            if fanin not in region and fanin not in bi
        )
    )
    unexpected_out = tuple(
        sorted(
            f"{node}->{fanout}"
            for node in region
            for fanout in graph.fanouts.get(node, tuple())
            if fanout not in region and node not in bo
        )
    )
    errors.extend(f"unexpected_external_input_edge:{edge}" for edge in unexpected_in)
    errors.extend(f"unexpected_external_output_edge:{edge}" for edge in unexpected_out)

    components = tuple(component_labels(graph, region))
    if require_connected and len(components) > 1:
        errors.append("disconnected_region")

    non_input_nodes = {node for node in graph.nodes if node not in graph.inputs}
    whole_design = bool(region) and region >= non_input_nodes
    if whole_design:
        warnings.append("whole_design_region")

    return CoiValidationResult(
        valid=not errors,
        errors=tuple(errors),
        warnings=tuple(warnings),
        derived_bi=tuple(sorted(derived_bi)),
        derived_bo=tuple(sorted(derived_bo)),
        missing_bi=missing_bi,
        extra_bi=extra_bi,
        missing_bo=missing_bo,
        extra_bo=extra_bo,
        unexpected_external_in_edges=unexpected_in,
        unexpected_external_out_edges=unexpected_out,
        disconnected_region_components=components,
        whole_design_region=whole_design,
    )


def component_labels(graph: CircuitGraph, region: set[str]) -> list[str]:
    unseen = set(region)
    labels: list[str] = []
    while unseen:
        start = min(unseen)
        queue = deque([start])
        component = {start}
        unseen.remove(start)
        while queue:
            node = queue.popleft()
            neighbors = set(graph.fanins.get(node, tuple())) | set(graph.fanouts.get(node, tuple()))
            for nxt in sorted(neighbors & unseen):
                unseen.remove(nxt)
                component.add(nxt)
                queue.append(nxt)
        labels.append(";".join(sorted(component)))
    return labels


def extract_region_from_boundaries(
    graph: CircuitGraph,
    ebi: set[str],
    ebo: set[str],
    required_nodes: set[str] | None = None,
) -> ExtractedRegion:
    """Extract the canonical region enclosed by EBI/EBO.

    The candidate is the intersection of nodes reachable forward from EBI
    successors and nodes that can reach an EBO, excluding EBI and including EBO.
    If ``required_nodes`` is provided, it is used only as a validation constraint
    and to report unexpected/missing nodes; extraction still comes from graph
    reachability.
    """

    starts = sorted({fanout for node in ebi for fanout in graph.fanouts.get(node, tuple()) if fanout not in ebi})
    forward = forward_reachable(graph, starts, stop_at=ebi)
    backward = graph.transitive_fanin(list(ebo), stop_at=ebi)
    region = (forward & backward) | set(ebo)
    region -= set(ebi)
    required = set(required_nodes or set())
    edges = tuple(
        sorted(
            (fanin, node)
            for node in region
            for fanin in graph.fanins.get(node, tuple())
            if fanin in region
        )
    )
    bypass = tuple(
        sorted(
            (fanin, node)
            for node in region
            for fanin in graph.fanins.get(node, tuple())
            if fanin not in region and fanin not in ebi
        )
    )
    return ExtractedRegion(
        region_nodes=tuple(sorted(region)),
        region_edges=edges,
        unexpected_nodes=tuple(sorted(region - required)) if required else tuple(),
        missing_required_nodes=tuple(sorted(required - region)),
        bypass_edges=bypass,
    )


def forward_reachable(graph: CircuitGraph, starts: list[str], stop_at: set[str] | None = None) -> set[str]:
    stop = set(stop_at or set())
    seen: set[str] = set()
    stack = list(reversed(sorted(starts)))
    while stack:
        node = stack.pop()
        if node in seen or node in stop:
            continue
        seen.add(node)
        for fanout in sorted(graph.fanouts.get(node, tuple()), reverse=True):
            stack.append(fanout)
    return seen


def canonical_dict(coi: CanonicalCoi) -> dict[str, object]:
    return {
        "benchmark": coi.benchmark,
        "optimization": coi.optimization,
        "coi_name": coi.coi_name,
        "region_nodes": list(coi.region_nodes),
        "boundary_inputs": list(coi.boundary_inputs),
        "boundary_outputs": list(coi.boundary_outputs),
        "source": coi.source,
        "coi_schema_version": coi.coi_schema_version,
        "boundary_membership_convention": coi.boundary_membership_convention,
        "generation_method": coi.generation_method,
        "original_manifest_status": coi.original_manifest_status,
        "repair_notes": coi.repair_notes,
    }
