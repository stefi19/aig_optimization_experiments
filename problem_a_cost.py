"""Problem-A-inspired RTL cost for verified semantic expressions.

This is not the official contest scorer.  It is a deterministic lightweight
proxy that rewards compact high-level RTL over gate-level primitive fallback.
"""

from __future__ import annotations

from semantic_ast import SemanticExpr


OP_WEIGHTS = {
    "input": 0,
    "const": 0,
    "add": 2,
    "sub": 2,
    "mul": 4,
    "neg": 1,
    "not": 1,
    "and": 1,
    "or": 1,
    "xor": 1,
    "xnor": 2,
    "eq": 2,
    "ne": 2,
    "ult": 2,
    "ule": 2,
    "ugt": 2,
    "uge": 2,
    "slt": 2,
    "sle": 2,
    "sgt": 2,
    "sge": 2,
    "mux": 3,
    "shl": 1,
    "lshr": 1,
    "ashr": 1,
    "slice": 1,
    "concat": 1,
    "zero_extend": 1,
    "sign_extend": 1,
    "reduce_and": 1,
    "reduce_or": 1,
    "reduce_xor": 1,
    "parity": 1,
    "majority": 3,
    "mask_and": 1,
    "mask_or": 1,
    "mask_xor": 1,
}


def expression_cost(expr: SemanticExpr) -> int:
    return OP_WEIGHTS.get(expr.operator, 5) + sum(expression_cost(operand) for operand in expr.operands)


def reduction_rate(candidate_rtl_cost: int, input_gate_count: int) -> float:
    if input_gate_count <= 0:
        return 0.0
    return (1.0 - candidate_rtl_cost / input_gate_count) * 100.0
