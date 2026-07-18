import csv
import subprocess
import sys

import pytest

pytest.importorskip("z3")

from boundary_graph import CircuitGraph
from joint_region_interface import (
    add_cut_inputs,
    diagnose_counterexample,
    make_candidate,
    promote_outputs,
    recompute_closure,
    reorder_outputs,
    seed_from_output_cone,
    transition_row,
)
from semantic_region_replacement import derive_closed_region, full_adder_module, write_replaced_blif


ROOT = __import__("pathlib").Path(__file__).resolve().parents[1]


def write_full_adder(tmp_path):
    path = tmp_path / "fa.blif"
    path.write_text(
        """.model fa
.inputs a b cin
.outputs sum cout
.names a b xab
10 1
01 1
.names xab cin sum
10 1
01 1
.names a b ab
11 1
.names a cin ac
11 1
.names b cin bc
11 1
.names ab ac bc cout
1-- 1
-1- 1
--1 1
.end
""",
        encoding="utf-8",
    )
    return path


def test_joint_candidate_fingerprint_is_deterministic(tmp_path):
    graph = CircuitGraph.from_blif(write_full_adder(tmp_path))
    first = seed_from_output_cone(graph, seed_id="seed", benchmark="fa", outputs=("sum", "cout"), max_nodes=16)
    second = seed_from_output_cone(graph, seed_id="seed", benchmark="fa", outputs=("cout", "sum"), max_nodes=16)
    assert first.fingerprint == second.fingerprint
    assert first.source_blind is True
    assert first.closure_status == "closed"


def test_counterexample_repair_adds_missing_cut_input(tmp_path):
    graph = CircuitGraph.from_blif(write_full_adder(tmp_path))
    region, cut, edges, _ = derive_closed_region(graph, ("sum", "cout"))
    broken = make_candidate(
        seed_id="seed",
        benchmark="fa",
        implementation_nodes=region,
        input_cut=tuple(node for node in cut if node != "cin"),
        output_cut=("sum", "cout"),
        external_fanout_edges=edges,
        observable_outputs=("sum", "cout"),
    )
    broken = recompute_closure(graph, broken)
    assert broken.closure_status == "invalid_incomplete_input_cut"
    fixed = add_cut_inputs(graph, broken, ("cin",))
    assert "cin" in fixed.input_cut
    assert fixed.closure_status == "closed"


def test_promote_and_reorder_outputs_are_recorded(tmp_path):
    graph = CircuitGraph.from_blif(write_full_adder(tmp_path))
    seed = seed_from_output_cone(graph, seed_id="seed", benchmark="fa", outputs=("sum",), max_nodes=16)
    promoted = promote_outputs(graph, seed, ("cout",))
    reordered = reorder_outputs(promoted, ("cout", "sum"))
    row = transition_row(from_candidate=promoted, to_candidate=reordered, operation="reorder_output_bits", reason="test")
    assert "cout" in promoted.output_cut
    assert reordered.output_cut == ("cout", "sum")
    assert row["operation"] == "reorder_output_bits"


def test_counterexample_diagnostic_is_source_blind_and_influential(tmp_path):
    graph = CircuitGraph.from_blif(write_full_adder(tmp_path))
    seed = seed_from_output_cone(graph, seed_id="seed", benchmark="fa", outputs=("sum",), max_nodes=16)
    row = diagnose_counterexample(
        seed,
        counterexample_id="cex0",
        assignment={"a": 1, "b": 1, "cin": 0},
        failing_outputs=("cout",),
        suggested_operation="promote_output",
        suggested_nodes=("cout",),
    )
    assert row["counterexample_reproduced"] == "true"
    assert row["influenced_next_candidate"] == "true"
    assert row["source_blind"] == "true"


def test_graph_active_joint_replacement_uses_real_writer(tmp_path):
    path = write_full_adder(tmp_path)
    graph = CircuitGraph.from_blif(path)
    region, _, _, status = derive_closed_region(graph, ("sum", "cout"))
    assert status == "closed"
    out = tmp_path / "replaced.blif"
    result = write_replaced_blif(path, region, full_adder_module(), out)
    assert result["graph_rewrite_status"] == "valid"
    assert result["graph_active"] == "true"
    assert out.exists()


def test_joint_controlled_pipeline_and_checker_run(tmp_path):
    out_dir = tmp_path / "joint_results"
    bench_dir = tmp_path / "joint_bench"
    subprocess.run(
        [
            sys.executable,
            "scripts/run_joint_region_interface_discovery.py",
            "--mode",
            "controlled",
            "--max-real-seeds",
            "0",
            "--output-dir",
            str(out_dir),
            "--bench-dir",
            str(bench_dir),
        ],
        cwd=ROOT,
        check=True,
    )
    checker = [sys.executable, "scripts/check_joint_region_interface_results.py", "--output-dir", str(out_dir)]
    if not (ROOT / ".abc_build" / "abc_repo" / "abc").exists():
        checker.append("--allow-no-abc")
    subprocess.run(checker, cwd=ROOT, check=True)
    rows = list(csv.DictReader((out_dir / "controlled_benchmark_results.csv").open()))
    positives = [row for row in rows if row["expected_outcome"].startswith("positive")]
    assert positives
    if (ROOT / ".abc_build" / "abc_repo" / "abc").exists():
        assert any(row["final_status"] == "accepted" for row in positives)


def test_checker_rejects_fabricated_global_cec(tmp_path):
    if not (ROOT / ".abc_build" / "abc_repo" / "abc").exists():
        pytest.skip("ABC is required to create an accepted controlled row before corruption")
    out_dir = tmp_path / "joint_results"
    bench_dir = tmp_path / "joint_bench"
    subprocess.run(
        [
            sys.executable,
            "scripts/run_joint_region_interface_discovery.py",
            "--mode",
            "controlled",
            "--max-real-seeds",
            "0",
            "--output-dir",
            str(out_dir),
            "--bench-dir",
            str(bench_dir),
        ],
        cwd=ROOT,
        check=True,
    )
    cec_path = out_dir / "global_cec_results.csv"
    rows = list(csv.DictReader(cec_path.open()))
    for row in rows:
        if row["implementation_global_cec"] == "equivalent":
            row["implementation_global_cec"] = "not_run"
            break
    with cec_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=rows[0].keys(), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    result = subprocess.run(
        [sys.executable, "scripts/check_joint_region_interface_results.py", "--output-dir", str(out_dir)],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert result.returncode != 0
    assert "lacks equivalent global CEC" in result.stderr
