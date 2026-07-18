from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path

from analyze_blif_matches import parse_blif
from analyze_blif_matches import BlifNode
from formal_locality_barriers import (
    CandidateSignalUniverse,
    all_assignments,
    build_source_universes,
    difference_set,
    exact_minimum_hitting_set,
    output_interface_sufficiency,
    prove_interface_sufficiency,
    scalar_eval_exact,
    solve_minimum_interface,
)
from semantic_region import file_hash


ROOT = Path(__file__).resolve().parents[1]


def _write_truth(path: Path, inputs: tuple[str, ...], outputs: tuple[str, ...], fn) -> None:
    lines = [".model t", ".inputs " + " ".join(inputs), ".outputs " + " ".join(outputs)]
    for idx, output in enumerate(outputs):
        lines.append(".names " + " ".join([*inputs, output]))
        for assignment in all_assignments(inputs):
            if fn(assignment)[idx]:
                lines.append("".join(str(assignment[name]) for name in inputs) + " 1")
    lines.append(".end")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def test_interface_sufficiency_sat_unsat_and_difference_set(tmp_path: Path) -> None:
    src = tmp_path / "s.blif"
    opt = tmp_path / "o.blif"
    _write_truth(src, ("a", "b"), ("s",), lambda x: (x["a"] ^ x["b"],))
    _write_truth(opt, ("a", "b"), ("t",), lambda x: (x["a"] ^ x["b"],))
    bad = prove_interface_sufficiency(source_path=src, optimized_path=opt, interface=("a",), target_vector=("t",))
    assert bad.status == "sat"
    assert bad.counterexample is not None
    assert bad.counterexample_reproduced
    diff = difference_set(src, ("a", "b", "s"), *bad.counterexample)
    assert "b" in diff
    good = prove_interface_sufficiency(source_path=src, optimized_path=opt, interface=("a", "b"), target_vector=("t",))
    assert good.status == "unsat"


def test_blif_off_set_cover_rows_are_evaluated_exactly(tmp_path: Path) -> None:
    path = tmp_path / "not_and.blif"
    path.write_text(
        "\n".join(
            [
                ".model not_and",
                ".inputs a b",
                ".outputs y",
                ".names a b y",
                "11 0",
                ".end",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    values = {
        tuple(sorted(assignment.items())): scalar_eval_exact(parse_blif(path), assignment)["y"]
        for assignment in all_assignments(("a", "b"))
    }
    assert values[(("a", 1), ("b", 1))] == 0
    assert values[(("a", 0), ("b", 0))] == 1
    assert values[(("a", 1), ("b", 0))] == 1


def test_hitting_set_exact_minimum_widths(tmp_path: Path) -> None:
    src = tmp_path / "s.blif"
    opt = tmp_path / "o.blif"
    _write_truth(src, ("a", "b", "c"), ("y",), lambda x: ((x["a"] & x["b"]) | (x["a"] & x["c"]) | (x["b"] & x["c"]),))
    _write_truth(opt, ("a", "b", "c"), ("t",), lambda x: ((x["a"] & x["b"]) | (x["a"] & x["c"]) | (x["b"] & x["c"]),))
    universe = CandidateSignalUniverse(
        "u",
        "target",
        "test",
        1,
        ("a", "b", "c"),
        str(src),
        file_hash(src),
        str(opt),
        file_hash(opt),
    )
    cert, cexs, iterations = solve_minimum_interface(
        target_id="target",
        benchmark="controlled",
        split="controlled",
        failure_group="controlled",
        source_path=src,
        optimized_path=opt,
        target_vector=("t",),
        universe=universe,
        max_width=3,
    )
    assert cert.exact_minimum_status == "exact_minimum"
    assert cert.best_upper_bound == 3
    assert cert.proved_lower_bound == 3
    assert all(c.counterexample_reproduced for c in cexs)
    assert iterations[-1]["termination"] == "sufficient"


def test_empty_difference_set_marks_universe_insufficient(tmp_path: Path) -> None:
    src = tmp_path / "s.blif"
    opt = tmp_path / "o.blif"
    _write_truth(src, ("a", "b"), ("y",), lambda x: (x["a"],))
    _write_truth(opt, ("a", "b"), ("t",), lambda x: (x["b"],))
    universe = CandidateSignalUniverse("u", "target", "test", 0, ("a",), str(src), file_hash(src), str(opt), file_hash(opt))
    cert, cexs, _ = solve_minimum_interface(
        target_id="target",
        benchmark="controlled",
        split="controlled",
        failure_group="controlled",
        source_path=src,
        optimized_path=opt,
        target_vector=("t",),
        universe=universe,
        max_width=1,
    )
    assert cert.classification == "local_input_universe_formally_insufficient"
    assert any(len(c.difference_set) == 0 for c in cexs)


def test_universe_construction_is_deterministic(tmp_path: Path) -> None:
    src = tmp_path / "s.blif"
    opt = tmp_path / "o.blif"
    _write_truth(src, ("a", "b"), ("n",), lambda x: (x["a"] & x["b"],))
    _write_truth(opt, ("a", "b"), ("t",), lambda x: (x["a"] & x["b"],))
    left = build_source_universes(target_id="t", source_path=src, optimized_path=opt, target_vector=("t",))
    right = build_source_universes(target_id="t", source_path=src, optimized_path=opt, target_vector=("t",))
    assert [u.universe_hash for u in left] == [u.universe_hash for u in right]
    assert left[-1].diagnostic_only


def test_output_interface_sufficiency_and_target_utility_shape(tmp_path: Path) -> None:
    src = tmp_path / "s.blif"
    opt = tmp_path / "o.blif"
    _write_truth(src, ("a", "z"), ("y",), lambda x: (x["a"] ^ x["z"],))
    _write_truth(opt, ("a", "z"), ("b0",), lambda x: (x["a"],))
    bad = output_interface_sufficiency(source_path=src, optimized_path=opt, optimized_interface=("b0",), residual_source=(), source_outputs=("y",))
    assert bad.status == "sat"
    assert bad.counterexample_reproduced
    good = output_interface_sufficiency(source_path=src, optimized_path=opt, optimized_interface=("b0",), residual_source=("z",), source_outputs=("y",))
    assert good.status == "unsat"


def test_hitting_set_constraints() -> None:
    selected, lower, exact = exact_minimum_hitting_set([("a", "b"), ("b", "c"), ("c",)], ("a", "b", "c"), max_width=3)
    assert selected is not None
    assert len(selected) == 2
    assert all(set(selected) & set(constraint) for constraint in [("a", "b"), ("b", "c"), ("c",)])
    assert lower == 2
    assert exact


def test_runner_and_checker_controlled(tmp_path: Path) -> None:
    out = tmp_path / "out"
    subprocess.run([sys.executable, str(ROOT / "scripts" / "run_formal_locality_barriers.py"), "--mode", "controlled", "--output-dir", str(out)], cwd=ROOT, check=True)
    subprocess.run([sys.executable, str(ROOT / "scripts" / "check_formal_locality_barrier_results.py"), "--output-dir", str(out)], cwd=ROOT, check=True)
    rows = list(csv.DictReader((out / "controlled_results.csv").open()))
    assert {row["case_id"] for row in rows} >= {"min1", "min2_xor", "min3_maj", "nonlinear_and"}
    assert all(row["expected_minimum"] == row["exhaustive_minimum"] for row in rows)


def test_checker_rejects_exact_without_unsat(tmp_path: Path) -> None:
    out = tmp_path / "out"
    subprocess.run([sys.executable, str(ROOT / "scripts" / "run_formal_locality_barriers.py"), "--mode", "controlled", "--output-dir", str(out)], cwd=ROOT, check=True)
    path = out / "input_exact_minimum_certificates.csv"
    rows = list(csv.DictReader(path.open()))
    fields = list(rows[0].keys())
    rows[0]["solver_status"] = "sat"
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    result = subprocess.run([sys.executable, str(ROOT / "scripts" / "check_formal_locality_barrier_results.py"), "--output-dir", str(out)], cwd=ROOT)
    assert result.returncode != 0
