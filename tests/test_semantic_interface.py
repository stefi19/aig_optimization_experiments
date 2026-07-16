import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from boundary_graph import CircuitGraph
from semantic_interface import (
    compare_scalar_interface,
    extract_scalar_interface,
    normalize_bus_metadata,
    ordered_nodes,
)


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
            .inputs b_1 a_0 b_0 a_1 sel
            .outputs y_1 y_0
            .names a_0 b_0 y_0
            11 1
            .names a_1 b_1 y_1
            11 1
            .end
            """,
        )
    )


def input_buses():
    return [
        {"name": "a", "width": 2, "role": "data", "signed": True},
        {"name": "b", "width": 2, "role": "data_operand"},
        {"name": "sel", "width": 1, "role": "control"},
    ]


def output_buses():
    return [{"name": "y", "width": 2, "role": "output"}]


def test_bus_metadata_normalization_preserves_width_order_and_roles():
    rows = normalize_bus_metadata("case", input_buses(), output_buses())
    a = next(row for row in rows if row.bus_name == "a")
    sel = next(row for row in rows if row.bus_name == "sel")
    y = next(row for row in rows if row.bus_name == "y")
    assert a.signedness == "signed"
    assert a.member_signal_names == ("a_0", "a_1")
    assert a.role == "data_operand"
    assert sel.member_signal_names == ("sel",)
    assert sel.role == "control"
    assert y.direction == "output"


def test_ordered_nodes_prefers_declared_bus_order_over_lexical_order():
    assert ordered_nodes(("b_1", "a_1", "a_0"), ("a_0", "a_1", "b_0", "b_1"), ("b_1", "a_1", "a_0")) == (
        "a_0",
        "a_1",
        "b_1",
    )


def test_scalar_interface_extracts_declared_input_and_output_order(tmp_path):
    graph = sample_graph(tmp_path)
    rows = extract_scalar_interface(
        graph,
        region_id="r",
        case_id="case",
        optimization="identity",
        source_type="ground_truth_region",
        boundary_inputs=("b_1", "a_1", "b_0", "a_0", "sel"),
        boundary_outputs=("y_1", "y_0"),
        input_buses=input_buses(),
        output_buses=output_buses(),
    )
    assert [row.raw_node_name for row in rows if row.direction == "input"] == ["a_0", "a_1", "b_0", "b_1", "sel"]
    assert [row.raw_node_name for row in rows if row.direction == "output"] == ["y_0", "y_1"]
    assert [row.bus_name for row in rows if row.direction == "output"] == ["y", "y"]


def test_interface_alignment_exact_and_missing_bits(tmp_path):
    graph = sample_graph(tmp_path)
    rows = extract_scalar_interface(
        graph,
        region_id="r",
        case_id="case",
        optimization="identity",
        source_type="ground_truth_region",
        boundary_inputs=("a_0", "a_1", "b_0", "b_1", "sel"),
        boundary_outputs=("y_0", "y_1"),
        input_buses=input_buses(),
        output_buses=output_buses(),
    )
    exact = compare_scalar_interface(
        region_id="r",
        case_id="case",
        optimization="identity",
        source_type="ground_truth_region",
        scalar_rows=rows,
        input_buses=input_buses(),
        output_buses=output_buses(),
    )
    assert exact["exact_scalar_interface_match"] == "true"
    assert exact["input_bit_recall"] == "1.000000"

    missing_rows = [row for row in rows if row.raw_node_name != "b_1"]
    missing = compare_scalar_interface(
        region_id="r",
        case_id="case",
        optimization="identity",
        source_type="ground_truth_region",
        scalar_rows=missing_rows,
        input_buses=input_buses(),
        output_buses=output_buses(),
    )
    assert missing["exact_scalar_interface_match"] == "false"
    assert json.loads(missing["missing_declared_input_bits"]) == ["b_1"]
    assert missing["input_bit_recall"] == "0.800000"
