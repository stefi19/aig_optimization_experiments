"""Proof-carrying semantic region replacement models and helpers."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path

from analyze_blif_matches import BlifNetwork, BlifNode, parse_blif
from boundary_graph import CircuitGraph
from semantic_ast import SemanticExpr, const_expr, input_expr
from semantic_region import write_csv
from semantic_z3_validation import validate_candidate_z3


SCHEMA_VERSION = "semantic_region_replacement_v1"


@dataclass(frozen=True)
class SemanticReplacementRegion:
    region_id: str
    benchmark: str
    optimisation: str
    coi_name: str
    implementation_nodes: tuple[str, ...]
    input_cut: tuple[str, ...]
    output_cut: tuple[str, ...]
    external_fanout_edges: tuple[tuple[str, str], ...]
    observable_outputs: tuple[str, ...]
    inferred_input_buses: tuple[dict[str, object], ...]
    inferred_output_buses: tuple[dict[str, object], ...]
    recovered_expressions: tuple[dict[str, object], ...]
    proof_scope: str
    region_proof_status: str
    graph_closure_status: str
    replacement_cost: int
    provenance: dict[str, object]
    schema_version: str = SCHEMA_VERSION

    def to_csv_row(self) -> dict[str, str]:
        data = asdict(self)
        return {field: _csv_value(data[field]) for field in REGION_FIELDS}


@dataclass(frozen=True)
class SemanticModule:
    module_id: str
    input_buses: tuple[dict[str, object], ...]
    output_buses: tuple[dict[str, object], ...]
    output_expressions: tuple[SemanticExpr, ...]
    shared_subexpressions: tuple[str, ...]
    proof_status: str = "unproven"

    @property
    def canonical_form(self) -> str:
        return ";".join(f"{bus['name']}={expr.canonical_form}" for bus, expr in zip(self.output_buses, self.output_expressions))

    @property
    def dag_cost(self) -> int:
        seen: set[str] = set()
        def visit(expr: SemanticExpr) -> int:
            if expr.canonical_form in seen:
                return 0
            seen.add(expr.canonical_form)
            return 1 + sum(visit(arg) for arg in expr.operands)
        return sum(visit(expr) for expr in self.output_expressions)

    def to_verilog(self) -> str:
        ports = [str(b["name"]) for b in self.input_buses] + [str(b["name"]) for b in self.output_buses]
        lines = [f"module {self.module_id}({', '.join(ports)});"]
        for bus in self.input_buses:
            lines.append(_decl("input", bus))
        for bus in self.output_buses:
            lines.append(_decl("output", bus))
        for bus, expr in zip(self.output_buses, self.output_expressions):
            lines.append(f"  assign {bus['name']} = {expr.rtl_text};")
        lines.append("endmodule")
        return "\n".join(lines) + "\n"

    def to_json(self) -> dict[str, object]:
        return {
            "module_id": self.module_id,
            "input_buses": list(self.input_buses),
            "output_buses": list(self.output_buses),
            "output_expressions": [expr.to_tree() for expr in self.output_expressions],
            "canonical_form": self.canonical_form,
            "dag_cost": self.dag_cost,
            "proof_status": self.proof_status,
            "schema_version": SCHEMA_VERSION,
        }


REGION_FIELDS = [
    "region_id", "benchmark", "optimisation", "coi_name", "implementation_nodes",
    "input_cut", "output_cut", "external_fanout_edges", "observable_outputs",
    "inferred_input_buses", "inferred_output_buses", "recovered_expressions",
    "proof_scope", "region_proof_status", "graph_closure_status",
    "replacement_cost", "provenance", "schema_version",
]


def derive_closed_region(graph: CircuitGraph, output_cut: tuple[str, ...], *, max_nodes: int = 64) -> tuple[tuple[str, ...], tuple[str, ...], tuple[tuple[str, str], ...], str]:
    region = set(output_cut)
    stack = list(output_cut)
    while stack and len(region) <= max_nodes:
        node = stack.pop()
        for fanin in graph.fanins.get(node, ()):
            if fanin in graph.inputs:
                continue
            if fanin not in region:
                region.add(fanin)
                stack.append(fanin)
    if len(region) > max_nodes:
        return tuple(sorted(region)), tuple(), tuple(), "rejected_region_node_bound"
    input_cut = sorted({fanin for node in region for fanin in graph.fanins.get(node, ()) if fanin not in region})
    external_edges = sorted((node, fanout) for node in region for fanout in graph.fanouts.get(node, ()) if fanout not in region)
    output_nodes = sorted(set(output_cut) | {src for src, _ in external_edges} | {node for node in region if node in graph.outputs})
    status = validate_closed_region(graph, tuple(sorted(region)), tuple(input_cut), tuple(output_nodes), tuple(external_edges))
    return tuple(sorted(region)), tuple(input_cut), tuple(external_edges), status


def validate_closed_region(graph: CircuitGraph, region: tuple[str, ...], input_cut: tuple[str, ...], output_cut: tuple[str, ...], external_edges: tuple[tuple[str, str], ...]) -> str:
    r = set(region)
    ci = set(input_cut)
    co = set(output_cut)
    for node in r:
        for fanin in graph.fanins.get(node, ()):
            if fanin not in r and fanin not in ci:
                return "invalid_incomplete_input_cut"
        for fanout in graph.fanouts.get(node, ()):
            if fanout not in r and node not in co:
                return "invalid_unaccounted_external_fanout"
    for src, dst in external_edges:
        if src not in co or dst in r:
            return "invalid_external_fanout_edge"
    if not region or set(graph.nodes) == r:
        return "invalid_whole_design_expansion"
    return "closed"


def make_bus(name: str, members: tuple[str, ...], role: str) -> dict[str, object]:
    return {"name": name, "role": role, "width": len(members), "signed": False, "ordered_member_nodes": members}


def module_for_identity_region(region_id: str, input_cut: tuple[str, ...], output_cut: tuple[str, ...]) -> SemanticModule:
    inputs = tuple(make_bus(f"in{idx}", (node,), "data_operand") for idx, node in enumerate(input_cut))
    outputs = tuple(make_bus(f"out{idx}", (node,), "output") for idx, node in enumerate(output_cut))
    exprs = []
    for idx, _ in enumerate(output_cut):
        source = inputs[min(idx, max(0, len(inputs) - 1))]["name"] if inputs else "zero"
        exprs.append(input_expr(str(source), 1) if inputs else const_expr(0, 1))
    return SemanticModule(f"sem_region_{_safe(region_id)}", inputs, outputs, tuple(exprs), tuple())


def full_adder_module(module_id: str = "sem_full_adder") -> SemanticModule:
    a, b, cin = input_expr("a", 1), input_expr("b", 1), input_expr("cin", 1)
    xor_ab = SemanticExpr("xor", (a, b), output_type=a.output_type)
    sum_expr = SemanticExpr("xor", (xor_ab, cin), output_type=a.output_type)
    carry = SemanticExpr("or", (
        SemanticExpr("or", (SemanticExpr("and", (a, b), output_type=a.output_type), SemanticExpr("and", (a, cin), output_type=a.output_type)), output_type=a.output_type),
        SemanticExpr("and", (b, cin), output_type=a.output_type),
    ), output_type=a.output_type)
    return SemanticModule(
        module_id,
        (make_bus("a", ("a",), "data_operand"), make_bus("b", ("b",), "data_operand"), make_bus("cin", ("cin",), "data_operand")),
        (make_bus("sum", ("sum",), "output"), make_bus("cout", ("cout",), "output")),
        (sum_expr, carry),
        (xor_ab.canonical_form,),
    )


def emit_module_blif(module: SemanticModule, path: Path) -> None:
    lines = [f".model {module.module_id}"]
    scalar_inputs = [member for bus in module.input_buses for member in bus["ordered_member_nodes"]]
    scalar_outputs = [member for bus in module.output_buses for member in bus["ordered_member_nodes"]]
    lines.append(".inputs " + " ".join(scalar_inputs))
    lines.append(".outputs " + " ".join(scalar_outputs))
    for bus, expr in zip(module.output_buses, module.output_expressions):
        out = str(bus["ordered_member_nodes"][0])
        lines.append(".names " + " ".join(scalar_inputs + [out]))
        for assignment in range(1 << len(scalar_inputs)):
            env: dict[str, int] = {}
            for bus_in in module.input_buses:
                value = 0
                for idx, member in enumerate(bus_in["ordered_member_nodes"]):
                    scalar_idx = scalar_inputs.index(str(member))
                    if (assignment >> scalar_idx) & 1:
                        value |= 1 << idx
                env[str(bus_in["name"])] = value
            if expr.eval(env) & 1:
                lines.append("".join(str((assignment >> idx) & 1) for idx in range(len(scalar_inputs))) + " 1")
    lines.append(".end")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_replaced_blif(original: Path, region: tuple[str, ...], module: SemanticModule, output_path: Path) -> dict[str, str]:
    net = parse_blif(original)
    removed = set(region)
    new_nodes = [node for node in net.nodes if node.output not in removed]
    # For controlled benchmarks, replacement outputs intentionally reuse cut
    # names so all existing external fanouts remain graph-active.
    repl_path = output_path.with_suffix(".module.blif")
    emit_module_blif(module, repl_path)
    repl_net = parse_blif(repl_path)
    new_nodes.extend(repl_net.nodes)
    _write_network(BlifNetwork(inputs=net.inputs, outputs=net.outputs, nodes=new_nodes), output_path)
    reparsed = parse_blif(output_path)
    driven = [node.output for node in reparsed.nodes]
    if len(driven) != len(set(driven)):
        return {"graph_rewrite_status": "invalid_multiple_driver", "graph_active": "false"}
    fanins = {name for node in reparsed.nodes for name in node.inputs}
    known = set(reparsed.inputs) | set(driven)
    dangling = sorted(fanins - known)
    if dangling:
        return {"graph_rewrite_status": "invalid_dangling_fanin", "graph_active": "false", "dangling_fanins": json.dumps(dangling)}
    return {"graph_rewrite_status": "valid", "graph_active": "true", "dangling_fanins": "[]"}


def _write_network(net: BlifNetwork, path: Path) -> None:
    lines = [".model replaced", ".inputs " + " ".join(net.inputs), ".outputs " + " ".join(net.outputs)]
    for node in net.nodes:
        lines.append(".names " + " ".join(node.inputs + [node.output]))
        lines.extend(node.cover)
    lines.append(".end")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _decl(kind: str, bus: dict[str, object]) -> str:
    width = int(bus["width"])
    rng = f"[{width - 1}:0] " if width > 1 else ""
    return f"  {kind} {rng}{bus['name']};"


def _csv_value(value: object) -> str:
    if isinstance(value, (tuple, list, dict)):
        return json.dumps(value, sort_keys=True, separators=(",", ":"))
    return str(value)


def _safe(value: str) -> str:
    return hashlib.sha1(value.encode("utf-8")).hexdigest()[:10]
