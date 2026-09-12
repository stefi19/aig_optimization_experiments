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
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _sha256(path: Path) -> str:
    import hashlib

    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


@pytest.fixture(scope="module", autouse=True)
def _built_evidence() -> None:
    subprocess.run([sys.executable, str(ROOT / "scripts" / "build_evidence_advancement.py")], cwd=ROOT, check=True)


def test_evidence_advancement_builds_and_checks() -> None:
    subprocess.run([sys.executable, str(ROOT / "scripts" / "check_evidence_advancement.py")], cwd=ROOT, check=True)


def test_evidence_advancement_keeps_evidence_levels_separate() -> None:
    placement = _rows("results/evidence_advancement/source_blind_counterpart_placement.csv")
    window_expression = _rows("results/evidence_advancement/source_blind_window_expression_placement.csv")
    source_blind = _rows("results/evidence_advancement/source_blind_counterpart_inference.csv")
    decompositions = _rows("results/evidence_advancement/optimized_target_decompositions.csv")
    virtual_anchors = _rows("results/evidence_advancement/virtual_anchor_certificates.csv")
    constructive = _rows("results/evidence_advancement/constructive_rewrite_selection.csv")
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
    assert sum(r["decomposition_status"] == "unsupported_no_replay_artifacts" for r in decompositions) == 36
    assert sum(r["proof_status"] == "proven_virtual_anchor" for r in virtual_anchors) == 20
    assert sum(r["objective_status"] == "graph_active_cec_recovery" for r in constructive) == 20
    assert sum(r["rewrite_support_status"] == "constructive_expanded_support" for r in constructive) == 6
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


def test_virtual_anchor_proof_objects_discharge_constructive_rewrites() -> None:
    proof_rows = _rows("results/evidence_advancement/virtual_anchor_certificates.csv")
    proven = [row for row in proof_rows if row["proof_status"] == "proven_virtual_anchor"]
    assert len(proven) == 20
    for row in proven[:5]:
        proof = json.loads((ROOT / row["proof_object_path"]).read_text(encoding="utf-8"))
        assert proof["proof_style"] == "proof_carrying_virtual_anchor_synthesis"
        assert proof["proof_status"] == "proven_virtual_anchor"
        assert proof["obligations"]["source_graph_or_pi_only"] is True
        assert proof["obligations"]["target_vector_replayed"] is True
        assert proof["obligations"]["graph_active"] is True
        assert proof["obligations"]["global_cec_equivalent"] is True


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


def test_checker_rejects_tampered_source_blind_expression_witness() -> None:
    path = ROOT / "results/evidence_advancement/source_blind_window_expression_placement.csv"
    rows = list(csv.DictReader(path.open()))
    original = [dict(row) for row in rows]
    row = next(r for r in rows if r["promotion"] == "graph_active_recovery" and r["expression_language"] != "not")
    window = json.loads(row["candidate_source_window"])
    row["expression_language"] = "not"
    row["expression"] = f"not({window[0]})"
    row["candidate_source_window"] = json.dumps([window[0]])
    features = json.loads(row["selection_features"])
    features["selected_window_width"] = 1
    row["selection_features"] = json.dumps(features, sort_keys=True)
    try:
        _write_rows(path, rows)
        result = subprocess.run([sys.executable, str(ROOT / "scripts" / "check_evidence_advancement.py")], cwd=ROOT)
        assert result.returncode != 0
    finally:
        _write_rows(path, original)


def test_checker_rejects_tampered_source_blind_selected_support() -> None:
    path = ROOT / "results/evidence_advancement/source_blind_window_expression_placement.csv"
    rows = list(csv.DictReader(path.open()))
    original = [dict(row) for row in rows]
    row = next(r for r in rows if r["promotion"] == "graph_active_recovery")
    features = json.loads(row["selection_features"])
    features["selected_support"] = []
    row["selection_features"] = json.dumps(features, sort_keys=True)
    try:
        _write_rows(path, rows)
        result = subprocess.run([sys.executable, str(ROOT / "scripts" / "check_evidence_advancement.py")], cwd=ROOT)
        assert result.returncode != 0
    finally:
        _write_rows(path, original)


def test_checker_rejects_tampered_virtual_anchor_proof_object() -> None:
    path = ROOT / "results/evidence_advancement/virtual_anchor_certificates.csv"
    rows = list(csv.DictReader(path.open()))
    row = next(r for r in rows if r["proof_status"] == "proven_virtual_anchor")
    proof_path = ROOT / row["proof_object_path"]
    original = proof_path.read_text(encoding="utf-8")
    proof = json.loads(original)
    proof["obligations"]["global_cec_equivalent"] = False
    try:
        proof_path.write_text(json.dumps(proof, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        result = subprocess.run([sys.executable, str(ROOT / "scripts" / "check_evidence_advancement.py")], cwd=ROOT)
        assert result.returncode != 0
    finally:
        proof_path.write_text(original, encoding="utf-8")


def test_checker_rejects_compact_rewrite_artifact_drift() -> None:
    path = ROOT / "results/evidence_advancement/compact_interface_rewrite_attempts.csv"
    rows = list(csv.DictReader(path.open()))
    original = [dict(row) for row in rows]
    emitted = [r for r in rows if r["rewrite_emitted"] == "true"]
    emitted[0]["rewrite_artifact"] = emitted[1]["rewrite_artifact"]
    try:
        _write_rows(path, rows)
        result = subprocess.run([sys.executable, str(ROOT / "scripts" / "check_evidence_advancement.py")], cwd=ROOT)
        assert result.returncode != 0
    finally:
        _write_rows(path, original)


def test_checker_rejects_compact_rewrite_cec_scope_drift() -> None:
    path = ROOT / "results/evidence_advancement/compact_interface_rewrite_attempts.csv"
    rows = list(csv.DictReader(path.open()))
    original = [dict(row) for row in rows]
    row = next(r for r in rows if r["rewrite_emitted"] == "true" and r["new_boundary"] == "false")
    row["source_vs_rewrite_cec"] = "not_run"
    try:
        _write_rows(path, rows)
        result = subprocess.run([sys.executable, str(ROOT / "scripts" / "check_evidence_advancement.py")], cwd=ROOT)
        assert result.returncode != 0
    finally:
        _write_rows(path, original)


def test_checker_rejects_grammar_proof_hash_drift() -> None:
    path = ROOT / "results/evidence_advancement/grammar_completeness_certificates.csv"
    rows = list(csv.DictReader(path.open()))
    original = [dict(row) for row in rows]
    row = next(r for r in rows if r["bounded_grammar_complete_for_attempted_rows"] == "true")
    row["proof_hash"] = "0" * 64
    try:
        _write_rows(path, rows)
        result = subprocess.run([sys.executable, str(ROOT / "scripts" / "check_evidence_advancement.py")], cwd=ROOT)
        assert result.returncode != 0
    finally:
        _write_rows(path, original)


def test_checker_rejects_grammar_grouped_count_drift() -> None:
    path = ROOT / "results/evidence_advancement/grammar_completeness_certificates.csv"
    rows = list(csv.DictReader(path.open()))
    original = [dict(row) for row in rows]
    row = next(r for r in rows if r["mode"] == "blind" and r["operator"] == "sign_extend")
    row["regions_recovered"] = str(int(row["regions_recovered"]) - 1)
    try:
        _write_rows(path, rows)
        result = subprocess.run([sys.executable, str(ROOT / "scripts" / "check_evidence_advancement.py")], cwd=ROOT)
        assert result.returncode != 0
    finally:
        _write_rows(path, original)


def test_checker_rejects_odc_boundary_success_drift() -> None:
    path = ROOT / "results/evidence_advancement/odc_placement_accounting.csv"
    rows = list(csv.DictReader(path.open()))
    original = [dict(row) for row in rows]
    row = next(r for r in rows if r["boundary_success"] == "true")
    row["boundary_success"] = "false"
    row["promotion"] = "contextual_anchor_only"
    try:
        _write_rows(path, rows)
        result = subprocess.run([sys.executable, str(ROOT / "scripts" / "check_evidence_advancement.py")], cwd=ROOT)
        assert result.returncode != 0
    finally:
        _write_rows(path, original)


def test_checker_rejects_odc_contextual_anchor_as_graph_active() -> None:
    path = ROOT / "results/evidence_advancement/odc_placement_accounting.csv"
    rows = list(csv.DictReader(path.open()))
    original = [dict(row) for row in rows]
    row = rows[0]
    row["graph_active"] = "true"
    row["global_cec_status"] = "equivalent"
    try:
        _write_rows(path, rows)
        result = subprocess.run([sys.executable, str(ROOT / "scripts" / "check_evidence_advancement.py")], cwd=ROOT)
        assert result.returncode != 0
    finally:
        _write_rows(path, original)


def test_checker_rejects_missing_locality_proof_object_row() -> None:
    path = ROOT / "results/evidence_advancement/locality_proof_objects.csv"
    rows = list(csv.DictReader(path.open()))
    original = [dict(row) for row in rows]
    try:
        _write_rows(path, rows[1:])
        result = subprocess.run([sys.executable, str(ROOT / "scripts" / "check_evidence_advancement.py")], cwd=ROOT)
        assert result.returncode != 0
    finally:
        _write_rows(path, original)


def test_checker_rejects_locality_proof_object_predicate_drift() -> None:
    table_path = ROOT / "results/evidence_advancement/locality_proof_objects.csv"
    rows = list(csv.DictReader(table_path.open()))
    original_rows = [dict(row) for row in rows]
    row = rows[0]
    proof_path = ROOT / row["proof_object_path"]
    original_proof_text = proof_path.read_text(encoding="utf-8")
    proof = json.loads(original_proof_text)
    proof["predicate"] = "weaker_metadata_only_claim"
    proof_path.write_text(json.dumps(proof, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    row["proof_object_sha256"] = _sha256(proof_path)
    try:
        _write_rows(table_path, rows)
        result = subprocess.run([sys.executable, str(ROOT / "scripts" / "check_evidence_advancement.py")], cwd=ROOT)
        assert result.returncode != 0
    finally:
        proof_path.write_text(original_proof_text, encoding="utf-8")
        _write_rows(table_path, original_rows)


def test_checker_rejects_rtl_corpus_design_set_drift() -> None:
    path = ROOT / "results/evidence_advancement/rtl_corpus_manifest.csv"
    rows = list(csv.DictReader(path.open()))
    original = [dict(row) for row in rows]
    rows[0]["design_id"] = "rtl_untracked"
    try:
        _write_rows(path, rows)
        result = subprocess.run([sys.executable, str(ROOT / "scripts" / "check_evidence_advancement.py")], cwd=ROOT)
        assert result.returncode != 0
    finally:
        _write_rows(path, original)


def test_checker_rejects_rtl_source_license_drift() -> None:
    table_path = ROOT / "results/evidence_advancement/rtl_corpus_manifest.csv"
    rows = list(csv.DictReader(table_path.open()))
    original_rows = [dict(row) for row in rows]
    row = rows[0]
    rtl_path = ROOT / row["rtl_path"]
    original_text = rtl_path.read_text(encoding="utf-8")
    rtl_path.write_text(original_text.replace("// SPDX-License-Identifier: CC0-1.0\n", "", 1), encoding="utf-8")
    row["rtl_sha256"] = _sha256(rtl_path)
    try:
        _write_rows(table_path, rows)
        result = subprocess.run([sys.executable, str(ROOT / "scripts" / "check_evidence_advancement.py")], cwd=ROOT)
        assert result.returncode != 0
    finally:
        rtl_path.write_text(original_text, encoding="utf-8")
        _write_rows(table_path, original_rows)
