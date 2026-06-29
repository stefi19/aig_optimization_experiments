import csv
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_REPO_ROOT))
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from investigate_abc_provenance import (
    ProvenanceRow,
    analyze_output_features,
    controlled_blif_text,
    detect_node_survival,
    expected_nodes,
    parse_blif_defined_names,
    write_csv,
)


def test_controlled_duplicate_and_blif_contains_expected_internal_names():
    text = controlled_blif_text("duplicate_and")
    assert ".model duplicate_and" in text
    assert expected_nodes("duplicate_and") == ["n_ab1", "n_ab2"]
    assert "n_ab1" in text
    assert "n_ab2" in text


def test_parse_blif_defined_names_reads_names_outputs():
    text = """
    .model sample
    .inputs a b
    .outputs y
    .names a b n1
    11 1
    .names n1 y
    1 1
    .end
    """
    assert parse_blif_defined_names(text) == ["n1", "y"]


def test_detect_node_survival_counts_expected_names_only():
    swept = """
    .names a b n_ab1
    11 1
    .names n_ab1 y
    1 1
    """
    survived, names = detect_node_survival(["n_ab1", "n_ab2"], swept)
    assert survived
    assert names == ["n_ab1"]


def test_output_feature_detection_for_explicit_classes():
    output = "Fraig completed. Equivalence class 1: n_ab1 n_ab2"
    merge_info_visible, classes_visible = analyze_output_features(output)
    assert not merge_info_visible
    assert classes_visible


def test_output_feature_detection_for_plain_stats_is_conservative():
    output = "network : i/o = 2/1 lat = 0 and = 1 lev = 1"
    merge_info_visible, classes_visible = analyze_output_features(output)
    assert not merge_info_visible
    assert not classes_visible


def test_provenance_csv_schema(tmp_path):
    out = tmp_path / "abc_provenance_probe.csv"
    row = ProvenanceRow(
        benchmark="duplicate_and",
        source_family="controlled",
        optimization="none",
        command_flow="fraig",
        supported=True,
        controlled_example="duplicate_and",
        node_names_survived=False,
        surviving_node_count=0,
        expected_node_count=2,
        merge_info_visible=True,
        equivalence_classes_exposed=False,
        node_count_before=3,
        node_count_after=2,
        level_count_before=2,
        level_count_after=1,
        runtime_seconds=0.01,
        swept_blif_path="",
        stdout_stderr_snippet="ok",
        notes="test row",
    )
    write_csv([row], out)
    with out.open(newline="", encoding="utf-8") as fh:
        header = next(csv.reader(fh))
    assert header == [
        "benchmark",
        "source_family",
        "optimization",
        "command_flow",
        "supported",
        "controlled_example",
        "node_names_survived",
        "surviving_node_count",
        "expected_node_count",
        "merge_info_visible",
        "equivalence_classes_exposed",
        "node_count_before",
        "node_count_after",
        "level_count_before",
        "level_count_after",
        "runtime_seconds",
        "swept_blif_path",
        "stdout_stderr_snippet",
        "notes",
    ]
