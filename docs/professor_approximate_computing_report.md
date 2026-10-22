# Findings for Professor Carmine Rizzi

The approximate-computing connection has been implemented as quantitative analysis of internal correspondence, with exact circuit correctness retained as a hard constraint.

The extension measures Boolean disagreement and the output error caused by replacing a target with a source-derived candidate in its actual consumer context. An independent exhaustive oracle and symbolic checks validate the bounded cases. It shows both important extremes: globally different functions can be exactly interchangeable under observability don't-cares, while a rare difference can be fully observable and unsuitable for an exact replacement.

Before extending the research, we found and corrected a shared BLIF evaluator/encoder defect: output-0 covers were ignored. A frozen 32-row replay reproduces the historical measurements; all 16 selected verified examples correct to zero distance and pass fresh ABC CEC. The complete historical measurement pool has not been revalidated.

The controlled 48-case study finds that low functional distance is weak evidence of historical ancestry. The separate 26-target path diagnostic adds one context-only exact relationship, but no additional nonzero near match within 5%. These results do not establish general RTL back-mapping performance.

Approximate ordering was also integrated into the existing source-blind exact expression-placement search. Under identical proposal pools and tight exact-check budgets it reaches accepted graph-active rewrites earlier. At full restricted-pool budget the accepted set is unchanged, and the two accepted flow instances share one distinct graph artifact. Both global ABC CEC scopes remain mandatory. Total runtime does not improve at this scale.

The strongest result is a validated separation between functional similarity, contextual interchangeability, lineage evidence, and proof-carrying graph reconstruction, with a small matched-budget ordering demonstration. The next decisive experiment is a larger independently instrumented synthesis-lineage corpus with disjoint design families and matched wall-clock budgets against stronger exact-search baselines.

The full report is [available as a PDF](publications/approximate_computing_aig_correspondence_research.pdf), with [the research presentation](presentation/) and [claim-to-evidence guide](approximate_computing_correspondence_research.md).

## Short response to send

Yes, I investigated and implemented the approximate-computing connection. The new analysis measures both internal Boolean distance and the output-observable error of a valid substitution, with independent exhaustive and symbolic validation. It demonstrates that ODCs can make globally different nodes exactly interchangeable, while rare differences can still be fully observable. I also used sampled similarity to order the existing exact reconstruction search: it reaches accepted CEC-backed graph artifacts under smaller candidate-check budgets, but does not add recoveries at full budget or improve total runtime in this study. The report includes the negative lineage-ranking findings and a corrected audit of an earlier BLIF measurement bug. The next step is a larger synthesis-lineage corpus with stronger exact-search baselines.
