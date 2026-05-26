"""
tests/test_import_real_benchmarks.py

Unit tests for scripts/import_real_benchmarks.py:
  - _parse_blif_stats: correct node/input/output counts from BLIF text
  - validate_blif: accepts valid files, rejects files missing required keywords
  - import_iscas85: copies valid files, skips invalid ones, creates output dir
  - _list_real_benchmarks: runs without error on the actual benchmarks/real/ dir
  - _yosys_available: returns a bool (no crash)
"""

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).parent.parent
_SCRIPTS_DIR = _REPO_ROOT / "scripts"


def _import_irb():
    if str(_SCRIPTS_DIR) not in sys.path:
        sys.path.insert(0, str(_SCRIPTS_DIR))
    import importlib
    import import_real_benchmarks as irb
    importlib.reload(irb)
    return irb


_VALID_BLIF = ".model test\n.inputs a b c\n.outputs y\n.names a b c y\n111 1\n.end\n"
_INVALID_BLIF_NO_INPUTS = ".model test\n.outputs y\n.names y\n1\n.end\n"


# ── _parse_blif_stats ─────────────────────────────────────────────────────────

class TestParseBlifStats:
    def test_counts_inputs(self, tmp_path):
        irb = _import_irb()
        p = tmp_path / "test.blif"; p.write_text(_VALID_BLIF)
        assert irb._parse_blif_stats(p)["inputs"] == 3

    def test_counts_outputs(self, tmp_path):
        irb = _import_irb()
        blif = ".model t\n.inputs a b\n.outputs y z\n.names a b y\n11 1\n.names a b z\n00 1\n.end\n"
        p = tmp_path / "test.blif"; p.write_text(blif)
        assert irb._parse_blif_stats(p)["outputs"] == 2

    def test_counts_nodes(self, tmp_path):
        irb = _import_irb()
        blif = ".model t\n.inputs a b c\n.outputs y\n.names a b t1\n11 1\n.names t1 c y\n11 1\n.end\n"
        p = tmp_path / "test.blif"; p.write_text(blif)
        assert irb._parse_blif_stats(p)["nodes"] == 2

    def test_name_from_stem(self, tmp_path):
        irb = _import_irb()
        p = tmp_path / "mymodule.blif"; p.write_text(_VALID_BLIF)
        assert irb._parse_blif_stats(p)["name"] == "mymodule"


# ── validate_blif ─────────────────────────────────────────────────────────────

class TestValidateBlif:
    def test_valid_file_no_errors(self, tmp_path):
        irb = _import_irb()
        p = tmp_path / "ok.blif"; p.write_text(_VALID_BLIF)
        assert irb.validate_blif(p) == []

    def test_missing_inputs_keyword(self, tmp_path):
        irb = _import_irb()
        p = tmp_path / "bad.blif"; p.write_text(_INVALID_BLIF_NO_INPUTS)
        assert any(".inputs" in e for e in irb.validate_blif(p))

    def test_missing_model_keyword(self, tmp_path):
        irb = _import_irb()
        p = tmp_path / "bad.blif"; p.write_text(".inputs a\n.outputs y\n.names a y\n1 1\n.end\n")
        assert any(".model" in e for e in irb.validate_blif(p))

    def test_missing_end_keyword(self, tmp_path):
        irb = _import_irb()
        p = tmp_path / "bad.blif"; p.write_text(".model m\n.inputs a\n.outputs y\n.names a y\n1 1\n")
        assert any(".end" in e for e in irb.validate_blif(p))

    def test_empty_file_has_multiple_errors(self, tmp_path):
        irb = _import_irb()
        p = tmp_path / "empty.blif"; p.write_text("")
        assert len(irb.validate_blif(p)) >= 4


# ── import_iscas85 ────────────────────────────────────────────────────────────

class TestImportIscas85:
    def test_copies_valid_blif(self, tmp_path):
        irb = _import_irb()
        src = tmp_path / "src"; src.mkdir()
        (src / "c17.blif").write_text(_VALID_BLIF)
        dst = tmp_path / "dst"
        irb.import_iscas85(src, dst)
        assert (dst / "c17.blif").exists()

    def test_skips_invalid_blif(self, tmp_path):
        irb = _import_irb()
        src = tmp_path / "src"; src.mkdir()
        (src / "bad.blif").write_text(_INVALID_BLIF_NO_INPUTS)
        dst = tmp_path / "dst"
        irb.import_iscas85(src, dst)
        assert not (dst / "bad.blif").exists()

    def test_creates_output_dir(self, tmp_path):
        irb = _import_irb()
        src = tmp_path / "src"; src.mkdir()
        (src / "c17.blif").write_text(_VALID_BLIF)
        dst = tmp_path / "new" / "nested" / "dir"
        assert not dst.exists()
        irb.import_iscas85(src, dst)
        assert dst.is_dir()

    def test_empty_source_prints_message(self, tmp_path, capsys):
        irb = _import_irb()
        src = tmp_path / "empty_src"; src.mkdir()
        irb.import_iscas85(src, tmp_path / "dst")
        assert "No .blif" in capsys.readouterr().out

    def test_copies_multiple_files(self, tmp_path):
        irb = _import_irb()
        src = tmp_path / "src"; src.mkdir()
        for name in ["c17.blif", "c432.blif", "c499.blif"]:
            (src / name).write_text(_VALID_BLIF)
        dst = tmp_path / "dst"
        irb.import_iscas85(src, dst)
        assert len(list(dst.glob("*.blif"))) == 3

    def test_mixed_valid_and_invalid(self, tmp_path):
        irb = _import_irb()
        src = tmp_path / "src"; src.mkdir()
        (src / "good.blif").write_text(_VALID_BLIF)
        (src / "bad.blif").write_text(_INVALID_BLIF_NO_INPUTS)
        dst = tmp_path / "dst"
        irb.import_iscas85(src, dst)
        copied = list(dst.glob("*.blif"))
        assert len(copied) == 1 and copied[0].name == "good.blif"


# ── _list_real_benchmarks ─────────────────────────────────────────────────────

class TestListRealBenchmarks:
    def test_runs_on_real_dir(self, capsys):
        irb = _import_irb()
        irb._list_real_benchmarks(_REPO_ROOT / "benchmarks" / "real")
        assert capsys.readouterr().out.count(".blif") >= 4

    def test_prints_no_blif_message_for_empty_dir(self, tmp_path, capsys):
        irb = _import_irb()
        irb._list_real_benchmarks(tmp_path)
        assert "No BLIF" in capsys.readouterr().out


# ── _yosys_available ──────────────────────────────────────────────────────────

class TestYosysAvailable:
    def test_returns_bool(self):
        assert isinstance(_import_irb()._yosys_available(), bool)
