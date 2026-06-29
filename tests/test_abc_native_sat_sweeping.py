import csv
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_REPO_ROOT))
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from abc_native_sat_sweep_baseline import BaselineRow, parse_ps_metrics, write_baseline_csv
from probe_abc_sat_sweeping import (
    ProbeResult,
    command_supported,
    looks_unsupported,
    write_csv as write_capability_csv,
)


def test_parse_ps_metrics_extracts_nodes_and_levels():
    text = """
    probe : i/o = 3/1 lat = 0 and = 5 lev = 3
    probe : i/o = 3/1 lat = 0 and = 4 lev = 2
    """
    assert parse_ps_metrics(text) == [(5, 3), (4, 2)]


def test_parse_ps_metrics_ignores_unrelated_text():
    assert parse_ps_metrics("ABC command line\nno stats here\n") == []


def test_unsupported_command_detection():
    output = "ABC command line: unknown command '&fraig'"
    assert looks_unsupported(output)
    assert not command_supported(0, output)


def test_supported_ps_command_detection():
    output = "probe : i/o = 3/1 lat = 0 and = 2 lev = 1"
    assert command_supported(0, output, required_pattern=r"and\s*=")


def test_capability_csv_schema(tmp_path):
    out = tmp_path / "capabilities.csv"
    write_capability_csv(
        [
            ProbeResult(
                command="fraig",
                supported=True,
                exit_code=0,
                stdout_stderr_snippet="ok",
            )
        ],
        out,
    )
    with out.open(newline="", encoding="utf-8") as fh:
        reader = csv.reader(fh)
        header = next(reader)
    assert header == ["command", "supported", "exit_code", "stdout_stderr_snippet"]


def test_baseline_csv_schema(tmp_path):
    out = tmp_path / "baseline.csv"
    row = BaselineRow(
        benchmark="majority3",
        source_family="toy",
        optimization="rewrite",
        original_optimized_blif_path="variants/majority3_rewrite.blif",
        abc_sweep_flow_name="fraig",
        node_count_before=5,
        node_count_after=4,
        level_count_before=3,
        level_count_after=2,
        node_reduction=1,
        level_reduction=1,
        runtime_seconds=0.01,
        abc_reported_equivalence_or_failure="completed",
        abc_statistics="stats",
        swept_blif_path="results/abc_native_swept/majority3_rewrite_fraig.blif",
    )
    write_baseline_csv([row], out)
    with out.open(newline="", encoding="utf-8") as fh:
        header = next(csv.reader(fh))
    assert header == [
        "benchmark",
        "source_family",
        "optimization",
        "original_optimized_blif_path",
        "abc_sweep_flow_name",
        "node_count_before",
        "node_count_after",
        "level_count_before",
        "level_count_after",
        "node_reduction",
        "level_reduction",
        "runtime_seconds",
        "abc_reported_equivalence_or_failure",
        "abc_statistics",
        "swept_blif_path",
    ]

