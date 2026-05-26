"""
tests/test_cegar_refinement.py
================================
Unit tests for counterexample_guided_refinement.py.

All tests use in-memory DataFrames — no CSV files on disk are required.

Fixture topology
----------------
Benchmark "toy", optimization "balance", 2 optimised nodes: m1, m2.
Each has 3 candidates (original nodes n1, n2, n3) with hand-crafted scores.

  m1 candidates (by rank):   n1 score=0.90, n2 score=0.70, n3 score=0.50
  m2 candidates (by rank):   n2 score=0.85, n1 score=0.60, n3 score=0.40

SAT verdict: (m1, n1) → rejected.
Expected CEGAR behaviour:
  - m1/n2 and m1/n3 get penalised (feature-similar to rejected m1/n1)
  - m2 candidates are unaffected (different node, no rejection for m2)
"""

import os
import sys
import math

import pandas as pd
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from counterexample_guided_refinement import (
    build_rejection_index,
    feature_sim,
    compute_penalty,
    refine,
    compute_summary,
    build_markdown,
    FEATURE_COLS,
    REJECTION_WEIGHT,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _cand_df():
    rows = [
        # m1 candidates
        {"benchmark": "toy", "optimization": "balance",
         "optimized_node": "m1", "rank": 1, "original_candidate": "n1",
         "combined_score": 0.90,
         "simulation_similarity": 0.95, "support_overlap": 0.90, "depth_similarity": 1.00,
         "optimized_level": 2, "original_level": 2},
        {"benchmark": "toy", "optimization": "balance",
         "optimized_node": "m1", "rank": 2, "original_candidate": "n2",
         "combined_score": 0.70,
         "simulation_similarity": 0.80, "support_overlap": 0.70, "depth_similarity": 0.80,
         "optimized_level": 2, "original_level": 2},
        {"benchmark": "toy", "optimization": "balance",
         "optimized_node": "m1", "rank": 3, "original_candidate": "n3",
         "combined_score": 0.50,
         "simulation_similarity": 0.30, "support_overlap": 0.20, "depth_similarity": 0.50,
         "optimized_level": 2, "original_level": 3},
        # m2 candidates (no rejection for m2)
        {"benchmark": "toy", "optimization": "balance",
         "optimized_node": "m2", "rank": 1, "original_candidate": "n2",
         "combined_score": 0.85,
         "simulation_similarity": 0.88, "support_overlap": 0.80, "depth_similarity": 0.90,
         "optimized_level": 1, "original_level": 1},
        {"benchmark": "toy", "optimization": "balance",
         "optimized_node": "m2", "rank": 2, "original_candidate": "n1",
         "combined_score": 0.60,
         "simulation_similarity": 0.65, "support_overlap": 0.55, "depth_similarity": 0.70,
         "optimized_level": 1, "original_level": 1},
        {"benchmark": "toy", "optimization": "balance",
         "optimized_node": "m2", "rank": 3, "original_candidate": "n3",
         "combined_score": 0.40,
         "simulation_similarity": 0.40, "support_overlap": 0.35, "depth_similarity": 0.50,
         "optimized_level": 1, "original_level": 2},
    ]
    return pd.DataFrame(rows)


def _sat_df_with_rejection():
    """SAT results: m1/n1 rejected, m2/n2 verified."""
    return pd.DataFrame([
        {"benchmark": "toy", "optimization": "balance",
         "optimized_node": "m1", "original_candidate": "n1",
         "combined_score": 0.90, "sat_status": "rejected",
         "abc_result": "Networks are NOT EQUIVALENT.", "notes": ""},
        {"benchmark": "toy", "optimization": "balance",
         "optimized_node": "m2", "original_candidate": "n2",
         "combined_score": 0.85, "sat_status": "verified",
         "abc_result": "Networks are equivalent.", "notes": ""},
    ])


def _sat_df_no_rejection():
    """SAT results: all verified."""
    return pd.DataFrame([
        {"benchmark": "toy", "optimization": "balance",
         "optimized_node": "m1", "original_candidate": "n1",
         "combined_score": 0.90, "sat_status": "verified",
         "abc_result": "Networks are equivalent.", "notes": ""},
    ])


# ---------------------------------------------------------------------------
# feature_sim
# ---------------------------------------------------------------------------

class TestFeatureSim:

    def test_identical_vectors_give_1(self):
        v = {"simulation_similarity": 0.8, "support_overlap": 0.6, "depth_similarity": 0.9}
        assert feature_sim(v, v) == pytest.approx(1.0)

    def test_maximally_different_give_0(self):
        v_a = {"simulation_similarity": 1.0, "support_overlap": 1.0, "depth_similarity": 1.0}
        v_b = {"simulation_similarity": 0.0, "support_overlap": 0.0, "depth_similarity": 0.0}
        assert feature_sim(v_a, v_b) == pytest.approx(0.0)

    def test_half_distance(self):
        # L1 = 0.5+0.5+0.5 = 1.5; sim = 1 - 1.5/3 = 0.5
        v_a = {"simulation_similarity": 1.0, "support_overlap": 1.0, "depth_similarity": 1.0}
        v_b = {"simulation_similarity": 0.5, "support_overlap": 0.5, "depth_similarity": 0.5}
        assert feature_sim(v_a, v_b) == pytest.approx(0.5)

    def test_symmetric(self):
        v_a = {"simulation_similarity": 0.7, "support_overlap": 0.4, "depth_similarity": 0.9}
        v_b = {"simulation_similarity": 0.2, "support_overlap": 0.8, "depth_similarity": 0.5}
        assert feature_sim(v_a, v_b) == pytest.approx(feature_sim(v_b, v_a))

    def test_result_in_unit_interval(self):
        for s in [0.0, 0.3, 0.7, 1.0]:
            v_a = {c: s  for c in FEATURE_COLS}
            v_b = {c: 1.0 for c in FEATURE_COLS}
            assert 0.0 <= feature_sim(v_a, v_b) <= 1.0


# ---------------------------------------------------------------------------
# compute_penalty
# ---------------------------------------------------------------------------

class TestComputePenalty:

    def _v(self, s=0.9, sup=0.8, d=1.0):
        return {"simulation_similarity": s, "support_overlap": sup, "depth_similarity": d}

    def test_no_rejections_gives_zero(self):
        assert compute_penalty(self._v(), []) == pytest.approx(0.0)

    def test_identical_rejection_gives_rejection_weight(self):
        v = self._v()
        penalty = compute_penalty(v, [v])
        assert penalty == pytest.approx(REJECTION_WEIGHT * 1.0)

    def test_uses_max_not_sum(self):
        # Two rejections: one identical, one maximally different
        v     = self._v(1.0, 1.0, 1.0)
        rej1  = {c: 1.0 for c in FEATURE_COLS}   # identical → sim = 1.0
        rej2  = {c: 0.0 for c in FEATURE_COLS}   # opposite  → sim = 0.0
        penalty = compute_penalty(v, [rej1, rej2])
        # max(1.0, 0.0) = 1.0
        assert penalty == pytest.approx(REJECTION_WEIGHT * 1.0)

    def test_dissimilar_rejection_small_penalty(self):
        v_cand = {c: 1.0 for c in FEATURE_COLS}
        v_rej  = {c: 0.0 for c in FEATURE_COLS}  # maximally different
        penalty = compute_penalty(v_cand, [v_rej])
        assert penalty == pytest.approx(0.0)

    def test_penalty_bounded_by_rejection_weight(self):
        v = self._v()
        penalty = compute_penalty(v, [v, v, v])
        assert penalty <= REJECTION_WEIGHT


# ---------------------------------------------------------------------------
# build_rejection_index
# ---------------------------------------------------------------------------

class TestBuildRejectionIndex:

    def test_returns_dict(self):
        idx = build_rejection_index(_cand_df(), _sat_df_with_rejection())
        assert isinstance(idx, dict)

    def test_rejected_node_in_index(self):
        idx = build_rejection_index(_cand_df(), _sat_df_with_rejection())
        assert ("toy", "balance", "m1") in idx

    def test_verified_node_not_in_index(self):
        idx = build_rejection_index(_cand_df(), _sat_df_with_rejection())
        # m2/n2 was verified, not rejected
        assert ("toy", "balance", "m2") not in idx

    def test_no_sat_df_returns_empty(self):
        assert build_rejection_index(_cand_df(), None) == {}

    def test_no_rejections_returns_empty(self):
        idx = build_rejection_index(_cand_df(), _sat_df_no_rejection())
        assert idx == {}

    def test_feature_vectors_have_correct_keys(self):
        idx = build_rejection_index(_cand_df(), _sat_df_with_rejection())
        vecs = idx[("toy", "balance", "m1")]
        assert len(vecs) == 1
        for key in FEATURE_COLS:
            assert key in vecs[0]


# ---------------------------------------------------------------------------
# refine
# ---------------------------------------------------------------------------

class TestRefine:

    def _do_refine(self):
        cands = _cand_df()
        sat   = _sat_df_with_rejection()
        idx   = build_rejection_index(cands, sat)
        return refine(cands, idx, sat)

    def test_returns_dataframe(self):
        assert isinstance(self._do_refine(), pd.DataFrame)

    def test_same_row_count(self):
        result = self._do_refine()
        assert len(result) == len(_cand_df())

    def test_adds_required_columns(self):
        result = self._do_refine()
        for col in ("penalty", "refined_score", "cegar_rank", "rank_change", "is_rejected_pair"):
            assert col in result.columns

    def test_rejected_pair_flagged(self):
        result = self._do_refine()
        rej = result[
            (result["optimized_node"] == "m1") & (result["original_candidate"] == "n1")
        ]
        assert rej.iloc[0]["is_rejected_pair"] is True or rej.iloc[0]["is_rejected_pair"] == True

    def test_non_rejected_pair_not_flagged(self):
        result = self._do_refine()
        row = result[
            (result["optimized_node"] == "m2") & (result["original_candidate"] == "n1")
        ]
        assert not row.iloc[0]["is_rejected_pair"]

    def test_m2_has_zero_penalty(self):
        result = self._do_refine()
        m2_rows = result[result["optimized_node"] == "m2"]
        assert (m2_rows["penalty"] == 0.0).all()

    def test_m1_n1_has_nonzero_penalty(self):
        # n1 is identical to the rejected vector → should get REJECTION_WEIGHT penalty
        result = self._do_refine()
        row = result[
            (result["optimized_node"] == "m1") & (result["original_candidate"] == "n1")
        ]
        assert row.iloc[0]["penalty"] == pytest.approx(REJECTION_WEIGHT, rel=1e-3)

    def test_refined_score_nonneg(self):
        result = self._do_refine()
        assert (result["refined_score"] >= 0.0).all()

    def test_refined_score_equals_original_when_no_penalty(self):
        cands = _cand_df()
        result = refine(cands, {}, None)
        assert (result["refined_score"] == result["combined_score"]).all()

    def test_cegar_rank_1_per_node(self):
        result = self._do_refine()
        for _, group in result.groupby(["benchmark", "optimization", "optimized_node"]):
            assert 1 in group["cegar_rank"].values

    def test_rank_change_zero_without_rejections(self):
        cands = _cand_df()
        result = refine(cands, {}, None)
        assert (result["rank_change"] == 0).all()


# ---------------------------------------------------------------------------
# compute_summary
# ---------------------------------------------------------------------------

class TestComputeSummary:

    def _refined(self):
        cands = _cand_df()
        sat   = _sat_df_with_rejection()
        idx   = build_rejection_index(cands, sat)
        return refine(cands, idx, sat)

    def test_returns_list(self):
        result = compute_summary(self._refined())
        assert isinstance(result, list)

    def test_one_row_per_bench_opt(self):
        result = compute_summary(self._refined())
        keys = {(r["benchmark"], r["optimization"]) for r in result}
        assert len(result) == len(keys)

    def test_required_columns_present(self):
        result = compute_summary(self._refined())
        for col in ("benchmark", "optimization", "total_nodes",
                    "nodes_with_penalty", "nodes_rank1_changed",
                    "avg_refined_rank1", "avg_original_rank1",
                    "avg_penalty_rank1", "n_rejected_pairs"):
            assert col in result[0], f"missing column: {col}"

    def test_total_nodes_correct(self):
        result = compute_summary(self._refined())
        assert result[0]["total_nodes"] == 2   # m1 and m2

    def test_n_rejected_pairs_correct(self):
        result = compute_summary(self._refined())
        assert result[0]["n_rejected_pairs"] == 1   # only m1/n1

    def test_nodes_with_penalty_at_least_1(self):
        result = compute_summary(self._refined())
        assert result[0]["nodes_with_penalty"] >= 1

    def test_empty_df_returns_empty(self):
        empty = _cand_df().iloc[:0].copy()
        for col in ("penalty", "refined_score", "cegar_rank",
                    "rank_change", "is_rejected_pair"):
            empty[col] = []
        result = compute_summary(empty)
        assert result == []


# ---------------------------------------------------------------------------
# build_markdown
# ---------------------------------------------------------------------------

class TestBuildMarkdown:

    def _summary(self):
        cands = _cand_df()
        sat   = _sat_df_with_rejection()
        idx   = build_rejection_index(cands, sat)
        refined = refine(cands, idx, sat)
        return compute_summary(refined), refined

    def test_returns_string(self):
        summary, refined = self._summary()
        md = build_markdown(summary, refined, True, True, 1)
        assert isinstance(md, str) and len(md) > 0

    def test_contains_prototype_notice(self):
        summary, refined = self._summary()
        md = build_markdown(summary, refined, True, True, 1)
        assert "Prototype" in md or "prototype" in md

    def test_contains_configuration_section(self):
        summary, refined = self._summary()
        md = build_markdown(summary, refined, True, True, 1)
        assert "Configuration" in md

    def test_contains_interpretation_section(self):
        summary, refined = self._summary()
        md = build_markdown(summary, refined, True, True, 1)
        assert "Interpretation" in md

    def test_missing_candidates_note(self):
        md = build_markdown([], None, False, False, 0)
        assert "top_candidates" in md.lower() or "missing" in md.lower()

    def test_no_sat_note(self):
        summary, refined = self._summary()
        md = build_markdown(summary, refined, True, False, 0)
        assert "zero" in md.lower() or "no rejected" in md.lower() or "sat" in md.lower()

    def test_rejection_count_shown(self):
        summary, refined = self._summary()
        md = build_markdown(summary, refined, True, True, 1)
        assert "1" in md   # the rejection count appears somewhere

    def test_global_rollup_section(self):
        summary, refined = self._summary()
        md = build_markdown(summary, refined, True, True, 1)
        assert "rollup" in md.lower() or "Global" in md

    def test_empty_summary_does_not_crash(self):
        empty_refined = _cand_df().iloc[:0].copy()
        md = build_markdown([], empty_refined, True, True, 0)
        assert isinstance(md, str)
