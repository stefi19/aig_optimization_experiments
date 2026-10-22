from pathlib import Path

import pytest
import z3

from analyze_blif_matches import BlifNetwork, BlifNode, eval_cover
from blif_z3 import encode_cover
from contextual_error_metrics import exact_patterns, sampled_patterns
from scripts.analysis.approximate_correspondence import aligned, interval, measured_pair, sampled_order
from scripts.validation.approximate_oracle import oracle_pair


@pytest.mark.parametrize("cover,expected", [(["11 0"], 0b0111), (["1- 0", "-1 0"], 0b0001), (["00 1"], 0b0001), ([], 0)])
def test_offset_covers_agree_with_symbolic_backend(cover, expected):
    node = BlifNode("f", ["a", "b"], cover)
    p = exact_patterns(["a", "b"])
    assert eval_cover(node, p.values, p.mask) == expected
    a, b = z3.Bools("a b")
    expr = encode_cover([a,b], cover)
    for i in range(4):
        assert z3.is_true(z3.simplify(z3.substitute(expr, (a, z3.BoolVal(bool(i & 1))), (b, z3.BoolVal(bool(i & 2)))))) == bool(expected & (1 << i))


@pytest.mark.parametrize("inputs,cover", [(["a", "b"], ["1 1"]), (["a"], ["0 0", "1 1"]), (["a"], ["x 1"])])
def test_invalid_covers_rejected(inputs, cover):
    with pytest.raises(ValueError):
        eval_cover(BlifNode("f",inputs,cover), dict(a=0,b=0), 1)
    with pytest.raises(ValueError):
        encode_cover([z3.Bool(n) for n in inputs],cover)


def masked_pair():
    source = BlifNetwork(["a","b"],["y"],[BlifNode("f",["a","b"],["11 1"]),BlifNode("y",["f"],["1 1"])])
    optimized = BlifNetwork(["a","b"],["y"],[BlifNode("t",["a"],["1 1"]),BlifNode("y",["t","b"],["11 1"])])
    return source, optimized


def test_global_distance_is_not_contextual_error():
    source, optimized = masked_pair()
    metrics, _ = measured_pair(source,optimized,"t","f",exact_patterns(source.inputs))
    oracle = oracle_pair(source,optimized,"t","f")
    assert metrics["distance"] == oracle["distance"] == 0.25
    assert metrics["contextual_error"] == oracle["contextual_error"] == 0
    assert metrics["observability"] == 0.5


def test_complement_context_and_named_pi_alignment():
    source, optimized = masked_pair()
    source.inputs.reverse()
    metrics, _ = measured_pair(source,optimized,"t","f",exact_patterns(optimized.inputs),invert=True)
    oracle = oracle_pair(source,optimized,"t","f",invert=True)
    assert metrics["contextual_error"] == oracle["contextual_error"] == 0.5
    assert metrics["distance"] == 0.75
    source.inputs = ["a","c"]
    with pytest.raises(ValueError):
        aligned(source,optimized)


def test_sampling_never_has_exact_interval():
    source, optimized = masked_pair()
    m, _ = measured_pair(source,optimized,"t","f",sampled_patterns(source.inputs,128,7))
    assert m["mode"] == "sampled"
    assert m["distance_lower"] < m["distance_upper"]
    assert interval(0,128)[1] > 0


def test_order_preserves_pool_and_seed():
    proposals=[dict(ordinal=0,vector=(0,0,0,0)),dict(ordinal=1,vector=(0,1,0,1))]
    ordered=sampled_order(proposals,(0,1,0,1),7,8)
    assert ordered[0]["ordinal"] == 1
    assert set(x["ordinal"] for x in ordered) == {0,1}
    assert ordered == sampled_order(proposals,(0,1,0,1),7,8)


def test_bounded_reconstruction_pool_and_exhaustive_gate():
    from source_blind_counterpart_placement import _find_expression_match
    candidates=[dict(name="a",support=("a",),vector=(0,1,0,1)),dict(name="b",support=("b",),vector=(0,0,1,1))]
    target=(0,0,0,1)
    pools=[]
    for ordering in ["enumeration","sampled_distance"]:
        options=dict(ordering=ordering,seed=7,sample_count=8,budget=8)
        match=_find_expression_match(target,candidates,2,options)
        assert match["expression"]=="and(a,b)"
        assert options["exact_checks"]<=8
        pools.append(options["candidate_pool_hash"])
    assert len(set(pools))==1
    options=dict(ordering="enumeration",seed=7,sample_count=8,budget=0)
    assert _find_expression_match(target,candidates,2,options) is None
    assert options["exact_checks"]==0


def test_no_abc_cannot_promote_graph_rewrite(tmp_path):
    from source_blind_counterpart_placement import _abc_cec
    assert _abc_cec(None,tmp_path/"source",tmp_path/"rewrite")=="abc_unavailable"


def test_staged_cec_handles_space_paths(tmp_path):
    from contextual_error_metrics import write_blif
    from scripts.abc.cec import staged_cec
    abc=Path(__file__).resolve().parents[1]/".abc_build/abc_repo/abc"
    if not abc.is_file():
        pytest.skip("ABC unavailable")
    folder=tmp_path/"directory with spaces"
    folder.mkdir()
    source,_=masked_pair()
    a,b=folder/"left input.blif",folder/"right input.blif"
    write_blif(source,a)
    write_blif(source,b)
    assert staged_cec(abc,a,b)[0]=="equivalent"


def test_packed_source_vectors_match_independent_scalar():
    from source_blind_counterpart_placement import _bit_vector
    from scripts.validation.approximate_oracle import scalar_values
    source,_=masked_pair()
    expected=tuple(scalar_values(source,dict(a=i&1,b=(i>>1)&1),["f"])["f"] for i in range(4))
    assert _bit_vector(source,"f")==expected


def test_relocated_historical_certificate_requires_matching_hash(tmp_path,monkeypatch):
    from scripts.validation import check_formal_locality_barrier_results as checker
    from semantic_region import file_hash
    root=tmp_path/"aig_optimization_experiments"
    root.mkdir()
    artifact=root/"source.blif"
    artifact.write_text(".model f\n.inputs a\n.outputs a\n.end\n")
    monkeypatch.setattr(checker,"ROOT",root)
    recorded="/old/workspace/aig_optimization_experiments/source.blif"
    assert checker._certificate_path(recorded,file_hash(artifact))==artifact
    assert checker._certificate_path(recorded,"bad_hash") is None
