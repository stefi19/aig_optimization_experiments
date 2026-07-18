"""Proof-carrying semantic functional refactoring.

This module implements the source-blind decomposition proof used by the
semantic-functional-refactoring experiment:

    F(X, Z) = H(G(X), Z)

The core proof is the standard two-copy decomposition obligation.  A quotient
exists for a divisor ``G`` and residual interface ``Z`` iff two assignments with
equal ``G`` and equal ``Z`` can never disagree on the selected window outputs.
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

try:  # pragma: no cover
    import z3
except Exception:  # pragma: no cover
    z3 = None  # type: ignore[assignment]

from analyze_blif_matches import BlifNetwork, BlifNode, parse_blif
from blif_z3 import bool_to_bv1, encode_cover
from functional_signal_utils import FeaturePatternSet, evaluate_network
from semantic_ast import SemanticExpr
from semantic_region_replacement import SemanticModule, emit_module_blif
from semantic_z3 import expr_to_z3


SCHEMA_VERSION = "semantic_functional_refactoring_v1"


@dataclass(frozen=True)
class SemanticDivisor:
    divisor_id: str
    benchmark: str
    origin: str
    support_buses: tuple[dict[str, object], ...]
    output_buses: tuple[dict[str, object], ...]
    expressions: tuple[SemanticExpr, ...]
    semantic_family: str
    semantic_cost: int
    source_blind: bool = True
    schema_version: str = SCHEMA_VERSION

    @property
    def canonical_form(self) -> str:
        return ";".join(f"{bus['name']}={expr.canonical_form}" for bus, expr in zip(self.output_buses, self.expressions))

    @property
    def fingerprint(self) -> str:
        payload = {
            "support": self.support_buses,
            "outputs": self.output_buses,
            "expr": self.canonical_form,
        }
        return _hash(payload)

    def module(self, module_id: str | None = None) -> SemanticModule:
        from semantic_types import unsigned_bitvector

        output_buses: list[dict[str, object]] = []
        expressions: list[SemanticExpr] = []
        for bus, expr in zip(self.output_buses, self.expressions):
            members = tuple(str(node) for node in bus["ordered_member_nodes"])
            if expr.width == 1 and len(members) == 1:
                output_buses.append(bus)
                expressions.append(expr)
                continue
            for idx, member in enumerate(members):
                output_buses.append({"name": member, "role": bus.get("role", "semantic_divisor"), "width": 1, "signed": False, "ordered_member_nodes": (member,)})
                expressions.append(SemanticExpr("slice", (expr,), output_type=unsigned_bitvector(1), slice_range=(idx, idx)))
        return SemanticModule(
            module_id or f"div_{self.divisor_id}",
            self.support_buses,
            tuple(output_buses),
            tuple(expressions),
            tuple(sorted({expr.canonical_form for expr in self.expressions})),
            proof_status="proven",
        )


@dataclass(frozen=True)
class RefactoringWindow:
    window_id: str
    benchmark: str
    optimisation: str
    split: str
    blif_path: str
    window_inputs: tuple[str, ...]
    window_outputs: tuple[str, ...]
    window_nodes: tuple[str, ...]
    reason: str
    source_blind: bool = True
    schema_version: str = SCHEMA_VERSION

    @property
    def fingerprint(self) -> str:
        return _hash(asdict(self))


@dataclass(frozen=True)
class FunctionalDecompositionCandidate:
    candidate_id: str
    benchmark: str
    split: str
    divisor_id: str
    window_id: str
    divisor_support: tuple[str, ...]
    residual_support: tuple[str, ...]
    divisor_outputs: tuple[str, ...]
    window_outputs: tuple[str, ...]
    grammar_tier: str
    deterministic_seed: int = 0
    source_blind: bool = True
    schema_version: str = SCHEMA_VERSION

    @property
    def fingerprint(self) -> str:
        return _hash(asdict(self))


@dataclass(frozen=True)
class QuotientFunction:
    quotient_id: str
    candidate_id: str
    input_order: tuple[str, ...]
    output_order: tuple[str, ...]
    rows: tuple[tuple[str, str], ...]
    completion_policy: str
    node_count: int
    schema_version: str = SCHEMA_VERSION


@dataclass(frozen=True)
class SemanticRefactoringResult:
    candidate_id: str
    decomposition_status: str
    quotient_status: str
    non_vacuity_status: str
    graph_rewrite_status: str
    global_cec_status: str
    graph_active: bool
    boundary_restored: bool
    rejection_reason: str
    schema_version: str = SCHEMA_VERSION


def make_bus(name: str, members: Iterable[str], role: str = "data") -> dict[str, object]:
    members_tuple = tuple(members)
    return {"name": name, "role": role, "width": len(members_tuple), "signed": False, "ordered_member_nodes": members_tuple}


def scalar_eval(net: BlifNetwork, assignment: dict[str, int]) -> dict[str, int]:
    pattern = FeaturePatternSet(values={name: int(assignment.get(name, 0)) for name in net.inputs}, mask=1, pattern_count=1, mode="single", evidence_level="single_pattern", seed=0, active_support=tuple(net.inputs))
    evaluated = evaluate_network(net, pattern)
    return {name: int(value.value & 1) for name, value in evaluated.items()}


def eval_outputs(net: BlifNetwork, outputs: tuple[str, ...], assignment: dict[str, int]) -> tuple[int, ...]:
    values = scalar_eval(net, assignment)
    return tuple(values.get(name, 0) for name in outputs)


def eval_divisor(divisor: SemanticDivisor, assignment: dict[str, int]) -> tuple[int, ...]:
    env: dict[str, int] = {}
    for bus in divisor.support_buses:
        value = 0
        for idx, node in enumerate(bus["ordered_member_nodes"]):
            value |= (int(assignment.get(str(node), 0)) & 1) << idx
        env[str(bus["name"])] = value
    out: list[int] = []
    for bus, expr in zip(divisor.output_buses, divisor.expressions):
        value = expr.eval(env)
        for idx, _node in enumerate(bus["ordered_member_nodes"]):
            out.append((value >> idx) & 1)
    return tuple(out)


def prove_decomposability_z3(
    *,
    blif_path: Path,
    divisor: SemanticDivisor,
    residual_support: tuple[str, ...],
    output_nodes: tuple[str, ...],
    timeout_ms: int = 5000,
) -> dict[str, object]:
    """Prove exact quotient existence with the two-copy miter."""

    start = time.perf_counter()
    if z3 is None:
        return _proof_row("unsupported", "unknown", start, unsupported_reason="z3_not_installed")
    try:
        net = parse_blif(blif_path)
        a_values, a_inputs = _encode_network_with_prefix(net, "a")
        b_values, b_inputs = _encode_network_with_prefix(net, "b")
        a_env = _divisor_env(divisor, a_values)
        b_env = _divisor_env(divisor, b_values)
        a_m = _pack_expr_outputs(divisor, a_env)
        b_m = _pack_expr_outputs(divisor, b_env)
        a_y = _pack_nodes(a_values, output_nodes)
        b_y = _pack_nodes(b_values, output_nodes)
        solver = z3.Solver()
        solver.set("timeout", timeout_ms)
        solver.set("random_seed", 0)
        solver.add(a_m == b_m)
        for node in residual_support:
            solver.add(a_values[node] == b_values[node])
        solver.add(a_y != b_y)
        result = solver.check()
        runtime = time.perf_counter() - start
        if result == z3.unsat:
            return _proof_row("decomposable", "unsat", start, runtime=runtime, counterexample_available=False)
        if result == z3.sat:
            model = solver.model()
            a_assignment = {name: int(bool(model.eval(sym, model_completion=True))) for name, sym in a_inputs.items()}
            b_assignment = {name: int(bool(model.eval(sym, model_completion=True))) for name, sym in b_inputs.items()}
            reproduced = eval_divisor(divisor, a_assignment) == eval_divisor(divisor, b_assignment)
            reproduced = reproduced and tuple(a_assignment.get(z, 0) for z in residual_support) == tuple(b_assignment.get(z, 0) for z in residual_support)
            reproduced = reproduced and eval_outputs(net, output_nodes, a_assignment) != eval_outputs(net, output_nodes, b_assignment)
            return _proof_row(
                "non_decomposable",
                "sat",
                start,
                runtime=runtime,
                counterexample_available=True,
                counterexample={
                    "a": a_assignment,
                    "b": b_assignment,
                    "m_a": eval_divisor(divisor, a_assignment),
                    "m_b": eval_divisor(divisor, b_assignment),
                    "z_a": {node: a_assignment.get(node, 0) for node in residual_support},
                    "z_b": {node: b_assignment.get(node, 0) for node in residual_support},
                    "y_a": eval_outputs(net, output_nodes, a_assignment),
                    "y_b": eval_outputs(net, output_nodes, b_assignment),
                },
                counterexample_reproduced=reproduced,
            )
        return _proof_row("timeout", "unknown", start, runtime=runtime, timeout=True, unsupported_reason="z3_timeout_or_unknown")
    except Exception as exc:
        return _proof_row("unsupported", "error", start, runtime=time.perf_counter() - start, unsupported_reason=f"{type(exc).__name__}:{exc}")


def synthesize_truth_table_quotient(
    *,
    blif_path: Path,
    divisor: SemanticDivisor,
    residual_support: tuple[str, ...],
    output_nodes: tuple[str, ...],
    candidate_id: str,
) -> tuple[QuotientFunction | None, dict[str, str]]:
    net = parse_blif(blif_path)
    if len(net.inputs) > 12:
        return None, {"quotient_status": "unsupported_large_interface", "rejection_reason": "truth_table_input_bound"}
    mapping: dict[tuple[int, ...], tuple[int, ...]] = {}
    conflicts: list[dict[str, object]] = []
    for assignment_index in range(1 << len(net.inputs)):
        assignment = {name: (assignment_index >> idx) & 1 for idx, name in enumerate(net.inputs)}
        key = eval_divisor(divisor, assignment) + tuple(assignment.get(node, 0) for node in residual_support)
        value = eval_outputs(net, output_nodes, assignment)
        if key in mapping and mapping[key] != value:
            conflicts.append({"key": key, "old": mapping[key], "new": value, "assignment": assignment})
            break
        mapping[key] = value
    if conflicts:
        return None, {"quotient_status": "conflicting_quotient_rows", "rejection_reason": "non_decomposable_truth_table"}
    input_order = tuple(_divisor_scalar_names(divisor)) + residual_support
    rows = tuple(sorted((bits_to_string(key), bits_to_string(value)) for key, value in mapping.items()))
    quotient = QuotientFunction(
        quotient_id=f"{candidate_id}__quotient",
        candidate_id=candidate_id,
        input_order=input_order,
        output_order=output_nodes,
        rows=rows,
        completion_policy="zero_completion_for_unreachable_mz",
        node_count=len(output_nodes),
    )
    return quotient, {"quotient_status": "synthesized_truth_table", "rejection_reason": ""}


def emit_quotient_blif(quotient: QuotientFunction, path: Path, *, model: str = "quotient") -> None:
    lines = [f".model {model}", ".inputs " + " ".join(quotient.input_order), ".outputs " + " ".join(quotient.output_order)]
    by_output = {out: [] for out in quotient.output_order}
    for key, value in quotient.rows:
        for idx, bit in enumerate(value):
            if bit == "1":
                by_output[quotient.output_order[idx]].append(key + " 1")
    for output in quotient.output_order:
        lines.append(".names " + " ".join((*quotient.input_order, output)))
        lines.extend(by_output[output])
    lines.append(".end")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def prove_quotient_equivalence_z3(
    *,
    original_blif: Path,
    divisor: SemanticDivisor,
    quotient: QuotientFunction,
    output_nodes: tuple[str, ...],
    timeout_ms: int = 5000,
) -> dict[str, object]:
    start = time.perf_counter()
    if z3 is None:
        return _proof_row("unsupported", "unknown", start, unsupported_reason="z3_not_installed")
    try:
        net = parse_blif(original_blif)
        values, inputs = _encode_network_with_prefix(net, "q")
        env = _divisor_env(divisor, values)
        m = _pack_expr_outputs(divisor, env)
        q_outputs = _quotient_to_z3(quotient, m, values)
        original = _pack_nodes(values, output_nodes)
        solver = z3.Solver()
        solver.set("timeout", timeout_ms)
        solver.set("random_seed", 0)
        solver.add(original != q_outputs)
        result = solver.check()
        runtime = time.perf_counter() - start
        if result == z3.unsat:
            return _proof_row("quotient_equivalent", "unsat", start, runtime=runtime, counterexample_available=False)
        if result == z3.sat:
            model = solver.model()
            assignment = {name: int(bool(model.eval(sym, model_completion=True))) for name, sym in inputs.items()}
            reproduced = tuple(_eval_quotient_python(quotient, eval_divisor(divisor, assignment), tuple(assignment.get(node, 0) for node in _residual_names(quotient)))) != eval_outputs(net, output_nodes, assignment)
            return _proof_row("quotient_disproved", "sat", start, runtime=runtime, counterexample_available=True, counterexample={"assignment": assignment}, counterexample_reproduced=reproduced)
        return _proof_row("timeout", "unknown", start, runtime=runtime, timeout=True, unsupported_reason="z3_timeout_or_unknown")
    except Exception as exc:
        return _proof_row("unsupported", "error", start, runtime=time.perf_counter() - start, unsupported_reason=f"{type(exc).__name__}:{exc}")


def prove_quotient_depends_on_m(quotient: QuotientFunction) -> dict[str, str]:
    m_width = len([name for name in quotient.input_order if name.startswith("m")])
    residual = quotient.input_order[m_width:]
    if m_width == 0:
        return {"non_vacuity_status": "vacuous_no_divisor_output", "quotient_depends_on_m": "false", "witness": "{}", "schema_version": SCHEMA_VERSION}
    table = {key: value for key, value in quotient.rows}
    for residual_bits in _all_bit_tuples(len(residual)):
        seen: dict[str, tuple[int, ...]] = {}
        for m_bits in _all_bit_tuples(m_width):
            out = tuple(int(ch) for ch in table.get(bits_to_string(m_bits + residual_bits), "0" * len(quotient.output_order)))
            seen[bits_to_string(m_bits)] = out
        values = list(seen.items())
        for idx, (left_m, left_out) in enumerate(values):
            for right_m, right_out in values[idx + 1:]:
                if left_out != right_out:
                    return {
                        "non_vacuity_status": "non_vacuous_depends_on_m",
                        "quotient_depends_on_m": "true",
                        "witness": json.dumps({"m0": left_m, "m1": right_m, "z": bits_to_string(residual_bits), "y0": left_out, "y1": right_out}, sort_keys=True),
                        "schema_version": SCHEMA_VERSION,
                    }
    return {"non_vacuity_status": "vacuous_h_ignores_m", "quotient_depends_on_m": "false", "witness": "{}", "schema_version": SCHEMA_VERSION}


def write_refactored_blif(
    *,
    original_blif: Path,
    divisor: SemanticDivisor,
    quotient: QuotientFunction,
    output_path: Path,
    window_outputs: tuple[str, ...],
) -> dict[str, str]:
    net = parse_blif(original_blif)
    divisor_module = divisor.module(f"div_{divisor.divisor_id}")
    div_path = output_path.with_suffix(".divisor.blif")
    quo_path = output_path.with_suffix(".quotient.blif")
    emit_module_blif(divisor_module, div_path)
    emit_quotient_blif(quotient, quo_path, model=f"quo_{divisor.divisor_id}")
    div_net = parse_blif(div_path)
    quo_net = parse_blif(quo_path)
    removed = set(window_outputs)
    nodes = [node for node in net.nodes if node.output not in removed]
    nodes.extend(div_net.nodes)
    nodes.extend(quo_net.nodes)
    _write_network(BlifNetwork(inputs=net.inputs, outputs=net.outputs, nodes=nodes), output_path)
    reparsed = parse_blif(output_path)
    driven = [node.output for node in reparsed.nodes]
    if len(driven) != len(set(driven)):
        return {"graph_rewrite_status": "invalid_multiple_driver", "graph_active": "false", "dangling_fanins": "[]"}
    known = set(reparsed.inputs) | set(driven)
    dangling = sorted({fanin for node in reparsed.nodes for fanin in node.inputs} - known)
    if dangling:
        return {"graph_rewrite_status": "invalid_dangling_fanin", "graph_active": "false", "dangling_fanins": json.dumps(dangling)}
    consumers = [node.output for node in reparsed.nodes if any(fanin in quotient.input_order[: len(_divisor_scalar_names(divisor))] for fanin in node.inputs)]
    active = bool(consumers)
    return {"graph_rewrite_status": "valid", "graph_active": str(active).lower(), "dangling_fanins": "[]", "divisor_consumers": json.dumps(consumers, sort_keys=True)}


def divisor_is_identity(divisor: SemanticDivisor, original_inputs: tuple[str, ...]) -> bool:
    support = tuple(node for bus in divisor.support_buses for node in bus["ordered_member_nodes"])
    m_nodes = tuple(_divisor_scalar_names(divisor))
    return len(m_nodes) >= len(original_inputs) and set(support) == set(original_inputs)


def interface_metrics(*, original_width: int, residual_width: int, semantic_width: int, original_nodes: int, refactored_nodes: int) -> dict[str, str]:
    ref_width = residual_width + semantic_width
    return {
        "original_effective_interface_width": str(original_width),
        "refactored_interface_width": str(ref_width),
        "residual_width": str(residual_width),
        "semantic_width": str(semantic_width),
        "interface_compression": f"{(original_width - ref_width) / max(1, original_width):.6f}",
        "original_node_count": str(original_nodes),
        "refactored_node_count": str(refactored_nodes),
        "area_delta": str(refactored_nodes - original_nodes),
        "schema_version": SCHEMA_VERSION,
    }


def bits_to_string(bits: Iterable[int]) -> str:
    return "".join(str(int(bit)) for bit in bits)


def _encode_network_with_prefix(net: BlifNetwork, prefix: str) -> tuple[dict[str, object], dict[str, object]]:
    if z3 is None:
        raise RuntimeError("z3 is not installed")
    values: dict[str, object] = {}
    inputs: dict[str, object] = {}
    for name in net.inputs:
        sym = z3.Bool(f"{prefix}_{_safe(name)}")
        values[name] = sym
        inputs[name] = sym
    for node in net.nodes:
        missing = [fanin for fanin in node.inputs if fanin not in values]
        if missing:
            raise ValueError(f"node {node.output} has missing fanins: {missing}")
        values[node.output] = encode_cover([values[fanin] for fanin in node.inputs], node.cover)
    return values, inputs


def _divisor_env(divisor: SemanticDivisor, values: dict[str, object]) -> dict[str, object]:
    from blif_z3 import pack_bus

    return {str(bus["name"]): pack_bus(values, tuple(bus["ordered_member_nodes"])) for bus in divisor.support_buses}


def _pack_expr_outputs(divisor: SemanticDivisor, env: dict[str, object]) -> object:
    if z3 is None:
        raise RuntimeError("z3 is not installed")
    bits = []
    for expr in divisor.expressions:
        value = expr_to_z3(expr, env)
        for idx in range(expr.width):
            bits.append(z3.Extract(idx, idx, value))
    if not bits:
        return z3.BitVecVal(0, 1)
    result = bits[0]
    for bit in bits[1:]:
        result = z3.Concat(bit, result)
    return result


def _pack_nodes(values: dict[str, object], nodes: tuple[str, ...]) -> object:
    if z3 is None:
        raise RuntimeError("z3 is not installed")
    bits = [bool_to_bv1(values[node]) for node in nodes]
    result = bits[0]
    for bit in bits[1:]:
        result = z3.Concat(bit, result)
    return result


def _divisor_scalar_names(divisor: SemanticDivisor) -> tuple[str, ...]:
    names: list[str] = []
    for bus in divisor.output_buses:
        names.extend(str(node) for node in bus["ordered_member_nodes"])
    return tuple(names)


def _residual_names(quotient: QuotientFunction) -> tuple[str, ...]:
    return tuple(name for name in quotient.input_order if not name.startswith("m"))


def _quotient_to_z3(quotient: QuotientFunction, m: object, values: dict[str, object]) -> object:
    if z3 is None:
        raise RuntimeError("z3 is not installed")
    m_width = len([name for name in quotient.input_order if name.startswith("m")])
    q_values: dict[str, object] = {}
    for idx in range(m_width):
        q_values[f"m{idx}"] = z3.Extract(idx, idx, m) == z3.BitVecVal(1, 1)
    for name in quotient.input_order[m_width:]:
        q_values[name] = values[name]
    output_bits: list[object] = []
    table = {key: value for key, value in quotient.rows}
    for out_idx, _out in enumerate(quotient.output_order):
        cubes = []
        for key, value in table.items():
            if value[out_idx] != "1":
                continue
            terms = []
            for bit, input_name in zip(key, quotient.input_order):
                terms.append(q_values[input_name] if bit == "1" else z3.Not(q_values[input_name]))
            cubes.append(z3.And(*terms) if terms else z3.BoolVal(True))
        output_bits.append(bool_to_bv1(z3.Or(*cubes) if cubes else z3.BoolVal(False)))
    result = output_bits[0]
    for bit in output_bits[1:]:
        result = z3.Concat(bit, result)
    return result


def _eval_quotient_python(quotient: QuotientFunction, m_bits: tuple[int, ...], z_bits: tuple[int, ...]) -> tuple[int, ...]:
    table = {key: value for key, value in quotient.rows}
    return tuple(int(ch) for ch in table.get(bits_to_string(m_bits + z_bits), "0" * len(quotient.output_order)))


def _all_bit_tuples(width: int) -> Iterable[tuple[int, ...]]:
    for value in range(1 << width):
        yield tuple((value >> idx) & 1 for idx in range(width))


def _proof_row(
    status: str,
    solver_result: str,
    start: float,
    *,
    runtime: float | None = None,
    counterexample_available: bool = False,
    counterexample: dict[str, object] | None = None,
    counterexample_reproduced: bool = False,
    timeout: bool = False,
    unsupported_reason: str = "",
) -> dict[str, object]:
    return {
        "formal_backend": "z3",
        "formal_status": status,
        "solver_result": solver_result,
        "formal_evidence_level": "formal_smt" if status in {"decomposable", "non_decomposable", "quotient_equivalent", "quotient_disproved"} else "unresolved",
        "counterexample_available": str(counterexample_available).lower(),
        "counterexample": counterexample or {},
        "counterexample_reproduced": str(counterexample_reproduced or not counterexample_available).lower(),
        "runtime_seconds": f"{(runtime if runtime is not None else time.perf_counter() - start):.6f}",
        "timeout": str(timeout).lower(),
        "unsupported_reason": unsupported_reason,
        "schema_version": SCHEMA_VERSION,
    }


def _write_network(net: BlifNetwork, path: Path) -> None:
    lines = [".model semantic_refactored", ".inputs " + " ".join(net.inputs), ".outputs " + " ".join(net.outputs)]
    for node in net.nodes:
        lines.append(".names " + " ".join(node.inputs + [node.output]))
        lines.extend(node.cover)
    lines.append(".end")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _hash(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str).encode("utf-8")).hexdigest()[:16]


def _safe(value: str) -> str:
    return "".join(ch if ch.isalnum() else "_" for ch in value) + "_" + hashlib.sha1(value.encode("utf-8")).hexdigest()[:8]
