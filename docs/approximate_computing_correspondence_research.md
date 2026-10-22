# Formal and observability-aware approximate correspondence

Completed research extension, 22 October 2026. The [academic report](publications/approximate_computing_aig_correspondence_research.pdf) and [16-slide presentation](presentation/) are built from the same checked CSVs.

The connection to approximate computing is quantitative error analysis of internal candidates under an exact whole-circuit correctness contract. A near match is a suggestion, not a recovered historical ancestor or permission to change circuit behavior.

## Completed work

- Repaired output-0 BLIF cover evaluation in the shared packed simulator and Z3 encoder, with malformed-cover rejection and polarity regressions.
- Added a reusable analysis module for direct/complement Boolean distance, valid contextual substitution, output Hamming error, declared-encoding MAE/WCE, target observability, conditional observability, and pointwise Hoeffding sampling intervals.
- Added an independent recursive scalar oracle, a frozen 48-case algebraic-rewrite study, and separate 26-target generated/standard-netlist path diagnostics.
- Compared the maintained fingerprint score, structural and exact baselines, global/complement/contextual methods, a fixed hybrid, feature ablations, and coverage versus abstention.
- Integrated optional eight-sample ordering into the existing source-blind expression-placement backend. Both orderings use identical hashed proposal pools, budgets, exact checks, activity gates, and source/cross-design CEC obligations.
- Fixed space-containing-path handling in the CEC wrappers used by this reconstruction and the older evidence/necessity workflows.

## Supported findings

The audit freezes eight examples in each exact/sampled × verified/rejected stratum. All 32 historical distances reproduce under the old evaluator. After the fix, all 16 selected verified examples have zero distance and pass fresh ABC CEC; the 16 rejected controls remain non-equivalent. Historical variant hashes are unavailable, so these are regenerated replays, not full archival certification. The old 2,609-row measurement pool remains unchanged and is not fully revalidated.

The controlled study has 24 development and 24 width-holdout queries, including four missing-ancestor queries in each split, and 472 candidate rows. Similarity often chooses an accidental closer function over the independently designated algebraic ancestor. The hybrid does not beat structural Precision@1 on this suite. Several feature ablations are null. Large global disagreement can be exactly masked; small disagreement can be fully observable.

The path diagnostic has 26 targets: 25 have an exact or complemented candidate, one has a context-only exact candidate, and none adds a nonzero near match within 5%. These rows have no historical-lineage labels and cannot support ancestry precision.

The reconstruction experiment deduplicates the old window rows to 18 target IDs (10 dc2 development; eight resyn2 holdout). At budget one, guided ordering accepts one target per split and enumeration accepts zero, at all three seeds. At full restricted-pool budget, the accepted set is the same. The two accepted flow instances share one distinct rewritten graph. This is a source-derived graph-active replacement in the optimized network, not a newly constructed source-side boundary. Exact-check counts fall; total measured runtime is effectively unchanged. The paired target-level holdout interval includes zero.

## Claim-to-evidence table

All paths below are repository-relative. New data live under `results/formal_approximate_correspondence/`.

| Claim | Artifact | Validation |
|---|---|---|
| Output-0 cover defect reproduced and corrected in selected historical rows | `audit/replay.csv`, `audit/*_cec.log`, `audit/historical_inputs.json` | Old-evaluator replay, independent scalar values, fresh ABC CEC |
| Controlled functions and lineage labels have separate roles | `cases.csv`, `artifacts/*.source.blif`, `artifacts/*.optimized.blif` | Source/optimized hashes; generator algebraic witness; independent oracle |
| Global/contextual/observability/error values agree | `candidates.csv` | Independent scalar enumeration, symbolic statuses, concrete counterexample replay |
| Fixed-pool ranking and null ablations | `ranking_queries.csv`, `ranking_summary.csv`, `coverage_abstention.csv` | Frozen configuration and per-query denominators |
| Sampling remains statistical evidence | `sampling.csv` | Seeds 7/19/41, 1,024 IID draws, pointwise Hoeffding intervals, exhaustive reference |
| Limited path coverage result | `critical_path_diagnostics.csv` | Exact bounded PI enumeration; no ancestry labels |
| Tight-budget ordering gain, no full-budget additional target | `reconstruction.csv`, `reconstruction_summary.csv`, `reconstruction/*.blif` | Identical pool hashes, exact target equality, graph activity, both CEC scopes |
| One distinct accepted graph, descriptive paired uncertainty | `paired_comparisons.csv`, artifact hashes in `reconstruction.csv` | Seeds averaged within unique target ID; 2,000 paired resamples |
| Low error cannot replace proof | `formal_gate_ablation.csv` | Count nonzero contextual errors passing the same 5% distance filter |
| Reproducible tools and publication | `provenance.json`, `publication_tools.json`, `publication_summary.json` | Config/source hashes and generated figures/tables |

Run `make check-approx-correspondence` for the independent checker, including fresh CEC where ABC is available. This checker independently replays measurements and accepted graphs. The ranking-query and publication consistency checks complement that oracle; an UNSAT status is not a solver-native proof trace.

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

The generated report is `output/pdf/approximate_computing_aig_correspondence_research.pdf`; a byte-identical publication copy is placed under `docs/publications/`. Editable narrative is in `paper/approximate_computing_correspondence.md.in`; the PDF builder inserts CSV-derived tables and saves the complete Markdown source alongside it. Figures use standard Matplotlib. Pandoc and pdfLaTeX are required for report builds.

The website uses relative routes, local assets, and `.nojekyll`, preserving the repository's GitHub Pages `main /docs` deployment. Open the local preview at `http://127.0.0.1:8765/`. The old deck is retained as `presentation/legacy.html` with a supersession notice.

## Limits and next experiment

This is a bounded combinational BLIF study with constructed lineage, not external RTL recovery. Width holdout shares the same generator families. Reconstruction uses a restricted unary/binary subset of the existing grammar and still constructs exhaustive proposal vectors. Its check-budget improvement does not establish scalable approximate search or a wall-clock benefit. Failed bounded search does not prove impossibility.

The most useful next experiment is independently instrumented synthesis lineage over a larger checkpoint corpus, disjoint design-family holdout, and matched wall-clock budgets against exact hashing or symbolic pruning. Source-cut selection for the two-copy sufficiency prover is a further integration point; it remains future work.

Background: [Vašíček, IEEE Access 2019](https://www.fit.vut.cz/research/result/c161468/.en), [ABC documentation](https://people.eecs.berkeley.edu/~alanmi/abc/abc.htm), and the report bibliography.
