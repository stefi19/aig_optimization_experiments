import argparse
import csv
import hashlib
import itertools
import json
import platform
import random
import subprocess
import time
from pathlib import Path

import z3

from analyze_blif_matches import BlifNetwork, BlifNode, parse_blif, depth_similarity
from blif_z3 import encode_blif
from contextual_error_metrics import evaluate_network, exact_patterns, sampled_patterns, write_blif
from formal_locality_barriers import structural_supports
from scripts.analysis.approximate_correspondence import SCHEMA, measured_pair, rank_candidates
from scripts.analysis.audit_approximate_distance import ROOT, FLOWS, abc_call, audit, sha, write_csv
from scripts.analysis.critical_path_back_mapping import extract_longest_internal_path
from scripts.validation.approximate_oracle import oracle_pair


def truth_node(name, inputs, function):
    essential = []
    for i, signal in enumerate(inputs):
        if any(function(dict(zip(inputs, bits))) != function(dict(zip(inputs, bits[:i]+(1-bits[i],)+bits[i+1:]))) for bits in itertools.product((0,1), repeat=len(inputs))):
            essential.append(signal)
    cover = []
    for bits in itertools.product((0,1), repeat=len(essential)):
        assignment = dict.fromkeys(inputs,0)
        assignment.update(zip(essential,bits))
        if function(assignment):
            cover.append("".join(map(str,bits))+" 1" if bits else "1")
    return BlifNode(name,essential,cover)


def build_case(out, family, width, replicate, split, config):
    rng=random.Random(config["seed"]+replicate+1000*width+config["families"].index(family)*100)
    inputs=[f"x{i}" for i in range(width)]
    shuffled=inputs.copy()
    rng.shuffle(shuffled)
    a,b=shuffled[:2]
    rest=shuffled[2:]
    rare=lambda x: int(all(x[k] for k in rest))
    base=lambda x:x[a]
    ancestor={"odc_factor":lambda x:x[a]&x[b], "reconvergent_mask":lambda x:x[a]^x[b],
              "complement":lambda x:1-x[a], "rare_observable":lambda x:x[a]^rare(x),
              "exact_factor":lambda x:x[a]&x[b], "missing_representation":None}[family]
    if family in {"exact_factor","missing_representation"}:
        base=lambda x:x[a]&x[b] if family=="exact_factor" else x[a]^x[b]
    ids=list(range(config["candidate_decoys"]+int(ancestor is not None)))
    rng.shuffle(ids)
    candidates=[]
    lineage=""
    if ancestor is not None:
        lineage=f"s{ids.pop():03}"
        candidates.append(truth_node(lineage,inputs,ancestor))
    for index,ident in enumerate(ids):
        if index==0:
            fn=(lambda x:x[a]^(rare(x)&x[b])) if family=="rare_observable" else (lambda x:x[a])
        elif index==1:
            fn=(lambda x:1^x[a]^(rare(x)&x[b])) if family=="rare_observable" else (lambda x:1-x[a])
        elif index==2:
            fn=lambda x:x[b]
        else:
            table=[int(rng.random() < (0.08 if index%2 else 0.5)) for _ in range(1<<width)]
            fn=lambda x,table=table:table[sum(x[k]<<i for i,k in enumerate(inputs))]
        candidates.append(truth_node(f"s{ident:03}",inputs,fn))
    rng.shuffle(candidates)
    rare_node=truth_node("rare",inputs,rare)
    decoy_names=[n.output for n in candidates if n.output!=lineage]
    aux_nodes=[]
    last=decoy_names[0]
    for index,signal in enumerate(decoy_names[1:]):
        name="aux" if index==len(decoy_names)-2 else f"aux_{index}"
        aux_nodes.append(BlifNode(name,[last,signal],["01 1","10 1"]))
        last=name
    source_nodes=[*candidates,rare_node]
    optimized_nodes=[*candidates,rare_node,truth_node("t",inputs,base)]
    if family=="odc_factor":
        ys=BlifNode("y",[lineage],["1 1"])
        yo=BlifNode("y",["t",b],["11 1"])
    elif family=="reconvergent_mask":
        ys=BlifNode("y",[lineage,b],["10 1"])
        yo=BlifNode("y",["t",b],["10 1"])
    elif family=="complement":
        ys=BlifNode("y",[lineage],["0 1"])
        yo=BlifNode("y",["t"],["1 1"])
    elif family=="rare_observable":
        ys=BlifNode("y",[lineage],["1 1"])
        yo=BlifNode("y",["t","rare"],["01 1","10 1"])
    elif family=="exact_factor":
        ys=BlifNode("y",[lineage],["1 1"])
        yo=BlifNode("y",["t"],["1 1"])
    else:
        ys=truth_node("y",inputs,lambda x:(x[a]^x[b])&x[rest[0]])
        yo=BlifNode("y",["t",rest[0]],["11 1"])
    source=BlifNetwork(inputs,["y","aux"],[*source_nodes,ys,*aux_nodes])
    optimized=BlifNetwork(inputs,["y","aux"],[*optimized_nodes,yo,*aux_nodes])
    case_id=f"{split}_{family}_{replicate}"
    source_path=out/f"{case_id}.source.blif"
    optimized_path=out/f"{case_id}.optimized.blif"
    write_blif(source,source_path)
    write_blif(optimized,optimized_path)
    return dict(case_id=case_id,family=family,split=split,evidence="controlled_algebraic_rewrite",width=width,
                replicate=replicate,source=str(source_path.relative_to(ROOT)),optimized=str(optimized_path.relative_to(ROOT)),
                target="t",lineage=lineage,candidates=json.dumps([n.output for n in candidates]),
                source_sha256=sha(source_path),optimized_sha256=sha(optimized_path),
                lineage_basis="generator_algebraic_rewrite_witness" if lineage else "no_designated_ancestor")


def prove(left,right,timeout,inputs):
    solver=z3.Solver()
    solver.set(timeout=timeout)
    solver.add(left != right)
    status=solver.check()
    witness={name:int(z3.is_true(solver.model().eval(v,model_completion=True))) for name,v in inputs.items()} if status==z3.sat else {}
    return str(status),witness


def candidate_rows(case,out,config):
    source_path=ROOT/case["source"]
    optimized_path=ROOT/case["optimized"]
    source,optimized=parse_blif(source_path),parse_blif(optimized_path)
    if source.inputs != optimized.inputs:
        raise ValueError("study requires aligned input ordering")
    patterns=exact_patterns(source.inputs)
    sv,ov=evaluate_network(source,patterns),evaluate_network(optimized,patterns)
    if any(sv[y]!=ov[y] for y in source.outputs):
        raise AssertionError("baseline pair is not equivalent")
    src_encoding,opt_encoding=encode_blif(source_path),encode_blif(optimized_path)
    supports=structural_supports(source)
    opt_supports=structural_supports(optimized)
    levels=lambda net: level_map(net)
    sl,ol=levels(source),levels(optimized)
    rows=[]
    samples=[]
    for candidate in json.loads(case["candidates"]):
        start=time.perf_counter()
        direct,rewrite=measured_pair(source,optimized,case["target"],candidate,patterns)
        inverse,inverse_rewrite=measured_pair(source,optimized,case["target"],candidate,patterns,True)
        orientation=int(inverse["contextual_error"] < direct["contextual_error"])
        best=inverse if orientation else direct
        exact,global_witness=prove(opt_encoding.values[case["target"]],src_encoding.values[candidate],config["solver_timeout_ms"],opt_encoding.inputs)
        complement,_=prove(opt_encoding.values[case["target"]],z3.Not(src_encoding.values[candidate]),config["solver_timeout_ms"],opt_encoding.inputs)
        replacement_path=out/f"{case['case_id']}_{candidate}.blif"
        write_blif(rewrite,replacement_path)
        re=encode_blif(replacement_path)
        status,context_witness=prove(z3.Or(*[opt_encoding.values[y]!=re.values[y] for y in optimized.outputs]),z3.BoolVal(False),config["solver_timeout_ms"],opt_encoding.inputs)
        best_status=status
        if orientation:
            inverse_path=out/f"{case['case_id']}_{candidate}_inverse.blif"
            write_blif(inverse_rewrite,inverse_path)
            ie=encode_blif(inverse_path)
            best_status,_=prove(z3.Or(*[opt_encoding.values[y]!=ie.values[y] for y in optimized.outputs]),z3.BoolVal(False),config["solver_timeout_ms"],opt_encoding.inputs)
        overlap=len(supports[candidate]&opt_supports[case["target"]])/max(1,len(supports[candidate]|opt_supports[case["target"]]))
        gap=abs(sl[candidate]-ol[case["target"]])/max(1,sl[candidate],ol[case["target"]])
        depth_score=depth_similarity(sl[candidate],ol[case["target"]])
        score=0.6*overlap+0.4*depth_score
        row=dict(case_id=case["case_id"],family=case["family"],split=case["split"],evidence=case["evidence"],
                 target=case["target"],candidate=candidate,lineage=int(candidate==case["lineage"] and bool(case["lineage"])),
                 lineage_available=bool(case["lineage"]),**direct,inverse_contextual_error=inverse["contextual_error"],
                 best_contextual_error=best["contextual_error"],context_invert=orientation,global_status=exact,
                 complement_status=complement,contextual_status=status,best_contextual_status=best_status,best_conditional_observability=best["conditional_observability"],global_counterexample=json.dumps(global_witness,sort_keys=True),
                 contextual_counterexample=json.dumps(context_witness,sort_keys=True),
                 support_overlap=overlap,level_gap=gap,depth_score=depth_score,structural_score=score,smt_queries=3+orientation,runtime_seconds=time.perf_counter()-start)
        if case["evidence"]=="controlled_algebraic_rewrite":
            oracle=oracle_pair(source,optimized,case["target"],candidate)
            for key in ("distance","contextual_error","observability","output_hamming","mae","wce","worst_hamming"):
                if oracle[key]!=row[key]:
                    raise AssertionError((case["case_id"],candidate,key,oracle[key],row[key]))
        rows.append(row)
        for seed in config["sampling_seeds"]:
            sp=sampled_patterns(source.inputs,config["sample_count"],seed,case["case_id"])
            estimate,_=measured_pair(source,optimized,case["target"],candidate,sp)
            samples.append(dict(case_id=case["case_id"],candidate=candidate,seed=seed,estimate=estimate["distance"],
                                lower=estimate["distance_lower"],upper=estimate["distance_upper"],truth=direct["distance"],
                                sample_count=sp.pattern_count,covered=int(estimate["distance_lower"]<=direct["distance"]<=estimate["distance_upper"])))
    return rows,samples


def level_map(net):
    levels=dict.fromkeys(net.inputs,0)
    for node in net.nodes:
        levels[node.output]=1+max((levels[n] for n in node.inputs),default=-1)
    return levels


def evaluate_rankings(rows,config):
    queries=[]
    abstention=[]
    for case_id in sorted({r["case_id"] for r in rows}):
        group=[r for r in rows if r["case_id"]==case_id]
        for method in config["methods"]:
            ordered=rank_candidates(group,method)
            ranks=[i+1 for i,r in enumerate(ordered) if r["lineage"]]
            first=ranks[0] if ranks else None
            queries.append(dict(case_id=case_id,family=group[0]["family"],split=group[0]["split"],evidence=group[0]["evidence"],method=method,
                                lineage_available=group[0]["lineage_available"],candidates=len(group),
                                precision1=int(first==1),precision5=sum(r["lineage"] for r in ordered[:5])/min(5,len(group)),
                                reciprocal_rank=1/first if first else 0,coverage1=int(first==1),coverage5=int(first is not None and first<=5),
                                top1_candidate=ordered[0]["candidate"],top1_contextual_error=ordered[0]["best_contextual_error"],
                                verified_top5=sum(r["contextual_status"]=="unsat" for r in ordered[:5]),
                                exact_top5=sum(r["global_status"]=="unsat" for r in ordered[:5])))
            for threshold in config["abstention_thresholds"]:
                top=ordered[0]
                accepted=top["complement_distance"] <= threshold
                if method=="sat_only":
                    accepted=top["global_status"]=="unsat"
                abstention.append(dict(case_id=case_id,split=group[0]["split"],method=method,threshold=threshold,
                                       accepted=int(accepted),lineage_correct=int(accepted and top["lineage"]),
                                       direct_contextually_exact=int(accepted and top["contextual_status"]=="unsat")))
    summary=[]
    for split in sorted({r["split"] for r in queries}):
        for family in ["all"]+sorted({r["family"] for r in queries if r["split"]==split}):
            for method in config["methods"]:
                group=[r for r in queries if r["split"]==split and r["method"]==method and (family=="all" or r["family"]==family)]
                if not group:
                    continue
                summary.append(dict(split=split,family=family,method=method,queries=len(group),positives=sum(r["lineage_available"] for r in group),
                                    **{key:sum(r[key] for r in group)/len(group) for key in ("precision1","precision5","reciprocal_rank")},
                                    coverage5=sum(r["coverage5"] for r in group)/max(1,sum(r["lineage_available"] for r in group)),
                                    verified_top5=sum(r["verified_top5"] for r in group)))
    return queries,summary,abstention


def diagnostics(out,config,abc):
    cases=[]
    for spec in config["diagnostics"]:
        for flow in spec["flows"]:
            source=ROOT/spec["source"]
            path=out/f"{spec['benchmark']}_{flow}.blif"
            log=out/f"{spec['benchmark']}_{flow}.log"
            abc_call(abc,f"read_blif {source.relative_to(ROOT)}; {FLOWS[flow]}; write_blif {path.relative_to(ROOT)}",log)
            net=parse_blif(path)
            src=parse_blif(source)
            pool=[n.output for n in src.nodes if n.output not in src.outputs]
            if len(src.inputs)>12:
                continue
            for point in extract_longest_internal_path(net):
                if point.node in net.outputs:
                    continue
                cases.append(dict(case_id=f"diagnostic_{spec['benchmark']}_{flow}_{point.node}",family=spec["benchmark"],split="diagnostic",evidence="generated_netlist" if spec["benchmark"].startswith("generated") else "standard_netlist",
                                  source=str(source.relative_to(ROOT)),optimized=str(path.relative_to(ROOT)),target=point.node,lineage="",candidates=json.dumps(pool),
                                  source_sha256=sha(source),optimized_sha256=sha(path),lineage_basis="unavailable_no_historical_precision_claim"))
    return cases


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--config",default="configs/formal_approximate_correspondence.json")
    parser.add_argument("--skip-audit",action="store_true")
    parser.add_argument("--skip-reconstruction",action="store_true")
    args=parser.parse_args()
    config_path=ROOT/args.config
    config=json.loads(config_path.read_text())
    out=ROOT/"results/formal_approximate_correspondence"
    artifacts=out/"artifacts"
    artifacts.mkdir(parents=True,exist_ok=True)
    abc=(ROOT/".abc_build/abc_repo/abc").resolve()
    if not abc.exists():
        raise RuntimeError("pinned ABC is required for this experiment")
    started=time.perf_counter()
    cases=[]
    for split,width in [("development",config["development_width"]),("heldout",config["heldout_width"])]:
        for family in config["families"]:
            for replicate in config["replicates"]:
                cases.append(build_case(artifacts,family,width,replicate,split,config))
    cases.extend(diagnostics(artifacts,config,abc))
    write_csv(out/"cases.csv",cases)
    rows=[]
    sampled=[]
    for case in cases:
        r,s=candidate_rows(case,artifacts,config)
        rows.extend(r)
        sampled.extend(s)
    write_csv(out/"candidates.csv",rows)
    write_csv(out/"sampling.csv",sampled)
    controlled=[r for r in rows if r["evidence"]=="controlled_algebraic_rewrite"]
    queries,summary,abstention=evaluate_rankings(controlled,config)
    write_csv(out/"ranking_queries.csv",queries)
    write_csv(out/"ranking_summary.csv",summary)
    write_csv(out/"coverage_abstention.csv",abstention)
    diagnostic_rows=[]
    for case in cases:
        if case["split"]!="diagnostic":
            continue
        pool=[r for r in rows if r["case_id"]==case["case_id"]]
        exact=[r for r in pool if r["global_status"]=="unsat" or r["complement_status"]=="unsat"]
        best=min(pool,key=lambda r:r["complement_distance"])
        context=min(pool,key=lambda r:r["best_contextual_error"])
        diagnostic_rows.append(dict(case_id=case["case_id"],benchmark=case["family"],evidence=case["evidence"],
                                    exact_available=int(bool(exact)),min_complement_distance=best["complement_distance"],
                                    min_contextual_error=context["best_contextual_error"],candidate_count=len(pool),
                                    near_5pct=int(not exact and best["complement_distance"]<=0.05),
                                    odc_only=int(not exact and context["best_contextual_error"]==0)))
    write_csv(out/"critical_path_diagnostics.csv",diagnostic_rows)
    from scripts.analysis.run_approximation_guided_reconstruction import run as reconstruct
    reconstruction=list(csv.DictReader((out/"reconstruction.csv").open())) if args.skip_reconstruction else reconstruct(out,config,abc)
    if not args.skip_audit:
        audit(out/"audit",abc,config["historical_replay_per_stratum"])
    meta=dict(schema=SCHEMA,python=platform.python_version(),platform=platform.platform(),z3=z3.get_version_string(),
              abc_revision=subprocess.check_output(["git","-C",str(ROOT/".abc_build/abc_repo"),"rev-parse","HEAD"],text=True).strip(),
              git_base=subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip(),config_sha256=sha(config_path),
              seed=config["seed"],sample_count=config["sample_count"],sampling_seeds=config["sampling_seeds"],
              solver_timeout_ms=config["solver_timeout_ms"],abc_timeout_seconds=config["abc_timeout_seconds"],
              runtime_scope="candidate_analysis_reusing_other_components" if args.skip_reconstruction or args.skip_audit else "full_pipeline",reconstruction_reused=args.skip_reconstruction,audit_reused=args.skip_audit,
              distribution="uniform independent primary inputs",numeric_encoding="unsigned synthetic vector: y bit0, aux bit1; diagnostic values are declared BLIF-order encodings, not application arithmetic",runtime_seconds=time.perf_counter()-started)
    (out/"provenance.json").write_text(json.dumps(meta,indent=2)+"\n")
    from scripts.publication.seal_approximate_measurements import seal
    seal()
    print(json.dumps(dict(cases=len(cases),controlled_cases=sum(c["evidence"]=="controlled_algebraic_rewrite" for c in cases),candidate_rows=len(rows),sampling_rows=len(sampled),reconstruction_rows=len(reconstruction),runtime=meta["runtime_seconds"])))


if __name__=="__main__":
    main()
