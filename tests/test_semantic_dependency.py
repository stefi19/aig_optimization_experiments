from analyze_blif_matches import parse_blif
from boundary_graph import CircuitGraph
from semantic_dependency import (
    boolean_difference_dependency,
    compute_dependency_matrices,
    geometry_features,
    make_sample_patterns,
    simulated_dependency,
    structural_dependency,
)


def write_tiny_blif(path):
    path.write_text(
        ".model tiny\n"
        ".inputs a_0 a_1 b_0 b_1\n"
        ".outputs y_0 y_1\n"
        ".names a_0 b_0 y_0\n11 1\n"
        ".names a_1 b_1 y_1\n1- 1\n-1 1\n"
        ".end\n",
        encoding="utf-8",
    )


def test_structural_dependency_matrix(tmp_path):
    blif = tmp_path / "tiny.blif"
    write_tiny_blif(blif)
    graph = CircuitGraph.from_blif(blif)
    matrix = structural_dependency(graph, ("a_0", "a_1", "b_0", "b_1"), ("y_0", "y_1"))
    assert matrix == [[1, 0, 1, 0], [0, 1, 0, 1]]


def test_sampled_patterns_are_deterministic():
    first = make_sample_patterns(["a", "b"], 16, 7, "k")
    second = make_sample_patterns(["a", "b"], 16, 7, "k")
    third = make_sample_patterns(["a", "b"], 16, 8, "k")
    assert first.values == second.values
    assert first.values != third.values
    assert first.evidence_level == "sampled_estimate"


def test_simulated_dependency_is_sampled_not_formal(tmp_path):
    blif = tmp_path / "tiny.blif"
    write_tiny_blif(blif)
    net = parse_blif(blif)
    matrix, evidence, count = simulated_dependency(net, ("a_0", "a_1"), ("y_0", "y_1"), sample_count=32, seed=4)
    assert len(matrix) == 2
    assert evidence == "sampled_estimate"
    assert count == 32


def test_boolean_difference_dependency_exact_for_small_support(tmp_path):
    blif = tmp_path / "tiny.blif"
    write_tiny_blif(blif)
    net = parse_blif(blif)
    matrix, evidence = boolean_difference_dependency(net, ("a_0", "a_1"), ("y_0", "y_1"), exact_support_limit=4)
    assert evidence == "formal_exhaustive"
    assert matrix[0][0] > 0
    assert matrix[0][1] == 0


def test_geometry_features_are_bounded():
    features = geometry_features([[1, 0], [1, 1]])
    for key, value in features.items():
        if key not in {"minimum_dependency_slope", "maximum_dependency_slope"}:
            assert 0.0 <= value <= 1.0, key
    assert features["dependency_density"] == 0.75


def test_compute_dependency_matrices_schema(tmp_path):
    blif = tmp_path / "tiny.blif"
    write_tiny_blif(blif)
    dep = compute_dependency_matrices(
        region_id="r",
        blif_path=blif,
        input_nodes=("a_0", "a_1", "b_0", "b_1"),
        output_nodes=("y_0", "y_1"),
        sample_count=16,
        seed=5,
    )
    row = dep.to_json_row()
    assert row["region_id"] == "r"
    assert row["simulation_evidence_level"] == "sampled_estimate"
    assert "D_structural" in row
