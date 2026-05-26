"""
tests/test_select_sat_candidates.py

Unit tests for select_sat_candidates.py:
  - filter_for_sat: rank / score filtering
  - annotate: adds BLIF path columns
  - load_candidates: FileNotFoundError on missing file
  - benchmark discovery: benchmarks/real/**/*.blif is picked up
"""

import os
import sys
import tempfile
import textwrap
from pathlib import Path

import pandas as pd
import pytest

# ── Import helper ─────────────────────────────────────────────────────────────

_REPO_ROOT = Path(__file__).parent.parent

def _import_ssc():
    """Import select_sat_candidates as a module (add repo root to sys.path)."""
    if str(_REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(_REPO_ROOT))
    import importlib
    import select_sat_candidates
    importlib.reload(select_sat_candidates)
    return select_sat_candidates


# ── Fixtures ──────────────────────────────────────────────────────────────────

def _make_df(**overrides):
    base = {
        "benchmark": ["b1", "b1", "b2"],
        "optimization": ["balance", "rewrite", "balance"],
        "orig_node": ["n1", "n2", "n3"],
        "opt_node": ["x1", "x2", "x3"],
        "combined_score": [0.90, 0.70, 0.88],
        "rank": [1, 2, 1],
        "is_exact_signature_match": [0, 0, 0],
        "match_category": ["non_exact_candidate", "non_exact_candidate", "non_exact_candidate"],
    }
    base.update(overrides)
    return pd.DataFrame(base)


def _make_df_with_exact(**overrides):
    """DataFrame that has a mix of exact and non-exact candidates (all rank-1, high score)."""
    base = {
        "benchmark": ["b1", "b1", "b2"],
        "optimization": ["balance", "balance", "balance"],
        "orig_node": ["n1", "n2", "n3"],
        "opt_node": ["x1", "x2", "x3"],
        "combined_score": [0.92, 0.91, 0.90],
        "rank": [1, 1, 1],
        "is_exact_signature_match": [1, 0, 1],   # b1/n1 and b2/n3 are exact
        "match_category": ["exact_anchor", "non_exact_candidate", "exact_anchor"],
    }
    base.update(overrides)
    return pd.DataFrame(base)


# ── Tests: filter_for_sat ─────────────────────────────────────────────────────

class TestFilterForSat:
    def test_keeps_only_rank1_by_default(self):
        ssc = _import_ssc()
        df = _make_df()
        out = ssc.filter_for_sat(df)
        assert all(out["rank"] == 1)

    def test_keeps_only_high_score(self):
        ssc = _import_ssc()
        df = _make_df()
        out = ssc.filter_for_sat(df)
        assert all(out["combined_score"] >= ssc.SAT_SCORE_THRESHOLD)

    def test_empty_result_below_threshold(self):
        ssc = _import_ssc()
        df = _make_df(combined_score=[0.50, 0.60, 0.55], rank=[1, 1, 1])
        out = ssc.filter_for_sat(df)
        assert out.empty

    def test_no_rank_column_still_filters_by_score(self):
        ssc = _import_ssc()
        df = _make_df()
        df = df.drop(columns=["rank"])
        out = ssc.filter_for_sat(df)
        assert all(out["combined_score"] >= ssc.SAT_SCORE_THRESHOLD)

    def test_all_rows_pass_when_all_qualify(self):
        ssc = _import_ssc()
        df = _make_df(combined_score=[0.95, 0.91, 0.87], rank=[1, 1, 1])
        out = ssc.filter_for_sat(df)
        assert len(out) == 3


# ── Tests: annotate ───────────────────────────────────────────────────────────

class TestAnnotate:
    def test_adds_blif_path_columns(self):
        ssc = _import_ssc()
        df = _make_df().query("rank == 1 and combined_score >= 0.85").copy()
        out = ssc.annotate(df)
        assert "orig_blif" in out.columns
        assert "opt_blif" in out.columns

    def test_blif_paths_use_variants_prefix(self):
        ssc = _import_ssc()
        row = pd.DataFrame({
            "benchmark": ["myfunc"], "optimization": ["resyn2"],
            "orig_node": ["n0"], "opt_node": ["x0"],
            "combined_score": [0.92], "rank": [1],
        })
        out = ssc.annotate(row)
        assert out["orig_blif"].iloc[0].startswith("variants/")
        assert out["opt_blif"].iloc[0].startswith("variants/")
        assert "myfunc_original" in out["orig_blif"].iloc[0]
        assert "resyn2" in out["opt_blif"].iloc[0]

    def test_needs_sat_check_flag(self):
        ssc = _import_ssc()
        df = _make_df().iloc[:1].copy()
        out = ssc.annotate(df)
        assert out["needs_sat_check"].all()

    def test_sat_reason_mentions_score(self):
        ssc = _import_ssc()
        df = _make_df().iloc[:1].copy()
        out = ssc.annotate(df)
        assert "score" in out["sat_reason"].iloc[0].lower()


# ── Tests: load_candidates ────────────────────────────────────────────────────

class TestLoadCandidates:
    def test_raises_on_missing_file(self, tmp_path):
        ssc = _import_ssc()
        with pytest.raises(FileNotFoundError, match="top_candidates"):
            ssc.load_candidates(str(tmp_path / "nonexistent.csv"))

    def test_loads_valid_csv(self, tmp_path):
        ssc = _import_ssc()
        csv = tmp_path / "top_candidates.csv"
        _make_df().to_csv(csv, index=False)
        df = ssc.load_candidates(str(csv))
        assert len(df) == 3


# ── Tests: real benchmark discovery ──────────────────────────────────────────

class TestRealBenchmarkDiscovery:
    """Confirm that benchmarks/real/**/*.blif files actually exist in the repo."""

    def test_hand_written_benchmarks_present(self):
        real_dir = _REPO_ROOT / "benchmarks" / "real" / "hand_written"
        blif_files = list(real_dir.glob("*.blif"))
        assert len(blif_files) >= 4, (
            f"Expected at least 4 hand-written BLIFs, found {len(blif_files)}: "
            + ", ".join(f.name for f in blif_files)
        )

    def test_blif_files_have_model_and_end(self):
        real_dir = _REPO_ROOT / "benchmarks" / "real" / "hand_written"
        for bf in real_dir.glob("*.blif"):
            text = bf.read_text()
            assert ".model" in text, f"{bf.name} missing .model"
            assert ".end" in text, f"{bf.name} missing .end"

    def test_blif_files_have_inputs_and_outputs(self):
        real_dir = _REPO_ROOT / "benchmarks" / "real" / "hand_written"
        for bf in real_dir.glob("*.blif"):
            text = bf.read_text()
            assert ".inputs" in text, f"{bf.name} missing .inputs"
            assert ".outputs" in text, f"{bf.name} missing .outputs"


# ── Tests: exact-match filtering (Carmine's methodology fix) ─────────────────

class TestExactMatchFiltering:
    """
    Verify that filter_for_sat() excludes exact-signature-match candidates
    by default, and that annotate() writes the correct match_category and
    sat_reason for each row.
    """

    def test_exact_matches_excluded_by_default(self):
        """Rows with is_exact_signature_match==1 must not reach the SAT queue."""
        ssc = _import_ssc()
        df = _make_df_with_exact()
        out = ssc.filter_for_sat(df)
        assert 1 not in out["is_exact_signature_match"].tolist(), (
            "Exact-match rows should be excluded when INCLUDE_EXACT_ANCHORS=False"
        )

    def test_non_exact_candidates_retained(self):
        """Rows with is_exact_signature_match==0 must survive the filter."""
        ssc = _import_ssc()
        df = _make_df_with_exact()
        out = ssc.filter_for_sat(df)
        assert len(out) == 1
        assert out.iloc[0]["is_exact_signature_match"] == 0

    def test_missing_column_treated_as_non_exact(self):
        """
        If is_exact_signature_match is absent (old CSV), the function should
        emit a warning and treat all rows as non-exact (conservative path).
        """
        ssc = _import_ssc()
        df = _make_df_with_exact().drop(columns=["is_exact_signature_match", "match_category"])
        # Should not raise; all rank-1 high-score rows survive
        out = ssc.filter_for_sat(df)
        assert len(out) >= 1

    def test_annotate_adds_match_category_column(self):
        """annotate() must always produce a match_category column."""
        ssc = _import_ssc()
        df = _make_df().iloc[:1].copy()   # single non-exact row
        out = ssc.annotate(df)
        assert "match_category" in out.columns

    def test_annotate_non_exact_category_value(self):
        """A non-exact row gets match_category == 'non_exact_candidate'."""
        ssc = _import_ssc()
        df = _make_df().iloc[:1].copy()
        out = ssc.annotate(df)
        assert out["match_category"].iloc[0] == "non_exact_candidate"

    def test_annotate_exact_anchor_sat_reason(self):
        """
        If an exact-anchor row passes through (INCLUDE_EXACT_ANCHORS=True
        scenario), annotate() should write a sat_reason that mentions 'anchor'
        or 'sanity'.
        """
        ssc = _import_ssc()
        # Build a single-row DataFrame that looks like an exact-anchor row
        df = pd.DataFrame({
            "benchmark": ["b1"],
            "optimization": ["balance"],
            "orig_node": ["n1"],
            "opt_node": ["x1"],
            "combined_score": [0.95],
            "rank": [1],
            "is_exact_signature_match": [1],
            "match_category": ["exact_anchor"],
        })
        out = ssc.annotate(df)
        reason = out["sat_reason"].iloc[0].lower()
        assert "anchor" in reason or "sanity" in reason, (
            f"Expected 'anchor' or 'sanity' in sat_reason for exact-anchor row; got: {reason}"
        )

    def test_annotate_non_exact_sat_reason_mentions_score(self):
        """sat_reason for a non-exact candidate should mention the score."""
        ssc = _import_ssc()
        df = _make_df().iloc[:1].copy()
        out = ssc.annotate(df)
        assert "score" in out["sat_reason"].iloc[0].lower()

    def test_filter_all_exact_returns_empty(self):
        """When all candidates are exact matches, filter_for_sat should return empty."""
        ssc = _import_ssc()
        df = pd.DataFrame({
            "benchmark": ["b1", "b1"],
            "optimization": ["balance", "balance"],
            "orig_node": ["n1", "n2"],
            "opt_node": ["x1", "x2"],
            "combined_score": [0.99, 0.97],
            "rank": [1, 1],
            "is_exact_signature_match": [1, 1],
            "match_category": ["exact_anchor", "exact_anchor"],
        })
        out = ssc.filter_for_sat(df)
        assert out.empty, "All-exact input should yield empty output by default"
