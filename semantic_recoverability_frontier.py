"""Semantic recoverability frontier utilities.

This module supports the trajectory experiment that asks where compact,
locally exploitable semantic structure stops being recoverable along synthesis
trajectories.  It deliberately separates blind observations from evaluation and
oracle diagnostics: blind candidate generation records checkpoint-local
features, while ground-truth boundary metadata is joined only by the experiment
runner when writing evaluation rows.
"""

from __future__ import annotations

import hashlib
import itertools
import json
import subprocess
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable, Iterable

from analyze_blif_matches import BlifNetwork, parse_blif
from semantic_functional_refactoring import (
    SemanticDivisor,
    eval_divisor,
    eval_outputs,
    prove_decomposability_z3,
)


SCHEMA_VERSION = "semantic_recoverability_frontier_v1"
RECOVERY_ORDER = {
    "R0_structural_survival": 0,
    "R1_functional_internal_survival": 1,
    "R2_blind_semantic_reconstruction": 2,
    "R3_blind_closed_region_replacement": 3,
    "R4_blind_functional_refactoring": 4,
    "R5_oracle_divisor_compact_decomposition": 5,
    "R6_oracle_divisor_support_decomposition": 6,
    "R7_oracle_window_decomposition": 7,
    "R8_non_local_global_factorisation": 8,
    "R9_unresolved": 9,
}
BLIND_FORBIDDEN_FIELDS = {
    "operator_type",
    "source_location",
    "source_support",
    "source_hierarchy",
    "ground_truth_expression",
    "oracle_divisor_id",
    "oracle_window_id",
    "original_bus_mapping",
    "boundary_type",
}


@dataclass(frozen=True)
class BoundaryRecord:
    boundary_id: str
    benchmark: str
    design_family: str
    split: str
    module: str
    operator_type: str
    source_location: str
    input_widths: tuple[int, ...]
    output_widths: tuple[int, ...]
    signedness: str
    source_support: tuple[str, ...]
    output_nodes: tuple[str, ...]
    consumer_count: int
    consumer_identities: tuple[str, ...]
    externally_observable: bool
    nontrivial: bool
    eligible_for_blind_evaluation: bool
    divisor: SemanticDivisor

    @property
    def fingerprint(self) -> str:
        payload = asdict(self)
        payload["divisor"] = self.divisor.canonical_form
        return stable_hash(payload)

    def manifest_row(self) -> dict[str, str]:
        return {
            "boundary_id": self.boundary_id,
            "benchmark": self.benchmark,
            "design_family": self.design_family,
            "split": self.split,
            "module": self.module,
            "source_location": self.source_location,
            "operator_type": self.operator_type,
            "input_widths": json.dumps(self.input_widths),
            "output_widths": json.dumps(self.output_widths),
            "signedness": self.signedness,
            "source_support": json.dumps(self.source_support),
            "output_function": self.divisor.canonical_form,
            "consumer_count": str(self.consumer_count),
            "consumer_identities": json.dumps(self.consumer_identities),
            "fanout_properties": json.dumps({"externally_observable": self.externally_observable}, sort_keys=True),
            "externally_observable": str(self.externally_observable).lower(),
            "nontrivial": str(self.nontrivial).lower(),
            "eligible_for_blind_evaluation": str(self.eligible_for_blind_evaluation).lower(),
            "fingerprint": self.fingerprint,
            "schema_version": SCHEMA_VERSION,
        }


@dataclass(frozen=True)
class TrajectorySpec:
    trajectory_id: str
    benchmark: str
    split: str
    source_blif: Path
    pass_sequence: tuple[str, ...]
    flow_family: str
    deterministic_seed: int = 0


@dataclass(frozen=True)
class Checkpoint:
    trajectory_id: str
    checkpoint_id: str
    benchmark: str
    split: str
    checkpoint_index: int
    pass_name: str
    pass_occurrence: int
    command_sequence: tuple[str, ...]
    blif_path: Path
    cec_status: str
    cec_output: str
    runtime_s: float
    unsupported_reason: str = ""
    artifact_status: str = "materialized"
    parse_status: str = "parse_valid"


def stable_hash(payload: object) -> str:
    text = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def structural_metrics(path: Path) -> dict[str, str]:
    net = parse_blif(path)
    fanout: dict[str, int] = {name: 0 for name in net.inputs}
    levels: dict[str, int] = {name: 0 for name in net.inputs}
    edges = 0
    for node in net.nodes:
        edges += len(node.inputs)
        for fanin in node.inputs:
            fanout[fanin] = fanout.get(fanin, 0) + 1
        levels[node.output] = 1 + max((levels.get(fanin, 0) for fanin in node.inputs), default=0)
    for output in net.outputs:
        fanout[output] = fanout.get(output, 0)
    return {
        "node_count": str(len(net.nodes)),
        "edge_count": str(edges),
        "level_count": str(max((levels.get(output, 0) for output in net.outputs), default=0)),
        "input_count": str(len(net.inputs)),
        "output_count": str(len(net.outputs)),
        "internal_fanout_sum": str(sum(v for k, v in fanout.items() if k not in net.inputs)),
    }


def write_truth_blif(
    path: Path,
    model: str,
    inputs: tuple[str, ...],
    outputs: tuple[str, ...],
    fn: Callable[[dict[str, int]], tuple[int, ...]],
    *,
    internal_nodes: dict[str, Callable[[dict[str, int]], int]] | None = None,
) -> None:
    """Write a small BLIF truth-table network with optional semantic internals."""

    lines = [f".model {model}", ".inputs " + " ".join(inputs)]
    internal_nodes = internal_nodes or {}
    lines.append(".outputs " + " ".join(outputs))
    for node_name, node_fn in sorted(internal_nodes.items()):
        lines.append(".names " + " ".join((*inputs, node_name)))
        for assignment in _assignments(inputs):
            if node_fn(assignment) & 1:
                lines.append("".join(str(assignment[name]) for name in inputs) + " 1")
    available_inputs = tuple(inputs) + tuple(sorted(internal_nodes))
    for bit, output in enumerate(outputs):
        lines.append(".names " + " ".join((*available_inputs, output)))
        for assignment in _assignments(inputs):
            values = dict(assignment)
            for node_name, node_fn in sorted(internal_nodes.items()):
                values[node_name] = node_fn(assignment) & 1
            if fn(assignment)[bit] & 1:
                lines.append("".join(str(values[name]) for name in available_inputs) + " 1")
    lines.append(".end")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_abc_checkpoint(
    *,
    abc: Path,
    source: Path,
    output: Path,
    commands: tuple[str, ...],
    timeout_s: int = 10,
) -> tuple[str, str, float]:
    """Run an ABC command prefix and write a BLIF checkpoint."""

    output.parent.mkdir(parents=True, exist_ok=True)
    if not abc.exists():
        return "unsupported", "abc_unavailable", 0.0
    script = "; ".join(("read_blif " + str(source), *commands, "write_blif " + str(output)))
    start = time.perf_counter()
    try:
        proc = subprocess.run([str(abc), "-c", script], text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout_s, check=False)
    except subprocess.TimeoutExpired:
        return "timeout", "abc_timeout", time.perf_counter() - start
    runtime = time.perf_counter() - start
    if proc.returncode != 0 or not output.exists():
        return "unsupported", proc.stdout.strip() or "abc_failed_without_output", runtime
    try:
        parse_blif(output)
    except Exception as exc:
        return "unsupported", f"checkpoint_parse_failed:{type(exc).__name__}:{exc}", runtime
    return "ok", proc.stdout.strip(), runtime


def abc_cec(abc: Path, reference: Path, candidate: Path, timeout_s: int = 10) -> tuple[str, str]:
    if not abc.exists():
        return "unsupported", "abc_unavailable"
    script = f"cec {reference} {candidate}"
    try:
        proc = subprocess.run([str(abc), "-c", script], text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout_s, check=False)
    except subprocess.TimeoutExpired:
        return "timeout", "abc_timeout"
    output = proc.stdout.strip()
    if "Networks are equivalent" in output:
        return "equivalent", output
    if "Networks are NOT EQUIVALENT" in output or "not equivalent" in output.lower():
        return "not_equivalent", output
    return "unknown", output


def generate_trajectory(
    *,
    spec: TrajectorySpec,
    abc: Path,
    output_dir: Path,
    timeout_s: int = 10,
) -> list[Checkpoint]:
    checkpoints: list[Checkpoint] = []
    occurrence: dict[str, int] = {}
    source_out = output_dir / spec.trajectory_id / "cp000_source.blif"
    source_out.parent.mkdir(parents=True, exist_ok=True)
    source_out.write_text(spec.source_blif.read_text(encoding="utf-8"), encoding="utf-8")
    cec, cec_output = abc_cec(abc, spec.source_blif, source_out, timeout_s)
    checkpoints.append(Checkpoint(spec.trajectory_id, f"{spec.trajectory_id}__cp000_source", spec.benchmark, spec.split, 0, "source", 0, tuple(), source_out, cec, cec_output, 0.0, "", "materialized", "parse_valid"))
    prefix: list[str] = []
    for idx, command in enumerate(spec.pass_sequence, start=1):
        pass_name = command.split()[0]
        occurrence[pass_name] = occurrence.get(pass_name, 0) + 1
        prefix.append(command)
        checkpoint_path = output_dir / spec.trajectory_id / f"cp{idx:03d}_{pass_name}_{occurrence[pass_name]}.blif"
        status, output, runtime = run_abc_checkpoint(abc=abc, source=spec.source_blif, output=checkpoint_path, commands=tuple(prefix), timeout_s=timeout_s)
        if status == "ok":
            cec, cec_output = abc_cec(abc, spec.source_blif, checkpoint_path, timeout_s)
        else:
            cec, cec_output = "not_run", output
        if status == "ok":
            artifact_status = "materialized"
            parse_status = "parse_valid"
        elif checkpoint_path.exists():
            artifact_status = "materialized"
            try:
                parse_blif(checkpoint_path)
                parse_status = "parse_valid"
            except Exception:
                parse_status = "parse_invalid"
        else:
            artifact_status = "unrealized"
            parse_status = "not_run"
        checkpoints.append(Checkpoint(spec.trajectory_id, f"{spec.trajectory_id}__cp{idx:03d}_{pass_name}_{occurrence[pass_name]}", spec.benchmark, spec.split, idx, pass_name, occurrence[pass_name], tuple(prefix), checkpoint_path, cec, cec_output, runtime, "" if status == "ok" else output, artifact_status, parse_status))
    return checkpoints


def blind_prediction_rows(checkpoint: Checkpoint) -> list[dict[str, str]]:
    """Emit source-blind checkpoint observations without boundary metadata."""

    if checkpoint.cec_status != "equivalent":
        return []
    net = parse_blif(checkpoint.blif_path)
    rows: list[dict[str, str]] = []
    for idx, node in enumerate(sorted(net.nodes, key=lambda n: n.output)):
        rows.append(
            {
                "prediction_id": f"{checkpoint.checkpoint_id}__node_{idx:04d}",
                "trajectory_id": checkpoint.trajectory_id,
                "checkpoint_id": checkpoint.checkpoint_id,
                "checkpoint_index": str(checkpoint.checkpoint_index),
                "method": "blind_structural_scan",
                "candidate_signal": node.output,
                "support_size": str(len(node.inputs)),
                "fanin_signature": stable_hash({"inputs": sorted(node.inputs), "cover": node.cover}),
                "source_blind": "true",
                "schema_version": SCHEMA_VERSION,
            }
        )
    return rows


def classify_recoverability(
    *,
    checkpoint: Checkpoint,
    boundary: BoundaryRecord,
    method: str,
    oracle_mode: str,
    residual_support: tuple[str, ...],
    window_outputs: tuple[str, ...],
    local_threshold_nodes: int,
) -> dict[str, str]:
    """Classify one boundary/checkpoint/method row."""

    start = time.perf_counter()
    if checkpoint.cec_status != "equivalent":
        return _recovery_row(checkpoint, boundary, method, oracle_mode, "R9_unresolved", False, "checkpoint_failed_global_cec", 0.0)
    net = parse_blif(checkpoint.blif_path)
    if method == "structural":
        surviving = [node for node in boundary.output_nodes if node in {n.output for n in net.nodes}]
        if surviving:
            return _recovery_row(checkpoint, boundary, method, oracle_mode, "R0_structural_survival", True, "", time.perf_counter() - start)
        return _recovery_row(checkpoint, boundary, method, oracle_mode, "R9_unresolved", False, "no_exact_or_complemented_internal_survivor", time.perf_counter() - start)
    if oracle_mode == "blind":
        # Blind rows must not receive the true divisor.  Non-structural blind
        # method rows are populated from existing source-blind predictions or
        # reported as failures before any oracle proof is attempted.
        return _recovery_row(checkpoint, boundary, method, oracle_mode, "R9_unresolved", False, "blind_divisor_not_discovered", time.perf_counter() - start)
    proof = prove_decomposability_z3(blif_path=checkpoint.blif_path, divisor=boundary.divisor, residual_support=residual_support, output_nodes=window_outputs, timeout_ms=5000)
    if proof["formal_status"] == "decomposable":
        window_nodes = len(net.nodes)
        if window_nodes > local_threshold_nodes:
            level = "R8_non_local_global_factorisation"
            reason = "only_non_local_decomposition_established"
            recovered = False
        elif oracle_mode == "oracle_window":
            level = "R7_oracle_window_decomposition"
            reason = ""
            recovered = True
        elif oracle_mode == "oracle_divisor_support":
            level = "R6_oracle_divisor_support_decomposition"
            reason = ""
            recovered = True
        else:
            level = "R5_oracle_divisor_compact_decomposition"
            reason = ""
            recovered = True
        return _recovery_row(checkpoint, boundary, method, oracle_mode, level, recovered, reason, time.perf_counter() - start, proof)
    reason = "exact_decomposition_disproved_for_selected_g_z_window" if proof["solver_result"] == "sat" else "proof_timeout_or_unsupported"
    return _recovery_row(checkpoint, boundary, method, oracle_mode, "R9_unresolved", False, reason, time.perf_counter() - start, proof)


def residual_frontier(
    *,
    checkpoint: Checkpoint,
    boundary: BoundaryRecord,
    candidate_residuals: tuple[str, ...],
    output_nodes: tuple[str, ...],
    max_width: int = 4,
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    """Cardinality-ordered residual search with exact minimum for small sets."""

    rows: list[dict[str, str]] = []
    cex_rows: list[dict[str, str]] = []
    if checkpoint.cec_status != "equivalent":
        return rows, cex_rows
    exact_minimum: tuple[str, ...] | None = None
    lower_bound = 0
    for width in range(0, min(max_width, len(candidate_residuals)) + 1):
        any_unsat = False
        for residual in itertools.combinations(candidate_residuals, width):
            proof = prove_decomposability_z3(blif_path=checkpoint.blif_path, divisor=boundary.divisor, residual_support=tuple(residual), output_nodes=output_nodes, timeout_ms=5000)
            status = str(proof["formal_status"])
            if proof["counterexample_available"] == "true":
                cex = proof.get("counterexample", {})
                cex_rows.append(
                    {
                        "counterexample_id": f"{checkpoint.checkpoint_id}__{boundary.boundary_id}__z{width}__{len(cex_rows):04d}",
                        "trajectory_id": checkpoint.trajectory_id,
                        "checkpoint_id": checkpoint.checkpoint_id,
                        "boundary_id": boundary.boundary_id,
                        "residual_set": json.dumps(residual),
                        "assignment_a": json.dumps(cex.get("a", {}), sort_keys=True) if isinstance(cex, dict) else "{}",
                        "assignment_b": json.dumps(cex.get("b", {}), sort_keys=True) if isinstance(cex, dict) else "{}",
                        "equal_divisor_and_residual": "true",
                        "different_output": "true",
                        "counterexample_reproduced": str(proof["counterexample_reproduced"]),
                        "schema_version": SCHEMA_VERSION,
                    }
                )
            rows.append(
                {
                    "trajectory_id": checkpoint.trajectory_id,
                    "checkpoint_id": checkpoint.checkpoint_id,
                    "boundary_id": boundary.boundary_id,
                    "residual_set": json.dumps(residual),
                    "residual_width": str(width),
                    "search_status": status,
                    "solver_result": str(proof["solver_result"]),
                    "minimum_status": "candidate_exact_minimum" if status == "decomposable" and exact_minimum is None else "excluded_or_nonminimum",
                    "residual_lower_bound": str(lower_bound),
                    "residual_upper_bound": str(width if status == "decomposable" else ""),
                    "runtime_s": str(proof["runtime_seconds"]),
                    "timeout": str(proof["timeout"]),
                    "schema_version": SCHEMA_VERSION,
                }
            )
            if status == "decomposable":
                exact_minimum = tuple(residual)
                any_unsat = True
                break
        if exact_minimum is not None:
            break
        lower_bound = width + 1
        if not any_unsat:
            continue
    for row in rows:
        if exact_minimum is not None and tuple(json.loads(row["residual_set"])) == exact_minimum:
            row["minimum_status"] = "exact_minimum"
            row["residual_lower_bound"] = str(len(exact_minimum))
            row["residual_upper_bound"] = str(len(exact_minimum))
    return rows, cex_rows


def recoverability_transitions(rows: Iterable[dict[str, str]]) -> list[dict[str, str]]:
    grouped: dict[tuple[str, str, str], list[dict[str, str]]] = {}
    for row in rows:
        grouped.setdefault((row["boundary_id"], row["trajectory_id"], row["method"]), []).append(row)
    transitions: list[dict[str, str]] = []
    for (boundary_id, trajectory_id, method), items in sorted(grouped.items()):
        ordered = sorted(items, key=lambda r: int(r["checkpoint_index"]))
        previous = None
        successes = []
        for item in ordered:
            success = item["recovered"] == "true"
            if success:
                successes.append(int(item["checkpoint_index"]))
            if previous is not None and previous["recovered"] != item["recovered"]:
                direction = "success_to_failure" if previous["recovered"] == "true" else "failure_to_success"
                transitions.append(
                    {
                        "boundary_id": boundary_id,
                        "trajectory_id": trajectory_id,
                        "method": method,
                        "from_checkpoint": previous["checkpoint_id"],
                        "to_checkpoint": item["checkpoint_id"],
                        "transition": direction,
                        "from_level": previous["recovery_level"],
                        "to_level": item["recovery_level"],
                        "schema_version": SCHEMA_VERSION,
                    }
                )
            previous = item
        frontier = "none" if not successes else str(max(successes))
        transitions.append(
            {
                "boundary_id": boundary_id,
                "trajectory_id": trajectory_id,
                "method": method,
                "from_checkpoint": "",
                "to_checkpoint": "",
                "transition": "summary",
                "from_level": "longest_success_interval=" + str(_longest_run(successes)),
                "to_level": "last_success_checkpoint=" + frontier,
                "schema_version": SCHEMA_VERSION,
            }
        )
    return transitions


def pass_deltas(checkpoints: list[Checkpoint], recovery_rows: Iterable[dict[str, str]], metric_rows: dict[str, dict[str, str]]) -> list[dict[str, str]]:
    by_cp = {cp.checkpoint_id: cp for cp in checkpoints}
    by_key = {(r["boundary_id"], r["method"], r["checkpoint_id"]): r for r in recovery_rows}
    rows: list[dict[str, str]] = []
    for row in sorted(by_key.values(), key=lambda r: (r["boundary_id"], r["method"], int(r["checkpoint_index"]))):
        idx = int(row["checkpoint_index"])
        if idx == 0:
            continue
        prev_id = by_cp[row["checkpoint_id"]].trajectory_id + "__cp" + f"{idx-1:03d}"
        prev = next((cp for cp in checkpoints if cp.trajectory_id == by_cp[row["checkpoint_id"]].trajectory_id and cp.checkpoint_index == idx - 1), None)
        if prev is None:
            continue
        before = by_key.get((row["boundary_id"], row["method"], prev.checkpoint_id))
        if before is None:
            continue
        before_metrics = metric_rows.get(prev.checkpoint_id, {})
        after_metrics = metric_rows.get(row["checkpoint_id"], {})
        transition = "unchanged"
        if before["recovered"] == "true" and row["recovered"] != "true":
            transition = "loss_associated_with_pass"
        elif before["recovered"] != "true" and row["recovered"] == "true":
            transition = "recovery_associated_with_pass"
        rows.append(
            {
                "trajectory_id": row["trajectory_id"],
                "boundary_id": row["boundary_id"],
                "method": row["method"],
                "pass_name": row["pass_name"],
                "checkpoint_before": prev.checkpoint_id,
                "checkpoint_after": row["checkpoint_id"],
                "recovery_before": before["recovered"],
                "recovery_after": row["recovered"],
                "transition_class": transition,
                "node_delta": _delta(before_metrics, after_metrics, "node_count"),
                "depth_delta": _delta(before_metrics, after_metrics, "level_count"),
                "causal_claim": "not_claimed_controlled_ablation_required",
                "schema_version": SCHEMA_VERSION,
            }
        )
    return rows


def leakage_audit(rows: Iterable[dict[str, str]]) -> list[dict[str, str]]:
    audited = list(rows)
    out: list[dict[str, str]] = []
    for row in audited:
        present = sorted(field for field in BLIND_FORBIDDEN_FIELDS if field in row and row.get("oracle_mode") == "blind")
        out.append(
            {
                "row_id": row.get("prediction_id", row.get("result_id", "")),
                "oracle_mode": row.get("oracle_mode", "blind"),
                "forbidden_fields_present": json.dumps(present),
                "leakage_status": "fail" if present else "pass",
                "schema_version": SCHEMA_VERSION,
            }
        )
    return out


def _assignments(inputs: tuple[str, ...]) -> Iterable[dict[str, int]]:
    for idx in range(1 << len(inputs)):
        yield {name: (idx >> bit) & 1 for bit, name in enumerate(inputs)}


def _recovery_row(
    checkpoint: Checkpoint,
    boundary: BoundaryRecord,
    method: str,
    oracle_mode: str,
    level: str,
    recovered: bool,
    failure_reason: str,
    runtime_s: float,
    proof: dict[str, object] | None = None,
) -> dict[str, str]:
    proof = proof or {}
    return {
        "result_id": f"{boundary.boundary_id}__{checkpoint.checkpoint_id}__{method}__{oracle_mode}",
        "benchmark": boundary.benchmark,
        "design_family": boundary.design_family,
        "split": boundary.split,
        "boundary_id": boundary.boundary_id,
        "trajectory_id": checkpoint.trajectory_id,
        "checkpoint_id": checkpoint.checkpoint_id,
        "checkpoint_index": str(checkpoint.checkpoint_index),
        "pass_name": checkpoint.pass_name,
        "method": method,
        "oracle_mode": oracle_mode,
        "recovery_level": level,
        "recovered": str(recovered).lower(),
        "semantic_proof_status": str(proof.get("formal_status", "not_run")),
        "decomposition_status": str(proof.get("formal_status", "not_run")),
        "solver_result": str(proof.get("solver_result", "not_run")),
        "counterexample_available": str(proof.get("counterexample_available", "false")),
        "counterexample_reproduced": str(proof.get("counterexample_reproduced", "true")),
        "runtime_s": f"{runtime_s:.6f}",
        "timeout": str(proof.get("timeout", "false")),
        "failure_reason": failure_reason,
        "deterministic_seed": "0",
        "schema_version": SCHEMA_VERSION,
    }


def _longest_run(indices: list[int]) -> int:
    if not indices:
        return 0
    longest = current = 1
    for prev, nxt in zip(indices, indices[1:]):
        current = current + 1 if nxt == prev + 1 else 1
        longest = max(longest, current)
    return longest


def _delta(before: dict[str, str], after: dict[str, str], key: str) -> str:
    if key not in before or key not in after:
        return ""
    return str(int(after[key]) - int(before[key]))
