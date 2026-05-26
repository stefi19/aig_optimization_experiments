# Top-K Recovery Evaluation

## Data availability

- `top_candidates.csv`: ✅ loaded
- `sat_verified_candidates.csv`: ✅ loaded

## Recovery at K=1 (rank-1 candidate only)

| benchmark | optimization | verified_at_k | total_nodes | recovery_at_k | mrr | avg_score_at_1 |
| --- | --- | --- | --- | --- | --- | --- |
| majority3 | balance | 0 | 4 | 0.0% | 0.0000 | 0.9656 |
| majority3 | refactor | 0 | 3 | 0.0% | 0.0000 | 0.8299 |
| majority3 | resub | 1 | 4 | 25.0% | 0.2500 | 1.0000 |
| majority3 | resyn2_like | 1 | 3 | 33.3% | 0.3333 | 0.8625 |
| majority3 | rewrite | 1 | 4 | 25.0% | 0.2500 | 1.0000 |
| mux2 | balance | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| mux2 | refactor | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| mux2 | resub | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| mux2 | resyn2_like | 0 | 2 | 0.0% | 0.0000 | 0.7250 |
| mux2 | rewrite | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| toy_and_or | balance | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| toy_and_or | refactor | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| toy_and_or | resub | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| toy_and_or | resyn2_like | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| toy_and_or | rewrite | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| xor_chain | balance | 8 | 8 | 100.0% | 1.0000 | 1.0000 |
| xor_chain | refactor | 8 | 8 | 100.0% | 1.0000 | 1.0000 |
| xor_chain | resub | 8 | 8 | 100.0% | 1.0000 | 1.0000 |
| xor_chain | resyn2_like | 0 | 8 | 0.0% | 0.0000 | 0.7097 |
| xor_chain | rewrite | 8 | 8 | 100.0% | 1.0000 | 1.0000 |

## Full results (all K values)

| benchmark | optimization | k | verified_at_k | total_nodes | recovery_at_k | mrr | avg_score_at_1 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| majority3 | balance | 1 | 0 | 4 | 0.0% | 0.0000 | 0.9656 |
| majority3 | balance | 2 | 0 | 4 | 0.0% | 0.0000 | 0.9656 |
| majority3 | balance | 3 | 0 | 4 | 0.0% | 0.0000 | 0.9656 |
| majority3 | balance | 5 | 0 | 4 | 0.0% | 0.0000 | 0.9656 |
| majority3 | refactor | 1 | 0 | 3 | 0.0% | 0.0000 | 0.8299 |
| majority3 | refactor | 2 | 0 | 3 | 0.0% | 0.0000 | 0.8299 |
| majority3 | refactor | 3 | 0 | 3 | 0.0% | 0.0000 | 0.8299 |
| majority3 | refactor | 5 | 0 | 3 | 0.0% | 0.0000 | 0.8299 |
| majority3 | resub | 1 | 1 | 4 | 25.0% | 0.2500 | 1.0000 |
| majority3 | resub | 2 | 1 | 4 | 25.0% | 0.2500 | 1.0000 |
| majority3 | resub | 3 | 1 | 4 | 25.0% | 0.2500 | 1.0000 |
| majority3 | resub | 5 | 1 | 4 | 25.0% | 0.2500 | 1.0000 |
| majority3 | resyn2_like | 1 | 1 | 3 | 33.3% | 0.3333 | 0.8625 |
| majority3 | resyn2_like | 2 | 1 | 3 | 33.3% | 0.3333 | 0.8625 |
| majority3 | resyn2_like | 3 | 1 | 3 | 33.3% | 0.3333 | 0.8625 |
| majority3 | resyn2_like | 5 | 1 | 3 | 33.3% | 0.3333 | 0.8625 |
| majority3 | rewrite | 1 | 1 | 4 | 25.0% | 0.2500 | 1.0000 |
| majority3 | rewrite | 2 | 1 | 4 | 25.0% | 0.2500 | 1.0000 |
| majority3 | rewrite | 3 | 1 | 4 | 25.0% | 0.2500 | 1.0000 |
| majority3 | rewrite | 5 | 1 | 4 | 25.0% | 0.2500 | 1.0000 |
| mux2 | balance | 1 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| mux2 | balance | 2 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| mux2 | balance | 3 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| mux2 | balance | 5 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| mux2 | refactor | 1 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| mux2 | refactor | 2 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| mux2 | refactor | 3 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| mux2 | refactor | 5 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| mux2 | resub | 1 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| mux2 | resub | 2 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| mux2 | resub | 3 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| mux2 | resub | 5 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| mux2 | resyn2_like | 1 | 0 | 2 | 0.0% | 0.0000 | 0.7250 |
| mux2 | resyn2_like | 2 | 0 | 2 | 0.0% | 0.0000 | 0.7250 |
| mux2 | resyn2_like | 3 | 0 | 2 | 0.0% | 0.0000 | 0.7250 |
| mux2 | resyn2_like | 5 | 0 | 2 | 0.0% | 0.0000 | 0.7250 |
| mux2 | rewrite | 1 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| mux2 | rewrite | 2 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| mux2 | rewrite | 3 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| mux2 | rewrite | 5 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| toy_and_or | balance | 1 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| toy_and_or | balance | 2 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| toy_and_or | balance | 3 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| toy_and_or | balance | 5 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| toy_and_or | refactor | 1 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| toy_and_or | refactor | 2 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| toy_and_or | refactor | 3 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| toy_and_or | refactor | 5 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| toy_and_or | resub | 1 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| toy_and_or | resub | 2 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| toy_and_or | resub | 3 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| toy_and_or | resub | 5 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| toy_and_or | resyn2_like | 1 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| toy_and_or | resyn2_like | 2 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| toy_and_or | resyn2_like | 3 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| toy_and_or | resyn2_like | 5 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| toy_and_or | rewrite | 1 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| toy_and_or | rewrite | 2 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| toy_and_or | rewrite | 3 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| toy_and_or | rewrite | 5 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| xor_chain | balance | 1 | 8 | 8 | 100.0% | 1.0000 | 1.0000 |
| xor_chain | balance | 2 | 8 | 8 | 100.0% | 1.0000 | 1.0000 |
| xor_chain | balance | 3 | 8 | 8 | 100.0% | 1.0000 | 1.0000 |
| xor_chain | balance | 5 | 8 | 8 | 100.0% | 1.0000 | 1.0000 |
| xor_chain | refactor | 1 | 8 | 8 | 100.0% | 1.0000 | 1.0000 |
| xor_chain | refactor | 2 | 8 | 8 | 100.0% | 1.0000 | 1.0000 |
| xor_chain | refactor | 3 | 8 | 8 | 100.0% | 1.0000 | 1.0000 |
| xor_chain | refactor | 5 | 8 | 8 | 100.0% | 1.0000 | 1.0000 |
| xor_chain | resub | 1 | 8 | 8 | 100.0% | 1.0000 | 1.0000 |
| xor_chain | resub | 2 | 8 | 8 | 100.0% | 1.0000 | 1.0000 |
| xor_chain | resub | 3 | 8 | 8 | 100.0% | 1.0000 | 1.0000 |
| xor_chain | resub | 5 | 8 | 8 | 100.0% | 1.0000 | 1.0000 |
| xor_chain | resyn2_like | 1 | 0 | 8 | 0.0% | 0.0000 | 0.7097 |
| xor_chain | resyn2_like | 2 | 0 | 8 | 0.0% | 0.0000 | 0.7097 |
| xor_chain | resyn2_like | 3 | 0 | 8 | 0.0% | 0.0000 | 0.7097 |
| xor_chain | resyn2_like | 5 | 0 | 8 | 0.0% | 0.0000 | 0.7097 |
| xor_chain | rewrite | 1 | 8 | 8 | 100.0% | 1.0000 | 1.0000 |
| xor_chain | rewrite | 2 | 8 | 8 | 100.0% | 1.0000 | 1.0000 |
| xor_chain | rewrite | 3 | 8 | 8 | 100.0% | 1.0000 | 1.0000 |
| xor_chain | rewrite | 5 | 8 | 8 | 100.0% | 1.0000 | 1.0000 |

## Global summary

- **K=1**: 53/78 nodes recovered (67.9%)
- **K=2**: 53/78 nodes recovered (67.9%)
- **K=3**: 53/78 nodes recovered (67.9%)
- **K=5**: 53/78 nodes recovered (67.9%)

## Interpretation

**verified_at_k** is the number of optimized nodes for which the ABC-verified match appears within the top-K simulation-ranked candidates.

**recovery_at_k** = verified_at_k / total_nodes. A value of 1.0 at K=1 means the rank-1 candidate was always the formally correct match — the simulation ranking was perfect.

**MRR** (Mean Reciprocal Rank) measures how high the first verified candidate appears on average. MRR=1.0 means every verified match was rank-1; MRR=0.5 means verified matches appeared at rank 2 on average.

**avg_score_at_1** is the mean combined_score of the top-ranked candidate per node. It is available even without SAT results and gives a proxy for how confidently the simulation step selected candidates.
