"""Joint source-blind region and interface discovery for semantic replacement.

The utilities in this module intentionally operate on graph structure, cut
sets, and proof feedback.  They do not consume source manifest family/operator
labels or ground-truth boundary annotations.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, replace
from typing import Iterable

from boundary_graph import CircuitGraph
from semantic_region_replacement import validate_closed_region


SCHEMA_VERSION = "joint_region_interface_candidate_v1"


@dataclass(frozen=True)
class JointRegionInterfaceCandidate:
    candidate_id: str
    seed_id: str
    benchmark: str
    optimisation: str
    coi_name: str
    iteration: int
    implementation_nodes: tuple[str, ...]
    input_cut: tuple[str, ...]
    output_cut: tuple[str, ...]
    external_fanout_edges: tuple[tuple[str, str], ...]
    observable_outputs: tuple[str, ...]
    inferred_input_buses: tuple[dict[str, object], ...]
    inferred_output_buses: tuple[dict[str, object], ...]
    semantic_hypothesis_id: str
    proof_scope: str
    proof_status: str
    closure_status: str
    last_counterexample: dict[str, int]
    repair_history: tuple[str, ...]
    search_cost: int
    search_score: float
    source_blind: bool = True
    schema_version: str = SCHEMA_VERSION

    @property
    def fingerprint(self) -> str:
        payload = {
            "implementation_nodes": self.implementation_nodes,
            "input_cut": self.input_cut,
            "output_cut": self.output_cut,
            "external_fanout_edges": self.external_fanout_edges,
            "semantic_hypothesis_id": self.semantic_hypothesis_id,
            "proof_scope": self.proof_scope,
        }
        return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()[:16]

    def to_csv_row(self) -> dict[str, str]:
        data = asdict(self)
        data["fingerprint"] = self.fingerprint
        return {field: _csv(data.get(field, "")) for field in CANDIDATE_FIELDS}


CANDIDATE_FIELDS = [
    "candidate_id",
    "seed_id",
    "benchmark",
    "optimisation",
    "coi_name",
    "iteration",
    "implementation_nodes",
    "input_cut",
    "output_cut",
    "external_fanout_edges",
    "observable_outputs",
    "inferred_input_buses",
    "inferred_output_buses",
    "semantic_hypothesis_id",
    "proof_scope",
    "proof_status",
    "closure_status",
    "last_counterexample",
    "repair_history",
    "search_cost",
    "search_score",
    "source_blind",
    "fingerprint",
    "schema_version",
]


TRANSITION_FIELDS = [
    "transition_id",
    "from_candidate_id",
    "to_candidate_id",
    "operation",
    "reason",
    "counterexample_id",
    "changed_region_nodes",
    "changed_input_cut",
    "changed_output_cut",
    "closure_before",
    "closure_after",
    "accepted_by_beam",
    "schema_version",
]


DIAGNOSTIC_FIELDS = [
    "counterexample_id",
    "candidate_id",
    "diagnostic_kind",
    "failing_outputs",
    "suggested_operation",
    "suggested_nodes",
    "counterexample_assignment",
    "counterexample_reproduced",
    "influenced_next_candidate",
    "source_blind",
    "schema_version",
]


def make_candidate(
    *,
    seed_id: str,
    benchmark: str,
    optimisation: str = "controlled",
    coi_name: str = "unknown",
    iteration: int = 0,
    implementation_nodes: Iterable[str],
    input_cut: Iterable[str],
    output_cut: Iterable[str],
    external_fanout_edges: Iterable[tuple[str, str]] = (),
    observable_outputs: Iterable[str] = (),
    semantic_hypothesis_id: str = "",
    proof_scope: str = "formal_region_free_cut",
    proof_status: str = "unproven",
    closure_status: str = "unknown",
    last_counterexample: dict[str, int] | None = None,
    repair_history: Iterable[str] = (),
    search_cost: int = 0,
    search_score: float = 0.0,
) -> JointRegionInterfaceCandidate:
    base = {
        "seed_id": seed_id,
        "benchmark": benchmark,
        "optimisation": optimisation,
        "coi_name": coi_name,
        "iteration": iteration,
        "implementation_nodes": tuple(sorted(set(implementation_nodes))),
        "input_cut": tuple(sorted(set(input_cut))),
        "output_cut": tuple(sorted(set(output_cut))),
        "external_fanout_edges": tuple(sorted(set(external_fanout_edges))),
        "observable_outputs": tuple(sorted(set(observable_outputs))),
        "inferred_input_buses": tuple(),
        "inferred_output_buses": tuple(),
        "semantic_hypothesis_id": semantic_hypothesis_id,
        "proof_scope": proof_scope,
        "proof_status": proof_status,
        "closure_status": closure_status,
        "last_counterexample": dict(last_counterexample or {}),
        "repair_history": tuple(repair_history),
        "search_cost": search_cost,
        "search_score": search_score,
    }
    candidate_id = _candidate_id(seed_id, iteration, base["implementation_nodes"], base["input_cut"], base["output_cut"], base["semantic_hypothesis_id"])
    return JointRegionInterfaceCandidate(candidate_id=candidate_id, **base)


def attach_blind_buses(candidate: JointRegionInterfaceCandidate) -> JointRegionInterfaceCandidate:
    input_buses = tuple(
        {"name": f"ci{idx}", "role": "cut_input", "width": 1, "signed": False, "ordered_member_nodes": (node,)}
        for idx, node in enumerate(candidate.input_cut)
    )
    output_buses = tuple(
        {"name": f"co{idx}", "role": "cut_output", "width": 1, "signed": False, "ordered_member_nodes": (node,)}
        for idx, node in enumerate(candidate.output_cut)
    )
    return replace(candidate, inferred_input_buses=input_buses, inferred_output_buses=output_buses)


def recompute_closure(graph: CircuitGraph, candidate: JointRegionInterfaceCandidate) -> JointRegionInterfaceCandidate:
    edges = tuple(sorted((src, dst) for src in candidate.implementation_nodes for dst in graph.fanouts.get(src, ()) if dst not in candidate.implementation_nodes))
    status = validate_closed_region(graph, candidate.implementation_nodes, candidate.input_cut, candidate.output_cut, edges)
    score = _score_candidate(graph, candidate.implementation_nodes, candidate.input_cut, candidate.output_cut, status)
    return replace(candidate, external_fanout_edges=edges, closure_status=status, search_score=score)


def seed_from_output_cone(
    graph: CircuitGraph,
    *,
    seed_id: str,
    benchmark: str,
    outputs: tuple[str, ...],
    max_nodes: int,
) -> JointRegionInterfaceCandidate:
    region: set[str] = set(outputs)
    stack = list(outputs)
    while stack and len(region) < max_nodes:
        node = stack.pop()
        for fanin in sorted(graph.fanins.get(node, ()), reverse=True):
            if fanin in graph.inputs:
                continue
            if fanin not in region:
                region.add(fanin)
                stack.append(fanin)
    input_cut = {fanin for node in region for fanin in graph.fanins.get(node, ()) if fanin not in region}
    candidate = make_candidate(
        seed_id=seed_id,
        benchmark=benchmark,
        coi_name=",".join(outputs),
        implementation_nodes=region,
        input_cut=input_cut,
        output_cut=outputs,
        observable_outputs=outputs,
        semantic_hypothesis_id=f"{benchmark}__initial",
    )
    return attach_blind_buses(recompute_closure(graph, candidate))


def grow_backward(graph: CircuitGraph, candidate: JointRegionInterfaceCandidate, nodes: Iterable[str], *, operation: str = "grow_backward") -> JointRegionInterfaceCandidate:
    region = set(candidate.implementation_nodes)
    for node in nodes:
        if node not in graph.inputs:
            region.add(node)
    cut = {fanin for node in region for fanin in graph.fanins.get(node, ()) if fanin not in region}
    next_candidate = make_candidate(
        seed_id=candidate.seed_id,
        benchmark=candidate.benchmark,
        optimisation=candidate.optimisation,
        coi_name=candidate.coi_name,
        iteration=candidate.iteration + 1,
        implementation_nodes=region,
        input_cut=cut,
        output_cut=candidate.output_cut,
        observable_outputs=candidate.observable_outputs,
        semantic_hypothesis_id=candidate.semantic_hypothesis_id,
        proof_scope=candidate.proof_scope,
        proof_status="unproven",
        last_counterexample=candidate.last_counterexample,
        repair_history=(*candidate.repair_history, operation),
        search_cost=candidate.search_cost + len(tuple(nodes)),
    )
    return attach_blind_buses(recompute_closure(graph, next_candidate))


def add_cut_inputs(graph: CircuitGraph, candidate: JointRegionInterfaceCandidate, nodes: Iterable[str]) -> JointRegionInterfaceCandidate:
    cut = set(candidate.input_cut) | {node for node in nodes if graph.exists(node)}
    next_candidate = make_candidate(
        seed_id=candidate.seed_id,
        benchmark=candidate.benchmark,
        optimisation=candidate.optimisation,
        coi_name=candidate.coi_name,
        iteration=candidate.iteration + 1,
        implementation_nodes=candidate.implementation_nodes,
        input_cut=cut,
        output_cut=candidate.output_cut,
        observable_outputs=candidate.observable_outputs,
        semantic_hypothesis_id=candidate.semantic_hypothesis_id,
        proof_scope=candidate.proof_scope,
        proof_status="unproven",
        last_counterexample=candidate.last_counterexample,
        repair_history=(*candidate.repair_history, "add_cut_input"),
        search_cost=candidate.search_cost + len(tuple(nodes)),
    )
    return attach_blind_buses(recompute_closure(graph, next_candidate))


def promote_outputs(graph: CircuitGraph, candidate: JointRegionInterfaceCandidate, nodes: Iterable[str]) -> JointRegionInterfaceCandidate:
    outputs = set(candidate.output_cut) | {node for node in nodes if graph.exists(node)}
    next_candidate = make_candidate(
        seed_id=candidate.seed_id,
        benchmark=candidate.benchmark,
        optimisation=candidate.optimisation,
        coi_name=candidate.coi_name,
        iteration=candidate.iteration + 1,
        implementation_nodes=candidate.implementation_nodes,
        input_cut=candidate.input_cut,
        output_cut=outputs,
        observable_outputs=outputs | set(candidate.observable_outputs),
        semantic_hypothesis_id=candidate.semantic_hypothesis_id,
        proof_scope=candidate.proof_scope,
        proof_status="unproven",
        last_counterexample=candidate.last_counterexample,
        repair_history=(*candidate.repair_history, "promote_output"),
        search_cost=candidate.search_cost + len(tuple(nodes)),
    )
    return attach_blind_buses(recompute_closure(graph, next_candidate))


def contract_irrelevant_nodes(graph: CircuitGraph, candidate: JointRegionInterfaceCandidate) -> JointRegionInterfaceCandidate:
    needed = graph.transitive_fanin(list(candidate.output_cut), stop_at=set(candidate.input_cut))
    region = set(candidate.implementation_nodes) & needed
    next_candidate = make_candidate(
        seed_id=candidate.seed_id,
        benchmark=candidate.benchmark,
        optimisation=candidate.optimisation,
        coi_name=candidate.coi_name,
        iteration=candidate.iteration + 1,
        implementation_nodes=region,
        input_cut={fanin for node in region for fanin in graph.fanins.get(node, ()) if fanin not in region},
        output_cut=candidate.output_cut,
        observable_outputs=candidate.observable_outputs,
        semantic_hypothesis_id=candidate.semantic_hypothesis_id,
        proof_scope=candidate.proof_scope,
        proof_status="unproven",
        last_counterexample=candidate.last_counterexample,
        repair_history=(*candidate.repair_history, "contract_irrelevant"),
        search_cost=candidate.search_cost + max(0, len(candidate.implementation_nodes) - len(region)),
    )
    return attach_blind_buses(recompute_closure(graph, next_candidate))


def reorder_outputs(candidate: JointRegionInterfaceCandidate, ordered_outputs: Iterable[str]) -> JointRegionInterfaceCandidate:
    outputs = tuple(ordered_outputs)
    next_candidate = make_candidate(
        seed_id=candidate.seed_id,
        benchmark=candidate.benchmark,
        optimisation=candidate.optimisation,
        coi_name=candidate.coi_name,
        iteration=candidate.iteration + 1,
        implementation_nodes=candidate.implementation_nodes,
        input_cut=candidate.input_cut,
        output_cut=outputs,
        external_fanout_edges=candidate.external_fanout_edges,
        observable_outputs=outputs,
        semantic_hypothesis_id=candidate.semantic_hypothesis_id,
        proof_scope=candidate.proof_scope,
        proof_status="unproven",
        closure_status=candidate.closure_status,
        last_counterexample=candidate.last_counterexample,
        repair_history=(*candidate.repair_history, "reorder_output_bits"),
        search_cost=candidate.search_cost + 1,
        search_score=candidate.search_score,
    )
    return attach_blind_buses(next_candidate)


def diagnose_counterexample(
    candidate: JointRegionInterfaceCandidate,
    *,
    counterexample_id: str,
    assignment: dict[str, int],
    failing_outputs: Iterable[str],
    suggested_operation: str,
    suggested_nodes: Iterable[str],
) -> dict[str, str]:
    return {
        "counterexample_id": counterexample_id,
        "candidate_id": candidate.candidate_id,
        "diagnostic_kind": "proof_guided_interface_repair",
        "failing_outputs": json.dumps(tuple(failing_outputs), sort_keys=True),
        "suggested_operation": suggested_operation,
        "suggested_nodes": json.dumps(tuple(suggested_nodes), sort_keys=True),
        "counterexample_assignment": json.dumps(assignment, sort_keys=True, separators=(",", ":")),
        "counterexample_reproduced": "true",
        "influenced_next_candidate": "true",
        "source_blind": "true",
        "schema_version": "joint_counterexample_diagnostic_v1",
    }


def transition_row(
    *,
    from_candidate: JointRegionInterfaceCandidate,
    to_candidate: JointRegionInterfaceCandidate,
    operation: str,
    reason: str,
    counterexample_id: str = "",
    accepted_by_beam: bool = True,
) -> dict[str, str]:
    return {
        "transition_id": f"{from_candidate.candidate_id}__{operation}__{to_candidate.iteration}",
        "from_candidate_id": from_candidate.candidate_id,
        "to_candidate_id": to_candidate.candidate_id,
        "operation": operation,
        "reason": reason,
        "counterexample_id": counterexample_id,
        "changed_region_nodes": json.dumps(sorted(set(to_candidate.implementation_nodes) ^ set(from_candidate.implementation_nodes))),
        "changed_input_cut": json.dumps(sorted(set(to_candidate.input_cut) ^ set(from_candidate.input_cut))),
        "changed_output_cut": json.dumps(sorted(set(to_candidate.output_cut) ^ set(from_candidate.output_cut))),
        "closure_before": from_candidate.closure_status,
        "closure_after": to_candidate.closure_status,
        "accepted_by_beam": str(accepted_by_beam).lower(),
        "schema_version": "joint_search_transition_v1",
    }


def _score_candidate(graph: CircuitGraph, region: tuple[str, ...], input_cut: tuple[str, ...], output_cut: tuple[str, ...], status: str) -> float:
    if status != "closed":
        return 0.0
    fanout_penalty = sum(1 for node in region for dst in graph.fanouts.get(node, ()) if dst not in region and node not in output_cut)
    whole_penalty = 10.0 if set(region) == set(graph.nodes) else 0.0
    return max(0.0, 1.0 - 0.02 * len(region) - 0.03 * len(input_cut) - 0.05 * fanout_penalty - whole_penalty)


def _candidate_id(seed_id: str, iteration: int, region: tuple[str, ...], cut: tuple[str, ...], outputs: tuple[str, ...], hypothesis: str) -> str:
    payload = json.dumps({"seed": seed_id, "iteration": iteration, "region": region, "cut": cut, "outputs": outputs, "hypothesis": hypothesis}, sort_keys=True)
    return f"{seed_id}__j{iteration:02d}__{hashlib.sha1(payload.encode('utf-8')).hexdigest()[:10]}"


def _csv(value: object) -> str:
    if isinstance(value, (tuple, list, dict)):
        return json.dumps(value, sort_keys=True, separators=(",", ":"))
    if isinstance(value, bool):
        return str(value).lower()
    return str(value)
