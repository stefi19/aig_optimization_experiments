"""Dependency matrices and geometry features for semantic regions."""

from __future__ import annotations

import json
import random
from dataclasses import dataclass

from analyze_blif_matches import BlifNetwork, parse_blif
from boolean_difference import boolean_difference_probability
from boundary_graph import CircuitGraph
from functional_signal_utils import FeaturePatternSet, bit_error_rate, evaluate_network, stable_seed, structural_supports


DEPENDENCY_SCHEMA_VERSION = "semantic_dependency_v1"

SEMANTIC_DEPENDENCY_FEATURE_FIELDS = [
    "region_id",
    "case_id",
    "optimization",
    "source_type",
    "input_count",
    "output_count",
    "structural_coverage",
    "simulation_coverage",
    "boolean_difference_coverage",
    "formal_dependency_coverage",
    "dependency_density",
    "row_density_mean",
    "column_density_mean",
    "lower_triangularity",
    "upper_triangularity",
    "diagonal_concentration",
    "bandwidth",
    "minimum_dependency_slope",
    "maximum_dependency_slope",
    "carry_progression_score",
    "multiplier_diagonal_score",
    "operand_symmetry_score",
    "output_prefix_dependency_score",
    "selectivity_change_score",
    "single_output_control_score",
    "high_bit_priority_score",
    "locality_score",
    "regularity_score",
    "simulation_evidence_level",
    "boolean_difference_evidence_level",
    "pattern_count",
    "seed",
    "runtime_seconds",
    "schema_version",
]

SEMANTIC_DEPENDENCY_BY_OPT_FIELDS = [
    "optimization",
    "eligible_rows",
    "complete_dependency_matrices",
    "mean_dependency_density",
    "mean_diagonal_concentration",
    "mean_lower_triangularity",
    "mean_bandwidth",
    "mean_runtime_seconds",
]

SEMANTIC_DEPENDENCY_FAILURE_FIELDS = [
    "region_id",
    "case_id",
    "optimization",
    "source_type",
    "stage",
    "reason",
]


@dataclass(frozen=True)
class DependencyMatrices:
    region_id: str
    input_nodes: tuple[str, ...]
    output_nodes: tuple[str, ...]
    structural: list[list[int]]
    simulated: list[list[float]]
    boolean_difference: list[list[float | None]]
    formal_optional: list[list[str]]
    simulation_evidence_level: str
    boolean_difference_evidence_level: str
    pattern_count: int
    seed: int
    schema_version: str = DEPENDENCY_SCHEMA_VERSION

    def to_json_row(self) -> dict[str, object]:
        return {
            "region_id": self.region_id,
            "input_nodes": list(self.input_nodes),
            "output_nodes": list(self.output_nodes),
            "D_structural": self.structural,
            "D_simulated": self.simulated,
            "D_boolean_difference": self.boolean_difference,
            "D_formal_optional": self.formal_optional,
            "simulation_evidence_level": self.simulation_evidence_level,
            "boolean_difference_evidence_level": self.boolean_difference_evidence_level,
            "pattern_count": self.pattern_count,
            "seed": self.seed,
            "schema_version": self.schema_version,
        }


def make_sample_patterns(inputs: list[str], sample_count: int, seed: int, key: str) -> FeaturePatternSet:
    rng = random.Random(stable_seed(seed, key))
    values: dict[str, int] = {}
    for name in inputs:
        bits = 0
        for idx in range(sample_count):
            if rng.getrandbits(1):
                bits |= 1 << idx
        values[name] = bits
    return FeaturePatternSet(
        values=values,
        mask=(1 << sample_count) - 1,
        pattern_count=sample_count,
        mode="sampled",
        evidence_level="sampled_estimate",
        seed=seed,
        active_support=tuple(inputs),
    )


def structural_dependency(graph: CircuitGraph, inputs: tuple[str, ...], outputs: tuple[str, ...]) -> list[list[int]]:
    matrix: list[list[int]] = []
    for out in outputs:
        row: list[int] = []
        fanin = graph.transitive_fanin([out])
        for inp in inputs:
            row.append(1 if inp in fanin or graph.has_path(inp, out) else 0)
        matrix.append(row)
    return matrix


def simulated_dependency(net: BlifNetwork, inputs: tuple[str, ...], outputs: tuple[str, ...], *, sample_count: int = 256, seed: int = 31, key: str = "") -> tuple[list[list[float]], str, int]:
    base = make_sample_patterns(net.inputs, sample_count, seed, f"simdep|{key}")
    base_values = evaluate_network(net, base)
    matrix: list[list[float]] = []
    for out in outputs:
        row: list[float] = []
        for inp in inputs:
            if inp not in base.values or out not in base_values:
                row.append(0.0)
                continue
            toggled_values = dict(base.values)
            toggled_values[inp] = (~toggled_values[inp]) & base.mask
            toggled = FeaturePatternSet(
                values=toggled_values,
                mask=base.mask,
                pattern_count=base.pattern_count,
                mode=base.mode,
                evidence_level=base.evidence_level,
                seed=base.seed,
                active_support=base.active_support,
            )
            toggled_eval = evaluate_network(net, toggled)
            row.append(bit_error_rate(base_values[out].value, toggled_eval[out].value, base.pattern_count) if out in toggled_eval else 0.0)
        matrix.append(row)
    return matrix, base.evidence_level, base.pattern_count


def boolean_difference_dependency(
    net: BlifNetwork,
    inputs: tuple[str, ...],
    outputs: tuple[str, ...],
    *,
    exact_support_limit: int = 10,
    sample_count: int = 512,
    seed: int = 37,
    key: str = "",
) -> tuple[list[list[float | None]], str]:
    try:
        supports = structural_supports(net)
    except ValueError:
        return [[None for _ in inputs] for _ in outputs], "unsupported"
    matrix: list[list[float | None]] = []
    evidence: set[str] = set()
    for out in outputs:
        row: list[float | None] = []
        for inp in inputs:
            if out not in supports:
                row.append(None)
                evidence.add("unsupported")
                continue
            result = boolean_difference_probability(
                net,
                out,
                set(supports.get(out, frozenset())),
                inp,
                exact_support_limit=exact_support_limit,
                sample_count=sample_count,
                seed=seed,
                key=f"{key}|{out}|{inp}",
            )
            row.append(result.probability if result.evidence_level != "unresolved" else None)
            evidence.add(result.evidence_level if result.evidence_level != "unresolved" else "unsupported")
        matrix.append(row)
    if evidence == {"formal_exhaustive"}:
        return matrix, "formal_exhaustive"
    if "sampled_estimate" in evidence:
        return matrix, "sampled_estimate"
    return matrix, "unsupported"


def compute_dependency_matrices(
    *,
    region_id: str,
    blif_path,
    input_nodes: tuple[str, ...],
    output_nodes: tuple[str, ...],
    sample_count: int = 256,
    seed: int = 31,
    enable_formal_dependency: bool = False,
) -> DependencyMatrices:
    graph = CircuitGraph.from_blif(blif_path)
    net = parse_blif(blif_path)
    structural = structural_dependency(graph, input_nodes, output_nodes)
    simulated, sim_evidence, pattern_count = simulated_dependency(net, input_nodes, output_nodes, sample_count=sample_count, seed=seed, key=region_id)
    bdiff, bdiff_evidence = boolean_difference_dependency(net, input_nodes, output_nodes, sample_count=max(sample_count, 512), seed=seed + 1, key=region_id)
    formal = [["unsupported" for _ in input_nodes] for _ in output_nodes]
    if enable_formal_dependency:
        # Formal dependency is intentionally left unsupported in this lightweight
        # phase unless a bounded SAT-region backend is added later.
        formal = [["unsupported" for _ in input_nodes] for _ in output_nodes]
    return DependencyMatrices(
        region_id=region_id,
        input_nodes=input_nodes,
        output_nodes=output_nodes,
        structural=structural,
        simulated=simulated,
        boolean_difference=bdiff,
        formal_optional=formal,
        simulation_evidence_level=sim_evidence,
        boolean_difference_evidence_level=bdiff_evidence,
        pattern_count=pattern_count,
        seed=seed,
    )


def density_binary(matrix: list[list[int]]) -> float:
    entries = [value for row in matrix for value in row]
    return sum(entries) / max(1, len(entries))


def geometry_features(matrix: list[list[int]]) -> dict[str, float]:
    rows = len(matrix)
    cols = len(matrix[0]) if rows else 0
    if rows == 0 or cols == 0:
        return {key: 0.0 for key in GEOMETRY_FEATURE_NAMES}
    ones = [(r, c) for r, row in enumerate(matrix) for c, value in enumerate(row) if value]
    total = rows * cols
    density = len(ones) / total
    row_density = [sum(row) / max(1, cols) for row in matrix]
    col_density = [sum(matrix[r][c] for r in range(rows)) / max(1, rows) for c in range(cols)]
    lower = sum(1 for r, c in ones if c <= min(cols - 1, r)) / max(1, len(ones))
    upper = sum(1 for r, c in ones if c >= min(cols - 1, r)) / max(1, len(ones))
    diagonal = sum(1 for r, c in ones if abs(c - min(cols - 1, r)) <= 0) / max(1, len(ones))
    bandwidth = max((abs(c - min(cols - 1, r)) for r, c in ones), default=0) / max(1, max(rows, cols) - 1)
    slopes = [(r / max(1, c)) for r, c in ones if c != 0]
    carry = lower * (1.0 - min(1.0, bandwidth / 2.0))
    multiplier = density * (1.0 - diagonal) * (1.0 - abs((sum(row_density) / rows) - (sum(col_density) / cols)))
    symmetry = 1.0 - min(1.0, sum(abs(col_density[i] - col_density[-i - 1]) for i in range(cols)) / max(1, cols))
    single_output_control = 1.0 if rows == 1 and density > 0.7 else 0.0
    high_bit_priority = sum(row_density[rows // 2 :]) / max(1, len(row_density[rows // 2 :])) if rows > 1 else row_density[0]
    locality = 1.0 - min(1.0, bandwidth)
    regularity = 1.0 - min(1.0, (max(row_density) - min(row_density)) if row_density else 0.0)
    return {
        "dependency_density": density,
        "row_density_mean": sum(row_density) / rows,
        "column_density_mean": sum(col_density) / cols,
        "lower_triangularity": lower,
        "upper_triangularity": upper,
        "diagonal_concentration": diagonal,
        "bandwidth": bandwidth,
        "minimum_dependency_slope": min(slopes) if slopes else 0.0,
        "maximum_dependency_slope": max(slopes) if slopes else 0.0,
        "carry_progression_score": carry,
        "multiplier_diagonal_score": multiplier,
        "operand_symmetry_score": symmetry,
        "output_prefix_dependency_score": lower,
        "selectivity_change_score": 1.0 - regularity,
        "single_output_control_score": single_output_control,
        "high_bit_priority_score": high_bit_priority,
        "locality_score": locality,
        "regularity_score": regularity,
    }


GEOMETRY_FEATURE_NAMES = [
    "dependency_density",
    "row_density_mean",
    "column_density_mean",
    "lower_triangularity",
    "upper_triangularity",
    "diagonal_concentration",
    "bandwidth",
    "minimum_dependency_slope",
    "maximum_dependency_slope",
    "carry_progression_score",
    "multiplier_diagonal_score",
    "operand_symmetry_score",
    "output_prefix_dependency_score",
    "selectivity_change_score",
    "single_output_control_score",
    "high_bit_priority_score",
    "locality_score",
    "regularity_score",
]


def feature_row(region_row: dict[str, str], matrices: DependencyMatrices, runtime_seconds: float) -> dict[str, str]:
    features = geometry_features(matrices.structural)
    row = {
        "region_id": region_row["region_id"],
        "case_id": region_row["case_id"],
        "optimization": region_row["optimization"],
        "source_type": region_row["source_type"],
        "input_count": str(len(matrices.input_nodes)),
        "output_count": str(len(matrices.output_nodes)),
        "structural_coverage": "1.000000",
        "simulation_coverage": "1.000000",
        "boolean_difference_coverage": "1.000000" if matrices.boolean_difference_evidence_level != "unsupported" else "0.000000",
        "formal_dependency_coverage": "0.000000",
        "simulation_evidence_level": matrices.simulation_evidence_level,
        "boolean_difference_evidence_level": matrices.boolean_difference_evidence_level,
        "pattern_count": str(matrices.pattern_count),
        "seed": str(matrices.seed),
        "runtime_seconds": f"{runtime_seconds:.6f}",
        "schema_version": DEPENDENCY_SCHEMA_VERSION,
    }
    row.update({key: f"{features[key]:.6f}" for key in GEOMETRY_FEATURE_NAMES})
    return {field: row[field] for field in SEMANTIC_DEPENDENCY_FEATURE_FIELDS}


def matrices_json(rows: list[DependencyMatrices]) -> str:
    return json.dumps([row.to_json_row() for row in rows], indent=2, sort_keys=True) + "\n"
