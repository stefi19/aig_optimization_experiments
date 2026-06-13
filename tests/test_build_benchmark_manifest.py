"""
tests/test_build_benchmark_manifest.py

Unit tests for scripts/build_benchmark_manifest.py (research iteration 2).
"""

import csv
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts import build_benchmark_manifest as bm


_BLIF_SMALL = ".model m\n.inputs a b c\n.outputs y\n.names a b y\n11 1\n.names y c z\n10 1\n.end\n"
_BLIF_WIDE = (
    ".model wide\n.inputs " + " ".join(f"i{n}" for n in range(20)) + "\n"
    ".outputs y\n.names i0 i1 y\n11 1\n.end\n"
)
_BLIF_WITH_CONTINUATIONS = (
    ".model continued\n"
    ".inputs i0 i1 i2 i3 i4 i5 i6 \\\n"
    "  i7 i8 i9 i10 i11 i12\n"
    ".outputs y0 \\\n"
    "  y1 y2\n"
    ".names i0 i1 y0\n"
    "11 1\n"
    ".names i2 i3 \\\n"
    "  y1\n"
    "11 1\n"
    ".end\n"
)


class TestParseBlifStats:
    def test_counts(self, tmp_path):
        p = tmp_path / "s.blif"
        p.write_text(_BLIF_SMALL)
        s = bm.parse_blif_stats(p)
        assert s == {"n_inputs": 3, "n_outputs": 1, "n_internal_nodes": 2}

    def test_counts_inputs_outputs_with_backslash_continuations(self, tmp_path):
        p = tmp_path / "continued.blif"
        p.write_text(_BLIF_WITH_CONTINUATIONS)
        s = bm.parse_blif_stats(p)
        assert s == {"n_inputs": 13, "n_outputs": 3, "n_internal_nodes": 2}

    def test_iter_logical_lines_joins_continuations(self, tmp_path):
        p = tmp_path / "continued.blif"
        p.write_text(_BLIF_WITH_CONTINUATIONS)
        lines = list(bm.iter_blif_logical_lines(p))
        assert ".inputs i0 i1 i2 i3 i4 i5 i6 i7 i8 i9 i10 i11 i12" in lines
        assert ".outputs y0 y1 y2" in lines


class TestBuildManifest:
    def test_rows_and_source_family(self, tmp_path):
        # blif_to_id strips up to and including 'benchmarks/', so scan a tree
        # that contains that segment (as the real layout does).
        root = tmp_path / "benchmarks"
        gen = root / "generated"
        ext = root / "external" / "iscas85"
        gen.mkdir(parents=True)
        ext.mkdir(parents=True)
        (gen / "adder_4.blif").write_text(_BLIF_SMALL)
        (ext / "c17.blif").write_text(_BLIF_SMALL)

        rows = bm.build_manifest(root)
        by_id = {r["benchmark"]: r for r in rows}

        assert by_id["generated_adder_4"]["source_family"] == "generated"
        assert by_id["external_iscas85_c17"]["source_family"] == "iscas85"

    def test_exact_mode_flag(self, tmp_path):
        small = tmp_path / "small.blif"
        wide = tmp_path / "wide.blif"
        small.write_text(_BLIF_SMALL)
        wide.write_text(_BLIF_WIDE)
        rows = {r["path"]: r for r in bm.build_manifest(tmp_path)}
        small_row = next(r for r in rows.values() if r["path"].endswith("small.blif"))
        wide_row = next(r for r in rows.values() if r["path"].endswith("wide.blif"))
        assert small_row["exact_mode_possible"] is True
        assert wide_row["exact_mode_possible"] is False
        assert "wide input cone" in wide_row["notes"]

    def test_exact_mode_flag_uses_continued_input_count(self, tmp_path):
        p = tmp_path / "continued.blif"
        p.write_text(_BLIF_WITH_CONTINUATIONS)
        row = bm.build_manifest(tmp_path)[0]
        assert row["n_inputs"] == 13
        assert row["exact_mode_possible"] is False
        assert "wide input cone (13 inputs)" in row["notes"]


class TestWriteManifest:
    def test_header_and_roundtrip(self, tmp_path):
        (tmp_path / "x.blif").write_text(_BLIF_SMALL)
        rows = bm.build_manifest(tmp_path)
        out = tmp_path / "manifest.csv"
        bm.write_manifest(rows, out)
        with out.open(newline="") as fh:
            reader = csv.DictReader(fh)
            assert reader.fieldnames == bm.FIELDS
            data = list(reader)
        assert len(data) == len(rows)
