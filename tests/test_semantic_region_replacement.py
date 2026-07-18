import pytest

z3 = pytest.importorskip("z3")

from analyze_blif_matches import parse_blif
from boundary_graph import CircuitGraph
from semantic_region_replacement import derive_closed_region, full_adder_module, write_replaced_blif


def write_fa(tmp_path):
    path = tmp_path / "fa.blif"
    path.write_text(
        """.model fa
.inputs a b cin
.outputs sum cout
.names a b xab
10 1
01 1
.names xab cin sum
10 1
01 1
.names a b ab
11 1
.names a cin ac
11 1
.names b cin bc
11 1
.names ab ac bc cout
1-- 1
-1- 1
--1 1
.end
""",
        encoding="utf-8",
    )
    return path


def test_closed_region_derivation_multi_output(tmp_path):
    path = write_fa(tmp_path)
    graph = CircuitGraph.from_blif(path)
    region, cut, edges, status = derive_closed_region(graph, ("sum", "cout"))
    assert status == "closed"
    assert set(cut) == {"a", "b", "cin"}
    assert {"sum", "cout"} <= set(region)


def test_graph_active_replacement_reuses_output_cut(tmp_path):
    path = write_fa(tmp_path)
    graph = CircuitGraph.from_blif(path)
    region, _, _, status = derive_closed_region(graph, ("sum", "cout"))
    assert status == "closed"
    out = tmp_path / "replaced.blif"
    result = write_replaced_blif(path, region, full_adder_module(), out)
    assert result["graph_rewrite_status"] == "valid"
    assert result["graph_active"] == "true"
    net = parse_blif(out)
    assert {"sum", "cout"} <= {node.output for node in net.nodes}
