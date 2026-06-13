"""
tests/test_import_external_benchmarks.py

Unit tests for scripts/import_external_benchmarks.py (research iteration 2).
Network and external tools (ABC/Yosys) are never invoked: only BLIF copy and
validation paths are exercised.
"""

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).parent.parent
_SCRIPTS_DIR = _REPO_ROOT / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))


def _import_mod():
    import importlib
    import import_external_benchmarks as ieb
    importlib.reload(ieb)
    return ieb


_VALID = ".model t\n.inputs a b\n.outputs y\n.names a b y\n11 1\n.end\n"
_INVALID = ".model t\n.outputs y\n.end\n"  # missing .inputs


class TestValidateBlif:
    def test_valid(self, tmp_path):
        ieb = _import_mod()
        p = tmp_path / "ok.blif"
        p.write_text(_VALID)
        assert ieb.validate_blif(p) == []

    def test_invalid(self, tmp_path):
        ieb = _import_mod()
        p = tmp_path / "bad.blif"
        p.write_text(_INVALID)
        errors = ieb.validate_blif(p)
        assert any(".inputs" in e for e in errors)


class TestImportFamily:
    def test_copies_valid_skips_invalid(self, tmp_path, monkeypatch):
        ieb = _import_mod()
        in_dir = tmp_path / "src"
        in_dir.mkdir()
        (in_dir / "c17.blif").write_text(_VALID)
        (in_dir / "broken.blif").write_text(_INVALID)

        ext_root = tmp_path / "external"
        monkeypatch.setattr(ieb, "EXTERNAL_ROOT", ext_root)

        placed = ieb.import_family("iscas85", in_dir,
                                   convert_aiger_flag=False,
                                   convert_verilog_flag=False)
        assert placed == 1
        assert (ext_root / "iscas85" / "c17.blif").exists()
        assert not (ext_root / "iscas85" / "broken.blif").exists()

    def test_no_files(self, tmp_path, monkeypatch):
        ieb = _import_mod()
        in_dir = tmp_path / "empty"
        in_dir.mkdir()
        monkeypatch.setattr(ieb, "EXTERNAL_ROOT", tmp_path / "external")
        placed = ieb.import_family("epfl", in_dir, False, False)
        assert placed == 0

    def test_discovers_nested_blifs_recursively(self, tmp_path, monkeypatch):
        ieb = _import_mod()
        in_dir = tmp_path / "suite"
        nested = in_dir / "arithmetic" / "small"
        nested.mkdir(parents=True)
        (nested / "c17.blif").write_text(_VALID)

        ext_root = tmp_path / "external"
        monkeypatch.setattr(ieb, "EXTERNAL_ROOT", ext_root)

        placed = ieb.import_family("iscas85", in_dir, False, False)
        assert placed == 1
        assert (ext_root / "iscas85" / "c17.blif").exists()

    def test_discovery_order_is_deterministic_and_skips_hidden_dirs(self, tmp_path):
        ieb = _import_mod()
        in_dir = tmp_path / "suite"
        (in_dir / "z").mkdir(parents=True)
        (in_dir / "a").mkdir()
        (in_dir / ".cache").mkdir()
        (in_dir / "z" / "late.blif").write_text(_VALID)
        (in_dir / "a" / "early.blif").write_text(_VALID)
        (in_dir / ".cache" / "hidden.blif").write_text(_VALID)

        found = ieb._discover_files(in_dir, ieb.BLIF_EXTENSIONS)
        assert [p.relative_to(in_dir).as_posix() for p in found] == [
            "a/early.blif",
            "z/late.blif",
        ]

    def test_discovers_aiger_and_systemverilog_extensions(self, tmp_path):
        ieb = _import_mod()
        in_dir = tmp_path / "suite"
        nested = in_dir / "nested"
        nested.mkdir(parents=True)
        (nested / "adder.aiger").write_text("aiger placeholder")
        (nested / "control.sv").write_text("module control; endmodule")

        aigers = ieb._discover_files(in_dir, ieb.AIGER_EXTENSIONS)
        hdls = ieb._discover_files(in_dir, ieb.VERILOG_EXTENSIONS)

        assert [p.name for p in aigers] == ["adder.aiger"]
        assert [p.name for p in hdls] == ["control.sv"]


class TestListExternal:
    def test_runs_without_error(self, capsys, monkeypatch, tmp_path):
        ieb = _import_mod()
        monkeypatch.setattr(ieb, "EXTERNAL_ROOT", tmp_path / "external")
        ieb.list_external()
        out = capsys.readouterr().out
        assert "external" in out.lower()
