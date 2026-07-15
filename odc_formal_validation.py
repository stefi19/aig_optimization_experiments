"""Formal ODC-aware contextual interchangeability checks.

The proof compares an implementation circuit against a copy where one
implementation node is replaced by a specification node cone.  ABC CEC proves
whether the selected observable outputs remain unchanged.  A proven result is
contextual only; it is not global node equivalence.
"""

from __future__ import annotations

import hashlib
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

from analyze_blif_matches import BlifNetwork, BlifNode, parse_blif
from contextual_error_metrics import run_abc_cec, substitute_candidate, write_blif


@dataclass(frozen=True)
class OdcProofResult:
    status: str
    sat_result: str
    runtime_seconds: float
    proof_mode: str
    context_mode: str
    observable_outputs: tuple[str, ...]
    spec_fingerprint: str
    impl_fingerprint: str
    failure_reason: str
    cec_output_snippet: str


def circuit_fingerprint(path: Path, node: str = "") -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    digest.update(b"\0")
    digest.update(node.encode("utf-8"))
    return digest.hexdigest()[:16]


def prove_contextual_interchangeability(
    spec_circuit: Path,
    impl_circuit: Path,
    spec_node: str,
    impl_node: str,
    polarity: str,
    context_mode: str,
    observable_outputs: tuple[str, ...],
    timeout_seconds: int,
    abc_bin: str | None,
) -> OdcProofResult:
    start = time.perf_counter()
    spec_fp = circuit_fingerprint(spec_circuit, spec_node)
    impl_fp = circuit_fingerprint(impl_circuit, impl_node)
    if polarity not in {"positive", "inverted"}:
        return _result("unsupported", "not_run", start, context_mode, observable_outputs, spec_fp, impl_fp, "unsupported_polarity", "")
    if context_mode not in {"global_output_odc", "coi_output_odc"}:
        return _result("unsupported", "not_run", start, context_mode, observable_outputs, spec_fp, impl_fp, "invalid_context", "")
    try:
        spec = parse_blif(spec_circuit)
        impl = parse_blif(impl_circuit)
    except Exception as exc:  # pragma: no cover - defensive against malformed inputs
        return _result("tool_error", "not_run", start, context_mode, observable_outputs, spec_fp, impl_fp, f"parse_error:{exc}", "")
    alignment = validate_alignment(spec, impl, spec_node, impl_node, observable_outputs)
    if alignment:
        return _result("alignment_failure", "not_run", start, context_mode, observable_outputs, spec_fp, impl_fp, alignment, "")
    substitution = substitute_candidate(impl, spec, impl_node, spec_node)
    if substitution.status != "ok" or substitution.network is None:
        return _result("unsupported", "not_run", start, context_mode, observable_outputs, spec_fp, impl_fp, substitution.reason, "")
    substituted = apply_polarity(substitution.network, impl_node, polarity)
    baseline = restrict_outputs(impl, observable_outputs)
    candidate = restrict_outputs(substituted, observable_outputs)
    with tempfile.TemporaryDirectory(prefix="odc_formal_") as tmp:
        tmpdir = Path(tmp)
        baseline_path = tmpdir / "baseline.blif"
        candidate_path = tmpdir / "candidate.blif"
        write_blif(baseline, baseline_path, model_name="odc_baseline")
        write_blif(candidate, candidate_path, model_name="odc_candidate")
        cec_status, snippet = run_abc_cec(abc_bin, baseline_path, candidate_path, timeout=timeout_seconds)
    if cec_status == "verified_equivalent":
        status = "proven_odc_valid"
    elif cec_status == "rejected_non_equivalent":
        status = "disproven"
    elif cec_status == "not_run":
        status = "tool_error"
    else:
        status = "timeout" if "timed out" in snippet.lower() else "tool_error"
    return _result(status, cec_status, start, context_mode, observable_outputs, spec_fp, impl_fp, "" if status == "proven_odc_valid" else cec_status, snippet)


def prove_boundary_contextual_interchangeability(
    spec_circuit: Path,
    impl_circuit: Path,
    replacements: tuple[tuple[str, str, str], ...],
    context_mode: str,
    observable_outputs: tuple[str, ...],
    timeout_seconds: int,
    abc_bin: str | None,
) -> OdcProofResult:
    """Prove all selected ODC replacements preserve observable outputs together.

    ``replacements`` contains ``(spec_node, impl_node, polarity)`` tuples.
    """

    start = time.perf_counter()
    spec_fp = circuit_fingerprint(spec_circuit, "boundary")
    impl_fp = circuit_fingerprint(impl_circuit, "boundary")
    if not replacements:
        return _result("unsupported", "not_run", start, context_mode, observable_outputs, spec_fp, impl_fp, "no_replacements", "")
    try:
        spec = parse_blif(spec_circuit)
        modified = parse_blif(impl_circuit)
        baseline = parse_blif(impl_circuit)
    except Exception as exc:  # pragma: no cover
        return _result("tool_error", "not_run", start, context_mode, observable_outputs, spec_fp, impl_fp, f"parse_error:{exc}", "")
    for spec_node, impl_node, polarity in replacements:
        alignment = validate_alignment(spec, modified, spec_node, impl_node, observable_outputs)
        if alignment:
            return _result("alignment_failure", "not_run", start, context_mode, observable_outputs, spec_fp, impl_fp, alignment, "")
        substitution = substitute_candidate(modified, spec, impl_node, spec_node)
        if substitution.status != "ok" or substitution.network is None:
            return _result("unsupported", "not_run", start, context_mode, observable_outputs, spec_fp, impl_fp, substitution.reason, "")
        modified = apply_polarity(substitution.network, impl_node, polarity)
    with tempfile.TemporaryDirectory(prefix="odc_boundary_") as tmp:
        tmpdir = Path(tmp)
        baseline_path = tmpdir / "baseline.blif"
        candidate_path = tmpdir / "candidate.blif"
        write_blif(restrict_outputs(baseline, observable_outputs), baseline_path, model_name="odc_boundary_baseline")
        write_blif(restrict_outputs(modified, observable_outputs), candidate_path, model_name="odc_boundary_candidate")
        cec_status, snippet = run_abc_cec(abc_bin, baseline_path, candidate_path, timeout=timeout_seconds)
    if cec_status == "verified_equivalent":
        status = "proven_odc_valid"
    elif cec_status == "rejected_non_equivalent":
        status = "disproven"
    elif cec_status == "not_run":
        status = "tool_error"
    else:
        status = "timeout" if "timed out" in snippet.lower() else "tool_error"
    return _result(status, cec_status, start, context_mode, observable_outputs, spec_fp, impl_fp, "" if status == "proven_odc_valid" else cec_status, snippet)


def validate_alignment(spec: BlifNetwork, impl: BlifNetwork, spec_node: str, impl_node: str, observable_outputs: tuple[str, ...]) -> str:
    if spec.inputs != impl.inputs:
        return "pi_mismatch"
    spec_nodes = {node.output for node in spec.nodes}
    impl_nodes = {node.output for node in impl.nodes}
    if spec_node not in spec_nodes:
        return "missing_node:spec"
    if impl_node not in impl_nodes:
        return "missing_node:impl"
    if impl_node in impl.inputs:
        return "unsupported_impl_primary_input"
    if impl_node in impl.outputs:
        return "unsupported_impl_primary_output"
    missing_outputs = [out for out in observable_outputs if out not in impl.outputs]
    if missing_outputs:
        return "missing_observable_output:" + ";".join(sorted(missing_outputs))
    return ""


def restrict_outputs(net: BlifNetwork, outputs: tuple[str, ...]) -> BlifNetwork:
    return BlifNetwork(inputs=list(net.inputs), outputs=list(outputs), nodes=[BlifNode(node.output, list(node.inputs), list(node.cover)) for node in net.nodes])


def apply_polarity(net: BlifNetwork, impl_node: str, polarity: str) -> BlifNetwork:
    if polarity == "positive":
        return net
    nodes: list[BlifNode] = []
    for node in net.nodes:
        if node.output == impl_node and len(node.inputs) == 1 and node.cover == ["1 1"]:
            nodes.append(BlifNode(node.output, list(node.inputs), ["0 1"]))
        else:
            nodes.append(BlifNode(node.output, list(node.inputs), list(node.cover)))
    return BlifNetwork(inputs=list(net.inputs), outputs=list(net.outputs), nodes=nodes)


def _result(
    status: str,
    sat_result: str,
    start: float,
    context_mode: str,
    observable_outputs: tuple[str, ...],
    spec_fingerprint: str,
    impl_fingerprint: str,
    failure_reason: str,
    snippet: str,
) -> OdcProofResult:
    return OdcProofResult(
        status=status,
        sat_result=sat_result,
        runtime_seconds=time.perf_counter() - start,
        proof_mode="abc_cec_contextual_miter",
        context_mode=context_mode,
        observable_outputs=tuple(observable_outputs),
        spec_fingerprint=spec_fingerprint,
        impl_fingerprint=impl_fingerprint,
        failure_reason=failure_reason,
        cec_output_snippet=snippet,
    )
