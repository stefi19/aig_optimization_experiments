from problem_a_cost import expression_cost, reduction_rate
from semantic_ast import SemanticExpr, input_expr
from semantic_types import unsigned_bitvector


def test_problem_a_inspired_cost_counts_operations():
    expr = SemanticExpr("add", (input_expr("a", 2), input_expr("b", 2)), unsigned_bitvector(2))
    assert expression_cost(expr) == 2
    mux = SemanticExpr("mux", (input_expr("s", 1), input_expr("a", 2), input_expr("b", 2)), unsigned_bitvector(2))
    assert expression_cost(mux) == 3


def test_reduction_rate_is_bounded_for_empty_gate_count():
    assert reduction_rate(1, 0) == 0.0
    assert reduction_rate(2, 10) == 80.0
