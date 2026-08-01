# Case Study: Proof-Carrying Counterparts and Blind CEGIS

The controlled half of the case study demonstrates a graph-active source-side counterpart accepted only after local proof, quotient synthesis, and ABC CEC checks. The blind half shows counterexample-guided refinement adding concrete distinguishing assignments before the bounded candidate family is exhausted, plus a separate blind positive control with a formal proof.

| mode       | stage                                     | subject                                              | status                          | evidence_level            | artifact                                                                |
| ---------- | ----------------------------------------- | ---------------------------------------------------- | ------------------------------- | ------------------------- | ----------------------------------------------------------------------- |
| controlled | select graph-active source counterpart    | distributed_affine_divisor                           | proven_counterpart_equivalent   | formal_exhaustive         | results/active_source_counterpart_refactoring/counterpart_proofs.csv    |
| controlled | decompose source window                   | distributed_affine_divisor                           | decomposable                    | formal_exhaustive         | results/active_source_counterpart_refactoring/decomposition_queries.csv |
| controlled | synthesize quotient                       | distributed_affine_divisor                           | synthesized_truth_table         | truth_table_synthesis     | results/active_source_counterpart_refactoring/quotient_synthesis.csv    |
| controlled | prove global source and cross equivalence | distributed_affine_divisor                           | equivalent/equivalent           | abc_cec                   | results/active_source_counterpart_refactoring/global_cec.csv            |
| blind      | cegis iteration 1                         | arithmetic_add_add_w2__identity__ground_truth_region | counterexample_added            | counterexample_refinement | results/blind_semantic_cegis/cegis_iterations.csv                       |
| blind      | cegis iteration 2                         | arithmetic_add_add_w2__identity__ground_truth_region | counterexample_added            | counterexample_refinement | results/blind_semantic_cegis/cegis_iterations.csv                       |
| blind      | cegis iteration 3                         | arithmetic_add_add_w2__identity__ground_truth_region | no_candidate_satisfies_examples | bounded_exhaustion        | results/blind_semantic_cegis/cegis_iterations.csv                       |
| blind      | verified positive blind control           | arithmetic_affine_w2__balance__whole_output_cone     | formally_verified_region        | formal_exhaustive         | results/blind_semantic_cegis/formal_proofs.csv                          |

Interpretation: controlled source access can support graph-active recovery, while blind bounded template search must report both verified regions and replayable negative traces.
