from pathlib import Path

from boundary_graph import CircuitGraph
from boundary_semantics import identity_anchor_map, recover_semantic_boundary
from coi_model import (
    derive_boundary_inputs,
    derive_boundary_outputs,
    extract_region_from_boundaries,
    normalize_coi,
    validate_coi,
)


def write_blif(path: Path, text: str) -> Path:
    path.write_text(text.strip() + "\n", encoding="utf-8")
    return path


def graph(tmp_path, text: str) -> CircuitGraph:
    return CircuitGraph.from_blif(write_blif(tmp_path / "m.blif", text))


CHAIN = """
.model m
.inputs a
.outputs y
.names a n1
1 1
.names n1 n2
1 1
.names n2 n3
1 1
.names n3 y
1 1
.end
"""


def test_linear_chain_boundary_derivation(tmp_path):
    g = graph(tmp_path, CHAIN)
    region = {"n2"}

    assert derive_boundary_inputs(g, region) == ("n1",)
    assert derive_boundary_outputs(g, region) == ("n2",)


def test_po_boundary_derivation(tmp_path):
    g = graph(tmp_path, CHAIN)
    region = {"y"}

    assert derive_boundary_inputs(g, region) == ("n3",)
    assert derive_boundary_outputs(g, region) == ("y",)


def test_shared_fanout_node_becomes_boundary_output(tmp_path):
    g = graph(
        tmp_path,
        """
.model m
.inputs a b
.outputs y z
.names a b n1
11 1
.names n1 n2
1 1
.names n2 y
1 1
.names n1 z
1 1
.end
""",
    )

    assert derive_boundary_outputs(g, {"n1", "n2"}) == ("n1", "n2")


def test_validation_reports_missing_and_extra_boundaries(tmp_path):
    g = graph(tmp_path, CHAIN)
    coi = normalize_coi(g, benchmark="b", optimization="*", coi_name="c", region_nodes={"n2"}, source="test")
    bad = coi.__class__(
        benchmark=coi.benchmark,
        optimization=coi.optimization,
        coi_name=coi.coi_name,
        region_nodes=coi.region_nodes,
        boundary_inputs=tuple(),
        boundary_outputs=("n2", "n3"),
        source=coi.source,
    )

    result = validate_coi(g, bad)

    assert "missing_boundary_input:n1" in result.errors
    assert "extra_boundary_output:n3" in result.errors


def test_region_extraction_exact_for_identity_chain(tmp_path):
    g = graph(tmp_path, CHAIN)
    extracted = extract_region_from_boundaries(g, {"n1"}, {"n2"}, required_nodes={"n2"})

    assert extracted.region_nodes == ("n2",)
    assert extracted.missing_required_nodes == tuple()
    assert extracted.unexpected_nodes == tuple()


def test_identity_recovery_exact_zero_extension(tmp_path):
    g = graph(tmp_path, CHAIN)
    coi = normalize_coi(g, benchmark="b", optimization="*", coi_name="c", region_nodes={"n2"}, source="test")

    result = recover_semantic_boundary(g, coi, identity_anchor_map(g))

    assert result.success
    assert result.boundary_extension_ratio == 0.0
    assert result.ebi_exact_match
    assert result.ebo_exact_match
    assert result.region_exact_match


def test_disconnected_region_is_invalid(tmp_path):
    g = graph(
        tmp_path,
        """
.model m
.inputs a b
.outputs y z
.names a n1
1 1
.names n1 y
1 1
.names b n2
1 1
.names n2 z
1 1
.end
""",
    )
    coi = normalize_coi(g, benchmark="b", optimization="*", coi_name="c", region_nodes={"n1", "n2"}, source="test")

    assert "disconnected_region" in validate_coi(g, coi).errors
