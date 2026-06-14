import csv
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts import approximate_node_distance as andist


def test_identical_functions_have_distance_zero():
    assert andist.hamming_distance_fraction(0b101010, 0b101010, 6) == 0.0


def test_complemented_single_input_functions_have_distance_one():
    # f = x has signature 10 over assignments {0, 1}; NOT x has 01.
    assert andist.hamming_distance_fraction(0b10, 0b01, 2) == 1.0


def test_partially_different_functions_have_expected_distance():
    # Differ in two of four bit positions.
    assert andist.hamming_distance_fraction(0b1100, 0b1010, 4) == pytest.approx(0.5)


def test_exact_mode_used_only_below_threshold():
    assert andist.choose_distance_mode(3, max_exact_support=3, sampled_fallback=True) == "exact"
    assert andist.choose_distance_mode(4, max_exact_support=3, sampled_fallback=True) == "sampled"
    assert andist.choose_distance_mode(4, max_exact_support=3, sampled_fallback=False) == "skipped"


def test_exact_pattern_values_only_vary_active_support():
    values, mask, pattern_count = andist.exact_pattern_values(["a", "b", "c"], {"a", "c"})

    assert pattern_count == 4
    assert mask == 0b1111
    assert values["a"] == 0b1010
    assert values["b"] == 0
    assert values["c"] == 0b1100


def test_sampled_pattern_values_are_deterministic_and_labeled_large_support():
    first, _, count = andist.sampled_pattern_values(
        ["a", "b", "c"], {"a", "b", "c"}, pattern_count=32, seed_key="same"
    )
    second, _, _ = andist.sampled_pattern_values(
        ["a", "b", "c"], {"a", "b", "c"}, pattern_count=32, seed_key="same"
    )

    assert count == 32
    assert first == second
    assert andist.choose_distance_mode(10, max_exact_support=2, sampled_fallback=True) == "sampled"


def test_evaluate_network_exact_distance_for_small_blif(tmp_path):
    blif = tmp_path / "simple.blif"
    blif.write_text(
        "\n".join(
            [
                ".model simple",
                ".inputs a b",
                ".outputs y",
                ".names a n_a",
                "1 1",
                ".names a b n_and",
                "11 1",
                ".names n_and y",
                "1 1",
                ".end",
            ]
        ),
        encoding="utf-8",
    )
    values, mask, pattern_count = andist.exact_pattern_values(["a", "b"], {"a", "b"})
    evaluated = andist.evaluate_network_with_values(blif, values, mask)

    distance = andist.hamming_distance_fraction(
        evaluated["n_a"].value, evaluated["n_and"].value, pattern_count
    )
    assert distance == pytest.approx(0.25)


def test_summary_columns_are_stable():
    rows = pd.DataFrame(
        [
            {"distance_mode": "exact", "sat_status": "verified", "distance": 0.0},
            {"distance_mode": "exact", "sat_status": "rejected", "distance": 0.25},
        ]
    )
    summary = andist.summarize_distances(rows)

    expected = {
        "distance_mode",
        "sat_status",
        "count",
        "mean_distance",
        "median_distance",
        "min_distance",
        "max_distance",
        "pct_distance_le_1pct",
        "pct_distance_le_5pct",
        "pct_distance_le_10pct",
    }
    assert expected.issubset(summary.columns)


def test_output_files_have_expected_columns(tmp_path, monkeypatch):
    exact = pd.DataFrame(
        [
            {
                "benchmark": "external_iscas85_c17",
                "circuit": "c17",
                "optimization": "rewrite",
                "optimized_node": "n1",
                "original_candidate": "n2",
                "rank": 1,
                "sat_status": "verified",
                "combined_score": 1.0,
                "support_overlap": 1.0,
                "simulation_similarity": 1.0,
                "distance_mode": "exact",
                "skip_reason": "ok",
                "union_support_size": 1,
                "pattern_count": 2,
                "distance": 0.0,
                "similarity": 1.0,
                "is_formal_distance": True,
            }
        ]
    )
    sampled = exact.assign(distance_mode="sampled", is_formal_distance=False)
    skipped = exact.assign(distance_mode="skipped", distance=None, similarity=None)
    summary = andist.summarize_distances(pd.concat([exact, sampled], ignore_index=True))

    monkeypatch.setattr(andist, "SUMMARY_MD", tmp_path / "summary.md")
    andist.write_markdown_summary(summary, exact, sampled, skipped)
    assert (tmp_path / "summary.md").read_text(encoding="utf-8").startswith(
        "# Approximate Node Distance Summary"
    )

    out = tmp_path / "exact.csv"
    exact.to_csv(out, index=False)
    with out.open(newline="", encoding="utf-8") as fh:
        header = next(csv.reader(fh))
    assert {"distance_mode", "distance", "similarity", "is_formal_distance"}.issubset(header)
