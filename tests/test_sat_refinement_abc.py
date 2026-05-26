"""
tests/test_sat_refinement_abc.py

Unit tests for pure helper functions in sat_refinement_abc.py.

These tests do NOT require ABC to be installed. They only test the Python
helper functions: expose_node_as_output and parse_cec_output.

Run with:  python3 -m pytest tests/ -v
"""

import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sat_refinement_abc import expose_node_as_output, parse_cec_output


# ── parse_cec_output ──────────────────────────────────────────────────────────

class TestParseCecOutput:
    def test_equivalent(self):
        output = (
            "UC Berkeley, ABC 1.01\n"
            "Networks are equivalent after structural hashing.  Time =  0.00 sec\n"
            "***EOF***\n"
        )
        assert parse_cec_output(output) == "verified"

    def test_not_equivalent(self):
        output = (
            "UC Berkeley, ABC 1.01\n"
            "Networks are NOT EQUIVALENT.  Time =  0.01 sec\n"
            "INPUT: a = 1'h1, b = 1'h0.  OUTPUT: y = 1'h0, y = 1'h1.\n"
        )
        assert parse_cec_output(output) == "rejected"

    def test_empty_output(self):
        assert parse_cec_output("") == "inconclusive"

    def test_unrelated_output(self):
        assert parse_cec_output("Cannot open input file") == "inconclusive"

    def test_case_insensitive_equivalent(self):
        # ABC output is mixed case; make sure lowercase comparison works.
        assert parse_cec_output("networks are equivalent.") == "verified"

    def test_not_equivalent_takes_priority(self):
        # Hypothetical output that mentions both (should not happen in practice,
        # but we want the logic to be deterministic).
        output = "networks are equivalent ... networks are NOT EQUIVALENT"
        assert parse_cec_output(output) == "rejected"


# ── expose_node_as_output ────────────────────────────────────────────────────

class TestExposeNodeAsOutput:
    def _write_blif(self, content: str) -> str:
        tmp = tempfile.NamedTemporaryFile(
            mode="w", suffix=".blif", delete=False
        )
        tmp.write(content)
        tmp.close()
        return tmp.name

    def _read(self, path: str) -> str:
        with open(path) as f:
            return f.read()

    def test_output_line_replaced(self):
        src = (
            ".model test\n"
            ".inputs a b\n"
            ".outputs y\n"
            ".names a b n_ab\n"
            "11 1\n"
            ".names n_ab n_ab y\n"
            "1- 1\n"
            ".end\n"
        )
        src_path = self._write_blif(src)
        dst = tempfile.NamedTemporaryFile(suffix=".blif", delete=False)
        dst.close()

        expose_node_as_output(src_path, "n_ab", dst.name)
        content = self._read(dst.name)

        os.unlink(src_path)
        os.unlink(dst.name)

        assert ".outputs n_ab" in content
        assert ".outputs y" not in content

    def test_inputs_unchanged(self):
        src = (
            ".model test\n"
            ".inputs a b c\n"
            ".outputs z\n"
            ".names a b x\n"
            "11 1\n"
            ".names x c z\n"
            "11 1\n"
            ".end\n"
        )
        src_path = self._write_blif(src)
        dst = tempfile.NamedTemporaryFile(suffix=".blif", delete=False)
        dst.close()

        expose_node_as_output(src_path, "x", dst.name)
        content = self._read(dst.name)

        os.unlink(src_path)
        os.unlink(dst.name)

        assert ".inputs a b c" in content

    def test_names_lines_preserved(self):
        src = (
            ".model test\n"
            ".inputs a b\n"
            ".outputs y\n"
            ".names a b x\n"
            "11 1\n"
            ".names x x y\n"
            "1- 1\n"
            ".end\n"
        )
        src_path = self._write_blif(src)
        dst = tempfile.NamedTemporaryFile(suffix=".blif", delete=False)
        dst.close()

        expose_node_as_output(src_path, "x", dst.name)
        content = self._read(dst.name)

        os.unlink(src_path)
        os.unlink(dst.name)

        # Both .names blocks must still be in the file.
        assert content.count(".names") == 2

    def test_expose_primary_input(self):
        # Primary inputs are "defined" (no .names line), so exposing one
        # should succeed and just change .outputs.
        src = (
            ".model test\n"
            ".inputs a b\n"
            ".outputs y\n"
            ".names a b y\n"
            "11 1\n"
            ".end\n"
        )
        src_path = self._write_blif(src)
        dst = tempfile.NamedTemporaryFile(suffix=".blif", delete=False)
        dst.close()

        expose_node_as_output(src_path, "a", dst.name)
        content = self._read(dst.name)

        os.unlink(src_path)
        os.unlink(dst.name)

        assert ".outputs a" in content

    def test_missing_node_raises(self):
        src = (
            ".model test\n"
            ".inputs a b\n"
            ".outputs y\n"
            ".names a b y\n"
            "11 1\n"
            ".end\n"
        )
        src_path = self._write_blif(src)
        dst = tempfile.NamedTemporaryFile(suffix=".blif", delete=False)
        dst.close()

        try:
            raised = False
            try:
                expose_node_as_output(src_path, "does_not_exist", dst.name)
            except ValueError:
                raised = True
            assert raised, "Expected ValueError for unknown node"
        finally:
            os.unlink(src_path)
            os.unlink(dst.name)

    def test_multiple_outputs_replaced(self):
        # If a BLIF somehow has multiple .outputs lines, all should be replaced.
        src = (
            ".model test\n"
            ".inputs a b\n"
            ".outputs y z\n"
            ".names a b y\n"
            "11 1\n"
            ".names a b z\n"
            "10 1\n"
            ".end\n"
        )
        src_path = self._write_blif(src)
        dst = tempfile.NamedTemporaryFile(suffix=".blif", delete=False)
        dst.close()

        expose_node_as_output(src_path, "y", dst.name)
        content = self._read(dst.name)

        os.unlink(src_path)
        os.unlink(dst.name)

        # There should be no reference to the old .outputs line anymore.
        assert ".outputs y" in content
        assert ".outputs y z" not in content
