# Formal approximate correspondence — speaker notes

## 1. From approximate computing to exact correspondence

The answer to the approximate-computing connection is yes: the repository now measures internal disagreement and its output consequences. The evidence is bounded. This talk separates completed results, preliminary search observations, and proposed experiments. It does not claim an industrial lineage predictor or end-to-end speedup.

## 2. Same outputs, different internal functions

This opening diagram illustrates the problem algebraically; it is not a measured synthesis checkpoint. Source s=a AND b and optimized t=a both give output ab. Matching internal names or functions alone need not recover the original decomposition. The concrete committed examples later use controlled algebraic labels.

## 3. The approximate-computing connection

Vašíček (IEEE Access 2019) provides background on formal error analysis of approximate circuits; see the full bibliography in the PDF. Here we transfer error analysis to internal correspondence and search scheduling. Uniform independent PIs define the probability space. Ordinary approximate computing often accepts a specified output error for cost savings; this project accepts no nonzero functional error in its emitted rewrites. No novelty is claimed for Boolean distance, observability, SAT, or heuristic ordering.

## 4. Three questions need three kinds of evidence

The controlled study has designated algebraic ancestors. That label is independent of the ranking metric but is not a recorded industrial synthesis history. Functional equality may be a perfectly good replacement and still fail the ancestry label. Contextual exactness is specific to a single replacement and the current consumer graph.

## 5. The motivating expectations

These expectations organize the interpretation without inventing preregistration. The experiments test different units and outcomes: candidate ranking, contextual single substitutions, and restricted graph reconstruction. A positive observation on one question cannot be used as evidence for another.

## 6. Counts, estimates, and proofs remain distinct

The 3,234 calibration intervals cover the exact values 98.98% of the time in this suite. They are dependent across shared cases and streams. The interval is pointwise, not a simultaneous guarantee for adaptive candidate selection. Exact counts enumerate PI assignments, not solver auxiliaries. Z3 UNSAT is a solver result, not an independently checked proof trace; exhaustive scalar checks and ABC provide separate validation here.

## 7. First, repair the instrument

ABC can emit homogeneous off-set covers: the listed cubes produce zero and uncovered assignments produce one. Both old evaluation paths treated those covers incorrectly. The correction supports declared on-set/off-set semantics and rejects unsupported or mixed forms. A frozen stratified replay selects eight rows from each exact/sampled × verified/rejected stratum. Regenerated pairs lack old artifact hashes; the full historical 2,609-row pool has not been revalidated. Old fingerprint and distance conclusions are not fresh evidence. The independent scalar oracle checks the new controlled measurements.

## 8. Three experiments, three denominators

There are 472 controlled candidate rows. Each ranking split includes four queries with no designated ancestor, leaving 20 positive queries. The holdouts are width and flow holdouts, not disjoint circuit-family generalization. The 540 reconstruction rows repeat 18 target IDs over budgets, seeds, and orderings. Never sum these denominators or call seeds independent circuits.

## 9. The unexpected result: structure ranks better

Precision@1 includes all 24 queries; the four missing-ancestor queries receive zero. The hybrid does not beat the structural baseline on this constructed suite. Complement handling improves some rankings relative to direct distance, but contextual and observability ablations do not independently improve headline P@1. Shared exhaustive feature extraction does not equalize feature acquisition costs. This result contradicts a simple similarity-led ancestry expectation; it does not prove similarity can never help on another corpus.

## 10. Closer can mean the wrong ancestor

Both formulas are checked against the actual source BLIF on all 256 inputs, and counts are independently recomputed. In this case structural ranking selects the designated ancestor; global ranking selects s007. The complemented s003 also supplies a close best-polarity distractor in contextual/hybrid ranking. The controlled generator deliberately injects distractors: their frequency is not representative of synthesis. The example establishes non-identifiability from distance alone, not a population error rate.

## 11. Large internal differences can disappear at the output

These are formulas recovered from the committed heldout_reconvergent_mask_0 pair, not an invented measurement. All 256 full-PI assignments and both primary outputs are checked. The auxiliary output does not depend on t and remains unchanged. This demonstrates single-node contextual substitutability. Whole-circuit graph emission would still need graph activity and both CEC scopes; this candidate-level case study is not counted as a new accepted graph.

## 12. The truth table explains the masking

D marks candidate disagreement; o_t marks whether toggling t can alter any output. Here D=b while o_t=NOT b, so they are perfectly anti-correlated. Multiplying mean distance and mean observability would give the wrong answer. An exact but non-ancestor source candidate s000=a also exists in this case and ranks ahead of s001 under global distance. Contextual safety and ancestry remain separate.

## 13. Small global error can be fully observable

Use heldout_rare_observable_0, the same actual pair as the ranking counterexample. Source and optimized original outputs are equal. Cloning the source ancestor into t changes its role: the optimized XOR with r cancels the rare term. Thus contextual error equals direct distance for both candidates. The auxiliary output is unchanged. r is a six-input conjunction with probability 1/64, not an independent fair bit; compact reasoning must preserve that weight.

## 14. One witness defeats an exact replacement

The named all-one witness comes from the committed contextual_counterexample field and is replayed by the independent scalar evaluator. For the ancestor s002, the stored witness sets x0=x1=0 and x2 through x7=1, also producing an output difference. In a weighted table, r=0 represents 63 assignments of its six inputs per fixed a,b; r=1 represents one. Sampling can miss these events; no probability threshold authorizes an exact rewrite.

## 15. The full candidate cloud has the same distinction

Multiple points overlap, so visual density is not a frequency estimate. All output mismatches are evaluated after cloning the source cone into the optimized target context. The plot uses direct polarity; other tables also report best polarity and explicit inversion. Held-out formal-gate ablation finds 12 unsafe rows among 44 near rows at complement distance at most 5%, reinforcing the need for exact checks.

## 16. Use similarity to choose what to prove next

Stable ties retain enumeration order. Pool hashes verify that guidance changes order, not candidate availability. Budgets are 1,4,16,64,176; three seeds are repeated ordering trials. The implementation already constructs exhaustive proposal vectors, so sampling is not an asymptotically scalable replacement for this backend. Exact check counts are distinct from total feature and pool construction cost.

## 17. A small-budget gain; the same full-budget set

The two flow instances share a single rewritten graph, SHA-256 beginning 8601cd0c46bd. Do not interpret the two instances as independent recoveries or the three seeds as independent circuits. The target-level paired held-out tight-budget effect is 0.125 with descriptive bootstrap interval [0,0.375]. It includes zero. At full budget the difference is zero. This is a scheduling observation on selected generated targets.

## 18. The acceptance contract stays exact

Graph validation checks activity and a real changed driver, preventing a vacuous success. Both global ABC CEC scopes are required. The backend emits a source-derived optimized-network anchor; it does not recover a new source-side boundary or transplant an optimized cone as a hidden oracle. The independent checker replays the expression, checks graph differences and output equality, and reruns both CEC scopes for the distinct graph.

## 19. Fewer vector checks did not mean faster recovery

Totals include both flow splits and all three seeds at budget 176. These are short aggregate measurements, not a robust speed benchmark. Exact vector equality is cheap and vectors already exist; an exact-hash lookup is a particularly important missing baseline. Approximate ordering may save counted comparisons while adding sampling and ordering overhead. Stronger baselines and matched total cost are necessary before claiming practical benefit.

## 20. The path diagnostic is mostly a null result

These targets have no historical node-lineage labels. The longest internal path is a structural proxy, not a static timing analysis result. The one zero-context case without a global equal/complemented candidate illustrates contextual analysis, not a broad recovery rate. Future critical-path claims need timing metadata and independently verified path relevance.

## 21. What survived the experiments?

These statements refer to distinct outcomes and do not recast the negative ranking result as an improvement. The controlled construction shows that closeness cannot logically identify ancestry on its own. It does not estimate the best achievable predictor on instrumented real synthesis histories. Contextual and hybrid ranking coincide in the headline result, and individual feature ablations are mostly null.

## 22. The contribution is a checked reasoning layer

The project contribution is the integration and evidence discipline in this correspondence workflow, including an instrument correction and independent replay. The graph-active source-derived reconstruction observation is bounded to the declared language. MAE and WCE require explicit output encoding and are not application-level error models. Prior exact-recovery pipelines retain their own denominators and proof scopes.

## 23. Keep three levels of certainty visible

Established means verified for these committed cases, not universally true for every circuit. Uncertainties include controlled labels, intentionally adversarial distractors, repeated generator families, selected targets, exhaustive feature extraction, incomplete historical provenance, and solver proof logs without proof certificates. No full industrial-scale, sequential, joint-substitution, or workload-distribution study was completed.

## 24. A defensible paper claim

State the negative ranking result nearby: structural ranking recovered 10/24 designated ancestors at rank one, versus 6/24 for hybrid/contextual and 4/24 for global distance. Avoid claiming ancestry discovery from error metrics, new general boundary recovery, industrial speedup, or improved physical critical paths. The PDF includes the same interpretation and a proposed protocol.

## 25. Where Do We Go From Here?

This is the next publishable question, not a completed experiment or promised positive result. The current negative ranking result makes genuine lineage labels especially important. The next study must distinguish recovering historical ancestry from finding a formally interchangeable function; both can be useful, but they require separate scoring.

## 26. Build ground truth independently of the metric

A checkpoint name or truth-vector equality is not automatically a lineage label. Record operator-level provenance and the relation being labeled, including ambiguous and missing descendants. Keep the provenance collector separate from the ranking system. Preserve original sources, intermediate graphs, configs, tool revisions, and digests. Freeze candidate pools, eligibility rules, and splits; prevent near-duplicate designs across families. These choices must precede evaluation.

## 27. Compare strong alternatives at the same cost

Run all methods on paired targets and identical hardware. Count preprocessing and amortization explicitly; an already available exact hash may make sampling redundant. Use unchanged exact acceptance gates. Use a fixed configuration or development-only tuning with equal tuning budgets. Randomize run order and repeat timing measurements. Compare time-to-first-accepted with timeouts censored rather than silently discarded.

## 28. Measure usefulness, not just rank

Report distributions and paired target effects, not only pooled averages. Stratify by family, size, transformation, and representation availability. Deduplicate identical accepted graphs across flows. Path relevance should state whether the recovered interface lies on a measured timing-critical path or merely a structural longest path. Log failures for every method so a lower success count cannot be hidden by exclusions.

## 29. What would support or falsify the hypothesis?

A better ancestry rank without useful reconstruction is insufficient to establish the search hypothesis. Conversely, an exact alternative recovery may be useful without matching historical lineage and must be scored separately. One null result would falsify the declared practical claim in that protocol, not prove no approximate heuristic could ever help. Keep the exact safety contract fixed in both outcomes.

## 30. Second direction: choose a source cut to prove

The existing two-copy sufficiency prover asks whether two PI assignments can agree on all cut signals while disagreeing on the target. UNSAT establishes target determination by the cut under the modeled domain. Proposed similarity guidance would order cuts, not relax this query. Compare with structural cut selection and the current sufficiency pipeline at matched time and proof calls. Evaluate independently verified new interfaces, not only existing exact target functions. Sufficiency alone does not establish graph activity or both whole-design CEC scopes.

## 31. The Connection

Self-contained reply to Carmine’s question. Approximate computing motivates quantifying disagreement instead of retaining only SAT pass/fail. Here the metrics explain relationships and prioritize candidates. The project does not accept an approximate final circuit and does not claim novelty for the underlying error metrics or equivalence machinery.

## 32. What We Implemented and Found

The 48 controlled cases are 24 development plus 24 held-out width cases, with four absent ancestors per split. They are designated algebraic labels, not recorded industrial lineage. Reconstruction uses 18 selected generated target IDs and repeated seeds; the two successful flow instances share one graph. The audit replays 32 historical rows, not all 2,609. These limitations are integral to the result.

## 33. Why This Is Worth Pursuing

The precise next contribution would be evidence that a quantitative heuristic buys useful exact reconstruction under realistic computational constraints. It may fail against exact hashing, especially where complete truth vectors already exist. A second proposed direction ranks source cuts for the two-copy sufficiency prover. Neither future experiment has been implemented in this extension.

## 34. Reproduce, inspect, and discuss

Background references: Vašíček 2019, Formal Methods for Exact Analysis of Approximate Circuits; Mishchenko et al. 2011 on don’t-care resynthesis; Mishchenko et al. 2006 on DAG-aware rewriting; Brayton and Mishchenko 2010 on ABC; de Moura and Bjørner 2008 on Z3; Hoeffding 1963. Full bibliographic entries and DOI links are in the PDF. Research sources are linked at the bottom of each relevant slide. Notes are available with N; overview shows the full narrative.
