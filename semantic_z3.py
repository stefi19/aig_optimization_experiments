"""Z3 semantics for typed semantic AST expressions."""

from __future__ import annotations

try:  # pragma: no cover
    import z3
except Exception:  # pragma: no cover
    z3 = None  # type: ignore[assignment]

from semantic_ast import SemanticExpr


def _mask(width: int) -> int:
    return (1 << width) - 1


def bv(value: int, width: int) -> object:
    if z3 is None:
        raise RuntimeError("z3 is not installed")
    return z3.BitVecVal(value & _mask(width), width)


def resize(expr: object, from_width: int, to_width: int, *, signed: bool = False) -> object:
    if z3 is None:
        raise RuntimeError("z3 is not installed")
    if from_width == to_width:
        return expr
    if from_width > to_width:
        return z3.Extract(to_width - 1, 0, expr)
    extra = to_width - from_width
    return z3.SignExt(extra, expr) if signed else z3.ZeroExt(extra, expr)


def expr_to_z3(expr: SemanticExpr, env: dict[str, object]) -> object:
    if z3 is None:
        raise RuntimeError("z3 is not installed")
    op = expr.operator
    if op == "input":
        if expr.name not in env:
            raise KeyError(f"missing AST input: {expr.name}")
        value = env[expr.name]
        return resize(value, value.size(), expr.width, signed=expr.output_type.signed)  # type: ignore[attr-defined]
    if op == "const":
        return bv(expr.constant_value or 0, expr.width)
    args = [expr_to_z3(arg, env) for arg in expr.operands]
    arg_widths = [arg.width for arg in expr.operands]

    def r(value: object, width: int | None = None) -> object:
        return resize(value, width or value.size(), expr.width, signed=expr.output_type.signed)  # type: ignore[attr-defined]

    if op == "not":
        return r(~resize(args[0], arg_widths[0], expr.width))
    if op == "neg":
        return r(-resize(args[0], arg_widths[0], expr.width))
    if op in {"add", "sub", "mul", "and", "or", "xor", "xnor"}:
        left = resize(args[0], arg_widths[0], expr.width)
        right = resize(args[1], arg_widths[1], expr.width)
        if op == "add":
            out = left + right
        elif op == "sub":
            out = left - right
        elif op == "mul":
            out = left * right
        elif op == "and":
            out = left & right
        elif op == "or":
            out = left | right
        elif op == "xor":
            out = left ^ right
        else:
            out = ~(left ^ right)
        return r(out)
    if op in {"eq", "ne", "ult", "ule", "ugt", "uge", "slt", "sle", "sgt", "sge"}:
        width = max(arg_widths)
        left = resize(args[0], arg_widths[0], width, signed=op.startswith("s"))
        right = resize(args[1], arg_widths[1], width, signed=op.startswith("s"))
        pred = {
            "eq": left == right,
            "ne": left != right,
            "ult": z3.ULT(left, right),
            "ule": z3.ULE(left, right),
            "ugt": z3.UGT(left, right),
            "uge": z3.UGE(left, right),
            "slt": left < right,
            "sle": left <= right,
            "sgt": left > right,
            "sge": left >= right,
        }[op]
        return z3.If(pred, bv(1, expr.width), bv(0, expr.width))
    if op == "mux":
        return r(z3.If(z3.Extract(0, 0, args[0]) == bv(1, 1), resize(args[1], arg_widths[1], expr.width), resize(args[2], arg_widths[2], expr.width)))
    if op == "shl":
        return r(resize(args[0], arg_widths[0], expr.width) << int(expr.constant_value or 0))
    if op == "lshr":
        return r(z3.LShR(resize(args[0], arg_widths[0], expr.width), int(expr.constant_value or 0)))
    if op == "ashr":
        return r(resize(args[0], arg_widths[0], expr.width, signed=True) >> int(expr.constant_value or 0))
    if op == "slice":
        hi, lo = expr.slice_range or (expr.width - 1, 0)
        return resize(z3.Extract(hi, lo, args[0]), hi - lo + 1, expr.width)
    if op == "concat":
        out = args[0]
        for arg in args[1:]:
            out = z3.Concat(out, arg)
        return resize(out, sum(arg_widths), expr.width)
    if op == "zero_extend":
        return resize(args[0], arg_widths[0], expr.width)
    if op == "sign_extend":
        return resize(args[0], arg_widths[0], expr.width, signed=True)
    if op == "reduce_and":
        return z3.If(args[0] == bv(_mask(arg_widths[0]), arg_widths[0]), bv(1, expr.width), bv(0, expr.width))
    if op == "reduce_or":
        return z3.If(args[0] != bv(0, arg_widths[0]), bv(1, expr.width), bv(0, expr.width))
    if op in {"reduce_xor", "parity"}:
        bit = z3.Extract(0, 0, args[0])
        for idx in range(1, arg_widths[0]):
            bit = bit ^ z3.Extract(idx, idx, args[0])
        return resize(bit, 1, expr.width)
    if op == "mask_and":
        return r(resize(args[0], arg_widths[0], expr.width) & bv(expr.constant_value or 0, expr.width))
    if op == "mask_or":
        return r(resize(args[0], arg_widths[0], expr.width) | bv(expr.constant_value or 0, expr.width))
    if op == "mask_xor":
        return r(resize(args[0], arg_widths[0], expr.width) ^ bv(expr.constant_value or 0, expr.width))
    raise ValueError(f"unsupported semantic AST operator for Z3: {op}")
