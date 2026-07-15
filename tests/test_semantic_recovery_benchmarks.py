import csv
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts import check_semantic_recovery_benchmarks as checker
from scripts import generate_semantic_recovery_benchmarks as gen


def test_specs_are_deterministic_and_unique():
    first = gen.specs()
    second = gen.specs()
    assert [spec.case_id for spec in first] == [spec.case_id for spec in second]
    assert len({spec.case_id for spec in first}) == len(first)


def test_specs_cover_required_families_and_widths():
    specs = gen.specs()
    families = {spec.family for spec in specs}
    widths = {bus.width for spec in specs for bus in spec.inputs}
    assert checker.REQUIRED_FAMILIES <= families
    assert checker.REQUIRED_WIDTHS <= widths


def test_manifest_row_schema_and_json_fields():
    spec = next(spec for spec in gen.specs() if spec.case_id == "arithmetic_unsigned_add_w2")
    row = gen.manifest_row(spec, gen.SOURCE_BLIF_DIR / f"{spec.case_id}.blif")
    assert list(row) == gen.MANIFEST_FIELDS
    assert row["schema_version"] == gen.SCHEMA_VERSION
    assert row["exact_blif_available"] == "true"
    assert json.loads(row["input_widths"]) == {"a": 2, "b": 2}
    boundary = json.loads(row["ground_truth_boundary"])
    assert boundary["flat_inputs"] == ["a_0", "a_1", "b_0", "b_1"]
    assert boundary["flat_outputs"] == ["y_0", "y_1", "y_2"]


def test_truth_table_blif_for_xor_case_is_exact():
    spec = next(spec for spec in gen.specs() if spec.case_id == "boolean_bitwise_xor_w2")
    blif = gen.spec_to_blif(spec)
    assert ".model boolean_bitwise_xor_w2" in blif
    assert ".inputs a_0 a_1 b_0 b_1" in blif
    assert ".outputs y_0 y_1" in blif
    assert "1000 1" in blif
    assert "0110 1" in blif


def test_assignment_order_is_little_endian_and_stable():
    spec = next(spec for spec in gen.specs() if spec.case_id == "arithmetic_unsigned_add_w2")
    values = gen.assignment_to_buses(spec, 0b1001)
    assert values == {"a": 0b01, "b": 0b10}
    assert gen.pattern_for_assignment(spec, 0b1001) == "1001"


def test_checker_rejects_duplicate_manifest_ids(tmp_path):
    row = {
        field: ""
        for field in checker.MANIFEST_FIELDS
    }
    row.update(
        {
            "case_id": "dup",
            "family": "arithmetic",
            "input_widths": '{"a":2}',
            "output_widths": '{"y":2}',
            "ground_truth_region": "{}",
            "ground_truth_boundary": '{"flat_inputs":["a_0"],"flat_outputs":["y_0"]}',
            "source_rtl": str(tmp_path.relative_to(_REPO_ROOT) if tmp_path.is_relative_to(_REPO_ROOT) else tmp_path),
            "exact_blif_available": "false",
        }
    )
    problems = checker.validate_manifest([row, dict(row)])
    assert any("duplicate case_id" in problem for problem in problems)


def test_variant_csv_header_constant_matches_generator():
    assert checker.VARIANT_FIELDS == gen.VARIANT_FIELDS
    assert checker.MANIFEST_FIELDS == gen.MANIFEST_FIELDS


def test_write_csv_preserves_stable_header(tmp_path):
    out = tmp_path / "manifest.csv"
    row = {field: "" for field in gen.MANIFEST_FIELDS}
    gen.write_csv([row], out, gen.MANIFEST_FIELDS)
    with out.open(newline="", encoding="utf-8") as fh:
        reader = csv.reader(fh)
        assert next(reader) == gen.MANIFEST_FIELDS
