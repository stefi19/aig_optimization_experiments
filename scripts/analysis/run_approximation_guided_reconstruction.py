import csv
import json
import time
from pathlib import Path

from scripts.analysis.audit_approximate_distance import ROOT, sha, write_csv
from source_blind_counterpart_placement import attempt_source_blind_window_expression_placement


def run(out,config,abc):
    historical=list(csv.DictReader((ROOT/"results/evidence_advancement/source_blind_window_expression_placement.csv").open()))
    targets=sorted({r["target_id"] for r in historical if "|" in r["target_id"]})
    results=[]
    directory=out/"reconstruction"
    directory.mkdir(parents=True,exist_ok=True)
    for index,target_id in enumerate(targets):
        benchmark,region,flow,target=target_id.split("|")
        source=ROOT/f"variants/{benchmark}_original.blif"
        optimized=ROOT/f"variants/{benchmark}_{flow}.blif"
        split="development" if flow==config["reconstruction"]["development_flow"] else "heldout"
        for seed in config["sampling_seeds"]:
            for budget in config["reconstruction"]["budgets"]:
                for ordering in ("enumeration","sampled_distance"):
                    path=directory/f"{index}_{seed}_{budget}_{ordering}.blif"
                    options=dict(ordering=ordering,budget=budget,seed=seed,sample_count=config["reconstruction"]["sample_count"])
                    started=time.perf_counter()
                    result=attempt_source_blind_window_expression_placement(target_id=target_id,semantic_counterpart_status="not_used_for_search",
                        source_path=source,optimized_path=optimized,optimized_target_node=target,output_path=path,root=ROOT,abc_path=abc,
                        max_support_inputs=config["reconstruction"]["max_support_inputs"],max_candidate_signals=config["reconstruction"]["max_candidate_signals"],search_options=options)
                    row=result.row()
                    features=json.loads(row["selection_features"])
                    results.append(dict(target_id=target_id,benchmark=benchmark,optimization=flow,split=split,evidence="existing_generated_source_blind_targets_unique_target_ids",
                                        ordering=ordering,budget=budget,seed=seed,candidate_pool_hash=features.get("candidate_pool_hash",""),candidate_pool_size=features.get("candidate_pool_size",0),
                                        exact_checks=features.get("exact_checks",0),formal_cec_calls=2 if result.rewrite_emitted else 0,
                                        ranking_seconds=features.get("ranking_seconds",0),proposal_generation_seconds=features.get("proposal_generation_seconds",0),
                                        time_to_first_exact_seconds=features.get("time_to_first_exact_seconds",""),runtime_seconds=time.perf_counter()-started,
                                        accepted=int(result.promotion=="graph_active_recovery"),expression=result.expression,
                                        graph_active=result.graph_active,source_cec=result.source_vs_rewrite_cec,cross_cec=result.rewrite_vs_optimized_cec,
                                        blocker=result.blocker,artifact=row["rewrite_artifact"] if result.rewrite_emitted else "",artifact_sha256=sha(path) if result.rewrite_emitted else "",
                                        source=str(source.relative_to(ROOT)),optimized=str(optimized.relative_to(ROOT)),target=target,
                                        source_sha256=sha(source),optimized_sha256=sha(optimized)))
    write_csv(out/"reconstruction.csv",results)
    return results
