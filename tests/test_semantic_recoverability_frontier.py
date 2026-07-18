from __future__ import annotations

import csv
import subprocess
import sys
from pathlib import Path

from semantic_ast import SemanticExpr, input_expr
from semantic_functional_refactoring import SemanticDivisor, make_bus
from semantic_recoverability_frontier import (
    BoundaryRecord,
    Checkpoint,
    TrajectorySpec,
    blind_prediction_rows,
    leakage_audit,
    recoverability_transitions,
    residual_frontier,
    stable_hash,
    structural_metrics,
    write_truth_blif,
)
from semantic_types import unsigned_bitvector


ROOT = Path(__file__).resolve().parents[1]


def _xor_boundary(tmp_path: Path) -> tuple[Path, BoundaryRecord, Checkpoint]:
    blif = tmp_path / "xor_factor.blif"
    write_truth_blif(
        blif,
        "xor_factor",
        ("x0", "x1", "r0"),
        ("y0",),
        lambda a: ((a["x0"] ^ a["x1"]) ^ a["r0"],),
        internal_nodes={"m0": lambda a: a["x0"] ^ a["x1"]},
    )
    expr = SemanticExpr("xor", (input_expr("x0", 1), input_expr("x1", 1)), output_type=unsigned_bitvector(1))
    divisor = SemanticDivisor("b__div", "xor_factor", "test", (make_bus("x0", ("x0",), "data"), make_bus("x1", ("x1",), "data")), (make_bus("m", ("m0",), "semantic_divisor"),), (expr,), "xor", 2)
    boundary = BoundaryRecord("xor_factor__b0", "xor_factor", "controlled", "controlled", "xor_factor", "xor", str(blif), (1, 1), (1,), "unsigned", ("x0", "x1"), ("m0",), 1, ("y0",), False, True, True, divisor)
    cp = Checkpoint("traj", "traj__cp000_source", "xor_factor", "controlled", 0, "source", 0, tuple(), blif, "equivalent", "test", 0.0)
    return blif, boundary, cp


def test_stable_boundary_hash_and_metrics(tmp_path: Path) -> None:
    blif, boundary, _cp = _xor_boundary(tmp_path)
    assert boundary.fingerprint == boundary.fingerprint
    assert stable_hash({"b": 2, "a": 1}) == stable_hash({"a": 1, "b": 2})
    metrics = structural_metrics(blif)
    assert metrics["input_count"] == "3"
    assert int(metrics["node_count"]) >= 2


def test_blind_prediction_leakage_guard(tmp_path: Path) -> None:
    _blif, _boundary, cp = _xor_boundary(tmp_path)
    rows = blind_prediction_rows(cp)
    assert rows
    audit = leakage_audit(rows)
    assert {row["leakage_status"] for row in audit} == {"pass"}


def test_residual_exact_minimum_and_counterexample(tmp_path: Path) -> None:
    _blif, boundary, cp = _xor_boundary(tmp_path)
    rows, cex = residual_frontier(checkpoint=cp, boundary=boundary, candidate_residuals=("r0",), output_nodes=("y0",), max_width=1)
    exact = [row for row in rows if row["minimum_status"] == "exact_minimum"]
    assert exact
    assert exact[0]["residual_width"] == "1"
    assert cex
    assert all(row["counterexample_reproduced"] == "True" or row["counterexample_reproduced"] == "true" for row in cex)


def test_recoverability_transitions_non_monotonic() -> None:
    rows = [
        {"boundary_id": "b", "trajectory_id": "t", "method": "m", "checkpoint_index": "0", "checkpoint_id": "c0", "recovered": "true", "recovery_level": "R0_structural_survival"},
        {"boundary_id": "b", "trajectory_id": "t", "method": "m", "checkpoint_index": "1", "checkpoint_id": "c1", "recovered": "false", "recovery_level": "R9_unresolved"},
        {"boundary_id": "b", "trajectory_id": "t", "method": "m", "checkpoint_index": "2", "checkpoint_id": "c2", "recovered": "true", "recovery_level": "R1_functional_internal_survival"},
    ]
    transitions = recoverability_transitions(rows)
    assert any(row["transition"] == "success_to_failure" for row in transitions)
    assert any(row["transition"] == "failure_to_success" for row in transitions)


def test_trajectory_spec_records_split(tmp_path: Path) -> None:
    blif, _boundary, _cp = _xor_boundary(tmp_path)
    spec = TrajectorySpec("controlled__xor__flow", "xor", "controlled", blif, ("strash",), "test")
    assert spec.trajectory_id.startswith("controlled__")
    assert spec.pass_sequence == ("strash",)


def test_runner_and_checker_temp_dir(tmp_path: Path) -> None:
    out = tmp_path / "out"
    bench = tmp_path / "bench"
    subprocess.run([sys.executable, "scripts/run_semantic_recoverability_frontier.py", "--mode", "controlled", "--output-dir", str(out), "--bench-dir", str(bench)], cwd=ROOT, check=True)
    subprocess.run([sys.executable, "scripts/check_semantic_recoverability_results.py", "--output-dir", str(out), "--allow-no-abc"], cwd=ROOT, check=True)
    with (out / "final_supported_claims_summary.md").open(encoding="utf-8") as fh:
        assert "ground-truth boundaries" in fh.read()
    checkpoints = list(csv.DictReader((out / "checkpoint_hashes.csv").open()))
    unrealized = [row for row in checkpoints if row["artifact_status"] != "materialized"]
    if unrealized:
        assert all(row["artifact_exists"] == "false" for row in unrealized)
        assert all(row["sha256"] == "" for row in unrealized)
        recovered = list(csv.DictReader((out / "blind_recovery_results.csv").open()))
        assert not ({row["checkpoint_id"] for row in unrealized} & {row["checkpoint_id"] for row in recovered})


def test_checker_rejects_blind_oracle_level_corruption(tmp_path: Path) -> None:
    out = tmp_path / "out"
    bench = tmp_path / "bench"
    subprocess.run([sys.executable, "scripts/run_semantic_recoverability_frontier.py", "--mode", "controlled", "--output-dir", str(out), "--bench-dir", str(bench)], cwd=ROOT, check=True)
    blind = out / "blind_recovery_results.csv"
    rows = list(csv.DictReader(blind.open(newline="", encoding="utf-8")))
    if not rows:
        fields = blind.read_text(encoding="utf-8").splitlines()[0].split(",")
        checkpoint = next(csv.DictReader((out / "checkpoint_hashes.csv").open(newline="", encoding="utf-8")))
        rows.append({field: "" for field in fields})
        rows[0].update(
            {
                "result_id": "corrupted_blind_oracle_level",
                "boundary_id": "corrupted_boundary",
                "checkpoint_id": checkpoint["checkpoint_id"],
                "method": "blind",
                "oracle_mode": "blind",
                "recovered": "false",
                "timeout": "false",
                "schema_version": "semantic_recoverability_frontier_v1",
            }
        )
    rows[0]["recovery_level"] = "R5_oracle_divisor_compact_decomposition"
    with blind.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    proc = subprocess.run([sys.executable, "scripts/check_semantic_recoverability_results.py", "--output-dir", str(out), "--allow-no-abc"], cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    assert proc.returncode != 0
    assert "oracle recovery level appears in blind row" in proc.stderr


def test_checker_rejects_missing_checkpoint_artifact_claim(tmp_path: Path) -> None:
    out = tmp_path / "out"
    bench = tmp_path / "bench"
    subprocess.run([sys.executable, "scripts/run_semantic_recoverability_frontier.py", "--mode", "controlled", "--output-dir", str(out), "--bench-dir", str(bench)], cwd=ROOT, check=True)
    subprocess.run([sys.executable, "scripts/check_semantic_recoverability_results.py", "--output-dir", str(out), "--allow-no-abc"], cwd=ROOT, check=True)
    hashes = out / "checkpoint_hashes.csv"
    rows = list(csv.DictReader(hashes.open(newline="", encoding="utf-8")))
    fields = list(rows[0].keys())
    target = next(row for row in rows if row["artifact_status"] == "materialized")
    artifact = Path(target["blif_path"])
    if not artifact.is_absolute():
        artifact = ROOT / artifact
    artifact.unlink()
    with hashes.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    proc = subprocess.run([sys.executable, "scripts/check_semantic_recoverability_results.py", "--output-dir", str(out), "--allow-no-abc"], cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    assert proc.returncode != 0
    assert "file is missing" in proc.stderr
