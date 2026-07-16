"""Exhaustive region-equivalence validation for direct semantic candidates."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass

from analyze_blif_matches import parse_blif
from semantic_ast import SemanticExpr
from semantic_patterns import exhaustive_bus_assignments
from semantic_simulation import gate_output_value


SEMANTIC_FORMAL_SCHEMA_VERSION = "semantic_formal_validation_v1"


@dataclass(frozen=True)
class FormalValidationConfig:
    max_scalar_bits: int = 12
    timeout_seconds: float = 10.0


def validate_candidate_exhaustive(
    *,
    blif_path,
    input_buses: list[dict[str, object]],
    output_bus: dict[str, object],
    expr: SemanticExpr,
    config: FormalValidationConfig | None = None,
) -> dict[str, str]:
    config = config or FormalValidationConfig()
    start = time.perf_counter()
    assignments, evidence = exhaustive_bus_assignments(input_buses, config.max_scalar_bits)
    if not assignments:
        return {
            "formal_status": "unsupported",
            "proof_scope": "region",
            "formal_evidence_level": "unresolved",
            "formal_patterns": "0",
            "counterexample_available": "false",
            "counterexample_assignment": "{}",
            "counterexample_output_difference": "",
            "counterexample_source": "",
            "formal_runtime": f"{time.perf_counter() - start:.6f}",
            "formal_skip_reason": evidence,
            "schema_version": SEMANTIC_FORMAL_SCHEMA_VERSION,
        }
    net = parse_blif(blif_path)
    for idx, assignment in enumerate(assignments):
        if time.perf_counter() - start > config.timeout_seconds:
            return {
                "formal_status": "timeout",
                "proof_scope": "region",
                "formal_evidence_level": "unresolved",
                "formal_patterns": str(idx),
                "counterexample_available": "false",
                "counterexample_assignment": "{}",
                "counterexample_output_difference": "",
                "counterexample_source": "",
                "formal_runtime": f"{time.perf_counter() - start:.6f}",
                "formal_skip_reason": "formal_timeout",
                "schema_version": SEMANTIC_FORMAL_SCHEMA_VERSION,
            }
        gate = gate_output_value(net, input_buses, output_bus, assignment)
        candidate = expr.eval(assignment)
        if gate != candidate:
            return {
                "formal_status": "disproven",
                "proof_scope": "region",
                "formal_evidence_level": "formal_exhaustive",
                "formal_patterns": str(len(assignments)),
                "counterexample_available": "true",
                "counterexample_assignment": json.dumps(assignment, sort_keys=True, separators=(",", ":")),
                "counterexample_output_difference": str(gate ^ candidate),
                "counterexample_source": "exhaustive_region_truth_table",
                "formal_runtime": f"{time.perf_counter() - start:.6f}",
                "formal_skip_reason": "",
                "schema_version": SEMANTIC_FORMAL_SCHEMA_VERSION,
            }
    return {
        "formal_status": "formally_verified_region",
        "proof_scope": "region",
        "formal_evidence_level": "formal_exhaustive",
        "formal_patterns": str(len(assignments)),
        "counterexample_available": "false",
        "counterexample_assignment": "{}",
        "counterexample_output_difference": "",
        "counterexample_source": "",
        "formal_runtime": f"{time.perf_counter() - start:.6f}",
        "formal_skip_reason": "",
        "schema_version": SEMANTIC_FORMAL_SCHEMA_VERSION,
    }
