import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from boundary_graph import CircuitGraph
from semantic_region import (
    ACTIVE_REGION_SOURCES,
    SEMANTIC_REGION_FIELDS,
    SEMANTIC_REGION_SCHEMA_VERSION,
    SemanticRegion,
    file_hash,
    output_cone_region,
)


def write_blif(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "tiny.blif"
    path.write_text(text.strip() + "\n", encoding="utf-8")
    return path


def test_semantic_region_serialization_is_stable():
    region = SemanticRegion(
        region_id="case__identity__ground_truth_region",
        case_id="case",
        benchmark="case",
        family="boolean",
        operator="and",
        optimization="identity",
        source_type="ground_truth_region",
        spec_circuit_path="benchmarks/semantic_recovery/blif/source/case.blif",
        impl_circuit_path="benchmarks/semantic_recovery/blif/source/case.blif",
        region_nodes=("n1", "y_0"),
        boundary_inputs=("a_0", "b_0"),
        boundary_outputs=("y_0",),
        observable_outputs=("y_0",),
        ground_truth_expression="a & b",
        ground_truth_input_buses=({"name": "a", "width": 1}, {"name": "b", "width": 1}),
        ground_truth_output_buses=({"name": "y", "width": 1},),
        ground_truth_signedness="unsigned",
        ground_truth_width_semantics="fixed",
        formal_scope="none",
        context_mode="not_applicable",
        source_manifest="results/semantic_recovery/semantic_benchmark_manifest.csv",
        spec_fingerprint="{}",
        impl_fingerprint="{}",
        declared=True,
        circuit_available=True,
        region_available=True,
        structurally_valid=True,
        interface_extractable=True,
        eligible=True,
        attempted=True,
        status="eligible",
        skip_reason="",
    )
    row = region.to_csv_row()
    assert list(row) == SEMANTIC_REGION_FIELDS
    assert row["schema_version"] == SEMANTIC_REGION_SCHEMA_VERSION
    assert json.loads(row["region_nodes"]) == ["n1", "y_0"]
    assert row["eligible"] == "true"
    assert "ground_truth_region" in ACTIVE_REGION_SOURCES
    assert "whole_output_cone" in ACTIVE_REGION_SOURCES


def test_whole_output_cone_uses_canonical_non_pi_region(tmp_path):
    graph = CircuitGraph.from_blif(
        write_blif(
            tmp_path,
            """
            .model tiny
            .inputs a b sel
            .outputs y z
            .names a b n1
            11 1
            .names sel n1 y
            11 1
            .names a z
            1 1
            .end
            """,
        )
    )
    assert output_cone_region(graph, ("y",)) == ("n1", "y")
    assert output_cone_region(graph, ("y", "z")) == ("n1", "y", "z")


def test_circuit_file_hash_ignores_abc_timestamp_comments(tmp_path):
    first = tmp_path / "first.blif"
    second = tmp_path / "second.blif"
    body = ".model m\n.inputs a\n.outputs y\n.names a y\n1 1\n.end\n"
    first.write_text('# Benchmark "m" written by ABC on Thu Jul 16 01:00:00 2026\n' + body, encoding="utf-8")
    second.write_text('# Benchmark "m" written by ABC on Thu Jul 16 19:00:00 2026\n' + body, encoding="utf-8")
    assert file_hash(first) == file_hash(second)
