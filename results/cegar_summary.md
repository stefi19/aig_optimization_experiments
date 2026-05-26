# CEGAR-Style Candidate Refinement — Prototype

> **Prototype notice**: This script implements a lightweight approximation of counterexample-guided refinement.  It does *not* call ABC or any SAT solver; it uses previously recorded ABC rejections as penalty signals.  A real CEGAR loop would iteratively re-verify the new rank-1 candidate after each refinement step.  See the module docstring for known limitations.

## Data availability

- `top_candidates.csv`: ✅ loaded
- `sat_verified_candidates.csv`: ✅ loaded
- Rejected pairs used as penalty sources: **20**

## Configuration

- `REJECTION_WEIGHT` = **0.2** — fraction of original score a candidate identical to a rejected one loses
- Feature space: `['simulation_similarity', 'support_overlap', 'depth_similarity']`
- Penalty formula: `penalty = 0.2 × max_over_rejections(feature_sim)`
- Refined score: `max(0, combined_score − penalty)`
- Similarity metric: `1 − L1_distance / 3`

## Per-(benchmark, optimization) summary

| benchmark | optimization | total_nodes | nodes_with_penalty | nodes_rank1_changed | n_rejected_pairs | avg_original_rank1 | avg_refined_rank1 | avg_penalty_rank1 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| generated_adder_4 | balance | 31 | 0 | 0 | 0 | 1.0000 | 1.0000 | 0.0000 |
| generated_adder_4 | compress2rs | 23 | 0 | 0 | 0 | 0.8874 | 0.8874 | 0.0000 |
| generated_adder_4 | dc2 | 23 | 0 | 0 | 0 | 0.8874 | 0.8874 | 0.0000 |
| generated_adder_4 | refactor | 23 | 0 | 0 | 0 | 0.8874 | 0.8874 | 0.0000 |
| generated_adder_4 | refactor_z | 23 | 0 | 0 | 0 | 0.8874 | 0.8874 | 0.0000 |
| generated_adder_4 | resub | 31 | 0 | 0 | 0 | 1.0000 | 1.0000 | 0.0000 |
| generated_adder_4 | resyn | 28 | 0 | 0 | 0 | 0.9709 | 0.9709 | 0.0000 |
| generated_adder_4 | resyn2 | 23 | 0 | 0 | 0 | 0.8874 | 0.8874 | 0.0000 |
| generated_adder_4 | resyn2_like | 23 | 0 | 0 | 0 | 0.8874 | 0.8874 | 0.0000 |
| generated_adder_4 | rewrite | 28 | 0 | 0 | 0 | 0.9709 | 0.9709 | 0.0000 |
| generated_adder_4 | rewrite_z | 28 | 0 | 0 | 0 | 0.9709 | 0.9709 | 0.0000 |
| generated_adder_8 | balance | 63 | 0 | 0 | 0 | 1.0000 | 1.0000 | 0.0000 |
| generated_adder_8 | compress2rs | 47 | 0 | 0 | 0 | 0.8932 | 0.8932 | 0.0000 |
| generated_adder_8 | dc2 | 47 | 0 | 0 | 0 | 0.8932 | 0.8932 | 0.0000 |
| generated_adder_8 | refactor | 47 | 0 | 0 | 0 | 0.8932 | 0.8932 | 0.0000 |
| generated_adder_8 | refactor_z | 47 | 0 | 0 | 0 | 0.8932 | 0.8932 | 0.0000 |
| generated_adder_8 | resub | 63 | 0 | 0 | 0 | 1.0000 | 1.0000 | 0.0000 |
| generated_adder_8 | resyn | 56 | 0 | 0 | 0 | 0.9682 | 0.9682 | 0.0000 |
| generated_adder_8 | resyn2 | 47 | 0 | 0 | 0 | 0.8932 | 0.8932 | 0.0000 |
| generated_adder_8 | resyn2_like | 47 | 0 | 0 | 0 | 0.8932 | 0.8932 | 0.0000 |
| generated_adder_8 | rewrite | 56 | 0 | 0 | 0 | 0.9682 | 0.9682 | 0.0000 |
| generated_adder_8 | rewrite_z | 56 | 0 | 0 | 0 | 0.9682 | 0.9682 | 0.0000 |
| generated_multiplier_2 | balance | 8 | 0 | 0 | 0 | 1.0000 | 1.0000 | 0.0000 |
| generated_multiplier_2 | compress2rs | 4 | 0 | 0 | 0 | 0.9141 | 0.9141 | 0.0000 |
| generated_multiplier_2 | dc2 | 4 | 0 | 0 | 0 | 0.8539 | 0.8539 | 0.0000 |
| generated_multiplier_2 | refactor | 6 | 0 | 0 | 0 | 0.8740 | 0.8740 | 0.0000 |
| generated_multiplier_2 | refactor_z | 6 | 0 | 0 | 0 | 0.8740 | 0.8740 | 0.0000 |
| generated_multiplier_2 | resub | 5 | 0 | 0 | 0 | 1.0000 | 1.0000 | 0.0000 |
| generated_multiplier_2 | resyn | 5 | 0 | 0 | 0 | 1.0000 | 1.0000 | 0.0000 |
| generated_multiplier_2 | resyn2 | 4 | 0 | 0 | 0 | 0.9141 | 0.9141 | 0.0000 |
| generated_multiplier_2 | resyn2_like | 4 | 0 | 0 | 0 | 0.9141 | 0.9141 | 0.0000 |
| generated_multiplier_2 | rewrite | 5 | 0 | 0 | 0 | 1.0000 | 1.0000 | 0.0000 |
| generated_multiplier_2 | rewrite_z | 5 | 0 | 0 | 0 | 1.0000 | 1.0000 | 0.0000 |
| generated_multiplier_4 | balance | 112 | 0 | 0 | 0 | 0.9970 | 0.9970 | 0.0000 |
| generated_multiplier_4 | compress2rs | 75 | 1 | 0 | 1 | 0.9360 | 0.9333 | 0.0027 |
| generated_multiplier_4 | dc2 | 82 | 1 | 0 | 1 | 0.9330 | 0.9306 | 0.0024 |
| generated_multiplier_4 | refactor | 100 | 0 | 0 | 0 | 0.9789 | 0.9789 | 0.0000 |
| generated_multiplier_4 | refactor_z | 100 | 0 | 0 | 0 | 0.9500 | 0.9500 | 0.0000 |
| generated_multiplier_4 | resub | 101 | 0 | 0 | 0 | 0.9927 | 0.9927 | 0.0000 |
| generated_multiplier_4 | resyn | 83 | 1 | 0 | 1 | 0.9388 | 0.9363 | 0.0024 |
| generated_multiplier_4 | resyn2 | 82 | 1 | 0 | 1 | 0.9339 | 0.9315 | 0.0024 |
| generated_multiplier_4 | resyn2_like | 82 | 1 | 0 | 1 | 0.9339 | 0.9315 | 0.0024 |
| generated_multiplier_4 | rewrite | 85 | 1 | 0 | 1 | 0.9730 | 0.9706 | 0.0024 |
| generated_multiplier_4 | rewrite_z | 91 | 4 | 2 | 4 | 0.9337 | 0.9251 | 0.0077 |
| generated_mux_tree_16 | balance | 44 | 0 | 0 | 0 | 1.0000 | 1.0000 | 0.0000 |
| generated_mux_tree_16 | compress2rs | 44 | 0 | 0 | 0 | 0.7891 | 0.7891 | 0.0000 |
| generated_mux_tree_16 | dc2 | 44 | 0 | 0 | 0 | 0.6463 | 0.6463 | 0.0000 |
| generated_mux_tree_16 | refactor | 44 | 0 | 0 | 0 | 1.0000 | 1.0000 | 0.0000 |
| generated_mux_tree_16 | refactor_z | 44 | 0 | 0 | 0 | 0.9286 | 0.9286 | 0.0000 |
| generated_mux_tree_16 | resub | 44 | 0 | 0 | 0 | 1.0000 | 1.0000 | 0.0000 |
| generated_mux_tree_16 | resyn | 44 | 0 | 0 | 0 | 0.7982 | 0.7982 | 0.0000 |
| generated_mux_tree_16 | resyn2 | 44 | 0 | 0 | 0 | 0.7891 | 0.7891 | 0.0000 |
| generated_mux_tree_16 | resyn2_like | 44 | 0 | 0 | 0 | 0.7891 | 0.7891 | 0.0000 |
| generated_mux_tree_16 | rewrite | 44 | 0 | 0 | 0 | 1.0000 | 1.0000 | 0.0000 |
| generated_mux_tree_16 | rewrite_z | 44 | 0 | 0 | 0 | 0.8301 | 0.8301 | 0.0000 |
| generated_mux_tree_4 | balance | 8 | 0 | 0 | 0 | 1.0000 | 1.0000 | 0.0000 |
| generated_mux_tree_4 | compress2rs | 8 | 0 | 0 | 0 | 0.7250 | 0.7250 | 0.0000 |
| generated_mux_tree_4 | dc2 | 8 | 0 | 0 | 0 | 0.8883 | 0.8883 | 0.0000 |
| generated_mux_tree_4 | refactor | 8 | 0 | 0 | 0 | 1.0000 | 1.0000 | 0.0000 |
| generated_mux_tree_4 | refactor_z | 8 | 0 | 0 | 0 | 0.7250 | 0.7250 | 0.0000 |
| generated_mux_tree_4 | resub | 8 | 0 | 0 | 0 | 1.0000 | 1.0000 | 0.0000 |
| generated_mux_tree_4 | resyn | 8 | 0 | 0 | 0 | 0.8109 | 0.8109 | 0.0000 |
| generated_mux_tree_4 | resyn2 | 8 | 0 | 0 | 0 | 0.7250 | 0.7250 | 0.0000 |
| generated_mux_tree_4 | resyn2_like | 8 | 0 | 0 | 0 | 0.7250 | 0.7250 | 0.0000 |
| generated_mux_tree_4 | rewrite | 8 | 0 | 0 | 0 | 1.0000 | 1.0000 | 0.0000 |
| generated_mux_tree_4 | rewrite_z | 8 | 0 | 0 | 0 | 0.8109 | 0.8109 | 0.0000 |
| generated_mux_tree_8 | balance | 20 | 0 | 0 | 0 | 1.0000 | 1.0000 | 0.0000 |
| generated_mux_tree_8 | compress2rs | 20 | 0 | 0 | 0 | 0.8287 | 0.8287 | 0.0000 |
| generated_mux_tree_8 | dc2 | 20 | 0 | 0 | 0 | 0.5815 | 0.5815 | 0.0000 |
| generated_mux_tree_8 | refactor | 20 | 0 | 0 | 0 | 1.0000 | 1.0000 | 0.0000 |
| generated_mux_tree_8 | refactor_z | 20 | 0 | 0 | 0 | 0.8975 | 0.8975 | 0.0000 |
| generated_mux_tree_8 | resub | 20 | 0 | 0 | 0 | 1.0000 | 1.0000 | 0.0000 |
| generated_mux_tree_8 | resyn | 20 | 0 | 0 | 0 | 0.8488 | 0.8488 | 0.0000 |
| generated_mux_tree_8 | resyn2 | 20 | 0 | 0 | 0 | 0.8287 | 0.8287 | 0.0000 |
| generated_mux_tree_8 | resyn2_like | 20 | 0 | 0 | 0 | 0.8287 | 0.8287 | 0.0000 |
| generated_mux_tree_8 | rewrite | 20 | 0 | 0 | 0 | 1.0000 | 1.0000 | 0.0000 |
| generated_mux_tree_8 | rewrite_z | 20 | 0 | 0 | 0 | 0.8488 | 0.8488 | 0.0000 |
| generated_random_medium | balance | 17 | 0 | 0 | 0 | 1.0000 | 1.0000 | 0.0000 |
| generated_random_medium | compress2rs | 17 | 1 | 0 | 1 | 0.8466 | 0.8348 | 0.0118 |
| generated_random_medium | dc2 | 17 | 0 | 0 | 0 | 0.8560 | 0.8560 | 0.0000 |
| generated_random_medium | refactor | 17 | 0 | 0 | 0 | 1.0000 | 1.0000 | 0.0000 |
| generated_random_medium | refactor_z | 17 | 0 | 0 | 0 | 0.9216 | 0.9216 | 0.0000 |
| generated_random_medium | resub | 17 | 0 | 0 | 0 | 1.0000 | 1.0000 | 0.0000 |
| generated_random_medium | resyn | 17 | 0 | 0 | 0 | 0.8845 | 0.8845 | 0.0000 |
| generated_random_medium | resyn2 | 17 | 1 | 0 | 1 | 0.8466 | 0.8348 | 0.0118 |
| generated_random_medium | resyn2_like | 17 | 1 | 0 | 1 | 0.8466 | 0.8348 | 0.0118 |
| generated_random_medium | rewrite | 17 | 0 | 0 | 0 | 1.0000 | 1.0000 | 0.0000 |
| generated_random_medium | rewrite_z | 17 | 0 | 0 | 0 | 0.8865 | 0.8865 | 0.0000 |
| generated_xor_chain_16 | balance | 44 | 0 | 0 | 0 | 1.0000 | 1.0000 | 0.0000 |
| generated_xor_chain_16 | compress2rs | 44 | 0 | 0 | 0 | 0.5941 | 0.5941 | 0.0000 |
| generated_xor_chain_16 | dc2 | 44 | 0 | 0 | 0 | 0.5205 | 0.5205 | 0.0000 |
| generated_xor_chain_16 | refactor | 44 | 0 | 0 | 0 | 1.0000 | 1.0000 | 0.0000 |
| generated_xor_chain_16 | refactor_z | 44 | 0 | 0 | 0 | 0.9874 | 0.9874 | 0.0000 |
| generated_xor_chain_16 | resub | 44 | 0 | 0 | 0 | 1.0000 | 1.0000 | 0.0000 |
| generated_xor_chain_16 | resyn | 44 | 0 | 0 | 0 | 0.6067 | 0.6067 | 0.0000 |
| generated_xor_chain_16 | resyn2 | 44 | 0 | 0 | 0 | 0.5941 | 0.5941 | 0.0000 |
| generated_xor_chain_16 | resyn2_like | 44 | 0 | 0 | 0 | 0.5941 | 0.5941 | 0.0000 |
| generated_xor_chain_16 | rewrite | 44 | 0 | 0 | 0 | 1.0000 | 1.0000 | 0.0000 |
| generated_xor_chain_16 | rewrite_z | 44 | 0 | 0 | 0 | 0.6067 | 0.6067 | 0.0000 |
| generated_xor_chain_32 | balance | 92 | 0 | 0 | 0 | 1.0000 | 1.0000 | 0.0000 |
| generated_xor_chain_32 | compress2rs | 92 | 0 | 0 | 0 | 0.5763 | 0.5763 | 0.0000 |
| generated_xor_chain_32 | dc2 | 92 | 0 | 0 | 0 | 0.4750 | 0.4750 | 0.0000 |
| generated_xor_chain_32 | refactor | 92 | 0 | 0 | 0 | 1.0000 | 1.0000 | 0.0000 |
| generated_xor_chain_32 | refactor_z | 92 | 0 | 0 | 0 | 0.9940 | 0.9940 | 0.0000 |
| generated_xor_chain_32 | resub | 92 | 0 | 0 | 0 | 1.0000 | 1.0000 | 0.0000 |
| generated_xor_chain_32 | resyn | 92 | 0 | 0 | 0 | 0.5823 | 0.5823 | 0.0000 |
| generated_xor_chain_32 | resyn2 | 92 | 0 | 0 | 0 | 0.5763 | 0.5763 | 0.0000 |
| generated_xor_chain_32 | resyn2_like | 92 | 0 | 0 | 0 | 0.5763 | 0.5763 | 0.0000 |
| generated_xor_chain_32 | rewrite | 92 | 0 | 0 | 0 | 1.0000 | 1.0000 | 0.0000 |
| generated_xor_chain_32 | rewrite_z | 92 | 0 | 0 | 0 | 0.5823 | 0.5823 | 0.0000 |
| generated_xor_chain_8 | balance | 20 | 0 | 0 | 0 | 1.0000 | 1.0000 | 0.0000 |
| generated_xor_chain_8 | compress2rs | 20 | 0 | 0 | 0 | 0.6257 | 0.6257 | 0.0000 |
| generated_xor_chain_8 | dc2 | 20 | 0 | 0 | 0 | 0.5678 | 0.5678 | 0.0000 |
| generated_xor_chain_8 | refactor | 20 | 0 | 0 | 0 | 1.0000 | 1.0000 | 0.0000 |
| generated_xor_chain_8 | refactor_z | 20 | 0 | 0 | 0 | 0.9719 | 0.9719 | 0.0000 |
| generated_xor_chain_8 | resub | 20 | 0 | 0 | 0 | 1.0000 | 1.0000 | 0.0000 |
| generated_xor_chain_8 | resyn | 20 | 0 | 0 | 0 | 0.6538 | 0.6538 | 0.0000 |
| generated_xor_chain_8 | resyn2 | 20 | 0 | 0 | 0 | 0.6257 | 0.6257 | 0.0000 |
| generated_xor_chain_8 | resyn2_like | 20 | 0 | 0 | 0 | 0.6257 | 0.6257 | 0.0000 |
| generated_xor_chain_8 | rewrite | 20 | 0 | 0 | 0 | 1.0000 | 1.0000 | 0.0000 |
| generated_xor_chain_8 | rewrite_z | 20 | 0 | 0 | 0 | 0.6538 | 0.6538 | 0.0000 |
| majority3 | balance | 4 | 1 | 0 | 1 | 0.9656 | 0.9156 | 0.0500 |
| majority3 | compress2rs | 3 | 0 | 0 | 0 | 0.8625 | 0.8625 | 0.0000 |
| majority3 | dc2 | 3 | 0 | 0 | 0 | 0.8625 | 0.8625 | 0.0000 |
| majority3 | refactor | 3 | 0 | 0 | 0 | 0.8299 | 0.8299 | 0.0000 |
| majority3 | refactor_z | 3 | 0 | 0 | 0 | 0.8625 | 0.8625 | 0.0000 |
| majority3 | resub | 4 | 0 | 0 | 0 | 1.0000 | 1.0000 | 0.0000 |
| majority3 | resyn | 4 | 1 | 0 | 1 | 0.9656 | 0.9156 | 0.0500 |
| majority3 | resyn2 | 3 | 0 | 0 | 0 | 0.8625 | 0.8625 | 0.0000 |
| majority3 | resyn2_like | 3 | 0 | 0 | 0 | 0.8625 | 0.8625 | 0.0000 |
| majority3 | rewrite | 4 | 0 | 0 | 0 | 1.0000 | 1.0000 | 0.0000 |
| majority3 | rewrite_z | 4 | 1 | 0 | 1 | 0.9656 | 0.9156 | 0.0500 |
| mux2 | balance | 2 | 0 | 0 | 0 | 1.0000 | 1.0000 | 0.0000 |
| mux2 | compress2rs | 2 | 0 | 0 | 0 | 0.7250 | 0.7250 | 0.0000 |
| mux2 | dc2 | 2 | 0 | 0 | 0 | 0.7250 | 0.7250 | 0.0000 |
| mux2 | refactor | 2 | 0 | 0 | 0 | 1.0000 | 1.0000 | 0.0000 |
| mux2 | refactor_z | 2 | 0 | 0 | 0 | 0.7250 | 0.7250 | 0.0000 |
| mux2 | resub | 2 | 0 | 0 | 0 | 1.0000 | 1.0000 | 0.0000 |
| mux2 | resyn | 2 | 0 | 0 | 0 | 1.0000 | 1.0000 | 0.0000 |
| mux2 | resyn2 | 2 | 0 | 0 | 0 | 0.7250 | 0.7250 | 0.0000 |
| mux2 | resyn2_like | 2 | 0 | 0 | 0 | 0.7250 | 0.7250 | 0.0000 |
| mux2 | rewrite | 2 | 0 | 0 | 0 | 1.0000 | 1.0000 | 0.0000 |
| mux2 | rewrite_z | 2 | 0 | 0 | 0 | 1.0000 | 1.0000 | 0.0000 |
| real_hand_written_comparator_4 | balance | 14 | 0 | 0 | 0 | 0.9741 | 0.9741 | 0.0000 |
| real_hand_written_comparator_4 | compress2rs | 14 | 0 | 0 | 0 | 0.9741 | 0.9741 | 0.0000 |
| real_hand_written_comparator_4 | dc2 | 14 | 0 | 0 | 0 | 0.9339 | 0.9339 | 0.0000 |
| real_hand_written_comparator_4 | refactor | 14 | 0 | 0 | 0 | 1.0000 | 1.0000 | 0.0000 |
| real_hand_written_comparator_4 | refactor_z | 14 | 0 | 0 | 0 | 0.9741 | 0.9741 | 0.0000 |
| real_hand_written_comparator_4 | resub | 14 | 0 | 0 | 0 | 1.0000 | 1.0000 | 0.0000 |
| real_hand_written_comparator_4 | resyn | 14 | 0 | 0 | 0 | 0.8536 | 0.8536 | 0.0000 |
| real_hand_written_comparator_4 | resyn2 | 14 | 0 | 0 | 0 | 0.9741 | 0.9741 | 0.0000 |
| real_hand_written_comparator_4 | resyn2_like | 14 | 0 | 0 | 0 | 0.9741 | 0.9741 | 0.0000 |
| real_hand_written_comparator_4 | rewrite | 14 | 0 | 0 | 0 | 1.0000 | 1.0000 | 0.0000 |
| real_hand_written_comparator_4 | rewrite_z | 14 | 0 | 0 | 0 | 0.9256 | 0.9256 | 0.0000 |
| real_hand_written_full_adder | balance | 9 | 1 | 0 | 1 | 0.9847 | 0.9625 | 0.0222 |
| real_hand_written_full_adder | compress2rs | 5 | 0 | 0 | 0 | 0.9250 | 0.9250 | 0.0000 |
| real_hand_written_full_adder | dc2 | 6 | 0 | 0 | 0 | 0.8490 | 0.8490 | 0.0000 |
| real_hand_written_full_adder | refactor | 8 | 0 | 0 | 0 | 0.9531 | 0.9531 | 0.0000 |
| real_hand_written_full_adder | refactor_z | 8 | 0 | 0 | 0 | 0.9016 | 0.9016 | 0.0000 |
| real_hand_written_full_adder | resub | 9 | 0 | 0 | 0 | 1.0000 | 1.0000 | 0.0000 |
| real_hand_written_full_adder | resyn | 9 | 1 | 0 | 1 | 0.9847 | 0.9625 | 0.0222 |
| real_hand_written_full_adder | resyn2 | 8 | 0 | 0 | 0 | 0.9016 | 0.9016 | 0.0000 |
| real_hand_written_full_adder | resyn2_like | 8 | 0 | 0 | 0 | 0.9016 | 0.9016 | 0.0000 |
| real_hand_written_full_adder | rewrite | 9 | 0 | 0 | 0 | 1.0000 | 1.0000 | 0.0000 |
| real_hand_written_full_adder | rewrite_z | 9 | 1 | 0 | 1 | 0.9847 | 0.9625 | 0.0222 |
| real_hand_written_mux_4to1 | balance | 10 | 0 | 0 | 0 | 0.9058 | 0.9058 | 0.0000 |
| real_hand_written_mux_4to1 | compress2rs | 8 | 0 | 0 | 0 | 0.6505 | 0.6505 | 0.0000 |
| real_hand_written_mux_4to1 | dc2 | 8 | 0 | 0 | 0 | 0.7497 | 0.7497 | 0.0000 |
| real_hand_written_mux_4to1 | refactor | 8 | 0 | 0 | 0 | 0.7620 | 0.7620 | 0.0000 |
| real_hand_written_mux_4to1 | refactor_z | 8 | 0 | 0 | 0 | 0.6505 | 0.6505 | 0.0000 |
| real_hand_written_mux_4to1 | resub | 10 | 0 | 0 | 0 | 1.0000 | 1.0000 | 0.0000 |
| real_hand_written_mux_4to1 | resyn | 8 | 0 | 0 | 0 | 0.7286 | 0.7286 | 0.0000 |
| real_hand_written_mux_4to1 | resyn2 | 8 | 0 | 0 | 0 | 0.6505 | 0.6505 | 0.0000 |
| real_hand_written_mux_4to1 | resyn2_like | 8 | 0 | 0 | 0 | 0.6505 | 0.6505 | 0.0000 |
| real_hand_written_mux_4to1 | rewrite | 8 | 0 | 0 | 0 | 0.7286 | 0.7286 | 0.0000 |
| real_hand_written_mux_4to1 | rewrite_z | 8 | 0 | 0 | 0 | 0.7286 | 0.7286 | 0.0000 |
| real_hand_written_parity_8 | balance | 20 | 0 | 0 | 0 | 1.0000 | 1.0000 | 0.0000 |
| real_hand_written_parity_8 | compress2rs | 20 | 0 | 0 | 0 | 0.8594 | 0.8594 | 0.0000 |
| real_hand_written_parity_8 | dc2 | 20 | 1 | 0 | 1 | 0.8071 | 0.7971 | 0.0100 |
| real_hand_written_parity_8 | refactor | 20 | 0 | 0 | 0 | 1.0000 | 1.0000 | 0.0000 |
| real_hand_written_parity_8 | refactor_z | 20 | 0 | 0 | 0 | 0.8875 | 0.8875 | 0.0000 |
| real_hand_written_parity_8 | resub | 20 | 0 | 0 | 0 | 1.0000 | 1.0000 | 0.0000 |
| real_hand_written_parity_8 | resyn | 20 | 0 | 0 | 0 | 0.9719 | 0.9719 | 0.0000 |
| real_hand_written_parity_8 | resyn2 | 20 | 0 | 0 | 0 | 0.8594 | 0.8594 | 0.0000 |
| real_hand_written_parity_8 | resyn2_like | 20 | 0 | 0 | 0 | 0.8594 | 0.8594 | 0.0000 |
| real_hand_written_parity_8 | rewrite | 20 | 0 | 0 | 0 | 1.0000 | 1.0000 | 0.0000 |
| real_hand_written_parity_8 | rewrite_z | 20 | 0 | 0 | 0 | 0.9719 | 0.9719 | 0.0000 |
| real_hand_written_priority_enc_4 | balance | 2 | 0 | 0 | 0 | 1.0000 | 1.0000 | 0.0000 |
| real_hand_written_priority_enc_4 | compress2rs | 2 | 0 | 0 | 0 | 1.0000 | 1.0000 | 0.0000 |
| real_hand_written_priority_enc_4 | dc2 | 2 | 0 | 0 | 0 | 0.7750 | 0.7750 | 0.0000 |
| real_hand_written_priority_enc_4 | refactor | 2 | 0 | 0 | 0 | 1.0000 | 1.0000 | 0.0000 |
| real_hand_written_priority_enc_4 | refactor_z | 2 | 0 | 0 | 0 | 1.0000 | 1.0000 | 0.0000 |
| real_hand_written_priority_enc_4 | resub | 2 | 0 | 0 | 0 | 1.0000 | 1.0000 | 0.0000 |
| real_hand_written_priority_enc_4 | resyn | 2 | 0 | 0 | 0 | 1.0000 | 1.0000 | 0.0000 |
| real_hand_written_priority_enc_4 | resyn2 | 2 | 0 | 0 | 0 | 1.0000 | 1.0000 | 0.0000 |
| real_hand_written_priority_enc_4 | resyn2_like | 2 | 0 | 0 | 0 | 1.0000 | 1.0000 | 0.0000 |
| real_hand_written_priority_enc_4 | rewrite | 2 | 0 | 0 | 0 | 1.0000 | 1.0000 | 0.0000 |
| real_hand_written_priority_enc_4 | rewrite_z | 2 | 0 | 0 | 0 | 1.0000 | 1.0000 | 0.0000 |
| toy_and_or | balance | 2 | 0 | 0 | 0 | 1.0000 | 1.0000 | 0.0000 |
| toy_and_or | compress2rs | 2 | 0 | 0 | 0 | 1.0000 | 1.0000 | 0.0000 |
| toy_and_or | dc2 | 2 | 0 | 0 | 0 | 1.0000 | 1.0000 | 0.0000 |
| toy_and_or | refactor | 2 | 0 | 0 | 0 | 1.0000 | 1.0000 | 0.0000 |
| toy_and_or | refactor_z | 2 | 0 | 0 | 0 | 1.0000 | 1.0000 | 0.0000 |
| toy_and_or | resub | 2 | 0 | 0 | 0 | 1.0000 | 1.0000 | 0.0000 |
| toy_and_or | resyn | 2 | 0 | 0 | 0 | 1.0000 | 1.0000 | 0.0000 |
| toy_and_or | resyn2 | 2 | 0 | 0 | 0 | 1.0000 | 1.0000 | 0.0000 |
| toy_and_or | resyn2_like | 2 | 0 | 0 | 0 | 1.0000 | 1.0000 | 0.0000 |
| toy_and_or | rewrite | 2 | 0 | 0 | 0 | 1.0000 | 1.0000 | 0.0000 |
| toy_and_or | rewrite_z | 2 | 0 | 0 | 0 | 1.0000 | 1.0000 | 0.0000 |
| xor_chain | balance | 8 | 0 | 0 | 0 | 1.0000 | 1.0000 | 0.0000 |
| xor_chain | compress2rs | 8 | 0 | 0 | 0 | 0.7097 | 0.7097 | 0.0000 |
| xor_chain | dc2 | 8 | 0 | 0 | 0 | 0.7149 | 0.7149 | 0.0000 |
| xor_chain | refactor | 8 | 0 | 0 | 0 | 1.0000 | 1.0000 | 0.0000 |
| xor_chain | refactor_z | 8 | 0 | 0 | 0 | 0.9297 | 0.9297 | 0.0000 |
| xor_chain | resub | 8 | 0 | 0 | 0 | 1.0000 | 1.0000 | 0.0000 |
| xor_chain | resyn | 8 | 0 | 0 | 0 | 0.7800 | 0.7800 | 0.0000 |
| xor_chain | resyn2 | 8 | 0 | 0 | 0 | 0.7097 | 0.7097 | 0.0000 |
| xor_chain | resyn2_like | 8 | 0 | 0 | 0 | 0.7097 | 0.7097 | 0.0000 |
| xor_chain | rewrite | 8 | 0 | 0 | 0 | 1.0000 | 1.0000 | 0.0000 |
| xor_chain | rewrite_z | 8 | 0 | 0 | 0 | 0.7800 | 0.7800 | 0.0000 |

## Global rollup

| total_nodes | nodes_with_penalty | pct_penalized | nodes_rank1_changed | pct_rank1_changed | n_rejected_pairs | avg_original_rank1 | avg_refined_rank1 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 5350 | 20 | 0.4% | 2 | 0.0% | 20 | 0.8901 | 0.8888 |

## Rank changes

- **4** candidate rows moved to a higher rank (rank_change > 0)
- **3** candidate rows moved to a lower rank (rank_change < 0)
- **26507** rows unchanged

### Most penalised candidates (largest rank drops)

| benchmark              | optimization   | optimized_node   | original_candidate   |   combined_score |   penalty |   refined_score |   rank |   cegar_rank |
|:-----------------------|:---------------|:-----------------|:---------------------|-----------------:|----------:|----------------:|-------:|-------------:|
| generated_multiplier_4 | rewrite_z      | new_n104         | new_n105             |         0.901172 |   0.19375 |        0.707422 |      3 |            5 |
| generated_multiplier_4 | rewrite_z      | new_n104         | new_n104             |         0.952734 |   0.2     |        0.752734 |      1 |            2 |
| generated_multiplier_4 | rewrite_z      | new_n40          | new_n40              |         0.965625 |   0.2     |        0.765625 |      1 |            2 |

## Interpretation

**What the penalty signal captures**: when ABC proves two nodes are *not* equivalent, the feature vector of that rejected pair identifies a region of score space where the simulation / support / depth signals are collectively misleading.  Other candidates for the same optimised node that fall in the same region are penalised, under the hypothesis that the misleading pattern is local to that region.

**When penalties are zero**: if no ABC rejections are available (e.g. the SAT stage has not been run, or all checked candidates were verified), the refined ranking is identical to the original ranking.  This is the correct behaviour — without evidence of spurious regions, no adjustment is warranted.

**`nodes_rank1_changed`**: the most actionable metric.  A value > 0 means CEGAR refinement re-ordered the top candidate for at least one node.  In a full iterative loop these new rank-1 candidates would be submitted to ABC next; the loop terminates when no new rejections appear.

**Known limitations of this prototype**:
1. Penalties are not iterated — a single refinement pass is performed.
2. Only rank-1 ABC results are currently available as rejection sources.
3. The feature similarity is a coarse L1 proxy; a learned distance metric would be more precise.
4. `refined_score` is clipped at 0 and may not preserve the relative ordering of heavily penalised candidates well.
