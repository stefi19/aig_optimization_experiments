from pathlib import Path

import pytest

from boundary_anchor_map import Anchor, AnchorMap
from boundary_graph import CircuitGraph
from boundary_recovery import (
    CoiSpec,
    compute_boundary_metrics,
    detect_mapped_boundary_cycles,
    extract_region_between_cuts,
    first_equivalent_cut_tfi,
    first_equivalent_cut_tfo,
    recover_extended_boundary,
    validate_recovered_boundary,
)


def write_blif(path: Path) -> Path:
    path.write_text(
        """
.model m
.inputs a b c
.outputs y
.names a b n1
11 1
.names n1 c n2
1- 1
-1 1
.names n2 y
1 1
.names a z
1 1
.end
""".strip()
        + "\n",
        encoding="utf-8",
    )
    return path


def anchors(*nodes: str) -> AnchorMap:
    return AnchorMap(
        [
            Anchor(node, node, "same", "exact_signature_match", "formal_exhaustive", "test", "test", "1.0")
            for node in nodes
        ]
    )


def test_tfi_tfo_and_deterministic_cut_recovery(tmp_path):
    graph = CircuitGraph.from_blif(write_blif(tmp_path / "m.blif"))
    amap = anchors("a", "y")

    ebi, distances, failures = first_equivalent_cut_tfi(graph, ["n1"], amap)
    ebo, out_distances, out_failures = first_equivalent_cut_tfo(graph, ["n2"], amap)

    assert ebi == {"a"}
    assert distances["a"] == 1
    assert not failures
    assert ebo == {"y"}
    assert out_distances["y"] == 1
    assert not out_failures


def test_region_extraction_between_cuts(tmp_path):
    graph = CircuitGraph.from_blif(write_blif(tmp_path / "m.blif"))

    region = extract_region_between_cuts(graph, {"a", "b", "c"}, {"y"})

    assert {"n1", "n2", "y"}.issubset(region)
    assert "a" not in region


def test_recover_valid_boundary_with_interface_anchors(tmp_path):
    graph = CircuitGraph.from_blif(write_blif(tmp_path / "m.blif"))
    coi = CoiSpec("b", "opt", "coi", ("n1", "n2", "y"), ("a", "b", "c"), ("y",), "test")
    amap = anchors("a", "b", "c", "y")

    result = recover_extended_boundary(graph, graph, coi, amap)

    assert result.validation_status == "valid"
    assert set(result.extended_boundary_inputs) == {"a", "b", "c"}
    assert result.extended_boundary_outputs == ("y",)


def test_validation_reports_missing_anchor(tmp_path):
    graph = CircuitGraph.from_blif(write_blif(tmp_path / "m.blif"))
    coi = CoiSpec("b", "opt", "coi", ("n1",), ("a",), ("y",), "test")

    status, reason, conflicts = validate_recovered_boundary(graph, graph, coi, {"a"}, {"y"}, {"n1", "n2", "y"}, anchors("a"))

    assert status == "missing_anchor"
    assert "y" in reason
    assert conflicts == []


def test_cycle_detection_flags_impl_feedback_risk(tmp_path):
    graph = CircuitGraph.from_blif(write_blif(tmp_path / "m.blif"))
    amap = AnchorMap(
        [
            Anchor("ebi", "n2", "same", "exact_signature_match", "formal_exhaustive", "test", "test", "1.0"),
            Anchor("ebo", "n1", "same", "exact_signature_match", "formal_exhaustive", "test", "test", "1.0"),
        ]
    )

    conflicts = detect_mapped_boundary_cycles(graph, {"ebi"}, {"ebo"}, amap)

    assert conflicts == [("ebi", "ebo")]


def test_boundary_metrics_zero_denominator(tmp_path):
    graph = CircuitGraph.from_blif(write_blif(tmp_path / "m.blif"))
    coi = CoiSpec("b", "opt", "coi", tuple(n for n in graph.nodes if n not in graph.inputs), ("a",), ("y",), "test")
    result = recover_extended_boundary(graph, graph, coi, anchors("a", "y"))

    metrics = compute_boundary_metrics(result, graph, graph)

    assert 0.0 <= metrics["boundary_extension_ratio"] <= 1.0
