import json

from semantic_ast import SemanticExpr, const_expr, expr_from_tree, input_expr
from semantic_grammar import generate_direct_candidates
from semantic_types import signed_bitvector, to_signed, unsigned_bitvector


def test_signed_and_unsigned_types_are_distinct():
    assert unsigned_bitvector(4) != signed_bitvector(4)
    assert signed_bitvector(4).signedness == "signed"


def test_width_truncation_and_signed_conversion():
    expr = SemanticExpr("add", (input_expr("a", 2), input_expr("b", 2)), unsigned_bitvector(2))
    assert expr.eval({"a": 3, "b": 1}) == 0
    assert to_signed(0b11, 2) == -1


def test_commutative_canonicalization_deduplicates():
    left = SemanticExpr("add", (input_expr("a", 2), input_expr("b", 2)), unsigned_bitvector(2))
    right = SemanticExpr("add", (input_expr("b", 2), input_expr("a", 2)), unsigned_bitvector(2))
    assert left.canonical_form == right.canonical_form


def test_expression_json_round_trip():
    expr = SemanticExpr("mul", (input_expr("a", 3), const_expr(3, 3)), unsigned_bitvector(3))
    restored = expr_from_tree(json.loads(expr.to_csv_fields()["expression_json"]))
    assert restored.canonical_form == expr.canonical_form
    assert restored.eval({"a": 2}) == 6


def test_direct_grammar_generates_add_and_mux_candidates():
    buses = [
        {"name": "a", "width": 2, "role": "data_operand"},
        {"name": "b", "width": 2, "role": "data_operand"},
        {"name": "s", "width": 1, "role": "selector"},
    ]
    rows = generate_direct_candidates(input_buses=buses, output_width=2)
    ops = {expr.operator for _, expr in rows}
    assert "add" in ops
    assert "mux" in ops
