"""Active source-side counterpart construction utilities.

This module is the source-side dual of the semantic functional-refactoring
experiment.  It distinguishes three facts that previous additive
materialization deliberately kept separate:

* a constructed source signal is equivalent to an optimized implementation node;
* the source graph is rewritten so preserved consumers depend on that signal;
* the adapted source still passes global equivalence checks.
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

from analyze_blif_matches import BlifNetwork, BlifNode, parse_blif
from semantic_functional_refactoring import (
    QuotientFunction,
    SemanticDivisor,
    eval_divisor,
    eval_outputs,
    scalar_eval,
)
from semantic_region_replacement import emit_module_blif


SCHEMA_VERSION = "active_source_counterpart_refactoring_v1"


@dataclass(frozen=True)
class ActiveSourceCounterpartCandidate:
    candidate_id: str
    benchmark: str
    optimization_flow: str
    split: str
    optimized_target_nodes: tuple[str, ...]
    target_selection_reason: str
    optimized_cut_id: str
    implementation_cut_leaves: tuple[str, ...]
    mapped_source_cut_leaves: tuple[str, ...]
    leaf_polarities: tuple[str, ...]
    target_function_id: str
    generated_source_counterpart_nodes: tuple[str, ...]
    counterpart_backend: str
    selected_source_window: str
    source_window_inputs: tuple[str, ...]
    source_window_outputs: tuple[str, ...]
    residual_interface: tuple[str, ...]
    quotient_id: str
    search_provenance: str
    source_blind: bool = True
    schema_version: str = SCHEMA_VERSION

    @property
    def fingerprint(self) -> str:
        return stable_hash(asdict(self))


def stable_hash(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str, separators=(",", ":")).encode("utf-8")).hexdigest()[:16]


def candidate_to_row(candidate: ActiveSourceCounterpartCandidate) -> dict[str, str]:
    return {
        "candidate_id": candidate.candidate_id,
        "benchmark": candidate.benchmark,
        "optimization_flow": candidate.optimization_flow,
        "split": candidate.split,
        "optimized_target_nodes": json.dumps(candidate.optimized_target_nodes),
        "target_selection_reason": candidate.target_selection_reason,
        "optimized_cut_id": candidate.optimized_cut_id,
        "implementation_cut_leaves": json.dumps(candidate.implementation_cut_leaves),
        "mapped_source_cut_leaves": json.dumps(candidate.mapped_source_cut_leaves),
        "leaf_polarities": json.dumps(candidate.leaf_polarities),
        "target_function_id": candidate.target_function_id,
        "generated_source_counterpart_nodes": json.dumps(candidate.generated_source_counterpart_nodes),
        "counterpart_backend": candidate.counterpart_backend,
        "selected_source_window": candidate.selected_source_window,
        "source_window_inputs": json.dumps(candidate.source_window_inputs),
        "source_window_outputs": json.dumps(candidate.source_window_outputs),
        "residual_interface": json.dumps(candidate.residual_interface),
        "quotient_id": candidate.quotient_id,
        "search_provenance": candidate.search_provenance,
        "source_blind": str(candidate.source_blind).lower(),
        "fingerprint": candidate.fingerprint,
        "schema_version": candidate.schema_version,
    }


def write_network(net: BlifNetwork, path: Path, *, model: str = "network") -> None:
    lines = [f".model {model}", ".inputs " + " ".join(net.inputs), ".outputs " + " ".join(net.outputs)]
    for node in net.nodes:
        lines.append(".names " + " ".join([*node.inputs, node.output]))
        lines.extend(node.cover)
    lines.append(".end")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def construct_impl_with_target(source_blif: Path, divisor: SemanticDivisor, impl_path: Path) -> dict[str, str]:
    """Create an implementation-equivalent circuit with exposed target nodes.

    The implementation primary outputs are left unchanged.  The target nodes are
    internal nodes implementing the divisor expression over the same primary
    inputs, which gives the source-side construction a concrete optimized
    target to prove against in controlled experiments.
    """

    source = parse_blif(source_blif)
    module_path = impl_path.with_suffix(".target_module.blif")
    emit_module_blif(divisor.module(f"impl_target_{divisor.divisor_id}"), module_path)
    module = parse_blif(module_path)
    existing = set(source.inputs) | set(source.outputs) | {node.output for node in source.nodes}
    collisions = sorted(existing & {node.output for node in module.nodes})
    if collisions:
        return {"status": "failed", "impl_path": "", "target_nodes": "[]", "failure_reason": "target_name_collision:" + ";".join(collisions)}
    write_network(BlifNetwork(inputs=source.inputs, outputs=source.outputs, nodes=[*source.nodes, *module.nodes]), impl_path, model=f"impl_{divisor.divisor_id}")
    return {
        "status": "generated",
        "impl_path": display_path(impl_path),
        "target_nodes": json.dumps(divisor_scalar_names(divisor)),
        "failure_reason": "",
    }


def prove_cross_node_equivalence(
    *,
    source_blif: Path,
    impl_blif: Path,
    source_nodes: tuple[str, ...],
    impl_nodes: tuple[str, ...],
    polarity: tuple[str, ...] | None = None,
    exact_input_limit: int = 12,
) -> dict[str, str]:
    start = time.perf_counter()
    polarity = polarity or tuple("same" for _ in source_nodes)
    source = parse_blif(source_blif)
    impl = parse_blif(impl_blif)
    reason = _node_proof_precheck(source, impl, source_nodes, impl_nodes, polarity, exact_input_limit)
    if reason:
        return _proof_row("unsupported" if "too_large" in reason else "alignment_failure", "not_run", start, "exhaustive_node_miter", reason)
    for assignment in _all_assignments(tuple(source.inputs)):
        s_values = scalar_eval(source, assignment)
        i_values = scalar_eval(impl, assignment)
        s_bits = tuple(s_values[node] for node in source_nodes)
        i_bits = tuple(i_values[node] if pol == "same" else 1 - i_values[node] for node, pol in zip(impl_nodes, polarity))
        if s_bits != i_bits:
            return _proof_row(
                "disproven",
                "sat_exhaustive",
                start,
                "exhaustive_node_miter",
                "counterpart_mismatch",
                counterexample={"assignment": assignment, "source": s_bits, "implementation": i_bits},
                counterexample_reproduced=True,
            )
    return _proof_row("proven_counterpart_equivalent", "unsat_exhaustive", start, "exhaustive_node_miter", "")


def prove_window_rewrite_equivalence(
    *,
    original_blif: Path,
    refactored_blif: Path,
    exact_input_limit: int = 12,
) -> dict[str, str]:
    start = time.perf_counter()
    original = parse_blif(original_blif)
    refactored = parse_blif(refactored_blif)
    if original.inputs != refactored.inputs or original.outputs != refactored.outputs:
        return _proof_row("alignment_failure", "not_run", start, "exhaustive_output_miter", "primary_interface_mismatch")
    if len(original.inputs) > exact_input_limit:
        return _proof_row("unsupported", "not_run", start, "exhaustive_output_miter", "support_too_large_for_exhaustive")
    for assignment in _all_assignments(tuple(original.inputs)):
        if eval_outputs(original, tuple(original.outputs), assignment) != eval_outputs(refactored, tuple(refactored.outputs), assignment):
            return _proof_row("disproven", "sat_exhaustive", start, "exhaustive_output_miter", "output_mismatch", counterexample={"assignment": assignment}, counterexample_reproduced=True)
    return _proof_row("proven_window_rewrite_equivalent", "unsat_exhaustive", start, "exhaustive_output_miter", "")


def validate_active_rewrite(
    *,
    refactored_blif: Path,
    counterpart_nodes: tuple[str, ...],
    window_outputs: tuple[str, ...],
) -> dict[str, str]:
    if not refactored_blif.exists():
        return _graph_row("invalid_missing_refactored_blif", False, False, False, "missing_refactored_blif")
    net = parse_blif(refactored_blif)
    driven = [node.output for node in net.nodes]
    if len(driven) != len(set(driven)):
        return _graph_row("invalid_multiple_driver", False, False, False, "multiple_driver")
    known = set(net.inputs) | set(driven)
    dangling = sorted({fanin for node in net.nodes for fanin in node.inputs} - known)
    if dangling:
        return _graph_row("invalid_dangling_net", False, False, False, "dangling_net:" + ";".join(dangling))
    if _has_cycle(net):
        return _graph_row("invalid_cycle", False, False, False, "cycle")
    consumers = sorted(node.output for node in net.nodes if any(fanin in counterpart_nodes for fanin in node.inputs))
    output_influence = bool(consumers) and any(out in set(net.outputs) for out in window_outputs)
    return _graph_row("valid", bool(consumers), output_influence, True, "", consumers)


def quotient_uses_counterpart(quotient: QuotientFunction) -> bool:
    width = len([name for name in quotient.input_order if name.startswith("m")])
    if width == 0:
        return False
    by_z: dict[str, set[str]] = {}
    for key, value in quotient.rows:
        by_z.setdefault(key[width:], set()).add(value)
    return any(len(values) > 1 for values in by_z.values())


def gf2_affine_model(
    *,
    blif_path: Path,
    output_node: str,
    input_order: tuple[str, ...] | None = None,
    exact_input_limit: int = 12,
) -> dict[str, str]:
    net = parse_blif(blif_path)
    input_order = input_order or tuple(net.inputs)
    if len(input_order) > exact_input_limit:
        return {"status": "unsupported", "is_affine": "false", "constant": "", "coefficients": "{}", "rank": "", "backend": "gf2_linear_special_case", "rejection_reason": "support_too_large", "schema_version": SCHEMA_VERSION}
    zero = {name: 0 for name in net.inputs}
    values0 = scalar_eval(net, zero)
    if output_node not in values0:
        return {"status": "unsupported", "is_affine": "false", "constant": "", "coefficients": "{}", "rank": "", "backend": "gf2_linear_special_case", "rejection_reason": "missing_output_node", "schema_version": SCHEMA_VERSION}
    constant = values0[output_node]
    coeffs: dict[str, int] = {}
    for name in input_order:
        assignment = {inp: 0 for inp in net.inputs}
        assignment[name] = 1
        coeffs[name] = scalar_eval(net, assignment)[output_node] ^ constant
    for assignment in _all_assignments(tuple(net.inputs)):
        predicted = constant
        for name, coef in coeffs.items():
            predicted ^= coef & assignment.get(name, 0)
        if predicted != scalar_eval(net, assignment).get(output_node, 0):
            return {"status": "rejected_nonlinear", "is_affine": "false", "constant": str(constant), "coefficients": json.dumps(coeffs, sort_keys=True), "rank": str(sum(coeffs.values())), "backend": "gf2_linear_special_case", "rejection_reason": "nonlinear_counterexample", "schema_version": SCHEMA_VERSION}
    return {"status": "exact_affine_solution", "is_affine": "true", "constant": str(constant), "coefficients": json.dumps(coeffs, sort_keys=True), "rank": str(sum(coeffs.values())), "backend": "gf2_linear_special_case", "rejection_reason": "", "schema_version": SCHEMA_VERSION}


def divisor_scalar_names(divisor: SemanticDivisor) -> tuple[str, ...]:
    names: list[str] = []
    for bus in divisor.output_buses:
        names.extend(str(node) for node in bus["ordered_member_nodes"])
    return tuple(names)


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(Path.cwd()))
    except ValueError:
        return str(path)


def _node_proof_precheck(source: BlifNetwork, impl: BlifNetwork, source_nodes: tuple[str, ...], impl_nodes: tuple[str, ...], polarity: tuple[str, ...], exact_input_limit: int) -> str:
    if source.inputs != impl.inputs:
        return "pi_mismatch"
    if len(source.inputs) > exact_input_limit:
        return "support_too_large_for_exhaustive"
    if len(source_nodes) != len(impl_nodes) or len(source_nodes) != len(polarity):
        return "node_width_mismatch"
    source_known = set(source.inputs) | set(source.outputs) | {node.output for node in source.nodes}
    impl_known = set(impl.inputs) | set(impl.outputs) | {node.output for node in impl.nodes}
    missing_source = sorted(set(source_nodes) - source_known)
    missing_impl = sorted(set(impl_nodes) - impl_known)
    if missing_source:
        return "missing_source_counterpart:" + ";".join(missing_source)
    if missing_impl:
        return "missing_implementation_target:" + ";".join(missing_impl)
    if any(pol not in {"same", "inverted"} for pol in polarity):
        return "unsupported_polarity"
    return ""


def _all_assignments(inputs: tuple[str, ...]) -> Iterable[dict[str, int]]:
    for value in range(1 << len(inputs)):
        yield {name: (value >> idx) & 1 for idx, name in enumerate(inputs)}


def _has_cycle(net: BlifNetwork) -> bool:
    fanins = {node.output: tuple(node.inputs) for node in net.nodes}
    visiting: set[str] = set()
    visited: set[str] = set()

    def dfs(node: str) -> bool:
        if node in visited or node in net.inputs:
            return False
        if node in visiting:
            return True
        visiting.add(node)
        for fanin in fanins.get(node, ()):
            if dfs(fanin):
                return True
        visiting.remove(node)
        visited.add(node)
        return False

    return any(dfs(node.output) for node in net.nodes)


def _proof_row(
    status: str,
    solver_result: str,
    start: float,
    backend: str,
    reason: str,
    *,
    counterexample: dict[str, object] | None = None,
    counterexample_reproduced: bool = False,
) -> dict[str, str]:
    return {
        "formal_status": status,
        "solver_result": solver_result,
        "formal_backend": backend,
        "formal_evidence_level": "formal_exhaustive" if status.startswith("proven") or status == "disproven" else "unresolved",
        "counterexample_available": str(counterexample is not None).lower(),
        "counterexample": json.dumps(counterexample or {}, sort_keys=True),
        "counterexample_reproduced": str(counterexample_reproduced or counterexample is None).lower(),
        "runtime_seconds": f"{time.perf_counter() - start:.6f}",
        "timeout": "false",
        "unsupported_reason": reason,
        "schema_version": SCHEMA_VERSION,
    }


def _graph_row(status: str, graph_active: bool, output_influence: bool, cycle_free: bool, reason: str, consumers: list[str] | None = None) -> dict[str, str]:
    return {
        "graph_rewrite_status": status,
        "graph_active": str(graph_active).lower(),
        "functional_influence": str(output_influence).lower(),
        "cycle_free": str(cycle_free).lower(),
        "counterpart_consumers": json.dumps(consumers or [], sort_keys=True),
        "bypass_status": "no_bypass_detected" if graph_active and output_influence else "inactive_or_bypassed",
        "failure_reason": reason,
        "schema_version": SCHEMA_VERSION,
    }
