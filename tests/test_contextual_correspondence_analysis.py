import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import contextual_correspondence_analysis as cca


def test_summary_generation_counts():
    rows = [
        {"classification": "globally_exact", "contextual_error_mode": "exact", "cec_status": "not_run", "circuit": "c432", "optimization": "rewrite_z"},
        {"classification": "unsafe_candidate", "contextual_error_mode": "sampled", "cec_status": "rejected_non_equivalent", "circuit": "c432", "optimization": "dc2"},
    ]
    summary = cca.summarize(rows)
    assert {"summary_type": "classification", "name": "globally_exact", "count": 1} in summary
    assert {"summary_type": "contextual_mode", "name": "sampled", "count": 1} in summary


def test_write_rows_schema(tmp_path):
    out = tmp_path / "rows.csv"
    cca.write_rows(out, [{"a": 1, "b": 2}], ["a", "b"])
    with out.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    assert rows == [{"a": "1", "b": "2"}]


def test_select_candidates_respects_missing_files(tmp_path, monkeypatch):
    monkeypatch.setattr(cca, "RESULTS", tmp_path)
    assert cca.select_candidates(["c432"], ["dc2"], 5) == []
