from pathlib import Path

from boundary_anchor_map import Anchor, AnchorMap, load_anchor_map


def test_anchor_selection_prefers_exact_same_polarity():
    anchors = AnchorMap(
        [
            Anchor("n1", "z", "inverted", "complemented_equivalence", "formal_cec", "cec", "x", "verified"),
            Anchor("n1", "a", "same", "exact_signature_match", "formal_exhaustive", "truth", "x", "1.0"),
        ]
    )

    selected = anchors.selected_for("n1")

    assert selected.impl_node == "a"
    assert selected.selected
    assert "category priority" in selected.selection_reason


def test_primary_io_identity_anchors_are_added(tmp_path):
    results = tmp_path / "results"
    results.mkdir()
    (results / "top_candidates.csv").write_text(
        "benchmark,optimization,optimized_node,original_candidate,rank,match_category,combined_score,is_formal_exact_mode\n",
        encoding="utf-8",
    )

    anchors = load_anchor_map(
        "b",
        "opt",
        "exact_only",
        results_dir=results,
        spec_inputs=["a"],
        impl_inputs=["a"],
        spec_outputs=["y"],
        impl_outputs=["y"],
    )

    assert anchors.selected_for("a").proof_mode == "primary_input_identity"
    assert anchors.selected_for("y").proof_mode == "primary_output_identity"
