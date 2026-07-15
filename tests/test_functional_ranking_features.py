from functional_ranking_features import compute_ranking_scores, formal_label, support_bucket


def test_full_combined_uses_baseline_and_available_features():
    row = {
        "combined_score": 0.5,
        "cofactor_status": "ok",
        "cofactor_consistency_score": 1.0,
        "mean_cofactor_similarity": 0.9,
        "max_cofactor_error": 0.1,
        "sensitivity_status": "ok",
        "sensitivity_cosine_similarity": 0.8,
        "boolean_difference_similarity": 0.7,
        "dominant_variable_agreement": 1,
        "inactive_variable_agreement": 1,
    }

    scores = compute_ranking_scores(row)

    assert 0.0 <= scores.full_combined <= 1.0
    assert scores.full_combined > scores.baseline
    assert scores.cofactor_only > 0.0
    assert scores.sensitivity_only > 0.0


def test_missing_features_do_not_accidentally_promote_candidate():
    scores = compute_ranking_scores({"combined_score": 0.25})

    assert scores.baseline == 0.25
    assert scores.cofactor_only == 0.0
    assert scores.sensitivity_only == 0.0


def test_formal_labels_keep_sat_cec_authority():
    assert formal_label({"sat_status": "verified"}) == "verified_equivalent"
    assert formal_label({"sat_status": "rejected"}) == "rejected_non_equivalent"
    assert formal_label({"sat_status": "timeout"}) == "inconclusive"
    assert formal_label({}) == "not_checked"


def test_support_bucket_ranges():
    assert support_bucket(4) == "0-4"
    assert support_bucket(8) == "5-8"
    assert support_bucket(12) == "9-12"
    assert support_bucket(13) == "13+"
