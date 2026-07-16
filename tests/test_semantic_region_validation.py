import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from boundary_graph import CircuitGraph
from coi_model import derive_boundary_inputs, derive_boundary_outputs
from semantic_region_validation import validate_semantic_region


def write_blif(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "tiny.blif"
    path.write_text(text.strip() + "\n", encoding="utf-8")
    return path


def sample_graph(tmp_path: Path) -> CircuitGraph:
    return CircuitGraph.from_blif(
        write_blif(
            tmp_path,
            """
            .model tiny
            .inputs a b sel
            .outputs y side
            .names a b n1
            11 1
            .names sel n1 y
            11 1
            .names n1 side
            1 1
            .end
            """,
        )
    )


def test_valid_region_can_differ_from_whole_design(tmp_path):
    graph = sample_graph(tmp_path)
    region = ("n1", "y")
    result = validate_semantic_region(
        graph,
        region_id="r",
        region_nodes=region,
        boundary_inputs=derive_boundary_inputs(graph, region),
        boundary_outputs=derive_boundary_outputs(graph, region),
        observable_outputs=("y",),
        expected_region_nodes=("n1",),
    )
    assert result.valid
    assert result.derived_bi == ("a", "b", "sel")
    assert result.derived_bo == ("n1", "y")
    assert result.extra_region_nodes == ("y",)
    assert not result.whole_design_region


def test_validation_reports_missing_nodes_and_expected_region(tmp_path):
    graph = sample_graph(tmp_path)
    result = validate_semantic_region(
        graph,
        region_id="r",
        region_nodes=("n1", "missing"),
        boundary_inputs=("a", "b"),
        boundary_outputs=("n1",),
        observable_outputs=("y",),
        expected_region_nodes=("n1", "y"),
    )
    assert not result.valid
    assert "missing_region_node:missing" in result.errors
    assert "missing_expected_region_node:y" in result.errors


def test_validation_reports_incorrect_boundaries_and_bypasses(tmp_path):
    graph = sample_graph(tmp_path)
    result = validate_semantic_region(
        graph,
        region_id="r",
        region_nodes=("n1", "y"),
        boundary_inputs=("a",),
        boundary_outputs=("y",),
        observable_outputs=("y",),
    )
    assert not result.valid
    assert "missing_boundary_input:b" in result.errors
    assert "missing_boundary_input:sel" in result.errors
    assert "missing_boundary_output:n1" in result.errors
    assert "incoming_bypass:b->n1" in result.errors
    assert "incoming_bypass:sel->y" in result.errors
    assert "outgoing_bypass:n1->side" in result.errors


def test_validation_rejects_fingerprint_alignment_mismatch(tmp_path):
    graph = sample_graph(tmp_path)
    result = validate_semantic_region(
        graph,
        region_id="r",
        region_nodes=("n1", "y", "side"),
        boundary_inputs=derive_boundary_inputs(graph, ("n1", "y", "side")),
        boundary_outputs=derive_boundary_outputs(graph, ("n1", "y", "side")),
        observable_outputs=("y", "side"),
        expected_benchmark="expected",
        actual_benchmark="actual",
        expected_optimization="identity",
        actual_optimization="rewrite",
    )
    assert not result.valid
    assert "benchmark_mismatch" in result.errors
    assert "optimization_mismatch" in result.errors
    assert result.whole_design_region
