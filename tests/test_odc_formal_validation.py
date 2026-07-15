from pathlib import Path

from analyze_blif_matches import parse_blif
from odc_formal_validation import apply_polarity, prove_contextual_interchangeability, validate_alignment


def write(path: Path, text: str) -> Path:
    path.write_text(text.strip() + "\n", encoding="utf-8")
    return path


BLIF = """
.model m
.inputs a b
.outputs y
.names a n1
1 1
.names b n2
1 1
.names n1 n2 y
11 1
.end
"""


def test_missing_observable_output_rejected(tmp_path):
    path = write(tmp_path / "m.blif", BLIF)
    net = parse_blif(path)
    assert validate_alignment(net, net, "n1", "n2", ("missing",)) == "missing_observable_output:missing"


def test_missing_node_rejected(tmp_path):
    path = write(tmp_path / "m.blif", BLIF)
    net = parse_blif(path)
    assert validate_alignment(net, net, "nope", "n2", ("y",)) == "missing_node:spec"


def test_timeout_or_missing_abc_is_not_valid(tmp_path):
    path = write(tmp_path / "m.blif", BLIF)
    result = prove_contextual_interchangeability(path, path, "n1", "n2", "positive", "global_output_odc", ("y",), 1, None)
    assert result.status == "tool_error"
    assert result.evidence_level if hasattr(result, "evidence_level") else True


def test_inverted_polarity_changes_replacement_cover(tmp_path):
    path = write(tmp_path / "m.blif", BLIF)
    net = parse_blif(path)
    inverted = apply_polarity(net, "n1", "inverted")
    node = next(n for n in inverted.nodes if n.output == "n1")
    assert node.cover == ["0 1"]
