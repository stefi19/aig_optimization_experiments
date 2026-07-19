from __future__ import annotations

import csv
import subprocess
import sys
from pathlib import Path

from analyze_blif_matches import parse_blif
from necessity_first_targets import (
    forced_observability_witness,
    functional_fingerprint,
    nonconstant_witness,
    reachable_necessity_witness,
    source_optimized_cec,
    stable_target_id,
    structural_path_to_output,
)
from semantic_region import file_hash


ROOT = Path(__file__).resolve().parents[1]


def _write_blif(path: Path, body: str) -> None:
    path.write_text(body.strip() + "\n", encoding="utf-8")


def test_target_observability_and_necessity(tmp_path: Path) -> None:
    blif = tmp_path / "obs.blif"
    _write_blif(
        blif,
        """
        .model obs
        .inputs a b
        .outputs y
        .names a t
        1 1
        .names t b y
        1- 1
        -1 1
        .end
        """,
    )
    net = parse_blif(blif)
    assert structural_path_to_output(net, "t")
    assert nonconstant_witness(net, "t")[0] == "nonconstant"
    assert forced_observability_witness(net, "t")[0] == "forced_observable"
    assert reachable_necessity_witness(net, "t")[0] == "reachable_necessary"


def test_constant_target_rejected(tmp_path: Path) -> None:
    blif = tmp_path / "const.blif"
    _write_blif(
        blif,
        """
        .model const
        .inputs a
        .outputs y
        .names t
        1
        .names t y
        1 1
        .end
        """,
    )
    net = parse_blif(blif)
    assert nonconstant_witness(net, "t")[0] == "constant"


def test_forced_observable_can_be_reachable_redundant(tmp_path: Path) -> None:
    blif = tmp_path / "forced_only.blif"
    _write_blif(
        blif,
        """
        .model forced_only
        .inputs a
        .outputs y
        .names a t
        1 1
        .names y
        1
        .end
        """,
    )
    net = parse_blif(blif)
    assert forced_observability_witness(net, "y")[0] == "forced_observable"
    assert reachable_necessity_witness(net, "t")[0] == "not_reachable_necessary"


def test_source_optimized_cec_and_stable_id(tmp_path: Path) -> None:
    source = tmp_path / "s.blif"
    optimized = tmp_path / "o.blif"
    body = """
    .model same
    .inputs a
    .outputs y
    .names a y
    1 1
    .end
    """
    _write_blif(source, body)
    _write_blif(optimized, body)
    assert source_optimized_cec(source, optimized)["status"] == "equivalent"
    net = parse_blif(optimized)
    fp = functional_fingerprint(net, "y")
    left = stable_target_id("b", "f", source, optimized, "y", fp)
    right = stable_target_id("b", "f", source, optimized, "y", fp)
    assert left == right
    assert file_hash(source)


def test_runner_and_checkers_controlled_outputs(tmp_path: Path) -> None:
    audit = tmp_path / "audit"
    out = tmp_path / "out"
    subprocess.run([sys.executable, str(ROOT / "scripts" / "run_necessity_first_targets.py"), "--mode", "all", "--audit-dir", str(audit), "--output-dir", str(out)], cwd=ROOT, check=True)
    subprocess.run([sys.executable, str(ROOT / "scripts" / "check_provenance_eligibility_results.py"), "--output-dir", str(audit)], cwd=ROOT, check=True)
    subprocess.run([sys.executable, str(ROOT / "scripts" / "check_necessity_first_target_results.py"), "--output-dir", str(out)], cwd=ROOT, check=True)
    rows = list(csv.DictReader((out / "eligible_target_manifest.csv").open()))
    assert rows
    assert all(row["eligibility_status"] == "eligible_target_necessary" for row in rows)


def test_checker_rejects_constant_eligible_target(tmp_path: Path) -> None:
    audit = tmp_path / "audit"
    out = tmp_path / "out"
    subprocess.run([sys.executable, str(ROOT / "scripts" / "run_necessity_first_targets.py"), "--mode", "all", "--audit-dir", str(audit), "--output-dir", str(out)], cwd=ROOT, check=True)
    path = out / "nonconstant_proofs.csv"
    rows = list(csv.DictReader(path.open()))
    fields = list(rows[0].keys())
    rows[0]["status"] = "constant"
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    result = subprocess.run([sys.executable, str(ROOT / "scripts" / "check_necessity_first_target_results.py"), "--output-dir", str(out)], cwd=ROOT)
    assert result.returncode != 0
