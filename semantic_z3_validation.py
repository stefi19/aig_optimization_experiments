"""Region miter validation using Z3 bit-vector semantics."""

from __future__ import annotations

import json
import time
from pathlib import Path

try:  # pragma: no cover
    import z3
except Exception:  # pragma: no cover
    z3 = None  # type: ignore[assignment]

from blif_z3 import encode_blif, model_bus_assignment, pack_bus, provenance_row
from semantic_ast import SemanticExpr
from semantic_simulation import gate_output_value
from semantic_z3 import expr_to_z3


SEMANTIC_Z3_SCHEMA_VERSION = "semantic_z3_validation_v1"


def validate_candidate_z3(
    *,
    blif_path: Path,
    input_buses: list[dict[str, object]],
    output_bus: dict[str, object],
    expr: SemanticExpr,
    timeout_ms: int = 5000,
) -> dict[str, str]:
    start = time.perf_counter()
    if z3 is None:
        return _row("unsupported", "unresolved", "unknown", {}, 0.0, "z3_not_installed", start, "false")
    try:
        encoded = encode_blif(blif_path)
        env = {str(bus["name"]): pack_bus(encoded.values, tuple(bus.get("ordered_member_nodes", ()))) for bus in input_buses}
        gate = pack_bus(encoded.values, tuple(output_bus.get("ordered_member_nodes", ())))
        candidate = expr_to_z3(expr, env)
        candidate = candidate if candidate.size() == gate.size() else candidate
        solver = z3.Solver()
        solver.set("timeout", timeout_ms)
        solver.set("random_seed", 0)
        solver.add(gate != candidate)
        check_start = time.perf_counter()
        result = solver.check()
        runtime = time.perf_counter() - start
        if result == z3.unsat:
            return _row("formally_verified_region", "formal_smt", "unsat", {}, runtime, "", start, "false")
        if result == z3.sat:
            model = solver.model()
            assignment = model_bus_assignment(model, input_buses, encoded)
            gate_value = gate_output_value(encoded.net, input_buses, output_bus, assignment)
            expr_value = expr.eval(assignment)
            return {
                **_row("disproven", "formal_smt", "sat", assignment, runtime, "", start, "false"),
                "counterexample_output_difference": str(gate_value ^ expr_value),
                "counterexample_reproduced": str(gate_value != expr_value).lower(),
            }
        return _row("timeout", "unresolved", "unknown", {}, runtime, "z3_timeout_or_unknown", start, "true")
    except Exception as exc:
        return _row("unsupported", "unresolved", "error", {}, time.perf_counter() - start, f"{type(exc).__name__}:{exc}", start, "false")


def _row(status: str, evidence: str, solver_result: str, assignment: dict[str, int], runtime: float, reason: str, start: float, timeout: str) -> dict[str, str]:
    return {
        "formal_backend": "z3",
        "proof_scope": "region",
        "formal_status": status,
        "formal_evidence_level": evidence,
        "solver_result": solver_result,
        "counterexample_available": str(bool(assignment)).lower(),
        "counterexample_assignment": json.dumps(assignment, sort_keys=True, separators=(",", ":")),
        "counterexample_output_difference": "",
        "counterexample_reproduced": str(not assignment).lower(),
        "proof_runtime": f"{runtime:.6f}",
        "timeout": timeout,
        "unsupported_reason": reason,
        "z3_version": provenance_row()["z3_version"],
        "schema_version": SEMANTIC_Z3_SCHEMA_VERSION,
    }
