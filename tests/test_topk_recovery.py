"""
tests/test_topk_recovery.py
============================
Unit tests for evaluate_topk_recovery.py.

Does NOT require any files on disk; SAT results are provided as in-memory
DataFrames.  Tests cover: build_verified_set, compute_recovery_for_group,
compute_topk_table, build_markdown (graceful degradation), and the
no-SAT-data path.
"""

import os
import sys
import math

import pandas as pd
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from evaluate_topk_recovery import (
    build_verified_set,
    compute_recovery_for_group,
    compute_topk_table,
    build_markdown,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _cand_df(rows):
    """Build a top_candidates-style DataFrame."""
    cols = [
        "benchmark", "optimization", "optimized_node",
        "original_candidate", "rank", "combined_score",
    ]
    return pd.DataFrame(rows, columns=cols)


def _verified_df(rows):
    """Build a sat_verified_candidates-style DataFrame."""
    cols = [
        "benchmark", "optimization", "optimized_node",
        "original_candidate", "sat_status",
    ]
    return pd.DataFrame(rows, columns=cols)


# Three optimized nodes, ranks 1-3 against three original candidates.
CANDS = _cand_df([
    # node m1: rank-1 orig=n1 (will be verified), rank-2 orig=n2, rank-3 orig=n3
    ("toy", "balance", "m1", "n1", 1, 0.95),
    ("toy", "balance", "m1", "n2", 2, 0.80),
    ("toy", "balance", "m1", "n3", 3, 0.60),
    # node m2: rank-1 orig=n2 (will be verified)
    ("toy", "balance", "m2", "n2", 1, 0.90),
    ("toy", "balance", "m2", "n1", 2, 0.70),
    ("toy", "balance", "m2", "n3", 3, 0.50),
    # node m3: rank-1 orig=n3 (NOT verified — rank-2 n1 is verified)
    ("toy", "balance", "m3", "n3", 1, 0.85),
    ("toy", "balance", "m3", "n1", 2, 0.75),
    ("toy", "balance", "m3", "n2", 3, 0.65),
])

VERIFIED = _verified_df([
    ("toy", "balance", "m1", "n1", "verified"),
    ("toy", "balance", "m2", "n2", "verified"),
    ("toy", "balance", "m3", "n1", "verified"),   # rank-2 for m3
    ("toy", "balance", "m1", "n2", "rejected"),   # rejected, should not count
])


# ---------------------------------------------------------------------------
# build_verified_set
# ---------------------------------------------------------------------------

class TestBuildVerifiedSet:

    def test_returns_set(self):
        s = build_verified_set(VERIFIED)
        assert isinstance(s, set)

    def test_includes_verified(self):
        s = build_verified_set(VERIFIED)
        assert ("toy", "balance", "m1", "n1") in s
        assert ("toy", "balance", "m2", "n2") in s
        assert ("toy", "balance", "m3", "n1") in s

    def test_excludes_rejected(self):
        s = build_verified_set(VERIFIED)
        assert ("toy", "balance", "m1", "n2") not in s

    def test_empty_df_gives_empty_set(self):
        empty = _verified_df([])
        assert build_verified_set(empty) == set()

    def test_all_inconclusive_gives_empty_set(self):
        df = _verified_df([
            ("toy", "balance", "m1", "n1", "inconclusive"),
        ])
        assert build_verified_set(df) == set()


# ---------------------------------------------------------------------------
# compute_recovery_for_group
# ---------------------------------------------------------------------------

class TestComputeRecoveryForGroup:

    def _group(self):
        return CANDS[CANDS["optimization"] == "balance"].copy()

    def _verified_set(self):
        return build_verified_set(VERIFIED)

    def test_verified_at_1_correct(self):
        # m1 rank-1 verified, m2 rank-1 verified, m3 rank-1 NOT verified → 2
        result = compute_recovery_for_group(self._group(), self._verified_set(), k=1)
        assert result["verified_at_k"] == 2

    def test_verified_at_2_includes_m3(self):
        # m3's verified candidate (n1) is at rank 2 → all 3 recovered at K=2
        result = compute_recovery_for_group(self._group(), self._verified_set(), k=2)
        assert result["verified_at_k"] == 3

    def test_total_nodes_correct(self):
        result = compute_recovery_for_group(self._group(), self._verified_set(), k=1)
        assert result["total_nodes"] == 3

    def test_recovery_at_k1(self):
        result = compute_recovery_for_group(self._group(), self._verified_set(), k=1)
        assert result["recovery_at_k"] == pytest.approx(2 / 3)

    def test_recovery_at_k2(self):
        result = compute_recovery_for_group(self._group(), self._verified_set(), k=2)
        assert result["recovery_at_k"] == pytest.approx(1.0)

    def test_mrr_correct(self):
        # m1: verified at rank 1 → rr=1.0
        # m2: verified at rank 1 → rr=1.0
        # m3: verified at rank 2 → rr=0.5
        # MRR = (1.0 + 1.0 + 0.5) / 3 = 0.833...
        result = compute_recovery_for_group(self._group(), self._verified_set(), k=5)
        assert result["mrr"] == pytest.approx(2.5 / 3, rel=1e-4)

    def test_avg_score_at_1(self):
        result = compute_recovery_for_group(self._group(), self._verified_set(), k=1)
        # rank-1 scores: m1=0.95, m2=0.90, m3=0.85 → mean=0.90
        assert result["avg_score_at_1"] == pytest.approx(0.90, rel=1e-4)

    def test_no_verified_set_returns_nan(self):
        result = compute_recovery_for_group(self._group(), None, k=1)
        assert math.isnan(result["verified_at_k"])
        assert math.isnan(result["recovery_at_k"])
        assert math.isnan(result["mrr"])

    def test_no_verified_set_still_computes_score(self):
        result = compute_recovery_for_group(self._group(), None, k=1)
        assert not math.isnan(result["avg_score_at_1"])

    def test_empty_group_returns_nan_score(self):
        # An empty group has no rank-1 rows → avg_score_at_1 is NaN.
        # Pass verified_set=None to avoid iloc[0] on empty benchmark col.
        empty = CANDS.iloc[:0].copy()
        result = compute_recovery_for_group(empty, None, k=1)
        assert math.isnan(result["avg_score_at_1"])


# ---------------------------------------------------------------------------
# compute_topk_table
# ---------------------------------------------------------------------------

class TestComputeTopkTable:

    def test_returns_dataframe(self):
        result = compute_topk_table(CANDS, build_verified_set(VERIFIED), [1, 2])
        assert isinstance(result, pd.DataFrame)

    def test_rows_per_k(self):
        # One (benchmark, optimization) pair × 2 k values = 2 rows
        result = compute_topk_table(CANDS, build_verified_set(VERIFIED), [1, 2])
        assert len(result) == 2

    def test_k_column_values(self):
        result = compute_topk_table(CANDS, build_verified_set(VERIFIED), [1, 2, 5])
        assert set(result["k"]) == {1, 2, 5}

    def test_required_columns_present(self):
        result = compute_topk_table(CANDS, None, [1])
        for col in ("benchmark", "optimization", "k",
                    "verified_at_k", "total_nodes", "recovery_at_k",
                    "mrr", "avg_score_at_1"):
            assert col in result.columns

    def test_empty_candidates_returns_empty(self):
        result = compute_topk_table(CANDS.iloc[:0], None, [1])
        assert result.empty

    def test_multiple_groups(self):
        # Add a second (benchmark, optimization) pair
        extra = _cand_df([
            ("other_bench", "rewrite", "x1", "y1", 1, 0.88),
            ("other_bench", "rewrite", "x2", "y2", 1, 0.77),
        ])
        combined = pd.concat([CANDS, extra], ignore_index=True)
        result = compute_topk_table(combined, None, [1, 3])
        # 2 groups × 2 k values = 4 rows
        assert len(result) == 4


# ---------------------------------------------------------------------------
# build_markdown
# ---------------------------------------------------------------------------

class TestBuildMarkdown:

    def _table(self):
        return compute_topk_table(CANDS, build_verified_set(VERIFIED), [1, 2, 3, 5])

    def test_returns_string(self):
        md = build_markdown(self._table(), True, True)
        assert isinstance(md, str) and len(md) > 0

    def test_contains_k1_section(self):
        md = build_markdown(self._table(), True, True)
        assert "K=1" in md

    def test_contains_interpretation_section(self):
        md = build_markdown(self._table(), True, True)
        assert "Interpretation" in md

    def test_missing_candidates_note(self):
        md = build_markdown(pd.DataFrame(), False, False)
        assert "top_candidates" in md.lower() or "missing" in md.lower()

    def test_missing_sat_note(self):
        table = compute_topk_table(CANDS, None, [1])
        md = build_markdown(table, True, False)
        assert "n/a" in md or "missing" in md.lower() or "sat" in md.lower()

    def test_data_availability_section(self):
        md = build_markdown(self._table(), True, True)
        assert "Data availability" in md or "availability" in md.lower()

    def test_empty_table_does_not_crash(self):
        empty = pd.DataFrame(columns=[
            "benchmark", "optimization", "k", "verified_at_k",
            "total_nodes", "recovery_at_k", "mrr", "avg_score_at_1",
        ])
        md = build_markdown(empty, True, False)
        assert isinstance(md, str)
