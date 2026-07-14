#!/usr/bin/env python3
"""Context-aware error metrics for internal-node correspondence experiments."""

from __future__ import annotations

import hashlib
import random
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from analyze_blif_matches import BlifNetwork, BlifNode, eval_cover, parse_blif


@dataclass(frozen=True)
class PatternSet:
    values: dict[str, int]
    mask: int
    pattern_count: int
    mode: str
    seed: int


@dataclass(frozen=True)
class OutputMetrics:
    contextual_output_error_rate: float
    mean_output_hamming_distance: float
    worst_case_output_hamming_distance: int
    mean_absolute_output_error: float
    worst_case_absolute_output_error: int


@dataclass(frozen=True)
class SubstitutionResult:
    status: str
    reason: str
    network: BlifNetwork | None


LEGACY_CATEGORY_MAP = {
    "exact": "exact_signature_match",
    "exact_anchor": "exact_signature_match",
    "exact signature match": "exact_signature_match",
    "complemented": "complemented_equivalence",
    "complemented match": "complemented_equivalence",
    "complemented equivalence": "complemented_equivalence",
    "sat_verified_nonexact": "sat_cec_proven_equivalent",
    "sat_verified_non_exact": "sat_cec_proven_equivalent",
    "sat verified non-exact": "sat_cec_proven_equivalent",
    "sat verified non exact": "sat_cec_proven_equivalent",
    "sat-verified non-exact": "sat_cec_proven_equivalent",
    "sat/cec-proven equivalent after structural mismatch": "sat_cec_proven_equivalent",
    "approximate_near_match": "global_approximate_near_match",
    "global approximate near-match": "global_approximate_near_match",
    "odc_valid_contextual": "odc_valid_correspondence",
    "contextually_approximate": "contextually_approximate_sampled",
}

CATEGORY_DISPLAY_LABELS = {
    "exact_signature_match": "Signature match",
    "complemented_equivalence": "Complemented equivalence",
    "sat_cec_proven_equivalent": "SAT/CEC-proven equivalent",
    "odc_valid_correspondence": "ODC-valid contextual",
    "contextually_approximate_exact": "Exact contextual approximation",
    "contextually_approximate_sampled": "Sampled contextual approximation",
    "global_approximate_near_match": "Global approximate near-match",
    "globally_exact": "Globally exact",
    "unsafe_candidate": "Unsafe",
    "unresolved": "Unresolved",
}


def normalize_mapping_category(category: object) -> str:
    text = str(category or "").strip()
    lowered = re.sub(r"\s+", " ", text.lower().replace("_", " ")).strip()
    underscore = lowered.replace(" ", "_").replace("-", "_")
    return LEGACY_CATEGORY_MAP.get(text, LEGACY_CATEGORY_MAP.get(lowered, LEGACY_CATEGORY_MAP.get(underscore, text)))


def category_display_label(category: object) -> str:
    normalized = normalize_mapping_category(category)
    return CATEGORY_DISPLAY_LABELS.get(normalized, normalized.replace("_", " "))


def contextual_evidence_level(classification: str, contextual_formal: bool, cec_status: str) -> str:
    classification = normalize_mapping_category(classification)
    if classification == "odc_valid_correspondence":
        return "formal_cec"
    if classification in {"globally_exact", "contextually_approximate_exact"}:
        return "formal_exhaustive" if contextual_formal else "unresolved"
    if classification in {"contextually_approximate_sampled", "unsafe_candidate"}:
        return "formal_exhaustive" if contextual_formal else "sampled_estimate"
    if cec_status == "verified_equivalent":
        return "formal_cec"
    return "unresolved"


def stable_seed(seed: int, key: str) -> int:
    digest = hashlib.sha256(f"{seed}|{key}".encode("utf-8")).hexdigest()
    return int(digest[:16], 16)


def exact_patterns(inputs: list[str]) -> PatternSet:
    pattern_count = 1 << len(inputs)
    mask = (1 << pattern_count) - 1
    values: dict[str, int] = {}
    for input_index, name in enumerate(inputs):
        bits = 0
        for assignment in range(pattern_count):
            if (assignment >> input_index) & 1:
                bits |= 1 << assignment
        values[name] = bits
    return PatternSet(values=values, mask=mask, pattern_count=pattern_count, mode="exact", seed=0)


def sampled_patterns(inputs: list[str], sample_count: int, seed: int, key: str = "") -> PatternSet:
    rng = random.Random(stable_seed(seed, key))
    mask = (1 << sample_count) - 1
    values = {name: 0 for name in inputs}
    for pattern_index in range(sample_count):
        for name in inputs:
            if rng.getrandbits(1):
                values[name] |= 1 << pattern_index
    return PatternSet(values=values, mask=mask, pattern_count=sample_count, mode="sampled", seed=seed)


def choose_patterns(inputs: list[str], exact_support_cap: int, sample_count: int, seed: int, key: str = "") -> PatternSet:
    if len(inputs) <= exact_support_cap:
        return exact_patterns(inputs)
    return sampled_patterns(inputs, sample_count, seed, key)


def evaluate_network(net: BlifNetwork, patterns: PatternSet) -> dict[str, int]:
    values = dict(patterns.values)
    for node in net.nodes:
        values[node.output] = eval_cover(node, values, patterns.mask)
    return values


def hamming_distance_rate(a: int, b: int, pattern_count: int) -> float:
    if pattern_count <= 0:
        return 0.0
    return (a ^ b).bit_count() / pattern_count


def output_numeric_value(bits: Iterable[int]) -> int:
    value = 0
    for index, bit in enumerate(bits):
        if bit:
            value |= 1 << index
    return value


def output_metrics(
    baseline_outputs: list[int],
    substituted_outputs: list[int],
    pattern_count: int,
) -> OutputMetrics:
    if len(baseline_outputs) != len(substituted_outputs):
        raise ValueError("output vectors must have the same length")
    if pattern_count <= 0:
        return OutputMetrics(0.0, 0.0, 0, 0.0, 0)

    differing_input_count = 0
    total_hamming = 0
    worst_hamming = 0
    total_abs = 0
    worst_abs = 0

    for pattern_index in range(pattern_count):
        baseline_bits = [(value >> pattern_index) & 1 for value in baseline_outputs]
        substituted_bits = [(value >> pattern_index) & 1 for value in substituted_outputs]
        hamming = sum(a != b for a, b in zip(baseline_bits, substituted_bits))
        if hamming:
            differing_input_count += 1
        total_hamming += hamming
        worst_hamming = max(worst_hamming, hamming)
        abs_error = abs(output_numeric_value(baseline_bits) - output_numeric_value(substituted_bits))
        total_abs += abs_error
        worst_abs = max(worst_abs, abs_error)

    return OutputMetrics(
        contextual_output_error_rate=differing_input_count / pattern_count,
        mean_output_hamming_distance=total_hamming / pattern_count,
        worst_case_output_hamming_distance=worst_hamming,
        mean_absolute_output_error=total_abs / pattern_count,
        worst_case_absolute_output_error=worst_abs,
    )


def find_node(net: BlifNetwork, output: str) -> BlifNode | None:
    for node in net.nodes:
        if node.output == output:
            return node
    return None


def prefixed_name(prefix: str, name: str) -> str:
    return f"{prefix}{name}" if name else name


def clone_candidate_cone(
    original: BlifNetwork,
    candidate_node: str,
    target_output: str,
    optimized_inputs: set[str],
    forbidden_names: set[str] | None = None,
    prefix: str = "__ctx_orig_",
) -> tuple[list[BlifNode], str, str]:
    """Clone the candidate's transitive fanin cone into an optimized network context."""
    by_output = {node.output: node for node in original.nodes}
    if candidate_node not in by_output:
        return [], "", f"candidate node {candidate_node!r} missing from original network"

    cloned: list[BlifNode] = []
    visiting: set[str] = set()
    visited: set[str] = set()
    forbidden = set(forbidden_names or set())

    def visit(signal: str) -> str:
        if signal in optimized_inputs:
            return signal
        if signal not in by_output:
            raise ValueError(f"candidate dependency {signal!r} is not a primary input or original node")
        if signal in visiting:
            raise ValueError(f"cycle detected while cloning {signal!r}")
        if signal in visited:
            return prefixed_name(prefix, signal)
        visiting.add(signal)
        node = by_output[signal]
        mapped_inputs = [visit(fanin) for fanin in node.inputs]
        cloned_output = prefixed_name(prefix, signal)
        if cloned_output in forbidden:
            raise ValueError(f"cloned candidate-cone node {cloned_output!r} collides with optimized network name")
        cloned.append(BlifNode(output=cloned_output, inputs=mapped_inputs, cover=list(node.cover)))
        visiting.remove(signal)
        visited.add(signal)
        return cloned_output

    cloned_candidate = visit(candidate_node)
    replacement = BlifNode(output=target_output, inputs=[cloned_candidate], cover=["1 1"])
    return cloned + [replacement], target_output, ""


def substitute_candidate(
    optimized: BlifNetwork,
    original: BlifNetwork,
    optimized_node: str,
    candidate_original_node: str,
) -> SubstitutionResult:
    """Return optimized network with `optimized_node` replaced by candidate's original cone."""
    if not optimized.outputs:
        return SubstitutionResult("skipped", "optimized circuit has no primary outputs", None)
    if len(set(optimized.outputs)) != len(optimized.outputs):
        return SubstitutionResult("skipped", "optimized primary output names are not unique", None)
    if optimized_node in optimized.inputs:
        return SubstitutionResult("skipped", "optimized node is a primary input", None)
    if optimized_node in optimized.outputs:
        return SubstitutionResult("skipped", "optimized node is a primary output; direct output rewiring is not supported", None)
    if find_node(optimized, optimized_node) is None:
        return SubstitutionResult("skipped", f"optimized node {optimized_node!r} missing", None)
    if find_node(original, candidate_original_node) is None:
        return SubstitutionResult("skipped", f"candidate original node {candidate_original_node!r} missing", None)
    if optimized.inputs != original.inputs:
        return SubstitutionResult("skipped", "primary input ordering differs between original and optimized networks", None)
    existing_names = set(optimized.inputs) | set(optimized.outputs) | {node.output for node in optimized.nodes}
    existing_names.discard(optimized_node)

    try:
        cloned_nodes, _, reason = clone_candidate_cone(
            original,
            candidate_original_node,
            optimized_node,
            set(optimized.inputs),
            existing_names,
        )
    except ValueError as exc:
        return SubstitutionResult("skipped", str(exc), None)
    if reason:
        return SubstitutionResult("skipped", reason, None)

    new_nodes: list[BlifNode] = []
    inserted = False
    for node in optimized.nodes:
        if node.output == optimized_node:
            new_nodes.extend(cloned_nodes)
            inserted = True
        else:
            new_nodes.append(BlifNode(output=node.output, inputs=list(node.inputs), cover=list(node.cover)))
    if not inserted:
        return SubstitutionResult("skipped", f"optimized node {optimized_node!r} was not replaced", None)
    substituted = BlifNetwork(inputs=list(optimized.inputs), outputs=list(optimized.outputs), nodes=new_nodes)
    if substituted.outputs != optimized.outputs:
        return SubstitutionResult("skipped", "optimized primary output ordering changed during substitution", None)
    return SubstitutionResult(
        "ok",
        "substitution constructed",
        substituted,
    )


def write_blif(net: BlifNetwork, path: Path, model_name: str = "contextual") -> None:
    lines = [f".model {model_name}", ".inputs " + " ".join(net.inputs), ".outputs " + " ".join(net.outputs)]
    for node in net.nodes:
        lines.append(".names " + " ".join([*node.inputs, node.output]))
        lines.extend(node.cover)
    lines.append(".end")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_abc_cec(output: str, exit_code: int = 0) -> str:
    lowered = output.lower()
    if "networks are equivalent" in lowered or "equivalent after" in lowered:
        return "verified_equivalent"
    if re.search(r"not equivalent|are not equivalent|cex|counter-example", lowered):
        return "rejected_non_equivalent"
    if exit_code != 0:
        return "inconclusive"
    return "inconclusive"


def run_abc_cec(abc_bin: str | None, baseline: Path, substituted: Path, timeout: int = 20) -> tuple[str, str]:
    if not abc_bin:
        return "not_run", "ABC binary unavailable"
    try:
        completed = subprocess.run(
            [abc_bin, "-c", f"cec {baseline} {substituted}"],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return "inconclusive", str(exc)
    output = (completed.stdout or "") + "\n" + (completed.stderr or "")
    snippet = " ".join(output.split())
    snippet = snippet.replace(str(baseline), "<baseline_blif>").replace(str(substituted), "<substituted_blif>")
    home_pattern = re.escape(str(Path.home())) + r"/\S+"
    private_tmp = re.escape("/private" + "/var") + r"/\S+"
    var_tmp = re.escape("/var" + "/folders") + r"/\S+"
    snippet = re.sub(private_tmp + "|" + var_tmp + "|" + home_pattern, "<local_path>", snippet)
    return parse_abc_cec(output, completed.returncode), snippet[:500]


def classify_candidate(
    global_error_rate: float | None,
    global_formal: bool,
    contextual_error_rate: float | None,
    contextual_formal: bool,
    cec_status: str,
    threshold: float,
    substitution_status: str = "ok",
) -> str:
    if substitution_status != "ok":
        return "unresolved"
    if global_error_rate is None or contextual_error_rate is None:
        return "unresolved"
    if global_error_rate == 0 and global_formal:
        return "globally_exact"
    if global_error_rate > 0 and cec_status == "verified_equivalent":
        return "odc_valid_correspondence"
    if cec_status == "rejected_non_equivalent" and contextual_error_rate <= threshold:
        if contextual_formal:
            return "contextually_approximate_exact"
        return "contextually_approximate_sampled"
    if contextual_error_rate > threshold:
        return "unsafe_candidate"
    return "unresolved"


def evaluate_contextual_pair(
    original_path: Path,
    optimized_path: Path,
    optimized_node: str,
    candidate_original_node: str,
    exact_support_cap: int,
    sample_count: int,
    seed: int,
    threshold: float,
) -> tuple[dict[str, object], BlifNetwork | None, BlifNetwork | None]:
    original = parse_blif(original_path)
    optimized = parse_blif(optimized_path)
    if optimized.inputs != original.inputs:
        reason = "primary inputs differ between original and optimized networks"
        return {
            "substitution_status": "skipped",
            "reason": reason,
            "classification": "unresolved",
            "evidence_level": "unresolved",
        }, None, None

    substitution = substitute_candidate(optimized, original, optimized_node, candidate_original_node)
    if substitution.status != "ok" or substitution.network is None:
        return {
            "substitution_status": substitution.status,
            "reason": substitution.reason,
            "classification": "unresolved",
            "evidence_level": "unresolved",
        }, optimized, None

    key = f"{optimized_path}|{optimized_node}|{candidate_original_node}"
    patterns = choose_patterns(optimized.inputs, exact_support_cap, sample_count, seed, key)
    original_patterns = patterns
    baseline_values = evaluate_network(optimized, patterns)
    substituted_values = evaluate_network(substitution.network, patterns)
    original_values = evaluate_network(original, original_patterns)

    if optimized_node not in baseline_values:
        reason = f"optimized node {optimized_node!r} missing after evaluation"
        return {"substitution_status": "skipped", "reason": reason, "classification": "unresolved", "evidence_level": "unresolved"}, optimized, substitution.network
    if candidate_original_node not in original_values:
        reason = f"candidate node {candidate_original_node!r} missing after evaluation"
        return {"substitution_status": "skipped", "reason": reason, "classification": "unresolved", "evidence_level": "unresolved"}, optimized, substitution.network
    missing_outputs = [name for name in optimized.outputs if name not in baseline_values or name not in substituted_values]
    if missing_outputs:
        reason = f"missing primary output values: {', '.join(missing_outputs)}"
        return {"substitution_status": "skipped", "reason": reason, "classification": "unresolved", "evidence_level": "unresolved"}, optimized, substitution.network

    global_error = hamming_distance_rate(
        baseline_values[optimized_node],
        original_values[candidate_original_node],
        patterns.pattern_count,
    )
    metrics = output_metrics(
        [baseline_values[name] for name in optimized.outputs],
        [substituted_values[name] for name in optimized.outputs],
        patterns.pattern_count,
    )
    classification = classify_candidate(
        global_error,
        patterns.mode == "exact",
        metrics.contextual_output_error_rate,
        patterns.mode == "exact",
        "not_run",
        threshold,
        "ok",
    )
    return {
        "global_error_rate": global_error,
        "global_error_mode": patterns.mode,
        "global_pattern_count": patterns.pattern_count,
        "contextual_output_error_rate": metrics.contextual_output_error_rate,
        "contextual_error_mode": patterns.mode,
        "contextual_pattern_count": patterns.pattern_count,
        "mean_output_hamming_distance": metrics.mean_output_hamming_distance,
        "worst_case_output_hamming_distance": metrics.worst_case_output_hamming_distance,
        "mean_absolute_output_error": metrics.mean_absolute_output_error,
        "worst_case_absolute_output_error": metrics.worst_case_absolute_output_error,
        "is_formal_global": patterns.mode == "exact",
        "is_formal_contextual": patterns.mode == "exact",
        "substitution_status": "ok",
        "reason": "substitution constructed; CEC not run yet",
        "classification": classification,
        "evidence_level": contextual_evidence_level(classification, patterns.mode == "exact", "not_run"),
        "seed": seed,
    }, optimized, substitution.network
