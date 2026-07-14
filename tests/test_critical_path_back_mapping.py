import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from analyze_blif_matches import parse_blif
from scripts import critical_path_back_mapping as cpmap


def write_blif(path: Path) -> None:
    path.write_text(
        "\n".join(
            [
                ".model tiny",
                ".inputs a b c",
                ".outputs y",
                ".names a b n1",
                "11 1",
                ".names n1 c n2",
                "1- 1",
                "-1 1",
                ".names a c n3",
                "11 1",
                ".names n2 n3 y",
                "1- 1",
                "-1 1",
                ".end",
            ]
        ),
        encoding="utf-8",
    )


def candidates(rows):
    return pd.DataFrame(rows)


def empty():
    return cpmap.empty_candidate_frame()


def test_longest_path_extraction_on_small_blif(tmp_path):
    blif = tmp_path / "tiny.blif"
    write_blif(blif)

    path = cpmap.extract_longest_internal_path(parse_blif(blif))

    assert [node.node for node in path] == ["n1", "n2", "y"]
    assert [node.level for node in path] == [1, 2, 3]
    assert [node.path_index for node in path] == [1, 2, 3]


def test_mapping_priority_exact_before_sat_and_approximate():
    exact = candidates(
        [
            {
                "benchmark": "b",
                "optimization": "rewrite",
                "optimized_node": "n",
                "rank": 1,
                "original_candidate": "orig_exact",
                "combined_score": 1.0,
                "support_overlap": 1.0,
                "simulation_similarity": 1.0,
                "is_formal_exact_mode": True,
            }
        ]
    )
    sat = candidates(
        [
            {
                "benchmark": "b",
                "optimization": "rewrite",
                "optimized_node": "n",
                "rank": 1,
                "original_candidate": "orig_sat",
                "combined_score": 0.9,
                "support_overlap": 1.0,
                "simulation_similarity": 0.9,
            }
        ]
    )
    approx = candidates(
        [
            {
                "benchmark": "b",
                "optimization": "rewrite",
                "optimized_node": "n",
                "rank": 1,
                "original_candidate": "orig_approx",
                "combined_score": 0.8,
                "support_overlap": 1.0,
                "simulation_similarity": 0.8,
                "distance": 0.01,
                "similarity": 0.99,
                "distance_mode": "exact",
                "is_formal_distance": True,
            }
        ]
    )

    choice = cpmap.choose_mapping_for_node("b", "rewrite", "n", exact, empty(), sat, approx)

    assert choice.category == "exact_signature_match"
    assert choice.original_node == "orig_exact"


def test_complemented_priority_before_sat_verified():
    complemented = candidates(
        [
            {
                "benchmark": "b",
                "optimization": "balance",
                "optimized_node": "n",
                "rank": 1,
                "original_candidate": "orig_not",
                "combined_score": 0.95,
                "support_overlap": 1.0,
                "simulation_similarity": 0.95,
            }
        ]
    )
    sat = candidates(
        [
            {
                "benchmark": "b",
                "optimization": "balance",
                "optimized_node": "n",
                "rank": 1,
                "original_candidate": "orig_sat",
                "combined_score": 0.9,
                "support_overlap": 1.0,
                "simulation_similarity": 0.9,
            }
        ]
    )

    choice = cpmap.choose_mapping_for_node("b", "balance", "n", empty(), complemented, sat, empty())

    assert choice.category == "complemented_equivalence"
    assert choice.original_node == "orig_not"


def test_approximate_threshold_filtering():
    rows = candidates(
        [
            {"sat_status": "rejected", "distance": 0.03, "benchmark": "b"},
            {"sat_status": "rejected", "distance": 0.07, "benchmark": "b"},
            {"sat_status": "verified", "distance": 0.01, "benchmark": "b"},
        ]
    )
    filtered = rows[
        (rows["sat_status"] == "rejected")
        & (rows["distance"].notna())
        & (rows["distance"] <= 0.05)
    ]

    assert len(filtered) == 1
    assert filtered.iloc[0]["distance"] == 0.03


def test_unresolved_when_no_layer_has_candidate():
    choice = cpmap.choose_mapping_for_node(
        "missing", "rewrite", "n", empty(), empty(), empty(), empty()
    )

    assert choice.category == "unresolved"
    assert choice.original_node == ""


def test_output_schema_for_mapping_rows(tmp_path, monkeypatch):
    variants = tmp_path / "variants"
    variants.mkdir()
    blif = variants / "external_iscas85_c432_rewrite.blif"
    write_blif(blif)

    monkeypatch.setattr(cpmap, "ROOT", tmp_path)
    monkeypatch.setattr(cpmap, "load_exact_candidates", lambda: empty())
    monkeypatch.setattr(cpmap, "load_complemented_candidates", lambda: empty())
    monkeypatch.setattr(cpmap, "load_sat_cec_proven_equivalent_candidates", lambda: empty())
    monkeypatch.setattr(cpmap, "load_approximate_candidates", lambda threshold: empty())

    rows = cpmap.build_mapping_rows([("external_iscas85_c432", "rewrite")], threshold=0.05)

    expected = {
        "benchmark",
        "circuit",
        "optimization",
        "path_length",
        "path_index",
        "optimized_node",
        "optimized_depth",
        "mapped_original_node",
        "mapping_category",
        "confidence",
        "distance",
        "combined_score",
        "support_overlap",
        "simulation_similarity",
        "explanation",
    }
    assert expected.issubset(rows.columns)
    assert set(rows["mapping_category"]) == {"unresolved"}


def test_choice_from_row_normalizes_legacy_sat_category():
    sat_row = pd.Series(
        {
            "original_candidate": "orig_sat",
            "combined_score": 0.9,
            "support_overlap": 1.0,
            "simulation_similarity": 0.9,
        }
    )
    choice = cpmap.choice_from_row(
        "sat_verified_nonexact",
        sat_row,
        "legacy category",
    )
    assert choice.category == "sat_cec_proven_equivalent"
    assert choice.confidence == 1.0
