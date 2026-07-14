import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import build_source_map_prototype as source_map
import probe_yosys_source_metadata as yosys_probe


def test_unavailable_yosys_probe_schema(tmp_path, monkeypatch):
    monkeypatch.setattr(yosys_probe, "find_yosys", lambda: None)
    result = yosys_probe.run_probe(ROOT / "benchmarks" / "source_examples" / "simple_pipeline.v")
    csv_out = tmp_path / "probe.csv"
    md_out = tmp_path / "probe.md"
    yosys_probe.write_outputs(result, csv_out, md_out)

    with csv_out.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    assert list(rows[0].keys()) == yosys_probe.PROBE_COLUMNS
    assert rows[0]["available"] == "false"
    assert "Yosys not found" in md_out.read_text(encoding="utf-8")


def test_parse_src_attribute_file_and_line():
    source_file, line = source_map.parse_src_attribute("benchmarks/source_examples/simple_pipeline.v:17.18-17.28")
    assert source_file == "benchmarks/source_examples/simple_pipeline.v"
    assert line == "17"


def test_source_map_rows_from_sample_json(tmp_path):
    sample = {
        "modules": {
            "\\simple_pipeline": {
                "netnames": {
                    "\\mix": {
                        "bits": [1],
                        "attributes": {"src": "benchmarks/source_examples/simple_pipeline.v:15.12-15.15"},
                    },
                    "\\gated": {
                        "bits": [2],
                        "attributes": {},
                    },
                }
            }
        }
    }
    path = tmp_path / "sample.json"
    path.write_text(json.dumps(sample), encoding="utf-8")
    rows = source_map.rows_from_yosys_json(path, ["mix", "gated"])
    by_signal = {row.rtl_signal: row for row in rows}

    assert by_signal["mix"].source_line == "15"
    assert by_signal["mix"].confidence == "name+attribute"
    assert by_signal["gated"].confidence == "name-only"


def test_source_map_output_schema_and_skip(tmp_path, monkeypatch):
    monkeypatch.setattr(source_map, "find_yosys", lambda: None)
    rows = source_map.build_source_map(ROOT / "benchmarks" / "source_examples" / "simple_pipeline.v")
    csv_out = tmp_path / "source_map.csv"
    md_out = tmp_path / "source_map.md"
    source_map.write_source_map(rows, csv_out, md_out)

    with csv_out.open(newline="", encoding="utf-8") as fh:
        read_rows = list(csv.DictReader(fh))
    assert list(read_rows[0].keys()) == source_map.SOURCE_MAP_COLUMNS
    assert all(row["available"] == "false" for row in read_rows)
    assert "`skipped`" in md_out.read_text(encoding="utf-8")


def test_next_steps_explanation_generation(tmp_path):
    out = tmp_path / "next_steps.md"
    source_map.write_next_steps(out)
    text = out.read_text(encoding="utf-8")
    assert "optimized path node" in text
    assert "RTL signal" in text
    assert "register insertion suggestion" in text
