import json

from boundary_graph import CircuitGraph
from semantic_bus_inference import (
    annotate_ground_truth_matches,
    evaluate_hypotheses,
    infer_bus_hypotheses,
    parse_name_features,
)
from semantic_interface import BusGroundTruth


def test_parse_name_features_handles_common_bit_styles():
    assert parse_name_features("a[3]").prefix == "a"
    assert parse_name_features("data_2").index == 2
    assert parse_name_features("out15").prefix == "out"
    assert parse_name_features("sel").style == "scalar"


def test_inferred_bus_mode_does_not_use_ground_truth_for_generation():
    hyps = infer_bus_hypotheses(
        region_id="r0",
        direction="input",
        nodes=("a_0", "a_1", "b_0", "sel"),
        graph=None,
        feature_mode="names_only",
    )
    assert all(not hyp.used_ground_truth_for_generation for hyp in hyps)
    assert all(hyp.inference_mode == "inferred_bus_mode" for hyp in hyps)
    assert hyps[0].rank == 1


def test_bus_hypothesis_csv_serializes_sequences():
    hyp = infer_bus_hypotheses(
        region_id="r0",
        direction="input",
        nodes=("a_0", "a_1"),
        graph=None,
        feature_mode="full_combined",
    )[0]
    row = hyp.to_csv_row()
    assert json.loads(row["member_nodes"]) == ["a_0", "a_1"]
    assert json.loads(row["evidence_sources"])


def test_ground_truth_annotation_and_evaluation_are_separate():
    bus = BusGroundTruth(
        case_id="case",
        bus_name="a",
        direction="input",
        width=2,
        signedness="unsigned",
        declared_msb=1,
        declared_lsb=0,
        bit_order="lsb_to_msb",
        member_signal_names=("a_0", "a_1"),
        member_canonical_node_ids=("a_0", "a_1"),
        role="data_operand",
        mode="ground_truth_bus_mode",
    )
    hyps = infer_bus_hypotheses(
        region_id="case__identity__ground_truth_region",
        direction="input",
        nodes=("a_0", "a_1"),
        graph=None,
    )
    annotated = annotate_ground_truth_matches(hyps, [bus])
    assert annotated[0].ground_truth_match == "exact"
    assert not annotated[0].used_ground_truth_for_generation
    row = evaluate_hypotheses(
        region_row={
            "region_id": "case__identity__ground_truth_region",
            "case_id": "case",
            "optimization": "identity",
            "source_type": "ground_truth_region",
        },
        direction="input",
        hypotheses=annotated,
        bus_rows=[bus],
        scalar_nodes=("a_0", "a_1"),
        feature_mode="full_combined",
    )
    assert row["top_1_bus_match"] == "true"
    assert row["bus_membership_recall"] == "1.000000"


def test_structural_grouping_is_deterministic(tmp_path):
    blif = tmp_path / "tiny.blif"
    blif.write_text(
        ".model tiny\n"
        ".inputs a_0 a_1\n"
        ".outputs y_0 y_1\n"
        ".names a_0 y_0\n1 1\n"
        ".names a_1 y_1\n1 1\n"
        ".end\n",
        encoding="utf-8",
    )
    graph = CircuitGraph.from_blif(blif)
    first = infer_bus_hypotheses(region_id="r", direction="input", nodes=("a_1", "a_0"), graph=graph, feature_mode="structure_only")
    second = infer_bus_hypotheses(region_id="r", direction="input", nodes=("a_1", "a_0"), graph=graph, feature_mode="structure_only")
    assert [h.to_csv_row() for h in first] == [h.to_csv_row() for h in second]
