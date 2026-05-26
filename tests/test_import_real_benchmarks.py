"""
tests/test_import_real_benchmarks.py

Unit tests for scripts/import_real_benchmarks.py:
  - _parse_blif_stats: correct node/input/output counts from BLIF text
  - _list_real_benchmarks: runs without error on the actual benchmarks/real/ dir
  - _yosys_available: returns a bool (no crash)
"""

import sys
import textwrap
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).parent.parent
_SCRIPTS_DIR = _REPO_ROOT / "scripts"


def _import_irb():
    if str(_SCRIPTS_DIR) not in sys.path:
        sys.path.insert(0, str(_SCRIPTS_DIR))
    import importlib
    import import_real_benchmarks as irb
    importlib.reload(irb)
    return irb


# ── _parse_blif_stats ─────────────────────────────────────────────────────────

class TestParseBlifStats:
    def _write_blif(self, tmp_path, content):
        p = tmp_path / "test.blif"
        p.write_text(textwrap.dedent(content))
        return p

    def test_counts_inputs(self, tmp_path):
        irb = _import_irb()
        p = self._write_blif(tmp_path, """\
            .model test
            .inputs a b c
            .outputs y
            .names a b c y
            111 1
            .end
        """)
        s = irb._parse_blif_stats(p)
        assert s["inputs"] == 3

    def test_counts_outputs(self, tmp_path):
        irb = _import_irb()
        p = self._write_blif(tmp_path, """\
            .model test
            .inputs a b
            .outputs y z
            .names a b y
            11 1
            .names a b z
            00 1
            .end
        """)
        s = irb._parse_blif_stats(p)
        assert s["outputs"] == 2

    def test_counts_nodes(self, tmp_path):
        irb = _import_irb()
        p = self._write_blif(tmp_path, """\
            .model test
            .inputs a b c
            .outputs y
            .names a b t1
            11 1
            .names t1 c y
            11 1
            .end
        """)
        s = irb._parse_blif_stats(p)
        # two .names lines → 2 nodes
        assert s["nodes"] == 2

    def test_name_from_stem(self, tmp_path):
        irb = _import_irb()
        p = self._write_blif(tmp_path, """\
            .model mymod
            .inputs x
            .outputs y
            .names x y
            1 1
            .end
        """)
        s = irb._parse_blif_stats(p)
        assert s["name"] == "test"   # from path.stem, not .model line


# ── _list_real_benchmarks ─────────────────────────────────────────────────────

class TestListRealBenchmarks:
    def test_runs_on_real_dir(self, capsys):
        irb = _import_irb()
        real_dir = _REPO_ROOT / "benchmarks" / "real"
        irb._list_real_benchmarks(real_dir)
        captured = capsys.readouterr()
        # Should print at least 4 benchmark rows
        assert captured.out.count(".blif") >= 4

    def test_prints_no_blif_message_for_empty_dir(self, tmp_path, capsys):
        irb = _import_irb()
        irb._list_real_benchmarks(tmp_path)
        captured = capsys.readouterr()
        assert "No BLIF" in captured.out


# ── _yosys_available ──────────────────────────────────────────────────────────

class TestYosysAvailable:
    def test_returns_bool(self):
        irb = _import_irb()
        result = irb._yosys_available()
        assert isinstance(result, bool)
