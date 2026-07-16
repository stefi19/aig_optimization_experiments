from semantic_family_ranking import (
    confusion_matrix,
    evaluation_rows,
    ground_truth_family,
    rank_region_family,
)


def test_ground_truth_family_mapping_is_broad_not_operator_recovery():
    assert ground_truth_family("arithmetic", "unsigned_add") == "arithmetic_add_sub"
    assert ground_truth_family("arithmetic", "full_multiply") == "arithmetic_multiply"
    assert ground_truth_family("control", "mux2") == "control_mux"
    assert ground_truth_family("boolean", "bitwise_xor") == "boolean_bitwise"


def test_rank_region_family_is_deterministic():
    region = {
        "region_id": "r",
        "case_id": "case",
        "optimization": "identity",
        "source_type": "ground_truth_region",
        "family": "comparison",
        "operator": "eq",
    }
    feature = {
        "region_id": "r",
        "output_count": "1",
        "input_count": "4",
        "dependency_density": "0.9",
        "diagonal_concentration": "0.1",
        "lower_triangularity": "0.5",
        "bandwidth": "1.0",
        "carry_progression_score": "0.1",
        "multiplier_diagonal_score": "0.1",
        "locality_score": "0.0",
        "regularity_score": "0.7",
        "high_bit_priority_score": "0.8",
    }
    first = rank_region_family(region, feature, [])
    second = rank_region_family(region, feature, [])
    assert first == second
    assert first[0]["rank"] == "1"
    assert first[0]["ground_truth_family"] == "comparison"


def test_evaluation_rows_and_confusion_matrix():
    regions = {
        "r": {
            "region_id": "r",
            "family": "comparison",
            "operator": "eq",
            "optimization": "identity",
            "source_type": "ground_truth_region",
        }
    }
    rankings = [
        {
            "region_id": "r",
            "candidate_family": "comparison",
            "rank": "1",
            "ground_truth_family": "comparison",
            "ground_truth_rank": "1",
        },
        {
            "region_id": "r",
            "candidate_family": "boolean_bitwise",
            "rank": "2",
            "ground_truth_family": "comparison",
            "ground_truth_rank": "1",
        },
    ]
    overall = next(row for row in evaluation_rows(rankings, regions) if row["scope"] == "overall")
    assert overall["top_1_family_accuracy"] == "1.000000"
    assert confusion_matrix(rankings) == {("comparison", "comparison"): 1}
