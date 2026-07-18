import pytest

z3 = pytest.importorskip("z3")

from blif_z3 import encode_blif, pack_bus
from semantic_ast import SemanticExpr, const_expr, input_expr
from semantic_types import unsigned_bitvector
from semantic_z3 import expr_to_z3
from semantic_z3_validation import validate_candidate_z3


def write_blif(tmp_path, text):
    path = tmp_path / "case.blif"
    path.write_text(text, encoding="utf-8")
    return path


def test_z3_import_smoke():
    x = z3.BitVec("x_smoke", 8)
    solver = z3.Solver()
    solver.add(x + 1 == 6)
    assert solver.check() == z3.sat
    assert solver.model()[x].as_long() == 5


def test_blif_z3_constants_inversion_and_multicube(tmp_path):
    path = write_blif(
        tmp_path,
        """.model c
.inputs a b
.outputs z c0 o n
.names c0
.names o
1
.names a n
0 1
.names a b z
1- 1
-1 1
.end
""",
    )
    enc = encode_blif(path)
    solver = z3.Solver()
    solver.add(enc.values["z"] != z3.Or(enc.values["a"], enc.values["b"]))
    solver.add(enc.values["c0"] != z3.BoolVal(False))
    solver.add(enc.values["o"] != z3.BoolVal(True))
    solver.add(enc.values["n"] != z3.Not(enc.values["a"]))
    assert solver.check() == z3.unsat


def test_blif_z3_dont_care_and_bus_order(tmp_path):
    path = write_blif(
        tmp_path,
        """.model c
.inputs a0 a1
.outputs y0 y1
.names a0 y0
1 1
.names a1 y1
1 1
.end
""",
    )
    enc = encode_blif(path)
    bus = pack_bus(enc.values, ("y0", "y1"))
    solver = z3.Solver()
    solver.add(enc.values["a0"])
    solver.add(z3.Not(enc.values["a1"]))
    assert solver.check() == z3.sat
    assert solver.model().eval(bus, model_completion=True).as_long() == 1


def test_semantic_ast_z3_fixed_width_arithmetic():
    a = z3.BitVec("a_ast", 4)
    expr = SemanticExpr("mul", (input_expr("a", 4), const_expr(9, 4)), output_type=unsigned_bitvector(4))
    solver = z3.Solver()
    solver.add(a == 3)
    assert solver.check() == z3.sat
    assert solver.model().eval(expr_to_z3(expr, {"a": a}), model_completion=True).as_long() == 11


def test_validate_candidate_z3_equivalent_and_counterexample(tmp_path):
    path = write_blif(
        tmp_path,
        """.model c
.inputs a0 a1
.outputs y0 y1
.names a0 y0
1 1
.names a1 y1
1 1
.end
""",
    )
    bus = {"name": "a", "width": 2, "ordered_member_nodes": ("a0", "a1"), "role": "data_operand"}
    out = {"name": "y", "width": 2, "ordered_member_nodes": ("y0", "y1"), "role": "output"}
    ok = validate_candidate_z3(blif_path=path, input_buses=[bus], output_bus=out, expr=input_expr("a", 2))
    assert ok["formal_status"] == "formally_verified_region"
    bad = validate_candidate_z3(blif_path=path, input_buses=[bus], output_bus=out, expr=const_expr(0, 2))
    assert bad["formal_status"] == "disproven"
    assert bad["counterexample_available"] == "true"
    assert bad["counterexample_reproduced"] == "true"
