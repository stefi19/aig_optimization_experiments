from __future__ import annotations

import csv
import subprocess
import sys
from pathlib import Path

from analyze_blif_matches import parse_blif
from necessity_first_rewrites import synthesize_compact_interface_rewrite
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


def _missing_abc(tmp_path: Path) -> Path:
    return tmp_path / "missing_abc"


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


def test_compact_rewrite_synthesizes_adder_carry(tmp_path: Path) -> None:
    source = tmp_path / "source.blif"
    optimized = tmp_path / "optimized.blif"
    _write_blif(
        source,
        """
        .model adder_source
        .inputs a0 b0 cin
        .outputs y
        .names a0 b0 ab
        11 1
        .names a0 cin ac
        11 1
        .names b0 cin bc
        11 1
        .names ab ac bc t
        1-- 1
        -1- 1
        --1 1
        .names t y
        1 1
        .end
        """,
    )
    _write_blif(
        optimized,
        """
        .model adder_optimized
        .inputs a0 b0 cin
        .outputs y
        .names a0 b0 ab
        11 1
        .names a0 cin ac
        11 1
        .names b0 cin bc
        11 1
        .names ab ac bc t
        1-- 1
        -1- 1
        --1 1
        .names t y
        1 1
        .end
        """,
    )
    result = synthesize_compact_interface_rewrite(
        stable_target_id="adder",
        source_path=source,
        optimized_path=optimized,
        optimized_target_node="t",
        tested_interface=("a0", "b0", "cin"),
        output_path=tmp_path / "rewrite.blif",
        root=tmp_path,
        abc_path=_missing_abc(tmp_path),
    )
    assert result.rewrite_emitted
    assert result.graph_active
    assert result.onset_size == 4
    assert result.cec_source_status == "abc_unavailable"


def test_compact_rewrite_synthesizes_mux(tmp_path: Path) -> None:
    source = tmp_path / "source.blif"
    optimized = tmp_path / "optimized.blif"
    body = """
        .model mux
        .inputs d0 d1 s0
        .outputs y
        .names s0 ns0
        0 1
        .names d0 ns0 left
        11 1
        .names d1 s0 right
        11 1
        .names left right t
        1- 1
        -1 1
        .names t y
        1 1
        .end
        """
    _write_blif(source, body)
    _write_blif(optimized, body)
    result = synthesize_compact_interface_rewrite(
        stable_target_id="mux",
        source_path=source,
        optimized_path=optimized,
        optimized_target_node="t",
        tested_interface=("d0", "d1", "s0"),
        output_path=tmp_path / "mux_rewrite.blif",
        root=tmp_path,
        abc_path=_missing_abc(tmp_path),
    )
    assert result.rewrite_emitted
    assert result.graph_active
    assert result.onset_size == 4


def test_compact_rewrite_handles_empty_constant_interface(tmp_path: Path) -> None:
    source = tmp_path / "source.blif"
    optimized = tmp_path / "optimized.blif"
    body = """
        .model const
        .inputs a
        .outputs y
        .names a t
        - 1
        .names t y
        1 1
        .end
        """
    _write_blif(source, body)
    _write_blif(optimized, body)
    result = synthesize_compact_interface_rewrite(
        stable_target_id="const",
        source_path=source,
        optimized_path=optimized,
        optimized_target_node="t",
        tested_interface=tuple(),
        output_path=tmp_path / "const_rewrite.blif",
        root=tmp_path,
        abc_path=_missing_abc(tmp_path),
    )
    assert result.rewrite_emitted
    assert result.graph_active
    assert result.onset_size == 1
    text = (tmp_path / "const_rewrite.blif").read_text(encoding="utf-8")
    assert ".names t\n1" in text


def test_checker_rejects_missing_rewrite_artifact(tmp_path: Path) -> None:
    audit = tmp_path / "audit"
    out = tmp_path / "out"
    subprocess.run([sys.executable, str(ROOT / "scripts" / "run_necessity_first_targets.py"), "--mode", "all", "--audit-dir", str(audit), "--output-dir", str(out)], cwd=ROOT, check=True)
    path = out / "graph_rewrites.csv"
    rows = list(csv.DictReader(path.open()))
    fields = list(rows[0].keys())
    emitted = next(row for row in rows if row["rewrite_emitted"] == "true")
    emitted["rewrite_artifact"] = "results/necessity_first_target_discovery/artifacts/missing.blif"
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    result = subprocess.run([sys.executable, str(ROOT / "scripts" / "check_necessity_first_target_results.py"), "--output-dir", str(out)], cwd=ROOT)
    assert result.returncode != 0


def test_checker_rejects_duplicate_driver_rewrite_artifact(tmp_path: Path) -> None:
    audit = tmp_path / "audit"
    out = tmp_path / "out"
    subprocess.run([sys.executable, str(ROOT / "scripts" / "run_necessity_first_targets.py"), "--mode", "all", "--audit-dir", str(audit), "--output-dir", str(out)], cwd=ROOT, check=True)
    graph_rows = list(csv.DictReader((out / "graph_rewrites.csv").open()))
    synth_rows = {row["stable_target_id"]: row for row in csv.DictReader((out / "rewrite_function_synthesis.csv").open())}
    emitted = next(row for row in graph_rows if row["rewrite_emitted"] == "true")
    target = synth_rows[emitted["stable_target_id"]]["optimized_target_node"]
    artifact = ROOT / emitted["rewrite_artifact"]
    with artifact.open("a", encoding="utf-8") as fh:
        fh.write(f".names {target}\n1\n")
    result = subprocess.run([sys.executable, str(ROOT / "scripts" / "check_necessity_first_target_results.py"), "--output-dir", str(out)], cwd=ROOT)
    assert result.returncode != 0


def test_checker_rejects_graph_active_boundary_without_cec(tmp_path: Path) -> None:
    audit = tmp_path / "audit"
    out = tmp_path / "out"
    subprocess.run([sys.executable, str(ROOT / "scripts" / "run_necessity_first_targets.py"), "--mode", "all", "--audit-dir", str(audit), "--output-dir", str(out)], cwd=ROOT, check=True)
    boundary_path = out / "boundary_recovery.csv"
    cec_path = out / "global_cec.csv"
    boundary_rows = list(csv.DictReader(boundary_path.open()))
    boundary_fields = list(boundary_rows[0].keys())
    accepted = next(row for row in boundary_rows if row["new_boundary"] == "true")
    cec_rows = list(csv.DictReader(cec_path.open()))
    cec_fields = list(cec_rows[0].keys())
    for row in cec_rows:
        if row["stable_target_id"] == accepted["stable_target_id"] and row["scope"] == "Sprime_vs_I":
            row["status"] = "not_run"
    with boundary_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=boundary_fields)
        writer.writeheader()
        writer.writerows(boundary_rows)
    with cec_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=cec_fields)
        writer.writeheader()
        writer.writerows(cec_rows)
    result = subprocess.run([sys.executable, str(ROOT / "scripts" / "check_necessity_first_target_results.py"), "--output-dir", str(out)], cwd=ROOT)
    assert result.returncode != 0


def test_identity_bypass_rewrite_is_not_graph_active(tmp_path: Path) -> None:
    audit = tmp_path / "audit"
    out = tmp_path / "out"
    subprocess.run([sys.executable, str(ROOT / "scripts" / "run_necessity_first_targets.py"), "--mode", "all", "--audit-dir", str(audit), "--output-dir", str(out)], cwd=ROOT, check=True)
    rows = list(csv.DictReader((out / "graph_rewrites.csv").open()))
    bypass = [row for row in rows if row["reason"] == "rewrite_not_graph_active"]
    assert bypass
    assert all(row["rewrite_emitted"] == "true" and row["graph_active"] == "false" for row in bypass)
