from pathlib import Path

from sensitivity_signatures import compare_sensitivity_profiles


def write_blif(path: Path, body: str) -> Path:
    path.write_text(body.strip() + "\n", encoding="utf-8")
    return path


def test_equivalent_functions_have_matching_sensitivity(tmp_path):
    blif = """
.model m
.inputs a b
.outputs y
.names a b y
01 1
10 1
.end
"""
    left = write_blif(tmp_path / "left.blif", blif)
    right = write_blif(tmp_path / "right.blif", blif)

    result = compare_sensitivity_profiles(left, right, "y", "y", exact_support_limit=4)

    assert result.status == "ok"
    assert result.sensitivity_evidence_level == "formal_exhaustive"
    assert result.sensitivity_cosine_similarity > 0.999999
    assert result.boolean_difference_similarity == 1.0
    assert result.dominant_variable_agreement == 1


def test_globally_close_but_different_sensitivity_is_detected(tmp_path):
    left = write_blif(
        tmp_path / "left.blif",
        """
.model l
.inputs a b
.outputs y
.names a y
1 1
.end
""",
    )
    right = write_blif(
        tmp_path / "right.blif",
        """
.model r
.inputs a b
.outputs y
.names a b y
11 1
.end
""",
    )

    result = compare_sensitivity_profiles(left, right, "y", "y", exact_support_limit=4)

    assert result.status == "ok"
    assert result.sensitivity_cosine_similarity < 1.0
    assert result.boolean_difference_similarity < 1.0


def test_sampled_sensitivity_is_labeled_as_estimate(tmp_path):
    blif = """
.model m
.inputs a b c d
.outputs y
.names a b c d y
1111 1
.end
"""
    left = write_blif(tmp_path / "left.blif", blif)
    right = write_blif(tmp_path / "right.blif", blif)

    result = compare_sensitivity_profiles(left, right, "y", "y", exact_support_limit=1, sample_count=64, seed=9)

    assert result.sensitivity_evidence_level == "sampled_estimate"
    assert result.sensitivity_mode in {"sampled", "mixed"}
