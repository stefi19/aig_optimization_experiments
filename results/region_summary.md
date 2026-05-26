# Region Correspondence Baseline

## Data availability

- BLIF variant files: ✅ loaded

## Configuration

Cone depths evaluated: **[1, 2, 3]**  
Top-K candidates kept per (node, depth): **5**  
Region score weights: sim=0.5, support=0.4, size=0.1

## Depth 1 — per-(benchmark, optimization) summary

| benchmark | optimization | total_opt_nodes | avg_rank1_region_score | avg_rank1_cone_sim | avg_rank1_cone_support | avg_rank1_cone_size_sim | pct_rank1_above_0_8 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| majority3 | balance | 4 | 0.9688 | 0.9375 | 1.0000 | 1.0000 | 100.0% |
| majority3 | refactor | 3 | 0.8347 | 0.7917 | 0.8889 | 0.8333 | 33.3% |
| majority3 | resub | 4 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 100.0% |
| majority3 | resyn2_like | 3 | 0.8583 | 0.7500 | 1.0000 | 0.8333 | 66.7% |
| majority3 | rewrite | 4 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 100.0% |
| mux2 | balance | 2 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 100.0% |
| mux2 | refactor | 2 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 100.0% |
| mux2 | resub | 2 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 100.0% |
| mux2 | resyn2_like | 2 | 0.7500 | 0.5000 | 1.0000 | 1.0000 | 0.0% |
| mux2 | rewrite | 2 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 100.0% |
| toy_and_or | balance | 2 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 100.0% |
| toy_and_or | refactor | 2 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 100.0% |
| toy_and_or | resub | 2 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 100.0% |
| toy_and_or | resyn2_like | 2 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 100.0% |
| toy_and_or | rewrite | 2 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 100.0% |
| xor_chain | balance | 8 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 100.0% |
| xor_chain | refactor | 8 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 100.0% |
| xor_chain | resub | 8 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 100.0% |
| xor_chain | resyn2_like | 8 | 0.6410 | 0.7188 | 0.5792 | 0.5000 | 37.5% |
| xor_chain | rewrite | 8 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 100.0% |

## Depth 2 — per-(benchmark, optimization) summary

| benchmark | optimization | total_opt_nodes | avg_rank1_region_score | avg_rank1_cone_sim | avg_rank1_cone_support | avg_rank1_cone_size_sim | pct_rank1_above_0_8 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| majority3 | balance | 4 | 0.9688 | 0.9375 | 1.0000 | 1.0000 | 100.0% |
| majority3 | refactor | 3 | 0.8347 | 0.7917 | 0.8889 | 0.8333 | 33.3% |
| majority3 | resub | 4 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 100.0% |
| majority3 | resyn2_like | 3 | 0.8583 | 0.7500 | 1.0000 | 0.8333 | 66.7% |
| majority3 | rewrite | 4 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 100.0% |
| mux2 | balance | 2 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 100.0% |
| mux2 | refactor | 2 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 100.0% |
| mux2 | resub | 2 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 100.0% |
| mux2 | resyn2_like | 2 | 0.7500 | 0.5000 | 1.0000 | 1.0000 | 0.0% |
| mux2 | rewrite | 2 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 100.0% |
| toy_and_or | balance | 2 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 100.0% |
| toy_and_or | refactor | 2 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 100.0% |
| toy_and_or | resub | 2 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 100.0% |
| toy_and_or | resyn2_like | 2 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 100.0% |
| toy_and_or | rewrite | 2 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 100.0% |
| xor_chain | balance | 8 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 100.0% |
| xor_chain | refactor | 8 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 100.0% |
| xor_chain | resub | 8 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 100.0% |
| xor_chain | resyn2_like | 8 | 0.7156 | 0.7188 | 0.8125 | 0.3125 | 37.5% |
| xor_chain | rewrite | 8 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 100.0% |

## Depth 3 — per-(benchmark, optimization) summary

| benchmark | optimization | total_opt_nodes | avg_rank1_region_score | avg_rank1_cone_sim | avg_rank1_cone_support | avg_rank1_cone_size_sim | pct_rank1_above_0_8 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| majority3 | balance | 4 | 0.9688 | 0.9375 | 1.0000 | 1.0000 | 100.0% |
| majority3 | refactor | 3 | 0.8347 | 0.7917 | 0.8889 | 0.8333 | 33.3% |
| majority3 | resub | 4 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 100.0% |
| majority3 | resyn2_like | 3 | 0.8583 | 0.7500 | 1.0000 | 0.8333 | 66.7% |
| majority3 | rewrite | 4 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 100.0% |
| mux2 | balance | 2 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 100.0% |
| mux2 | refactor | 2 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 100.0% |
| mux2 | resub | 2 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 100.0% |
| mux2 | resyn2_like | 2 | 0.7500 | 0.5000 | 1.0000 | 1.0000 | 0.0% |
| mux2 | rewrite | 2 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 100.0% |
| toy_and_or | balance | 2 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 100.0% |
| toy_and_or | refactor | 2 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 100.0% |
| toy_and_or | resub | 2 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 100.0% |
| toy_and_or | resyn2_like | 2 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 100.0% |
| toy_and_or | rewrite | 2 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 100.0% |
| xor_chain | balance | 8 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 100.0% |
| xor_chain | refactor | 8 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 100.0% |
| xor_chain | resub | 8 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 100.0% |
| xor_chain | resyn2_like | 8 | 0.6873 | 0.7188 | 0.7500 | 0.2792 | 37.5% |
| xor_chain | rewrite | 8 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 100.0% |

## Cross-depth comparison (averaged over all benchmark/optimization pairs)

| depth | n_groups | avg_rank1_region_score | avg_rank1_cone_sim | avg_rank1_cone_support | pct_rank1_above_0_8 |
| --- | --- | --- | --- | --- | --- |
| 1 | 20 | 0.9526 | 0.9349 | 0.9734 | 86.9% |
| 2 | 20 | 0.9564 | 0.9349 | 0.9851 | 86.9% |
| 3 | 20 | 0.9550 | 0.9349 | 0.9819 | 86.9% |

## Interpretation

**root_sim_score** — bit-similarity of the root node's output under the global simulation patterns. Identical to the simulation similarity in `top_candidates.csv`; included here for direct comparison with the region-specific signals.

**cone_support_jaccard** — Jaccard overlap of the *local* primary-input boundaries of the two cones.  At depth 1 this is the Jaccard overlap of direct fanins; at depth 3 it approximates the full support overlap but restricted to inputs reachable within 3 levels.  Higher depth → more inputs visible → scores converge toward the global support Jaccard.

**cone_size_sim** — penalises cones of very different internal complexity (node count).  A value near 1.0 means the two cones have about the same number of internal gates, regardless of what those gates compute.

**pct_rank1_above_0_8** — fraction of optimized nodes whose best-match region score ≥ 0.8.  This is a useful single-number quality indicator: a value near 1.0 means almost every optimized node has a structurally similar original counterpart within the shallow fanin cone.

**Depth effect** — shallower cones (depth 1) capture only the immediate gate-level structure; deeper cones (depth 3) increasingly resemble the global support-based matching.  A benchmark where depth-1 scores are already high has very locally stable structure across optimizations; one where scores only improve at depth 3 has more global restructuring.
