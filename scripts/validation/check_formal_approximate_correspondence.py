import argparse
import csv
import hashlib
import json
import tempfile
from collections import defaultdict
from pathlib import Path

from analyze_blif_matches import parse_blif
from contextual_error_metrics import evaluate_network, exact_patterns
from necessity_first_rewrites import validate_rewritten_graph
from scripts.analysis.audit_approximate_distance import ROOT, abc_call, sha
from scripts.validation.approximate_oracle import oracle_pair, scalar_values
from scripts.validation.check_evidence_advancement import _parse_expression, _evaluate_source_expression


def read(path):
    return list(csv.DictReader(path.open()))


def independent_pool(path,config):
    net=parse_blif(path)
    support={name:{name} for name in net.inputs}
    for node in net.nodes:
        support[node.output]=set().union(*(support[n] for n in node.inputs))
    names=sorted(support,key=lambda n:(len(support[n]),n))
    names=[n for n in names if len(support[n])<=config["max_support_inputs"]][:config["max_candidate_signals"]]
    expressions=[f"not({n})" for n in names]
    for i,left in enumerate(names):
        for right in names[i+1:]:
            if len(support[left]|support[right])<=config["max_support_inputs"]:
                expressions.extend(f"{op}({left},{right})" for op in ["and","or","xor","xnor","nand","nor"])
    return hashlib.sha256(json.dumps(expressions).encode()).hexdigest(),len(expressions)


def check(out,with_abc=False,quick=False):
    manifest=out/"measurement_manifest.json"
    assert manifest.is_file(),"missing measurement manifest"
    for recorded,digest in json.loads(manifest.read_text())["files"].items():
        assert sha(ROOT/recorded)==digest,recorded
    config_path=ROOT/"configs/formal_approximate_correspondence.json"
    config=json.loads(config_path.read_text())
    meta=json.loads((out/"provenance.json").read_text())
    assert meta["config_sha256"]==sha(config_path)
    cases={r["case_id"]:r for r in read(out/"cases.csv")}
    rows=read(out/"candidates.csv")
    assert sum(r["evidence"]=="controlled_algebraic_rewrite" for r in cases.values())==len(config["families"])*len(config["replicates"])*2
    checked_cases=set()
    pairs=set()
    for row in rows:
        key=(row["case_id"],row["candidate"])
        assert key not in pairs
        pairs.add(key)
        case=cases[row["case_id"]]
        source,optimized=ROOT/case["source"],ROOT/case["optimized"]
        if case["case_id"] not in checked_cases:
            assert sha(source)==case["source_sha256"] and sha(optimized)==case["optimized_sha256"]
            checked_cases.add(case["case_id"])
        assert int(row["lineage"])==int(bool(case["lineage"]) and row["candidate"]==case["lineage"])
        d=float(row["distance"])
        e=float(row["contextual_error"])
        assert float(row["complement_distance"])==min(d,1-d)
        assert 0<=e<=d<=1 and e<=float(row["observability"])
        for field,value in [("global_status",d),("complement_status",1-d),("contextual_status",e),("best_contextual_status",float(row["best_contextual_error"]))]:
            assert row[field] in {"sat","unsat","unknown"}
            if row[field]!="unknown":
                assert (row[field]=="unsat")== (value==0)
        if not quick and case["evidence"]=="controlled_algebraic_rewrite":
            oracle=oracle_pair(parse_blif(source),parse_blif(optimized),case["target"],row["candidate"])
            for name in ("distance","contextual_error","observability","output_hamming","mae","wce","worst_hamming"):
                assert float(row[name])==oracle[name],(key,name)
        for field,context in [("global_counterexample",False),("contextual_counterexample",True)]:
            assignment=json.loads(row[field])
            if assignment:
                source_net,opt_net=parse_blif(source),parse_blif(optimized)
                f=scalar_values(source_net,assignment,[row["candidate"]])[row["candidate"]]
                baseline=scalar_values(opt_net,assignment,[case["target"],*opt_net.outputs])
                if context:
                    changed=scalar_values(opt_net,assignment,opt_net.outputs,{case["target"]:f})
                    assert any(baseline[y]!=changed[y] for y in opt_net.outputs)
                else:
                    assert f!=baseline[case["target"]]
    for case in cases.values():
        assert {c for q,c in pairs if q==case["case_id"]}==set(json.loads(case["candidates"]))
    lookup={(r["case_id"],r["candidate"]):r for r in rows}
    for sample in read(out/"sampling.csv"):
        assert float(sample["truth"])==float(lookup[(sample["case_id"],sample["candidate"])]["distance"])
        assert int(sample["seed"]) in config["sampling_seeds"]
        assert int(sample["sample_count"])==config["sample_count"]
        from scripts.analysis.approximate_correspondence import interval
        count=int(sample["sample_count"])
        lo,hi=interval(round(float(sample["estimate"])*count),count,config["confidence_alpha"])
        assert abs(lo-float(sample["lower"]))<1e-12 and abs(hi-float(sample["upper"]))<1e-12
    grouped=defaultdict(list)
    reconstruction=read(out/"reconstruction.csv")
    abc=(ROOT/".abc_build/abc_repo/abc").resolve()
    cec_checked=set()
    pool_cache={}
    for row in reconstruction:
        grouped[(row["target_id"],row["seed"],row["budget"])].append(row)
        source_key=row["source_sha256"]
        if source_key not in pool_cache:
            pool_cache[source_key]=independent_pool(ROOT/row["source"],config["reconstruction"])
        assert row["candidate_pool_hash"]==pool_cache[source_key][0]
        assert int(row["candidate_pool_size"])==pool_cache[source_key][1]
        assert 0<=int(row["exact_checks"])<=min(int(row["budget"]),int(row["candidate_pool_size"]))
        assert sha(ROOT/row["source"])==row["source_sha256"] and sha(ROOT/row["optimized"])==row["optimized_sha256"]
        if int(row["accepted"]):
            assert row["graph_active"]=="True" and row["source_cec"]==row["cross_cec"]=="equivalent"
            path=ROOT/row["artifact"]
            assert path.is_file() and sha(path)==row["artifact_sha256"]
            assert validate_rewritten_graph(path,row["target"])=="valid"
            optimized,source,rewrite=parse_blif(ROOT/row["optimized"]),parse_blif(ROOT/row["source"]),parse_blif(path)
            patterns=exact_patterns(source.inputs)
            sv,ov,rv=[evaluate_network(net,patterns) for net in (source,optimized,rewrite)]
            assert all(sv[y]==ov[y]==rv[y] for y in source.outputs)
            expression=_parse_expression(row["expression"])
            assert expression is not None
            vector=_evaluate_source_expression(source,expression)
            assert tuple((ov[row["target"]]>>i)&1 for i in range(patterns.pattern_count))==vector
            assert ov[row["target"]]==rv[row["target"]]
            original_driver=next(n for n in optimized.nodes if n.output==row["target"])
            rewritten_driver=next(n for n in rewrite.nodes if n.output==row["target"])
            assert (original_driver.inputs,original_driver.cover)!=(rewritten_driver.inputs,rewritten_driver.cover)
            if with_abc and row["artifact_sha256"] not in cec_checked:
                for label,a,b in [("source",row["source"],row["artifact"]),("cross",row["artifact"],row["optimized"])]:
                    assert abc_call(abc,f"cec {a} {b}",out/"validation"/f"{row['artifact_sha256'][:16]}_{label}.log")=="equivalent"
                cec_checked.add(row["artifact_sha256"])
        else:
            assert row["blocker"]
    for key,group in grouped.items():
        assert len(group)==2 and {r["ordering"] for r in group}=={"enumeration","sampled_distance"}
        assert len({r["candidate_pool_hash"] for r in group})==1
        assert len({r["candidate_pool_size"] for r in group})==1
    for audit_row in read(out/"audit/replay.csv"):
        assert float(audit_row["corrected_distance"])==float(audit_row["independent_oracle_distance"])
        assert abs(float(audit_row["historical_distance"])-float(audit_row["legacy_replay_distance"]))<1e-12
        assert audit_row["pi_alignment"]=="True"
        if audit_row["fresh_cec"]=="equivalent":
            assert float(audit_row["corrected_distance"])==0
        assert audit_row["fresh_cec"] in {"equivalent","disproved","unknown","timeout"}
    for path,digest in json.loads((out/"audit/historical_inputs.json").read_text()).items():
        assert sha(ROOT/path)==digest
    print(f"Validated {len(cases)} cases, {len(rows)} candidate rows, {len(reconstruction)} paired reconstruction rows; {len(cec_checked)} distinct artifacts independently CEC-replayed")


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--with-abc",action="store_true")
    parser.add_argument("--quick",action="store_true")
    args=parser.parse_args()
    check(ROOT/"results/formal_approximate_correspondence",args.with_abc,args.quick)


if __name__=="__main__":
    main()
