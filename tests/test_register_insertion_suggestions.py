import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import suggest_register_insertion_points as reg


def row(**overrides):
    base = {
        "benchmark": "external_iscas85_c432",
        "optimization": "rewrite",
        "mapped_original_node": "new_n10",
        "optimized_node": "new_n20",
        "path_index": "5",
        "path_length": "9",
        "mapping_category": "exact",
        "confidence": "1.0",
        "distance": "",
        "combined_score": "1.0",
        "support_overlap": "1.0",
        "simulation_similarity": "1.0",
    }
    base.update(overrides)
    return base


def test_split_balance_prefers_middle():
    assert reg.split_balance_score(5, 9) == 1.0
    assert reg.split_balance_score(1, 9) == 0.0
    assert reg.split_balance_score(4, 9) > reg.split_balance_score(2, 9)


def test_mapping_preference_order_affects_score():
    exact = reg.score_candidate(row(mapping_category="exact"))
    sat = reg.score_candidate(row(mapping_category="sat_verified_nonexact"))
    approx = reg.score_candidate(row(mapping_category="approximate_near_match", distance="0.03"))
    assert exact > sat > approx


def test_unresolved_nodes_are_avoided():
    rows = [
        row(mapping_category="unresolved", mapped_original_node="", path_index="5"),
        row(mapping_category="exact", mapped_original_node="new_n11", path_index="4"),
    ]
    suggestions = reg.build_suggestions(rows)
    assert len(suggestions) == 1
    assert suggestions[0].suggested_original_node == "new_n11"


def test_output_schema(tmp_path):
    suggestions = reg.build_suggestions([row()])
    out = tmp_path / "suggestions.csv"
    reg.write_csv(suggestions, out)
    with out.open(newline="", encoding="utf-8") as fh:
        read_rows = list(csv.DictReader(fh))
    assert list(read_rows[0].keys()) == reg.OUTPUT_COLUMNS
    assert read_rows[0]["suggested_original_node"] == "new_n10"


def test_example_generation(tmp_path):
    suggestions = reg.build_suggestions([
        row(benchmark="external_iscas85_c432"),
        row(benchmark="external_iscas85_c2670", optimized_node="new_n30"),
        row(benchmark="external_iscas85_c6288", optimized_node="new_n40"),
    ])
    out = tmp_path / "suggestions.md"
    reg.write_markdown(suggestions, out, example_count=3)
    text = out.read_text(encoding="utf-8")
    assert "Example Suggestions" in text
    assert "not automatic RTL edits" in text
    assert "external_iscas85_c432" in text
