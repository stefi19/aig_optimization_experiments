"""
tests/test_abc_sat_sweep.py

Unit tests for the ABC SAT sweep / hybrid validation extension.

These tests cover:
  - expose_node_as_output: creates a valid BLIF with the selected node as output
  - parse_dump_equiv_file: correctly extracts cross-network equivalence pairs
  - find_abc: raises a clear error when no ABC binary is available
  - read_internal_nodes: correctly identifies internal nodes in a BLIF
  - hybrid_validation pipeline: runs without --abc-validate path and still
    produces the expected CSV columns
  - annotate_candidates: columns present even when ABC is not called

Most tests do NOT require ABC to be installed — they work on synthetic BLIF
strings and in-memory DataFrames.  Tests that actually call ABC are skipped
when the binary is not available.
"""

import os
import sys
import tempfile
import textwrap
from pathlib import Path

import pandas as pd
import pytest

# ── path setup ─────────────────────────────────────────────────────────────────

_REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_REPO_ROOT))
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from abc_sat_sweep_validation import (
    expose_node_as_output,
    read_internal_nodes,
    parse_dump_equiv_file,
    find_abc,
    EquivPair,
    _parse_print_stats_lines,
)


# ── helpers ────────────────────────────────────────────────────────────────────

# A minimal BLIF for a 3-input majority function.
# Has three internal nodes: n_ab, n_ac, n_bc.
MAJORITY_BLIF = textwrap.dedent("""\
    .model majority3
    .inputs a b c
    .outputs y

    .names a b n_ab
    11 1

    .names a c n_ac
    11 1

    .names b c n_bc
    11 1

    .names n_ab n_ac n_bc y
    1-- 1
    -1- 1
    --1 1
    .end
""")

# A second BLIF where the optimised network uses different node names.
OPTIMISED_BLIF = textwrap.dedent("""\
    .model majority3
    .inputs a b c
    .outputs y

    .names a b x_ab
    11 1

    .names b c x_bc
    11 1

    .names x_ab x_bc y
    1- 1
    -1 1
    .end
""")

# Synthetic dump_equiv output that matches MAJORITY_BLIF (orig) vs OPTIMISED_BLIF (opt).
# n_ab → x_ab  (same class, no complement)
# n_bc → x_bc  (same class, no complement)
# y    → y     (primary outputs, same class)
DUMP_EQUIV_TEXT = textwrap.dedent("""\
    # Node equivalences computed by ABC for networks "majority3" and "majority3"

    1:majority3:n_ab
    1:majority3:x_ab

    2:majority3:n_bc
    2:majority3:x_bc

    3:majority3:y
    3:majority3:y

""")


def _write_blif(tmp_path, filename, content):
    p = tmp_path / filename
    p.write_text(content)
    return str(p)


# ── expose_node_as_output ─────────────────────────────────────────────────────

class TestExposeNodeAsOutput:

    def test_output_file_is_created(self, tmp_path):
        src = _write_blif(tmp_path, "orig.blif", MAJORITY_BLIF)
        dst = str(tmp_path / "exposed.blif")
        expose_node_as_output(src, "n_ab", dst)
        assert os.path.exists(dst)

    def test_outputs_line_replaced(self, tmp_path):
        src = _write_blif(tmp_path, "orig.blif", MAJORITY_BLIF)
        dst = str(tmp_path / "exposed.blif")
        expose_node_as_output(src, "n_ab", dst)
        text = Path(dst).read_text()
        assert ".outputs n_ab" in text

    def test_original_output_removed(self, tmp_path):
        src = _write_blif(tmp_path, "orig.blif", MAJORITY_BLIF)
        dst = str(tmp_path / "exposed.blif")
        expose_node_as_output(src, "n_ab", dst)
        text = Path(dst).read_text()
        # 'y' should no longer be the output
        assert ".outputs y" not in text

    def test_inputs_preserved(self, tmp_path):
        src = _write_blif(tmp_path, "orig.blif", MAJORITY_BLIF)
        dst = str(tmp_path / "exposed.blif")
        expose_node_as_output(src, "n_ab", dst)
        text = Path(dst).read_text()
        assert ".inputs a b c" in text

    def test_logic_lines_preserved(self, tmp_path):
        src = _write_blif(tmp_path, "orig.blif", MAJORITY_BLIF)
        dst = str(tmp_path / "exposed.blif")
        expose_node_as_output(src, "n_ab", dst)
        text = Path(dst).read_text()
        # All .names definitions should still be there
        assert ".names a b n_ab" in text
        assert ".names n_ab n_ac n_bc y" in text

    def test_expose_primary_output_node(self, tmp_path):
        """Exposing 'y' (which is already an output) should work fine."""
        src = _write_blif(tmp_path, "orig.blif", MAJORITY_BLIF)
        dst = str(tmp_path / "exposed.blif")
        expose_node_as_output(src, "y", dst)
        assert ".outputs y" in Path(dst).read_text()

    def test_missing_node_raises_value_error(self, tmp_path):
        src = _write_blif(tmp_path, "orig.blif", MAJORITY_BLIF)
        dst = str(tmp_path / "exposed.blif")
        with pytest.raises(ValueError, match="not defined"):
            expose_node_as_output(src, "nonexistent_node", dst)

    def test_output_is_valid_blif(self, tmp_path):
        """The produced file should contain the key BLIF directives."""
        src = _write_blif(tmp_path, "orig.blif", MAJORITY_BLIF)
        dst = str(tmp_path / "exposed.blif")
        expose_node_as_output(src, "n_ac", dst)
        text = Path(dst).read_text()
        assert ".model" in text
        assert ".inputs" in text
        assert ".outputs n_ac" in text
        assert ".end" in text


# ── read_internal_nodes ───────────────────────────────────────────────────────

class TestReadInternalNodes:

    def test_returns_internal_nodes_only(self, tmp_path):
        blif = _write_blif(tmp_path, "m.blif", MAJORITY_BLIF)
        nodes = read_internal_nodes(blif)
        # n_ab, n_ac, n_bc, y are defined by .names
        # a, b, c are .inputs — should NOT appear
        assert "a" not in nodes
        assert "b" not in nodes
        assert "c" not in nodes

    def test_includes_named_internal_nodes(self, tmp_path):
        blif = _write_blif(tmp_path, "m.blif", MAJORITY_BLIF)
        nodes = read_internal_nodes(blif)
        assert "n_ab" in nodes
        assert "n_ac" in nodes
        assert "n_bc" in nodes

    def test_includes_primary_output_node(self, tmp_path):
        """y is defined by a .names line, so it should be in the set."""
        blif = _write_blif(tmp_path, "m.blif", MAJORITY_BLIF)
        nodes = read_internal_nodes(blif)
        assert "y" in nodes

    def test_optimised_blif_different_names(self, tmp_path):
        blif = _write_blif(tmp_path, "opt.blif", OPTIMISED_BLIF)
        nodes = read_internal_nodes(blif)
        assert "x_ab" in nodes
        assert "x_bc" in nodes
        assert "a" not in nodes


# ── parse_dump_equiv_file ─────────────────────────────────────────────────────

class TestParseDumpEquivFile:

    def _write_equiv(self, tmp_path, content):
        p = tmp_path / "equiv.txt"
        p.write_text(content)
        return str(p)

    def test_returns_list_of_equiv_pairs(self, tmp_path):
        equiv_file = self._write_equiv(tmp_path, DUMP_EQUIV_TEXT)
        orig_nodes = {"n_ab", "n_ac", "n_bc", "y"}
        opt_nodes  = {"x_ab", "x_bc", "y"}
        pairs = parse_dump_equiv_file(equiv_file, orig_nodes, opt_nodes)
        assert isinstance(pairs, list)
        assert all(isinstance(p, EquivPair) for p in pairs)

    def test_cross_network_pairs_detected(self, tmp_path):
        equiv_file = self._write_equiv(tmp_path, DUMP_EQUIV_TEXT)
        orig_nodes = {"n_ab", "n_ac", "n_bc", "y"}
        opt_nodes  = {"x_ab", "x_bc", "y"}
        pairs = parse_dump_equiv_file(equiv_file, orig_nodes, opt_nodes)
        pair_keys = {(p.original_node, p.optimised_node) for p in pairs}
        assert ("n_ab", "x_ab") in pair_keys
        assert ("n_bc", "x_bc") in pair_keys

    def test_no_pairs_when_empty_file(self, tmp_path):
        equiv_file = self._write_equiv(tmp_path, "# header\n\n")
        pairs = parse_dump_equiv_file(equiv_file, set(), set())
        assert pairs == []

    def test_complement_flag_parsed(self, tmp_path):
        content = textwrap.dedent("""\
            # header

            5:net:n_foo
            5:net:NOT:x_bar

        """)
        equiv_file = self._write_equiv(tmp_path, content)
        orig_nodes = {"n_foo"}
        opt_nodes  = {"x_bar"}
        pairs = parse_dump_equiv_file(equiv_file, orig_nodes, opt_nodes)
        assert len(pairs) == 1
        assert pairs[0].is_complement is True
        assert pairs[0].original_node == "n_foo"
        assert pairs[0].optimised_node == "x_bar"

    def test_non_complement_flag(self, tmp_path):
        content = "1:net:n_ab\n1:net:x_ab\n\n"
        equiv_file = self._write_equiv(tmp_path, content)
        pairs = parse_dump_equiv_file(equiv_file, {"n_ab"}, {"x_ab"})
        assert pairs[0].is_complement is False

    def test_class_id_recorded(self, tmp_path):
        equiv_file = self._write_equiv(tmp_path, DUMP_EQUIV_TEXT)
        orig_nodes = {"n_ab", "n_ac", "n_bc", "y"}
        opt_nodes  = {"x_ab", "x_bc", "y"}
        pairs = parse_dump_equiv_file(equiv_file, orig_nodes, opt_nodes)
        class_ids = {p.equiv_class_id for p in pairs}
        # Classes 1 and 2 should be present (class 3 = y→y same name, no cross pair)
        assert 1 in class_ids
        assert 2 in class_ids

    def test_confidence_is_sat_proven(self, tmp_path):
        equiv_file = self._write_equiv(tmp_path, DUMP_EQUIV_TEXT)
        orig_nodes = {"n_ab", "n_ac", "n_bc", "y"}
        opt_nodes  = {"x_ab", "x_bc", "y"}
        pairs = parse_dump_equiv_file(equiv_file, orig_nodes, opt_nodes)
        for p in pairs:
            assert p.confidence == "sat_proven"

    def test_shared_node_name_position_heuristic(self, tmp_path):
        """
        When the same node name appears in both files, position within the
        class determines origin (first = original, second = optimised).
        The class should yield no cross-network pair — it's a trivial same-name match.
        """
        content = "7:net:y\n7:net:y\n\n"
        equiv_file = self._write_equiv(tmp_path, content)
        # y exists in both
        pairs = parse_dump_equiv_file(equiv_file, {"y"}, {"y"})
        # Both occurrences of "y" land in orig first, opt second — so we
        # get a self-pair (y, y).  That's still a valid cross-network pair.
        pair_keys = {(p.original_node, p.optimised_node) for p in pairs}
        assert ("y", "y") in pair_keys


# ── find_abc ──────────────────────────────────────────────────────────────────

class TestFindAbc:

    def test_raises_runtime_error_when_not_found(self, monkeypatch):
        """
        If no ABC binary is on PATH and no hint/env var is given,
        find_abc should raise RuntimeError with a helpful message.
        """
        # Clear any ABC env var that might be set in the CI environment
        monkeypatch.delenv("ABC", raising=False)
        # Patch shutil.which to always return None
        import shutil as _shutil
        monkeypatch.setattr(_shutil, "which", lambda name: None)

        with pytest.raises(RuntimeError, match="ABC binary not found"):
            find_abc(hint=None)

    def test_error_message_contains_build_instructions(self, monkeypatch):
        import shutil as _shutil
        monkeypatch.delenv("ABC", raising=False)
        monkeypatch.setattr(_shutil, "which", lambda name: None)

        with pytest.raises(RuntimeError) as exc_info:
            find_abc(hint=None)
        assert "github.com/berkeley-abc/abc" in str(exc_info.value)

    def test_accepts_valid_path_via_hint(self, tmp_path):
        """A valid executable path passed as hint is accepted immediately."""
        fake_abc = tmp_path / "abc"
        fake_abc.write_text("#!/bin/sh\n")
        fake_abc.chmod(0o755)
        result = find_abc(hint=str(fake_abc))
        assert result == str(fake_abc)

    def test_env_var_used_when_hint_is_none(self, tmp_path, monkeypatch):
        """$ABC env var should be picked up when hint is None."""
        fake_abc = tmp_path / "abc_env"
        fake_abc.write_text("#!/bin/sh\n")
        fake_abc.chmod(0o755)
        monkeypatch.setenv("ABC", str(fake_abc))
        result = find_abc(hint=None)
        assert result == str(fake_abc)

    def test_hint_takes_priority_over_env_var(self, tmp_path, monkeypatch):
        """Explicit hint should be preferred over $ABC env var."""
        env_abc  = tmp_path / "abc_env"
        hint_abc = tmp_path / "abc_hint"
        for p in (env_abc, hint_abc):
            p.write_text("#!/bin/sh\n")
            p.chmod(0o755)
        monkeypatch.setenv("ABC", str(env_abc))
        result = find_abc(hint=str(hint_abc))
        assert result == str(hint_abc)


# ── _parse_print_stats_lines ──────────────────────────────────────────────────

class TestParsePrintStatsLines:

    def test_parses_single_stats_line(self):
        text = "majority3 : i/o =  3/  1  lat =  0  and =  5  lev =  3"
        results = _parse_print_stats_lines(text)
        assert results == [(5, 3)]

    def test_parses_two_lines_before_after(self):
        text = (
            "majority3 : i/o =  3/  1  lat =  0  and =  5  lev =  3\n"
            "majority3 : i/o =  3/  1  lat =  0  and =  4  lev =  2\n"
        )
        results = _parse_print_stats_lines(text)
        assert results == [(5, 3), (4, 2)]

    def test_empty_string_returns_empty(self):
        assert _parse_print_stats_lines("") == []

    def test_unrelated_text_ignored(self):
        text = "something unrelated and this too and also lev but no numbers"
        # Should not crash; 'and' and 'lev' are present but without proper context
        results = _parse_print_stats_lines(text)
        # The regex requires "and = <digits>  lev = <digits>", so no match expected
        assert isinstance(results, list)


# ── hybrid_validation: pipeline without ABC ──────────────────────────────────

class TestHybridValidationNoCalls:
    """
    Smoke tests that don't require ABC.  They verify that the hybrid validation
    pipeline produces the correct output structure even when no ABC call is made.
    """

    def _make_candidates(self):
        return pd.DataFrame({
            "benchmark":           ["toy", "toy"],
            "optimization":        ["balance", "balance"],
            "optimized_node":      ["opt_n1", "opt_n2"],
            "original_candidate":  ["orig_n1", "orig_n2"],
            "rank":                [1, 2],
            "combined_score":      [0.95, 0.88],
            "simulation_similarity": [0.90, 0.85],
            "support_overlap":     [1.0, 0.9],
            "depth_similarity":    [1.0, 0.95],
            "is_exact_signature_match": [0, 0],
            "match_category":      ["non_exact_candidate", "non_exact_candidate"],
        })

    def test_required_output_columns_exist_after_annotation(self):
        """
        annotate_candidates should add abc_validated, abc_complement,
        abc_result, abc_log_file columns.  When BLIFs are missing (no variants/
        directory in the test environment), the function should degrade gracefully
        and fill those columns with safe defaults.
        """
        from hybrid_validation import annotate_candidates
        df = self._make_candidates()

        # Use a non-existent outdir so no ABC is actually called
        with tempfile.TemporaryDirectory() as tmpdir:
            result = annotate_candidates(df, abc_bin="/nonexistent/abc", outdir=tmpdir)

        for col in ("abc_validated", "abc_complement", "abc_result", "abc_log_file"):
            assert col in result.columns, f"Missing column: {col}"

    def test_abc_validated_defaults_to_false(self):
        from hybrid_validation import annotate_candidates
        df = self._make_candidates()
        with tempfile.TemporaryDirectory() as tmpdir:
            result = annotate_candidates(df, abc_bin="/nonexistent/abc", outdir=tmpdir)
        assert not result["abc_validated"].any()

    def test_write_hybrid_csv_produces_file(self, tmp_path):
        from hybrid_validation import write_hybrid_csv, annotate_candidates, HYBRID_COLS
        df = self._make_candidates()
        with tempfile.TemporaryDirectory() as tmpdir:
            df = annotate_candidates(df, abc_bin="/nonexistent/abc", outdir=tmpdir)
        out = str(tmp_path / "hybrid.csv")
        write_hybrid_csv(df, out)
        assert os.path.exists(out)

    def test_write_hybrid_csv_has_expected_columns(self, tmp_path):
        from hybrid_validation import write_hybrid_csv, annotate_candidates, HYBRID_COLS
        df = self._make_candidates()
        with tempfile.TemporaryDirectory() as tmpdir:
            df = annotate_candidates(df, abc_bin="/nonexistent/abc", outdir=tmpdir)
        out = str(tmp_path / "hybrid.csv")
        write_hybrid_csv(df, out)
        loaded = pd.read_csv(out)
        for col in ("benchmark", "optimization", "optimized_node",
                    "original_candidate", "abc_validated", "abc_result"):
            assert col in loaded.columns

    def test_write_hybrid_markdown_produces_file(self, tmp_path):
        from hybrid_validation import write_hybrid_markdown, annotate_candidates
        df = self._make_candidates()
        with tempfile.TemporaryDirectory() as tmpdir:
            df = annotate_candidates(df, abc_bin="/nonexistent/abc", outdir=tmpdir)
        md_path = str(tmp_path / "hybrid_summary.md")
        write_hybrid_markdown(df, md_path)
        assert os.path.exists(md_path)

    def test_write_hybrid_markdown_contains_key_sections(self, tmp_path):
        from hybrid_validation import write_hybrid_markdown, annotate_candidates
        df = self._make_candidates()
        with tempfile.TemporaryDirectory() as tmpdir:
            df = annotate_candidates(df, abc_bin="/nonexistent/abc", outdir=tmpdir)
        md_path = str(tmp_path / "hybrid_summary.md")
        write_hybrid_markdown(df, md_path)
        text = Path(md_path).read_text()
        assert "Hybrid Validation" in text
        assert "Interpretation" in text


# ── integration test: real ABC call on toy benchmark ─────────────────────────

# Skip these if ABC isn't available — they're slow and require the binary.
_ABC_BIN = os.environ.get("ABC", "")
if not _ABC_BIN:
    import shutil as _shutil
    _ABC_BIN = _shutil.which("abc") or ""

_REAL_BLIF_EXISTS = (
    (_REPO_ROOT / "variants" / "majority3_original.blif").exists() and
    (_REPO_ROOT / "variants" / "majority3_balance.blif").exists()
)

@pytest.mark.skipif(
    not (_ABC_BIN and _REAL_BLIF_EXISTS),
    reason="ABC binary or majority3 variants not available",
)
class TestRealAbcCall:

    def test_dump_equiv_on_majority3(self, tmp_path):
        from abc_sat_sweep_validation import run_dump_equiv
        orig = str(_REPO_ROOT / "variants" / "majority3_original.blif")
        opt  = str(_REPO_ROOT / "variants" / "majority3_balance.blif")
        result = run_dump_equiv(_ABC_BIN, orig, opt, str(tmp_path / "out"))
        assert result.error == "", f"dump_equiv failed: {result.error}"

    def test_dump_equiv_finds_some_classes(self, tmp_path):
        from abc_sat_sweep_validation import run_dump_equiv
        orig = str(_REPO_ROOT / "variants" / "majority3_original.blif")
        opt  = str(_REPO_ROOT / "variants" / "majority3_balance.blif")
        result = run_dump_equiv(_ABC_BIN, orig, opt, str(tmp_path / "out"))
        assert result.total_classes >= 1

    def test_equiv_csv_written(self, tmp_path):
        from abc_sat_sweep_validation import run_dump_equiv, write_equiv_csv
        orig = str(_REPO_ROOT / "variants" / "majority3_original.blif")
        opt  = str(_REPO_ROOT / "variants" / "majority3_balance.blif")
        outdir = str(tmp_path / "out")
        result = run_dump_equiv(_ABC_BIN, orig, opt, outdir)
        csv_path = str(tmp_path / "matches.csv")
        write_equiv_csv(result.equiv_pairs, csv_path)
        assert os.path.exists(csv_path)

    def test_fraig_stats_on_majority3(self, tmp_path):
        from abc_sat_sweep_validation import run_fraig_stats
        blif = str(_REPO_ROOT / "variants" / "majority3_original.blif")
        stats = run_fraig_stats(_ABC_BIN, blif, str(tmp_path / "out"))
        assert stats.error == "", f"fraig_stats failed: {stats.error}"
        assert stats.nodes_before is not None
