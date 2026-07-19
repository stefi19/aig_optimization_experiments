"""Provenance-complete, necessity-first target discovery helpers.

This module intentionally separates historical diagnostic row accounting from
target eligibility.  A row can be useful historical evidence without being a
valid graph-rewrite attempt.  The target-selection routines here use only
optimized-netlist structure/function and aligned primary-input behaviour; any
source-side semantic labels remain evaluation-only.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from analyze_blif_matches import BlifNetwork, parse_blif
from formal_locality_barriers import all_assignments, eval_cover_exact, scalar_eval_exact, stable_hash, vector_eval
from semantic_region import file_hash


SCHEMA_VERSION = "necessity_first_targets_v1"


def all_signal_names(net: BlifNetwork) -> tuple[str, ...]:
    return tuple(sorted(set([*net.inputs, *net.outputs, *[node.output for node in net.nodes]])))


def internal_signal_names(net: BlifNetwork) -> tuple[str, ...]:
    excluded = set(net.inputs) | set(net.outputs)
    return tuple(sorted(node.output for node in net.nodes if node.output not in excluded))


def pi_alignment(source: BlifNetwork, optimized: BlifNetwork) -> str:
    if tuple(source.inputs) != tuple(optimized.inputs):
        return "pi_mismatch"
    if tuple(source.outputs) != tuple(optimized.outputs):
        return "po_mismatch"
    return "aligned"


def pi_alignment_hash(source: BlifNetwork, optimized: BlifNetwork) -> str:
    return stable_hash({"inputs": source.inputs, "outputs": source.outputs, "optimized_inputs": optimized.inputs, "optimized_outputs": optimized.outputs})


def structural_fanout(net: BlifNetwork) -> dict[str, set[str]]:
    fanout: dict[str, set[str]] = {name: set() for name in all_signal_names(net)}
    for node in net.nodes:
        for fanin in node.inputs:
            fanout.setdefault(fanin, set()).add(node.output)
    return fanout


def structural_path_to_output(net: BlifNetwork, target: str) -> bool:
    fanout = structural_fanout(net)
    outputs = set(net.outputs)
    seen = set()
    stack = [target]
    while stack:
        node = stack.pop()
        if node in outputs:
            return True
        if node in seen:
            continue
        seen.add(node)
        stack.extend(sorted(fanout.get(node, set()) - seen))
    return False


def eval_with_forced(net: BlifNetwork, assignment: dict[str, int], forced: dict[str, int]) -> dict[str, int]:
    """Evaluate a BLIF network while overriding selected scalar nodes.

    Overrides are applied at primary inputs, internal node outputs, and primary
    output aliases.  This supports forced-value observability checks without
    editing or serialising a temporary circuit.
    """

    values = {name: int(assignment.get(name, 0)) & 1 for name in net.inputs}
    values.update({name: int(value) & 1 for name, value in forced.items() if name in values})
    for node in net.nodes:
        if node.output in forced:
            values[node.output] = int(forced[node.output]) & 1
        else:
            values[node.output] = eval_cover_exact(node.inputs, node.cover, values)
    for output in net.outputs:
        if output in forced:
            values[output] = int(forced[output]) & 1
        else:
            values.setdefault(output, values.get(output, 0))
    return values


def source_optimized_cec(source_path: Path, optimized_path: Path, *, max_inputs: int = 12) -> dict[str, object]:
    source = parse_blif(source_path)
    optimized = parse_blif(optimized_path)
    alignment = pi_alignment(source, optimized)
    if alignment != "aligned":
        return {"status": alignment, "counterexample": None, "backend": "not_run"}
    if len(source.inputs) > max_inputs:
        return {"status": "unsupported_input_width", "counterexample": None, "backend": "not_run"}
    for assignment in all_assignments(tuple(source.inputs)):
        src = vector_eval(source, tuple(source.outputs), assignment)
        opt = vector_eval(optimized, tuple(optimized.outputs), assignment)
        if src != opt:
            return {"status": "not_equivalent", "counterexample": assignment, "backend": "exhaustive"}
    return {"status": "equivalent", "counterexample": None, "backend": "exhaustive"}


def functional_fingerprint(net: BlifNetwork, target: str, *, max_inputs: int = 12) -> str:
    if len(net.inputs) > max_inputs or target not in all_signal_names(net):
        return ""
    bits = []
    for assignment in all_assignments(tuple(net.inputs)):
        bits.append(str(scalar_eval_exact(net, assignment).get(target, 0)))
    return hashlib.sha256("".join(bits).encode("ascii")).hexdigest()[:16]


def nonconstant_witness(net: BlifNetwork, target: str, *, max_inputs: int = 12) -> tuple[str, dict[str, int], dict[str, int]]:
    if target not in all_signal_names(net):
        return "target_missing", {}, {}
    if len(net.inputs) > max_inputs:
        return "unsupported_input_width", {}, {}
    seen: dict[int, dict[str, int]] = {}
    for assignment in all_assignments(tuple(net.inputs)):
        value = scalar_eval_exact(net, assignment).get(target, 0)
        if 1 - value in seen:
            return "nonconstant", seen[1 - value], assignment
        seen.setdefault(value, assignment)
    return "constant", {}, {}


def forced_observability_witness(net: BlifNetwork, target: str, *, max_inputs: int = 12) -> tuple[str, dict[str, int], tuple[str, ...]]:
    if target not in all_signal_names(net):
        return "target_missing", {}, tuple()
    if len(net.inputs) > max_inputs:
        return "unsupported_input_width", {}, tuple()
    affected: set[str] = set()
    for assignment in all_assignments(tuple(net.inputs)):
        zero = eval_with_forced(net, assignment, {target: 0})
        one = eval_with_forced(net, assignment, {target: 1})
        diff = tuple(output for output in net.outputs if zero.get(output, 0) != one.get(output, 0))
        if diff:
            affected.update(diff)
            return "forced_observable", assignment, tuple(sorted(affected))
    return "forced_unobservable", {}, tuple()


def reachable_necessity_witness(net: BlifNetwork, target: str, context: Iterable[str] = (), *, max_inputs: int = 12) -> tuple[str, dict[str, int], dict[str, int], tuple[str, ...]]:
    if target not in all_signal_names(net):
        return "target_missing", {}, {}, tuple()
    if len(net.inputs) > max_inputs:
        return "unsupported_input_width", {}, {}, tuple()
    context = tuple(context)
    buckets: dict[tuple[int, ...], list[tuple[dict[str, int], int, tuple[int, ...]]]] = {}
    for assignment in all_assignments(tuple(net.inputs)):
        values = scalar_eval_exact(net, assignment)
        key = tuple(values.get(name, 0) for name in context)
        target_value = values.get(target, 0)
        outputs = tuple(values.get(output, 0) for output in net.outputs)
        for previous_assignment, previous_target, previous_outputs in buckets.get(key, []):
            if previous_target != target_value and previous_outputs != outputs:
                affected = tuple(output for output, a, b in zip(net.outputs, previous_outputs, outputs) if a != b)
                return "reachable_necessary", previous_assignment, assignment, affected
        buckets.setdefault(key, []).append((assignment, target_value, outputs))
    return "not_reachable_necessary", {}, {}, tuple()


@dataclass(frozen=True)
class TargetProvenanceRecord:
    stable_target_id: str
    benchmark_id: str
    design_family: str
    dataset_class: str
    split: str
    source_origin: str
    source_license: str
    source_url: str
    source_revision: str
    source_file: str
    source_artifact_hash: str
    lowered_blif_hash: str
    optimized_artifact: str
    optimized_artifact_hash: str
    optimized_target_node: str
    target_node_functional_fingerprint: str
    synthesis_flow_id: str
    command_sequence: str
    abc_revision: str
    yosys_revision: str
    aligned_primary_inputs: tuple[str, ...]
    aligned_primary_outputs: tuple[str, ...]
    pi_alignment_hash: str
    source_optimized_cec_status: str
    target_selection_method: str
    target_selection_config_hash: str
    source_blind: bool
    artifact_regeneration_command: str
    artifact_availability: str
    eligibility_status: str
    ineligibility_reason: str
    schema_version: str = SCHEMA_VERSION

    def row(self) -> dict[str, str]:
        return {
            "schema_version": self.schema_version,
            "stable_target_id": self.stable_target_id,
            "benchmark_id": self.benchmark_id,
            "design_family": self.design_family,
            "dataset_class": self.dataset_class,
            "split": self.split,
            "source_origin": self.source_origin,
            "source_license": self.source_license,
            "source_url": self.source_url,
            "source_revision": self.source_revision,
            "source_file": self.source_file,
            "source_artifact_hash": self.source_artifact_hash,
            "lowered_blif_hash": self.lowered_blif_hash,
            "optimized_artifact": self.optimized_artifact,
            "optimized_artifact_hash": self.optimized_artifact_hash,
            "optimized_target_node": self.optimized_target_node,
            "target_node_functional_fingerprint": self.target_node_functional_fingerprint,
            "synthesis_flow_id": self.synthesis_flow_id,
            "command_sequence": self.command_sequence,
            "abc_revision": self.abc_revision,
            "yosys_revision": self.yosys_revision,
            "aligned_primary_inputs": json.dumps(self.aligned_primary_inputs),
            "aligned_primary_outputs": json.dumps(self.aligned_primary_outputs),
            "pi_alignment_hash": self.pi_alignment_hash,
            "source_optimized_cec_status": self.source_optimized_cec_status,
            "target_selection_method": self.target_selection_method,
            "target_selection_config_hash": self.target_selection_config_hash,
            "source_blind": str(self.source_blind).lower(),
            "artifact_regeneration_command": self.artifact_regeneration_command,
            "artifact_availability": self.artifact_availability,
            "eligibility_status": self.eligibility_status,
            "ineligibility_reason": self.ineligibility_reason,
        }


def stable_target_id(benchmark: str, flow: str, source_path: Path, optimized_path: Path, node: str, fingerprint: str) -> str:
    return stable_hash(
        {
            "benchmark": benchmark,
            "flow": flow,
            "source_hash": file_hash(source_path) if source_path.exists() else "",
            "optimized_hash": file_hash(optimized_path) if optimized_path.exists() else "",
            "node": node,
            "fingerprint": fingerprint,
        }
    )
