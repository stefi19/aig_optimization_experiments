"""Boolean-difference helpers for sensitivity estimation."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass

from analyze_blif_matches import BlifNetwork
from functional_signal_utils import FeaturePatternSet, bit_error_rate, evaluate_network, stable_seed


@dataclass(frozen=True)
class BooleanDifferenceResult:
    variable: str
    probability: float
    mode: str
    evidence_level: str
    pattern_count: int


def paired_difference_patterns(
    inputs: list[str],
    active_support: set[str],
    variable: str,
    exact_support_limit: int,
    sample_count: int,
    seed: int,
    key: str,
) -> tuple[FeaturePatternSet, FeaturePatternSet]:
    """Build paired x=0 and x=1 assignments for a Boolean difference."""

    other_variables = tuple(sorted(active_support - {variable}))
    values0 = {name: 0 for name in inputs}
    values1 = {name: 0 for name in inputs}
    if len(other_variables) <= max(0, exact_support_limit - 1):
        pattern_count = 1 << len(other_variables)
        mode = "exhaustive"
        evidence = "formal_exhaustive"
        actual_seed = 0
        for input_index, name in enumerate(other_variables):
            bits = 0
            for assignment in range(pattern_count):
                if (assignment >> input_index) & 1:
                    bits |= 1 << assignment
            values0[name] = bits
            values1[name] = bits
    else:
        pattern_count = sample_count
        mode = "sampled"
        evidence = "sampled_estimate"
        actual_seed = seed
        rng = random.Random(stable_seed(seed, f"bdiff|{key}|{variable}"))
        for name in other_variables:
            bits = 0
            for pattern_index in range(pattern_count):
                if rng.getrandbits(1):
                    bits |= 1 << pattern_index
            values0[name] = bits
            values1[name] = bits
    mask = (1 << pattern_count) - 1
    values0[variable] = 0
    values1[variable] = mask
    base = {
        "mask": mask,
        "pattern_count": pattern_count,
        "mode": mode,
        "evidence_level": evidence,
        "seed": actual_seed,
        "active_support": tuple(sorted(active_support)),
    }
    return (
        FeaturePatternSet(values=values0, **base),
        FeaturePatternSet(values=values1, **base),
    )


def boolean_difference_probability(
    net: BlifNetwork,
    node: str,
    active_support: set[str],
    variable: str,
    *,
    exact_support_limit: int = 10,
    sample_count: int = 1024,
    seed: int = 23,
    key: str = "",
) -> BooleanDifferenceResult:
    if variable not in net.inputs:
        return BooleanDifferenceResult(variable, 0.0, "unavailable", "unresolved", 0)
    patterns0, patterns1 = paired_difference_patterns(
        net.inputs,
        set(active_support) | {variable},
        variable,
        exact_support_limit,
        sample_count,
        seed,
        key,
    )
    values0 = evaluate_network(net, patterns0)
    values1 = evaluate_network(net, patterns1)
    if node not in values0 or node not in values1:
        return BooleanDifferenceResult(variable, 0.0, "unavailable", "unresolved", 0)
    probability = bit_error_rate(values0[node].value, values1[node].value, patterns0.pattern_count)
    return BooleanDifferenceResult(
        variable=variable,
        probability=probability,
        mode=patterns0.mode,
        evidence_level=patterns0.evidence_level,
        pattern_count=patterns0.pattern_count,
    )


def entropy(values: list[float]) -> float:
    total = sum(values)
    if total <= 0:
        return 0.0
    probs = [value / total for value in values if value > 0]
    if not probs:
        return 0.0
    raw = -sum(p * math.log2(p) for p in probs)
    max_entropy = math.log2(len(values)) if len(values) > 1 else 1.0
    return raw / max_entropy if max_entropy else 0.0
