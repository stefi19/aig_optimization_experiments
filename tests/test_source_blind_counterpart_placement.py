from __future__ import annotations

from pathlib import Path

from source_blind_counterpart_placement import attempt_source_blind_counterpart_placement


def _write_blif(path: Path, body: str) -> None:
    path.write_text(body.strip() + "\n", encoding="utf-8")


def _missing_abc(tmp_path: Path) -> Path:
    return tmp_path / "missing_abc"


def test_source_blind_exact_counterpart_emits_diagnostic_rewrite(tmp_path: Path) -> None:
    source = tmp_path / "source.blif"
    optimized = tmp_path / "optimized.blif"
    _write_blif(
        source,
        """
        .model source
        .inputs a b c
        .outputs y
        .names a b src_ab
        11 1
        .names src_ab c y
        1- 1
        -1 1
        .end
        """,
    )
    _write_blif(
        optimized,
        """
        .model optimized
        .inputs a b c
        .outputs y
        .names a na
        0 1
        .names b nb
        0 1
        .names na nb t
        00 1
        .names t c y
        1- 1
        -1 1
        .end
        """,
    )
    result = attempt_source_blind_counterpart_placement(
        target_id="controlled|region|flow|t",
        semantic_counterpart_status="proved_additive_counterpart",
        source_path=source,
        optimized_path=optimized,
        optimized_target_node="t",
        output_path=tmp_path / "rewrite.blif",
        root=tmp_path,
        abc_path=_missing_abc(tmp_path),
    )
    assert result.rewrite_emitted
    assert result.candidate_source_window == ("src_ab",)
    assert result.rewrite_artifact == "rewrite.blif"
    assert result.global_cec_status == "not_claimed"
    assert result.source_vs_rewrite_cec == "abc_unavailable"
    assert result.rewrite_vs_optimized_cec == "abc_unavailable"
    assert result.blocker == "source_vs_rewrite_cec_abc_unavailable"


def test_source_blind_identity_rewrite_is_not_emitted(tmp_path: Path) -> None:
    source = tmp_path / "source.blif"
    optimized = tmp_path / "optimized.blif"
    body = """
        .model identity
        .inputs a b
        .outputs y
        .names a b t
        11 1
        .names t y
        1 1
        .end
        """
    _write_blif(source, body)
    _write_blif(optimized, body)
    result = attempt_source_blind_counterpart_placement(
        target_id="controlled|region|flow|t",
        semantic_counterpart_status="proved_additive_counterpart",
        source_path=source,
        optimized_path=optimized,
        optimized_target_node="t",
        output_path=tmp_path / "rewrite.blif",
        root=tmp_path,
        abc_path=_missing_abc(tmp_path),
    )
    assert not result.rewrite_emitted
    assert result.blocker == "identical_driver"


def test_source_blind_bypass_rewrite_is_not_emitted(tmp_path: Path) -> None:
    source = tmp_path / "source.blif"
    optimized = tmp_path / "optimized.blif"
    _write_blif(
        source,
        """
        .model source
        .inputs a
        .outputs y
        .names a src_a
        1 1
        .names src_a y
        1 1
        .end
        """,
    )
    _write_blif(
        optimized,
        """
        .model optimized
        .inputs a
        .outputs y
        .names a na
        0 1
        .names na t
        0 1
        .names t y
        1 1
        .end
        """,
    )
    result = attempt_source_blind_counterpart_placement(
        target_id="controlled|region|flow|t",
        semantic_counterpart_status="proved_additive_counterpart",
        source_path=source,
        optimized_path=optimized,
        optimized_target_node="t",
        output_path=tmp_path / "rewrite.blif",
        root=tmp_path,
        abc_path=_missing_abc(tmp_path),
    )
    assert not result.rewrite_emitted
    assert result.blocker == "direct_bypass"


def test_source_blind_whole_design_replacement_rejected(tmp_path: Path) -> None:
    source = tmp_path / "source.blif"
    optimized = tmp_path / "optimized.blif"
    body = """
        .model whole
        .inputs a b
        .outputs y
        .names a b y
        11 1
        .end
        """
    _write_blif(source, body)
    _write_blif(optimized, body)
    result = attempt_source_blind_counterpart_placement(
        target_id="controlled|region|flow|y",
        semantic_counterpart_status="proved_additive_counterpart",
        source_path=source,
        optimized_path=optimized,
        optimized_target_node="y",
        output_path=tmp_path / "rewrite.blif",
        root=tmp_path,
        abc_path=_missing_abc(tmp_path),
    )
    assert not result.rewrite_emitted
    assert result.blocker == "whole_design_replacement_rejected"
