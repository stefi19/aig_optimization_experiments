# Ablation Study: Scoring Weight Sensitivity

## Data availability

- `top_candidates.csv`: ✅ loaded
- `sat_verified_candidates.csv`: ✅ loaded

## Scoring configurations

| config | w_sim | w_support | w_depth |
| --- | --- | --- | --- |
| baseline | 0.5500 | 0.3500 | 0.1000 |
| sim_only | 1.0000 | 0.0000 | 0.0000 |
| support_only | 0.0000 | 1.0000 | 0.0000 |
| depth_only | 0.0000 | 0.0000 | 1.0000 |
| sim_sup | 0.5000 | 0.5000 | 0.0000 |
| sim_dep | 0.7000 | 0.0000 | 0.3000 |

## Global summary (averaged over all benchmark/optimization pairs)

| config | weights | avg_rank1_score | rank1_consistency | rank1_precision | mrr |
| --- | --- | --- | --- | --- | --- |
| baseline | sim=0.55 sup=0.35 dep=0.10 | 0.9546 | 100.0% | 69.2% | 0.6917 |
| sim_only | sim=1.00 sup=0.00 dep=0.00 | 0.9391 | 96.7% | 69.2% | 0.6917 |
| support_only | sim=0.00 sup=1.00 dep=0.00 | 0.9906 | 97.1% | 69.2% | 0.6917 |
| depth_only | sim=0.00 sup=0.00 dep=1.00 | 0.9938 | 95.2% | 69.2% | 0.6917 |
| sim_sup | sim=0.50 sup=0.50 dep=0.00 | 0.9584 | 100.0% | 69.2% | 0.6917 |
| sim_dep | sim=0.70 sup=0.00 dep=0.30 | 0.9471 | 98.1% | 69.2% | 0.6917 |

## Per-group detail

| config | weights | benchmark | optimization | total_nodes | avg_rank1_score | rank1_consistency | rank1_precision | mrr |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline | sim=0.55 sup=0.35 dep=0.10 | majority3 | balance | 4 | 0.9656 | 100.0% | 0.0% | 0.0000 |
| baseline | sim=0.55 sup=0.35 dep=0.10 | majority3 | refactor | 3 | 0.8299 | 100.0% | 0.0% | 0.0000 |
| baseline | sim=0.55 sup=0.35 dep=0.10 | majority3 | resub | 4 | 1.0000 | 100.0% | 25.0% | 0.2500 |
| baseline | sim=0.55 sup=0.35 dep=0.10 | majority3 | resyn2_like | 3 | 0.8625 | 100.0% | 33.3% | 0.3333 |
| baseline | sim=0.55 sup=0.35 dep=0.10 | majority3 | rewrite | 4 | 1.0000 | 100.0% | 25.0% | 0.2500 |
| baseline | sim=0.55 sup=0.35 dep=0.10 | mux2 | balance | 2 | 1.0000 | 100.0% | 100.0% | 1.0000 |
| baseline | sim=0.55 sup=0.35 dep=0.10 | mux2 | refactor | 2 | 1.0000 | 100.0% | 100.0% | 1.0000 |
| baseline | sim=0.55 sup=0.35 dep=0.10 | mux2 | resub | 2 | 1.0000 | 100.0% | 100.0% | 1.0000 |
| baseline | sim=0.55 sup=0.35 dep=0.10 | mux2 | resyn2_like | 2 | 0.7250 | 100.0% | 0.0% | 0.0000 |
| baseline | sim=0.55 sup=0.35 dep=0.10 | mux2 | rewrite | 2 | 1.0000 | 100.0% | 100.0% | 1.0000 |
| baseline | sim=0.55 sup=0.35 dep=0.10 | toy_and_or | balance | 2 | 1.0000 | 100.0% | 100.0% | 1.0000 |
| baseline | sim=0.55 sup=0.35 dep=0.10 | toy_and_or | refactor | 2 | 1.0000 | 100.0% | 100.0% | 1.0000 |
| baseline | sim=0.55 sup=0.35 dep=0.10 | toy_and_or | resub | 2 | 1.0000 | 100.0% | 100.0% | 1.0000 |
| baseline | sim=0.55 sup=0.35 dep=0.10 | toy_and_or | resyn2_like | 2 | 1.0000 | 100.0% | 100.0% | 1.0000 |
| baseline | sim=0.55 sup=0.35 dep=0.10 | toy_and_or | rewrite | 2 | 1.0000 | 100.0% | 100.0% | 1.0000 |
| baseline | sim=0.55 sup=0.35 dep=0.10 | xor_chain | balance | 8 | 1.0000 | 100.0% | 100.0% | 1.0000 |
| baseline | sim=0.55 sup=0.35 dep=0.10 | xor_chain | refactor | 8 | 1.0000 | 100.0% | 100.0% | 1.0000 |
| baseline | sim=0.55 sup=0.35 dep=0.10 | xor_chain | resub | 8 | 1.0000 | 100.0% | 100.0% | 1.0000 |
| baseline | sim=0.55 sup=0.35 dep=0.10 | xor_chain | resyn2_like | 8 | 0.7097 | 100.0% | 0.0% | 0.0000 |
| baseline | sim=0.55 sup=0.35 dep=0.10 | xor_chain | rewrite | 8 | 1.0000 | 100.0% | 100.0% | 1.0000 |
| sim_only | sim=1.00 sup=0.00 dep=0.00 | majority3 | balance | 4 | 0.9375 | 100.0% | 0.0% | 0.0000 |
| sim_only | sim=1.00 sup=0.00 dep=0.00 | majority3 | refactor | 3 | 0.8333 | 66.7% | 0.0% | 0.0000 |
| sim_only | sim=1.00 sup=0.00 dep=0.00 | majority3 | resub | 4 | 1.0000 | 100.0% | 25.0% | 0.2500 |
| sim_only | sim=1.00 sup=0.00 dep=0.00 | majority3 | resyn2_like | 3 | 0.7917 | 66.7% | 33.3% | 0.3333 |
| sim_only | sim=1.00 sup=0.00 dep=0.00 | majority3 | rewrite | 4 | 1.0000 | 100.0% | 25.0% | 0.2500 |
| sim_only | sim=1.00 sup=0.00 dep=0.00 | mux2 | balance | 2 | 1.0000 | 100.0% | 100.0% | 1.0000 |
| sim_only | sim=1.00 sup=0.00 dep=0.00 | mux2 | refactor | 2 | 1.0000 | 100.0% | 100.0% | 1.0000 |
| sim_only | sim=1.00 sup=0.00 dep=0.00 | mux2 | resub | 2 | 1.0000 | 100.0% | 100.0% | 1.0000 |
| sim_only | sim=1.00 sup=0.00 dep=0.00 | mux2 | resyn2_like | 2 | 0.5000 | 100.0% | 0.0% | 0.0000 |
| sim_only | sim=1.00 sup=0.00 dep=0.00 | mux2 | rewrite | 2 | 1.0000 | 100.0% | 100.0% | 1.0000 |
| sim_only | sim=1.00 sup=0.00 dep=0.00 | toy_and_or | balance | 2 | 1.0000 | 100.0% | 100.0% | 1.0000 |
| sim_only | sim=1.00 sup=0.00 dep=0.00 | toy_and_or | refactor | 2 | 1.0000 | 100.0% | 100.0% | 1.0000 |
| sim_only | sim=1.00 sup=0.00 dep=0.00 | toy_and_or | resub | 2 | 1.0000 | 100.0% | 100.0% | 1.0000 |
| sim_only | sim=1.00 sup=0.00 dep=0.00 | toy_and_or | resyn2_like | 2 | 1.0000 | 100.0% | 100.0% | 1.0000 |
| sim_only | sim=1.00 sup=0.00 dep=0.00 | toy_and_or | rewrite | 2 | 1.0000 | 100.0% | 100.0% | 1.0000 |
| sim_only | sim=1.00 sup=0.00 dep=0.00 | xor_chain | balance | 8 | 1.0000 | 100.0% | 100.0% | 1.0000 |
| sim_only | sim=1.00 sup=0.00 dep=0.00 | xor_chain | refactor | 8 | 1.0000 | 100.0% | 100.0% | 1.0000 |
| sim_only | sim=1.00 sup=0.00 dep=0.00 | xor_chain | resub | 8 | 1.0000 | 100.0% | 100.0% | 1.0000 |
| sim_only | sim=1.00 sup=0.00 dep=0.00 | xor_chain | resyn2_like | 8 | 0.7188 | 100.0% | 0.0% | 0.0000 |
| sim_only | sim=1.00 sup=0.00 dep=0.00 | xor_chain | rewrite | 8 | 1.0000 | 100.0% | 100.0% | 1.0000 |
| support_only | sim=0.00 sup=1.00 dep=0.00 | majority3 | balance | 4 | 1.0000 | 100.0% | 0.0% | 0.0000 |
| support_only | sim=0.00 sup=1.00 dep=0.00 | majority3 | refactor | 3 | 1.0000 | 66.7% | 0.0% | 0.0000 |
| support_only | sim=0.00 sup=1.00 dep=0.00 | majority3 | resub | 4 | 1.0000 | 100.0% | 25.0% | 0.2500 |
| support_only | sim=0.00 sup=1.00 dep=0.00 | majority3 | resyn2_like | 3 | 1.0000 | 100.0% | 33.3% | 0.3333 |
| support_only | sim=0.00 sup=1.00 dep=0.00 | majority3 | rewrite | 4 | 1.0000 | 100.0% | 25.0% | 0.2500 |
| support_only | sim=0.00 sup=1.00 dep=0.00 | mux2 | balance | 2 | 1.0000 | 100.0% | 100.0% | 1.0000 |
| support_only | sim=0.00 sup=1.00 dep=0.00 | mux2 | refactor | 2 | 1.0000 | 100.0% | 100.0% | 1.0000 |
| support_only | sim=0.00 sup=1.00 dep=0.00 | mux2 | resub | 2 | 1.0000 | 100.0% | 100.0% | 1.0000 |
| support_only | sim=0.00 sup=1.00 dep=0.00 | mux2 | resyn2_like | 2 | 1.0000 | 100.0% | 0.0% | 0.0000 |
| support_only | sim=0.00 sup=1.00 dep=0.00 | mux2 | rewrite | 2 | 1.0000 | 100.0% | 100.0% | 1.0000 |
| support_only | sim=0.00 sup=1.00 dep=0.00 | toy_and_or | balance | 2 | 1.0000 | 100.0% | 100.0% | 1.0000 |
| support_only | sim=0.00 sup=1.00 dep=0.00 | toy_and_or | refactor | 2 | 1.0000 | 100.0% | 100.0% | 1.0000 |
| support_only | sim=0.00 sup=1.00 dep=0.00 | toy_and_or | resub | 2 | 1.0000 | 100.0% | 100.0% | 1.0000 |
| support_only | sim=0.00 sup=1.00 dep=0.00 | toy_and_or | resyn2_like | 2 | 1.0000 | 100.0% | 100.0% | 1.0000 |
| support_only | sim=0.00 sup=1.00 dep=0.00 | toy_and_or | rewrite | 2 | 1.0000 | 100.0% | 100.0% | 1.0000 |
| support_only | sim=0.00 sup=1.00 dep=0.00 | xor_chain | balance | 8 | 1.0000 | 100.0% | 100.0% | 1.0000 |
| support_only | sim=0.00 sup=1.00 dep=0.00 | xor_chain | refactor | 8 | 1.0000 | 100.0% | 100.0% | 1.0000 |
| support_only | sim=0.00 sup=1.00 dep=0.00 | xor_chain | resub | 8 | 1.0000 | 100.0% | 100.0% | 1.0000 |
| support_only | sim=0.00 sup=1.00 dep=0.00 | xor_chain | resyn2_like | 8 | 0.8125 | 75.0% | 0.0% | 0.0000 |
| support_only | sim=0.00 sup=1.00 dep=0.00 | xor_chain | rewrite | 8 | 1.0000 | 100.0% | 100.0% | 1.0000 |
| depth_only | sim=0.00 sup=0.00 dep=1.00 | majority3 | balance | 4 | 1.0000 | 100.0% | 0.0% | 0.0000 |
| depth_only | sim=0.00 sup=0.00 dep=1.00 | majority3 | refactor | 3 | 1.0000 | 66.7% | 0.0% | 0.0000 |
| depth_only | sim=0.00 sup=0.00 dep=1.00 | majority3 | resub | 4 | 1.0000 | 100.0% | 25.0% | 0.2500 |
| depth_only | sim=0.00 sup=0.00 dep=1.00 | majority3 | resyn2_like | 3 | 1.0000 | 100.0% | 33.3% | 0.3333 |
| depth_only | sim=0.00 sup=0.00 dep=1.00 | majority3 | rewrite | 4 | 1.0000 | 100.0% | 25.0% | 0.2500 |
| depth_only | sim=0.00 sup=0.00 dep=1.00 | mux2 | balance | 2 | 1.0000 | 100.0% | 100.0% | 1.0000 |
| depth_only | sim=0.00 sup=0.00 dep=1.00 | mux2 | refactor | 2 | 1.0000 | 100.0% | 100.0% | 1.0000 |
| depth_only | sim=0.00 sup=0.00 dep=1.00 | mux2 | resub | 2 | 1.0000 | 100.0% | 100.0% | 1.0000 |
| depth_only | sim=0.00 sup=0.00 dep=1.00 | mux2 | resyn2_like | 2 | 1.0000 | 100.0% | 0.0% | 0.0000 |
| depth_only | sim=0.00 sup=0.00 dep=1.00 | mux2 | rewrite | 2 | 1.0000 | 100.0% | 100.0% | 1.0000 |
| depth_only | sim=0.00 sup=0.00 dep=1.00 | toy_and_or | balance | 2 | 1.0000 | 100.0% | 100.0% | 1.0000 |
| depth_only | sim=0.00 sup=0.00 dep=1.00 | toy_and_or | refactor | 2 | 1.0000 | 100.0% | 100.0% | 1.0000 |
| depth_only | sim=0.00 sup=0.00 dep=1.00 | toy_and_or | resub | 2 | 1.0000 | 100.0% | 100.0% | 1.0000 |
| depth_only | sim=0.00 sup=0.00 dep=1.00 | toy_and_or | resyn2_like | 2 | 1.0000 | 100.0% | 100.0% | 1.0000 |
| depth_only | sim=0.00 sup=0.00 dep=1.00 | toy_and_or | rewrite | 2 | 1.0000 | 100.0% | 100.0% | 1.0000 |
| depth_only | sim=0.00 sup=0.00 dep=1.00 | xor_chain | balance | 8 | 1.0000 | 100.0% | 100.0% | 1.0000 |
| depth_only | sim=0.00 sup=0.00 dep=1.00 | xor_chain | refactor | 8 | 1.0000 | 100.0% | 100.0% | 1.0000 |
| depth_only | sim=0.00 sup=0.00 dep=1.00 | xor_chain | resub | 8 | 1.0000 | 100.0% | 100.0% | 1.0000 |
| depth_only | sim=0.00 sup=0.00 dep=1.00 | xor_chain | resyn2_like | 8 | 0.8750 | 37.5% | 0.0% | 0.0000 |
| depth_only | sim=0.00 sup=0.00 dep=1.00 | xor_chain | rewrite | 8 | 1.0000 | 100.0% | 100.0% | 1.0000 |
| sim_sup | sim=0.50 sup=0.50 dep=0.00 | majority3 | balance | 4 | 0.9688 | 100.0% | 0.0% | 0.0000 |
| sim_sup | sim=0.50 sup=0.50 dep=0.00 | majority3 | refactor | 3 | 0.8403 | 100.0% | 0.0% | 0.0000 |
| sim_sup | sim=0.50 sup=0.50 dep=0.00 | majority3 | resub | 4 | 1.0000 | 100.0% | 25.0% | 0.2500 |
| sim_sup | sim=0.50 sup=0.50 dep=0.00 | majority3 | resyn2_like | 3 | 0.8750 | 100.0% | 33.3% | 0.3333 |
| sim_sup | sim=0.50 sup=0.50 dep=0.00 | majority3 | rewrite | 4 | 1.0000 | 100.0% | 25.0% | 0.2500 |
| sim_sup | sim=0.50 sup=0.50 dep=0.00 | mux2 | balance | 2 | 1.0000 | 100.0% | 100.0% | 1.0000 |
| sim_sup | sim=0.50 sup=0.50 dep=0.00 | mux2 | refactor | 2 | 1.0000 | 100.0% | 100.0% | 1.0000 |
| sim_sup | sim=0.50 sup=0.50 dep=0.00 | mux2 | resub | 2 | 1.0000 | 100.0% | 100.0% | 1.0000 |
| sim_sup | sim=0.50 sup=0.50 dep=0.00 | mux2 | resyn2_like | 2 | 0.7500 | 100.0% | 0.0% | 0.0000 |
| sim_sup | sim=0.50 sup=0.50 dep=0.00 | mux2 | rewrite | 2 | 1.0000 | 100.0% | 100.0% | 1.0000 |
| sim_sup | sim=0.50 sup=0.50 dep=0.00 | toy_and_or | balance | 2 | 1.0000 | 100.0% | 100.0% | 1.0000 |
| sim_sup | sim=0.50 sup=0.50 dep=0.00 | toy_and_or | refactor | 2 | 1.0000 | 100.0% | 100.0% | 1.0000 |
| sim_sup | sim=0.50 sup=0.50 dep=0.00 | toy_and_or | resub | 2 | 1.0000 | 100.0% | 100.0% | 1.0000 |
| sim_sup | sim=0.50 sup=0.50 dep=0.00 | toy_and_or | resyn2_like | 2 | 1.0000 | 100.0% | 100.0% | 1.0000 |
| sim_sup | sim=0.50 sup=0.50 dep=0.00 | toy_and_or | rewrite | 2 | 1.0000 | 100.0% | 100.0% | 1.0000 |
| sim_sup | sim=0.50 sup=0.50 dep=0.00 | xor_chain | balance | 8 | 1.0000 | 100.0% | 100.0% | 1.0000 |
| sim_sup | sim=0.50 sup=0.50 dep=0.00 | xor_chain | refactor | 8 | 1.0000 | 100.0% | 100.0% | 1.0000 |
| sim_sup | sim=0.50 sup=0.50 dep=0.00 | xor_chain | resub | 8 | 1.0000 | 100.0% | 100.0% | 1.0000 |
| sim_sup | sim=0.50 sup=0.50 dep=0.00 | xor_chain | resyn2_like | 8 | 0.7344 | 100.0% | 0.0% | 0.0000 |
| sim_sup | sim=0.50 sup=0.50 dep=0.00 | xor_chain | rewrite | 8 | 1.0000 | 100.0% | 100.0% | 1.0000 |
| sim_dep | sim=0.70 sup=0.00 dep=0.30 | majority3 | balance | 4 | 0.9563 | 100.0% | 0.0% | 0.0000 |
| sim_dep | sim=0.70 sup=0.00 dep=0.30 | majority3 | refactor | 3 | 0.8042 | 100.0% | 0.0% | 0.0000 |
| sim_dep | sim=0.70 sup=0.00 dep=0.30 | majority3 | resub | 4 | 1.0000 | 100.0% | 25.0% | 0.2500 |
| sim_dep | sim=0.70 sup=0.00 dep=0.30 | majority3 | resyn2_like | 3 | 0.8250 | 100.0% | 33.3% | 0.3333 |
| sim_dep | sim=0.70 sup=0.00 dep=0.30 | majority3 | rewrite | 4 | 1.0000 | 100.0% | 25.0% | 0.2500 |
| sim_dep | sim=0.70 sup=0.00 dep=0.30 | mux2 | balance | 2 | 1.0000 | 100.0% | 100.0% | 1.0000 |
| sim_dep | sim=0.70 sup=0.00 dep=0.30 | mux2 | refactor | 2 | 1.0000 | 100.0% | 100.0% | 1.0000 |
| sim_dep | sim=0.70 sup=0.00 dep=0.30 | mux2 | resub | 2 | 1.0000 | 100.0% | 100.0% | 1.0000 |
| sim_dep | sim=0.70 sup=0.00 dep=0.30 | mux2 | resyn2_like | 2 | 0.6500 | 100.0% | 0.0% | 0.0000 |
| sim_dep | sim=0.70 sup=0.00 dep=0.30 | mux2 | rewrite | 2 | 1.0000 | 100.0% | 100.0% | 1.0000 |
| sim_dep | sim=0.70 sup=0.00 dep=0.30 | toy_and_or | balance | 2 | 1.0000 | 100.0% | 100.0% | 1.0000 |
| sim_dep | sim=0.70 sup=0.00 dep=0.30 | toy_and_or | refactor | 2 | 1.0000 | 100.0% | 100.0% | 1.0000 |
| sim_dep | sim=0.70 sup=0.00 dep=0.30 | toy_and_or | resub | 2 | 1.0000 | 100.0% | 100.0% | 1.0000 |
| sim_dep | sim=0.70 sup=0.00 dep=0.30 | toy_and_or | resyn2_like | 2 | 1.0000 | 100.0% | 100.0% | 1.0000 |
| sim_dep | sim=0.70 sup=0.00 dep=0.30 | toy_and_or | rewrite | 2 | 1.0000 | 100.0% | 100.0% | 1.0000 |
| sim_dep | sim=0.70 sup=0.00 dep=0.30 | xor_chain | balance | 8 | 1.0000 | 100.0% | 100.0% | 1.0000 |
| sim_dep | sim=0.70 sup=0.00 dep=0.30 | xor_chain | refactor | 8 | 1.0000 | 100.0% | 100.0% | 1.0000 |
| sim_dep | sim=0.70 sup=0.00 dep=0.30 | xor_chain | resub | 8 | 1.0000 | 100.0% | 100.0% | 1.0000 |
| sim_dep | sim=0.70 sup=0.00 dep=0.30 | xor_chain | resyn2_like | 8 | 0.7063 | 62.5% | 0.0% | 0.0000 |
| sim_dep | sim=0.70 sup=0.00 dep=0.30 | xor_chain | rewrite | 8 | 1.0000 | 100.0% | 100.0% | 1.0000 |

## Interpretation

**avg_rank1_score** — mean re-scored value of the rank-1 candidate under each config. A higher score does not necessarily mean better ranking quality; configs that use fewer signals can achieve artificially high scores if that signal happens to be large for all nodes.

**rank1_consistency** — fraction of nodes where this config's rank-1 choice agrees with the baseline (0.55/0.35/0.10) choice. A value near 1.0 means removing or down-weighting this signal does not change the top candidate; a low value means that signal is a decisive tie-breaker.

**rank1_precision** — fraction of rank-1 candidates that were formally verified by ABC. The config with the highest precision places the correct match at rank 1 most often.

**mrr** (Mean Reciprocal Rank) — how high the first verified match appears on average. MRR=1.0 means verified matches were always rank 1.
