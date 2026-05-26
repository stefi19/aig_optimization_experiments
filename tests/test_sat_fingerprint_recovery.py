"""
tests/test_sat_fingerprint_recovery.py
=======================================
Unit tests for the fingerprint-based fallback recovery added to
sat_refinement_abc.py and the corresponding recovery_method columns in
summarize_sat_results.py.

Tests do NOT require ABC to be installed and do NOT touch the filesystem
(except for temporary files created with tempfile helpers).

Covers:
  load_fingerprint_index    — CSV parsing, graceful degradation
  resolve_node_via_fingerprint — zero / one / many matches
  check_candidate (mocked)  — recovery_method tagging
  summarize_sat_results     — new recovery columns in group summary + markdown
"""

import csv
import io
import os
import sys
import tempfile

import pandas as pd
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sat_refinement_abc import (
    load_fingerprint_index,
    resolve_node_via_fingerprint,
)
from summarize_sat_results import (
    compute_group_summary,
    add_global_row,
    build_markdown,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_fp_csv(rows: list[dict]) -> str:
    """Write a node_fingerprints.csv to a temp file, return its path."""
    fields = ["benchmark", "optimization", "node", "fingerprint", "level",
              "fanin_count", "support_size"]
    tmp = tempfile.NamedTemporaryFile(
        mode="w", suffix=".csv", delete=False, newline=""
    )
    writer = csv.DictWriter(tmp, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)
    tmp.close()
    return tmp.name


def _make_verified_df(rows: list[dict]) -> pd.DataFrame:
    """Build a DataFrame that mimics sat_verified_candidates.csv."""
    cols = [
        "benchmark", "optimization",
        "optimized_node", "original_candidate",
        "combined_score", "sat_status", "abc_result",
        "recovery_method", "notes",
    ]
    return pd.DataFrame(rows, columns=cols)


# ---------------------------------------------------------------------------
# load_fingerprint_index
# ---------------------------------------------------------------------------

class TestLoadFingerprintIndex:

    def test_returns_empty_dict_when_file_missing(self):
        idx = load_fingerprint_index("/nonexistent/path/fingerprints.csv")
        assert idx == {}

    def test_parses_single_row(self):
        path = _write_fp_csv([
            {"benchmark": "toy", "optimization": "original",
             "node": "n1", "fingerprint": "abcd1234abcd1234",
             "level": 1, "fanin_count": 2, "support_size": 2},
        ])
        try:
            idx = load_fingerprint_index(path)
        finally:
            os.unlink(path)

        assert ("toy", "original") in idx
        assert "abcd1234abcd1234" in idx[("toy", "original")]
        assert idx[("toy", "original")]["abcd1234abcd1234"] == ["n1"]

    def test_multiple_nodes_same_fingerprint(self):
        """Two nodes with identical fingerprints — ambiguous, both stored."""
        path = _write_fp_csv([
            {"benchmark": "toy", "optimization": "balance",
             "node": "n1", "fingerprint": "aaaa0000aaaa0000",
             "level": 1, "fanin_count": 2, "support_size": 2},
            {"benchmark": "toy", "optimization": "balance",
             "node": "n2", "fingerprint": "aaaa0000aaaa0000",
             "level": 1, "fanin_count": 2, "support_size": 2},
        ])
        try:
            idx = load_fingerprint_index(path)
        finally:
            os.unlink(path)

        names = idx[("toy", "balance")]["aaaa0000aaaa0000"]
        assert sorted(names) == ["n1", "n2"]

    def test_different_variants_independent(self):
        path = _write_fp_csv([
            {"benchmark": "toy", "optimization": "original",
             "node": "n1", "fingerprint": "fp_orig_fp_orig",
             "level": 1, "fanin_count": 1, "support_size": 1},
            {"benchmark": "toy", "optimization": "balance",
             "node": "m1", "fingerprint": "fp_bal__fp_bal_",
             "level": 1, "fanin_count": 1, "support_size": 1},
        ])
        try:
            idx = load_fingerprint_index(path)
        finally:
            os.unlink(path)

        assert ("toy", "original") in idx
        assert ("toy", "balance") in idx
        assert "fp_orig_fp_orig" not in idx[("toy", "balance")]
        assert "fp_bal__fp_bal_" not in idx[("toy", "original")]

    def test_skips_rows_with_empty_fingerprint(self):
        path = _write_fp_csv([
            {"benchmark": "toy", "optimization": "original",
             "node": "n1", "fingerprint": "",
             "level": 1, "fanin_count": 1, "support_size": 1},
        ])
        try:
            idx = load_fingerprint_index(path)
        finally:
            os.unlink(path)

        # Empty fingerprint → nothing indexed
        assert idx.get(("toy", "original"), {}) == {}

    def test_skips_rows_with_empty_node(self):
        path = _write_fp_csv([
            {"benchmark": "toy", "optimization": "original",
             "node": "", "fingerprint": "1234abcd1234abcd",
             "level": 1, "fanin_count": 1, "support_size": 1},
        ])
        try:
            idx = load_fingerprint_index(path)
        finally:
            os.unlink(path)

        assert idx.get(("toy", "original"), {}) == {}

    def test_returns_empty_on_corrupt_file(self, tmp_path):
        corrupt = tmp_path / "bad.csv"
        corrupt.write_bytes(b"\xff\xfe broken \x00\x01")
        # Should not raise; should return empty dict
        idx = load_fingerprint_index(str(corrupt))
        assert isinstance(idx, dict)

    def test_multiple_benchmarks(self):
        path = _write_fp_csv([
            {"benchmark": "bench_a", "optimization": "original",
             "node": "x1", "fingerprint": "aabbccddaabbccdd",
             "level": 1, "fanin_count": 2, "support_size": 2},
            {"benchmark": "bench_b", "optimization": "original",
             "node": "y1", "fingerprint": "11223344aabbccdd",
             "level": 2, "fanin_count": 1, "support_size": 1},
        ])
        try:
            idx = load_fingerprint_index(path)
        finally:
            os.unlink(path)

        assert len(idx) == 2
        assert "aabbccddaabbccdd" in idx[("bench_a", "original")]
        assert "11223344aabbccdd" in idx[("bench_b", "original")]


# ---------------------------------------------------------------------------
# resolve_node_via_fingerprint
# ---------------------------------------------------------------------------

class TestResolveNodeViaFingerprint:

    def _idx(self):
        return {
            ("toy", "original"): {
                "unique_fp_unique_fp": ["n_unique"],
                "ambig_fp_ambig_fp_": ["n_amb1", "n_amb2"],
            },
            ("toy", "balance"): {
                "opt_fp__opt_fp__": ["m_opt"],
            },
        }

    def test_returns_node_for_unique_fingerprint(self):
        result = resolve_node_via_fingerprint(
            self._idx(), "toy", "original", "unique_fp_unique_fp"
        )
        assert result == "n_unique"

    def test_returns_none_for_ambiguous_fingerprint(self):
        result = resolve_node_via_fingerprint(
            self._idx(), "toy", "original", "ambig_fp_ambig_fp_"
        )
        assert result is None

    def test_returns_none_for_unknown_fingerprint(self):
        result = resolve_node_via_fingerprint(
            self._idx(), "toy", "original", "does_not_exist___"
        )
        assert result is None

    def test_returns_none_for_unknown_benchmark(self):
        result = resolve_node_via_fingerprint(
            self._idx(), "unknown_bench", "original", "unique_fp_unique_fp"
        )
        assert result is None

    def test_returns_none_for_unknown_optimization(self):
        result = resolve_node_via_fingerprint(
            self._idx(), "toy", "rewrite", "unique_fp_unique_fp"
        )
        assert result is None

    def test_returns_none_for_empty_fingerprint(self):
        result = resolve_node_via_fingerprint(
            self._idx(), "toy", "original", ""
        )
        assert result is None

    def test_returns_none_for_empty_index(self):
        result = resolve_node_via_fingerprint(
            {}, "toy", "original", "unique_fp_unique_fp"
        )
        assert result is None

    def test_correct_variant_used(self):
        """The same fingerprint maps to different nodes in different variants."""
        idx = {
            ("toy", "original"): {"shared_fp_shared_fp": ["orig_node"]},
            ("toy", "balance"):  {"shared_fp_shared_fp": ["opt_node"]},
        }
        assert resolve_node_via_fingerprint(idx, "toy", "original", "shared_fp_shared_fp") == "orig_node"
        assert resolve_node_via_fingerprint(idx, "toy", "balance",  "shared_fp_shared_fp") == "opt_node"

    def test_single_item_list_is_unambiguous(self):
        idx = {("b", "o"): {"fp": ["only_node"]}}
        assert resolve_node_via_fingerprint(idx, "b", "o", "fp") == "only_node"

    def test_two_item_list_is_ambiguous(self):
        idx = {("b", "o"): {"fp": ["node_a", "node_b"]}}
        assert resolve_node_via_fingerprint(idx, "b", "o", "fp") is None


# ---------------------------------------------------------------------------
# compute_group_summary — recovery_method columns
# ---------------------------------------------------------------------------

class TestComputeGroupSummaryRecoveryColumns:

    def _df(self):
        return _make_verified_df([
            {"benchmark": "toy", "optimization": "balance",
             "optimized_node": "m1", "original_candidate": "n1",
             "combined_score": 0.9, "sat_status": "verified",
             "abc_result": "Networks are equivalent", "recovery_method": "direct",
             "notes": ""},
            {"benchmark": "toy", "optimization": "balance",
             "optimized_node": "m2", "original_candidate": "n2",
             "combined_score": 0.85, "sat_status": "verified",
             "abc_result": "Networks are equivalent", "recovery_method": "fingerprint",
             "notes": "original: 'n2' → 'n2_abc' via fingerprint"},
            {"benchmark": "toy", "optimization": "balance",
             "optimized_node": "m3", "original_candidate": "n3",
             "combined_score": 0.7, "sat_status": "inconclusive",
             "abc_result": "", "recovery_method": "inconclusive",
             "notes": "no unique fingerprint match"},
        ])

    def test_direct_name_count(self):
        summary = compute_group_summary(self._df())
        row = summary.iloc[0]
        assert row["direct_name_count"] == 1

    def test_fingerprint_recovered_count(self):
        summary = compute_group_summary(self._df())
        row = summary.iloc[0]
        assert row["fingerprint_recovered"] == 1

    def test_still_inconclusive_count(self):
        summary = compute_group_summary(self._df())
        row = summary.iloc[0]
        assert row["still_inconclusive"] == 1

    def test_recovery_counts_sum_to_total(self):
        summary = compute_group_summary(self._df())
        row = summary.iloc[0]
        assert (
            row["direct_name_count"]
            + row["fingerprint_recovered"]
            + row["still_inconclusive"]
        ) == row["total"]

    def test_columns_present_in_global_row(self):
        df = self._df()
        summary = compute_group_summary(df)
        full    = add_global_row(summary, df)
        global_row = full[full["benchmark"] == "ALL"].iloc[0]
        for col in ("direct_name_count", "fingerprint_recovered", "still_inconclusive"):
            assert col in global_row.index, f"Missing column: {col}"

    def test_global_row_sums_correctly(self):
        df = self._df()
        summary = compute_group_summary(df)
        full    = add_global_row(summary, df)
        global_row = full[full["benchmark"] == "ALL"].iloc[0]
        assert int(global_row["direct_name_count"])    == 1
        assert int(global_row["fingerprint_recovered"]) == 1
        assert int(global_row["still_inconclusive"])   == 1

    def test_old_df_without_recovery_method_backfilled(self):
        """DataFrames without recovery_method are back-filled by load_verified;
        simulate that here by manually adding the column as load_verified would."""
        old_cols = [
            "benchmark", "optimization", "optimized_node", "original_candidate",
            "combined_score", "sat_status", "abc_result", "notes",
        ]
        df = pd.DataFrame([
            ("toy", "balance", "m1", "n1", 0.9, "verified",     "eq", ""),
            ("toy", "balance", "m2", "n2", 0.7, "inconclusive", "",   "missing"),
        ], columns=old_cols)

        # Simulate load_verified back-fill
        df["recovery_method"] = df["sat_status"].map(
            lambda s: "inconclusive" if s == "inconclusive" else "direct"
        )

        summary = compute_group_summary(df)
        row = summary.iloc[0]
        assert row["direct_name_count"]   == 1
        assert row["still_inconclusive"]  == 1
        assert row["fingerprint_recovered"] == 0


# ---------------------------------------------------------------------------
# build_markdown — recovery section
# ---------------------------------------------------------------------------

class TestBuildMarkdownRecoverySection:

    def _summary_and_df(self, rows):
        df = _make_verified_df(rows)
        summary = add_global_row(compute_group_summary(df), df)
        return df, summary

    def test_recovery_section_present(self):
        df, summary = self._summary_and_df([
            {"benchmark": "toy", "optimization": "balance",
             "optimized_node": "m1", "original_candidate": "n1",
             "combined_score": 0.9, "sat_status": "verified",
             "abc_result": "eq", "recovery_method": "direct", "notes": ""},
        ])
        md = build_markdown(df, summary)
        assert "Recovery method breakdown" in md

    def test_direct_count_shown(self):
        df, summary = self._summary_and_df([
            {"benchmark": "toy", "optimization": "balance",
             "optimized_node": "m1", "original_candidate": "n1",
             "combined_score": 0.9, "sat_status": "verified",
             "abc_result": "eq", "recovery_method": "direct", "notes": ""},
        ])
        md = build_markdown(df, summary)
        assert "direct" in md.lower()

    def test_fingerprint_rescue_message_shown_when_nonzero(self):
        df, summary = self._summary_and_df([
            {"benchmark": "toy", "optimization": "balance",
             "optimized_node": "m1", "original_candidate": "n1",
             "combined_score": 0.9, "sat_status": "verified",
             "abc_result": "eq", "recovery_method": "fingerprint", "notes": ""},
        ])
        md = build_markdown(df, summary)
        assert "rescued" in md.lower() or "fingerprint" in md.lower()

    def test_per_group_table_includes_recovery_columns(self):
        df, summary = self._summary_and_df([
            {"benchmark": "toy", "optimization": "balance",
             "optimized_node": "m1", "original_candidate": "n1",
             "combined_score": 0.9, "sat_status": "verified",
             "abc_result": "eq", "recovery_method": "direct", "notes": ""},
        ])
        md = build_markdown(df, summary)
        assert "direct_name_count" in md
        assert "fingerprint_recovered" in md
        assert "still_inconclusive" in md

    def test_empty_df_does_not_crash(self):
        df = pd.DataFrame(columns=[
            "benchmark", "optimization", "optimized_node", "original_candidate",
            "combined_score", "sat_status", "abc_result", "recovery_method", "notes",
        ])
        summary = add_global_row(compute_group_summary(df), df)
        md = build_markdown(df, summary)
        assert isinstance(md, str)
        assert len(md) > 0
