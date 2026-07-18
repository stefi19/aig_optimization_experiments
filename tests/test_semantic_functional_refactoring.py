import csv
import os
import subprocess
import sys

import pytest

pytest.importorskip("z3")

from semantic_ast import SemanticExpr, const_expr, input_expr
from semantic_functional_refactoring import (
    SemanticDivisor,
    divisor_is_identity,
    make_bus,
    prove_decomposability_z3,
    prove_quotient_depends_on_m,
    prove_quotient_equivalence_z3,
    synthesize_truth_table_quotient,
    write_refactored_blif,
)
from semantic_types import unsigned_bitvector


ROOT = __import__("pathlib").Path(__file__).resolve().parents[1]
ABC = ROOT / ".abc_build" / "abc_repo" / "abc"


def _abc_available():
    override = os.environ.get("AIG_ABC")
    return __import__("pathlib").Path(override).exists() if override else ABC.exists()


def write_xor_residual(tmp_path):
    path = tmp_path / "xor_residual.blif"
    path.write_text(
        """.model xor_residual
.inputs x z
.outputs y
.names x z y
10 1
01 1
.end
""",
        encoding="utf-8",
    )
    return path


def one_bit_divisor(member="x"):
    x = input_expr("x", 1)
    return SemanticDivisor(
        "d_x",
        "case",
        "test_source_blind",
        (make_bus("x", (member,)),),
        (make_bus("m", ("m0",), "semantic_divisor"),),
        (x,),
        "identity_bit",
        1,
    )


def test_two_copy_miter_proves_decomposable_with_residual(tmp_path):
    path = write_xor_residual(tmp_path)
    proof = prove_decomposability_z3(blif_path=path, divisor=one_bit_divisor(), residual_support=("z",), output_nodes=("y",))
    assert proof["formal_status"] == "decomposable"
    assert proof["solver_result"] == "unsat"


def test_two_copy_miter_finds_and_reproduces_counterexample(tmp_path):
    path = write_xor_residual(tmp_path)
    proof = prove_decomposability_z3(blif_path=path, divisor=one_bit_divisor(), residual_support=tuple(), output_nodes=("y",))
    assert proof["formal_status"] == "non_decomposable"
    assert proof["solver_result"] == "sat"
    assert proof["counterexample_reproduced"] == "true"


def test_truth_table_quotient_is_independently_proved(tmp_path):
    path = write_xor_residual(tmp_path)
    divisor = one_bit_divisor()
    quotient, meta = synthesize_truth_table_quotient(blif_path=path, divisor=divisor, residual_support=("z",), output_nodes=("y",), candidate_id="c")
    assert quotient is not None
    assert meta["quotient_status"] == "synthesized_truth_table"
    proof = prove_quotient_equivalence_z3(original_blif=path, divisor=divisor, quotient=quotient, output_nodes=("y",))
    assert proof["formal_status"] == "quotient_equivalent"
    nonvac = prove_quotient_depends_on_m(quotient)
    assert nonvac["quotient_depends_on_m"] == "true"


def test_vacuous_and_identity_decompositions_are_detected(tmp_path):
    path = tmp_path / "z_only.blif"
    path.write_text(
        """.model z_only
.inputs x z
.outputs y
.names z y
1 1
.end
""",
        encoding="utf-8",
    )
    divisor = one_bit_divisor()
    quotient, _ = synthesize_truth_table_quotient(blif_path=path, divisor=divisor, residual_support=("z",), output_nodes=("y",), candidate_id="c")
    assert quotient is not None
    assert prove_quotient_depends_on_m(quotient)["quotient_depends_on_m"] == "false"

    identity = SemanticDivisor(
        "identity",
        "case",
        "test_source_blind",
        (make_bus("x", ("x",)), make_bus("z", ("z",))),
        (make_bus("m", ("m0",), "semantic_divisor"), make_bus("n", ("m1",), "semantic_divisor")),
        (input_expr("x", 1), input_expr("z", 1)),
        "identity",
        2,
    )
    assert divisor_is_identity(identity, ("x", "z")) is True


def test_graph_active_refactoring_rewrite_passes_abc_when_available(tmp_path):
    path = write_xor_residual(tmp_path)
    divisor = one_bit_divisor()
    quotient, _ = synthesize_truth_table_quotient(blif_path=path, divisor=divisor, residual_support=("z",), output_nodes=("y",), candidate_id="c")
    out = tmp_path / "refactored.blif"
    result = write_refactored_blif(original_blif=path, divisor=divisor, quotient=quotient, output_path=out, window_outputs=("y",))
    assert result["graph_rewrite_status"] == "valid"
    assert result["graph_active"] == "true"
    assert out.exists()


def test_functional_refactoring_runner_and_checker(tmp_path):
    out_dir = tmp_path / "functional_results"
    bench_dir = tmp_path / "functional_bench"
    subprocess.run(
        [
            sys.executable,
            "scripts/run_semantic_functional_refactoring.py",
            "--mode",
            "controlled",
            "--output-dir",
            str(out_dir),
            "--bench-dir",
            str(bench_dir),
        ],
        cwd=ROOT,
        check=True,
    )
    checker = [sys.executable, "scripts/check_semantic_functional_refactoring_results.py", "--output-dir", str(out_dir)]
    if not _abc_available():
        checker.append("--allow-no-abc")
    subprocess.run(checker, cwd=ROOT, check=True)
    rows = list(csv.DictReader((out_dir / "controlled_experiments.csv").open()))
    assert any(row["expected_outcome"].startswith("positive") for row in rows)


def test_checker_rejects_fabricated_restoration(tmp_path):
    out_dir = tmp_path / "functional_results"
    bench_dir = tmp_path / "functional_bench"
    env = {**os.environ, "AIG_ABC": str(tmp_path / "missing_abc")}
    subprocess.run(
        [
            sys.executable,
            "scripts/run_semantic_functional_refactoring.py",
            "--mode",
            "controlled",
            "--output-dir",
            str(out_dir),
            "--bench-dir",
            str(bench_dir),
        ],
        cwd=ROOT,
        check=True,
        env=env,
    )
    subprocess.run(
        [sys.executable, "scripts/check_semantic_functional_refactoring_results.py", "--output-dir", str(out_dir), "--allow-no-abc"],
        cwd=ROOT,
        check=True,
        env=env,
    )
    cec_path = out_dir / "global_abc_cec.csv"
    rows = list(csv.DictReader(cec_path.open()))
    for row in rows:
        row["global_cec_status"] = "not_run"
        row["abc_available"] = "false"
        break
    with cec_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=rows[0].keys(), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    controlled_path = out_dir / "controlled_experiments.csv"
    controlled = list(csv.DictReader(controlled_path.open()))
    controlled_fields = list(controlled[0].keys())
    controlled[0]["final_status"] = "accepted"
    controlled[0]["global_cec_status"] = "equivalent"
    controlled[0]["graph_active"] = "true"
    controlled[0]["restored_boundary"] = "true"
    with controlled_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=controlled_fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(controlled)
    boundary_path = out_dir / "boundary_restoration.csv"
    boundaries = list(csv.DictReader(boundary_path.open()))
    boundary_fields = list(boundaries[0].keys())
    boundaries[0]["restored_boundary"] = "true"
    boundaries[0]["global_cec_status"] = "equivalent"
    with boundary_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=boundary_fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(boundaries)
    result = subprocess.run(
        [sys.executable, "scripts/check_semantic_functional_refactoring_results.py", "--output-dir", str(out_dir), "--allow-no-abc"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
    )
    assert result.returncode != 0
    assert "ABC global CEC" in result.stderr or "ABC unavailable" in result.stderr
