"""
tests/test_source_family.py

Unit tests for scripts/benchmark_id.py::infer_source_family (research iteration 2).
"""

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).parent.parent
_SCRIPTS_DIR = _REPO_ROOT / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

import benchmark_id as bm


class TestInferSourceFamily:
    def test_external_iscas85(self):
        assert bm.infer_source_family("external_iscas85_c17") == "iscas85"

    def test_external_epfl(self):
        assert bm.infer_source_family("external_epfl_adder") == "epfl"

    def test_generated(self):
        assert bm.infer_source_family("generated_adder_4") == "generated"

    def test_custom_real(self):
        assert bm.infer_source_family("real_hand_written_full_adder") == "custom"

    def test_legacy_real_iscas85(self):
        # Back-compat: ISCAS-85 files previously lived under benchmarks/real/.
        assert bm.infer_source_family("real_iscas85_c432") == "iscas85"

    def test_toy_bare_names(self):
        for bid in ("majority3", "mux2", "toy_and_or", "xor_chain"):
            assert bm.infer_source_family(bid) == "toy"

    def test_case_insensitive(self):
        assert bm.infer_source_family("EXTERNAL_ISCAS85_C17") == "iscas85"

    def test_full_path_via_blif_to_id(self):
        bid = bm.blif_to_id("benchmarks/external/iscas85/c17.blif")
        assert bm.infer_source_family(bid) == "iscas85"
