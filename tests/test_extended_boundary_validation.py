from boundary_anchor_map import Anchor, AnchorMap
from boundary_graph import CircuitGraph
from coi_model import normalize_coi
from extended_boundary_search import (
    SearchConfig,
    enumerate_anchored_tfi_frontiers,
    first_frontier_extended_boundary,
    search_valid_extended_boundary,
    validate_extended_boundary,
)


def graph(tmp_path, text: str):
    path = tmp_path / "m.blif"
    path.write_text(text.strip() + "\n", encoding="utf-8")
    return CircuitGraph.from_blif(path)


def anchor_map(g: CircuitGraph, missing=()):
    missing_set = set(missing)
    return AnchorMap(
        [
            Anchor(
                spec_node=n,
                impl_node=n,
                polarity="same",
                mapping_category="exact_signature_match",
                evidence_level="formal_exhaustive",
                proof_mode="test",
                source_result_file="test",
                confidence_or_status="test",
            )
            for n in sorted(g.nodes)
            if n not in missing_set
        ]
    )


def test_extended_boundary_allows_extra_region_nodes(tmp_path):
    g = graph(tmp_path, """
.model m
.inputs a
.outputs y
.names a n1
1 1
.names n1 n2
1 1
.names n2 n3
1 1
.names n3 y
1 1
.end
""")
    coi = normalize_coi(g, benchmark="b", optimization="original", coi_name="n2_only", region_nodes={"n2"}, source="test")
    result = validate_extended_boundary(g, g, coi, anchor_map(g), {"n1"}, {"n3"}, {"n1": 0, "n3": 0}, "test", SearchConfig(), runtime_seconds=0, candidate_frontiers=2)
    assert result.success
    assert result.contains_original_coi
    assert not result.original_region_exact_match
    assert result.extension_nodes == ("n3",)


def test_missing_original_node_rejected(tmp_path):
    g = graph(tmp_path, """
.model m
.inputs a
.outputs y
.names a n1
1 1
.names n1 n2
1 1
.names n2 y
1 1
.end
""")
    coi = normalize_coi(g, benchmark="b", optimization="original", coi_name="n2", region_nodes={"n2"}, source="test")
    result = validate_extended_boundary(g, g, coi, anchor_map(g), {"a"}, {"n1"}, {"a": 0, "n1": 0}, "test", SearchConfig(), runtime_seconds=0, candidate_frontiers=2)
    assert not result.success
    assert not result.contains_original_coi
    assert "missing_original_coi_nodes" in result.failure_reason


def test_incoming_bypass_rejected(tmp_path):
    g = graph(tmp_path, """
.model m
.inputs a b
.outputs y
.names a n1
1 1
.names b n2
1 1
.names n1 n2 y
11 1
.end
""")
    coi = normalize_coi(g, benchmark="b", optimization="original", coi_name="y", region_nodes={"y"}, source="test")
    result = validate_extended_boundary(g, g, coi, anchor_map(g), {"n1"}, {"y"}, {"n1": 0, "y": 0}, "test", SearchConfig(), runtime_seconds=0, candidate_frontiers=2)
    assert not result.success
    assert result.incoming_bypass_edges == (("n2", "y"),)


def test_candidate_frontier_generation_is_bounded_and_deterministic(tmp_path):
    g = graph(tmp_path, """
.model m
.inputs a
.outputs y
.names a n1
1 1
.names n1 n2
1 1
.names n2 y
1 1
.end
""")
    anchors = anchor_map(g)
    cfg = SearchConfig(max_frontier_depth=3, max_candidates_per_boundary_node=2)
    first = enumerate_anchored_tfi_frontiers(g, ("n2",), anchors, cfg)
    second = enumerate_anchored_tfi_frontiers(g, ("n2",), anchors, cfg)
    assert first == second
    assert [c.node for c in first["n2"]] == ["n2", "n1"]


def test_first_frontier_invalid_second_frontier_valid_for_cost_guided(tmp_path):
    g = graph(tmp_path, """
.model m
.inputs a
.outputs y
.names a n1
1 1
.names n1 n2
1 1
.names n2 n3
1 1
.names n3 y
1 1
.end
""")
    coi = normalize_coi(g, benchmark="b", optimization="original", coi_name="n2", region_nodes={"n2"}, source="test")
    anchors = anchor_map(g, missing={"n1"})
    first = first_frontier_extended_boundary(g, g, coi, anchors)
    cost = search_valid_extended_boundary(g, g, coi, anchors, SearchConfig(max_frontier_depth=4, max_candidates_per_boundary_node=3))
    assert not first.original_ebi_exact_match
    assert cost.success
    assert cost.search_mode == "cost_guided"


def test_missing_formal_anchor_blocks_boundary(tmp_path):
    g = graph(tmp_path, """
.model m
.inputs a
.outputs y
.names a n1
1 1
.names n1 y
1 1
.end
""")
    coi = normalize_coi(g, benchmark="b", optimization="original", coi_name="n1", region_nodes={"n1"}, source="test")
    anchors = anchor_map(g, missing={"n1", "y"})
    result = search_valid_extended_boundary(g, g, coi, anchors, SearchConfig(max_frontier_depth=1))
    assert not result.success
    assert result.failure_reason == "no_anchored_frontier"
