"""Per-input sensitivity signatures for BLIF internal nodes."""

from __future__ import annotations

import math
import statistics
from dataclasses import dataclass
from pathlib import Path

from boolean_difference import boolean_difference_probability, entropy
from functional_signal_utils import load_aligned_networks, structural_supports


@dataclass(frozen=True)
class SensitivityProfile:
    status: str
    skipped_reason: str
    mode: str
    evidence_level: str
    pattern_count: int
    seed: int
    support_size: int
    probabilities: dict[str, float]
    dominant_variable: str
    max_sensitivity: float
    mean_sensitivity: float
    sensitivity_entropy: float
    inactive_support_variables: int


@dataclass(frozen=True)
class SensitivityPairFeatures:
    status: str
    skipped_reason: str
    sensitivity_mode: str
    sensitivity_evidence_level: str
    sensitivity_pattern_count: int
    sensitivity_seed: int
    original_support_size: int
    optimized_support_size: int
    sensitivity_cosine_similarity: float
    sensitivity_l1_distance: float
    sensitivity_l2_distance: float
    dominant_variable_agreement: int
    inactive_variable_agreement: float
    sensitivity_rank_correlation: float
    boolean_difference_similarity: float
    original_dominant_sensitivity_variable: str
    optimized_dominant_sensitivity_variable: str
    original_max_sensitivity: float
    optimized_max_sensitivity: float
    original_mean_sensitivity: float
    optimized_mean_sensitivity: float
    original_sensitivity_entropy: float
    optimized_sensitivity_entropy: float
    original_inactive_support_variables: int
    optimized_inactive_support_variables: int

    def as_dict(self) -> dict[str, object]:
        return self.__dict__.copy()


def _profile_empty(reason: str) -> SensitivityProfile:
    return SensitivityProfile(
        status="skipped",
        skipped_reason=reason,
        mode="unavailable",
        evidence_level="unresolved",
        pattern_count=0,
        seed=0,
        support_size=0,
        probabilities={},
        dominant_variable="",
        max_sensitivity=0.0,
        mean_sensitivity=0.0,
        sensitivity_entropy=0.0,
        inactive_support_variables=0,
    )


def _pair_empty(reason: str) -> SensitivityPairFeatures:
    return SensitivityPairFeatures(
        status="skipped",
        skipped_reason=reason,
        sensitivity_mode="unavailable",
        sensitivity_evidence_level="unresolved",
        sensitivity_pattern_count=0,
        sensitivity_seed=0,
        original_support_size=0,
        optimized_support_size=0,
        sensitivity_cosine_similarity=0.0,
        sensitivity_l1_distance=1.0,
        sensitivity_l2_distance=1.0,
        dominant_variable_agreement=0,
        inactive_variable_agreement=0.0,
        sensitivity_rank_correlation=0.0,
        boolean_difference_similarity=0.0,
        original_dominant_sensitivity_variable="",
        optimized_dominant_sensitivity_variable="",
        original_max_sensitivity=0.0,
        optimized_max_sensitivity=0.0,
        original_mean_sensitivity=0.0,
        optimized_mean_sensitivity=0.0,
        original_sensitivity_entropy=0.0,
        optimized_sensitivity_entropy=0.0,
        original_inactive_support_variables=0,
        optimized_inactive_support_variables=0,
    )


def sensitivity_profile(
    net,
    node: str,
    variables: list[str],
    node_support: set[str],
    *,
    exact_support_limit: int = 10,
    sample_count: int = 1024,
    seed: int = 23,
    key: str = "",
) -> SensitivityProfile:
    if node not in structural_supports(net):
        return _profile_empty("invalid_node")
    probabilities: dict[str, float] = {}
    modes: set[str] = set()
    evidence: set[str] = set()
    pattern_counts: list[int] = []
    for variable in variables:
        result = boolean_difference_probability(
            net,
            node,
            node_support,
            variable,
            exact_support_limit=exact_support_limit,
            sample_count=sample_count,
            seed=seed,
            key=key,
        )
        probabilities[variable] = result.probability
        modes.add(result.mode)
        evidence.add(result.evidence_level)
        if result.pattern_count:
            pattern_counts.append(result.pattern_count)

    values = [probabilities[name] for name in variables]
    dominant = max(probabilities.items(), key=lambda item: (item[1], item[0]))[0] if probabilities else ""
    mode = modes.pop() if len(modes) == 1 else ("mixed" if modes else "unavailable")
    evidence_level = "formal_exhaustive" if evidence == {"formal_exhaustive"} else (
        "sampled_estimate" if "sampled_estimate" in evidence else "unresolved"
    )
    return SensitivityProfile(
        status="ok",
        skipped_reason="",
        mode=mode,
        evidence_level=evidence_level,
        pattern_count=max(pattern_counts) if pattern_counts else 0,
        seed=seed if evidence_level == "sampled_estimate" else 0,
        support_size=len(node_support),
        probabilities=probabilities,
        dominant_variable=dominant,
        max_sensitivity=max(values) if values else 0.0,
        mean_sensitivity=statistics.fmean(values) if values else 0.0,
        sensitivity_entropy=entropy(values),
        inactive_support_variables=sum(1 for name in node_support if probabilities.get(name, 0.0) == 0.0),
    )


def cosine_similarity(left: list[float], right: list[float]) -> float:
    dot = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))
    if left_norm == 0 and right_norm == 0:
        return 1.0
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return dot / (left_norm * right_norm)


def rank_correlation(left: list[float], right: list[float]) -> float:
    if len(left) < 2:
        return 1.0
    left_ranks = {idx: rank for rank, idx in enumerate(sorted(range(len(left)), key=lambda i: (left[i], i)))}
    right_ranks = {idx: rank for rank, idx in enumerate(sorted(range(len(right)), key=lambda i: (right[i], i)))}
    n = len(left)
    diff_sq = sum((left_ranks[i] - right_ranks[i]) ** 2 for i in range(n))
    return 1.0 - (6.0 * diff_sq) / (n * (n * n - 1))


def compare_sensitivity_profiles(
    original_path: Path,
    optimized_path: Path,
    original_node: str,
    optimized_node: str,
    *,
    exact_support_limit: int = 10,
    sample_count: int = 1024,
    seed: int = 23,
) -> SensitivityPairFeatures:
    original, optimized, alignment = load_aligned_networks(original_path, optimized_path)
    if alignment != "ok":
        return _pair_empty(alignment)
    try:
        original_supports = structural_supports(original)
        optimized_supports = structural_supports(optimized)
    except ValueError:
        return _pair_empty("invalid_node")
    if original_node not in original_supports or optimized_node not in optimized_supports:
        return _pair_empty("invalid_node")

    original_support = set(original_supports[original_node])
    optimized_support = set(optimized_supports[optimized_node])
    variables = sorted(original_support | optimized_support)
    if not variables:
        return _pair_empty("constant_pair_not_applicable")

    original_profile = sensitivity_profile(
        original,
        original_node,
        variables,
        original_support,
        exact_support_limit=exact_support_limit,
        sample_count=sample_count,
        seed=seed,
        key=f"orig|{original_path}|{original_node}",
    )
    optimized_profile = sensitivity_profile(
        optimized,
        optimized_node,
        variables,
        optimized_support,
        exact_support_limit=exact_support_limit,
        sample_count=sample_count,
        seed=seed,
        key=f"opt|{optimized_path}|{optimized_node}",
    )
    if original_profile.status != "ok" or optimized_profile.status != "ok":
        return _pair_empty(original_profile.skipped_reason or optimized_profile.skipped_reason)

    left = [original_profile.probabilities[name] for name in variables]
    right = [optimized_profile.probabilities[name] for name in variables]
    l1 = sum(abs(a - b) for a, b in zip(left, right)) / len(variables)
    l2 = math.sqrt(sum((a - b) ** 2 for a, b in zip(left, right)) / len(variables))
    inactive_agreement = sum((a == 0.0) == (b == 0.0) for a, b in zip(left, right)) / len(variables)
    mode = original_profile.mode if original_profile.mode == optimized_profile.mode else "mixed"
    evidence_level = (
        "formal_exhaustive"
        if original_profile.evidence_level == optimized_profile.evidence_level == "formal_exhaustive"
        else "sampled_estimate"
    )
    return SensitivityPairFeatures(
        status="ok",
        skipped_reason="",
        sensitivity_mode=mode,
        sensitivity_evidence_level=evidence_level,
        sensitivity_pattern_count=max(original_profile.pattern_count, optimized_profile.pattern_count),
        sensitivity_seed=seed if evidence_level == "sampled_estimate" else 0,
        original_support_size=len(original_support),
        optimized_support_size=len(optimized_support),
        sensitivity_cosine_similarity=cosine_similarity(left, right),
        sensitivity_l1_distance=l1,
        sensitivity_l2_distance=l2,
        dominant_variable_agreement=int(original_profile.dominant_variable == optimized_profile.dominant_variable),
        inactive_variable_agreement=inactive_agreement,
        sensitivity_rank_correlation=rank_correlation(left, right),
        boolean_difference_similarity=max(0.0, 1.0 - l1),
        original_dominant_sensitivity_variable=original_profile.dominant_variable,
        optimized_dominant_sensitivity_variable=optimized_profile.dominant_variable,
        original_max_sensitivity=original_profile.max_sensitivity,
        optimized_max_sensitivity=optimized_profile.max_sensitivity,
        original_mean_sensitivity=original_profile.mean_sensitivity,
        optimized_mean_sensitivity=optimized_profile.mean_sensitivity,
        original_sensitivity_entropy=original_profile.sensitivity_entropy,
        optimized_sensitivity_entropy=optimized_profile.sensitivity_entropy,
        original_inactive_support_variables=original_profile.inactive_support_variables,
        optimized_inactive_support_variables=optimized_profile.inactive_support_variables,
    )
