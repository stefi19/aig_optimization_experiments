"""
tests/test_ablation_study.py
=============================
Unit tests for ablation_study.py.

Does NOT require any files on disk.  Tests cover: ScoringConfig, CONFIGS
constant, rerank_with_config, compute_group_metrics, rollup_by_config, and
build_markdown (graceful degradation).
"""

import os
import sys
import math

import pandas as pd
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from ablation_study import (
    ScoringConfig,
    CONFIGS,
    rerank_with_config,
    compute_group_metrics,
    rollup_by_config,
    build_markdown,
)
from evaluate_topk_recovery import build_verified_set


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _cand_df(rows=None):
    if rows is None:
        rows = [
            # node m1 — rank-1 orig=n1 (highest score under baseline)
            ("toy", "balance", "m1", "n1", 1, 0.95, 0.90, 0.80, 1.00),
            ("toy", "balance", "m1", "n2", 2, 0.75, 0.70, 0.60, 0.80),
            ("toy", "balance", "m1", "n3", 3, 0.55, 0.50, 0.40, 0.60),
            # node m2 — rank-1 orig=n2
            ("toy", "balance", "m2", "n2", 1, 0.88, 0.85, 0.70, 0.90),
            ("toy", "balance", "m2", "n1", 2, 0.72, 0.65, 0.60, 0.85),
            ("toy", "balance", "m2", "n3", 3, 0.50, 0.45, 0.50, 0.70),
        ]
    cols = [
        "benchmark", "optimization", "optimized_node", "original_candidate",
        "rank", "combined_score",
        "simulation_similarity", "support_overlap", "depth_similarity",
    ]
    return pd.DataFrame(rows, columns=cols)


def _verified_df(rows=None):
    if rows is None:
        rows = [
            ("toy", "balance", "m1", "n1", "verified"),
            ("toy", "balance", "m2", "n2", "verified"),
        ]
    cols = [
        "benchmark", "optimization", "optimized_node",
        "original_candidate", "sat_status",
    ]
    return pd.DataFrame(rows, columns=cols)


# ---------------------------------------------------------------------------
# ScoringConfig
# ---------------------------------------------------------------------------

class TestScoringConfig:

    def test_score_baseline_known_value(self):
        cfg = ScoringConfig("baseline", 0.55, 0.35, 0.10)
        expected = 0.55 * 1.0 + 0.35 * 0.8 + 0.10 * 0.9
        assert cfg.score(1.0, 0.8, 0.9) == pytest.approx(expected)

    def test_score_sim_only(self):
        cfg = ScoringConfig("sim_only", 1.0, 0.0, 0.0)
        assert cfg.score(0.75, 0.99, 0.99) == pytest.approx(0.75)

    def test_score_depth_only(self):
        cfg = ScoringConfig("depth_only", 0.0, 0.0, 1.0)
        assert cfg.score(0.0, 0.0, 0.42) == pytest.approx(0.42)

    def test_frozen_dataclass(self):
        cfg = ScoringConfig("baseline", 0.55, 0.35, 0.10)
        with pytest.raises((AttributeError, TypeError)):
            cfg.w_sim = 0.0  # type: ignore[misc]

    def test_label_includes_weights(self):
        cfg = ScoringConfig("baseline", 0.55, 0.35, 0.10)
        label = cfg.label()
        assert isinstance(label, str)
        assert "0.55" in label or "55" in label


# ---------------------------------------------------------------------------
# CONFIGS constant
# ---------------------------------------------------------------------------

class TestConfigs:

    def test_six_configs(self):
        assert len(CONFIGS) == 6

    def test_first_is_baseline(self):
        assert CONFIGS[0].name == "baseline"

    def test_all_names_unique(self):
        names = [c.name for c in CONFIGS]
        assert len(names) == len(set(names))

    def test_all_weights_nonneg(self):
        for cfg in CONFIGS:
            assert cfg.w_sim >= 0
            assert cfg.w_support >= 0
            assert cfg.w_depth >= 0

    def test_baseline_weights(self):
        baseline = next(c for c in CONFIGS if c.name == "baseline")
        assert baseline.w_sim == pytest.approx(0.55)
        assert baseline.w_support == pytest.approx(0.35)
        assert baseline.w_depth == pytest.approx(0.10)


# ---------------------------------------------------------------------------
# rerank_with_config
# ---------------------------------------------------------------------------

class TestRerankWithConfig:

    def test_adds_new_score_column(self):
        df = _cand_df()
        cfg = CONFIGS[0]  # baseline
        result = rerank_with_config(df, cfg)
        assert "new_score" in result.columns

    def test_adds_new_rank_column(self):
        df = _cand_df()
        result = rerank_with_config(df, CONFIGS[0])
        assert "new_rank" in result.columns

    def test_rank_1_has_highest_score_per_group(self):
        df = _cand_df()
        result = rerank_with_config(df, CONFIGS[0])
        for _, grp in result.groupby(["benchmark", "optimization", "optimized_node"]):
            rank1_score = grp.loc[grp["new_rank"] == 1, "new_score"].iloc[0]
            assert rank1_score == grp["new_score"].max()

    def test_sim_only_ranks_by_sim(self):
        cfg = ScoringConfig("sim_only", 1.0, 0.0, 0.0)
        df = _cand_df()
        result = rerank_with_config(df, cfg)
        for _, grp in result.groupby(["benchmark", "optimization", "optimized_node"]):
            top = grp[grp["new_rank"] == 1].iloc[0]
            assert top["simulation_similarity"] == grp["simulation_similarity"].max()

    def test_does_not_mutate_input(self):
        df = _cand_df()
        original_columns = set(df.columns)
        rerank_with_config(df, CONFIGS[0])
        assert set(df.columns) == original_columns


# ---------------------------------------------------------------------------
# compute_group_metrics
# ---------------------------------------------------------------------------

class TestComputeGroupMetrics:

    def _setup(self):
        cands = _cand_df()
        verified = build_verified_set(_verified_df())
        baseline_cfg = CONFIGS[0]
        group = cands[
            (cands["benchmark"] == "toy") & (cands["optimization"] == "balance")
        ].copy()
        reranked = rerank_with_config(group, baseline_cfg)
        baseline_rank1 = {}
        for node, sub in reranked.groupby("optimized_node"):
            rank1_row = sub[sub["new_rank"] == 1].iloc[0]
            baseline_rank1[node] = rank1_row["original_candidate"]
        # Return the reranked group (compute_group_metrics expects new_rank col)
        return reranked, baseline_rank1, verified

    def test_returns_dict(self):
        grp, br1, vs = self._setup()
        result = compute_group_metrics(grp, br1, vs, "toy", "balance")
        assert isinstance(result, dict)

    def test_baseline_consistency_is_1(self):
        # When using the same config as baseline, rank-1 should always match
        grp, br1, vs = self._setup()
        result = compute_group_metrics(grp, br1, vs, "toy", "balance")
        assert result["rank1_consistency"] == pytest.approx(1.0)

    def test_rank1_precision_with_all_verified(self):
        # Both m1 rank-1=n1 and m2 rank-1=n2 are verified
        grp, br1, vs = self._setup()
        result = compute_group_metrics(grp, br1, vs, "toy", "balance")
        assert result["rank1_precision"] == pytest.approx(1.0)

    def test_rank1_precision_no_verified_set(self):
        grp, br1, _ = self._setup()
        result = compute_group_metrics(grp, br1, None, "toy", "balance")
        assert math.isnan(result["rank1_precision"])

    def test_avg_rank1_score_nonneg(self):
        grp, br1, vs = self._setup()
        result = compute_group_metrics(grp, br1, vs, "toy", "balance")
        assert result["avg_rank1_score"] >= 0.0

    def test_total_nodes_correct(self):
        grp, br1, vs = self._setup()
        result = compute_group_metrics(grp, br1, vs, "toy", "balance")
        assert result["total_nodes"] == 2  # m1, m2

    def test_mrr_all_rank1_gives_1(self):
        # When verified candidates are all at rank 1, MRR = 1.0
        grp, br1, vs = self._setup()
        result = compute_group_metrics(grp, br1, vs, "toy", "balance")
        assert result["mrr"] == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# rollup_by_config
# ---------------------------------------------------------------------------

class TestRollupByConfig:

    def _ablation_df(self):
        """Minimal per-group ablation DataFrame (includes 'weights' column)."""
        rows = []
        for cfg in CONFIGS:
            rows.append({
                "config": cfg.name,
                "weights": cfg.label(),
                "benchmark": "toy",
                "optimization": "balance",
                "total_nodes": 2,
                "avg_rank1_score": 0.9,
                "rank1_consistency": 1.0 if cfg.name == "baseline" else 0.5,
                "rank1_precision": 1.0,
                "mrr": 1.0,
            })
        return pd.DataFrame(rows)

    def test_returns_dataframe(self):
        result = rollup_by_config(self._ablation_df())
        assert isinstance(result, pd.DataFrame)

    def test_one_row_per_config(self):
        result = rollup_by_config(self._ablation_df())
        assert len(result) == len(CONFIGS)

    def test_config_order_preserved(self):
        result = rollup_by_config(self._ablation_df())
        for i, cfg in enumerate(CONFIGS):
            assert result.iloc[i]["config"] == cfg.name

    def test_required_columns_present(self):
        result = rollup_by_config(self._ablation_df())
        for col in ("config", "avg_rank1_score", "rank1_consistency",
                    "rank1_precision", "mrr"):
            assert col in result.columns

    def test_baseline_consistency_is_1(self):
        result = rollup_by_config(self._ablation_df())
        baseline_row = result[result["config"] == "baseline"].iloc[0]
        assert baseline_row["rank1_consistency"] == pytest.approx(1.0)

    def test_empty_df_returns_empty(self):
        empty = pd.DataFrame(columns=["config", "weights", "benchmark", "optimization",
                                      "total_nodes", "avg_rank1_score",
                                      "rank1_consistency", "rank1_precision", "mrr"])
        result = rollup_by_config(empty)
        assert result.empty


# ---------------------------------------------------------------------------
# build_markdown
# ---------------------------------------------------------------------------

class TestBuildMarkdown:

    def _tables(self):
        adf = pd.DataFrame([{
            "config": c.name, "weights": c.label(), "benchmark": "toy",
            "optimization": "balance", "total_nodes": 2, "avg_rank1_score": 0.9,
            "rank1_consistency": 1.0, "rank1_precision": 1.0, "mrr": 1.0,
        } for c in CONFIGS])
        rdf = rollup_by_config(adf)
        return adf, rdf

    def test_returns_string(self):
        adf, rdf = self._tables()
        md = build_markdown(adf, rdf, True, True)
        assert isinstance(md, str) and len(md) > 0

    def test_contains_baseline(self):
        adf, rdf = self._tables()
        md = build_markdown(adf, rdf, True, True)
        assert "baseline" in md

    def test_contains_rollup_section(self):
        adf, rdf = self._tables()
        md = build_markdown(adf, rdf, True, True)
        assert "Global summary" in md or "global summary" in md

    def test_missing_candidates_note(self):
        empty = pd.DataFrame()
        md = build_markdown(empty, empty, False, False)
        assert "missing" in md.lower() or "top_candidates" in md.lower()

    def test_missing_sat_note(self):
        adf, rdf = self._tables()
        md = build_markdown(adf, rdf, True, False)
        assert "n/a" in md or "sat" in md.lower() or "missing" in md.lower()

    def test_empty_does_not_crash(self):
        empty = pd.DataFrame(columns=["config", "weights", "benchmark", "optimization",
                                      "total_nodes", "avg_rank1_score",
                                      "rank1_consistency", "rank1_precision", "mrr"])
        md = build_markdown(empty, empty, True, False)
        assert isinstance(md, str)
