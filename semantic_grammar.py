"""Bounded direct-template grammars for Phase 4 semantic recovery."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations, permutations

from semantic_ast import SemanticExpr, const_expr, input_expr
from semantic_types import SemanticType, boolean_scalar, unsigned_bitvector


GRAMMAR_FAMILIES = (
    "arithmetic_direct",
    "boolean_direct",
    "control_direct",
    "comparison_direct",
    "bitmanip_direct",
)


@dataclass(frozen=True)
class GrammarConfig:
    max_candidates_per_family: int = 24
    max_total_candidates_per_region: int = 96
    max_expression_depth: int = 3
    max_constant_candidates: int = 6
    max_shift_amount: int = 4


def output_type(width: int, signed: bool = False) -> SemanticType:
    return boolean_scalar() if width == 1 and not signed else SemanticType("bitvector", width, signed)


def input_bus_exprs(input_buses: list[dict[str, object]]) -> dict[str, SemanticExpr]:
    return {
        str(bus["name"]): input_expr(str(bus["name"]), int(bus["width"]), bool(bus.get("signed", False)))
        for bus in input_buses
    }


def data_buses(input_buses: list[dict[str, object]]) -> list[dict[str, object]]:
    return [bus for bus in input_buses if str(bus.get("role", "data_operand")) in {"data_operand", "output", "unknown"}]


def control_buses(input_buses: list[dict[str, object]]) -> list[dict[str, object]]:
    return [bus for bus in input_buses if str(bus.get("role", "")) in {"control", "selector"} or int(bus["width"]) <= 2 and str(bus["name"]).lower().startswith(("s", "sel", "ctrl"))]


def constants_for_region(manifest_constants: dict[str, int], output_width: int, config: GrammarConfig) -> list[int]:
    values = [int(v) for v in manifest_constants.values()]
    values.extend([0, 1, 2, 3, (1 << min(output_width, 8)) - 1])
    return sorted(set(v for v in values if v >= 0))[: config.max_constant_candidates]


def make_expr(operator: str, operands: tuple[SemanticExpr, ...], width: int, *, signed: bool = False, constant: int | None = None, slice_range: tuple[int, int] | None = None, extension_mode: str = "none") -> SemanticExpr:
    return SemanticExpr(operator, operands=operands, output_type=output_type(width, signed), constant_value=constant, slice_range=slice_range, extension_mode=extension_mode)


def arithmetic_candidates(input_buses: list[dict[str, object]], output_width: int, constants: list[int], config: GrammarConfig) -> list[SemanticExpr]:
    exprs = input_bus_exprs(input_buses)
    data = data_buses(input_buses)
    rows: list[SemanticExpr] = []
    for bus in data:
        a = exprs[str(bus["name"])]
        rows.append(make_expr("input", tuple(), output_width, signed=bool(bus.get("signed", False))) if False else make_expr("zero_extend" if output_width >= a.width else "slice", (a,), output_width, slice_range=(output_width - 1, 0) if output_width < a.width else None))
        rows.append(make_expr("neg", (a,), output_width, signed=bool(bus.get("signed", False))))
        for k in constants:
            c = const_expr(k, output_width)
            rows.append(make_expr("add", (a, c), output_width))
            rows.append(make_expr("sub", (a, c), output_width))
            rows.append(make_expr("mul", (a, c), output_width))
    for left, right in combinations(data, 2):
        a, b = exprs[str(left["name"])], exprs[str(right["name"])]
        rows.extend([
            make_expr("add", (a, b), output_width),
            make_expr("sub", (a, b), output_width),
            make_expr("sub", (b, a), output_width),
            make_expr("mul", (a, b), output_width),
        ])
        for shift in range(1, min(config.max_shift_amount, max(a.width, b.width) - 1) + 1):
            rows.append(make_expr("add", (make_expr("shl", (a,), output_width, constant=shift), b), output_width))
            rows.append(make_expr("sub", (make_expr("shl", (a,), output_width, constant=shift), b), output_width))
    for triple in combinations(data, 3):
        a, b, c = [exprs[str(bus["name"])] for bus in triple]
        rows.append(make_expr("add", (make_expr("add", (a, b), output_width), c), output_width))
        rows.append(make_expr("add", (make_expr("mul", (a, b), output_width), c), output_width))
        rows.append(make_expr("add", (c, make_expr("mul", (a, b), output_width)), output_width))
    return rows[: config.max_candidates_per_family]


def boolean_candidates(input_buses: list[dict[str, object]], output_width: int, config: GrammarConfig) -> list[SemanticExpr]:
    exprs = input_bus_exprs(input_buses)
    data = data_buses(input_buses)
    rows: list[SemanticExpr] = []
    for bus in data:
        a = exprs[str(bus["name"])]
        rows.append(make_expr("not", (a,), output_width))
        if output_width == 1:
            rows.extend([make_expr("reduce_and", (a,), 1), make_expr("reduce_or", (a,), 1), make_expr("reduce_xor", (a,), 1), make_expr("parity", (a,), 1)])
    for left, right in combinations(data, 2):
        a, b = exprs[str(left["name"])], exprs[str(right["name"])]
        rows.extend([make_expr("and", (a, b), output_width), make_expr("or", (a, b), output_width), make_expr("xor", (a, b), output_width), make_expr("xnor", (a, b), output_width)])
    for triple in combinations(data, 3):
        if output_width == int(triple[0]["width"]):
            rows.append(make_expr("majority", tuple(exprs[str(bus["name"])] for bus in triple), output_width))
    return rows[: config.max_candidates_per_family]


def comparison_candidates(input_buses: list[dict[str, object]], output_width: int, config: GrammarConfig) -> list[SemanticExpr]:
    if output_width != 1:
        return []
    exprs = input_bus_exprs(input_buses)
    rows: list[SemanticExpr] = []
    for left, right in combinations(data_buses(input_buses), 2):
        a, b = exprs[str(left["name"])], exprs[str(right["name"])]
        for op in ("eq", "ne", "ult", "ule", "ugt", "uge", "slt", "sle", "sgt", "sge"):
            rows.append(make_expr(op, (a, b), 1))
    return rows[: config.max_candidates_per_family]


def control_candidates(input_buses: list[dict[str, object]], output_width: int, config: GrammarConfig) -> list[SemanticExpr]:
    exprs = input_bus_exprs(input_buses)
    controls = [bus for bus in control_buses(input_buses) if int(bus["width"]) == 1]
    data = data_buses(input_buses)
    rows: list[SemanticExpr] = []
    for sel in controls:
        s = exprs[str(sel["name"])]
        for left, right in permutations(data, 2):
            rows.append(make_expr("mux", (s, exprs[str(left["name"])], exprs[str(right["name"])]), output_width))
    return rows[: config.max_candidates_per_family]


def bitmanip_candidates(input_buses: list[dict[str, object]], output_width: int, constants: list[int], config: GrammarConfig) -> list[SemanticExpr]:
    exprs = input_bus_exprs(input_buses)
    data = data_buses(input_buses)
    rows: list[SemanticExpr] = []
    for bus in data:
        a = exprs[str(bus["name"])]
        if output_width <= a.width:
            rows.append(make_expr("slice", (a,), output_width, slice_range=(output_width - 1, 0)))
        elif output_width > a.width:
            rows.append(make_expr("zero_extend", (a,), output_width, extension_mode="zero_extend"))
            rows.append(make_expr("sign_extend", (a,), output_width, signed=True, extension_mode="sign_extend"))
        for shift in range(1, min(config.max_shift_amount, max(1, a.width - 1)) + 1):
            rows.append(make_expr("shl", (a,), output_width, constant=shift))
            rows.append(make_expr("lshr", (a,), output_width, constant=shift))
            rows.append(make_expr("ashr", (a,), output_width, signed=True, constant=shift))
        for k in constants:
            rows.append(make_expr("mask_and", (a,), output_width, constant=k))
            rows.append(make_expr("mask_or", (a,), output_width, constant=k))
            rows.append(make_expr("mask_xor", (a,), output_width, constant=k))
    for left, right in permutations(data, 2):
        if int(left["width"]) + int(right["width"]) == output_width:
            rows.append(make_expr("concat", (exprs[str(left["name"])], exprs[str(right["name"])]), output_width))
    return rows[: config.max_candidates_per_family]


def generate_direct_candidates(
    *,
    input_buses: list[dict[str, object]],
    output_width: int,
    manifest_constants: dict[str, int] | None = None,
    family_order: list[str] | None = None,
    config: GrammarConfig | None = None,
) -> list[tuple[str, SemanticExpr]]:
    config = config or GrammarConfig()
    manifest_constants = manifest_constants or {}
    constants = constants_for_region(manifest_constants, output_width, config)
    family_order = family_order or list(GRAMMAR_FAMILIES)
    by_family = {
        "arithmetic_direct": lambda: arithmetic_candidates(input_buses, output_width, constants, config),
        "boolean_direct": lambda: boolean_candidates(input_buses, output_width, config),
        "control_direct": lambda: control_candidates(input_buses, output_width, config),
        "comparison_direct": lambda: comparison_candidates(input_buses, output_width, config),
        "bitmanip_direct": lambda: bitmanip_candidates(input_buses, output_width, constants, config),
    }
    rows: list[tuple[str, SemanticExpr]] = []
    seen: set[str] = set()
    for family in family_order:
        for expr in by_family.get(family, lambda: [])():
            if expr.expression_depth > config.max_expression_depth:
                continue
            if expr.canonical_form in seen:
                continue
            seen.add(expr.canonical_form)
            rows.append((family, expr))
            if len(rows) >= config.max_total_candidates_per_region:
                return rows
    return rows
