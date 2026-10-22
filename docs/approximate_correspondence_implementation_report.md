# Implementation and validation report

22 October 2026. The requested research implementation, academic PDF, and presentation website are complete. The extension retains exact correctness for accepted graph changes and preserves the historical experiment tables.

## What changed

| Area | Maintained files / outputs | Result |
|---|---|---|
| BLIF correctness | `analyze_blif_matches.py`, `blif_z3.py`, `scripts/analysis/approximate_node_distance.py` | Correct homogeneous off-set covers; reject malformed/mixed covers; record corrected measurement schema and complement distance |
| Reusable quantitative analysis | `scripts/analysis/approximate_correspondence.py`, `contextual_error_metrics.py` | Exact/sample global and complement distance, valid polarity-aware substitution, observability identity, output Hamming, declared-encoding MAE/WCE, confidence intervals |
| Independent verification | `scripts/validation/approximate_oracle.py`, `check_formal_approximate_correspondence.py` | Independent scalar enumeration, named counterexample replay, independent pool-hash reconstruction, artifact hashes and exact graph replay |
| Frozen experiments | `configs/formal_approximate_correspondence.json`, `scripts/analysis/run_formal_approximate_correspondence.py`, `audit_approximate_distance.py` | 48 controlled cases, 26 separate path diagnostics, stratified historical audit and calibration |
| Optional exact-search integration | `source_blind_counterpart_placement.py`, `scripts/analysis/run_approximation_guided_reconstruction.py` | Same unary/binary proposal pool, sampled ordering, fixed budgets, unchanged equality/activity/CEC acceptance gates |
| Reproduction portability | `scripts/abc/cec.py`, older evidence/necessity CEC wrappers, locality checker | Space-safe staged CEC; old absolute paths relocate only with matching recorded content digests |
| Academic publication | `paper/approximate_computing_correspondence.md.in`, generated `.md`, `paper/approximate_references.bib`, `paper/figures/approximate_correspondence/` | Editable source, CSV-derived tables/figures and a rendered 15-page PDF |
| Website | `docs/index.html`, `docs/presentation/index.html`, `approximate.css`, `approximate.js`, `legacy.html`, `docs/.nojekyll` | Responsive research site, 16-slide deck, local assets, notes, overview, deep links, keyboard controls and historical deck preserved |
| Integration | `Makefile`, `.github/workflows/tests.yml`, README, ARTIFACTS, CLAIMS, research guide and supersession notices | Reproducible analysis/build/check targets and portable CI checks |

The complete result family is `results/formal_approximate_correspondence/`. Its measurement manifest seals the maintained implementation, configuration, measured CSVs, BLIF artifacts and audit logs. Old distance CSVs and earlier proof/recovery counts remain unchanged. Regenerated older figures and manifests created while checking the artifact were restored to their historical snapshots.

## Actual results

- The fixed audit reproduces all 32 selected old distance measurements. Corrected packed evaluation and an independent scalar evaluator agree. All 16 selected verified pairs have distance zero and pass fresh ABC CEC; the 16 rejected controls remain non-equivalent. Old variant hashes are unavailable, so this is a regenerated replay rather than full archival certification.
- The 48 controlled algebraic-rewrite cases yield 472 candidate rows. Held-out lineage Precision@1 is 10/24 for structural ranking, 6/24 for hybrid/contextual ranking, and 4/24 for global distance. Several feature ablations are null. Low distance is weak evidence of historical ancestry in this suite.
- The separate 26-target path diagnostic has 25 exact/complemented candidates, one context-only exact candidate and zero additional nonzero near matches within 5%. It has no historical-lineage labels.
- The complete analysis has 1,078 candidate rows and 3,234 Monte Carlo calibration rows. Sampling uses 1,024 IID uniform patterns at seeds 7/19/41, with pointwise Hoeffding intervals. Sampling is not an equivalence proof.
- Reconstruction compares 18 unique existing generated target IDs, three ordering seeds, five budgets and two orderings: 540 rows. At budget one, guided search accepts 1/10 development targets and 1/8 flow-holdout targets; enumeration accepts zero. At full budget, the accepted sets are identical. The two accepted flow instances share one graph artifact, implementing source-derived `xor(a0,b0)` at the optimized target.
- At full budget over both splits and three seeds, exact candidate checks decrease from 8,379 to 7,417. Measured total runtime is about 1.23 seconds for either ordering; no runtime advantage is claimed. The paired target-level interval for the tight-budget gain includes zero.

The strongest defensible contribution is the corrected, independently replayed quantitative correspondence layer and its separation of global similarity, exact contextual interchangeability, controlled lineage and graph-active reconstruction. The ordering experiment is a bounded demonstration; it is not additional full-budget recovery, a new source-side boundary result, industrial RTL recovery or a claim of algorithmic novelty.

## Validation performed

- Full repository suite: **825 passed, four skipped**, approximately 220 seconds.
- Final focused tests after digest-relocation hardening: **16 passed**. Earlier combined metric/locality tests: **51 passed**.
- `make artifact-check`: passed, including historical freshness, blind semantic, active counterpart, transplantation, locality, provenance, necessity-first, research synthesis, evidence advancement and claims checks.
- Full new independent checker: passed for **74 cases, 1,078 candidate rows and 540 reconstruction rows**. The 472 controlled candidate measurements were independently enumerated; counterexamples and accepted expressions were replayed. Fresh CEC was run for the one distinct accepted graph in both source and cross-design scopes.
- Manifest integrity and independent proposal-pool reconstruction: passed. Unsupported/unknown/timeout results are never promoted to accepted graph changes.
- PDF: successfully compiled with Pandoc/pdfLaTeX, rendered with Poppler and visually inspected. All 15 pages contain text; automated glyph bounds found no out-of-page text. The publication copy is byte-identical to the research PDF.
- Website: an actual HTTP crawl under `/aig_optimization_experiments/` fetched **123 routes/assets** (four HTML routes and 119 assets) successfully, including the historical deck and PDF.
- Browser: navigated all 16 local slides; verified direct hashes, boundary buttons, notes, overview, keyboard navigation after mouse focus, all three new charts and no horizontal overflow at the inspected 662-pixel viewport. A reviewed screenshot is saved under `output/screenshots/`.

The initial full-suite failures exposed path handling in older CEC wrappers. Those failures were repaired and the suite rerun successfully. The artifact check initially exposed historical absolute paths; digest-checked relocation repaired that portability issue without rewriting the certificates or weakening proof conditions.

## Reproduction

```bash
python -m pip install -r requirements.txt
make build-abc
make approx-correspondence
make check-approx-correspondence
make approx-correspondence-pdf
make website
make website-check
make serve-website
```

The report output is `output/pdf/approximate_computing_aig_correspondence_research.pdf`. Its editable narrative template and complete generated Markdown are under `paper/`. The new analysis defaults to the pinned local ABC build. Report compilation requires Pandoc and pdfLaTeX. The PDF build does not rerun or overwrite older research evidence.

## Remaining research limits

The full historical 2,609-row distance pool and its affected fingerprint/path derivatives still need a separately versioned regeneration. The new audit is limited to 32 frozen examples. Controlled lineage comes from algebraic construction; width holdout shares families, and flow holdout shares generated designs. Ranking comparisons do not equalize feature-acquisition costs. Reconstruction still constructs bounded exhaustive proposal vectors, uses only a restricted part of the existing grammar, and has one distinct accepted graph. SAT/UNSAT statuses are not solver-native proof traces. Joint substitution, application workloads, scalable counting and physical timing are outside the completed scope.

The most valuable next experiment is an independently instrumented synthesis-checkpoint lineage corpus with disjoint design-family holdout and matched wall-clock budgets against exact hashing or symbolic pruning. Source-cut selection for the existing two-copy sufficiency prover is another proposed integration point.

## Response for Professor Carmine Rizzi

Yes, I investigated and implemented the approximate-computing connection. The analysis measures both internal Boolean disagreement and the output-observable error of a valid substitution, with independent exhaustive and symbolic validation. It shows that ODCs can make globally different nodes exactly interchangeable, while rare differences can still be fully observable. Sampled similarity also helps order the existing exact reconstruction search under small candidate-check budgets, while all accepted graph artifacts retain both ABC CEC checks. At full budget the accepted set is unchanged and total runtime does not improve in this study. The report includes those negative findings, the weak lineage-ranking results and a corrected audit of an earlier BLIF evaluation defect.

## Deployment and CI

The updated public [website](https://stefi19.github.io/aig_optimization_experiments/)
and [presentation](https://stefi19.github.io/aig_optimization_experiments/presentation/)
were verified after GitHub Pages reported the material publication commit built.
The same 123-route/asset traversal passed publicly, the deployed PDF matched the
local artifact byte for byte, and the public presentation's three figures loaded
without horizontal overflow. The existing `main /docs` hosting configuration was
retained.

The first remote portable CI run passed its analyses but failed the final
clean-worktree gate because the new website checker wrote a tracked QA report.
The checker now stays read-only by default; saving a report requires an explicit
`--report` path. The clean-worktree gate remains intact.

The original untracked `output/slides/` directory was left unchanged. No messages
were sent to Professor Rizzi; the response above is provided for the user to send.
