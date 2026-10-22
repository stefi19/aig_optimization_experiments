import html
import json
import re
import shutil
from pathlib import Path

import pandas as pd

from scripts.analysis.audit_approximate_distance import ROOT
from scripts.publication.approximate_examples import verified_examples
from scripts.publication.approximate_narrative import build_slides


def main():
    out=ROOT/"results/formal_approximate_correspondence"
    summary=json.loads((out/"publication_summary.json").read_text())
    ranks=pd.read_csv(out/"ranking_summary.csv")
    held=ranks[(ranks.family=="all")&(ranks.split=="heldout")].set_index("method")
    pub=ROOT/"docs/publications"
    pub.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(ROOT/"output/pdf/approximate_computing_aig_correspondence_research.pdf",pub/"approximate_computing_aig_correspondence_research.pdf")
    assets=ROOT/"docs/presentation/assets/approximate"
    assets.mkdir(parents=True,exist_ok=True)
    for path in (ROOT/"paper/figures/approximate_correspondence").glob("*.png"):
        shutil.copyfile(path,assets/path.name)
    (ROOT/"docs/.nojekyll").touch()
    (ROOT/"docs/research-evidence.json").write_text(json.dumps(summary,indent=2)+"\n")
    svg='''<svg viewBox="0 0 650 260" role="img" aria-label="Source and optimized logic share the output ab while internal functions differ"><g fill="none" stroke="#166d68" stroke-width="2"><rect x="22" y="70" width="220" height="100" rx="4"/><rect x="392" y="70" width="220" height="100" rx="4"/><path d="M265 120H365m-15-10 15 10-15 10"/></g><g fill="#172c38" font-family="Georgia,serif" text-anchor="middle"><text x="132" y="40" font-size="20">Source</text><text x="502" y="40" font-size="20">Optimized</text><text x="132" y="113" font-size="28">s = a ∧ b</text><text x="502" y="113" font-size="28">t = a</text><text x="132" y="147" font-size="21">y = s</text><text x="502" y="147" font-size="21">y = t ∧ b</text><text x="325" y="220" font-size="22">Same outputs · Different internal functions</text></g></svg>'''
    examples = verified_examples()
    (assets/"verified_examples.json").write_text(json.dumps(examples, indent=2)+"\n")
    slides = build_slides(summary, held, svg, examples)
    speaker_notes = ["# Formal approximate correspondence — speaker notes", ""]
    for index, item in enumerate(slides, 1):
        title = html.unescape(re.search(r'data-title="([^"]+)"', item).group(1))
        note = html.unescape(re.search(r'<aside class="notes">(.*?)</aside>', item).group(1))
        speaker_notes.extend([f"## {index}. {title}", "", note, ""])
    (ROOT/"docs/presentation/speaker_notes.md").write_text("\n".join(speaker_notes))
    document='''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Formal Approximate Correspondence</title><meta name="description" content="A validated research presentation on approximate computing, observability, and exact AIG correspondence reconstruction."><link rel="stylesheet" href="approximate.css"></head><body><header class="topbar"><a class="brand" href="../">AIG / CORRESPONDENCE</a><span>FORMAL APPROXIMATE RECOVERY · 2026</span><a href="../publications/approximate_computing_aig_correspondence_research.pdf">Read the report ↗</a></header><main class="deck">'''+''.join(slides)+'''</main><footer class="controls"><div class="progress" aria-hidden="true"><div class="progress-bar"></div></div><button id="prev" type="button" aria-label="Previous slide">Prev</button><span id="slide-number" aria-live="polite"></span><button id="next" type="button" aria-label="Next slide">Next</button><button id="notes-toggle" type="button" aria-expanded="false" aria-controls="notes-panel">Notes</button><button id="overview-toggle" type="button" aria-pressed="false">Overview</button><span class="shortcut">← → navigate · N notes · Home / End</span></footer><aside class="notes-panel" id="notes-panel" aria-label="Speaker notes"></aside><script src="approximate.js"></script></body></html>'''
    (ROOT/"docs/presentation/index.html").write_text(document)
    home=f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>AIG Correspondence Research</title><meta name="description" content="Formal approximate correspondence research: validated error metrics, observability, and proof-guided exact reconstruction."><link rel="stylesheet" href="presentation/approximate.css"></head><body class="home"><header class="topbar"><a class="brand" href="./">AIG / CORRESPONDENCE</a><span>RESEARCH ARTIFACT · 22 OCTOBER 2026</span><a href="https://github.com/stefi19/aig_optimization_experiments">Repository ↗</a></header><main class="container"><section class="hero"><p class="eyebrow">Approximate reasoning. Exact correctness.</p><h1>Understanding logic after optimization.</h1><p class="lead">Synthesis preserves what a circuit computes while changing the functions inside it. We measure those differences, ask which are observable, and use the evidence to guide exact correspondence reconstruction.</p><div class="actions"><a class="button primary" href="presentation/">Open the presentation →</a><a class="button" href="publications/approximate_computing_aig_correspondence_research.pdf">Read the research PDF ↗</a></div></section><section class="home-section"><div class="stats"><div class="stat"><strong>{summary['controlled_cases']}</strong><span>controlled rewrite cases</span></div><div class="stat"><strong>{summary['diagnostics']}</strong><span>structural-path diagnostic targets</span></div><div class="stat"><strong>{summary['reconstruction_unique_targets']}</strong><span>unique reconstruction target IDs</span></div></div><p class="caption">Separate experimental denominators. Controlled algebraic lineage, generated netlist reconstruction, and standard-netlist diagnostics are not interchangeable evidence.</p></section><section class="home-section research-grid"><div><p class="eyebrow">The connection to approximate computing</p><h2>Internal disagreement is only part of the story.</h2><p>Two internal functions can differ on half of all input assignments yet be exactly interchangeable in their consumer context. A rare difference can also be observable every time it occurs.</p><p>Functional similarity supports explanation and candidate ordering. Every accepted reconstruction still needs exact local validation, an active graph artifact, and global equivalence checks.</p></div><div>{svg}</div></section><section class="home-section"><p class="eyebrow">Completed experiment</p><h2>A bounded search-ordering result.</h2><div class="research-grid"><figure><img src="presentation/assets/approximate/reconstruction_budget.png" alt="Accepted graph-active reconstruction targets under matched candidate-check budgets"><figcaption>Frozen candidate pools and budgets; three disclosed sampling seeds.</figcaption></figure><div><p>Sampled ordering reaches accepted artifacts at smaller exact-check budgets. At full budget, the accepted target set is unchanged. Two accepted flow instances share one distinct graph.</p><p>Global similarity performs poorly as historical-lineage evidence in the controlled suite. No broad external RTL gain or runtime speedup is claimed.</p></div></div></section><section class="home-section"><p class="eyebrow">Measurement integrity</p><h2>Corrected before extending the claims.</h2><p>The shared simulator and symbolic encoder ignored output-0 BLIF covers. A frozen 32-row replay reproduces the old values; all 16 selected verified examples become zero-distance and pass fresh ABC CEC after the fix. The historical distance files remain available with a supersession notice. The complete historical pool has not been revalidated.</p></section><section class="home-section" id="publications"><p class="eyebrow">Publications and reproducibility</p><h2>Inspect the evidence.</h2><div class="document-list"><a href="publications/approximate_computing_aig_correspondence_research.pdf">From Approximate Computing to Formal Approximate Correspondence Recovery <span class="tag">Research report · PDF</span></a><a href="presentation/">Formal approximate correspondence <span class="tag">{len(slides)} HTML slides</span></a><a href="approximate_computing_correspondence_research.md">Method, limitations, and claim-to-evidence table <span class="tag">Research note</span></a><a href="professor_approximate_computing_report.md">Concise supervisor-facing findings <span class="tag">Short report</span></a><a href="https://github.com/stefi19/aig_optimization_experiments/tree/main/results/formal_approximate_correspondence">Frozen results, independent checker, and BLIF artifacts <span class="tag">GitHub</span></a><a href="presentation/legacy.html">Previous research presentation <span class="tag">Historical snapshot</span></a></div></section></main><footer class="home-footer container">AIG Optimization Correspondence Experiments · Exact evidence remains distinct from approximate similarity.</footer></body></html>'''
    (ROOT/"docs/index.html").write_text(home)
    print(f"Built website and {len(slides)} slides from checked result tables")


if __name__=="__main__":
    main()
