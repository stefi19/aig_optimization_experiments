import csv
from pathlib import Path

from boundary_semantics import write_csv


def test_semantics_csv_writer_has_stable_headers(tmp_path):
    path = tmp_path / "x.csv"
    write_csv(path, [{"b": 2, "a": 1}], ["a", "b"])

    assert path.read_text(encoding="utf-8").splitlines()[0] == "a,b"


def test_identity_result_schema_fixture(tmp_path):
    path = tmp_path / "identity.csv"
    write_csv(
        path,
        [
            {
                "case_id": "c",
                "top_level_classification": "success",
                "ebi_exact_match": True,
                "ebo_exact_match": True,
                "region_exact_match": True,
            }
        ],
        ["case_id", "top_level_classification", "ebi_exact_match", "ebo_exact_match", "region_exact_match"],
    )

    row = next(csv.DictReader(path.open(newline="", encoding="utf-8")))
    assert row["top_level_classification"] == "success"
    assert row["ebi_exact_match"] == "True"


def test_missing_spec_is_infrastructure_skip_semantics():
    row = {
        "eligible": True,
        "executable": False,
        "structurally_valid": True,
        "attempted": False,
        "top_level_classification": "infrastructure_skip",
        "failure_reason": "missing_spec_circuit",
    }

    assert row["top_level_classification"] == "infrastructure_skip"
    assert row["attempted"] is False
