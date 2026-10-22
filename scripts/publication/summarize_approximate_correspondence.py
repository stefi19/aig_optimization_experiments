import json
import random
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from scripts.analysis.audit_approximate_distance import ROOT, write_csv

OUT=ROOT/"results/formal_approximate_correspondence"
FIG=ROOT/"paper/figures/approximate_correspondence"


def bootstrap(values,seed=20261022):
    rng=random.Random(seed)
    means=sorted(sum(rng.choices(values,k=len(values)))/len(values) for _ in range(2000))
    return sum(values)/len(values),means[49],means[1949]


def main():
    FIG.mkdir(parents=True,exist_ok=True)
    summary=pd.read_csv(OUT/"ranking_summary.csv")
    queries=pd.read_csv(OUT/"ranking_queries.csv")
    candidates=pd.read_csv(OUT/"candidates.csv")
    reconstruction=pd.read_csv(OUT/"reconstruction.csv")
    audit=pd.read_csv(OUT/"audit/replay.csv")
    paths=pd.read_csv(OUT/"critical_path_diagnostics.csv")
    sampling=pd.read_csv(OUT/"sampling.csv")
    c=candidates[candidates.evidence=="controlled_algebraic_rewrite"]
    paired=[]
    for split in ["development","heldout"]:
        pivot=queries[queries.split==split].pivot(index="case_id",columns="method",values="precision1")
        for a,b in [("hybrid","structural"),("hybrid","global"),("complement","global")]:
            effect,lo,hi=bootstrap((pivot[a]-pivot[b]).tolist())
            paired.append(dict(experiment="lineage_precision1",split=split,method_a=a,method_b=b,budget="",unit="controlled_case",units=len(pivot),difference=effect,lower=lo,upper=hi))
    reco_summary=[]
    for (split,budget,seed,ordering),group in reconstruction.groupby(["split","budget","seed","ordering"]):
        accepted=group[group.accepted==1]
        reco_summary.append(dict(split=split,budget=int(budget),seed=int(seed),ordering=ordering,targets=len(group),accepted=int(group.accepted.sum()),
                                 exact_checks=int(group.exact_checks.sum()),cec_calls=int(group.formal_cec_calls.sum()),runtime_seconds=float(group.runtime_seconds.sum()),
                                 median_accepted_seconds=float(accepted.runtime_seconds.median()) if len(accepted) else ""))
    for (split,budget),group in reconstruction.groupby(["split","budget"]):
        by_target=group.groupby(["target_id","ordering"]).accepted.mean().unstack("ordering")
        effect,lo,hi=bootstrap((by_target.sampled_distance-by_target.enumeration).tolist())
        paired.append(dict(experiment="graph_active_acceptance",split=split,method_a="sampled_distance",method_b="enumeration",budget=int(budget),unit="unique_target_averaged_over_seeds",units=len(by_target),difference=effect,lower=lo,upper=hi))
    write_csv(OUT/"paired_comparisons.csv",paired)
    write_csv(OUT/"reconstruction_summary.csv",reco_summary)
    plt.rcParams.update({"font.size":10,"axes.spines.top":False,"axes.spines.right":False,"savefig.dpi":180})
    labels=["structural","fingerprint","sat_only","global","complement","contextual","hybrid"]
    fig,ax=plt.subplots(figsize=(8,3.8))
    sub=summary[(summary.family=="all") & (summary.split=="heldout")].set_index("method").loc[labels]
    ax.bar(range(len(labels)),sub.precision1,color=["#8a98a8"]*3+["#c08755"]*2+["#277a77"]*2)
    ax.set_xticks(range(len(labels)),[x.replace("_"," ") for x in labels],rotation=25,ha="right")
    ax.set_ylabel("Lineage Precision@1 (24 held-out cases)")
    ax.set_ylim(0,1)
    ax.set_title("Functional proximity does not identify synthesis lineage")
    fig.tight_layout();fig.savefig(FIG/"lineage_ranking.png");plt.close(fig)
    fig,ax=plt.subplots(figsize=(6.5,4))
    for family,group in c.groupby("family"):
        ax.scatter(group.distance,group.contextual_error,s=16,alpha=.55,label=family.replace("_"," "))
    ax.plot([0,1],[0,1],ls="--",color="#aaa",lw=1)
    ax.set(xlabel="Global Boolean distance",ylabel="Contextual output error",xlim=(-.02,1.02),ylim=(-.02,1.02))
    ax.legend(fontsize=7,loc="upper left");fig.tight_layout();fig.savefig(FIG/"global_contextual.png");plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(9,3.5))
    for ax,split in zip(axes,["development","heldout"]):
        for ordering,color in [("enumeration","#8a98a8"),("sampled_distance","#277a77")]:
            group=reconstruction[(reconstruction.split==split)&(reconstruction.ordering==ordering)]
            scores=group.groupby(["budget","seed"]).accepted.sum().unstack("seed")
            ax.plot(scores.index,scores.mean(axis=1),marker="o",label=ordering.replace("_"," "),color=color)
            ax.fill_between(scores.index,scores.min(axis=1),scores.max(axis=1),color=color,alpha=.15)
        ax.set(xlabel="Exact candidate checks allowed",ylabel="Accepted graph-active targets",title=split,xscale="log")
        ax.set_ylim(bottom=0)
        ax.legend(fontsize=8)
    fig.tight_layout();fig.savefig(FIG/"reconstruction_budget.png");plt.close(fig)
    lineage=c[c.lineage==1]
    formal=[]
    for split,group in c.groupby("split"):
        low=group[group.complement_distance<=.05]
        unsafe=low[low.best_contextual_error>0]
        formal.append(dict(split=split,near_rows=len(low),unsafe_near_rows=len(unsafe),contextually_exact_near_rows=int((low.best_contextual_status=="unsat").sum()),
                           near_rows_without_global_match=int(((low.global_status!="unsat")&(low.complement_status!="unsat")).sum())))
    write_csv(OUT/"formal_gate_ablation.csv",formal)
    checked=dict(schema="approximate_publication_v1",controlled_cases=int(c.case_id.nunique()),controlled_candidates=len(c),
                 diagnostics=int(paths.case_id.nunique()),diagnostic_unmatched=int((paths.exact_available==0).sum()),
                 diagnostic_near_5pct=int(paths.near_5pct.sum()),diagnostic_odc_only=int(paths.odc_only.sum()),
                 audited_rows=len(audit),audit_historical_verified=int((audit.historical_status=="verified").sum()),
                 audit_verified_corrected_zero=int(((audit.historical_status=="verified")&(audit.corrected_distance==0)).sum()),
                 audit_legacy_reproductions=int(((audit.historical_distance-audit.legacy_replay_distance).abs()<1e-12).sum()),
                 audit_fresh_cec_matches=int(((audit.historical_status=="verified")&(audit.fresh_cec=="equivalent")).sum()),
                 unknown_proofs=int((c[["global_status","complement_status","contextual_status"]]=="unknown").sum().sum()),
                 sampled_intervals=len(sampling),pointwise_coverage=float(sampling.covered.mean()),
                 reconstruction_unique_targets=int(reconstruction.target_id.nunique()),reconstruction_rows=len(reconstruction),
                 reconstruction_development_targets=int(reconstruction[reconstruction.split=="development"].target_id.nunique()),
                 reconstruction_heldout_targets=int(reconstruction[reconstruction.split=="heldout"].target_id.nunique()))
    (OUT/"publication_summary.json").write_text(json.dumps(checked,indent=2)+"\n")
    print(json.dumps(checked))


if __name__=="__main__":
    main()
