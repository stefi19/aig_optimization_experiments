"""
tests/test_summarize_sat_results.py

Unit tests for pure helper functions in summarize_sat_results.py.

These tests do NOT require ABC or any real CSV on disk.
They test: compute_group_summary, add_global_row, build_markdown, _df_to_md_table.

Run with:  python3 -m pytest tests/ -v
"""

import os
import sys
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from summarize_sat_results import (
    compute_group_summary,
    add_global_row,
    build_markdown,
    _df_to_md_table,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_df(rows):
    """Build a DataFrame with the columns sat_refinement_abc.py produces."""
    return pd.DataFrame(rows, columns=[
        "benchmark", "optimization",
        "optimized_node", "original_candidate",
        "combined_score", "sat_status", "abc_result", "notes",
    ])


def make_df_with_category(rows):
    """Build a DataFrame that also carries match_category (post-methodology-fix)."""
    return pd.DataFrame(rows, columns=[
        "benchmark", "optimization",
        "optimized_node", "original_candidate",
        "combined_score", "is_exact_signature_match", "match_category",
        "sat_status", "abc_result", "notes",
    ])


SAMPLE_ROWS = [
    ("bench_a", "balance",  "n1", "n1", 0.95, "verified",     "Networks are equivalent", ""),
    ("bench_a", "balance",  "n2", "n2", 0.90, "verified",     "Networks are equivalent", ""),
    ("bench_a", "balance",  "n3", "n9", 0.88, "inconclusive", "***EOF***",               "node not found"),
    ("bench_a", "rewrite",  "n4", "n4", 0.92, "verified",     "Networks are equivalent", ""),
    ("bench_b", "balance",  "n5", "n5", 0.91, "verified",     "Networks are equivalent", ""),
    ("bench_b", "balance",  "n6", "n7", 0.87, "rejected",     "Networks are NOT EQUIVALENT.", ""),
]

# Rows with match_category: mix of exact_anchor and non_exact_candidate.
SAMPLE_ROWS_CATEGORISED = [
    # exact anchors (sanity-check pairs — already known matches)
    ("bench_a", "balance", "n1", "n1", 0.99, 1, "exact_anchor",        "verified",     "Networks are equivalent",     ""),
    ("bench_a", "balance", "n2", "n2", 0.97, 1, "exact_anchor",        "rejected",     "Networks are NOT EQUIVALENT.", ""),
    # non-exact candidates (genuine recovery attempts)
    ("bench_a", "balance", "n3", "n9", 0.88, 0, "non_exact_candidate", "verified",     "Networks are equivalent",     ""),
    ("bench_a", "balance", "n4", "n8", 0.85, 0, "non_exact_candidate", "inconclusive", "***EOF***",                   ""),
    ("bench_b", "balance", "n5", "n6", 0.91, 0, "non_exact_candidate", "rejected",     "Networks are NOT EQUIVALENT.", ""),
]


# ── compute_group_summary ─────────────────────────────────────────────────────

class TestComputeGroupSummary:
    def test_counts_are_correct(self):
        df = make_df(SAMPLE_ROWS)
        summary = compute_group_summary(df)

        bench_a_bal = summary[
            (summary["benchmark"] == "bench_a") & (summary["optimization"] == "balance")
        ].iloc[0]
        assert bench_a_bal["verified"]     == 2
        assert bench_a_bal["inconclusive"] == 1
        assert bench_a_bal["rejected"]     == 0
        assert bench_a_bal["total"]        == 3

    def test_rates_sum_to_one(self):
        df = make_df(SAMPLE_ROWS)
        summary = compute_group_summary(df)
        for _, row in summary.iterrows():
            total_rate = row["verification_rate"] + row["rejection_rate"] + row["inconclusive_rate"]
            assert abs(total_rate - 1.0) < 1e-6

    def test_verification_rate_value(self):
        df = make_df(SAMPLE_ROWS)
        summary = compute_group_summary(df)
        bench_a_bal = summary[
            (summary["benchmark"] == "bench_a") & (summary["optimization"] == "balance")
        ].iloc[0]
        # 2 verified out of 3 total
        assert abs(bench_a_bal["verification_rate"] - 2/3) < 1e-4

    def test_rejection_rate_value(self):
        df = make_df(SAMPLE_ROWS)
        summary = compute_group_summary(df)
        bench_b_bal = summary[
            (summary["benchmark"] == "bench_b") & (summary["optimization"] == "balance")
        ].iloc[0]
        # 1 rejected out of 2 total
        assert abs(bench_b_bal["rejection_rate"] - 0.5) < 1e-4

    def test_avg_combined_score(self):
        df = make_df(SAMPLE_ROWS)
        summary = compute_group_summary(df)
        bench_a_bal = summary[
            (summary["benchmark"] == "bench_a") & (summary["optimization"] == "balance")
        ].iloc[0]
        expected_avg = round((0.95 + 0.90 + 0.88) / 3, 4)
        assert abs(bench_a_bal["avg_combined_score"] - expected_avg) < 1e-4

    def test_all_groups_present(self):
        df = make_df(SAMPLE_ROWS)
        summary = compute_group_summary(df)
        # bench_a/balance, bench_a/rewrite, bench_b/balance
        assert len(summary) == 3

    def test_empty_dataframe(self):
        df = make_df([])
        summary = compute_group_summary(df)
        assert summary.empty


# ── add_global_row ────────────────────────────────────────────────────────────

class TestAddGlobalRow:
    def test_global_row_is_appended(self):
        df = make_df(SAMPLE_ROWS)
        summary = compute_group_summary(df)
        full = add_global_row(summary, df)
        assert any((full["benchmark"] == "ALL") & (full["optimization"] == "ALL"))

    def test_global_total_is_sum(self):
        df = make_df(SAMPLE_ROWS)
        summary = compute_group_summary(df)
        full = add_global_row(summary, df)
        global_row = full[(full["benchmark"] == "ALL")].iloc[0]
        assert global_row["total"] == len(df)

    def test_global_verified_count(self):
        df = make_df(SAMPLE_ROWS)
        summary = compute_group_summary(df)
        full = add_global_row(summary, df)
        global_row = full[(full["benchmark"] == "ALL")].iloc[0]
        expected = sum(1 for r in SAMPLE_ROWS if r[5] == "verified")
        assert global_row["verified"] == expected

    def test_global_rejected_count(self):
        df = make_df(SAMPLE_ROWS)
        summary = compute_group_summary(df)
        full = add_global_row(summary, df)
        global_row = full[(full["benchmark"] == "ALL")].iloc[0]
        expected = sum(1 for r in SAMPLE_ROWS if r[5] == "rejected")
        assert global_row["rejected"] == expected

    def test_global_row_on_empty(self):
        df = make_df([])
        summary = compute_group_summary(df)
        full = add_global_row(summary, df)
        global_row = full[(full["benchmark"] == "ALL")].iloc[0]
        assert global_row["total"] == 0


# ── rejected candidates extraction ───────────────────────────────────────────

class TestRejectedExtraction:
    def test_rejected_rows_identified(self):
        df = make_df(SAMPLE_ROWS)
        rejected = df[df["sat_status"] == "rejected"]
        assert len(rejected) == 1
        assert rejected.iloc[0]["benchmark"] == "bench_b"

    def test_no_rejected_when_all_verified(self):
        rows = [r for r in SAMPLE_ROWS if r[5] != "rejected"]
        df = make_df(rows)
        rejected = df[df["sat_status"] == "rejected"]
        assert rejected.empty


# ── build_markdown ────────────────────────────────────────────────────────────

class TestBuildMarkdown:
    def test_contains_header(self):
        df = make_df(SAMPLE_ROWS)
        summary = add_global_row(compute_group_summary(df), df)
        md = build_markdown(df, summary)
        assert "# SAT Refinement Summary" in md

    def test_contains_overall_section(self):
        df = make_df(SAMPLE_ROWS)
        summary = add_global_row(compute_group_summary(df), df)
        md = build_markdown(df, summary)
        assert "## Overall result" in md
        assert "Total candidates checked" in md

    def test_contains_rejected_section(self):
        df = make_df(SAMPLE_ROWS)
        summary = add_global_row(compute_group_summary(df), df)
        md = build_markdown(df, summary)
        assert "## Rejected candidates" in md
        assert "bench_b" in md

    def test_no_rejected_message_when_empty(self):
        rows = [r for r in SAMPLE_ROWS if r[5] != "rejected"]
        df = make_df(rows)
        summary = add_global_row(compute_group_summary(df), df)
        md = build_markdown(df, summary)
        assert "No candidates were rejected" in md

    def test_contains_inconclusive_section(self):
        df = make_df(SAMPLE_ROWS)
        summary = add_global_row(compute_group_summary(df), df)
        md = build_markdown(df, summary)
        assert "## Inconclusive candidates" in md

    def test_contains_interpretation(self):
        df = make_df(SAMPLE_ROWS)
        summary = add_global_row(compute_group_summary(df), df)
        md = build_markdown(df, summary)
        assert "## Main interpretation" in md

    def test_empty_input(self):
        df = make_df([])
        summary = add_global_row(compute_group_summary(df), df)
        md = build_markdown(df, summary)
        assert "# SAT Refinement Summary" in md
        assert "No candidates were checked" in md


# ── _df_to_md_table ───────────────────────────────────────────────────────────

class TestDfToMdTable:
    def test_header_row_present(self):
        df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
        table = _df_to_md_table(df)
        assert "| a | b |" in table

    def test_separator_row_present(self):
        df = pd.DataFrame({"a": [1], "b": [2]})
        table = _df_to_md_table(df)
        assert "| --- | --- |" in table

    def test_data_row_present(self):
        df = pd.DataFrame({"x": ["hello"], "y": ["world"]})
        table = _df_to_md_table(df)
        assert "hello" in table
        assert "world" in table

    def test_empty_df_returns_placeholder(self):
        df = pd.DataFrame({"a": [], "b": []})
        result = _df_to_md_table(df)
        assert "_No rows._" in result

    def test_float_rate_formatted_as_percentage(self):
        df = pd.DataFrame({"verification_rate": [0.8166]})
        table = _df_to_md_table(df)
        assert "81.66%" in table

    def test_plain_float_not_percentage(self):
        df = pd.DataFrame({"avg_combined_score": [0.9500]})
        table = _df_to_md_table(df)
        assert "0.9500" in table


# ── match_category breakdown (Carmine's methodology fix) ─────────────────────

class TestMatchCategoryBreakdown:
    """
    Verify that _summarise_group() correctly splits results into
    exact_anchor vs non_exact_candidate, and that build_markdown()
    emits the 'Match category breakdown' section.
    """

    def _summary_with_categories(self):
        df = make_df_with_category(SAMPLE_ROWS_CATEGORISED)
        summary = compute_group_summary(df)
        return df, summary

    def test_exact_anchor_verified_count(self):
        df, summary = self._summary_with_categories()
        bench_a_bal = summary[
            (summary["benchmark"] == "bench_a") & (summary["optimization"] == "balance")
        ].iloc[0]
        assert bench_a_bal["exact_anchor_verified"] == 1

    def test_exact_anchor_rejected_count(self):
        df, summary = self._summary_with_categories()
        bench_a_bal = summary[
            (summary["benchmark"] == "bench_a") & (summary["optimization"] == "balance")
        ].iloc[0]
        assert bench_a_bal["exact_anchor_rejected"] == 1

    def test_non_exact_verified_count(self):
        df, summary = self._summary_with_categories()
        bench_a_bal = summary[
            (summary["benchmark"] == "bench_a") & (summary["optimization"] == "balance")
        ].iloc[0]
        assert bench_a_bal["non_exact_verified"] == 1

    def test_non_exact_inconclusive_count(self):
        df, summary = self._summary_with_categories()
        bench_a_bal = summary[
            (summary["benchmark"] == "bench_a") & (summary["optimization"] == "balance")
        ].iloc[0]
        assert bench_a_bal["non_exact_inconclusive"] == 1

    def test_category_columns_present_in_summary(self):
        df, summary = self._summary_with_categories()
        for col in (
            "exact_anchor_verified", "exact_anchor_rejected", "exact_anchor_inconclusive",
            "non_exact_verified",    "non_exact_rejected",    "non_exact_inconclusive",
        ):
            assert col in summary.columns, f"Missing column: {col}"

    def test_markdown_contains_category_breakdown_section(self):
        df, summary = self._summary_with_categories()
        full = add_global_row(summary, df)
        md = build_markdown(df, full)
        assert "Match category breakdown" in md, (
            "build_markdown() should contain a 'Match category breakdown' section"
        )

    def test_markdown_mentions_exact_anchor(self):
        df, summary = self._summary_with_categories()
        full = add_global_row(summary, df)
        md = build_markdown(df, full)
        assert "exact_anchor" in md

    def test_markdown_mentions_non_exact_candidate(self):
        df, summary = self._summary_with_categories()
        full = add_global_row(summary, df)
        md = build_markdown(df, full)
        assert "non_exact_candidate" in md

    def test_markdown_important_callout_present(self):
        """The 'Important' note distinguishing sanity checks from genuine recovery."""
        df, summary = self._summary_with_categories()
        full = add_global_row(summary, df)
        md = build_markdown(df, full)
        assert "Important" in md or "important" in md.lower()

    def test_old_csv_backfilled_as_non_exact(self):
        """
        A DataFrame without match_category (old pipeline output) should be
        back-filled as 'non_exact_candidate' — conservative assumption.
        """
        df = make_df(SAMPLE_ROWS)          # no match_category column
        assert "match_category" not in df.columns
        summary = compute_group_summary(df)
        # After back-fill inside _summarise_group the non_exact counts should
        # equal the overall counts (everything treated as non-exact).
        bench_a_bal = summary[
            (summary["benchmark"] == "bench_a") & (summary["optimization"] == "balance")
        ].iloc[0]
        assert bench_a_bal["non_exact_verified"] == bench_a_bal["verified"]
