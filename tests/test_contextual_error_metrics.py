import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import contextual_error_metrics as cem
from analyze_blif_matches import parse_blif


def write_blif(tmp_path, name, text):
    path = tmp_path / f"{name}.blif"
    path.write_text(text, encoding="utf-8")
    return path


def test_global_boolean_distance():
    assert cem.hamming_distance_rate(0b1100, 0b1010, 4) == 0.5


def test_multi_output_hamming_and_numeric_metrics():
    baseline = [0b10, 0b11]
    substituted = [0b11, 0b01]
    metrics = cem.output_metrics(baseline, substituted, 2)
    assert metrics.contextual_output_error_rate == 1.0
    assert metrics.mean_output_hamming_distance == 1.0
    assert metrics.worst_case_output_hamming_distance == 1
    assert metrics.mean_absolute_output_error == 1.5
    assert metrics.worst_case_absolute_output_error == 2


def test_exact_and_sampled_modes_are_distinct_and_deterministic():
    exact = cem.choose_patterns(["a", "b"], exact_support_cap=2, sample_count=8, seed=1, key="k")
    sampled_a = cem.choose_patterns(["a", "b", "c"], exact_support_cap=2, sample_count=8, seed=7, key="k")
    sampled_b = cem.choose_patterns(["a", "b", "c"], exact_support_cap=2, sample_count=8, seed=7, key="k")
    assert exact.mode == "exact"
    assert exact.pattern_count == 4
    assert sampled_a.mode == "sampled"
    assert sampled_a.values == sampled_b.values


def test_classification_thresholds_and_formality():
    assert cem.classify_candidate(0.0, True, 0.0, True, "not_run", 0.01) == "globally_exact"
    assert cem.classify_candidate(0.0, False, 0.0, False, "verified_equivalent", 0.01) == "unresolved"
    assert cem.classify_candidate(0.5, True, 0.0, True, "verified_equivalent", 0.01) == "odc_valid_correspondence"
    assert cem.classify_candidate(0.5, True, 0.005, True, "rejected_non_equivalent", 0.01) == "contextually_approximate_exact"
    assert cem.classify_candidate(0.5, False, 0.005, False, "rejected_non_equivalent", 0.01) == "contextually_approximate_sampled"
    assert cem.classify_candidate(0.5, True, 0.25, True, "rejected_non_equivalent", 0.01) == "unsafe_candidate"
    assert cem.classify_candidate(0.5, False, 0.0, False, "rejected_non_equivalent", 0.01) == "contextually_approximate_sampled"
    assert cem.classify_candidate(0.5, True, 0.0, True, "not_run", 0.01) == "unresolved"


def test_legacy_category_normalization_and_labels():
    assert cem.normalize_mapping_category("sat_verified_nonexact") == "sat_cec_proven_equivalent"
    assert cem.normalize_mapping_category("SAT-verified non-exact") == "sat_cec_proven_equivalent"
    assert cem.normalize_mapping_category("approximate_near_match") == "global_approximate_near_match"
    assert cem.normalize_mapping_category("contextually_approximate") == "contextually_approximate_sampled"
    assert cem.category_display_label("sat_verified_nonexact") == "SAT/CEC-proven equivalent"
    assert cem.category_display_label("contextually_approximate_sampled") == "Sampled contextual approximation"


def test_contextual_evidence_levels_are_explicit():
    assert cem.contextual_evidence_level("odc_valid_correspondence", False, "verified_equivalent") == "formal_cec"
    assert cem.contextual_evidence_level("contextually_approximate_exact", True, "rejected_non_equivalent") == "formal_exhaustive"
    assert cem.contextual_evidence_level("contextually_approximate_sampled", False, "rejected_non_equivalent") == "sampled_estimate"


def test_temp_node_renaming_and_substitution(tmp_path):
    optimized = write_blif(
        tmp_path,
        "opt",
        """.model opt
.inputs a b
.outputs y
.names a b v
11 1
.names v y
1 1
.end
""",
    )
    original = write_blif(
        tmp_path,
        "orig",
        """.model orig
.inputs a b
.outputs y
.names b a g
11 1
.names g y
1 1
.end
""",
    )
    opt_net = parse_blif(optimized)
    orig_net = parse_blif(original)
    result = cem.substitute_candidate(opt_net, orig_net, "v", "g")
    assert result.status == "ok"
    assert result.network is not None
    assert any(node.output == "__ctx_orig_g" for node in result.network.nodes)
    assert result.network.outputs == opt_net.outputs


def test_substitution_rejects_missing_outputs(tmp_path):
    optimized = write_blif(
        tmp_path,
        "opt_missing_output",
        """.model opt_missing_output
.inputs a b
.outputs y
.names a b v
11 1
.end
""",
    )
    original = write_blif(
        tmp_path,
        "orig_missing_output",
        """.model orig_missing_output
.inputs a b
.outputs out
.names a b g
11 1
.names g out
1 1
.end
""",
    )
    metrics, _, _ = cem.evaluate_contextual_pair(original, optimized, "v", "g", 12, 16, 1, 0.01)
    assert metrics["substitution_status"] == "skipped"
    assert "missing primary output values" in metrics["reason"]


def test_substitution_rejects_duplicate_primary_outputs(tmp_path):
    optimized = write_blif(
        tmp_path,
        "opt_dup_outputs",
        """.model opt_dup_outputs
.inputs a b
.outputs y y
.names a b v
11 1
.names v y
1 1
.end
""",
    )
    original = write_blif(
        tmp_path,
        "orig_dup_outputs",
        """.model orig_dup_outputs
.inputs a b
.outputs y
.names a b g
11 1
.names g y
1 1
.end
""",
    )
    result = cem.substitute_candidate(parse_blif(optimized), parse_blif(original), "v", "g")
    assert result.status == "skipped"
    assert "primary output names are not unique" in result.reason


def test_substitution_allows_different_original_output_names(tmp_path):
    optimized = write_blif(
        tmp_path,
        "opt_output_name",
        """.model opt_output_name
.inputs a b
.outputs opt_y
.names a b v
11 1
.names v opt_y
1 1
.end
""",
    )
    original = write_blif(
        tmp_path,
        "orig_output_name",
        """.model orig_output_name
.inputs a b
.outputs orig_y
.names a b g
11 1
.names g orig_y
1 1
.end
""",
    )
    result = cem.substitute_candidate(parse_blif(optimized), parse_blif(original), "v", "g")
    assert result.status == "ok"
    assert result.network is not None
    assert result.network.outputs == ["opt_y"]


def test_substitution_rejects_cloned_candidate_cone_collision(tmp_path):
    optimized = write_blif(
        tmp_path,
        "opt_collision",
        """.model opt_collision
.inputs a b
.outputs y
.names a __ctx_orig_g
11 1
.names a b v
11 1
.names v y
1 1
.end
""",
    )
    original = write_blif(
        tmp_path,
        "orig_collision",
        """.model orig_collision
.inputs a b
.outputs y
.names a b g
11 1
.names g y
1 1
.end
""",
    )
    result = cem.substitute_candidate(parse_blif(optimized), parse_blif(original), "v", "g")
    assert result.status == "skipped"
    assert "collides with optimized network name" in result.reason


def test_invalid_substitution_missing_node(tmp_path):
    path = write_blif(
        tmp_path,
        "n",
        """.model n
.inputs a
.outputs y
.names a y
1 1
.end
""",
    )
    net = parse_blif(path)
    result = cem.substitute_candidate(net, net, "missing", "y")
    assert result.status == "skipped"
    assert "missing" in result.reason


def test_parse_abc_cec_results():
    assert cem.parse_abc_cec("Networks are equivalent") == "verified_equivalent"
    assert cem.parse_abc_cec("Networks are NOT EQUIVALENT") == "rejected_non_equivalent"
    assert cem.parse_abc_cec("unknown output") == "inconclusive"


def test_case_a_globally_exact_commuted_and(tmp_path):
    original = write_blif(
        tmp_path,
        "orig_exact",
        """.model orig_exact
.inputs a b
.outputs y
.names b a g
11 1
.names g y
1 1
.end
""",
    )
    optimized = write_blif(
        tmp_path,
        "opt_exact",
        """.model opt_exact
.inputs a b
.outputs y
.names a b v
11 1
.names v y
1 1
.end
""",
    )
    metrics, _, _ = cem.evaluate_contextual_pair(original, optimized, "v", "g", 12, 16, 1, 0.01)
    assert metrics["global_error_rate"] == 0
    assert cem.classify_candidate(metrics["global_error_rate"], True, metrics["contextual_output_error_rate"], True, "not_run", 0.01) == "globally_exact"


def test_case_b_odc_valid(tmp_path):
    original = write_blif(
        tmp_path,
        "orig_odc",
        """.model orig_odc
.inputs a b
.outputs y
.names a b g
1- 1
-1 1
.names zero
.names g zero y
11 1
.end
""",
    )
    optimized = write_blif(
        tmp_path,
        "opt_odc",
        """.model opt_odc
.inputs a b
.outputs y
.names a b v
11 1
.names zero
.names v zero y
11 1
.end
""",
    )
    metrics, _, _ = cem.evaluate_contextual_pair(original, optimized, "v", "g", 12, 16, 1, 0.01)
    assert metrics["global_error_rate"] == 0.5
    assert metrics["contextual_output_error_rate"] == 0
    assert cem.classify_candidate(metrics["global_error_rate"], True, 0.0, True, "verified_equivalent", 0.01) == "odc_valid_correspondence"


def test_case_c_visible_unsafe(tmp_path):
    original = write_blif(
        tmp_path,
        "orig_visible",
        """.model orig_visible
.inputs a b
.outputs y
.names a b g
1- 1
-1 1
.names g y
1 1
.end
""",
    )
    optimized = write_blif(
        tmp_path,
        "opt_visible",
        """.model opt_visible
.inputs a b
.outputs y
.names a b v
11 1
.names v y
1 1
.end
""",
    )
    metrics, _, _ = cem.evaluate_contextual_pair(original, optimized, "v", "g", 12, 16, 1, 0.01)
    assert metrics["global_error_rate"] == 0.5
    assert metrics["contextual_output_error_rate"] == 0.5
    assert cem.classify_candidate(metrics["global_error_rate"], True, 0.5, True, "rejected_non_equivalent", 0.01) == "unsafe_candidate"


def test_case_d_contextually_approximate(tmp_path):
    original = write_blif(
        tmp_path,
        "orig_approx",
        """.model orig_approx
.inputs a b c d
.outputs y
.names a b f
11 1
.names c d cd
11 1
.names f cd g
1- 1
-1 1
.names g y
1 1
.end
""",
    )
    optimized = write_blif(
        tmp_path,
        "opt_approx",
        """.model opt_approx
.inputs a b c d
.outputs y
.names a b v
11 1
.names v y
1 1
.end
""",
    )
    metrics, _, _ = cem.evaluate_contextual_pair(original, optimized, "v", "g", 12, 16, 1, 0.20)
    assert metrics["contextual_output_error_rate"] == 0.1875
    assert cem.classify_candidate(metrics["global_error_rate"], True, 0.1875, True, "rejected_non_equivalent", 0.20) == "contextually_approximate_exact"
