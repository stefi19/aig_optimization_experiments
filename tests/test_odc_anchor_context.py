import csv

from boundary_anchor_map import load_anchor_map


def test_formal_plus_odc_loads_only_context_compatible_proven_rows(tmp_path):
    results = tmp_path / "results"
    out = results / "odc_anchor_generation"
    out.mkdir(parents=True)
    with (out / "odc_proven_anchors.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=[
                "benchmark",
                "optimization",
                "coi_name",
                "context_mode",
                "observable_outputs",
                "spec_node",
                "impl_node",
                "proven_polarity",
                "mapping_category",
                "evidence_level",
                "proof_status",
                "proof_mode",
            ],
        )
        writer.writeheader()
        writer.writerow(
            {
                "benchmark": "b",
                "optimization": "opt",
                "coi_name": "c1",
                "context_mode": "coi_output_odc",
                "observable_outputs": "y",
                "spec_node": "s",
                "impl_node": "i",
                "proven_polarity": "positive",
                "mapping_category": "formal_odc_valid_anchor",
                "evidence_level": "formal_contextual",
                "proof_status": "proven_odc_valid",
                "proof_mode": "abc_cec_contextual_miter",
            }
        )
    anchors = load_anchor_map("b", "opt", "formal_plus_odc", results_dir=results, coi_name="c1", context_mode="coi_output_odc", observable_outputs=("y",))
    assert anchors.has_anchor("s")
    assert anchors.selected_for("s").mapping_category == "formal_odc_valid_anchor"
    wrong = load_anchor_map("b", "opt", "formal_plus_odc", results_dir=results, coi_name="c2", context_mode="coi_output_odc", observable_outputs=("y",))
    assert not wrong.has_anchor("s")


def test_sampled_contextual_candidate_is_not_loaded(tmp_path):
    results = tmp_path / "results"
    out = results / "odc_anchor_generation"
    out.mkdir(parents=True)
    with (out / "odc_proven_anchors.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["benchmark", "optimization", "spec_node", "impl_node", "mapping_category", "evidence_level", "proof_status"])
        writer.writeheader()
        writer.writerow({"benchmark": "b", "optimization": "opt", "spec_node": "s", "impl_node": "i", "mapping_category": "sampled_contextual_candidate", "evidence_level": "sampled_estimate", "proof_status": "sampled"})
    anchors = load_anchor_map("b", "opt", "formal_plus_odc", results_dir=results)
    assert not anchors.has_anchor("s")
