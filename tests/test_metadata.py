"""
tests/test_metadata.py

Tests for the benchmark family and optimization group inference helpers
added to analyze_blif_matches.py.

Run with:  python3 -m pytest tests/ -v
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from analyze_blif_matches import infer_benchmark_family, infer_optimization_group


# ── infer_benchmark_family ─────────────────────────────────────────────────────

class TestInferBenchmarkFamily:

    # --- XOR chain family ---
    def test_xor_chain_exact(self):
        assert infer_benchmark_family("xor_chain") == "xor_chain"

    def test_xor_chain_with_size(self):
        assert infer_benchmark_family("xor_chain_8") == "xor_chain"

    def test_xor_chain_large(self):
        assert infer_benchmark_family("xor_chain_32") == "xor_chain"

    # --- MUX tree family ---
    def test_mux_tree_exact(self):
        assert infer_benchmark_family("mux_tree") == "mux_tree"

    def test_mux_tree_with_size(self):
        assert infer_benchmark_family("mux_tree_4") == "mux_tree"

    def test_mux_tree_16(self):
        assert infer_benchmark_family("mux_tree_16") == "mux_tree"

    # mux prefix should NOT match mux_tree (mux_tree is longer and matched first)
    def test_mux_simple_name(self):
        assert infer_benchmark_family("mux2") == "toy"

    # --- Adder family ---
    def test_adder_4(self):
        assert infer_benchmark_family("adder_4") == "adder"

    def test_adder_8(self):
        assert infer_benchmark_family("adder_8") == "adder"

    # --- Multiplier family ---
    def test_multiplier_2(self):
        assert infer_benchmark_family("multiplier_2") == "multiplier"

    def test_multiplier_4(self):
        assert infer_benchmark_family("multiplier_4") == "multiplier"

    # --- Random family ---
    def test_random_small(self):
        assert infer_benchmark_family("random_small") == "random"

    def test_random_medium(self):
        assert infer_benchmark_family("random_medium") == "random"

    # --- Toy family (hand-written benchmarks) ---
    def test_majority3(self):
        assert infer_benchmark_family("majority3") == "toy"

    def test_toy_and_or(self):
        assert infer_benchmark_family("toy_and_or") == "toy"

    # --- Unknown family ---
    def test_unknown_name(self):
        assert infer_benchmark_family("weird_circuit_v2") == "unknown"

    def test_empty_string(self):
        assert infer_benchmark_family("") == "unknown"

    # --- Case insensitivity ---
    def test_uppercase_xor(self):
        # Benchmark names from files are lowercased before matching.
        assert infer_benchmark_family("XOR_CHAIN_8") == "xor_chain"

    def test_mixed_case(self):
        assert infer_benchmark_family("Adder_4") == "adder"


# ── infer_optimization_group ───────────────────────────────────────────────────

class TestInferOptimizationGroup:

    def test_original_is_none(self):
        assert infer_optimization_group("original") == "none"

    def test_balance_is_low(self):
        assert infer_optimization_group("balance") == "low"

    def test_rewrite_is_medium(self):
        assert infer_optimization_group("rewrite") == "medium"

    def test_refactor_is_medium(self):
        assert infer_optimization_group("refactor") == "medium"

    def test_rewrite_z_is_medium(self):
        assert infer_optimization_group("rewrite_z") == "medium"

    def test_refactor_z_is_medium(self):
        assert infer_optimization_group("refactor_z") == "medium"

    def test_resub_is_high(self):
        assert infer_optimization_group("resub") == "high"

    def test_resyn_is_high(self):
        assert infer_optimization_group("resyn") == "high"

    def test_resyn2_is_very_high(self):
        assert infer_optimization_group("resyn2") == "very_high"

    def test_resyn2_like_is_very_high(self):
        assert infer_optimization_group("resyn2_like") == "very_high"

    def test_dc2_is_very_high(self):
        assert infer_optimization_group("dc2") == "very_high"

    def test_compress2rs_is_very_high(self):
        assert infer_optimization_group("compress2rs") == "very_high"

    def test_unknown_optimization(self):
        assert infer_optimization_group("some_new_pass") == "unknown"
