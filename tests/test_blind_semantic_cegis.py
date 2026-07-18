import json
from pathlib import Path

import pytest

from blind_semantic_cegis import (
    BlindBus,
    assert_inference_schema,
    blind_bus_hypotheses,
    candidate_rows,
    parametric_templates,
    stable_anonymize,
)
from semantic_ast import input_expr


def test_ground_truth_leakage_guard_rejects_truth_fields():
    with pytest.raises(ValueError):
        assert_inference_schema({"region_id": "r0", "ground_truth_expression": "a+b"})
    with pytest.raises(ValueError):
        assert_inference_schema({"region_id": "r0", "operator": "add"})
    with pytest.raises(ValueError):
        assert_inference_schema({"region_id": "r0", "constants": '{"k":3}'})
    with pytest.raises(ValueError):
        assert_inference_schema({"region_id": "r0", "bit_order_accuracy": "1.0"})


def test_truth_mutations_do_not_change_blind_predictions():
    public = {"region_id": "r0", "case_id": "c0", "optimization": "dc2"}
    assert_inference_schema(public, allow_labels={"case_id"})
    left = blind_bus_hypotheses("r0", "input", ("a_0", "a_1", "b_0", "b_1"))
    right = blind_bus_hypotheses("r0", "input", ("a_0", "a_1", "b_0", "b_1"))
    assert left == right


def test_anonymisation_is_deterministic_and_operand_only():
    names = ["sum_0", "a_1", "a_0", "carry"]
    first = stable_anonymize(names)
    second = stable_anonymize(list(reversed(names)))
    assert first == second
    assert set(first) == set(names)
    assert set(first.values()) == {"s0000", "s0001", "s0002", "s0003"}


def test_blind_bus_inference_deterministic_without_truth_names():
    rows = blind_bus_hypotheses("r1", "output", ("y_0", "y_1", "y_2"))
    assert rows == blind_bus_hypotheses("r1", "output", ("y_0", "y_1", "y_2"))
    assert rows[0]["used_ground_truth_for_generation"] == "false"
    assert "ground_truth_bus_name_if_known" not in rows[0]
    assert "ground_truth_match" not in rows[0]


def test_parametric_templates_cover_required_arithmetic_families():
    buses = [BlindBus("a", "data_operand", ("a_0", "a_1"), 2), BlindBus("b", "data_operand", ("b_0", "b_1"), 2), BlindBus("c", "data_operand", ("c_0", "c_1"), 2)]
    families = {family for family, _, _ in parametric_templates(buses, 2)}
    assert {"affine", "constant_multiply", "shifted_arithmetic", "truncated_multiply", "add_add", "multiply_accumulate", "masked_boolean"} <= families


def test_expression_rtl_emission_from_parametric_candidate():
    rows = candidate_rows("r2", [BlindBus("a", "data_operand", ("a_0",), 1)], 1, max_candidates=4)
    assert rows
    assert rows[0]["generated_without_ground_truth"] == "true"
    assert rows[0]["rtl_text"]
    assert json.loads(rows[0]["expression_json"])["op"]


def test_committed_cegis_trace_contains_counterexample_refinement():
    path = Path(__file__).resolve().parents[1] / "results" / "blind_semantic_cegis" / "cegis_iterations.csv"
    if not path.exists():
        pytest.skip("blind CEGIS results have not been generated")
    import csv

    with path.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    cex_rows = [row for row in rows if row["solver_status"] == "sat"]
    assert cex_rows
    assert all(int(row["examples_after"]) > int(row["examples_before"]) for row in cex_rows)
