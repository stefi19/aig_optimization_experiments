# Demo Wow Report

This is a reviewer-safe mini-report derived only from committed evidence tables.

| mode       | stage                                     | subject                                              | status                          | evidence_level            |
| ---------- | ----------------------------------------- | ---------------------------------------------------- | ------------------------------- | ------------------------- |
| controlled | select graph-active source counterpart    | distributed_affine_divisor                           | proven_counterpart_equivalent   | formal_exhaustive         |
| controlled | decompose source window                   | distributed_affine_divisor                           | decomposable                    | formal_exhaustive         |
| controlled | synthesize quotient                       | distributed_affine_divisor                           | synthesized_truth_table         | truth_table_synthesis     |
| controlled | prove global source and cross equivalence | distributed_affine_divisor                           | equivalent/equivalent           | abc_cec                   |
| blind      | cegis iteration 1                         | arithmetic_add_add_w2__identity__ground_truth_region | counterexample_added            | counterexample_refinement |
| blind      | cegis iteration 2                         | arithmetic_add_add_w2__identity__ground_truth_region | counterexample_added            | counterexample_refinement |
| blind      | cegis iteration 3                         | arithmetic_add_add_w2__identity__ground_truth_region | no_candidate_satisfies_examples | bounded_exhaustion        |
| blind      | verified positive blind control           | arithmetic_affine_w2__balance__whole_output_cone     | formally_verified_region        | formal_exhaustive         |

Run `make demo-wow` to regenerate this report and print the same trace.
