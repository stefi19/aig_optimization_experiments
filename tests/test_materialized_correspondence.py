from pathlib import Path

from analyze_blif_matches import BlifNetwork, BlifNode, parse_blif
from anchored_cut_enumeration import enumerate_anchored_cuts, invert_anchor_map
from boundary_anchor_map import Anchor, load_anchor_map
from boundary_graph import CircuitGraph
from contextual_error_metrics import write_blif
from cut_function_extraction import extract_cut_truth_table
from materialized_anchor_validation import prove_materialized_anchor_exhaustive
from materialized_expression import expression_from_truth_table
from wire_materialization import cover_from_truth_table, materialize_wire


def anchor(spec: str, impl: str, polarity: str = "same") -> Anchor:
    return Anchor(
        spec_node=spec,
        impl_node=impl,
        polarity=polarity,
        mapping_category="exact_signature_match" if polarity == "same" else "complemented_equivalence",
        evidence_level="formal_exhaustive",
        proof_mode="unit",
        source_result_file="unit",
        confidence_or_status="verified",
    )


def and_network(output: str = "n1") -> BlifNetwork:
    return BlifNetwork(inputs=["a", "b"], outputs=["out"], nodes=[BlifNode(output, ["a", "b"], ["11 1"]), BlifNode("out", [output], ["1 1"])])


def test_cut_enumeration_keeps_globally_anchored_leaves_and_polarity():
    net = and_network("n1")
    graph = CircuitGraph.from_network(net)
    inverse = invert_anchor_map([anchor("a", "a"), anchor("b_spec", "b", "inverted")])
    cuts = enumerate_anchored_cuts(graph, "n1", inverse, max_cut_size=2, max_depth=1)
    assert cuts
    cut = next(c for c in cuts if c.impl_leaf_nodes == ("a", "b"))
    assert cut.spec_leaf_nodes == ("a", "b_spec")
    assert cut.leaf_polarities == ("same", "inverted")
    assert cut.all_leaves_globally_formal is True


def test_cut_extraction_and_hidden_support_detection():
    net = BlifNetwork(
        inputs=["a", "b", "c"],
        outputs=["out"],
        nodes=[BlifNode("x", ["a", "b"], ["11 1"]), BlifNode("out", ["x", "c"], ["11 1"])],
    )
    ok = extract_cut_truth_table(net, target_impl_node="x", cut_id="cut_ok", impl_leaf_nodes=("a", "b"))
    assert ok.extraction_status == "extracted"
    assert ok.truth_table == (0, 0, 0, 1)
    bad = extract_cut_truth_table(net, target_impl_node="out", cut_id="cut_bad", impl_leaf_nodes=("a", "b"))
    assert bad.extraction_status == "failed"
    assert bad.failure_reason == "hidden_support"


def test_cover_generation_applies_inverted_leaf_polarity():
    cover = cover_from_truth_table((0, 1), ("s",), ("inverted",))
    assert cover == ["0 1"]


def test_materialized_wire_is_additive_and_formally_proven(tmp_path: Path):
    spec = and_network("orig_and")
    impl = and_network("impl_and")
    fn = extract_cut_truth_table(impl, target_impl_node="impl_and", cut_id="cut1", impl_leaf_nodes=("a", "b"))
    expr = expression_from_truth_table(fn)
    augmented, wire = materialize_wire(spec, fn, expr, spec_leaf_nodes=("a", "b"), leaf_polarities=("same", "same"), case_id="case", output_dir=tmp_path)
    assert augmented is not None
    assert wire.generation_status == "generated"
    assert augmented.outputs == spec.outputs
    assert any(node.output == wire.materialized_wire_name for node in augmented.nodes)
    spec_path = tmp_path / "spec.blif"
    impl_path = tmp_path / "impl.blif"
    write_blif(spec, spec_path)
    write_blif(impl, impl_path)
    proof = prove_materialized_anchor_exhaustive(
        spec,
        augmented,
        impl,
        spec_path=spec_path,
        impl_path=impl_path,
        augmented_spec_path=tmp_path / Path(wire.augmented_spec_path).name,
        materialized_wire_name=wire.materialized_wire_name,
        target_impl_node="impl_and",
    )
    assert proof.proof_status == "proven_materialized_anchor"
    assert proof.sat_result == "unsat_exhaustive"
    assert proof.augmentation_preserves_original_outputs is True


def test_incorrect_materialized_wire_is_disproven(tmp_path: Path):
    spec = BlifNetwork(inputs=["a", "b"], outputs=["out"], nodes=[BlifNode("out", ["a"], ["1 1"])])
    augmented = BlifNetwork(inputs=["a", "b"], outputs=["out"], nodes=[BlifNode("out", ["a"], ["1 1"]), BlifNode("bad", ["a"], ["1 1"])])
    impl = and_network("impl_and")
    spec_path = tmp_path / "spec.blif"
    impl_path = tmp_path / "impl.blif"
    aug_path = tmp_path / "aug.blif"
    write_blif(spec, spec_path)
    write_blif(impl, impl_path)
    write_blif(augmented, aug_path)
    proof = prove_materialized_anchor_exhaustive(spec, augmented, impl, spec_path=spec_path, impl_path=impl_path, augmented_spec_path=aug_path, materialized_wire_name="bad", target_impl_node="impl_and")
    assert proof.proof_status == "disproven"
    assert proof.sat_result == "sat_exhaustive"


def test_materialized_anchor_map_mode_loads_only_proven_rows(tmp_path: Path):
    out = tmp_path / "materialized_correspondence"
    out.mkdir()
    (out / "proven_materialized_anchors.csv").write_text(
        "benchmark,optimization,proof_status,mapping_category,evidence_level,equivalence_scope,materialized_spec_node,target_impl_node,target_polarity,formal_backend,cut_id,expression_id\n"
        "bench,opt,proven_materialized_anchor,formal_materialized_anchor,formal_exhaustive,global,mat1,impl1,positive,exhaustive_global_truth_table,cut1,expr1\n",
        encoding="utf-8",
    )
    amap = load_anchor_map("bench", "opt", "formal_plus_materialized", results_dir=tmp_path)
    selected = amap.selected_for("mat1")
    assert selected is not None
    assert selected.anchor_origin == "materialized_wire"
    assert selected.mapping_category == "formal_materialized_anchor"
    assert selected.equivalence_scope == "global"
