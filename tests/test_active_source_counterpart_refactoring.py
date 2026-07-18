from __future__ import annotations

import csv
import os
import subprocess
import sys
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
ABC = ROOT / ".abc_build" / "abc_repo" / "abc"


def _abc_available() -> bool:
    override = os.environ.get("AIG_ABC")
    return Path(override).exists() if override else ABC.exists()


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
        [sys.executable, str(ROOT / "scripts" / "run_active_source_counterpart_refactoring.py"), "--mode", "controlled", "--output-dir", str(out), "--bench-dir", str(bench)],
        cwd=ROOT,
        check=True,
    )
    checker = [sys.executable, str(ROOT / "scripts" / "check_active_source_counterpart_results.py"), "--output-dir", str(out)]
    if not _abc_available():
        checker.append("--allow-no-abc")
    subprocess.run(checker, cwd=ROOT, check=True)
    controlled = list(csv.DictReader((out / "controlled_results.csv").open()))
    accepted = [row for row in controlled if row["final_status"] == "accepted"]
    if _abc_available():
        assert len(accepted) >= 8
        assert any(row["family"] == "bilinear" and row["final_status"] == "accepted" for row in controlled)
        assert any(row["family"] == "mac" and row["final_status"] == "accepted" for row in controlled)
    else:
        assert not accepted
        assert all(row["new_recovered_boundary"] == "false" for row in controlled)
        assert all(row["source_cec_status"] != "equivalent" for row in controlled)


def test_checker_rejects_boundary_without_global_cec(tmp_path: Path) -> None:
    out = tmp_path / "out"
    bench = tmp_path / "bench"
    env = {**os.environ, "AIG_ABC": str(tmp_path / "missing_abc")}
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "run_active_source_counterpart_refactoring.py"), "--mode", "controlled", "--output-dir", str(out), "--bench-dir", str(bench)],
        cwd=ROOT,
        check=True,
        env=env,
    )
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "check_active_source_counterpart_results.py"), "--output-dir", str(out), "--allow-no-abc"],
        cwd=ROOT,
        check=True,
        env=env,
    )
    controlled_path = out / "controlled_results.csv"
    controlled = list(csv.DictReader(controlled_path.open()))
    controlled_fields = list(controlled[0].keys())
    for row in controlled:
        if row["expected_outcome"].startswith("positive"):
            row["final_status"] = "accepted"
            row["usable_anchor"] = "true"
            row["new_recovered_boundary"] = "true"
            break
    with controlled_path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=controlled_fields)
        writer.writeheader()
        writer.writerows(controlled)
    boundary_path = out / "boundary_recovery.csv"
    boundaries = list(csv.DictReader(boundary_path.open()))
    boundary_fields = list(boundaries[0].keys())
    boundaries[0]["usable_frontier_anchor"] = "true"
    boundaries[0]["selected_anchor"] = "true"
    boundaries[0]["new_recovered_boundary"] = "true"
    with boundary_path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=boundary_fields)
        writer.writeheader()
        writer.writerows(boundaries)
    path = out / "global_cec.csv"
    rows = list(csv.DictReader(path.open()))
    fields = list(rows[0].keys())
    for row in rows:
        if row["cec_scope"] == "S_vs_Sprime":
            row["cec_status"] = "not_run"
            row["abc_available"] = "false"
            break
    with path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "check_active_source_counterpart_results.py"), "--output-dir", str(out), "--allow-no-abc"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
    )
    assert proc.returncode != 0
    assert "ABC unavailable" in proc.stderr or "lacks S-vs-S' ABC CEC" in proc.stderr
