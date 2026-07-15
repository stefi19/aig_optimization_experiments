"""Shannon-cofactor consistency features for internal-node candidates."""

from __future__ import annotations

import statistics
from dataclasses import dataclass
from pathlib import Path

from functional_signal_utils import (
    bit_error_rate,
    build_patterns,
    evaluate_network,
    load_aligned_networks,
    structural_supports,
)


@dataclass(frozen=True)
class CofactorFeatureResult:
    status: str
    skipped_reason: str
    mode: str
    evidence_level: str
    pattern_count: int
    seed: int
    variables_tested: int
    exact_matching_cofactor_branches: int
    sampled_matching_cofactor_branches: int
    mean_cofactor_error: float
    max_cofactor_error: float
    min_cofactor_error: float
    cofactor_error_variance: float
    cofactor_consistency_score: float
    mean_cofactor_similarity: float
    worst_cofactor_variable: str
    best_cofactor_variable: str

    def as_dict(self) -> dict[str, object]:
        return self.__dict__.copy()


def _empty(status: str, reason: str) -> CofactorFeatureResult:
    return CofactorFeatureResult(
        status=status,
        skipped_reason=reason,
        mode="unavailable",
        evidence_level="unresolved",
        pattern_count=0,
        seed=0,
        variables_tested=0,
        exact_matching_cofactor_branches=0,
        sampled_matching_cofactor_branches=0,
        mean_cofactor_error=0.0,
        max_cofactor_error=0.0,
        min_cofactor_error=0.0,
        cofactor_error_variance=0.0,
        cofactor_consistency_score=0.0,
        mean_cofactor_similarity=0.0,
        worst_cofactor_variable="",
        best_cofactor_variable="",
    )


def normalized_dispersion_score(errors: list[float]) -> float:
    """Return a bounded 1-is-consistent score from branch-error dispersion."""

    if not errors:
        return 0.0
    if len(errors) == 1:
        return 1.0
    stdev = statistics.pstdev(errors)
    return max(0.0, min(1.0, 1.0 - (stdev / 0.5)))


def compute_cofactor_features(
    original_path: Path,
    optimized_path: Path,
    original_node: str,
    optimized_node: str,
    *,
    exact_support_limit: int = 10,
    sample_count: int = 1024,
    seed: int = 23,
) -> CofactorFeatureResult:
    """Compare aligned Shannon cofactor branches for a candidate pair.

    The result is formal only when the relevant support fits the exhaustive
    limit.  Sampled rows are ranking estimates and are labeled accordingly.
    """

    original, optimized, alignment = load_aligned_networks(original_path, optimized_path)
    if alignment != "ok":
        return _empty("skipped", alignment)
    try:
        original_supports = structural_supports(original)
        optimized_supports = structural_supports(optimized)
    except ValueError:
        return _empty("skipped", "invalid_node")
    if original_node not in original_supports or optimized_node not in optimized_supports:
        return _empty("skipped", "invalid_node")

    original_support = set(original_supports[original_node])
    optimized_support = set(optimized_supports[optimized_node])
    common_support = sorted(original_support & optimized_support)
    if not common_support:
        if not original_support and not optimized_support:
            return _empty("skipped", "constant_pair_not_applicable")
        return _empty("skipped", "no_common_support")

    union_support = original_support | optimized_support
    patterns = build_patterns(
        original.inputs,
        union_support,
        exact_support_limit,
        sample_count,
        seed,
        f"cofactor|{original_path}|{optimized_path}|{original_node}|{optimized_node}",
    )
    try:
        original_values = evaluate_network(original, patterns)
        optimized_values = evaluate_network(optimized, patterns)
    except ValueError:
        return _empty("skipped", "invalid_node")

    left = original_values[original_node].value
    right = optimized_values[optimized_node].value
    branch_errors: list[float] = []
    per_variable: list[tuple[str, float]] = []
    matching_branches = 0
    for variable in common_support:
        if variable not in patterns.values:
            return _empty("skipped", "missing_primary_input")
        one_mask = patterns.values[variable] & patterns.mask
        zero_mask = (~patterns.values[variable]) & patterns.mask
        errors_for_variable: list[float] = []
        for branch_mask in (zero_mask, one_mask):
            branch_count = branch_mask.bit_count()
            if branch_count == 0:
                continue
            error = bit_error_rate(left & branch_mask, right & branch_mask, branch_count)
            branch_errors.append(error)
            errors_for_variable.append(error)
            if error == 0.0:
                matching_branches += 1
        if errors_for_variable:
            per_variable.append((variable, statistics.fmean(errors_for_variable)))

    if not branch_errors:
        return _empty("skipped", "support_too_large_without_sampling")

    mean_error = statistics.fmean(branch_errors)
    variance = statistics.pvariance(branch_errors) if len(branch_errors) > 1 else 0.0
    worst = max(per_variable, key=lambda item: (item[1], item[0]))[0] if per_variable else ""
    best = min(per_variable, key=lambda item: (item[1], item[0]))[0] if per_variable else ""
    return CofactorFeatureResult(
        status="ok",
        skipped_reason="",
        mode=patterns.mode,
        evidence_level=patterns.evidence_level,
        pattern_count=patterns.pattern_count,
        seed=patterns.seed,
        variables_tested=len(common_support),
        exact_matching_cofactor_branches=matching_branches if patterns.mode == "exhaustive" else 0,
        sampled_matching_cofactor_branches=matching_branches if patterns.mode == "sampled" else 0,
        mean_cofactor_error=mean_error,
        max_cofactor_error=max(branch_errors),
        min_cofactor_error=min(branch_errors),
        cofactor_error_variance=variance,
        cofactor_consistency_score=normalized_dispersion_score(branch_errors),
        mean_cofactor_similarity=1.0 - mean_error,
        worst_cofactor_variable=worst,
        best_cofactor_variable=best,
    )
