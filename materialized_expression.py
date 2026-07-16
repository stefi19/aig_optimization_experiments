"""Materialized Boolean expression records for anchored-cut functions."""

from __future__ import annotations

from dataclasses import dataclass

from cut_function_extraction import CutFunction


@dataclass(frozen=True)
class MaterializedExpression:
    expression_id: str
    cut_id: str
    target_impl_node: str
    expression_ast: str
    expression_text: str
    truth_table_hash: str
    operator_count: int
    logic_node_count: int
    expression_depth: int
    estimated_cost: int
    minimization_backend: str
    canonical_hash: str


def expression_from_truth_table(fn: CutFunction) -> MaterializedExpression:
    """Represent the cut function as an exact BLIF-LUT/SOP expression."""

    ones = [idx for idx, bit in enumerate(fn.truth_table) if bit]
    width = len(fn.support_leaf_order)
    if not ones:
        text = "1'b0"
        op_count = 0
        depth = 0
    elif len(ones) == (1 << width):
        text = "1'b1"
        op_count = 0
        depth = 0
    else:
        terms = []
        for idx in ones:
            lits = []
            for bit, leaf in enumerate(fn.support_leaf_order):
                lits.append(leaf if (idx >> bit) & 1 else f"!{leaf}")
            terms.append("(" + " & ".join(lits) + ")")
        text = " | ".join(terms)
        op_count = sum(max(0, width - 1) for _ in terms) + max(0, len(terms) - 1)
        depth = 1 if width <= 1 else 2
    return MaterializedExpression(
        expression_id=f"expr_{fn.truth_table_hash}",
        cut_id=fn.cut_id,
        target_impl_node=fn.target_impl_node,
        expression_ast="truth_table_lut:" + "".join(str(bit) for bit in fn.truth_table),
        expression_text=text,
        truth_table_hash=fn.truth_table_hash,
        operator_count=op_count,
        logic_node_count=1,
        expression_depth=depth,
        estimated_cost=max(1, op_count),
        minimization_backend="truth_table_direct",
        canonical_hash=fn.truth_table_hash,
    )


def expression_to_row(expr: MaterializedExpression, *, case_id: str, benchmark: str, optimization: str, coi_name: str) -> dict[str, object]:
    return {
        "case_id": case_id,
        "benchmark": benchmark,
        "optimization": optimization,
        "coi_name": coi_name,
        "expression_id": expr.expression_id,
        "cut_id": expr.cut_id,
        "target_impl_node": expr.target_impl_node,
        "expression_ast": expr.expression_ast,
        "expression_text": expr.expression_text,
        "truth_table_hash": expr.truth_table_hash,
        "operator_count": expr.operator_count,
        "logic_node_count": expr.logic_node_count,
        "expression_depth": expr.expression_depth,
        "estimated_cost": expr.estimated_cost,
        "minimization_backend": expr.minimization_backend,
        "canonical_hash": expr.canonical_hash,
    }
