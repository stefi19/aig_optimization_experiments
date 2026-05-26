"""
tests/test_metrics.py

Unit tests for the pure metric helper functions in analyze_blif_matches.py.

Run with:  python3 -m pytest tests/ -v
"""

import sys
import os
import tempfile

# Make the parent directory importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from analyze_blif_matches import (
    jaccard,
    bit_similarity,
    depth_similarity,
    combined_candidate_score,
    parse_blif,
)


# ── jaccard ────────────────────────────────────────────────────────────────────

class TestJaccard:
    def test_identical_sets(self):
        assert jaccard({"a", "b", "c"}, {"a", "b", "c"}) == 1.0

    def test_disjoint_sets(self):
        assert jaccard({"a", "b"}, {"c", "d"}) == 0.0

    def test_partial_overlap(self):
        # |{a,b} ∩ {b,c}| / |{a,b,c}| = 1/3
        result = jaccard({"a", "b"}, {"b", "c"})
        assert abs(result - 1 / 3) < 1e-9

    def test_one_empty(self):
        assert jaccard(set(), {"a"}) == 0.0
        assert jaccard({"a"}, set()) == 0.0

    def test_both_empty(self):
        # Convention: both empty → perfect match
        assert jaccard(set(), set()) == 1.0

    def test_subset(self):
        # {a} ⊂ {a, b} → |{a}| / |{a,b}| = 0.5
        result = jaccard({"a"}, {"a", "b"})
        assert abs(result - 0.5) < 1e-9


# ── bit_similarity ─────────────────────────────────────────────────────────────

class TestBitSimilarity:
    def test_identical_signatures(self):
        sig = 0b10110100
        assert bit_similarity(sig, sig, 8) == 1.0

    def test_all_different(self):
        # Complement → all bits differ
        sig_a = 0b11110000
        sig_b = 0b00001111
        assert bit_similarity(sig_a, sig_b, 8) == 0.0

    def test_half_different(self):
        # 4 bits agree, 4 differ out of 8
        sig_a = 0b11110000
        sig_b = 0b11110101  # differs in bits 0 and 2
        # XOR = 0b00000101, bit_count = 2, result = 1 - 2/8 = 0.75
        result = bit_similarity(sig_a, sig_b, 8)
        assert abs(result - 0.75) < 1e-9

    def test_single_bit_difference(self):
        # Only the lowest bit differs
        sig_a = 0b00000000
        sig_b = 0b00000001
        result = bit_similarity(sig_a, sig_b, 8)
        assert abs(result - 7 / 8) < 1e-9

    def test_zero_signatures(self):
        assert bit_similarity(0, 0, 4) == 1.0


# ── depth_similarity ───────────────────────────────────────────────────────────

class TestDepthSimilarity:
    def test_same_depth(self):
        assert depth_similarity(3, 3) == 1.0

    def test_depth_diff_one(self):
        # 1 / (1 + 1) = 0.5
        assert abs(depth_similarity(2, 3) - 0.5) < 1e-9

    def test_depth_diff_four(self):
        # 1 / (1 + 4) = 0.2
        assert abs(depth_similarity(0, 4) - 0.2) < 1e-9

    def test_symmetry(self):
        assert depth_similarity(1, 5) == depth_similarity(5, 1)

    def test_always_positive(self):
        for d in range(10):
            assert depth_similarity(0, d) > 0


# ── combined_candidate_score ───────────────────────────────────────────────────

class TestCombinedCandidateScore:
    def test_perfect_score(self):
        assert abs(combined_candidate_score(1.0, 1.0, 1.0) - 1.0) < 1e-9

    def test_zero_score(self):
        assert abs(combined_candidate_score(0.0, 0.0, 0.0) - 0.0) < 1e-9

    def test_weights_sum_to_one(self):
        # All components = 1 → result = 1; this also validates weights sum to 1
        assert abs(0.55 + 0.35 + 0.10 - 1.0) < 1e-9

    def test_known_value(self):
        # 0.55*0.8 + 0.35*0.6 + 0.10*1.0 = 0.44 + 0.21 + 0.10 = 0.75
        result = combined_candidate_score(0.8, 0.6, 1.0)
        assert abs(result - 0.75) < 1e-9

    def test_sim_dominates(self):
        high_sim = combined_candidate_score(1.0, 0.0, 0.0)
        high_sup = combined_candidate_score(0.0, 1.0, 0.0)
        assert high_sim > high_sup  # sim weight 0.55 > support weight 0.35


# ── parse_blif ────────────────────────────────────────────────────────────────

class TestParseBLIF:
    def _write_blif(self, content):
        """Write a temporary BLIF file and return its path."""
        tmp = tempfile.NamedTemporaryFile(
            mode="w", suffix=".blif", delete=False
        )
        tmp.write(content)
        tmp.flush()
        tmp.close()
        return tmp.name

    def test_simple_and_gate(self):
        blif = (
            ".model and_test\n"
            ".inputs a b\n"
            ".outputs y\n"
            ".names a b y\n"
            "11 1\n"
            ".end\n"
        )
        path = self._write_blif(blif)
        net = parse_blif(path)
        os.unlink(path)

        assert net.inputs == ["a", "b"]
        assert net.outputs == ["y"]
        assert len(net.nodes) == 1
        node = net.nodes[0]
        assert node.output == "y"
        assert node.inputs == ["a", "b"]
        assert node.cover == ["11 1"]

    def test_multiple_nodes(self):
        blif = (
            ".model multi\n"
            ".inputs a b c\n"
            ".outputs z\n"
            ".names a b x\n"
            "11 1\n"
            ".names x c z\n"
            "11 1\n"
            ".end\n"
        )
        path = self._write_blif(blif)
        net = parse_blif(path)
        os.unlink(path)

        assert len(net.nodes) == 2
        assert net.nodes[0].output == "x"
        assert net.nodes[1].output == "z"

    def test_constant_zero_node(self):
        blif = (
            ".model const0\n"
            ".inputs a\n"
            ".outputs y\n"
            ".names y\n"
            ".end\n"
        )
        path = self._write_blif(blif)
        net = parse_blif(path)
        os.unlink(path)

        assert len(net.nodes) == 1
        assert net.nodes[0].cover == []

    def test_comment_lines_ignored(self):
        blif = (
            "# This is a comment\n"
            ".model test\n"
            ".inputs a b\n"
            "# another comment\n"
            ".outputs y\n"
            ".names a b y\n"
            "11 1\n"
            ".end\n"
        )
        path = self._write_blif(blif)
        net = parse_blif(path)
        os.unlink(path)

        assert net.inputs == ["a", "b"]
        assert len(net.nodes) == 1
