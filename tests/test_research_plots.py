"""
tests/test_research_plots.py

Unit tests for research_plots.py.
All tests are in-memory (no real CSV/PNG files required).
"""

from __future__ import annotations

import importlib
import sys
import types
import warnings
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

# ---------------------------------------------------------------------------
# Helpers to import research_plots without running __main__ code and while
# intercepting filesystem + matplotlib calls.
# ---------------------------------------------------------------------------

MODULE = "research_plots"


def _import_rp():
    if MODULE in sys.modules:
        return sys.modules[MODULE]
    return importlib.import_module(MODULE)


# ── Fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture()
def summary_df():
    return pd.DataFrame({
        "benchmark":                ["bA", "bA", "bB", "bB"],
        "optimization":             ["balance", "refactor", "balance", "refactor"],
        "original_nodes":           [4, 4, 6, 6],
        "optimized_nodes":          [4, 3, 5, 6],
        "original_levels":          [3, 3, 4, 4],
        "optimized_levels":         [3, 3, 3, 4],
        "exact_internal_matches":   [3, 1, 5, 2],
        "old_signatures_disappeared": [1, 3, 1, 4],
        "new_signatures_appeared":  [1, 2, 0, 3],
        "avg_best_support_overlap": [1.0, 1.0, 0.9, 0.8],
        "simulation_mode":          ["exact", "exact", "exact", "exact"],
    })


@pytest.fixture()
def top_candidates_df():
    return pd.DataFrame({
        "benchmark":            ["bA"] * 4 + ["bB"] * 4,
        "optimization":         ["balance"] * 4 + ["balance"] * 4,
        "optimized_node":       ["n1", "n1", "n2", "n2", "n3", "n3", "n4", "n4"],
        "rank":                 [1, 2, 1, 2, 1, 2, 1, 2],
        "original_candidate":   ["o1", "o2", "o3", "o4", "o5", "o6", "o7", "o8"],
        "combined_score":       [1.0, 0.7, 0.9, 0.6, 1.0, 0.8, 0.85, 0.5],
        "simulation_similarity": [1.0, 0.8, 0.9, 0.7, 1.0, 0.9, 0.8, 0.6],
        "support_overlap":      [1.0, 0.5, 0.8, 0.4, 1.0, 0.6, 0.75, 0.5],
        "depth_similarity":     [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0],
        "optimized_level":      [1, 1, 2, 2, 1, 1, 2, 2],
        "original_level":       [1, 1, 2, 2, 1, 1, 2, 2],
    })


@pytest.fixture()
def sat_summary_df():
    return pd.DataFrame({
        "benchmark":        ["bA", "bA", "bB", "bB"],
        "optimization":     ["balance", "refactor", "balance", "refactor"],
        "verified":         [2, 1, 3, 0],
        "rejected":         [0, 1, 0, 0],
        "inconclusive":     [1, 0, 0, 2],
        "total":            [3, 2, 3, 2],
        "verification_rate":[0.67, 0.5, 1.0, 0.0],
        "rejection_rate":   [0.0, 0.5, 0.0, 0.0],
        "inconclusive_rate":[0.33, 0.0, 0.0, 1.0],
        "avg_combined_score":[0.9, 0.8, 1.0, 0.75],
    })


@pytest.fixture()
def topk_df():
    rows = []
    for bm in ["bA", "bB"]:
        for k in [1, 2, 3, 5]:
            rows.append({
                "benchmark": bm, "optimization": "balance", "k": k,
                "verified_at_k": None, "total_nodes": 4,
                "recovery_at_k": None, "mrr": None,
                "avg_score_at_1": 0.95 if bm == "bA" else 0.80,
            })
    return pd.DataFrame(rows)


@pytest.fixture()
def ablation_df():
    configs = ["baseline", "sim_heavy", "sup_heavy"]
    rows = []
    for cfg in configs:
        for bm in ["bA", "bB"]:
            rows.append({
                "config": cfg,
                "weights": "sim=0.5 sup=0.3 dep=0.2",
                "benchmark": bm,
                "optimization": "balance",
                "total_nodes": 4,
                "avg_rank1_score": 0.9,
                "rank1_consistency": 1.0 if cfg == "baseline" else 0.8,
                "rank1_precision": None,
                "mrr": None,
            })
    return pd.DataFrame(rows)


@pytest.fixture()
def region_summary_df():
    rows = []
    for bm in ["bA", "bB"]:
        for depth in [1, 2, 3]:
            rows.append({
                "benchmark": bm,
                "optimization": "balance",
                "depth": depth,
                "total_opt_nodes": 4,
                "avg_rank1_region_score": 0.95 if depth == 1 else 0.90,
                "avg_rank1_cone_sim": 0.9,
                "avg_rank1_cone_support": 1.0,
                "avg_rank1_cone_size_sim": 1.0,
                "pct_rank1_above_0_8": 1.0,
            })
    return pd.DataFrame(rows)


# ── Helper: patch _load and _save in research_plots ─────────────────────────

def _make_loader(data: dict):
    """Return a _load replacement that serves DataFrames by key."""
    def _load(key):
        return data.get(key, None)
    return _load


def _mock_save(fig, name):
    """Fake _save — close the figure, return a dummy path string."""
    import matplotlib.pyplot as _plt
    _plt.close(fig)
    return f"results/plots/{name}"


# ---------------------------------------------------------------------------
# TestExactMatchRate
# ---------------------------------------------------------------------------

class TestExactMatchRate:
    def _run(self, df):
        rp = _import_rp()
        with patch.object(rp, "_load", _make_loader({"summary": df})), \
             patch.object(rp, "_save", _mock_save):
            return rp.plot_exact_match_rate()

    def test_returns_png_path(self, summary_df):
        path = self._run(summary_df)
        assert path is not None
        assert path.endswith("exact_match_rate.png")

    def test_missing_file_returns_none(self):
        rp = _import_rp()
        with patch.object(rp, "_load", _make_loader({})):
            result = rp.plot_exact_match_rate()
        assert result is None

    def test_all_benchmarks_represented(self, summary_df):
        """Smoke: no exception with two benchmarks and two optimizations."""
        path = self._run(summary_df)
        assert path is not None

    def test_zero_original_nodes_no_crash(self):
        df = pd.DataFrame({
            "benchmark": ["bX"], "optimization": ["balance"],
            "original_nodes": [0], "optimized_nodes": [0],
            "original_levels": [0], "optimized_levels": [0],
            "exact_internal_matches": [0],
            "old_signatures_disappeared": [0], "new_signatures_appeared": [0],
            "avg_best_support_overlap": [1.0], "simulation_mode": ["exact"],
        })
        path = self._run(df)
        assert path is not None

    def test_single_benchmark(self):
        df = pd.DataFrame({
            "benchmark": ["solo"], "optimization": ["balance"],
            "original_nodes": [5], "optimized_nodes": [4],
            "original_levels": [3], "optimized_levels": [2],
            "exact_internal_matches": [4],
            "old_signatures_disappeared": [1], "new_signatures_appeared": [0],
            "avg_best_support_overlap": [1.0], "simulation_mode": ["exact"],
        })
        path = self._run(df)
        assert path is not None


# ---------------------------------------------------------------------------
# TestSupportOverlapDist
# ---------------------------------------------------------------------------

class TestSupportOverlapDist:
    def _run(self, df):
        rp = _import_rp()
        with patch.object(rp, "_load", _make_loader({"top_candidates": df})), \
             patch.object(rp, "_save", _mock_save):
            return rp.plot_support_overlap_dist()

    def test_returns_path(self, top_candidates_df):
        path = self._run(top_candidates_df)
        assert path is not None
        assert "support_overlap_dist" in path

    def test_missing_file_returns_none(self):
        rp = _import_rp()
        with patch.object(rp, "_load", _make_loader({})):
            assert rp.plot_support_overlap_dist() is None

    def test_no_rank1_rows_returns_none(self):
        df = pd.DataFrame({
            "benchmark": ["bA"], "optimization": ["balance"],
            "optimized_node": ["n1"], "rank": [2],
            "original_candidate": ["o1"], "combined_score": [0.7],
            "simulation_similarity": [0.8], "support_overlap": [0.5],
            "depth_similarity": [1.0], "optimized_level": [1], "original_level": [1],
        })
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            path = self._run(df)
        assert path is None

    def test_perfect_overlap_values(self, top_candidates_df):
        # All rank-1 rows have support_overlap=1.0 or 0.75/0.8 — just check it runs
        path = self._run(top_candidates_df)
        assert path is not None

    def test_single_rank1_row(self):
        df = pd.DataFrame({
            "benchmark": ["bA"], "optimization": ["balance"],
            "optimized_node": ["n1"], "rank": [1],
            "original_candidate": ["o1"], "combined_score": [1.0],
            "simulation_similarity": [1.0], "support_overlap": [0.9],
            "depth_similarity": [1.0], "optimized_level": [1], "original_level": [1],
        })
        path = self._run(df)
        assert path is not None


# ---------------------------------------------------------------------------
# TestNodeReduction
# ---------------------------------------------------------------------------

class TestNodeReduction:
    def _run(self, df):
        rp = _import_rp()
        with patch.object(rp, "_load", _make_loader({"summary": df})), \
             patch.object(rp, "_save", _mock_save):
            return rp.plot_node_reduction()

    def test_returns_path(self, summary_df):
        path = self._run(summary_df)
        assert path is not None
        assert "node_reduction" in path

    def test_missing_file_returns_none(self):
        rp = _import_rp()
        with patch.object(rp, "_load", _make_loader({})):
            assert rp.plot_node_reduction() is None

    def test_single_optimization(self):
        df = pd.DataFrame({
            "benchmark": ["bA", "bB"],
            "optimization": ["balance", "balance"],
            "original_nodes": [4, 6], "optimized_nodes": [3, 5],
            "original_levels": [3, 4], "optimized_levels": [2, 3],
            "exact_internal_matches": [3, 4],
            "old_signatures_disappeared": [1, 2], "new_signatures_appeared": [0, 1],
            "avg_best_support_overlap": [1.0, 0.9], "simulation_mode": ["exact", "exact"],
        })
        path = self._run(df)
        assert path is not None

    def test_no_node_reduction(self, summary_df):
        """Handles case where optimized == original."""
        df = summary_df.copy()
        df["optimized_nodes"] = df["original_nodes"]
        path = self._run(df)
        assert path is not None


# ---------------------------------------------------------------------------
# TestLevelReduction
# ---------------------------------------------------------------------------

class TestLevelReduction:
    def _run(self, df):
        rp = _import_rp()
        with patch.object(rp, "_load", _make_loader({"summary": df})), \
             patch.object(rp, "_save", _mock_save):
            return rp.plot_level_reduction()

    def test_returns_path(self, summary_df):
        path = self._run(summary_df)
        assert path is not None
        assert "level_reduction" in path

    def test_missing_file_returns_none(self):
        rp = _import_rp()
        with patch.object(rp, "_load", _make_loader({})):
            assert rp.plot_level_reduction() is None

    def test_five_optimizations(self):
        rows = []
        for opt in ["balance", "refactor", "resub", "resyn2_like", "rewrite"]:
            rows.append({
                "benchmark": "bA", "optimization": opt,
                "original_nodes": 4, "optimized_nodes": 3,
                "original_levels": 3, "optimized_levels": 2,
                "exact_internal_matches": 2, "old_signatures_disappeared": 2,
                "new_signatures_appeared": 1, "avg_best_support_overlap": 1.0,
                "simulation_mode": "exact",
            })
        path = self._run(pd.DataFrame(rows))
        assert path is not None


# ---------------------------------------------------------------------------
# TestSatStatus
# ---------------------------------------------------------------------------

class TestSatStatus:
    def _run(self, df):
        rp = _import_rp()
        with patch.object(rp, "_load", _make_loader({"sat_summary": df})), \
             patch.object(rp, "_save", _mock_save):
            return rp.plot_sat_status()

    def test_returns_path(self, sat_summary_df):
        path = self._run(sat_summary_df)
        assert path is not None
        assert "sat_status" in path

    def test_missing_file_returns_none(self):
        rp = _import_rp()
        with patch.object(rp, "_load", _make_loader({})):
            assert rp.plot_sat_status() is None

    def test_all_row_stripped(self, sat_summary_df):
        """ALL summary row must be stripped without error."""
        df = sat_summary_df.copy()
        df = pd.concat([df, pd.DataFrame([{
            "benchmark": "ALL", "optimization": "ALL",
            "verified": 6, "rejected": 1, "inconclusive": 3,
            "total": 10, "verification_rate": 0.6, "rejection_rate": 0.1,
            "inconclusive_rate": 0.3, "avg_combined_score": 0.88,
        }])], ignore_index=True)
        path = self._run(df)
        assert path is not None

    def test_all_verified(self):
        df = pd.DataFrame({
            "benchmark": ["bX"], "optimization": ["balance"],
            "verified": [5], "rejected": [0], "inconclusive": [0],
            "total": [5], "verification_rate": [1.0],
            "rejection_rate": [0.0], "inconclusive_rate": [0.0],
            "avg_combined_score": [1.0],
        })
        path = self._run(df)
        assert path is not None

    def test_all_rejected(self):
        df = pd.DataFrame({
            "benchmark": ["bX"], "optimization": ["balance"],
            "verified": [0], "rejected": [5], "inconclusive": [0],
            "total": [5], "verification_rate": [0.0],
            "rejection_rate": [1.0], "inconclusive_rate": [0.0],
            "avg_combined_score": [0.3],
        })
        path = self._run(df)
        assert path is not None


# ---------------------------------------------------------------------------
# TestTopkRecovery
# ---------------------------------------------------------------------------

class TestTopkRecovery:
    def _run(self, df):
        rp = _import_rp()
        with patch.object(rp, "_load", _make_loader({"topk_recovery": df})), \
             patch.object(rp, "_save", _mock_save):
            return rp.plot_topk_recovery()

    def test_returns_path(self, topk_df):
        path = self._run(topk_df)
        assert path is not None
        assert "topk_recovery" in path

    def test_missing_file_returns_none(self):
        rp = _import_rp()
        with patch.object(rp, "_load", _make_loader({})):
            assert rp.plot_topk_recovery() is None

    def test_no_k1_rows_returns_none(self, topk_df):
        df = topk_df[topk_df["k"] != 1].copy()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            path = self._run(df)
        assert path is None

    def test_multiple_optimizations_averaged(self):
        rows = []
        for bm in ["bA"]:
            for opt, score in [("balance", 1.0), ("refactor", 0.8)]:
                rows.append({
                    "benchmark": bm, "optimization": opt, "k": 1,
                    "verified_at_k": None, "total_nodes": 4,
                    "recovery_at_k": None, "mrr": None,
                    "avg_score_at_1": score,
                })
        path = self._run(pd.DataFrame(rows))
        assert path is not None

    def test_perfect_scores(self):
        df = pd.DataFrame({
            "benchmark": ["bA", "bB"], "optimization": ["balance", "balance"],
            "k": [1, 1], "verified_at_k": [None, None], "total_nodes": [4, 4],
            "recovery_at_k": [None, None], "mrr": [None, None],
            "avg_score_at_1": [1.0, 1.0],
        })
        path = self._run(df)
        assert path is not None


# ---------------------------------------------------------------------------
# TestAblationComparison
# ---------------------------------------------------------------------------

class TestAblationComparison:
    def _run(self, df):
        rp = _import_rp()
        with patch.object(rp, "_load", _make_loader({"ablation": df})), \
             patch.object(rp, "_save", _mock_save):
            return rp.plot_ablation_comparison()

    def test_returns_path(self, ablation_df):
        path = self._run(ablation_df)
        assert path is not None
        assert "ablation_comparison" in path

    def test_missing_file_returns_none(self):
        rp = _import_rp()
        with patch.object(rp, "_load", _make_loader({})):
            assert rp.plot_ablation_comparison() is None

    def test_missing_columns_returns_none(self):
        df = pd.DataFrame({"config": ["baseline"], "weights": ["w1"]})
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            path = self._run(df)
        assert path is None

    def test_mrr_column_used_when_present(self):
        df = pd.DataFrame({
            "config": ["baseline", "sim_heavy"],
            "weights": ["w", "w"],
            "benchmark": ["bA", "bA"],
            "optimization": ["balance", "balance"],
            "total_nodes": [4, 4],
            "avg_rank1_score": [0.9, 0.8],
            "rank1_consistency": [1.0, 0.9],
            "rank1_precision": [None, None],
            "mrr": [0.95, 0.85],
        })
        path = self._run(df)
        assert path is not None

    def test_mrr_all_nan_skipped(self):
        df = pd.DataFrame({
            "config": ["baseline"],
            "weights": ["w"],
            "benchmark": ["bA"],
            "optimization": ["balance"],
            "total_nodes": [4],
            "avg_rank1_score": [0.9],
            "rank1_consistency": [1.0],
            "rank1_precision": [None],
            "mrr": [float("nan")],
        })
        path = self._run(df)
        # Should still produce a plot (just without MRR bars)
        assert path is not None

    def test_single_config(self):
        df = pd.DataFrame({
            "config": ["baseline"],
            "weights": ["sim=0.55 sup=0.35 dep=0.10"],
            "benchmark": ["bA"],
            "optimization": ["balance"],
            "total_nodes": [4],
            "avg_rank1_score": [0.9],
            "rank1_consistency": [1.0],
            "rank1_precision": [None],
            "mrr": [None],
        })
        path = self._run(df)
        assert path is not None


# ---------------------------------------------------------------------------
# TestRegionScores
# ---------------------------------------------------------------------------

class TestRegionScores:
    def _run(self, df):
        rp = _import_rp()
        with patch.object(rp, "_load", _make_loader({"region_summary": df})), \
             patch.object(rp, "_save", _mock_save):
            return rp.plot_region_scores()

    def test_returns_path(self, region_summary_df):
        path = self._run(region_summary_df)
        assert path is not None
        assert "region_scores" in path

    def test_missing_file_returns_none(self):
        rp = _import_rp()
        with patch.object(rp, "_load", _make_loader({})):
            assert rp.plot_region_scores() is None

    def test_single_depth(self):
        df = pd.DataFrame({
            "benchmark": ["bA"], "optimization": ["balance"], "depth": [1],
            "total_opt_nodes": [4], "avg_rank1_region_score": [0.9],
            "avg_rank1_cone_sim": [0.9], "avg_rank1_cone_support": [1.0],
            "avg_rank1_cone_size_sim": [1.0], "pct_rank1_above_0_8": [1.0],
        })
        path = self._run(df)
        assert path is not None

    def test_three_depths_two_benchmarks(self, region_summary_df):
        path = self._run(region_summary_df)
        assert path is not None

    def test_multiple_optimizations_averaged(self):
        rows = []
        for opt in ["balance", "refactor"]:
            for depth in [1, 2, 3]:
                rows.append({
                    "benchmark": "bA", "optimization": opt, "depth": depth,
                    "total_opt_nodes": 4,
                    "avg_rank1_region_score": 0.9 if opt == "balance" else 0.85,
                    "avg_rank1_cone_sim": 0.9, "avg_rank1_cone_support": 1.0,
                    "avg_rank1_cone_size_sim": 1.0, "pct_rank1_above_0_8": 1.0,
                })
        path = self._run(pd.DataFrame(rows))
        assert path is not None


# ---------------------------------------------------------------------------
# TestRunAll
# ---------------------------------------------------------------------------

class TestRunAll:
    def test_run_all_returns_dict(self):
        rp = _import_rp()
        # All _load calls return None → all plots should be skipped gracefully
        with patch.object(rp, "_load", return_value=None), \
             patch.object(rp, "_ensure_plots_dir"):
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                results = rp.run_all()
        assert isinstance(results, dict)
        assert set(results.keys()) == {name for name, _ in rp.ALL_PLOTS}

    def test_run_all_all_none_when_no_files(self):
        rp = _import_rp()
        with patch.object(rp, "_load", return_value=None), \
             patch.object(rp, "_ensure_plots_dir"):
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                results = rp.run_all()
        assert all(v is None for v in results.values())

    def test_run_all_eight_entries(self):
        rp = _import_rp()
        with patch.object(rp, "_load", return_value=None), \
             patch.object(rp, "_ensure_plots_dir"):
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                results = rp.run_all()
        assert len(results) == 8

    def test_all_plots_list_has_eight_entries(self):
        rp = _import_rp()
        assert len(rp.ALL_PLOTS) == 8

    def test_all_plots_callables(self):
        rp = _import_rp()
        for name, fn in rp.ALL_PLOTS:
            assert callable(fn), f"{name} is not callable"
