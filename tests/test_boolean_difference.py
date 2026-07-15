from pathlib import Path

from analyze_blif_matches import parse_blif
from boolean_difference import boolean_difference_probability


def write_blif(path: Path, body: str) -> Path:
    path.write_text(body.strip() + "\n", encoding="utf-8")
    return path


def test_constant_function_has_zero_difference(tmp_path):
    path = write_blif(
        tmp_path / "const.blif",
        """
.model c
.inputs a
.outputs y
.names y
1
.end
""",
    )
    net = parse_blif(path)

    result = boolean_difference_probability(net, "y", set(), "a")

    assert result.probability == 0.0
    assert result.evidence_level == "formal_exhaustive"


def test_identity_is_fully_sensitive_to_variable(tmp_path):
    path = write_blif(
        tmp_path / "id.blif",
        """
.model i
.inputs a
.outputs y
.names a y
1 1
.end
""",
    )
    net = parse_blif(path)

    result = boolean_difference_probability(net, "y", {"a"}, "a")

    assert result.probability == 1.0


def test_and_sensitivity_is_half_for_each_input(tmp_path):
    path = write_blif(
        tmp_path / "and.blif",
        """
.model and2
.inputs a b
.outputs y
.names a b y
11 1
.end
""",
    )
    net = parse_blif(path)

    da = boolean_difference_probability(net, "y", {"a", "b"}, "a")
    db = boolean_difference_probability(net, "y", {"a", "b"}, "b")

    assert da.probability == 0.5
    assert db.probability == 0.5


def test_xor_sensitivity_is_one(tmp_path):
    path = write_blif(
        tmp_path / "xor.blif",
        """
.model xor2
.inputs a b
.outputs y
.names a b y
01 1
10 1
.end
""",
    )
    net = parse_blif(path)

    assert boolean_difference_probability(net, "y", {"a", "b"}, "a").probability == 1.0
    assert boolean_difference_probability(net, "y", {"a", "b"}, "b").probability == 1.0
