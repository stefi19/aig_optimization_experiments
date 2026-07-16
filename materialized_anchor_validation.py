"""Formal validation for materialized-wire anchors."""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path

from analyze_blif_matches import BlifNetwork
from contextual_error_metrics import evaluate_network, exact_patterns
from odc_formal_validation import circuit_fingerprint


@dataclass(frozen=True)
class MaterializedAnchorProof:
    proof_status: str
    sat_result: str
    proof_runtime_seconds: float
    formal_backend: str
    target_polarity: str
    counterexample_available: bool
    counterexample_summary: str
    spec_fingerprint: str
    impl_fingerprint: str
    augmented_spec_fingerprint: str
    augmentation_preserves_original_outputs: bool
    failure_reason: str


def prove_materialized_anchor_exhaustive(
    original_spec: BlifNetwork,
    augmented_spec: BlifNetwork,
    impl: BlifNetwork,
    *,
    spec_path: Path,
    impl_path: Path,
    augmented_spec_path: Path,
    materialized_wire_name: str,
    target_impl_node: str,
    target_polarity: str = "positive",
    exact_input_limit: int = 12,
) -> MaterializedAnchorProof:
    start = time.perf_counter()
    spec_fp = circuit_fingerprint(spec_path, materialized_wire_name)
    impl_fp = circuit_fingerprint(impl_path, target_impl_node)
    aug_fp = circuit_fingerprint(augmented_spec_path, materialized_wire_name) if augmented_spec_path.exists() else ""
    reason = _validate_inputs(original_spec, augmented_spec, impl, materialized_wire_name, target_impl_node, target_polarity, exact_input_limit)
    if reason:
        return _result("unsupported" if "too_large" in reason else "alignment_failure", "not_run", start, target_polarity, False, "", spec_fp, impl_fp, aug_fp, False, reason)
    patterns = exact_patterns(list(original_spec.inputs))
    original_values = evaluate_network(original_spec, patterns)
    augmented_values = evaluate_network(augmented_spec, patterns)
    impl_values = evaluate_network(impl, patterns)
    preserves = all(original_values.get(out) == augmented_values.get(out) for out in original_spec.outputs)
    if not preserves:
        return _result("disproven", "augmentation_changed_outputs", start, target_polarity, True, "original primary outputs changed", spec_fp, impl_fp, aug_fp, False, "augmentation_changed_outputs")
    spec_bits = augmented_values.get(materialized_wire_name)
    impl_bits = impl_values.get(target_impl_node)
    if target_polarity == "inverted" and impl_bits is not None:
        impl_bits = (~impl_bits) & patterns.mask
    if spec_bits is None or impl_bits is None:
        return _result("alignment_failure", "not_run", start, target_polarity, False, "", spec_fp, impl_fp, aug_fp, preserves, "missing_evaluated_signal")
    if spec_bits == impl_bits:
        return _result("proven_materialized_anchor", "unsat_exhaustive", start, target_polarity, False, "", spec_fp, impl_fp, aug_fp, preserves, "")
    diff = spec_bits ^ impl_bits
    first = (diff & -diff).bit_length() - 1
    return _result("disproven", "sat_exhaustive", start, target_polarity, True, f"first_mismatch_pattern={first}", spec_fp, impl_fp, aug_fp, preserves, "formal_disproof")


def _validate_inputs(
    original_spec: BlifNetwork,
    augmented_spec: BlifNetwork,
    impl: BlifNetwork,
    materialized_wire_name: str,
    target_impl_node: str,
    target_polarity: str,
    exact_input_limit: int,
) -> str:
    if original_spec.inputs != impl.inputs or augmented_spec.inputs != original_spec.inputs:
        return "pi_mismatch"
    if original_spec.outputs != augmented_spec.outputs:
        return "original_output_order_changed"
    if len(original_spec.inputs) > exact_input_limit:
        return "support_too_large_without_sampling"
    if target_polarity not in {"positive", "inverted"}:
        return "unsupported_target_polarity"
    augmented_nodes = {node.output for node in augmented_spec.nodes}
    impl_nodes = {node.output for node in impl.nodes} | set(impl.outputs)
    if materialized_wire_name not in augmented_nodes:
        return "missing_materialized_wire"
    if target_impl_node not in impl_nodes:
        return "missing_target_impl_node"
    return ""


def proof_to_row(proof: MaterializedAnchorProof, *, case_id: str, benchmark: str, optimization: str, coi_name: str) -> dict[str, object]:
    return {
        "case_id": case_id,
        "benchmark": benchmark,
        "optimization": optimization,
        "coi_name": coi_name,
        "proof_status": proof.proof_status,
        "sat_result": proof.sat_result,
        "proof_runtime_seconds": f"{proof.proof_runtime_seconds:.6f}",
        "formal_backend": proof.formal_backend,
        "target_polarity": proof.target_polarity,
        "counterexample_available": proof.counterexample_available,
        "counterexample_summary": proof.counterexample_summary,
        "spec_fingerprint": proof.spec_fingerprint,
        "impl_fingerprint": proof.impl_fingerprint,
        "augmented_spec_fingerprint": proof.augmented_spec_fingerprint,
        "augmentation_preserves_original_outputs": proof.augmentation_preserves_original_outputs,
        "failure_reason": proof.failure_reason,
    }


def _result(
    status: str,
    sat_result: str,
    start: float,
    target_polarity: str,
    cex: bool,
    cex_summary: str,
    spec_fp: str,
    impl_fp: str,
    aug_fp: str,
    preserves: bool,
    reason: str,
) -> MaterializedAnchorProof:
    return MaterializedAnchorProof(
        proof_status=status,
        sat_result=sat_result,
        proof_runtime_seconds=time.perf_counter() - start,
        formal_backend="exhaustive_global_truth_table",
        target_polarity=target_polarity,
        counterexample_available=cex,
        counterexample_summary=cex_summary,
        spec_fingerprint=spec_fp,
        impl_fingerprint=impl_fp,
        augmented_spec_fingerprint=aug_fp,
        augmentation_preserves_original_outputs=preserves,
        failure_reason=reason,
    )
