"""Formal locality-barrier certificates for cross-netlist correspondence.

The core question is compact local functional sufficiency.  Given aligned
primary inputs, an optimized target is always determined by the full PI vector
for deterministic combinational circuits.  The routines here prove whether a
declared source-signal universe contains a smaller interface, and record the
counterexample-derived lower-bound evidence when it does not.
"""

from __future__ import annotations

import hashlib
import itertools
import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

try:  # pragma: no cover - import status is checked in CI smoke tests
    import z3
except Exception:  # pragma: no cover
    z3 = None  # type: ignore[assignment]

from analyze_blif_matches import BlifNetwork, eval_cover, parse_blif
from blif_z3 import encode_cover
from semantic_region import file_hash


SCHEMA_VERSION = "formal_locality_barriers_v1"


@dataclass(frozen=True)
class CandidateSignalUniverse:
    universe_id: str
    target_id: str
    construction_mode: str
    locality_radius: int
    signals: tuple[str, ...]
    source_path: str
    source_hash: str
    optimized_path: str
    optimized_hash: str
    diagnostic_only: bool = False
    schema_version: str = SCHEMA_VERSION

    @property
    def universe_hash(self) -> str:
        return stable_hash(
            {
                "mode": self.construction_mode,
                "radius": self.locality_radius,
                "signals": self.signals,
                "source_hash": self.source_hash,
                "optimized_hash": self.optimized_hash,
                "diagnostic_only": self.diagnostic_only,
            }
        )

    def row(self) -> dict[str, str]:
        return {
            "universe_id": self.universe_id,
            "target_id": self.target_id,
            "construction_mode": self.construction_mode,
            "locality_radius": str(self.locality_radius),
            "universe_size": str(len(self.signals)),
            "signals": json.dumps(self.signals),
            "universe_hash": self.universe_hash,
            "source_hash": self.source_hash,
            "optimized_hash": self.optimized_hash,
            "diagnostic_only": str(self.diagnostic_only).lower(),
            "schema_version": self.schema_version,
        }


@dataclass(frozen=True)
class DistinguishabilityCounterexample:
    counterexample_id: str
    target_id: str
    universe_id: str
    assignment_a: dict[str, int]
    assignment_b: dict[str, int]
    target_a: tuple[int, ...]
    target_b: tuple[int, ...]
    difference_set: tuple[str, ...]
    counterexample_reproduced: bool
    schema_version: str = SCHEMA_VERSION

    def row(self) -> dict[str, str]:
        return {
            "counterexample_id": self.counterexample_id,
            "target_id": self.target_id,
            "universe_id": self.universe_id,
            "assignment_a_path": f"counterexamples/{self.counterexample_id}.a.json",
            "assignment_b_path": f"counterexamples/{self.counterexample_id}.b.json",
            "target_a": json.dumps(self.target_a),
            "target_b": json.dumps(self.target_b),
            "difference_set": json.dumps(self.difference_set),
            "difference_set_hash": stable_hash(self.difference_set),
            "counterexample_reproduced": str(self.counterexample_reproduced).lower(),
            "schema_version": self.schema_version,
        }


@dataclass(frozen=True)
class LocalityBarrierCertificate:
    certificate_id: str
    target_id: str
    benchmark: str
    split: str
    failure_group: str
    source_path: str
    optimized_path: str
    source_hash: str
    optimized_hash: str
    pi_alignment_hash: str
    target_vector: tuple[str, ...]
    universe_id: str
    universe_hash: str
    universe_mode: str
    universe_size: int
    locality_radius: int
    tested_interface: tuple[str, ...]
    counterexample_ids: tuple[str, ...]
    hitting_set_constraints_hash: str
    proved_lower_bound: int
    best_upper_bound: int | None
    exact_minimum_status: str
    solver_backend: str
    solver_status: str
    timeout: bool
    proof_runtime: float
    reproducibility_seed: int
    failure_reason: str
    classification: str
    diagnostic_only: bool = False
    source_blind: bool = True
    schema_version: str = SCHEMA_VERSION

    def row(self) -> dict[str, str]:
        data = asdict(self)
        data["target_vector"] = json.dumps(self.target_vector)
        data["tested_interface"] = json.dumps(self.tested_interface)
        data["counterexample_ids"] = json.dumps(self.counterexample_ids)
        data["best_upper_bound"] = "" if self.best_upper_bound is None else str(self.best_upper_bound)
        data["timeout"] = str(self.timeout).lower()
        data["proof_runtime"] = f"{self.proof_runtime:.6f}"
        data["diagnostic_only"] = str(self.diagnostic_only).lower()
        data["source_blind"] = str(self.source_blind).lower()
        return {key: str(value) for key, value in data.items()}


def stable_hash(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()[:16]


def all_node_names(net: BlifNetwork) -> tuple[str, ...]:
    return tuple(dict.fromkeys([*net.inputs, *[n.output for n in net.nodes], *net.outputs]))


def internal_signal_names(net: BlifNetwork) -> tuple[str, ...]:
    inputs = set(net.inputs)
    return tuple(sorted(name for name in all_node_names(net) if name not in inputs))


def structural_supports(net: BlifNetwork) -> dict[str, frozenset[str]]:
    support: dict[str, frozenset[str]] = {name: frozenset([name]) for name in net.inputs}
    for node in net.nodes:
        missing = [fanin for fanin in node.inputs if fanin not in support]
        if missing:
            raise ValueError(f"missing fanins while computing support for {node.output}: {missing}")
        node_support: set[str] = set()
        for fanin in node.inputs:
            node_support |= set(support[fanin])
        support[node.output] = frozenset(node_support)
    for output in net.outputs:
        support.setdefault(output, frozenset([output]) if output in net.inputs else frozenset())
    return support


def build_source_universes(
    *,
    target_id: str,
    source_path: Path,
    optimized_path: Path,
    target_vector: tuple[str, ...],
    max_size: int = 64,
) -> list[CandidateSignalUniverse]:
    source = parse_blif(source_path)
    optimized = parse_blif(optimized_path)
    source_names = set(all_node_names(source))
    opt_supports = structural_supports(optimized)
    target_support = set()
    for target in target_vector:
        target_support |= set(opt_supports.get(target, frozenset()))
    direct = tuple(sorted((source_names & set(target_vector)) | (source_names & target_support)))
    support_pis = tuple(sorted(name for name in source.inputs if name in target_support))
    internals = internal_signal_names(source)[:max_size]
    all_pis = tuple(source.inputs[:max_size])
    src_hash = file_hash(source_path)
    opt_hash = file_hash(optimized_path)
    specs = [
        ("U0_direct_name_intersection", 0, direct, False),
        ("U1_source_target_support_pi", 1, support_pis, False),
        ("U5_all_source_internal", -1, internals, False),
        ("U6_all_aligned_primary_inputs", -1, all_pis, True),
    ]
    universes: list[CandidateSignalUniverse] = []
    for mode, radius, signals, diagnostic in specs:
        bounded = tuple(dict.fromkeys(signals[:max_size]))
        universes.append(
            CandidateSignalUniverse(
                universe_id=f"{target_id}::{mode}",
                target_id=target_id,
                construction_mode=mode,
                locality_radius=radius,
                signals=bounded,
                source_path=str(source_path),
                source_hash=src_hash,
                optimized_path=str(optimized_path),
                optimized_hash=opt_hash,
                diagnostic_only=diagnostic,
            )
        )
    return universes


def pi_alignment_hash(source: BlifNetwork, optimized: BlifNetwork) -> str:
    return stable_hash({"source_inputs": source.inputs, "optimized_inputs": optimized.inputs})


def validate_pair(source: BlifNetwork, optimized: BlifNetwork, target_vector: tuple[str, ...]) -> str:
    if source.inputs != optimized.inputs:
        return "pi_alignment_failure"
    names = set(all_node_names(optimized))
    missing = [target for target in target_vector if target not in names]
    if missing:
        return "optimized_target_missing:" + ",".join(missing)
    return "ok"


def all_assignments(inputs: tuple[str, ...]) -> Iterable[dict[str, int]]:
    for value in range(1 << len(inputs)):
        yield {name: (value >> idx) & 1 for idx, name in enumerate(inputs)}


def vector_eval(net: BlifNetwork, nodes: tuple[str, ...], assignment: dict[str, int]) -> tuple[int, ...]:
    values = scalar_eval_exact(net, assignment)
    return tuple(int(values.get(node, 0)) & 1 for node in nodes)


def scalar_eval_exact(net: BlifNetwork, assignment: dict[str, int]) -> dict[str, int]:
    """Evaluate the BLIF subset, including ABC's output-0 cover shorthand."""

    values = {name: int(assignment.get(name, 0)) & 1 for name in net.inputs}
    for node in net.nodes:
        missing = [fanin for fanin in node.inputs if fanin not in values]
        if missing:
            raise ValueError(f"missing fanin values for {node.output}: {missing}")
        values[node.output] = eval_cover_exact(node.inputs, node.cover, values)
    return values


def eval_cover_exact(inputs: list[str], cover: list[str], values: dict[str, int]) -> int:
    if not inputs:
        if any(row.strip() == "1" for row in cover):
            return 1
        return 0
    rows = []
    has_onset = False
    has_offset = False
    for raw in cover:
        parts = raw.split()
        if not parts:
            continue
        pattern = parts[0]
        out = parts[1] if len(parts) > 1 else "1"
        if out == "1":
            has_onset = True
        elif out == "0":
            has_offset = True
        else:
            raise ValueError(f"unsupported BLIF output value: {out}")
        rows.append((pattern, out))
    if has_onset:
        return int(any(_cube_matches(pattern, inputs, values) for pattern, out in rows if out == "1"))
    if has_offset:
        return int(not any(_cube_matches(pattern, inputs, values) for pattern, out in rows if out == "0"))
    return 0


def _cube_matches(pattern: str, inputs: list[str], values: dict[str, int]) -> bool:
    for char, name in zip(pattern, inputs):
        if char == "-":
            continue
        if char not in {"0", "1"}:
            raise ValueError(f"unsupported BLIF cover character: {char}")
        if values[name] != int(char):
            return False
    return True


@dataclass(frozen=True)
class SufficiencyQueryResult:
    status: str
    solver_backend: str
    runtime: float
    counterexample: tuple[dict[str, int], dict[str, int]] | None
    counterexample_reproduced: bool
    unsupported_reason: str = ""


def prove_interface_sufficiency(
    *,
    source_path: Path,
    optimized_path: Path,
    interface: tuple[str, ...],
    target_vector: tuple[str, ...],
    timeout_ms: int = 5000,
    exact_input_limit: int = 12,
) -> SufficiencyQueryResult:
    source = parse_blif(source_path)
    optimized = parse_blif(optimized_path)
    start = time.perf_counter()
    validation = validate_pair(source, optimized, target_vector)
    if validation != "ok":
        return SufficiencyQueryResult("unsupported", "validation", time.perf_counter() - start, None, False, validation)
    missing_interface = [name for name in interface if name not in set(all_node_names(source))]
    if missing_interface:
        return SufficiencyQueryResult("unsupported", "validation", time.perf_counter() - start, None, False, "source_interface_missing:" + ",".join(missing_interface))
    if len(source.inputs) <= exact_input_limit:
        return _prove_interface_exhaustive(source, optimized, interface, target_vector, start)
    return _prove_interface_z3(source, optimized, interface, target_vector, start, timeout_ms)


def _prove_interface_exhaustive(
    source: BlifNetwork,
    optimized: BlifNetwork,
    interface: tuple[str, ...],
    target_vector: tuple[str, ...],
    start: float,
) -> SufficiencyQueryResult:
    seen: dict[tuple[int, ...], tuple[tuple[int, ...], dict[str, int]]] = {}
    for assignment in all_assignments(tuple(source.inputs)):
        key = vector_eval(source, interface, assignment)
        target = vector_eval(optimized, target_vector, assignment)
        if key in seen and seen[key][0] != target:
            a_assignment = seen[key][1]
            b_assignment = assignment
            reproduced = (
                vector_eval(source, interface, a_assignment) == vector_eval(source, interface, b_assignment)
                and vector_eval(optimized, target_vector, a_assignment) != vector_eval(optimized, target_vector, b_assignment)
            )
            return SufficiencyQueryResult("sat", "exhaustive_two_copy_miter", time.perf_counter() - start, (a_assignment, b_assignment), reproduced)
        seen[key] = (target, assignment)
    return SufficiencyQueryResult("unsat", "exhaustive_two_copy_miter", time.perf_counter() - start, None, True)


def _encode_net_with_shared_inputs(net: BlifNetwork, prefix: str, pi_symbols: dict[str, object]) -> dict[str, object]:
    if z3 is None:
        raise RuntimeError("z3 is not installed")
    values = dict(pi_symbols)
    seen = set(values)
    for node in net.nodes:
        missing = [fanin for fanin in node.inputs if fanin not in values]
        if missing:
            raise ValueError(f"node {node.output} has missing fanins: {missing}")
        if node.output in seen:
            raise ValueError(f"duplicate BLIF output assignment: {node.output}")
        values[node.output] = encode_cover([values[fanin] for fanin in node.inputs], node.cover)
        seen.add(node.output)
    return values


def _pack_bool_vector(values: dict[str, object], names: tuple[str, ...]) -> object:
    if z3 is None:
        raise RuntimeError("z3 is not installed")
    bits = [values[name] for name in names]
    if not bits:
        return z3.BoolVal(True)
    return z3.And(*[a == b for a, b in zip(bits, bits)])


def _prove_interface_z3(
    source: BlifNetwork,
    optimized: BlifNetwork,
    interface: tuple[str, ...],
    target_vector: tuple[str, ...],
    start: float,
    timeout_ms: int,
) -> SufficiencyQueryResult:
    if z3 is None:
        return SufficiencyQueryResult("unsupported", "z3_two_copy_miter", time.perf_counter() - start, None, False, "z3_not_installed")
    try:
        a_pis = {name: z3.Bool(f"a_{name}_{stable_hash(name)}") for name in source.inputs}
        b_pis = {name: z3.Bool(f"b_{name}_{stable_hash(name)}") for name in source.inputs}
        a_source = _encode_net_with_shared_inputs(source, "a_src", a_pis)
        b_source = _encode_net_with_shared_inputs(source, "b_src", b_pis)
        a_opt = _encode_net_with_shared_inputs(optimized, "a_opt", a_pis)
        b_opt = _encode_net_with_shared_inputs(optimized, "b_opt", b_pis)
        solver = z3.Solver()
        solver.set("timeout", timeout_ms)
        solver.set("random_seed", 0)
        for name in interface:
            solver.add(a_source[name] == b_source[name])
        solver.add(z3.Or(*[a_opt[name] != b_opt[name] for name in target_vector]))
        result = solver.check()
        runtime = time.perf_counter() - start
        if result == z3.unsat:
            return SufficiencyQueryResult("unsat", "z3_two_copy_miter", runtime, None, True)
        if result == z3.sat:
            model = solver.model()
            a_assignment = {name: int(bool(model.eval(sym, model_completion=True))) for name, sym in a_pis.items()}
            b_assignment = {name: int(bool(model.eval(sym, model_completion=True))) for name, sym in b_pis.items()}
            reproduced = (
                vector_eval(source, interface, a_assignment) == vector_eval(source, interface, b_assignment)
                and vector_eval(optimized, target_vector, a_assignment) != vector_eval(optimized, target_vector, b_assignment)
            )
            return SufficiencyQueryResult("sat", "z3_two_copy_miter", runtime, (a_assignment, b_assignment), reproduced)
        return SufficiencyQueryResult("timeout", "z3_two_copy_miter", runtime, None, False, "z3_unknown_or_timeout")
    except Exception as exc:
        return SufficiencyQueryResult("unsupported", "z3_two_copy_miter", time.perf_counter() - start, None, False, f"{type(exc).__name__}:{exc}")


def difference_set(source_path: Path, universe: tuple[str, ...], a_assignment: dict[str, int], b_assignment: dict[str, int]) -> tuple[str, ...]:
    net = parse_blif(source_path)
    a_values = scalar_eval_exact(net, a_assignment)
    b_values = scalar_eval_exact(net, b_assignment)
    return tuple(sorted(name for name in universe if int(a_values.get(name, 0)) != int(b_values.get(name, 0))))


def exact_minimum_hitting_set(constraints: list[tuple[str, ...]], universe: tuple[str, ...], *, max_width: int, exact_threshold: int = 18) -> tuple[tuple[str, ...] | None, int, bool]:
    if any(len(set(c)) == 0 for c in constraints):
        return None, 10**9, True
    if not constraints:
        return tuple(), 0, True
    signals = tuple(sorted(universe))
    if len(signals) > exact_threshold:
        # Valid but conservative: the number of pairwise-disjoint constraints is
        # a lower bound, and a deterministic greedy set is only an upper-bound candidate.
        remaining = [set(c) for c in constraints]
        lower = _greedy_disjoint_lower_bound(remaining)
        chosen: list[str] = []
        while remaining and len(chosen) <= max_width:
            counts = {s: sum(s in c for c in remaining) for s in signals if s not in chosen}
            if not counts:
                break
            pick = max(sorted(counts), key=lambda s: counts[s])
            chosen.append(pick)
            remaining = [c for c in remaining if pick not in c]
        return (tuple(sorted(chosen)) if not remaining and len(chosen) <= max_width else None), lower, False
    for width in range(max_width + 1):
        for combo in itertools.combinations(signals, width):
            selected = set(combo)
            if all(selected & set(c) for c in constraints):
                return tuple(combo), width, True
    return None, max_width + 1, True


def _greedy_disjoint_lower_bound(constraints: list[set[str]]) -> int:
    used: set[str] = set()
    lower = 0
    for c in sorted(constraints, key=lambda item: (len(item), sorted(item))):
        if not used & c:
            lower += 1
            used |= c
    return lower


def solve_minimum_interface(
    *,
    target_id: str,
    benchmark: str,
    split: str,
    failure_group: str,
    source_path: Path,
    optimized_path: Path,
    target_vector: tuple[str, ...],
    universe: CandidateSignalUniverse,
    max_width: int = 6,
    max_iterations: int = 32,
    timeout_ms: int = 5000,
    exact_threshold: int = 18,
    seed: int = 0,
) -> tuple[LocalityBarrierCertificate, list[DistinguishabilityCounterexample], list[dict[str, str]]]:
    start = time.perf_counter()
    source = parse_blif(source_path)
    optimized = parse_blif(optimized_path)
    constraints: list[tuple[str, ...]] = []
    counterexamples: list[DistinguishabilityCounterexample] = []
    iteration_rows: list[dict[str, str]] = []
    validation = validate_pair(source, optimized, target_vector)
    if validation != "ok":
        return (
            _certificate(
                target_id=target_id,
                benchmark=benchmark,
                split=split,
                failure_group=failure_group,
                source_path=source_path,
                optimized_path=optimized_path,
                target_vector=target_vector,
                universe=universe,
                interface=tuple(),
                cex_ids=tuple(),
                constraints=constraints,
                lower=0,
                upper=None,
                exact_status="not_applicable",
                solver_status="not_run",
                solver_backend="validation",
                timeout=False,
                runtime=time.perf_counter() - start,
                seed=seed,
                failure_reason=validation,
                classification="insufficient_target_provenance",
            ),
            [],
            [],
        )
    current: tuple[str, ...] | None = tuple()
    lower_bound = 0
    exact_lower = True
    last_query = "not_run"
    backend = "not_run"
    timeout = False
    failure_reason = ""
    for iteration in range(max_iterations):
        current, lower_bound, exact_lower = exact_minimum_hitting_set(constraints, universe.signals, max_width=max_width, exact_threshold=exact_threshold)
        if current is None:
            failure_reason = "hitting_set_exceeds_configured_width"
            break
        before = len(counterexamples)
        proof = prove_interface_sufficiency(
            source_path=source_path,
            optimized_path=optimized_path,
            interface=current,
            target_vector=target_vector,
            timeout_ms=timeout_ms,
        )
        last_query = proof.status
        backend = proof.solver_backend
        timeout = proof.status == "timeout"
        row_base = {
            "target_id": target_id,
            "universe_id": universe.universe_id,
            "iteration": str(iteration),
            "candidate_interface": json.dumps(current),
            "candidate_width": str(len(current)),
            "lower_bound": str(lower_bound),
            "exact_hitting_set_lower_bound": str(exact_lower).lower(),
            "solver_status": proof.status,
            "solver_backend": proof.solver_backend,
            "runtime_s": f"{proof.runtime:.6f}",
            "counterexamples_before": str(before),
            "schema_version": SCHEMA_VERSION,
        }
        if proof.status == "unsat":
            iteration_rows.append({**row_base, "counterexamples_after": str(len(counterexamples)), "counterexample_id": "", "termination": "sufficient"})
            exact = exact_lower and lower_bound == len(current)
            classification = "whole_design_only" if universe.diagnostic_only else ("compact_exact_input_interface_found" if len(current) <= max_width else "input_minimum_above_previous_bound")
            return (
                _certificate(
                    target_id=target_id,
                    benchmark=benchmark,
                    split=split,
                    failure_group=failure_group,
                    source_path=source_path,
                    optimized_path=optimized_path,
                    target_vector=target_vector,
                    universe=universe,
                    interface=current,
                    cex_ids=tuple(c.counterexample_id for c in counterexamples),
                    constraints=constraints,
                    lower=lower_bound,
                    upper=len(current),
                    exact_status="exact_minimum" if exact else "sufficient_upper_bound",
                    solver_status="unsat",
                    solver_backend=backend,
                    timeout=False,
                    runtime=time.perf_counter() - start,
                    seed=seed,
                    failure_reason="" if exact else "hitting_set_lower_bound_not_exact",
                    classification="global_diagnostic_not_local_success" if universe.diagnostic_only else classification,
                    diagnostic_only=universe.diagnostic_only,
                ),
                counterexamples,
                iteration_rows,
            )
        if proof.status == "sat" and proof.counterexample is not None:
            a_assignment, b_assignment = proof.counterexample
            diff = difference_set(source_path, universe.signals, a_assignment, b_assignment)
            cex_id = f"{stable_hash([target_id, universe.universe_id, iteration, a_assignment, b_assignment])}_cex"
            cex = DistinguishabilityCounterexample(
                cex_id,
                target_id,
                universe.universe_id,
                a_assignment,
                b_assignment,
                vector_eval(optimized, target_vector, a_assignment),
                vector_eval(optimized, target_vector, b_assignment),
                diff,
                proof.counterexample_reproduced,
            )
            counterexamples.append(cex)
            constraints.append(diff)
            iteration_rows.append({**row_base, "counterexamples_after": str(len(counterexamples)), "counterexample_id": cex_id, "termination": "counterexample"})
            if not diff:
                return (
                    _certificate(
                        target_id=target_id,
                        benchmark=benchmark,
                        split=split,
                        failure_group=failure_group,
                        source_path=source_path,
                        optimized_path=optimized_path,
                        target_vector=target_vector,
                        universe=universe,
                        interface=current,
                        cex_ids=tuple(c.counterexample_id for c in counterexamples),
                        constraints=constraints,
                        lower=10**9,
                        upper=None,
                        exact_status="universe_formally_insufficient",
                        solver_status="sat",
                        solver_backend=backend,
                        timeout=False,
                        runtime=time.perf_counter() - start,
                        seed=seed,
                        failure_reason="empty_difference_set_for_target_distinguishing_pair",
                        classification="local_input_universe_formally_insufficient",
                        diagnostic_only=universe.diagnostic_only,
                    ),
                    counterexamples,
                    iteration_rows,
                )
            continue
        failure_reason = proof.unsupported_reason or proof.status
        break
    current = current or tuple()
    upper = len(current) if last_query == "unsat" else None
    classification = "unresolved_timeout" if timeout else ("input_lower_bound_above_previous_bound" if lower_bound > max_width else "search_budget_exhaustion")
    return (
        _certificate(
            target_id=target_id,
            benchmark=benchmark,
            split=split,
            failure_group=failure_group,
            source_path=source_path,
            optimized_path=optimized_path,
            target_vector=target_vector,
            universe=universe,
            interface=current,
            cex_ids=tuple(c.counterexample_id for c in counterexamples),
            constraints=constraints,
            lower=lower_bound,
            upper=upper,
            exact_status="proved_lower_bound_with_upper_bound" if upper is not None else "proved_lower_bound_no_upper_bound",
            solver_status=last_query,
            solver_backend=backend,
            timeout=timeout,
            runtime=time.perf_counter() - start,
            seed=seed,
            failure_reason=failure_reason,
            classification=classification,
            diagnostic_only=universe.diagnostic_only,
        ),
        counterexamples,
        iteration_rows,
    )


def _certificate(
    *,
    target_id: str,
    benchmark: str,
    split: str,
    failure_group: str,
    source_path: Path,
    optimized_path: Path,
    target_vector: tuple[str, ...],
    universe: CandidateSignalUniverse,
    interface: tuple[str, ...],
    cex_ids: tuple[str, ...],
    constraints: list[tuple[str, ...]],
    lower: int,
    upper: int | None,
    exact_status: str,
    solver_status: str,
    solver_backend: str,
    timeout: bool,
    runtime: float,
    seed: int,
    failure_reason: str,
    classification: str,
    diagnostic_only: bool = False,
) -> LocalityBarrierCertificate:
    source = parse_blif(source_path) if source_path.exists() else BlifNetwork([], [], [])
    optimized = parse_blif(optimized_path) if optimized_path.exists() else BlifNetwork([], [], [])
    return LocalityBarrierCertificate(
        certificate_id=stable_hash([target_id, universe.universe_id, interface, cex_ids, exact_status]),
        target_id=target_id,
        benchmark=benchmark,
        split=split,
        failure_group=failure_group,
        source_path=str(source_path),
        optimized_path=str(optimized_path),
        source_hash=file_hash(source_path) if source_path.exists() else "",
        optimized_hash=file_hash(optimized_path) if optimized_path.exists() else "",
        pi_alignment_hash=pi_alignment_hash(source, optimized),
        target_vector=target_vector,
        universe_id=universe.universe_id,
        universe_hash=universe.universe_hash,
        universe_mode=universe.construction_mode,
        universe_size=len(universe.signals),
        locality_radius=universe.locality_radius,
        tested_interface=interface,
        counterexample_ids=cex_ids,
        hitting_set_constraints_hash=stable_hash(constraints),
        proved_lower_bound=lower,
        best_upper_bound=upper,
        exact_minimum_status=exact_status,
        solver_backend=solver_backend,
        solver_status=solver_status,
        timeout=timeout,
        proof_runtime=runtime,
        reproducibility_seed=seed,
        failure_reason=failure_reason,
        classification=classification,
        diagnostic_only=diagnostic_only,
    )


def output_interface_sufficiency(
    *,
    source_path: Path,
    optimized_path: Path,
    optimized_interface: tuple[str, ...],
    residual_source: tuple[str, ...],
    source_outputs: tuple[str, ...],
    timeout_ms: int = 5000,
    exact_input_limit: int = 12,
) -> SufficiencyQueryResult:
    # Same two-copy form, but equality is over optimized B and residual source Z,
    # and the distinguished vector is the source output frontier.
    source = parse_blif(source_path)
    optimized = parse_blif(optimized_path)
    start = time.perf_counter()
    if source.inputs != optimized.inputs:
        return SufficiencyQueryResult("unsupported", "validation", time.perf_counter() - start, None, False, "pi_alignment_failure")
    if len(source.inputs) <= exact_input_limit:
        seen: dict[tuple[int, ...], tuple[tuple[int, ...], dict[str, int]]] = {}
        for assignment in all_assignments(tuple(source.inputs)):
            key = vector_eval(optimized, optimized_interface, assignment) + vector_eval(source, residual_source, assignment)
            y = vector_eval(source, source_outputs, assignment)
            if key in seen and seen[key][0] != y:
                a_assignment = seen[key][1]
                b_assignment = assignment
                reproduced = (
                    vector_eval(optimized, optimized_interface, a_assignment) == vector_eval(optimized, optimized_interface, b_assignment)
                    and vector_eval(source, residual_source, a_assignment) == vector_eval(source, residual_source, b_assignment)
                    and vector_eval(source, source_outputs, a_assignment) != vector_eval(source, source_outputs, b_assignment)
                )
                return SufficiencyQueryResult("sat", "exhaustive_output_interface_miter", time.perf_counter() - start, (a_assignment, b_assignment), reproduced)
            seen[key] = (y, assignment)
        return SufficiencyQueryResult("unsat", "exhaustive_output_interface_miter", time.perf_counter() - start, None, True)
    # For larger cases the input-interface Z3 miter can be reused by treating the
    # combined B/Z vector as the proposed interface in a product evaluator only
    # through exhaustive mode is currently required by committed benchmarks.
    return SufficiencyQueryResult("unsupported", "z3_output_interface_miter", time.perf_counter() - start, None, False, "large_output_interface_z3_not_enabled")
