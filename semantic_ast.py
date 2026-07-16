"""Typed semantic expression AST for bounded direct-template recovery."""

from __future__ import annotations

import json
from dataclasses import dataclass, field

from semantic_types import SemanticType, from_signed, mask, to_signed, truncate, unsigned_bitvector


SEMANTIC_AST_SCHEMA_VERSION = "semantic_ast_v1"
COMMUTATIVE = {"add", "mul", "and", "or", "xor", "xnor", "eq", "ne"}


@dataclass(frozen=True)
class SemanticExpr:
    operator: str
    operands: tuple["SemanticExpr", ...] = field(default_factory=tuple)
    output_type: SemanticType = field(default_factory=lambda: unsigned_bitvector(1))
    name: str = ""
    constant_value: int | None = None
    slice_range: tuple[int, int] | None = None
    extension_mode: str = "none"
    truncation_mode: str = "explicit_low_bits"

    @property
    def width(self) -> int:
        return self.output_type.width

    @property
    def signedness(self) -> str:
        return self.output_type.signedness

    @property
    def expression_depth(self) -> int:
        if not self.operands:
            return 0
        return 1 + max(operand.expression_depth for operand in self.operands)

    @property
    def canonical_form(self) -> str:
        if self.operator == "input":
            return self.name
        if self.operator == "const":
            return f"{self.width}'d{self.constant_value or 0}"
        parts = [operand.canonical_form for operand in self.operands]
        if self.operator in COMMUTATIVE:
            parts = sorted(parts)
        suffix = ""
        if self.slice_range:
            suffix = f"[{self.slice_range[0]}:{self.slice_range[1]}]"
        return f"{self.operator}<{self.width},{self.signedness}>({','.join(parts)}){suffix}"

    @property
    def expression_id(self) -> str:
        return self.canonical_form

    @property
    def rtl_text(self) -> str:
        if self.operator == "input":
            return self.name
        if self.operator == "const":
            return f"{self.width}'d{self.constant_value or 0}"
        if self.operator == "not":
            return f"~{self.operands[0].rtl_text}"
        if self.operator == "neg":
            return f"-{self.operands[0].rtl_text}"
        if self.operator in {"add", "sub", "mul", "and", "or", "xor", "eq", "ne", "ult", "ule", "ugt", "uge", "slt", "sle", "sgt", "sge"}:
            op = {
                "add": "+",
                "sub": "-",
                "mul": "*",
                "and": "&",
                "or": "|",
                "xor": "^",
                "eq": "==",
                "ne": "!=",
                "ult": "<",
                "ule": "<=",
                "ugt": ">",
                "uge": ">=",
                "slt": "<",
                "sle": "<=",
                "sgt": ">",
                "sge": ">=",
            }[self.operator]
            return f"({self.operands[0].rtl_text} {op} {self.operands[1].rtl_text})"
        if self.operator == "xnor":
            return f"~({self.operands[0].rtl_text} ^ {self.operands[1].rtl_text})"
        if self.operator == "mux":
            return f"({self.operands[0].rtl_text} ? {self.operands[1].rtl_text} : {self.operands[2].rtl_text})"
        if self.operator == "shl":
            return f"({self.operands[0].rtl_text} << {self.constant_value})"
        if self.operator == "lshr":
            return f"({self.operands[0].rtl_text} >> {self.constant_value})"
        if self.operator == "ashr":
            return f"($signed({self.operands[0].rtl_text}) >>> {self.constant_value})"
        if self.operator == "slice":
            hi, lo = self.slice_range or (self.width - 1, 0)
            return f"{self.operands[0].rtl_text}[{hi}:{lo}]" if hi != lo else f"{self.operands[0].rtl_text}[{lo}]"
        if self.operator == "concat":
            return "{" + ", ".join(operand.rtl_text for operand in self.operands) + "}"
        if self.operator == "zero_extend":
            extra = max(0, self.width - self.operands[0].width)
            return f"{{{extra}'d0, {self.operands[0].rtl_text}}}" if extra else self.operands[0].rtl_text
        if self.operator == "sign_extend":
            extra = max(0, self.width - self.operands[0].width)
            return f"{{{{{extra}{{{self.operands[0].rtl_text}[{self.operands[0].width - 1}]}}}}, {self.operands[0].rtl_text}}}" if extra else self.operands[0].rtl_text
        if self.operator == "reduce_and":
            return f"&{self.operands[0].rtl_text}"
        if self.operator == "reduce_or":
            return f"|{self.operands[0].rtl_text}"
        if self.operator in {"reduce_xor", "parity"}:
            return f"^{self.operands[0].rtl_text}"
        if self.operator == "majority":
            a, b, c = [operand.rtl_text for operand in self.operands]
            return f"(({a} & {b}) | ({a} & {c}) | ({b} & {c}))"
        if self.operator == "mask_and":
            return f"({self.operands[0].rtl_text} & {self.width}'d{self.constant_value or 0})"
        if self.operator == "mask_or":
            return f"({self.operands[0].rtl_text} | {self.width}'d{self.constant_value or 0})"
        if self.operator == "mask_xor":
            return f"({self.operands[0].rtl_text} ^ {self.width}'d{self.constant_value or 0})"
        return self.canonical_form

    @property
    def rtl_cost(self) -> int:
        return 1 + sum(operand.rtl_cost for operand in self.operands)

    def to_csv_fields(self) -> dict[str, str]:
        return {
            "expression_id": self.expression_id,
            "operator": self.operator,
            "operands": json.dumps([operand.expression_id for operand in self.operands], sort_keys=True, separators=(",", ":")),
            "input_types": json.dumps([operand.output_type.to_dict() for operand in self.operands], sort_keys=True, separators=(",", ":")),
            "output_type": json.dumps(self.output_type.to_dict(), sort_keys=True, separators=(",", ":")),
            "width": str(self.width),
            "signedness": self.signedness,
            "extension_mode": self.extension_mode,
            "truncation_mode": self.truncation_mode,
            "slice_range": json.dumps(list(self.slice_range) if self.slice_range else [], separators=(",", ":")),
            "constant_value": "" if self.constant_value is None else str(self.constant_value),
            "expression_depth": str(self.expression_depth),
            "canonical_form": self.canonical_form,
            "rtl_text": self.rtl_text,
            "rtl_cost": str(self.rtl_cost),
            "schema_version": SEMANTIC_AST_SCHEMA_VERSION,
            "expression_json": json.dumps(self.to_tree(), sort_keys=True, separators=(",", ":")),
        }

    def to_tree(self) -> dict[str, object]:
        return {
            "op": self.operator,
            "args": [operand.to_tree() for operand in self.operands],
            "t": [self.output_type.kind, self.output_type.width, self.output_type.signed],
            "n": self.name,
            "c": self.constant_value,
            "s": list(self.slice_range) if self.slice_range else [],
            "e": self.extension_mode,
            "tr": self.truncation_mode,
        }

    def eval(self, env: dict[str, int]) -> int:
        op = self.operator
        if op == "input":
            return truncate(env.get(self.name, 0), self.width)
        if op == "const":
            return truncate(self.constant_value or 0, self.width)
        values = [operand.eval(env) for operand in self.operands]
        if op == "not":
            return truncate(~values[0], self.width)
        if op == "neg":
            return truncate(-values[0], self.width)
        if op == "add":
            return truncate(values[0] + values[1], self.width)
        if op == "sub":
            return truncate(values[0] - values[1], self.width)
        if op == "mul":
            return truncate(values[0] * values[1], self.width)
        if op == "and":
            return truncate(values[0] & values[1], self.width)
        if op == "or":
            return truncate(values[0] | values[1], self.width)
        if op == "xor":
            return truncate(values[0] ^ values[1], self.width)
        if op == "xnor":
            return truncate(~(values[0] ^ values[1]), self.width)
        if op == "eq":
            return int(values[0] == values[1])
        if op == "ne":
            return int(values[0] != values[1])
        if op in {"ult", "ule", "ugt", "uge"}:
            return int({"ult": values[0] < values[1], "ule": values[0] <= values[1], "ugt": values[0] > values[1], "uge": values[0] >= values[1]}[op])
        if op in {"slt", "sle", "sgt", "sge"}:
            width = max(self.operands[0].width, self.operands[1].width)
            left, right = to_signed(values[0], width), to_signed(values[1], width)
            return int({"slt": left < right, "sle": left <= right, "sgt": left > right, "sge": left >= right}[op])
        if op == "mux":
            return truncate(values[1] if values[0] & 1 else values[2], self.width)
        if op == "shl":
            return truncate(values[0] << int(self.constant_value or 0), self.width)
        if op == "lshr":
            return truncate(values[0] >> int(self.constant_value or 0), self.width)
        if op == "ashr":
            return from_signed(to_signed(values[0], self.operands[0].width) >> int(self.constant_value or 0), self.width)
        if op == "slice":
            hi, lo = self.slice_range or (self.width - 1, 0)
            return truncate(values[0] >> lo, hi - lo + 1)
        if op == "concat":
            result = 0
            for value, operand in zip(values, self.operands):
                result = (result << operand.width) | truncate(value, operand.width)
            return truncate(result, self.width)
        if op in {"zero_extend", "sign_extend"}:
            if op == "sign_extend" and self.operands[0].width < self.width:
                return from_signed(to_signed(values[0], self.operands[0].width), self.width)
            return truncate(values[0], self.width)
        if op == "reduce_and":
            return int(values[0] == mask(self.operands[0].width))
        if op == "reduce_or":
            return int(values[0] != 0)
        if op in {"reduce_xor", "parity"}:
            return values[0].bit_count() & 1
        if op == "majority":
            return truncate((values[0] & values[1]) | (values[0] & values[2]) | (values[1] & values[2]), self.width)
        if op == "mask_and":
            return truncate(values[0] & int(self.constant_value or 0), self.width)
        if op == "mask_or":
            return truncate(values[0] | int(self.constant_value or 0), self.width)
        if op == "mask_xor":
            return truncate(values[0] ^ int(self.constant_value or 0), self.width)
        raise ValueError(f"unsupported operator: {op}")


def input_expr(name: str, width: int, signed: bool = False) -> SemanticExpr:
    return SemanticExpr("input", output_type=SemanticType("bitvector" if width > 1 else "boolean", width, signed), name=name)


def const_expr(value: int, width: int, signed: bool = False) -> SemanticExpr:
    return SemanticExpr("const", output_type=SemanticType("bitvector" if width > 1 else "boolean", width, signed), constant_value=value)


def expr_from_tree(tree: dict[str, object]) -> SemanticExpr:
    typ = tree.get("output_type", tree.get("t"))
    if isinstance(typ, dict):
        kind, width, signed = str(typ["kind"]), int(typ["width"]), bool(typ.get("signed", False))
    else:
        assert isinstance(typ, list)
        kind, width, signed = str(typ[0]), int(typ[1]), bool(typ[2])
    return SemanticExpr(
        str(tree.get("operator", tree.get("op"))),
        operands=tuple(expr_from_tree(child) for child in tree.get("operands", tree.get("args", []))),  # type: ignore[arg-type]
        output_type=SemanticType(kind, width, signed),
        name=str(tree.get("name", tree.get("n", ""))),
        constant_value=None if tree.get("constant_value", tree.get("c")) is None else int(tree.get("constant_value", tree.get("c"))),  # type: ignore[arg-type]
        slice_range=tuple(int(v) for v in tree.get("slice_range", tree.get("s", []))) if tree.get("slice_range", tree.get("s", [])) else None,  # type: ignore[arg-type]
        extension_mode=str(tree.get("extension_mode", tree.get("e", "none"))),
        truncation_mode=str(tree.get("truncation_mode", tree.get("tr", "explicit_low_bits"))),
    )
