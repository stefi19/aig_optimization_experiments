from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


def _rows(rel_path: str) -> list[dict[str, str]]:
    with (ROOT / rel_path).open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _write_rows(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


@pytest.fixture(scope="module", autouse=True)
def _built_evidence() -> None:
    subprocess.run([sys.executable, str(ROOT / "scripts" / "build_evidence_advancement.py")], cwd=ROOT, check=True)


def test_evidence_advancement_builds_and_checks() -> None:
    subprocess.run([sys.executable, str(ROOT / "scripts" / "build_evidence_advancement.py")], cwd=ROOT, check=True)
    subprocess.run([sys.executable, str(ROOT / "scripts" / "check_evidence_advancement.py")], cwd=ROOT, check=True)


def test_evidence_advancement_keeps_evidence_levels_separate() -> None:
    placement = _rows("results/evidence_advancement/source_blind_counterpart_placement.csv")
    window_expression = _rows("results/evidence_advancement/source_blind_window_expression_placement.csv")
    source_blind = _rows("results/evidence_advancement/source_blind_counterpart_inference.csv")
    rewrite_attempts = _rows("results/evidence_advancement/compact_interface_rewrite_attempts.csv")
    frontier = _rows("results/necessity_first_target_discovery/rewrite_frontier_expansion.csv")
    odc = _rows("results/evidence_advancement/odc_placement_accounting.csv")

    semantic_only = sum(r["promoted_evidence_level"] == "semantic_counterpart_only" for r in source_blind)
    graph_active_source_blind = sum(r["graph_active_recovery"] == "true" for r in source_blind)
    assert semantic_only + graph_active_source_blind == 20
    assert sum(r["semantic_counterpart_status"].startswith("proved_") for r in placement) == 20
    assert sum(r["promotion"] == "graph_active_recovery" for r in placement) == 0
    assert sum(r["semantic_counterpart_status"].startswith("proved_") for r in window_expression) == 20
    assert sum(r["graph_active_recovery"] == "true" for r in source_blind) == sum(r["promotion"] == "graph_active_recovery" for r in window_expression)
    for row in window_expression:
        if row["promotion"] == "graph_active_recovery":
            assert row["rewrite_emitted"] == "true"
            assert row["graph_active"] == "true"
            assert row["global_cec_status"] == "equivalent"
            assert row["source_vs_rewrite_cec"] == "equivalent"
            assert row["rewrite_vs_optimized_cec"] == "equivalent"
            assert row["expression"]
    assert sum(r["compact_interface"] == "true" for r in rewrite_attempts) == 31
    assert sum(r["rewrite_emitted"] == "true" for r in rewrite_attempts) == 31
    assert sum(r["graph_active"] == "true" for r in rewrite_attempts) == 22
    assert sum(r["new_boundary"] == "true" for r in rewrite_attempts) == 22
    assert sum(r["promotion"] == "graph_active_cec_recovery" for r in frontier) == 4
    assert sum(r["proof_status"] == "proven_odc_valid" for r in odc) == 10
    assert sum(r["graph_active"] == "true" for r in odc) == 0


def test_locality_proof_objects_mirror_exact_certificates() -> None:
    proof_rows = _rows("results/evidence_advancement/locality_proof_objects.csv")
    assert len(proof_rows) == 57
    for row in proof_rows[:5]:
        proof = json.loads((ROOT / row["proof_object_path"]).read_text(encoding="utf-8"))
        assert proof["solver_status"] == "unsat"
        assert proof["exact_minimum_status"] == "exact_minimum"
        assert len(proof["tested_interface"]) == int(row["tested_interface_width"])
        assert int(row["proved_lower_bound"]) == int(row["best_upper_bound"])


def test_checker_rejects_source_blind_placement_leakage(tmp_path: Path) -> None:
    path = ROOT / "results/evidence_advancement/source_blind_window_expression_placement.csv"
    rows = list(csv.DictReader(path.open()))
    original = [dict(row) for row in rows]
    rows[0]["source_blind"] = "false"
    try:
        _write_rows(path, rows)
        result = subprocess.run([sys.executable, str(ROOT / "scripts" / "check_evidence_advancement.py")], cwd=ROOT)
        assert result.returncode != 0
    finally:
        _write_rows(path, original)


def test_checker_rejects_source_blind_promotion_without_artifact() -> None:
    path = ROOT / "results/evidence_advancement/source_blind_window_expression_placement.csv"
    rows = list(csv.DictReader(path.open()))
    original = [dict(row) for row in rows]
    row = next(r for r in rows if r["semantic_counterpart_status"].startswith("proved_"))
    row["promotion"] = "graph_active_recovery"
    row["rewrite_emitted"] = "true"
    row["graph_active"] = "true"
    row["global_cec_status"] = "equivalent"
    row["source_vs_rewrite_cec"] = "equivalent"
    row["rewrite_vs_optimized_cec"] = "equivalent"
    row["rewrite_artifact"] = ""
    try:
        _write_rows(path, rows)
        result = subprocess.run([sys.executable, str(ROOT / "scripts" / "check_evidence_advancement.py")], cwd=ROOT)
        assert result.returncode != 0
    finally:
        _write_rows(path, original)


def test_checker_rejects_source_blind_graph_active_without_cec() -> None:
    path = ROOT / "results/evidence_advancement/source_blind_window_expression_placement.csv"
    rows = list(csv.DictReader(path.open()))
    original = [dict(row) for row in rows]
    row = next(r for r in rows if r["semantic_counterpart_status"].startswith("proved_"))
    row["graph_active"] = "true"
    row["global_cec_status"] = "not_claimed"
    try:
        _write_rows(path, rows)
        result = subprocess.run([sys.executable, str(ROOT / "scripts" / "check_evidence_advancement.py")], cwd=ROOT)
        assert result.returncode != 0
    finally:
        _write_rows(path, original)


def test_checker_rejects_source_blind_promotion_without_both_cec_scopes() -> None:
    path = ROOT / "results/evidence_advancement/source_blind_window_expression_placement.csv"
    rows = list(csv.DictReader(path.open()))
    original = [dict(row) for row in rows]
    row = next(r for r in rows if r["semantic_counterpart_status"].startswith("proved_"))
    artifact = ROOT / "results/evidence_advancement/source_blind_counterpart_placement_fake.blif"
    artifact.write_text(".model fake\n.inputs a\n.outputs y\n.names a y\n1 1\n.end\n", encoding="utf-8")
    row["promotion"] = "graph_active_recovery"
    row["rewrite_emitted"] = "true"
    row["graph_active"] = "true"
    row["global_cec_status"] = "equivalent"
    row["source_vs_rewrite_cec"] = "equivalent"
    row["rewrite_vs_optimized_cec"] = "not_run"
    row["rewrite_artifact"] = str(artifact.relative_to(ROOT))
    try:
        _write_rows(path, rows)
        result = subprocess.run([sys.executable, str(ROOT / "scripts" / "check_evidence_advancement.py")], cwd=ROOT)
        assert result.returncode != 0
    finally:
        artifact.unlink(missing_ok=True)
        _write_rows(path, original)
