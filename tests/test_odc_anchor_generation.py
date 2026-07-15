from analyze_blif_matches import BlifNetwork, BlifNode
from boundary_anchor_map import AnchorMap
from boundary_graph import CircuitGraph
from coi_model import normalize_coi
from odc_anchor_generation import generate_odc_anchor_candidates


def test_candidate_generation_is_deterministic_and_bounded():
    graph = CircuitGraph.from_network(
        BlifNetwork(
            inputs=["a", "b"],
            outputs=["y"],
            nodes=[
                BlifNode("n1", ["a"], ["1 1"]),
                BlifNode("n2", ["b"], ["1 1"]),
                BlifNode("y", ["n1", "n2"], ["11 1"]),
            ],
        )
    )
    coi = normalize_coi(graph, benchmark="b", optimization="*", coi_name="c", region_nodes={"y"}, source="test")
    first = generate_odc_anchor_candidates(
        benchmark="b",
        optimization="opt",
        coi=coi,
        spec_graph=graph,
        impl_graph=graph,
        anchors=AnchorMap([]),
        context_mode="global_output_odc",
        ranking_mode="combined",
        max_frontier_distance=2,
        max_spec_candidates_per_boundary=4,
        max_impl_candidates_per_spec_node=3,
        case_prefix="case",
    )
    second = generate_odc_anchor_candidates(
        benchmark="b",
        optimization="opt",
        coi=coi,
        spec_graph=graph,
        impl_graph=graph,
        anchors=AnchorMap([]),
        context_mode="global_output_odc",
        ranking_mode="combined",
        max_frontier_distance=2,
        max_spec_candidates_per_boundary=4,
        max_impl_candidates_per_spec_node=3,
        case_prefix="case",
    )
    assert first == second
    assert len(first) <= 6
    assert all(c.simulation_filter_status == "sampled_contextual_candidate" for c in first)
