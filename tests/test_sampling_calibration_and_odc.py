import csv
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from calibrate_approximate_distance_sampling import (  # noqa: E402
    CalibrationRow,
    spearman_rank_correlation,
    summarize,
    write_csv as write_calibration_csv,
)
from odc_aware_match_probe import (  # noqa: E402
    OdcProbeRow,
    compute_global_distance,
    controlled_blif_pair,
    parse_cec_observable_difference,
    write_csv as write_odc_csv,
)
from scripts.approximate_node_distance import sampled_pattern_values  # noqa: E402


def test_sampling_summary_error_metrics():
    rows = [
        CalibrationRow(
            benchmark="b",
            optimization="rewrite",
            optimized_node="o1",
            original_candidate="n1",
            sat_status="rejected",
            union_support_size=2,
            exact_distance=0.25,
            sample_size=128,
            seed=0,
            sampled_distance=0.20,
            absolute_error=0.05,
            exact_rank=1.0,
            sampled_rank=2.0,
            absolute_rank_delta=1.0,
        ),
        CalibrationRow(
            benchmark="b",
            optimization="rewrite",
            optimized_node="o2",
            original_candidate="n2",
            sat_status="rejected",
            union_support_size=2,
            exact_distance=0.50,
            sample_size=128,
            seed=0,
            sampled_distance=0.51,
            absolute_error=0.01,
            exact_rank=2.0,
            sampled_rank=1.0,
            absolute_rank_delta=1.0,
        ),
    ]
    summary = summarize(rows)
    assert summary.loc[0, "mean_absolute_error"] == pytest.approx(0.03)
    assert summary.loc[0, "max_error"] == pytest.approx(0.05)
    assert summary.loc[0, "pct_within_5pct_abs_error"] == pytest.approx(1.0)


def test_seeded_sampling_is_deterministic_for_calibration_inputs():
    first, _, count = sampled_pattern_values(["a", "b"], {"a", "b"}, 128, "pair|seed=7")
    second, _, _ = sampled_pattern_values(["a", "b"], {"a", "b"}, 128, "pair|seed=7")
    assert count == 128
    assert first == second


def test_spearman_rank_correlation_for_reversed_order():
    assert spearman_rank_correlation([1, 2, 3], [3, 2, 1]) == pytest.approx(-1.0)


def test_calibration_csv_schema(tmp_path):
    out = tmp_path / "calibration.csv"
    row = CalibrationRow(
        benchmark="b",
        optimization="balance",
        optimized_node="o",
        original_candidate="n",
        sat_status="verified",
        union_support_size=3,
        exact_distance=0.0,
        sample_size=512,
        seed=1,
        sampled_distance=0.0,
        absolute_error=0.0,
        exact_rank=1.0,
        sampled_rank=1.0,
        absolute_rank_delta=0.0,
    )
    write_calibration_csv([row], out)
    with out.open(newline="", encoding="utf-8") as fh:
        header = next(csv.reader(fh))
    assert header == list(CalibrationRow.__annotations__)


def test_odc_controlled_masked_example_has_global_difference(tmp_path):
    original, _modified = controlled_blif_pair("masked_and_or")
    distance = compute_global_distance(original, "f_and", "g_or", tmp_path)
    assert distance == pytest.approx(0.5)


def test_parse_cec_observable_difference():
    assert parse_cec_observable_difference("Networks are equivalent after structural hashing.")[1] is False
    assert parse_cec_observable_difference("Networks are NOT EQUIVALENT.")[1] is True
    parsed, observable, result = parse_cec_observable_difference("unexpected output")
    assert not parsed
    assert not observable
    assert result == "unknown"


def test_odc_csv_schema(tmp_path):
    out = tmp_path / "odc.csv"
    row = OdcProbeRow(
        example_name="masked_and_or",
        candidate_f="f_and",
        candidate_g="g_or",
        global_distance=0.5,
        output_observable_difference=False,
        abc_supported=True,
        abc_result="equivalent",
        interpretation="hidden",
        stdout_stderr_snippet="ok",
    )
    write_odc_csv([row], out)
    with out.open(newline="", encoding="utf-8") as fh:
        header = next(csv.reader(fh))
    assert header == list(OdcProbeRow.__annotations__)
