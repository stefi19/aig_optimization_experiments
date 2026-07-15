import pandas as pd

from scripts.compare_functional_ranking_ablations import aggregate_metrics, ranked_frame, seed_stability


def tiny_features() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "benchmark": "b",
                "optimization": "opt",
                "optimized_node": "n1",
                "original_node": "a",
                "seed": 1,
                "candidate_rank": 1,
                "formal_label": "rejected_non_equivalent",
                "baseline": 0.9,
                "cofactor_only": 0.2,
                "sensitivity_only": 0.2,
                "cofactor_plus_sensitivity": 0.2,
                "full_combined": 0.1,
                "support_size_bucket": "0-4",
            },
            {
                "benchmark": "b",
                "optimization": "opt",
                "optimized_node": "n1",
                "original_node": "good",
                "seed": 1,
                "candidate_rank": 2,
                "formal_label": "verified_equivalent",
                "baseline": 0.7,
                "cofactor_only": 1.0,
                "sensitivity_only": 1.0,
                "cofactor_plus_sensitivity": 1.0,
                "full_combined": 1.0,
                "support_size_bucket": "0-4",
            },
        ]
    )


def test_ranking_is_deterministic_and_scores_change_order():
    df = tiny_features()

    baseline = ranked_frame(df, "baseline")
    full = ranked_frame(df, "full_combined")

    assert baseline.iloc[0]["original_node"] == "a"
    assert full.iloc[0]["original_node"] == "good"


def test_aggregate_metrics_report_reciprocal_rank():
    metrics = aggregate_metrics(tiny_features())

    baseline = metrics[metrics["ranking_mode"] == "baseline"].iloc[0]
    full = metrics[metrics["ranking_mode"] == "full_combined"].iloc[0]

    assert baseline["mean_reciprocal_rank"] == 0.5
    assert full["mean_reciprocal_rank"] == 1.0
    assert full["precision_at_1"] == 1.0


def test_seed_stability_schema():
    stability = seed_stability(tiny_features())

    assert {"seed_count", "rank_spread"}.issubset(stability.columns)
