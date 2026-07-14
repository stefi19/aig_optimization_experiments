import csv
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from analyze_blif_matches import parse_blif  # noqa: E402
from probe_abc_sat_sweeping import command_supported, looks_unsupported  # noqa: E402
from probe_abc_timing_commands import (  # noqa: E402
    TimingProbeRow,
    has_timing_related_output,
    write_csv as write_timing_probe_csv,
)
from timing_aware_path_probe import (  # noqa: E402
    TimingComparisonRow,
    TimingPathRow,
    classify_node_delay,
    compute_delay_weighted_path,
    extract_structural_path,
    write_csvs,
)


def write_tiny_blif(path: Path) -> None:
    path.write_text(
        "\n".join(
            [
                ".model tiny",
                ".inputs a b c d",
                ".outputs y",
                ".names a b n1",
                "11 1",
                ".names n1 c n2",
                "11 1",
                ".names a b c wide",
                "111 1",
                ".names wide d y",
                "11 1",
                ".end",
            ]
        ),
        encoding="utf-8",
    )


def test_timing_related_output_detection():
    assert has_timing_related_output("network: and = 2 lev = 3")
    assert has_timing_related_output("area = 2.00 delay = 2.00")
    assert not has_timing_related_output("ABC command line")


def test_unsupported_timing_command_detection():
    output = "Error: Delay trace works only for network mapped into standard cells."
    assert looks_unsupported(output)
    assert not command_supported(0, output)


def test_delay_model_for_simple_and_wide_nodes(tmp_path):
    path = tmp_path / "tiny.blif"
    write_tiny_blif(path)
    net = parse_blif(path)
    by_name = {node.output: node for node in net.nodes}
    assert classify_node_delay(by_name["n1"]) == pytest.approx(1.0)
    assert classify_node_delay(by_name["wide"]) == pytest.approx(1.2)


def test_delay_weighted_longest_path_on_small_blif(tmp_path):
    path = tmp_path / "tiny.blif"
    write_tiny_blif(path)
    net = parse_blif(path)
    structural = extract_structural_path(net)
    delay_path = compute_delay_weighted_path(net)
    assert [node.node for node in structural]
    assert [node.node for node in delay_path]
    assert delay_path[-1].arrival_time >= structural[-1].arrival_time - 1


def test_timing_probe_csv_schema(tmp_path):
    out = tmp_path / "abc_timing.csv"
    write_timing_probe_csv(
        [
            TimingProbeRow(
                command="ps",
                supported=True,
                exit_code=0,
                timing_related_output=True,
                stdout_stderr_snippet="lev = 2",
            )
        ],
        out,
    )
    with out.open(newline="", encoding="utf-8") as fh:
        header = next(csv.reader(fh))
    assert header == list(TimingProbeRow.__annotations__)


def test_timing_path_output_schema(tmp_path, monkeypatch):
    monkeypatch.setattr("timing_aware_path_probe.TIMING_PATH_CSV", tmp_path / "timing_path.csv")
    monkeypatch.setattr("timing_aware_path_probe.COMPARE_CSV", tmp_path / "compare.csv")
    path_row = TimingPathRow(
        benchmark="external_iscas85_c432",
        circuit="c432",
        optimization="rewrite",
        path_type="delay_weighted",
        path_length=1,
        path_index=1,
        optimized_node="n1",
        structural_level=1,
        node_delay=1.0,
        arrival_time=1.0,
        mapped_original_node="n1",
        mapping_category="exact_signature_match",
        confidence=1.0,
        distance=None,
        explanation="test",
    )
    comparison = TimingComparisonRow(
        benchmark="external_iscas85_c432",
        circuit="c432",
        optimization="rewrite",
        structural_path_length=1,
        delay_weighted_path_length=1,
        structural_mapped_fraction=1.0,
        delay_weighted_mapped_fraction=1.0,
        structural_unresolved_fraction=0.0,
        delay_weighted_unresolved_fraction=0.0,
        shared_node_count=1,
        shared_node_jaccard=1.0,
        delay_path_total_delay=1.0,
        structural_path_total_proxy_delay=1.0,
    )
    write_csvs([path_row], [comparison])
    with (tmp_path / "timing_path.csv").open(newline="", encoding="utf-8") as fh:
        assert next(csv.reader(fh)) == list(TimingPathRow.__annotations__)
    with (tmp_path / "compare.csv").open(newline="", encoding="utf-8") as fh:
        assert next(csv.reader(fh)) == list(TimingComparisonRow.__annotations__)
