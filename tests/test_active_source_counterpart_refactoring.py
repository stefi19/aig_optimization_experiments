from __future__ import annotations

import csv
import subprocess
from pathlib import Path

from active_source_counterpart_refactoring import (
    ActiveSourceCounterpartCandidate,
    gf2_affine_model,
    prove_cross_node_equivalence,
    validate_active_rewrite,
)
from scripts.run_semantic_functional_refactoring import _controlled_cases
import scripts.run_semantic_functional_refactoring as sfr_runner


ROOT = Path(__file__).resolve().parents[1]


def test_candidate_fingerprint_is_deterministic() -> None:
    candidate = ActiveSourceCounterpartCandidate(
        candidate_id="c0",
        benchmark="bench",
        optimization_flow="flow",
        split="dev",
        optimized_target_nodes=("t",),
        target_selection_reason="utility",
        optimized_cut_id="cut",
        implementation_cut_leaves=("a",),
        mapped_source_cut_leaves=("a",),
        leaf_polarities=("same",),
        target_function_id="f",
        generated_source_counterpart_nodes=("w",),
        counterpart_backend="truth_table_lut",
        selected_source_window="win",
        source_window_inputs=("a", "z"),
        source_window_outputs=("y",),
        residual_interface=("z",),
        quotient_id="q",
        search_provenance="deterministic",
    )
    assert candidate.fingerprint == candidate.fingerprint
    assert candidate.source_blind is True


def test_cross_node_equivalence_and_counterexample(tmp_path: Path) -> None:
    left = tmp_path / "left.blif"
    right = tmp_path / "right.blif"
    left.write_text(".model l\n.inputs a\n.outputs y\n.names a w\n1 1\n.names w y\n1 1\n.end\n")
    right.write_text(".model r\n.inputs a\n.outputs y\n.names a t\n1 1\n.names t y\n1 1\n.end\n")
    proof = prove_cross_node_equivalence(source_blif=left, impl_blif=right, source_nodes=("w",), impl_nodes=("t",))
    assert proof["formal_status"] == "proven_counterpart_equivalent"
    right.write_text(".model r\n.inputs a\n.outputs y\n.names a t\n0 1\n.names t y\n1 1\n.end\n")
    proof = prove_cross_node_equivalence(source_blif=left, impl_blif=right, source_nodes=("w",), impl_nodes=("t",))
    assert proof["formal_status"] == "disproven"
    assert proof["counterexample_reproduced"] == "true"


def test_active_graph_validation_rejects_disconnected_and_cycles(tmp_path: Path) -> None:
    disconnected = tmp_path / "disconnected.blif"
    disconnected.write_text(".model d\n.inputs a\n.outputs y\n.names a w\n1 1\n.names a y\n1 1\n.end\n")
    row = validate_active_rewrite(refactored_blif=disconnected, counterpart_nodes=("w",), window_outputs=("y",))
    assert row["graph_rewrite_status"] == "valid"
    assert row["graph_active"] == "false"
    cyclic = tmp_path / "cyclic.blif"
    cyclic.write_text(".model c\n.inputs a\n.outputs y\n.names y w\n1 1\n.names w y\n1 1\n.end\n")
    row = validate_active_rewrite(refactored_blif=cyclic, counterpart_nodes=("w",), window_outputs=("y",))
    assert row["graph_rewrite_status"] == "invalid_cycle"


def test_gf2_baseline_accepts_affine_and_rejects_nonlinear(tmp_path: Path) -> None:
    affine = tmp_path / "affine.blif"
    affine.write_text(".model a\n.inputs x z\n.outputs y\n.names x z y\n01 1\n10 1\n.end\n")
    row = gf2_affine_model(blif_path=affine, output_node="y")
    assert row["status"] == "exact_affine_solution"
    nonlinear = tmp_path / "nonlinear.blif"
    nonlinear.write_text(".model n\n.inputs x z\n.outputs y\n.names x z y\n11 1\n.end\n")
    row = gf2_affine_model(blif_path=nonlinear, output_node="y")
    assert row["status"] == "rejected_nonlinear"


def test_controlled_runner_and_checker(tmp_path: Path) -> None:
    out = tmp_path / "out"
    bench = tmp_path / "bench"
    subprocess.run(
        [str(ROOT / ".venv-z3" / "bin" / "python"), str(ROOT / "scripts" / "run_active_source_counterpart_refactoring.py"), "--mode", "controlled", "--output-dir", str(out), "--bench-dir", str(bench)],
        cwd=ROOT,
        check=True,
    )
    subprocess.run(
        [str(ROOT / ".venv-z3" / "bin" / "python"), str(ROOT / "scripts" / "check_active_source_counterpart_results.py"), "--output-dir", str(out)],
        cwd=ROOT,
        check=True,
    )
    controlled = list(csv.DictReader((out / "controlled_results.csv").open()))
    assert sum(row["final_status"] == "accepted" for row in controlled) >= 8
    assert any(row["family"] == "bilinear" and row["final_status"] == "accepted" for row in controlled)
    assert any(row["family"] == "mac" and row["final_status"] == "accepted" for row in controlled)


def test_checker_rejects_boundary_without_global_cec(tmp_path: Path) -> None:
    out = tmp_path / "out"
    bench = tmp_path / "bench"
    subprocess.run(
        [str(ROOT / ".venv-z3" / "bin" / "python"), str(ROOT / "scripts" / "run_active_source_counterpart_refactoring.py"), "--mode", "controlled", "--output-dir", str(out), "--bench-dir", str(bench)],
        cwd=ROOT,
        check=True,
    )
    path = out / "global_cec.csv"
    rows = list(csv.DictReader(path.open()))
    fields = list(rows[0].keys())
    for row in rows:
        if row["cec_scope"] == "S_vs_Sprime" and row["cec_status"] == "equivalent":
            row["cec_status"] = "not_run"
            break
    with path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    proc = subprocess.run(
        [str(ROOT / ".venv-z3" / "bin" / "python"), str(ROOT / "scripts" / "check_active_source_counterpart_results.py"), "--output-dir", str(out)],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert proc.returncode != 0
    assert "lacks S-vs-S' ABC CEC" in proc.stderr
