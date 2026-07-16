"""Canonical scalar interface and ground-truth bus normalization."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass

from boundary_graph import CircuitGraph


BIT_SUFFIX_RE = re.compile(r"^(?P<base>.+)_(?P<index>\d+)$")


@dataclass(frozen=True)
class ScalarInterfaceEntry:
    region_id: str
    case_id: str
    optimization: str
    source_type: str
    direction: str
    interface_position: int
    raw_node_name: str
    canonical_node_id: str
    bus_name: str
    bit_index: str
    role: str

    def to_csv_row(self) -> dict[str, str]:
        return {field: str(getattr(self, field)) for field in SEMANTIC_SCALAR_INTERFACE_FIELDS}


@dataclass(frozen=True)
class BusGroundTruth:
    case_id: str
    bus_name: str
    direction: str
    width: int
    signedness: str
    declared_msb: int
    declared_lsb: int
    bit_order: str
    member_signal_names: tuple[str, ...]
    member_canonical_node_ids: tuple[str, ...]
    role: str
    mode: str = "ground_truth_bus_mode"

    def to_csv_row(self) -> dict[str, str]:
        data = asdict(self)
        row: dict[str, str] = {}
        for field in SEMANTIC_BUS_GROUND_TRUTH_FIELDS:
            value = data[field]
            if isinstance(value, tuple):
                row[field] = json.dumps(list(value), sort_keys=True, separators=(",", ":"))
            else:
                row[field] = str(value)
        return row


SEMANTIC_SCALAR_INTERFACE_FIELDS = [
    "region_id",
    "case_id",
    "optimization",
    "source_type",
    "direction",
    "interface_position",
    "raw_node_name",
    "canonical_node_id",
    "bus_name",
    "bit_index",
    "role",
]

SEMANTIC_BUS_GROUND_TRUTH_FIELDS = [
    "case_id",
    "bus_name",
    "direction",
    "width",
    "signedness",
    "declared_msb",
    "declared_lsb",
    "bit_order",
    "member_signal_names",
    "member_canonical_node_ids",
    "role",
    "mode",
]

SEMANTIC_INTERFACE_ALIGNMENT_FIELDS = [
    "region_id",
    "case_id",
    "optimization",
    "source_type",
    "all_declared_input_bits_found",
    "missing_declared_input_bits",
    "extra_scalar_inputs",
    "input_bit_order_match",
    "input_bus_membership_match",
    "all_declared_output_bits_found",
    "missing_declared_output_bits",
    "extra_scalar_outputs",
    "output_bit_order_match",
    "output_driver_alignment",
    "input_bit_recall",
    "input_bit_precision",
    "output_bit_recall",
    "output_bit_precision",
    "input_order_accuracy",
    "output_order_accuracy",
    "exact_scalar_interface_match",
]


def flat_bus_members(bus: dict[str, object]) -> tuple[str, ...]:
    name = str(bus["name"])
    width = int(bus.get("width", 1))
    if width == 1:
        return (name,)
    return tuple(f"{name}_{idx}" for idx in range(width))


def normalize_bus_metadata(case_id: str, input_buses: list[dict[str, object]], output_buses: list[dict[str, object]]) -> list[BusGroundTruth]:
    rows: list[BusGroundTruth] = []
    for direction, buses in (("input", input_buses), ("output", output_buses)):
        for bus in buses:
            name = str(bus["name"])
            width = int(bus.get("width", 1))
            role = str(bus.get("role", "output" if direction == "output" else "data_operand"))
            if role == "data":
                role = "data_operand"
            signedness = "signed" if bool(bus.get("signed", False)) else "unsigned"
            members = flat_bus_members(bus)
            rows.append(
                BusGroundTruth(
                    case_id=case_id,
                    bus_name=name,
                    direction=direction,
                    width=width,
                    signedness=signedness,
                    declared_msb=width - 1,
                    declared_lsb=0,
                    bit_order="lsb_to_msb",
                    member_signal_names=members,
                    member_canonical_node_ids=members,
                    role=role,
                )
            )
    return rows


def resolve_alias_chain(graph: CircuitGraph, node: str) -> str:
    """Resolve trivial one-input buffers while preserving distinct logic nodes."""

    seen: set[str] = set()
    current = node
    while current not in seen:
        seen.add(current)
        fanins = graph.fanins.get(current, tuple())
        if len(fanins) != 1:
            return current
        parent = fanins[0]
        if parent in graph.inputs:
            return current
        current = parent
    return node


def normalize_interface_node(graph: CircuitGraph, node: str) -> str:
    return resolve_alias_chain(graph, node)


def bit_index(name: str) -> str:
    match = BIT_SUFFIX_RE.match(name)
    return match.group("index") if match else "0"


def bus_name_for(name: str) -> str:
    match = BIT_SUFFIX_RE.match(name)
    return match.group("base") if match else name


def role_for(name: str, bus_rows: list[BusGroundTruth], direction: str) -> str:
    for row in bus_rows:
        if row.direction == direction and name in row.member_signal_names:
            return row.role
    return "unknown"


def ordered_nodes(nodes: tuple[str, ...], declared_order: tuple[str, ...], graph_order: tuple[str, ...]) -> tuple[str, ...]:
    node_set = set(nodes)
    ordered = [name for name in declared_order if name in node_set]
    remaining = sorted(node_set - set(ordered), key=lambda n: (graph_order.index(n) if n in graph_order else 10**9, n))
    return tuple(ordered + remaining)


def extract_scalar_interface(
    graph: CircuitGraph,
    *,
    region_id: str,
    case_id: str,
    optimization: str,
    source_type: str,
    boundary_inputs: tuple[str, ...],
    boundary_outputs: tuple[str, ...],
    input_buses: list[dict[str, object]],
    output_buses: list[dict[str, object]],
) -> list[ScalarInterfaceEntry]:
    bus_rows = normalize_bus_metadata(case_id, input_buses, output_buses)
    declared_inputs = tuple(name for bus in input_buses for name in flat_bus_members(bus))
    declared_outputs = tuple(name for bus in output_buses for name in flat_bus_members(bus))
    graph_order = tuple(graph.inputs) + tuple(graph.outputs) + tuple(graph.nodes)
    inputs = ordered_nodes(tuple(boundary_inputs), declared_inputs, graph_order)
    outputs = ordered_nodes(tuple(boundary_outputs), declared_outputs, graph_order)
    rows: list[ScalarInterfaceEntry] = []
    for direction, names in (("input", inputs), ("output", outputs)):
        for pos, name in enumerate(names):
            rows.append(
                ScalarInterfaceEntry(
                    region_id=region_id,
                    case_id=case_id,
                    optimization=optimization,
                    source_type=source_type,
                    direction=direction,
                    interface_position=pos,
                    raw_node_name=name,
                    canonical_node_id=normalize_interface_node(graph, name),
                    bus_name=bus_name_for(name),
                    bit_index=bit_index(name),
                    role=role_for(name, bus_rows, direction),
                )
            )
    return rows


def compare_scalar_interface(
    *,
    region_id: str,
    case_id: str,
    optimization: str,
    source_type: str,
    scalar_rows: list[ScalarInterfaceEntry],
    input_buses: list[dict[str, object]],
    output_buses: list[dict[str, object]],
) -> dict[str, str]:
    expected_inputs = [name for bus in input_buses for name in flat_bus_members(bus)]
    expected_outputs = [name for bus in output_buses for name in flat_bus_members(bus)]
    actual_inputs = [row.raw_node_name for row in scalar_rows if row.direction == "input"]
    actual_outputs = [row.raw_node_name for row in scalar_rows if row.direction == "output"]

    def metrics(expected: list[str], actual: list[str]) -> tuple[list[str], list[str], float, float, float, bool]:
        expected_set = set(expected)
        actual_set = set(actual)
        missing = sorted(expected_set - actual_set)
        extra = sorted(actual_set - expected_set)
        recall = len(expected_set & actual_set) / max(1, len(expected_set))
        precision = len(expected_set & actual_set) / max(1, len(actual_set))
        order_accuracy = 1.0 if [x for x in expected if x in actual_set] == [x for x in actual if x in expected_set] else 0.0
        return missing, extra, recall, precision, order_accuracy, not missing and not extra

    in_missing, in_extra, in_recall, in_precision, in_order, in_exact = metrics(expected_inputs, actual_inputs)
    out_missing, out_extra, out_recall, out_precision, out_order, out_exact = metrics(expected_outputs, actual_outputs)
    exact = in_exact and out_exact and in_order == 1.0 and out_order == 1.0
    return {
        "region_id": region_id,
        "case_id": case_id,
        "optimization": optimization,
        "source_type": source_type,
        "all_declared_input_bits_found": str(not in_missing).lower(),
        "missing_declared_input_bits": json.dumps(in_missing, sort_keys=True, separators=(",", ":")),
        "extra_scalar_inputs": json.dumps(in_extra, sort_keys=True, separators=(",", ":")),
        "input_bit_order_match": str(in_order == 1.0).lower(),
        "input_bus_membership_match": str(not in_missing and not in_extra).lower(),
        "all_declared_output_bits_found": str(not out_missing).lower(),
        "missing_declared_output_bits": json.dumps(out_missing, sort_keys=True, separators=(",", ":")),
        "extra_scalar_outputs": json.dumps(out_extra, sort_keys=True, separators=(",", ":")),
        "output_bit_order_match": str(out_order == 1.0).lower(),
        "output_driver_alignment": str(not out_missing).lower(),
        "input_bit_recall": f"{in_recall:.6f}",
        "input_bit_precision": f"{in_precision:.6f}",
        "output_bit_recall": f"{out_recall:.6f}",
        "output_bit_precision": f"{out_precision:.6f}",
        "input_order_accuracy": f"{in_order:.6f}",
        "output_order_accuracy": f"{out_order:.6f}",
        "exact_scalar_interface_match": str(exact).lower(),
    }
