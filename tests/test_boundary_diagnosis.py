from pathlib import Path

from boundary_anchor_map import Anchor, AnchorMap
from boundary_diagnosis import (
    alignment_row,
    anchor_coverage_row,
    classify_differential,
    generated_critical_path_coi_rows,
    identity_anchor_map,
    nearest_distances,
    stage_rows,
)
from boundary_graph import CircuitGraph
from boundary_recovery import CoiSpec


def write_blif(path: Path) -> Path:
    path.write_text(
        """
.model m
.inputs a b c
.outputs y
.names a b n1
11 1
.names n1 c n2
11 1
.names n2 y
1 1
.end
""".strip()
        + "\n",
        encoding="utf-8",
    )
    return path


def test_identity_anchor_map_covers_every_graph_node(tmp_path):
    graph = CircuitGraph.from_blif(write_blif(tmp_path / "m.blif"))
    anchors = identity_anchor_map(graph)

    for node in graph.nodes:
        selected = anchors.selected_for(node)
        assert selected is not None
        assert selected.impl_node == node
        assert selected.evidence_level == "formal_exhaustive"


def test_stage_rows_mark_terminal_failure():
    coi = CoiSpec("b", "balance", "coi", ("n1",), ("a",), ("y",), "test")
    rows = stage_rows("case", coi, "exact_only", {"load_inputs"}, "validate_coi", False)

    terminal = [row for row in rows if row["is_terminal_failure_stage"]]
    assert terminal[0]["stage"] == "validate_coi"
    assert any(row["stage"] == "load_inputs" and row["stage_passed"] for row in rows)


def test_alignment_detects_interface_mismatch(tmp_path):
    spec = CircuitGraph.from_blif(write_blif(tmp_path / "spec.blif"))
    impl_path = tmp_path / "impl.blif"
    impl_path.write_text(
        """
.model m
.inputs a b d
.outputs y
.names a b y
11 1
.end
""".strip()
        + "\n",
        encoding="utf-8",
    )
    impl = CircuitGraph.from_blif(impl_path)
    coi = CoiSpec("b", "balance", "coi", ("n1",), ("a",), ("y",), "test")

    row = alignment_row("case", coi, "exact_only", tmp_path / "spec.blif", impl_path, spec, impl)

    assert row["alignment_valid"] is False
    assert "primary_input_names_differ" in row["alignment_failure_reason"]
    assert row["spec_fingerprint"]


def test_anchor_coverage_separates_exact_and_sat_cec(tmp_path):
    graph = CircuitGraph.from_blif(write_blif(tmp_path / "m.blif"))
    anchors = AnchorMap(
        [
            Anchor("a", "a", "same", "exact_signature_match", "formal_exhaustive", "test", "x", "1"),
            Anchor("y", "y", "same", "sat_cec_proven_equivalent", "formal_cec", "test", "x", "verified"),
        ]
    )
    coi = CoiSpec("b", "balance", "coi", ("n1", "n2", "y"), ("a",), ("y",), "test")

    row = anchor_coverage_row("case", coi, "formal_all", graph, anchors)

    assert row["exact_anchor_count_global"] == 1
    assert row["sat_cec_anchor_count_global"] == 1
    assert row["formal_all_added_global_anchors"] == 1


def test_nearest_distances_records_unreachable(tmp_path):
    graph = CircuitGraph.from_blif(write_blif(tmp_path / "m.blif"))

    distances = nearest_distances(graph, ["y"], {"a"}, "fanout")

    assert distances["y"] is None


def test_differential_classification_no_extra_anchors():
    exact = {"recovery_success": False, "boundary_extension_ratio": 0}
    formal = {"recovery_success": False, "boundary_extension_ratio": 0}
    cov = {"formal_all_added_global_anchors": 0}

    assert classify_differential(exact, formal, cov, 0) == "no_extra_formal_anchors"


def test_generated_critical_path_cois_records_missing_spec(tmp_path):
    critical = tmp_path / "critical.csv"
    critical.write_text(
        "benchmark,optimization,path_index,mapped_original_node,optimized_node,mapping_category\n"
        "missing_bench,balance,1,n1,n1,unresolved\n"
        "missing_bench,balance,2,n2,n2,unresolved\n"
        "missing_bench,balance,3,n3,n3,unresolved\n",
        encoding="utf-8",
    )

    rows = generated_critical_path_coi_rows([3], critical_path=critical)

    assert rows
    assert rows[0]["failure_reason"] == "missing_spec_circuit"
    assert rows[0]["generated_coi_valid"] is False
