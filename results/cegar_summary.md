# CEGAR-Style Candidate Refinement — Prototype

> **Prototype notice**: This script implements a lightweight approximation of counterexample-guided refinement.  It does *not* call ABC or any SAT solver; it uses previously recorded ABC rejections as penalty signals.  A real CEGAR loop would iteratively re-verify the new rank-1 candidate after each refinement step.  See the module docstring for known limitations.

## Data availability

- `top_candidates.csv`: ✅ loaded
- `sat_verified_candidates.csv`: ✅ loaded
- Rejected pairs used as penalty sources: **1**

## Configuration

- `REJECTION_WEIGHT` = **0.2** — fraction of original score a candidate identical to a rejected one loses
- Feature space: `['simulation_similarity', 'support_overlap', 'depth_similarity']`
- Penalty formula: `penalty = 0.2 × max_over_rejections(feature_sim)`
- Refined score: `max(0, combined_score − penalty)`
- Similarity metric: `1 − L1_distance / 3`

## Per-(benchmark, optimization) summary

| benchmark | optimization | total_nodes | nodes_with_penalty | nodes_rank1_changed | n_rejected_pairs | avg_original_rank1 | avg_refined_rank1 | avg_penalty_rank1 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| majority3 | balance | 4 | 1 | 0 | 1 | 0.9656 | 0.9156 | 0.0500 |
| majority3 | refactor | 3 | 0 | 0 | 0 | 0.8299 | 0.8299 | 0.0000 |
| majority3 | resub | 4 | 0 | 0 | 0 | 1.0000 | 1.0000 | 0.0000 |
| majority3 | resyn2_like | 3 | 0 | 0 | 0 | 0.8625 | 0.8625 | 0.0000 |
| majority3 | rewrite | 4 | 0 | 0 | 0 | 1.0000 | 1.0000 | 0.0000 |
| mux2 | balance | 2 | 0 | 0 | 0 | 1.0000 | 1.0000 | 0.0000 |
| mux2 | refactor | 2 | 0 | 0 | 0 | 1.0000 | 1.0000 | 0.0000 |
| mux2 | resub | 2 | 0 | 0 | 0 | 1.0000 | 1.0000 | 0.0000 |
| mux2 | resyn2_like | 2 | 0 | 0 | 0 | 0.7250 | 0.7250 | 0.0000 |
| mux2 | rewrite | 2 | 0 | 0 | 0 | 1.0000 | 1.0000 | 0.0000 |
| toy_and_or | balance | 2 | 0 | 0 | 0 | 1.0000 | 1.0000 | 0.0000 |
| toy_and_or | refactor | 2 | 0 | 0 | 0 | 1.0000 | 1.0000 | 0.0000 |
| toy_and_or | resub | 2 | 0 | 0 | 0 | 1.0000 | 1.0000 | 0.0000 |
| toy_and_or | resyn2_like | 2 | 0 | 0 | 0 | 1.0000 | 1.0000 | 0.0000 |
| toy_and_or | rewrite | 2 | 0 | 0 | 0 | 1.0000 | 1.0000 | 0.0000 |
| xor_chain | balance | 8 | 0 | 0 | 0 | 1.0000 | 1.0000 | 0.0000 |
| xor_chain | refactor | 8 | 0 | 0 | 0 | 1.0000 | 1.0000 | 0.0000 |
| xor_chain | resub | 8 | 0 | 0 | 0 | 1.0000 | 1.0000 | 0.0000 |
| xor_chain | resyn2_like | 8 | 0 | 0 | 0 | 0.7097 | 0.7097 | 0.0000 |
| xor_chain | rewrite | 8 | 0 | 0 | 0 | 1.0000 | 1.0000 | 0.0000 |

## Global rollup

| total_nodes | nodes_with_penalty | pct_penalized | nodes_rank1_changed | pct_rank1_changed | n_rejected_pairs | avg_original_rank1 | avg_refined_rank1 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 78 | 1 | 1.3% | 0 | 0.0% | 1 | 0.9546 | 0.9521 |

## Rank changes

- **0** candidate rows moved to a higher rank (rank_change > 0)
- **0** candidate rows moved to a lower rank (rank_change < 0)
- **312** rows unchanged

## Interpretation

**What the penalty signal captures**: when ABC proves two nodes are *not* equivalent, the feature vector of that rejected pair identifies a region of score space where the simulation / support / depth signals are collectively misleading.  Other candidates for the same optimised node that fall in the same region are penalised, under the hypothesis that the misleading pattern is local to that region.

**When penalties are zero**: if no ABC rejections are available (e.g. the SAT stage has not been run, or all checked candidates were verified), the refined ranking is identical to the original ranking.  This is the correct behaviour — without evidence of spurious regions, no adjustment is warranted.

**`nodes_rank1_changed`**: the most actionable metric.  A value > 0 means CEGAR refinement re-ordered the top candidate for at least one node.  In a full iterative loop these new rank-1 candidates would be submitted to ABC next; the loop terminates when no new rejections appear.

**Known limitations of this prototype**:
1. Penalties are not iterated — a single refinement pass is performed.
2. Only rank-1 ABC results are currently available as rejection sources.
3. The feature similarity is a coarse L1 proxy; a learned distance metric would be more precise.
4. `refined_score` is clipped at 0 and may not preserve the relative ordering of heavily penalised candidates well.
