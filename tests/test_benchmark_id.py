"""
tests/test_benchmark_id.py

Unit tests for scripts/benchmark_id.py:
  - blif_to_id: converts BLIF paths to collision-free string IDs
"""

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).parent.parent
_SCRIPTS_DIR = _REPO_ROOT / "scripts"

if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

import benchmark_id as bm


class TestBlifToId:
    def test_top_level_benchmark(self):
        assert bm.blif_to_id("benchmarks/majority3.blif") == "majority3"

    def test_real_hand_written(self):
        assert (
            bm.blif_to_id("benchmarks/real/hand_written/full_adder.blif")
            == "real_hand_written_full_adder"
        )

    def test_generated_subdir(self):
        assert (
            bm.blif_to_id("benchmarks/generated/xor_chain_8.blif")
            == "generated_xor_chain_8"
        )

    def test_absolute_path_converted(self):
        # Absolute paths should also work; strip anything up to and including 'benchmarks/'
        p = str(_REPO_ROOT / "benchmarks" / "mux2.blif")
        result = bm.blif_to_id(p)
        assert result == "mux2"

    def test_leading_dotslash_stripped(self):
        assert bm.blif_to_id("./benchmarks/toy_and_or.blif") == "toy_and_or"

    def test_path_object_accepted(self):
        result = bm.blif_to_id(Path("benchmarks/xor_chain.blif"))
        assert result == "xor_chain"

    def test_hyphens_replaced_with_underscores(self):
        result = bm.blif_to_id("benchmarks/real/hand_written/half-adder.blif")
        assert result == "real_hand_written_half_adder"

    def test_spaces_replaced_with_underscores(self):
        result = bm.blif_to_id("benchmarks/my circuit.blif")
        assert result == "my_circuit"

    def test_no_double_underscores(self):
        # Two consecutive non-alphanumeric chars should collapse to one underscore
        result = bm.blif_to_id("benchmarks/a--b.blif")
        assert "__" not in result

    def test_no_leading_or_trailing_underscores(self):
        result = bm.blif_to_id("benchmarks/majority3.blif")
        assert not result.startswith("_") and not result.endswith("_")
