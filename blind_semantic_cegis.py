"""Source-blind parametric semantic recovery and proof metadata.

This module is intentionally independent from the existing assisted direct
pipeline.  Prediction APIs accept only inference-schema objects; evaluation
metadata is joined by separate scripts after prediction files exist.
"""

from __future__ import annotations

import csv
import hashlib
import itertools
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from analyze_blif_matches import parse_blif
from semantic_ast import SemanticExpr, const_expr, input_expr
from semantic_formal_validation import FormalValidationConfig, validate_candidate_exhaustive
from semantic_region import write_csv
from semantic_simulation import gate_output_value
from semantic_types import SemanticType


SCHEMA_VERSION = "blind_semantic_cegis_v1"
PROOF_SCHEMA_VERSION = "blind_semantic_proof_v1"
EVALUATION_SCHEMA_VERSION = "blind_semantic_evaluation_v1"

GROUND_TRUTH_FIELDS = {
    "family",
    "operator",
    "ground_truth_expression",
    "ground_truth_input_buses",
    "ground_truth_output_buses",
    "ground_truth_signedness",
    "ground_truth_bus_name_if_known",
    "ground_truth_match",
    "ground_truth_family",
    "ground_truth_rank",
    "constants",
    "top_1_bus_match",
    "top_3_bus_match",
    "top_5_bus_match",
    "exact_bus_partition_match",
    "exact_ordered_bus_match",
    "bus_membership_precision",
    "bus_membership_recall",
    "bit_order_accuracy",
    "control_input_accuracy",
    "data_operand_accuracy",
    "output_bus_accuracy",
    "correct",
    "classification",
}

LEAKAGE_AUDIT_FIELDS = [
    "component",
    "field",
    "inference_time_access",
    "ground_truth_derived",
    "risk_level",
    "evidence",
    "blind_replacement",
    "schema_version",
]

BLIND_BUS_FIELDS = [
    "bus_hypothesis_id",
    "region_id",
    "direction",
    "rank",
    "role",
    "member_nodes",
    "ordered_member_nodes",
    "width",
    "bit_order",
    "signedness_hypothesis",
    "grouping_score",
    "ordering_score",
    "evidence_sources",
    "used_ground_truth_for_generation",
    "schema_version",
]

PARAMETRIC_CANDIDATE_FIELDS = [
    "candidate_id",
    "region_id",
    "template_family",
    "symbolic_parameters",
    "parameter_domains",
    "width_constraints",
    "signedness_constraints",
    "expression_depth",
    "search_cost",
    "canonical_form",
    "rtl_text",
    "inference_evidence",
    "generated_without_ground_truth",
    "expression_json",
    "schema_version",
]

CEGIS_ITERATION_FIELDS = [
    "candidate_id",
    "region_id",
    "iteration",
    "examples_before",
    "examples_after",
    "candidate_parameters",
    "candidate_expression",
    "solver_status",
    "counterexample_assignment",
    "output_difference",
    "synthesis_runtime",
    "verification_runtime",
    "final_proof_status",
    "termination_reason",
    "schema_version",
]

PROOF_FIELDS = [
    "candidate_id",
    "region_id",
    "formal_backend",
    "proof_scope",
    "formal_status",
    "formal_evidence_level",
    "solver_result",
    "counterexample_available",
    "counterexample_assignment",
    "proof_runtime",
    "timeout",
    "unsupported_reason",
    "schema_version",
]


@dataclass(frozen=True)
class BlindBus:
    name: str
    role: str
    ordered_member_nodes: tuple[str, ...]
    width: int
    signed: bool = False


def assert_inference_schema(row: dict[str, object], *, allow_labels: set[str] | None = None) -> None:
    """Reject ground-truth/evaluation fields before blind prediction."""

    allowed = allow_labels or set()
    leaked = sorted((set(row) & GROUND_TRUTH_FIELDS) - allowed)
    if leaked:
        raise ValueError(f"blind inference schema contains ground-truth fields: {', '.join(leaked)}")


def stable_anonymize(names: list[str]) -> dict[str, str]:
    """Deterministically anonymise names without using prefixes or bit syntax."""

    ordered = sorted(names, key=lambda n: (hashlib.sha256(n.encode("utf-8")).hexdigest(), n))
    return {name: f"s{idx:04d}" for idx, name in enumerate(ordered)}


def anonymize_expr_operands(expr: SemanticExpr, rename: dict[str, str]) -> SemanticExpr:
    if expr.operator == "input":
        return input_expr(rename.get(expr.name, expr.name), expr.width, expr.output_type.signed)
    return SemanticExpr(
        expr.operator,
        operands=tuple(anonymize_expr_operands(arg, rename) for arg in expr.operands),
        output_type=expr.output_type,
        name=rename.get(expr.name, expr.name),
        constant_value=expr.constant_value,
        slice_range=expr.slice_range,
        extension_mode=expr.extension_mode,
        truncation_mode=expr.truncation_mode,
    )


def blind_bus_hypotheses(region_id: str, direction: str, scalar_nodes: tuple[str, ...], *, anonymize: bool = True) -> list[dict[str, str]]:
    """Blind bus grouping based on interface position only.

    This conservative primary mode avoids source prefixes and truth bus names.
    Multi-bit runs are inferred from contiguous scalar interface positions with
    a fixed max run; singleton controls remain singletons.
    """

    names = list(scalar_nodes)
    rename = stable_anonymize(names) if anonymize else {n: n for n in names}
    # The circuit-node IDs remain the executable interface used by BLIF
    # evaluation.  Anonymised labels are used for hypothesis IDs and expression
    # operands by callers that need display-level anonymisation.
    executable = tuple(names)
    if not executable:
        return []
    # Prefer one word-level bus for multi-output/data interfaces, preserving
    # scalar interface order as the only bit-order evidence.
    groups: list[tuple[str, tuple[str, ...], str]] = []
    if direction == "output" or len(executable) > 2:
        groups.append((f"{direction}_bus0", executable, "output" if direction == "output" else "data_operand"))
    else:
        for idx, node in enumerate(executable):
            groups.append((f"{direction}_scalar{idx}", (node,), "control" if direction == "input" else "output"))
    rows: list[dict[str, str]] = []
    for rank, (name, members, role) in enumerate(groups, start=1):
        rows.append(
            {
                "bus_hypothesis_id": f"{region_id}__blind__{direction}__{rank:02d}",
                "region_id": region_id,
                "direction": direction,
                "rank": str(rank),
                "role": role,
                "member_nodes": json.dumps(list(members), separators=(",", ":")),
                "ordered_member_nodes": json.dumps(list(members), separators=(",", ":")),
                "width": str(len(members)),
                "bit_order": "interface_position_lsb_to_msb" if len(members) > 1 else "scalar",
                "signedness_hypothesis": "unknown",
                "grouping_score": "0.500000",
                "ordering_score": "0.500000" if len(members) > 1 else "1.000000",
                "evidence_sources": json.dumps(["interface_position", "structural_dependency_placeholder"], separators=(",", ":")),
                "used_ground_truth_for_generation": "false",
                "schema_version": SCHEMA_VERSION,
            }
        )
    return rows


def _expr(op: str, args: tuple[SemanticExpr, ...], width: int, *, constant: int | None = None, signed: bool = False) -> SemanticExpr:
    return SemanticExpr(op, operands=args, output_type=SemanticType("bitvector" if width > 1 else "boolean", width, signed), constant_value=constant)


def parametric_templates(input_buses: list[BlindBus], output_width: int, *, max_constant: int = 8, max_shift: int = 4) -> list[tuple[str, SemanticExpr, dict[str, object]]]:
    """Bounded, source-blind parametric template enumeration."""

    inputs = [input_expr(bus.name, bus.width, bus.signed) for bus in input_buses]
    rows: list[tuple[str, SemanticExpr, dict[str, object]]] = []
    for a in inputs:
        for alpha in range(0, max_constant + 1):
            rows.append(("constant_multiply", _expr("mul", (a, const_expr(alpha, output_width)), output_width), {"alpha": alpha}))
        for mask in {0, 1, (1 << min(output_width, 8)) - 1}:
            rows.append(("masked_boolean", _expr("mask_and", (a,), output_width, constant=mask), {"mask": mask}))
        for shift in range(1, min(max_shift, max(1, output_width - 1)) + 1):
            rows.append(("shift", _expr("shl", (a,), output_width, constant=shift), {"s": shift, "mode": "left"}))
            rows.append(("shift", _expr("lshr", (a,), output_width, constant=shift), {"s": shift, "mode": "right"}))
    for a, b in itertools.permutations(inputs, 2):
        rows.extend(
            [
                ("affine", _expr("add", (a, b), output_width), {"alpha": 1, "beta": 1, "gamma": 0}),
                ("affine", _expr("sub", (a, b), output_width), {"alpha": 1, "beta": -1, "gamma": 0}),
                ("truncated_multiply", _expr("mul", (a, b), output_width), {"mode": "low_bits"}),
            ]
        )
        for shift in range(1, min(max_shift, max(1, output_width - 1)) + 1):
            rows.append(("shifted_arithmetic", _expr("add", (_expr("shl", (a,), output_width, constant=shift), b), output_width), {"s": shift, "form": "(a<<s)+b"}))
            rows.append(("shifted_arithmetic", _expr("sub", (_expr("shl", (a,), output_width, constant=shift), b), output_width), {"s": shift, "form": "(a<<s)-b"}))
    for a, b, c in itertools.permutations(inputs, 3):
        rows.append(("add_add", _expr("add", (_expr("add", (a, b), output_width), c), output_width), {"permutation": [a.name, b.name, c.name]}))
        rows.append(("multiply_accumulate", _expr("add", (_expr("mul", (a, b), output_width), c), output_width), {"permutation": [a.name, b.name, c.name]}))
    seen: set[str] = set()
    unique = []
    for family, expr, params in rows:
        if expr.canonical_form in seen:
            continue
        seen.add(expr.canonical_form)
        unique.append((family, expr, params))
    return unique


def candidate_rows(region_id: str, input_buses: list[BlindBus], output_width: int, *, max_candidates: int = 128) -> list[dict[str, str]]:
    rows = []
    for idx, (family, expr, params) in enumerate(parametric_templates(input_buses, output_width)[:max_candidates], start=1):
        rows.append(
            {
                "candidate_id": f"{region_id}__blind_cegis__{idx:04d}",
                "region_id": region_id,
                "template_family": family,
                "symbolic_parameters": json.dumps(sorted(params), separators=(",", ":")),
                "parameter_domains": json.dumps({key: "bounded_enumeration" for key in params}, sort_keys=True, separators=(",", ":")),
                "width_constraints": f"output_width={output_width}",
                "signedness_constraints": "signedness_hole=unknown",
                "expression_depth": str(expr.expression_depth),
                "search_cost": str(expr.rtl_cost),
                "canonical_form": expr.canonical_form,
                "rtl_text": expr.rtl_text,
                "inference_evidence": json.dumps(["template_enumeration", "sampled_examples", "formal_counterexamples"], separators=(",", ":")),
                "generated_without_ground_truth": "true",
                "expression_json": json.dumps(expr.to_tree(), sort_keys=True, separators=(",", ":")),
                "schema_version": SCHEMA_VERSION,
            }
        )
    return rows


def _deterministic_examples(input_buses: list[BlindBus], *, count: int = 1) -> list[dict[str, int]]:
    domains = [range(1 << min(bus.width, 4)) for bus in input_buses]
    examples = []
    for values in itertools.islice(itertools.product(*domains), count):
        examples.append({bus.name: int(value) for bus, value in zip(input_buses, values)})
    return examples


def _verify_or_counterexample(blif_path: Path, input_buses: list[dict[str, object]], output_bus: dict[str, object], expr: SemanticExpr, max_bits: int) -> tuple[str, dict[str, int], int, dict[str, str]]:
    result = validate_candidate_exhaustive(
        blif_path=blif_path,
        input_buses=input_buses,
        output_bus=output_bus,
        expr=expr,
        config=FormalValidationConfig(max_scalar_bits=max_bits, timeout_seconds=10.0),
    )
    if result["formal_status"] == "formally_verified_region":
        return "unsat", {}, 0, result
    if result["counterexample_available"] == "true":
        assignment = json.loads(result["counterexample_assignment"])
        return "sat", {str(k): int(v) for k, v in assignment.items()}, int(result["counterexample_output_difference"] or 0), result
    return result["formal_status"], {}, 0, result


def cegis_recover(
    *,
    blif_path: Path,
    region_id: str,
    input_buses: list[dict[str, object]],
    output_bus: dict[str, object],
    max_iterations: int = 8,
    max_candidates: int = 128,
    max_scalar_bits: int = 12,
) -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, str]]]:
    """Real bounded CEGIS: counterexamples prune the next candidate."""

    blind_inputs = [BlindBus(str(bus["name"]), str(bus.get("role", "data_operand")), tuple(bus.get("ordered_member_nodes", ())), int(bus["width"])) for bus in input_buses]
    examples = _deterministic_examples(blind_inputs)
    candidates = candidate_rows(region_id, blind_inputs, int(output_bus["width"]), max_candidates=max_candidates)
    candidate_exprs = [(row, SemanticExpr(**{}) if False else None) for row in candidates]
    net = parse_blif(blif_path)
    iterations: list[dict[str, str]] = []
    proofs: list[dict[str, str]] = []
    rejected: set[str] = set()
    for iteration in range(1, max_iterations + 1):
        synth_start = time.perf_counter()
        selected: tuple[dict[str, str], SemanticExpr] | None = None
        for row, _ in candidate_exprs:
            if row["candidate_id"] in rejected:
                continue
            expr = SemanticExpr.from_tree(json.loads(row["expression_json"])) if hasattr(SemanticExpr, "from_tree") else None
            from semantic_ast import expr_from_tree

            expr = expr_from_tree(json.loads(row["expression_json"]))
            ok = True
            for ex in examples:
                if gate_output_value(net, input_buses, output_bus, ex) != expr.eval(ex):
                    ok = False
                    break
            if ok:
                selected = (row, expr)
                break
        synth_runtime = time.perf_counter() - synth_start
        if selected is None:
            iterations.append(_iteration_row(region_id, "", iteration, len(examples), len(examples), {}, "", "unsat_examples", {}, 0, synth_runtime, 0.0, "unresolved", "no_candidate_satisfies_examples"))
            break
        row, expr = selected
        verify_start = time.perf_counter()
        solver_status, cex, diff, formal = _verify_or_counterexample(blif_path, input_buses, output_bus, expr, max_scalar_bits)
        verify_runtime = time.perf_counter() - verify_start
        if solver_status == "unsat":
            iterations.append(_iteration_row(region_id, row["candidate_id"], iteration, len(examples), len(examples), json.loads(row["parameter_domains"]), row["canonical_form"], "unsat", {}, 0, synth_runtime, verify_runtime, "formally_verified_region", "equivalence_proven"))
            proofs.append(_proof_row(row["candidate_id"], region_id, "exhaustive", "region", "formally_verified_region", "formal_exhaustive", "unsat", {}, verify_runtime, "false", ""))
            break
        if solver_status == "sat":
            examples.append(cex)
            rejected.add(row["candidate_id"])
            iterations.append(_iteration_row(region_id, row["candidate_id"], iteration, len(examples) - 1, len(examples), json.loads(row["parameter_domains"]), row["canonical_form"], "sat", cex, diff, synth_runtime, verify_runtime, "unresolved", "counterexample_added"))
            continue
        iterations.append(_iteration_row(region_id, row["candidate_id"], iteration, len(examples), len(examples), {}, row["canonical_form"], solver_status, {}, 0, synth_runtime, verify_runtime, "unresolved", "unsupported_or_timeout"))
        proofs.append(_proof_row(row["candidate_id"], region_id, "exhaustive", "region", formal["formal_status"], formal["formal_evidence_level"], solver_status, {}, verify_runtime, "true" if formal["formal_status"] == "timeout" else "false", formal["formal_skip_reason"]))
        break
    return candidates, iterations, proofs


def _iteration_row(region_id: str, candidate_id: str, iteration: int, before: int, after: int, params: dict[str, object], expr: str, status: str, cex: dict[str, int], diff: int, synth_runtime: float, verify_runtime: float, final: str, reason: str) -> dict[str, str]:
    return {
        "candidate_id": candidate_id,
        "region_id": region_id,
        "iteration": str(iteration),
        "examples_before": str(before),
        "examples_after": str(after),
        "candidate_parameters": json.dumps(params, sort_keys=True, separators=(",", ":")),
        "candidate_expression": expr,
        "solver_status": status,
        "counterexample_assignment": json.dumps(cex, sort_keys=True, separators=(",", ":")),
        "output_difference": str(diff),
        "synthesis_runtime": f"{synth_runtime:.6f}",
        "verification_runtime": f"{verify_runtime:.6f}",
        "final_proof_status": final,
        "termination_reason": reason,
        "schema_version": SCHEMA_VERSION,
    }


def _proof_row(candidate_id: str, region_id: str, backend: str, scope: str, status: str, evidence: str, solver: str, cex: dict[str, int], runtime: float, timeout: str, unsupported: str) -> dict[str, str]:
    return {
        "candidate_id": candidate_id,
        "region_id": region_id,
        "formal_backend": backend,
        "proof_scope": scope,
        "formal_status": status,
        "formal_evidence_level": evidence,
        "solver_result": solver,
        "counterexample_available": str(bool(cex)).lower(),
        "counterexample_assignment": json.dumps(cex, sort_keys=True, separators=(",", ":")),
        "proof_runtime": f"{runtime:.6f}",
        "timeout": timeout,
        "unsupported_reason": unsupported,
        "schema_version": PROOF_SCHEMA_VERSION,
    }


def write_leakage_audit(root: Path, out_dir: Path) -> list[dict[str, str]]:
    patterns = sorted(GROUND_TRUTH_FIELDS)
    components = ["semantic_direct_recovery.py", "semantic_grammar.py", "semantic_family_ranking.py", "scripts/generate_semantic_direct_candidates.py", "scripts/rank_semantic_families.py", "scripts/infer_semantic_buses.py"]
    rows: list[dict[str, str]] = []
    for component in components:
        text = (root / component).read_text(encoding="utf-8")
        for field in patterns:
            if field in text:
                inference = component not in {"scripts/infer_semantic_buses.py"} or field in {"ground_truth_bus_name_if_known", "constants", "family", "operator", "bit_order_accuracy", "control_input_accuracy", "data_operand_accuracy", "output_bus_accuracy"}
                rows.append(
                    {
                        "component": component,
                        "field": field,
                        "inference_time_access": str(inference).lower(),
                        "ground_truth_derived": "true",
                        "risk_level": "high" if inference else "evaluation_only",
                        "evidence": f"literal field reference `{field}`",
                        "blind_replacement": "blind inference schema rejects this field before prediction",
                        "schema_version": SCHEMA_VERSION,
                    }
                )
    out_dir.mkdir(parents=True, exist_ok=True)
    write_csv(rows, out_dir / "leakage_audit.csv", LEAKAGE_AUDIT_FIELDS)
    high = sum(1 for row in rows if row["risk_level"] == "high")
    (out_dir / "leakage_audit_summary.md").write_text(
        "# Blind Semantic CEGIS Leakage Audit\n\n"
        f"- Audited components: {len(components)}\n"
        f"- Ground-truth-derived references found: {len(rows)}\n"
        f"- Inference-time high-risk references in the existing assisted pipeline: {high}\n\n"
        "The new blind pipeline uses `assert_inference_schema` and writes predictions before evaluation-only joins. "
        "Existing assisted/oracle outputs are retained as ablations and are not reported as primary blind evidence.\n",
        encoding="utf-8",
    )
    return rows


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))
