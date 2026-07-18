from __future__ import annotations

import csv
import os
import shutil
import subprocess
import sys
from pathlib import Path

from analyze_blif_matches import BlifNetwork, BlifNode, parse_blif
from cross_netlist_cut_transplantation import (
    CrossNetlistTransplantCandidate,
    adapter_depends_on_inputs,
    gf2_affine_adapter,
    prove_primary_output_equivalence,
    synthesize_exact_adapter,
    transplant_region_into_source,
    validate_transplant_graph,
    write_network,
    write_truth_blif,
)


ROOT = Path(__file__).resolve().parents[1]
ABC = ROOT / ".abc_build" / "abc_repo" / "abc"


def _abc_available() -> bool:
    override = os.environ.get("AIG_ABC")
    return Path(override).exists() if override else ABC.exists()


def test_cross_netlist_candidate_fingerprint_is_deterministic() -> None:
    candidate = CrossNetlistTransplantCandidate(
        candidate_id="c0",
        benchmark="b",
        optimization_flow="flow",
        split="dev",
        optimized_target="t",
        target_selection_reason="utility",
        optimized_region=("t", "b0"),
        source_region=("y",),
        optimized_input_cut=("u0",),
        source_input_cut=("a",),
        optimized_output_cut=("b0",),
        source_output_cut=("y",),
        input_residuals=(),
        output_residuals=("z",),
        input_adapter_id="ein",
        output_adapter_id="eout",
        target_polarity="positive",
        cloned_region_nodes=("xri_t", "xri_b0"),
        parent_search_state="seed",
        proposal_operator="initial",
        counterexample_history=(),
        proof_statuses={"input": "proven"},
        graph_rewrite_status="pending",
        activity_status="pending",
        boundary_utility="pending",
        critical_path_utility="pending",
        durability_status="pending",
        area_delta=0,
        depth_delta=0,
        runtime_seconds=0.0,
        rejection_reason="",
    )
    assert candidate.fingerprint == candidate.fingerprint
    assert candidate.source_blind is True
    assert candidate.to_row()["schema_version"].startswith("cross_netlist")


def test_input_adapter_synthesis_proves_permutation_and_finds_counterexample() -> None:
    ok = synthesize_exact_adapter(
        adapter_id="ein_ok",
        adapter_kind="input",
        mode="direct",
        primary_inputs=("a", "b"),
        interface_inputs=("a", "b"),
        output_order=("u0", "u1"),
        output_fn=lambda x: (x["b"], 1 - x["a"]),
    )
    assert ok.existence_status == "adapter_exists"
    assert ok.proof_status == "proven"

    bad = synthesize_exact_adapter(
        adapter_id="ein_bad",
        adapter_kind="input",
        mode="direct",
        primary_inputs=("a", "b"),
        interface_inputs=("a",),
        output_order=("u0",),
        output_fn=lambda x: (x["a"] ^ x["b"],),
    )
    assert bad.existence_status == "insufficient_interface"
    assert bad.solver_result == "sat"
    assert bad.counterexample_reproduced is True


def test_output_adapter_dependency_and_gf2_nonlinear_rejection() -> None:
    linear = synthesize_exact_adapter(
        adapter_id="linear",
        adapter_kind="output",
        mode="direct",
        primary_inputs=("a", "b"),
        interface_inputs=("a", "b"),
        output_order=("y",),
        output_fn=lambda x: (x["a"] ^ x["b"],),
    )
    assert adapter_depends_on_inputs(linear, ("a",))
    assert gf2_affine_adapter(linear)["linearity_status"] == "proved_affine"

    nonlinear = synthesize_exact_adapter(
        adapter_id="nonlinear",
        adapter_kind="output",
        mode="direct",
        primary_inputs=("a", "b"),
        interface_inputs=("a", "b"),
        output_order=("y",),
        output_fn=lambda x: (x["a"] & x["b"],),
    )
    gf2 = gf2_affine_adapter(nonlinear)
    assert gf2["linearity_status"] == "rejected_nonlinear"
    assert gf2["proof_status"] == "disproven_nonlinear"


def test_graph_transplant_is_active_and_equivalent(tmp_path: Path) -> None:
    source = tmp_path / "source.blif"
    region = tmp_path / "region.blif"
    out = tmp_path / "transplant.blif"
    write_truth_blif(source, "source", ("a", "z"), ("y",), lambda x: (x["a"] ^ x["z"],))
    write_network(
        BlifNetwork(
            inputs=["u0"],
            outputs=["b0"],
            nodes=[
                BlifNode(output="t", inputs=["u0"], cover=["1 1"]),
                BlifNode(output="b0", inputs=["t", "u0"], cover=["10 1", "11 1"]),
            ],
        ),
        region,
        model="region",
    )
    ein = synthesize_exact_adapter(
        adapter_id="ein",
        adapter_kind="input",
        mode="direct",
        primary_inputs=("a", "z"),
        interface_inputs=("a",),
        output_order=("u0",),
        output_fn=lambda x: (x["a"],),
    )
    eout = synthesize_exact_adapter(
        adapter_id="eout",
        adapter_kind="output",
        mode="direct",
        primary_inputs=("a", "z"),
        interface_inputs=("b0", "z"),
        output_order=("y",),
        output_fn=lambda x: (x["a"] ^ x["z"],),
        interface_fn=lambda x: (x["a"], x["z"]),
    )
    graph = transplant_region_into_source(source_path=source, region_path=region, input_adapter=ein, output_adapter=eout, output_path=out)
    assert graph["graph_rewrite_status"] == "valid"
    assert graph["graph_active"] == "true"
    assert "xri_t" in {node.output for node in parse_blif(out).nodes}
    assert prove_primary_output_equivalence(source, out)["formal_status"] == "equivalent"


def test_graph_validation_rejects_dangling_multiple_driver_and_cycle(tmp_path: Path) -> None:
    dangling = tmp_path / "dangling.blif"
    dangling.write_text(".model d\n.inputs a\n.outputs y\n.names missing y\n1 1\n.end\n", encoding="utf-8")
    assert validate_transplant_graph(dangling, target_node="xri_t", bi_nodes=("xri_b0",), source_outputs=("y",), removed_source_nodes=("y",))["graph_rewrite_status"] == "invalid_dangling_net"

    multiple = tmp_path / "multiple.blif"
    multiple.write_text(".model m\n.inputs a\n.outputs y\n.names a xri_t\n1 1\n.names a xri_t\n0 1\n.names xri_t y\n1 1\n.end\n", encoding="utf-8")
    assert validate_transplant_graph(multiple, target_node="xri_t", bi_nodes=("xri_t",), source_outputs=("y",), removed_source_nodes=("y",))["graph_rewrite_status"] == "invalid_multiple_driver"

    cycle = tmp_path / "cycle.blif"
    cycle.write_text(".model c\n.inputs a\n.outputs y\n.names y xri_t\n1 1\n.names xri_t y\n1 1\n.end\n", encoding="utf-8")
    assert validate_transplant_graph(cycle, target_node="xri_t", bi_nodes=("xri_t",), source_outputs=("y",), removed_source_nodes=("y",))["graph_rewrite_status"] == "invalid_cycle"


def test_controlled_runner_and_checker(tmp_path: Path) -> None:
    out = tmp_path / "out"
    bench = tmp_path / "bench"
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "run_cross_netlist_cut_transplantation.py"), "--mode", "controlled", "--output-dir", str(out), "--bench-dir", str(bench)],
        cwd=ROOT,
        check=True,
    )
    cmd = [sys.executable, str(ROOT / "scripts" / "check_cross_netlist_transplant_results.py"), "--output-dir", str(out)]
    if not _abc_available():
        cmd.append("--allow-no-abc")
    subprocess.run(cmd, cwd=ROOT, check=True)
    controlled = list(csv.DictReader((out / "controlled_results.csv").open()))
    accepted = [row for row in controlled if row["final_status"] == "accepted"]
    if _abc_available():
        assert len(accepted) == 12
        assert all(row["source_cec_status"] == "equivalent" and row["cross_cec_status"] == "equivalent" for row in accepted)
        for family in ("affine", "add_add", "bilinear", "mac"):
            assert any(row["family"] == family and row["final_status"] == "accepted" for row in controlled)
    else:
        assert not accepted
        positives = [row for row in controlled if row["expected_outcome"].startswith("positive")]
        assert {row["family"] for row in positives} >= {"affine", "add_add", "bilinear", "mac"}
        assert all(row["local_proof_status"] == "equivalent" for row in positives)
        assert all(row["source_cec_status"] != "equivalent" for row in positives)
        assert all(row["new_recovered_boundary"] == "false" for row in controlled)
    negatives = [row for row in controlled if row["expected_outcome"].startswith("negative")]
    assert negatives and all(row["final_status"] == "rejected" for row in negatives)


def test_controlled_runner_explicit_no_abc_schema_mode(tmp_path: Path) -> None:
    out = tmp_path / "out"
    bench = tmp_path / "bench"
    env = {**os.environ, "AIG_ABC": str(tmp_path / "missing_abc")}
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "run_cross_netlist_cut_transplantation.py"), "--mode", "controlled", "--output-dir", str(out), "--bench-dir", str(bench)],
        cwd=ROOT,
        check=True,
        env=env,
    )
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "check_cross_netlist_transplant_results.py"), "--output-dir", str(out), "--allow-no-abc"],
        cwd=ROOT,
        check=True,
        env=env,
    )
    controlled = list(csv.DictReader((out / "controlled_results.csv").open()))
    assert sum(row["final_status"] == "accepted" for row in controlled) == 0
    assert all(row["new_recovered_boundary"] == "false" for row in controlled)
    assert all(row["source_cec_status"] != "equivalent" for row in controlled)


def test_checker_rejects_boundary_without_global_cec(tmp_path: Path) -> None:
    out = tmp_path / "out"
    bench = tmp_path / "bench"
    env = {**os.environ, "AIG_ABC": str(tmp_path / "missing_abc")}
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "run_cross_netlist_cut_transplantation.py"), "--mode", "controlled", "--output-dir", str(out), "--bench-dir", str(bench)],
        cwd=ROOT,
        check=True,
        env=env,
    )
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "check_cross_netlist_transplant_results.py"), "--output-dir", str(out), "--allow-no-abc"],
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
        [sys.executable, str(ROOT / "scripts" / "check_cross_netlist_transplant_results.py"), "--output-dir", str(out), "--allow-no-abc"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
    )
    assert proc.returncode != 0
    assert "S-vs-Sprime CEC" in proc.stderr or "ABC unavailable" in proc.stderr
