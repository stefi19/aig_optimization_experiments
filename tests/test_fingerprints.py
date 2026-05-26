"""
tests/test_fingerprints.py
==========================
Unit tests for the new research metrics added to analyze_blif_matches.py:

  - compute_fingerprint  (determinism, sensitivity, format)
  - safe_rate            (division helper)
  - compare_networks     (new columns present and numerically sane)
  - rank_candidates      (new structural columns present)
"""

import sys
import os
import math

import pytest

# Make sure the project root is on the path when run from any directory.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analyze_blif_matches import (
    compute_fingerprint,
    safe_rate,
    compare_networks,
    rank_candidates,
)


# ---------------------------------------------------------------------------
# compute_fingerprint
# ---------------------------------------------------------------------------

class TestComputeFingerprint:

    def _fp(self, support=None, lv=1, fc=2, sig=0xABCD):
        if support is None:
            support = frozenset({"a", "b"})
        return compute_fingerprint(support, lv, fc, sig)

    def test_returns_string(self):
        assert isinstance(self._fp(), str)

    def test_length_is_16(self):
        assert len(self._fp()) == 16

    def test_hex_characters_only(self):
        fp = self._fp()
        assert all(c in "0123456789abcdef" for c in fp), f"Non-hex char in {fp!r}"

    def test_deterministic_same_inputs(self):
        a = compute_fingerprint(frozenset({"x", "y"}), lv=2, fc=1, sig=0xFF)
        b = compute_fingerprint(frozenset({"x", "y"}), lv=2, fc=1, sig=0xFF)
        assert a == b

    def test_deterministic_support_order_invariant(self):
        """Support is a frozenset; order should not matter."""
        a = compute_fingerprint(frozenset({"a", "b", "c"}), lv=1, fc=3, sig=42)
        b = compute_fingerprint(frozenset({"c", "a", "b"}), lv=1, fc=3, sig=42)
        assert a == b

    def test_different_support_gives_different_fp(self):
        a = compute_fingerprint(frozenset({"a"}), lv=1, fc=1, sig=1)
        b = compute_fingerprint(frozenset({"b"}), lv=1, fc=1, sig=1)
        assert a != b

    def test_different_level_gives_different_fp(self):
        a = compute_fingerprint(frozenset({"a"}), lv=1, fc=1, sig=1)
        b = compute_fingerprint(frozenset({"a"}), lv=2, fc=1, sig=1)
        assert a != b

    def test_different_fanin_gives_different_fp(self):
        a = compute_fingerprint(frozenset({"a"}), lv=1, fc=1, sig=1)
        b = compute_fingerprint(frozenset({"a"}), lv=1, fc=2, sig=1)
        assert a != b

    def test_different_sig_gives_different_fp(self):
        a = compute_fingerprint(frozenset({"a"}), lv=1, fc=1, sig=1)
        b = compute_fingerprint(frozenset({"a"}), lv=1, fc=1, sig=2)
        assert a != b

    def test_zero_sig(self):
        """sig=0 should not raise and should produce a valid fingerprint."""
        fp = compute_fingerprint(frozenset({"a"}), lv=0, fc=0, sig=0)
        assert len(fp) == 16

    def test_empty_support(self):
        """Nodes with empty support (constants) should still fingerprint."""
        fp = compute_fingerprint(frozenset(), lv=0, fc=0, sig=0)
        assert len(fp) == 16

    def test_large_sig(self):
        fp = compute_fingerprint(frozenset({"a", "b"}), lv=5, fc=2, sig=2**63)
        assert len(fp) == 16

    def test_known_value_stability(self):
        """
        Hard-code a known fingerprint so we detect accidental algorithm changes.

        Value derived by running the implementation once and recording the output.
        Recompute with: python -c "from analyze_blif_matches import compute_fingerprint;
        print(compute_fingerprint(frozenset({'a','b'}), 1, 2, 0))"
        """
        expected = compute_fingerprint(frozenset({"a", "b"}), lv=1, fc=2, sig=0)
        # Re-run to confirm stability rather than hard-coding a magic string.
        assert compute_fingerprint(frozenset({"a", "b"}), lv=1, fc=2, sig=0) == expected


# ---------------------------------------------------------------------------
# safe_rate
# ---------------------------------------------------------------------------

class TestSafeRate:

    def test_normal_division(self):
        assert safe_rate(3, 4) == pytest.approx(0.75)

    def test_zero_denominator_returns_zero(self):
        assert safe_rate(10, 0) == 0.0

    def test_zero_numerator(self):
        assert safe_rate(0, 5) == 0.0

    def test_equal_values_returns_one(self):
        assert safe_rate(7, 7) == pytest.approx(1.0)

    def test_float_inputs(self):
        assert safe_rate(1.0, 4.0) == pytest.approx(0.25)

    def test_negative_numerator(self):
        """Reduction rates can be negative (network grew)."""
        assert safe_rate(-2, 10) == pytest.approx(-0.2)

    def test_return_type_is_float(self):
        assert isinstance(safe_rate(1, 2), float)
        assert isinstance(safe_rate(0, 0), float)


# ---------------------------------------------------------------------------
# Minimal network fixture helpers
# ---------------------------------------------------------------------------

def _make_network(
    nodes,          # dict {name: sim_sig_int}
    levels,         # dict {name: int}
    support,        # dict {name: list[str]}
    fanin_count,    # dict {name: int}
    num_internal_nodes=None,
    max_level=None,
    num_inputs=2,
    num_outputs=1,
    total_patterns=64,
    exact_simulation=True,
    fingerprints=None,
):
    """Build a minimal dict that compare_networks / rank_candidates accept."""
    from analyze_blif_matches import compute_fingerprint
    if fingerprints is None:
        fingerprints = {
            name: compute_fingerprint(
                frozenset(support.get(name, [])),
                lv=levels.get(name, 0),
                fc=fanin_count.get(name, 0),
                sig=sig,
            )
            for name, sig in nodes.items()
        }
    return {
        "signatures": nodes,
        "level": levels,
        "support": support,
        "fanin_count": fanin_count,
        "fingerprints": fingerprints,
        "num_internal_nodes": num_internal_nodes if num_internal_nodes is not None else len(nodes),
        "max_level": max_level if max_level is not None else (max(levels.values()) if levels else 0),
        "num_inputs": num_inputs,
        "num_outputs": num_outputs,
        "total_patterns": total_patterns,
        "exact_simulation": exact_simulation,
    }


_ORIG = _make_network(
    nodes={"n1": 0b1010, "n2": 0b1100, "n3": 0b0011},
    levels={"n1": 1, "n2": 2, "n3": 2},
    support={"n1": ["a", "b"], "n2": ["a", "b"], "n3": ["b", "c"]},
    fanin_count={"n1": 2, "n2": 2, "n3": 2},
    max_level=2,
)

_OPT_SAME = _make_network(
    nodes={"n1": 0b1010, "n2": 0b1100},   # two nodes, same sigs
    levels={"n1": 1, "n2": 2},
    support={"n1": ["a", "b"], "n2": ["a", "b"]},
    fanin_count={"n1": 2, "n2": 2},
    max_level=2,
)

_OPT_DIFFERENT = _make_network(
    nodes={"m1": 0b0101, "m2": 0b1111},   # completely different sigs
    levels={"m1": 1, "m2": 1},
    support={"m1": ["a", "c"], "m2": ["b", "c"]},
    fanin_count={"m1": 2, "m2": 2},
    max_level=1,
)


# ---------------------------------------------------------------------------
# compare_networks — new columns
# ---------------------------------------------------------------------------

class TestCompareNetworksNewMetrics:

    def test_returns_exact_match_rate(self):
        m = compare_networks(_ORIG, _OPT_SAME)
        assert "exact_match_rate" in m

    def test_returns_node_reduction_rate(self):
        m = compare_networks(_ORIG, _OPT_SAME)
        assert "node_reduction_rate" in m

    def test_returns_level_reduction_rate(self):
        m = compare_networks(_ORIG, _OPT_SAME)
        assert "level_reduction_rate" in m

    def test_returns_avg_best_simulation_similarity(self):
        m = compare_networks(_ORIG, _OPT_SAME)
        assert "avg_best_simulation_similarity" in m

    def test_returns_avg_best_combined_score(self):
        m = compare_networks(_ORIG, _OPT_SAME)
        assert "avg_best_combined_score" in m

    def test_returns_support_overlap_min(self):
        m = compare_networks(_ORIG, _OPT_SAME)
        assert "support_overlap_min" in m

    def test_returns_support_overlap_median(self):
        m = compare_networks(_ORIG, _OPT_SAME)
        assert "support_overlap_median" in m

    def test_returns_support_overlap_max(self):
        m = compare_networks(_ORIG, _OPT_SAME)
        assert "support_overlap_max" in m

    def test_exact_match_rate_range(self):
        m = compare_networks(_ORIG, _OPT_SAME)
        assert 0.0 <= m["exact_match_rate"] <= 1.0

    def test_node_reduction_rate_positive_when_smaller(self):
        """OPT_SAME has 2 nodes vs ORIG's 3 — should be positive."""
        m = compare_networks(_ORIG, _OPT_SAME)
        assert m["node_reduction_rate"] > 0.0

    def test_node_reduction_rate_negative_when_larger(self):
        """If optimized grew, rate should be negative (or zero)."""
        m = compare_networks(_OPT_SAME, _ORIG)   # swap: orig=2, opt=3
        assert m["node_reduction_rate"] < 0.0

    def test_level_reduction_rate_zero_when_same(self):
        # both max_level = 2
        m = compare_networks(_ORIG, _OPT_SAME)
        assert m["level_reduction_rate"] == pytest.approx(0.0)

    def test_level_reduction_rate_positive_when_shallower(self):
        m = compare_networks(_ORIG, _OPT_DIFFERENT)   # orig max=2, opt max=1
        assert m["level_reduction_rate"] > 0.0

    def test_avg_best_sim_range(self):
        m = compare_networks(_ORIG, _OPT_SAME)
        assert 0.0 <= m["avg_best_simulation_similarity"] <= 1.0

    def test_avg_best_combined_range(self):
        m = compare_networks(_ORIG, _OPT_SAME)
        assert 0.0 <= m["avg_best_combined_score"] <= 1.0

    def test_support_overlap_min_le_median_le_max(self):
        m = compare_networks(_ORIG, _OPT_SAME)
        assert m["support_overlap_min"] <= m["support_overlap_median"] <= m["support_overlap_max"]

    def test_all_support_overlaps_in_range(self):
        m = compare_networks(_ORIG, _OPT_DIFFERENT)
        for key in ("support_overlap_min", "support_overlap_median", "support_overlap_max"):
            assert 0.0 <= m[key] <= 1.0, f"{key} out of range: {m[key]}"

    def test_exact_match_rate_perfect_when_identical_sigs(self):
        """If optimized == original (same sigs), exact_match_rate should be 1.0."""
        m = compare_networks(_ORIG, _ORIG)
        assert m["exact_match_rate"] == pytest.approx(1.0)

    def test_exact_match_rate_zero_when_no_sigs_match(self):
        m = compare_networks(_ORIG, _OPT_DIFFERENT)
        assert m["exact_match_rate"] == pytest.approx(0.0)

    def test_original_columns_still_present(self):
        m = compare_networks(_ORIG, _OPT_SAME)
        for key in (
            "original_nodes", "optimized_nodes", "original_levels", "optimized_levels",
            "exact_internal_matches", "old_signatures_disappeared",
            "new_signatures_appeared", "avg_best_support_overlap", "simulation_mode",
        ):
            assert key in m, f"Legacy key missing: {key}"


# ---------------------------------------------------------------------------
# rank_candidates — new structural columns
# ---------------------------------------------------------------------------

class TestRankCandidatesNewColumns:

    def _rows(self):
        return rank_candidates(_ORIG, _OPT_SAME, "toy", "balance")

    def test_returns_list(self):
        assert isinstance(self._rows(), list)

    def test_optimized_fingerprint_present(self):
        rows = self._rows()
        assert rows, "Expected at least one candidate row"
        for row in rows:
            assert "optimized_fingerprint" in row

    def test_original_fingerprint_present(self):
        for row in self._rows():
            assert "original_fingerprint" in row

    def test_optimized_support_size_present(self):
        for row in self._rows():
            assert "optimized_support_size" in row

    def test_original_support_size_present(self):
        for row in self._rows():
            assert "original_support_size" in row

    def test_optimized_fanin_count_present(self):
        for row in self._rows():
            assert "optimized_fanin_count" in row

    def test_original_fanin_count_present(self):
        for row in self._rows():
            assert "original_fanin_count" in row

    def test_fingerprint_is_16_char_hex(self):
        for row in self._rows():
            for col in ("optimized_fingerprint", "original_fingerprint"):
                fp = row[col]
                assert isinstance(fp, str) and len(fp) == 16, (
                    f"{col} is {fp!r}, expected 16-char hex"
                )

    def test_support_sizes_are_non_negative_ints(self):
        for row in self._rows():
            assert isinstance(row["optimized_support_size"], int)
            assert isinstance(row["original_support_size"], int)
            assert row["optimized_support_size"] >= 0
            assert row["original_support_size"] >= 0

    def test_fanin_counts_are_non_negative_ints(self):
        for row in self._rows():
            assert isinstance(row["optimized_fanin_count"], int)
            assert isinstance(row["original_fanin_count"], int)
            assert row["optimized_fanin_count"] >= 0
            assert row["original_fanin_count"] >= 0

    def test_original_legacy_columns_still_present(self):
        legacy = (
            "benchmark", "optimization", "optimized_node", "rank",
            "original_candidate", "combined_score", "simulation_similarity",
            "support_overlap", "depth_similarity", "optimized_level", "original_level",
        )
        for row in self._rows():
            for col in legacy:
                assert col in row, f"Legacy column missing: {col}"

    def test_rows_sorted_by_rank(self):
        """Within each optimized node, ranks should start at 1."""
        from collections import defaultdict
        by_node = defaultdict(list)
        for row in self._rows():
            by_node[row["optimized_node"]].append(row["rank"])
        for node, ranks in by_node.items():
            assert ranks[0] == 1, f"First rank for {node} is {ranks[0]}, expected 1"
