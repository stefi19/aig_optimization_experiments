"""Shared BLIF evaluation helpers for functional correspondence features."""

from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass
from pathlib import Path

from analyze_blif_matches import BlifNetwork, eval_cover, parse_blif


@dataclass(frozen=True)
class FeaturePatternSet:
    values: dict[str, int]
    mask: int
    pattern_count: int
    mode: str
    evidence_level: str
    seed: int
    active_support: tuple[str, ...]


@dataclass(frozen=True)
class EvaluatedNode:
    value: int
    support: frozenset[str]


def stable_seed(seed: int, key: str) -> int:
    digest = hashlib.sha256(f"{seed}|{key}".encode("utf-8")).hexdigest()
    return int(digest[:16], 16)


def structural_supports(net: BlifNetwork) -> dict[str, frozenset[str]]:
    support: dict[str, frozenset[str]] = {name: frozenset([name]) for name in net.inputs}
    for node in net.nodes:
        node_support: set[str] = set()
        for fanin in node.inputs:
            if fanin not in support:
                raise ValueError(f"missing fanin {fanin!r} while computing support")
            node_support |= set(support[fanin])
        support[node.output] = frozenset(node_support)
    return support


def node_names(net: BlifNetwork) -> set[str]:
    return set(net.inputs) | set(net.outputs) | {node.output for node in net.nodes}


def build_patterns(
    all_inputs: list[str],
    active_support: set[str],
    exact_support_limit: int,
    sample_count: int,
    seed: int,
    key: str,
) -> FeaturePatternSet:
    """Build exhaustive or sampled bit-vector assignments over active inputs.

    Inputs outside ``active_support`` are held at zero.  This matches the
    repository's existing approximate-distance convention and keeps input
    alignment explicit.
    """

    ordered = tuple(sorted(active_support))
    values = {name: 0 for name in all_inputs}
    if len(ordered) <= exact_support_limit:
        pattern_count = 1 << len(ordered)
        for input_index, name in enumerate(ordered):
            bits = 0
            for assignment in range(pattern_count):
                if (assignment >> input_index) & 1:
                    bits |= 1 << assignment
            values[name] = bits
        mode = "exhaustive"
        evidence = "formal_exhaustive"
        actual_seed = 0
    else:
        pattern_count = sample_count
        rng = random.Random(stable_seed(seed, key))
        for name in ordered:
            bits = 0
            for pattern_index in range(pattern_count):
                if rng.getrandbits(1):
                    bits |= 1 << pattern_index
            values[name] = bits
        mode = "sampled"
        evidence = "sampled_estimate"
        actual_seed = seed
    return FeaturePatternSet(
        values=values,
        mask=(1 << pattern_count) - 1,
        pattern_count=pattern_count,
        mode=mode,
        evidence_level=evidence,
        seed=actual_seed,
        active_support=ordered,
    )


def evaluate_network(net: BlifNetwork, patterns: FeaturePatternSet) -> dict[str, EvaluatedNode]:
    missing_inputs = [name for name in net.inputs if name not in patterns.values]
    if missing_inputs:
        raise ValueError(f"missing input pattern values for {missing_inputs}")
    values = dict(patterns.values)
    supports: dict[str, frozenset[str]] = {name: frozenset([name]) for name in net.inputs}
    evaluated: dict[str, EvaluatedNode] = {
        name: EvaluatedNode(value=values[name], support=frozenset([name])) for name in net.inputs
    }
    for node in net.nodes:
        missing = [fanin for fanin in node.inputs if fanin not in values]
        if missing:
            raise ValueError(f"missing fanin values for {missing}")
        value = eval_cover(node, values, patterns.mask)
        values[node.output] = value
        node_support: set[str] = set()
        for fanin in node.inputs:
            node_support |= set(supports.get(fanin, frozenset()))
        supports[node.output] = frozenset(node_support)
        evaluated[node.output] = EvaluatedNode(value=value, support=frozenset(node_support))
    return evaluated


def load_aligned_networks(original_path: Path, optimized_path: Path) -> tuple[BlifNetwork, BlifNetwork, str]:
    original = parse_blif(original_path)
    optimized = parse_blif(optimized_path)
    if len(original.inputs) != len(set(original.inputs)) or len(optimized.inputs) != len(set(optimized.inputs)):
        return original, optimized, "duplicate_primary_input"
    if original.inputs != optimized.inputs:
        return original, optimized, "input_alignment_failure"
    return original, optimized, "ok"


def bit_error_rate(left: int, right: int, pattern_count: int) -> float:
    if pattern_count <= 0:
        return 0.0
    return (left ^ right).bit_count() / pattern_count


def safe_float(value: object, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        if value != value:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default
