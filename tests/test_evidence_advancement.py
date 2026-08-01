from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _rows(rel_path: str) -> list[dict[str, str]]:
    with (ROOT / rel_path).open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def test_evidence_advancement_builds_and_checks() -> None:
    subprocess.run([sys.executable, str(ROOT / "scripts" / "build_evidence_advancement.py")], cwd=ROOT, check=True)
    subprocess.run([sys.executable, str(ROOT / "scripts" / "check_evidence_advancement.py")], cwd=ROOT, check=True)


def test_evidence_advancement_keeps_evidence_levels_separate() -> None:
    subprocess.run([sys.executable, str(ROOT / "scripts" / "build_evidence_advancement.py")], cwd=ROOT, check=True)
    source_blind = _rows("results/evidence_advancement/source_blind_counterpart_inference.csv")
    rewrite_attempts = _rows("results/evidence_advancement/compact_interface_rewrite_attempts.csv")
    odc = _rows("results/evidence_advancement/odc_placement_accounting.csv")

    assert sum(r["promoted_evidence_level"] == "semantic_counterpart_only" for r in source_blind) == 20
    assert sum(r["graph_active_recovery"] == "true" for r in source_blind) == 0
    assert sum(r["compact_interface"] == "true" for r in rewrite_attempts) == 31
    assert sum(r["rewrite_emitted"] == "true" for r in rewrite_attempts) == 0
    assert sum(r["proof_status"] == "proven_odc_valid" for r in odc) == 10
    assert sum(r["graph_active"] == "true" for r in odc) == 0


def test_locality_proof_objects_mirror_exact_certificates() -> None:
    subprocess.run([sys.executable, str(ROOT / "scripts" / "build_evidence_advancement.py")], cwd=ROOT, check=True)
    proof_rows = _rows("results/evidence_advancement/locality_proof_objects.csv")
    assert len(proof_rows) == 57
    for row in proof_rows[:5]:
        proof = json.loads((ROOT / row["proof_object_path"]).read_text(encoding="utf-8"))
        assert proof["solver_status"] == "unsat"
        assert proof["exact_minimum_status"] == "exact_minimum"
        assert len(proof["tested_interface"]) == int(row["tested_interface_width"])
        assert int(row["proved_lower_bound"]) == int(row["best_upper_bound"])
