from pathlib import Path

import pytest

from cofactor_analysis import compute_cofactor_features, normalized_dispersion_score


def write_blif(path: Path, body: str) -> Path:
    path.write_text(body.strip() + "\n", encoding="utf-8")
    return path


def test_identical_and_cofactors_match_exhaustively(tmp_path):
    blif = """
.model m
.inputs a b
.outputs y
.names a b y
11 1
.end
"""
    left = write_blif(tmp_path / "left.blif", blif)
    right = write_blif(tmp_path / "right.blif", blif)

    result = compute_cofactor_features(left, right, "y", "y", exact_support_limit=4)

    assert result.status == "ok"
    assert result.evidence_level == "formal_exhaustive"
    assert result.mean_cofactor_error == 0.0
    assert result.exact_matching_cofactor_branches == 4
    assert result.cofactor_consistency_score == 1.0


def test_no_common_support_is_skipped(tmp_path):
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
.names b y
1 1
.end
""",
    )

    result = compute_cofactor_features(left, right, "y", "y")

    assert result.status == "skipped"
    assert result.skipped_reason == "no_common_support"


def test_input_order_mismatch_is_not_silently_compared(tmp_path):
    left = write_blif(
        tmp_path / "left.blif",
        """
.model l
.inputs a b
.outputs y
.names a b y
11 1
.end
""",
    )
    right = write_blif(
        tmp_path / "right.blif",
        """
.model r
.inputs b a
.outputs y
.names a b y
11 1
.end
""",
    )

    result = compute_cofactor_features(left, right, "y", "y")

    assert result.status == "skipped"
    assert result.skipped_reason == "input_alignment_failure"


def test_sampled_mode_is_deterministic(tmp_path):
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

    first = compute_cofactor_features(left, right, "y", "y", exact_support_limit=1, sample_count=64, seed=5)
    second = compute_cofactor_features(left, right, "y", "y", exact_support_limit=1, sample_count=64, seed=5)

    assert first.mode == "sampled"
    assert first.evidence_level == "sampled_estimate"
    assert first.as_dict() == second.as_dict()


@pytest.mark.parametrize("errors,expected", [([0.0, 0.0], 1.0), ([0.0, 1.0], 0.0)])
def test_dispersion_score_bounds(errors, expected):
    assert normalized_dispersion_score(errors) == expected
