import json
import shutil
import subprocess
from pathlib import Path

import pandas as pd

from scripts.analysis.audit_approximate_distance import ROOT

OUT=ROOT/"results/formal_approximate_correspondence"


def table(frame):
    return frame.to_markdown(index=False,floatfmt=".3f")


def build_results():
    summary=json.loads((OUT/"publication_summary.json").read_text())
    ranks=pd.read_csv(OUT/"ranking_summary.csv")
    candidates=pd.read_csv(OUT/"candidates.csv")
    reconstruction=pd.read_csv(OUT/"reconstruction.csv")
    audit=pd.read_csv(OUT/"audit/replay.csv")
    formal=pd.read_csv(OUT/"formal_gate_ablation.csv")
    paired=pd.read_csv(OUT/"paired_comparisons.csv")
    meta=json.loads((OUT/"provenance.json").read_text())
    sections=["## Audit and exact measurement integrity", "",
              f"The replay covers {summary['audited_rows']} historical pairs. All {summary['audit_legacy_reproductions']} old values reproduce, and all {summary['audit_verified_corrected_zero']} selected verified rows correct to zero and pass fresh CEC. The selected rejected controls remain disproved. The exact global/complement/contextual SMT queries have {summary['unknown_proofs']} unknown results in the controlled suite.","",
              table(audit.groupby(["historical_status","mode"]).agg(Rows=("corrected_distance","count"),Old_mean=("historical_distance","mean"),Corrected_mean=("corrected_distance","mean")).reset_index().rename(columns={"historical_status":"Old label","mode":"Mode"})), "",
              "These sampled audit rows reuse their historical 4,096-pattern streams; the separate calibration experiment uses 1,024 patterns.","",
              "## Known-lineage ranking", ""]
    methods=["structural","fingerprint","sat_only","global","complement","contextual","hybrid"]
    for split in ("development","heldout"):
        frame=ranks[(ranks.family=="all")&(ranks.split==split)&ranks.method.isin(methods)].set_index("method").loc[methods].reset_index()
        sections += [f"**{split.capitalize()}: 24 queries, 20 positive lineage queries.**", "",
                     table(frame[["method","precision1","precision5","reciprocal_rank","coverage5"]].rename(columns=dict(method="Method",precision1="P@1",precision5="P@5",reciprocal_rank="MRR",coverage5="Top-5 coverage"))), ""]
    sections += ["![Held-out lineage ranking. All methods use the same source-candidate pools.](figures/approximate_correspondence/lineage_ranking.png){width=90%}","",
                 "The hybrid falls below the structural baseline in held-out Precision@1; added functional features do not improve lineage accuracy on this suite. Complement handling improves some rankings relative to direct distance, but contextual and observability features do not independently improve this suite's headline ranking. Single-feature ablations remain in the full per-family CSVs.","",
                 "## Context, observability, and formal-gate ablation", "",
                 "![Global versus contextual error for all controlled candidates. Multiple points overlap.](figures/approximate_correspondence/global_contextual.png){width=80%}","",
                 table(formal.rename(columns=dict(split="Split",near_rows="Near rows",unsafe_near_rows="Unsafe",contextually_exact_near_rows="Exact context",near_rows_without_global_match="No global match"))),"",
                 "Near means complement distance at most 5%; unsafe means nonzero best-polarity contextual output error. Removing the formal gate admits these unsafe near rows even though their distance passes the filter. This is candidate-level accounting, not a count of accepted graph rewrites.", "",
                 "## Path diagnostics and sampling calibration", "",
                 f"The separate path diagnostic contains {summary['diagnostics']} targets: {summary['diagnostic_unmatched']} lacks any exact or complemented source node in its full internal pool. None adds a nonzero near match within 5%, while {summary['diagnostic_odc_only']} has a zero-context-error candidate despite lacking a globally equal/complemented candidate. This gives a small contextual observation and a null result for global near-match path coverage. These targets have no lineage labels.","",
                 f"Across {summary['sampled_intervals']:,} pointwise intervals, empirical coverage is {100*summary['pointwise_coverage']:.2f}%. Shared cases and streams make these intervals dependent; this percentage is a calibration diagnostic, not a coverage theorem or evidence of exact equality. Error estimates and all seeds are available in the sampling table.","",
                 "## Matched-budget exact reconstruction", ""]
    budget_rows=[]
    for split in ("development","heldout"):
        for budget in sorted(reconstruction.budget.unique()):
            row=dict(Split=split,Budget=int(budget))
            for ordering,label in [("enumeration","Enumeration"),("sampled_distance","Guided")]:
                group=reconstruction[(reconstruction.split==split)&(reconstruction.budget==budget)&(reconstruction.ordering==ordering)]
                counts=group.groupby("seed").accepted.sum()
                row[label]=f"{counts.min()}--{counts.max()} / {group.target_id.nunique()}"
            budget_rows.append(row)
    sections += [table(pd.DataFrame(budget_rows)),"",
                 "Counts are the minimum--maximum accepted target counts across the three seeds, with unique target IDs as denominator. At budget one, guided ordering accepts one target in each flow split and enumeration accepts zero. At budgets 64 and 176, both methods accept the same one target per split. Across flows these two target instances share one identical graph artifact (SHA-256 begins `8601cd0c46bd`).", "",
                 "![Exact-check budget versus accepted target instances; shaded ranges show minimum and maximum over three ordering seeds.](figures/approximate_correspondence/reconstruction_budget.png){width=98%}","",
                 table(reconstruction[reconstruction.budget==176].groupby("ordering").agg(Exact_checks=("exact_checks","sum"),CEC_calls=("formal_cec_calls","sum"),Total_seconds=("runtime_seconds","sum")).reset_index().rename(columns={"ordering":"Ordering"})), "",
                 "These totals include both flow splits and all three seeds. Exact-check counts fall, while total time remains effectively unchanged at this scale; no runtime advantage is claimed. Every emitted accepted artifact passed both ABC CEC scopes, and the independent checker replays each distinct graph. Most targets remain unresolved under the eight-signal unary/binary pool, or hit a graph-activity gate.","",
                 "## Paired uncertainty", ""]
    effect=paired[((paired.experiment=="lineage_precision1")&(paired.split=="heldout"))|((paired.experiment=="graph_active_acceptance")&(paired.split=="heldout")&(paired.budget==1))]
    sections += [table(effect[["experiment","method_a","method_b","difference","lower","upper"]].replace({"lineage_precision1":"Lineage P@1","graph_active_acceptance":"Graph acceptance","sampled_distance":"guided"}).rename(columns=dict(experiment="Outcome",method_a="A",method_b="B",difference="A-B",lower="95% low",upper="95% high"))),"",
                 "Bootstrap intervals use 2,000 deterministic paired resamples. Reconstruction first averages ordering seeds within target, so seed repetition does not inflate the independent-unit count. With only eight held-out target IDs, the tight-budget interval includes zero. The finite-suite effect should not be interpreted as a statistically established population improvement.","",
                 "## Toolchain", "",
                 f"The recorded run uses Python {meta['python']}, Z3 {meta['z3']}, ABC revision `{meta['abc_revision'][:12]}`, uniform PI inputs, and the frozen configuration hash recorded in `provenance.json`. Timeouts are 5 seconds per SMT query and 30 seconds per ABC call. Full version and artifact digests remain machine readable."]
    return "\n".join(sections)+"\n"


def main():
    for tool in ("pandoc","pdflatex"):
        if not shutil.which(tool):
            raise RuntimeError(f"missing publication dependency: {tool}")
    results=build_results()
    (ROOT/"paper/tables/approximate_correspondence_results.md").write_text(results)
    source=ROOT/"paper/approximate_computing_correspondence.md"
    template=(ROOT/"paper/approximate_computing_correspondence.md.in").read_text()
    source.write_text(template.replace("@@RESULTS@@",results))
    output=ROOT/"output/pdf/approximate_computing_aig_correspondence_research.pdf"
    output.parent.mkdir(parents=True,exist_ok=True)
    command=["pandoc",str(source),"--pdf-engine=pdflatex","--citeproc","--number-sections","--resource-path="+str(ROOT/"paper"),
             "--bibliography="+str(ROOT/"paper/references.bib"),"--bibliography="+str(ROOT/"paper/approximate_references.bib"),"-o",str(output)]
    proc=subprocess.run(command,cwd=ROOT,capture_output=True,text=True)
    (OUT/"pdf_build.log").write_text(proc.stdout+proc.stderr)
    if proc.returncode:
        raise RuntimeError(proc.stderr)
    versions={name:subprocess.check_output([name,"--version"],text=True).splitlines()[0] for name in ("pandoc","pdflatex")}
    (OUT/"publication_tools.json").write_text(json.dumps(versions,indent=2)+"\n")
    print(output)


if __name__=="__main__":
    main()
