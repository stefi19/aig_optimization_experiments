# Top-K Recovery Evaluation

## Data availability

- `top_candidates.csv`: ✅ loaded
- `sat_verified_candidates.csv`: ✅ loaded

## Recovery at K=1 (rank-1 candidate only)

| benchmark | optimization | verified_at_k | total_nodes | recovery_at_k | mrr | avg_score_at_1 |
| --- | --- | --- | --- | --- | --- | --- |
| generated_adder_4 | balance | 31 | 31 | 100.0% | 1.0000 | 1.0000 |
| generated_adder_4 | compress2rs | 0 | 23 | 0.0% | 0.0000 | 0.8874 |
| generated_adder_4 | dc2 | 0 | 23 | 0.0% | 0.0000 | 0.8874 |
| generated_adder_4 | refactor | 0 | 23 | 0.0% | 0.0000 | 0.8874 |
| generated_adder_4 | refactor_z | 0 | 23 | 0.0% | 0.0000 | 0.8874 |
| generated_adder_4 | resub | 31 | 31 | 100.0% | 1.0000 | 1.0000 |
| generated_adder_4 | resyn | 15 | 28 | 53.6% | 0.5357 | 0.9709 |
| generated_adder_4 | resyn2 | 0 | 23 | 0.0% | 0.0000 | 0.8874 |
| generated_adder_4 | resyn2_like | 0 | 23 | 0.0% | 0.0000 | 0.8874 |
| generated_adder_4 | rewrite | 15 | 28 | 53.6% | 0.5357 | 0.9709 |
| generated_adder_4 | rewrite_z | 15 | 28 | 53.6% | 0.5357 | 0.9709 |
| generated_adder_8 | balance | 63 | 63 | 100.0% | 1.0000 | 1.0000 |
| generated_adder_8 | compress2rs | 0 | 47 | 0.0% | 0.0000 | 0.8932 |
| generated_adder_8 | dc2 | 0 | 47 | 0.0% | 0.0000 | 0.8932 |
| generated_adder_8 | refactor | 0 | 47 | 0.0% | 0.0000 | 0.8932 |
| generated_adder_8 | refactor_z | 0 | 47 | 0.0% | 0.0000 | 0.8932 |
| generated_adder_8 | resub | 63 | 63 | 100.0% | 1.0000 | 1.0000 |
| generated_adder_8 | resyn | 15 | 56 | 26.8% | 0.2679 | 0.9682 |
| generated_adder_8 | resyn2 | 0 | 47 | 0.0% | 0.0000 | 0.8932 |
| generated_adder_8 | resyn2_like | 0 | 47 | 0.0% | 0.0000 | 0.8932 |
| generated_adder_8 | rewrite | 15 | 56 | 26.8% | 0.2679 | 0.9682 |
| generated_adder_8 | rewrite_z | 15 | 56 | 26.8% | 0.2679 | 0.9682 |
| generated_multiplier_2 | balance | 8 | 8 | 100.0% | 1.0000 | 1.0000 |
| generated_multiplier_2 | compress2rs | 2 | 4 | 50.0% | 0.5000 | 0.9141 |
| generated_multiplier_2 | dc2 | 2 | 4 | 50.0% | 0.5000 | 0.8539 |
| generated_multiplier_2 | refactor | 3 | 6 | 50.0% | 0.5000 | 0.8740 |
| generated_multiplier_2 | refactor_z | 3 | 6 | 50.0% | 0.5000 | 0.8740 |
| generated_multiplier_2 | resub | 5 | 5 | 100.0% | 1.0000 | 1.0000 |
| generated_multiplier_2 | resyn | 5 | 5 | 100.0% | 1.0000 | 1.0000 |
| generated_multiplier_2 | resyn2 | 2 | 4 | 50.0% | 0.5000 | 0.9141 |
| generated_multiplier_2 | resyn2_like | 2 | 4 | 50.0% | 0.5000 | 0.9141 |
| generated_multiplier_2 | rewrite | 5 | 5 | 100.0% | 1.0000 | 1.0000 |
| generated_multiplier_2 | rewrite_z | 5 | 5 | 100.0% | 1.0000 | 1.0000 |
| generated_multiplier_4 | balance | 96 | 112 | 85.7% | 0.8571 | 0.9970 |
| generated_multiplier_4 | compress2rs | 3 | 75 | 4.0% | 0.0400 | 0.9360 |
| generated_multiplier_4 | dc2 | 3 | 82 | 3.7% | 0.0366 | 0.9330 |
| generated_multiplier_4 | refactor | 8 | 100 | 8.0% | 0.0800 | 0.9789 |
| generated_multiplier_4 | refactor_z | 4 | 100 | 4.0% | 0.0400 | 0.9500 |
| generated_multiplier_4 | resub | 18 | 101 | 17.8% | 0.1782 | 0.9927 |
| generated_multiplier_4 | resyn | 5 | 83 | 6.0% | 0.0602 | 0.9388 |
| generated_multiplier_4 | resyn2 | 3 | 82 | 3.7% | 0.0366 | 0.9339 |
| generated_multiplier_4 | resyn2_like | 3 | 82 | 3.7% | 0.0366 | 0.9339 |
| generated_multiplier_4 | rewrite | 15 | 85 | 17.6% | 0.1765 | 0.9730 |
| generated_multiplier_4 | rewrite_z | 5 | 91 | 5.5% | 0.0549 | 0.9337 |
| generated_mux_tree_16 | balance | 1 | 44 | 2.3% | 0.0227 | 1.0000 |
| generated_mux_tree_16 | compress2rs | 0 | 44 | 0.0% | 0.0000 | 0.7891 |
| generated_mux_tree_16 | dc2 | 0 | 44 | 0.0% | 0.0000 | 0.6463 |
| generated_mux_tree_16 | refactor | 1 | 44 | 2.3% | 0.0227 | 1.0000 |
| generated_mux_tree_16 | refactor_z | 2 | 44 | 4.5% | 0.0455 | 0.9286 |
| generated_mux_tree_16 | resub | 1 | 44 | 2.3% | 0.0227 | 1.0000 |
| generated_mux_tree_16 | resyn | 1 | 44 | 2.3% | 0.0227 | 0.7982 |
| generated_mux_tree_16 | resyn2 | 0 | 44 | 0.0% | 0.0000 | 0.7891 |
| generated_mux_tree_16 | resyn2_like | 0 | 44 | 0.0% | 0.0000 | 0.7891 |
| generated_mux_tree_16 | rewrite | 1 | 44 | 2.3% | 0.0227 | 1.0000 |
| generated_mux_tree_16 | rewrite_z | 1 | 44 | 2.3% | 0.0227 | 0.8301 |
| generated_mux_tree_4 | balance | 1 | 8 | 12.5% | 0.1250 | 1.0000 |
| generated_mux_tree_4 | compress2rs | 0 | 8 | 0.0% | 0.0000 | 0.7250 |
| generated_mux_tree_4 | dc2 | 1 | 8 | 12.5% | 0.1250 | 0.8883 |
| generated_mux_tree_4 | refactor | 1 | 8 | 12.5% | 0.1250 | 1.0000 |
| generated_mux_tree_4 | refactor_z | 0 | 8 | 0.0% | 0.0000 | 0.7250 |
| generated_mux_tree_4 | resub | 1 | 8 | 12.5% | 0.1250 | 1.0000 |
| generated_mux_tree_4 | resyn | 1 | 8 | 12.5% | 0.1250 | 0.8109 |
| generated_mux_tree_4 | resyn2 | 0 | 8 | 0.0% | 0.0000 | 0.7250 |
| generated_mux_tree_4 | resyn2_like | 0 | 8 | 0.0% | 0.0000 | 0.7250 |
| generated_mux_tree_4 | rewrite | 1 | 8 | 12.5% | 0.1250 | 1.0000 |
| generated_mux_tree_4 | rewrite_z | 1 | 8 | 12.5% | 0.1250 | 0.8109 |
| generated_mux_tree_8 | balance | 1 | 20 | 5.0% | 0.0500 | 1.0000 |
| generated_mux_tree_8 | compress2rs | 0 | 20 | 0.0% | 0.0000 | 0.8287 |
| generated_mux_tree_8 | dc2 | 0 | 20 | 0.0% | 0.0000 | 0.5815 |
| generated_mux_tree_8 | refactor | 1 | 20 | 5.0% | 0.0500 | 1.0000 |
| generated_mux_tree_8 | refactor_z | 0 | 20 | 0.0% | 0.0000 | 0.8975 |
| generated_mux_tree_8 | resub | 1 | 20 | 5.0% | 0.0500 | 1.0000 |
| generated_mux_tree_8 | resyn | 1 | 20 | 5.0% | 0.0500 | 0.8488 |
| generated_mux_tree_8 | resyn2 | 0 | 20 | 0.0% | 0.0000 | 0.8287 |
| generated_mux_tree_8 | resyn2_like | 0 | 20 | 0.0% | 0.0000 | 0.8287 |
| generated_mux_tree_8 | rewrite | 1 | 20 | 5.0% | 0.0500 | 1.0000 |
| generated_mux_tree_8 | rewrite_z | 1 | 20 | 5.0% | 0.0500 | 0.8488 |
| generated_random_medium | balance | 17 | 17 | 100.0% | 1.0000 | 1.0000 |
| generated_random_medium | compress2rs | 5 | 17 | 29.4% | 0.2941 | 0.8466 |
| generated_random_medium | dc2 | 3 | 17 | 17.6% | 0.1765 | 0.8560 |
| generated_random_medium | refactor | 17 | 17 | 100.0% | 1.0000 | 1.0000 |
| generated_random_medium | refactor_z | 8 | 17 | 47.1% | 0.4706 | 0.9216 |
| generated_random_medium | resub | 17 | 17 | 100.0% | 1.0000 | 1.0000 |
| generated_random_medium | resyn | 5 | 17 | 29.4% | 0.2941 | 0.8845 |
| generated_random_medium | resyn2 | 5 | 17 | 29.4% | 0.2941 | 0.8466 |
| generated_random_medium | resyn2_like | 5 | 17 | 29.4% | 0.2941 | 0.8466 |
| generated_random_medium | rewrite | 17 | 17 | 100.0% | 1.0000 | 1.0000 |
| generated_random_medium | rewrite_z | 9 | 17 | 52.9% | 0.5294 | 0.8865 |
| generated_xor_chain_16 | balance | 44 | 44 | 100.0% | 1.0000 | 1.0000 |
| generated_xor_chain_16 | compress2rs | 0 | 44 | 0.0% | 0.0000 | 0.5941 |
| generated_xor_chain_16 | dc2 | 0 | 44 | 0.0% | 0.0000 | 0.5205 |
| generated_xor_chain_16 | refactor | 44 | 44 | 100.0% | 1.0000 | 1.0000 |
| generated_xor_chain_16 | refactor_z | 41 | 44 | 93.2% | 0.9318 | 0.9874 |
| generated_xor_chain_16 | resub | 44 | 44 | 100.0% | 1.0000 | 1.0000 |
| generated_xor_chain_16 | resyn | 3 | 44 | 6.8% | 0.0682 | 0.6067 |
| generated_xor_chain_16 | resyn2 | 0 | 44 | 0.0% | 0.0000 | 0.5941 |
| generated_xor_chain_16 | resyn2_like | 0 | 44 | 0.0% | 0.0000 | 0.5941 |
| generated_xor_chain_16 | rewrite | 44 | 44 | 100.0% | 1.0000 | 1.0000 |
| generated_xor_chain_16 | rewrite_z | 3 | 44 | 6.8% | 0.0682 | 0.6067 |
| generated_xor_chain_32 | balance | 92 | 92 | 100.0% | 1.0000 | 1.0000 |
| generated_xor_chain_32 | compress2rs | 0 | 92 | 0.0% | 0.0000 | 0.5763 |
| generated_xor_chain_32 | dc2 | 0 | 92 | 0.0% | 0.0000 | 0.4750 |
| generated_xor_chain_32 | refactor | 92 | 92 | 100.0% | 1.0000 | 1.0000 |
| generated_xor_chain_32 | refactor_z | 89 | 92 | 96.7% | 0.9674 | 0.9940 |
| generated_xor_chain_32 | resub | 92 | 92 | 100.0% | 1.0000 | 1.0000 |
| generated_xor_chain_32 | resyn | 3 | 92 | 3.3% | 0.0326 | 0.5823 |
| generated_xor_chain_32 | resyn2 | 0 | 92 | 0.0% | 0.0000 | 0.5763 |
| generated_xor_chain_32 | resyn2_like | 0 | 92 | 0.0% | 0.0000 | 0.5763 |
| generated_xor_chain_32 | rewrite | 92 | 92 | 100.0% | 1.0000 | 1.0000 |
| generated_xor_chain_32 | rewrite_z | 3 | 92 | 3.3% | 0.0326 | 0.5823 |
| generated_xor_chain_8 | balance | 20 | 20 | 100.0% | 1.0000 | 1.0000 |
| generated_xor_chain_8 | compress2rs | 0 | 20 | 0.0% | 0.0000 | 0.6257 |
| generated_xor_chain_8 | dc2 | 0 | 20 | 0.0% | 0.0000 | 0.5678 |
| generated_xor_chain_8 | refactor | 20 | 20 | 100.0% | 1.0000 | 1.0000 |
| generated_xor_chain_8 | refactor_z | 17 | 20 | 85.0% | 0.8500 | 0.9719 |
| generated_xor_chain_8 | resub | 20 | 20 | 100.0% | 1.0000 | 1.0000 |
| generated_xor_chain_8 | resyn | 3 | 20 | 15.0% | 0.1500 | 0.6538 |
| generated_xor_chain_8 | resyn2 | 0 | 20 | 0.0% | 0.0000 | 0.6257 |
| generated_xor_chain_8 | resyn2_like | 0 | 20 | 0.0% | 0.0000 | 0.6257 |
| generated_xor_chain_8 | rewrite | 20 | 20 | 100.0% | 1.0000 | 1.0000 |
| generated_xor_chain_8 | rewrite_z | 3 | 20 | 15.0% | 0.1500 | 0.6538 |
| majority3 | balance | 0 | 4 | 0.0% | 0.0000 | 0.9656 |
| majority3 | compress2rs | 1 | 3 | 33.3% | 0.3333 | 0.8625 |
| majority3 | dc2 | 0 | 3 | 0.0% | 0.0000 | 0.8625 |
| majority3 | refactor | 0 | 3 | 0.0% | 0.0000 | 0.8299 |
| majority3 | refactor_z | 0 | 3 | 0.0% | 0.0000 | 0.8625 |
| majority3 | resub | 1 | 4 | 25.0% | 0.2500 | 1.0000 |
| majority3 | resyn | 0 | 4 | 0.0% | 0.0000 | 0.9656 |
| majority3 | resyn2 | 1 | 3 | 33.3% | 0.3333 | 0.8625 |
| majority3 | resyn2_like | 1 | 3 | 33.3% | 0.3333 | 0.8625 |
| majority3 | rewrite | 1 | 4 | 25.0% | 0.2500 | 1.0000 |
| majority3 | rewrite_z | 1 | 4 | 25.0% | 0.2500 | 0.9656 |
| mux2 | balance | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| mux2 | compress2rs | 0 | 2 | 0.0% | 0.0000 | 0.7250 |
| mux2 | dc2 | 0 | 2 | 0.0% | 0.0000 | 0.7250 |
| mux2 | refactor | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| mux2 | refactor_z | 0 | 2 | 0.0% | 0.0000 | 0.7250 |
| mux2 | resub | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| mux2 | resyn | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| mux2 | resyn2 | 0 | 2 | 0.0% | 0.0000 | 0.7250 |
| mux2 | resyn2_like | 0 | 2 | 0.0% | 0.0000 | 0.7250 |
| mux2 | rewrite | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| mux2 | rewrite_z | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| real_hand_written_comparator_4 | balance | 1 | 14 | 7.1% | 0.0714 | 0.9741 |
| real_hand_written_comparator_4 | compress2rs | 1 | 14 | 7.1% | 0.0714 | 0.9741 |
| real_hand_written_comparator_4 | dc2 | 0 | 14 | 0.0% | 0.0000 | 0.9339 |
| real_hand_written_comparator_4 | refactor | 2 | 14 | 14.3% | 0.1429 | 1.0000 |
| real_hand_written_comparator_4 | refactor_z | 0 | 14 | 0.0% | 0.0000 | 0.9741 |
| real_hand_written_comparator_4 | resub | 2 | 14 | 14.3% | 0.1429 | 1.0000 |
| real_hand_written_comparator_4 | resyn | 1 | 14 | 7.1% | 0.0714 | 0.8536 |
| real_hand_written_comparator_4 | resyn2 | 1 | 14 | 7.1% | 0.0714 | 0.9741 |
| real_hand_written_comparator_4 | resyn2_like | 1 | 14 | 7.1% | 0.0714 | 0.9741 |
| real_hand_written_comparator_4 | rewrite | 2 | 14 | 14.3% | 0.1429 | 1.0000 |
| real_hand_written_comparator_4 | rewrite_z | 0 | 14 | 0.0% | 0.0000 | 0.9256 |
| real_hand_written_full_adder | balance | 5 | 9 | 55.6% | 0.5556 | 0.9847 |
| real_hand_written_full_adder | compress2rs | 2 | 5 | 40.0% | 0.4000 | 0.9250 |
| real_hand_written_full_adder | dc2 | 0 | 6 | 0.0% | 0.0000 | 0.8490 |
| real_hand_written_full_adder | refactor | 3 | 8 | 37.5% | 0.3750 | 0.9531 |
| real_hand_written_full_adder | refactor_z | 2 | 8 | 25.0% | 0.2500 | 0.9016 |
| real_hand_written_full_adder | resub | 6 | 9 | 66.7% | 0.6667 | 1.0000 |
| real_hand_written_full_adder | resyn | 5 | 9 | 55.6% | 0.5556 | 0.9847 |
| real_hand_written_full_adder | resyn2 | 3 | 8 | 37.5% | 0.3750 | 0.9016 |
| real_hand_written_full_adder | resyn2_like | 3 | 8 | 37.5% | 0.3750 | 0.9016 |
| real_hand_written_full_adder | rewrite | 6 | 9 | 66.7% | 0.6667 | 1.0000 |
| real_hand_written_full_adder | rewrite_z | 6 | 9 | 66.7% | 0.6667 | 0.9847 |
| real_hand_written_mux_4to1 | balance | 2 | 10 | 20.0% | 0.2000 | 0.9058 |
| real_hand_written_mux_4to1 | compress2rs | 0 | 8 | 0.0% | 0.0000 | 0.6505 |
| real_hand_written_mux_4to1 | dc2 | 0 | 8 | 0.0% | 0.0000 | 0.7497 |
| real_hand_written_mux_4to1 | refactor | 0 | 8 | 0.0% | 0.0000 | 0.7620 |
| real_hand_written_mux_4to1 | refactor_z | 0 | 8 | 0.0% | 0.0000 | 0.6505 |
| real_hand_written_mux_4to1 | resub | 1 | 10 | 10.0% | 0.1000 | 1.0000 |
| real_hand_written_mux_4to1 | resyn | 0 | 8 | 0.0% | 0.0000 | 0.7286 |
| real_hand_written_mux_4to1 | resyn2 | 0 | 8 | 0.0% | 0.0000 | 0.6505 |
| real_hand_written_mux_4to1 | resyn2_like | 0 | 8 | 0.0% | 0.0000 | 0.6505 |
| real_hand_written_mux_4to1 | rewrite | 0 | 8 | 0.0% | 0.0000 | 0.7286 |
| real_hand_written_mux_4to1 | rewrite_z | 0 | 8 | 0.0% | 0.0000 | 0.7286 |
| real_hand_written_parity_8 | balance | 20 | 20 | 100.0% | 1.0000 | 1.0000 |
| real_hand_written_parity_8 | compress2rs | 3 | 20 | 15.0% | 0.1500 | 0.8594 |
| real_hand_written_parity_8 | dc2 | 1 | 20 | 5.0% | 0.0500 | 0.8071 |
| real_hand_written_parity_8 | refactor | 20 | 20 | 100.0% | 1.0000 | 1.0000 |
| real_hand_written_parity_8 | refactor_z | 8 | 20 | 40.0% | 0.4000 | 0.8875 |
| real_hand_written_parity_8 | resub | 20 | 20 | 100.0% | 1.0000 | 1.0000 |
| real_hand_written_parity_8 | resyn | 15 | 20 | 75.0% | 0.7500 | 0.9719 |
| real_hand_written_parity_8 | resyn2 | 3 | 20 | 15.0% | 0.1500 | 0.8594 |
| real_hand_written_parity_8 | resyn2_like | 3 | 20 | 15.0% | 0.1500 | 0.8594 |
| real_hand_written_parity_8 | rewrite | 20 | 20 | 100.0% | 1.0000 | 1.0000 |
| real_hand_written_parity_8 | rewrite_z | 15 | 20 | 75.0% | 0.7500 | 0.9719 |
| real_hand_written_priority_enc_4 | balance | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| real_hand_written_priority_enc_4 | compress2rs | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| real_hand_written_priority_enc_4 | dc2 | 1 | 2 | 50.0% | 0.5000 | 0.7750 |
| real_hand_written_priority_enc_4 | refactor | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| real_hand_written_priority_enc_4 | refactor_z | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| real_hand_written_priority_enc_4 | resub | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| real_hand_written_priority_enc_4 | resyn | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| real_hand_written_priority_enc_4 | resyn2 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| real_hand_written_priority_enc_4 | resyn2_like | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| real_hand_written_priority_enc_4 | rewrite | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| real_hand_written_priority_enc_4 | rewrite_z | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| toy_and_or | balance | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| toy_and_or | compress2rs | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| toy_and_or | dc2 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| toy_and_or | refactor | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| toy_and_or | refactor_z | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| toy_and_or | resub | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| toy_and_or | resyn | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| toy_and_or | resyn2 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| toy_and_or | resyn2_like | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| toy_and_or | rewrite | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| toy_and_or | rewrite_z | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| xor_chain | balance | 8 | 8 | 100.0% | 1.0000 | 1.0000 |
| xor_chain | compress2rs | 0 | 8 | 0.0% | 0.0000 | 0.7097 |
| xor_chain | dc2 | 0 | 8 | 0.0% | 0.0000 | 0.7149 |
| xor_chain | refactor | 8 | 8 | 100.0% | 1.0000 | 1.0000 |
| xor_chain | refactor_z | 5 | 8 | 62.5% | 0.6250 | 0.9297 |
| xor_chain | resub | 8 | 8 | 100.0% | 1.0000 | 1.0000 |
| xor_chain | resyn | 3 | 8 | 37.5% | 0.3750 | 0.7800 |
| xor_chain | resyn2 | 0 | 8 | 0.0% | 0.0000 | 0.7097 |
| xor_chain | resyn2_like | 0 | 8 | 0.0% | 0.0000 | 0.7097 |
| xor_chain | rewrite | 8 | 8 | 100.0% | 1.0000 | 1.0000 |
| xor_chain | rewrite_z | 3 | 8 | 37.5% | 0.3750 | 0.7800 |

## Full results (all K values)

| benchmark | optimization | k | verified_at_k | total_nodes | recovery_at_k | mrr | avg_score_at_1 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| generated_adder_4 | balance | 1 | 31 | 31 | 100.0% | 1.0000 | 1.0000 |
| generated_adder_4 | balance | 2 | 31 | 31 | 100.0% | 1.0000 | 1.0000 |
| generated_adder_4 | balance | 3 | 31 | 31 | 100.0% | 1.0000 | 1.0000 |
| generated_adder_4 | balance | 5 | 31 | 31 | 100.0% | 1.0000 | 1.0000 |
| generated_adder_4 | compress2rs | 1 | 0 | 23 | 0.0% | 0.0000 | 0.8874 |
| generated_adder_4 | compress2rs | 2 | 0 | 23 | 0.0% | 0.0000 | 0.8874 |
| generated_adder_4 | compress2rs | 3 | 0 | 23 | 0.0% | 0.0000 | 0.8874 |
| generated_adder_4 | compress2rs | 5 | 0 | 23 | 0.0% | 0.0000 | 0.8874 |
| generated_adder_4 | dc2 | 1 | 0 | 23 | 0.0% | 0.0000 | 0.8874 |
| generated_adder_4 | dc2 | 2 | 0 | 23 | 0.0% | 0.0000 | 0.8874 |
| generated_adder_4 | dc2 | 3 | 0 | 23 | 0.0% | 0.0000 | 0.8874 |
| generated_adder_4 | dc2 | 5 | 0 | 23 | 0.0% | 0.0000 | 0.8874 |
| generated_adder_4 | refactor | 1 | 0 | 23 | 0.0% | 0.0000 | 0.8874 |
| generated_adder_4 | refactor | 2 | 0 | 23 | 0.0% | 0.0000 | 0.8874 |
| generated_adder_4 | refactor | 3 | 0 | 23 | 0.0% | 0.0000 | 0.8874 |
| generated_adder_4 | refactor | 5 | 0 | 23 | 0.0% | 0.0000 | 0.8874 |
| generated_adder_4 | refactor_z | 1 | 0 | 23 | 0.0% | 0.0000 | 0.8874 |
| generated_adder_4 | refactor_z | 2 | 0 | 23 | 0.0% | 0.0000 | 0.8874 |
| generated_adder_4 | refactor_z | 3 | 0 | 23 | 0.0% | 0.0000 | 0.8874 |
| generated_adder_4 | refactor_z | 5 | 0 | 23 | 0.0% | 0.0000 | 0.8874 |
| generated_adder_4 | resub | 1 | 31 | 31 | 100.0% | 1.0000 | 1.0000 |
| generated_adder_4 | resub | 2 | 31 | 31 | 100.0% | 1.0000 | 1.0000 |
| generated_adder_4 | resub | 3 | 31 | 31 | 100.0% | 1.0000 | 1.0000 |
| generated_adder_4 | resub | 5 | 31 | 31 | 100.0% | 1.0000 | 1.0000 |
| generated_adder_4 | resyn | 1 | 15 | 28 | 53.6% | 0.5357 | 0.9709 |
| generated_adder_4 | resyn | 2 | 15 | 28 | 53.6% | 0.5357 | 0.9709 |
| generated_adder_4 | resyn | 3 | 15 | 28 | 53.6% | 0.5357 | 0.9709 |
| generated_adder_4 | resyn | 5 | 15 | 28 | 53.6% | 0.5357 | 0.9709 |
| generated_adder_4 | resyn2 | 1 | 0 | 23 | 0.0% | 0.0000 | 0.8874 |
| generated_adder_4 | resyn2 | 2 | 0 | 23 | 0.0% | 0.0000 | 0.8874 |
| generated_adder_4 | resyn2 | 3 | 0 | 23 | 0.0% | 0.0000 | 0.8874 |
| generated_adder_4 | resyn2 | 5 | 0 | 23 | 0.0% | 0.0000 | 0.8874 |
| generated_adder_4 | resyn2_like | 1 | 0 | 23 | 0.0% | 0.0000 | 0.8874 |
| generated_adder_4 | resyn2_like | 2 | 0 | 23 | 0.0% | 0.0000 | 0.8874 |
| generated_adder_4 | resyn2_like | 3 | 0 | 23 | 0.0% | 0.0000 | 0.8874 |
| generated_adder_4 | resyn2_like | 5 | 0 | 23 | 0.0% | 0.0000 | 0.8874 |
| generated_adder_4 | rewrite | 1 | 15 | 28 | 53.6% | 0.5357 | 0.9709 |
| generated_adder_4 | rewrite | 2 | 15 | 28 | 53.6% | 0.5357 | 0.9709 |
| generated_adder_4 | rewrite | 3 | 15 | 28 | 53.6% | 0.5357 | 0.9709 |
| generated_adder_4 | rewrite | 5 | 15 | 28 | 53.6% | 0.5357 | 0.9709 |
| generated_adder_4 | rewrite_z | 1 | 15 | 28 | 53.6% | 0.5357 | 0.9709 |
| generated_adder_4 | rewrite_z | 2 | 15 | 28 | 53.6% | 0.5357 | 0.9709 |
| generated_adder_4 | rewrite_z | 3 | 15 | 28 | 53.6% | 0.5357 | 0.9709 |
| generated_adder_4 | rewrite_z | 5 | 15 | 28 | 53.6% | 0.5357 | 0.9709 |
| generated_adder_8 | balance | 1 | 63 | 63 | 100.0% | 1.0000 | 1.0000 |
| generated_adder_8 | balance | 2 | 63 | 63 | 100.0% | 1.0000 | 1.0000 |
| generated_adder_8 | balance | 3 | 63 | 63 | 100.0% | 1.0000 | 1.0000 |
| generated_adder_8 | balance | 5 | 63 | 63 | 100.0% | 1.0000 | 1.0000 |
| generated_adder_8 | compress2rs | 1 | 0 | 47 | 0.0% | 0.0000 | 0.8932 |
| generated_adder_8 | compress2rs | 2 | 0 | 47 | 0.0% | 0.0000 | 0.8932 |
| generated_adder_8 | compress2rs | 3 | 0 | 47 | 0.0% | 0.0000 | 0.8932 |
| generated_adder_8 | compress2rs | 5 | 0 | 47 | 0.0% | 0.0000 | 0.8932 |
| generated_adder_8 | dc2 | 1 | 0 | 47 | 0.0% | 0.0000 | 0.8932 |
| generated_adder_8 | dc2 | 2 | 0 | 47 | 0.0% | 0.0000 | 0.8932 |
| generated_adder_8 | dc2 | 3 | 0 | 47 | 0.0% | 0.0000 | 0.8932 |
| generated_adder_8 | dc2 | 5 | 0 | 47 | 0.0% | 0.0000 | 0.8932 |
| generated_adder_8 | refactor | 1 | 0 | 47 | 0.0% | 0.0000 | 0.8932 |
| generated_adder_8 | refactor | 2 | 0 | 47 | 0.0% | 0.0000 | 0.8932 |
| generated_adder_8 | refactor | 3 | 0 | 47 | 0.0% | 0.0000 | 0.8932 |
| generated_adder_8 | refactor | 5 | 0 | 47 | 0.0% | 0.0000 | 0.8932 |
| generated_adder_8 | refactor_z | 1 | 0 | 47 | 0.0% | 0.0000 | 0.8932 |
| generated_adder_8 | refactor_z | 2 | 0 | 47 | 0.0% | 0.0000 | 0.8932 |
| generated_adder_8 | refactor_z | 3 | 0 | 47 | 0.0% | 0.0000 | 0.8932 |
| generated_adder_8 | refactor_z | 5 | 0 | 47 | 0.0% | 0.0000 | 0.8932 |
| generated_adder_8 | resub | 1 | 63 | 63 | 100.0% | 1.0000 | 1.0000 |
| generated_adder_8 | resub | 2 | 63 | 63 | 100.0% | 1.0000 | 1.0000 |
| generated_adder_8 | resub | 3 | 63 | 63 | 100.0% | 1.0000 | 1.0000 |
| generated_adder_8 | resub | 5 | 63 | 63 | 100.0% | 1.0000 | 1.0000 |
| generated_adder_8 | resyn | 1 | 15 | 56 | 26.8% | 0.2679 | 0.9682 |
| generated_adder_8 | resyn | 2 | 15 | 56 | 26.8% | 0.2679 | 0.9682 |
| generated_adder_8 | resyn | 3 | 15 | 56 | 26.8% | 0.2679 | 0.9682 |
| generated_adder_8 | resyn | 5 | 15 | 56 | 26.8% | 0.2679 | 0.9682 |
| generated_adder_8 | resyn2 | 1 | 0 | 47 | 0.0% | 0.0000 | 0.8932 |
| generated_adder_8 | resyn2 | 2 | 0 | 47 | 0.0% | 0.0000 | 0.8932 |
| generated_adder_8 | resyn2 | 3 | 0 | 47 | 0.0% | 0.0000 | 0.8932 |
| generated_adder_8 | resyn2 | 5 | 0 | 47 | 0.0% | 0.0000 | 0.8932 |
| generated_adder_8 | resyn2_like | 1 | 0 | 47 | 0.0% | 0.0000 | 0.8932 |
| generated_adder_8 | resyn2_like | 2 | 0 | 47 | 0.0% | 0.0000 | 0.8932 |
| generated_adder_8 | resyn2_like | 3 | 0 | 47 | 0.0% | 0.0000 | 0.8932 |
| generated_adder_8 | resyn2_like | 5 | 0 | 47 | 0.0% | 0.0000 | 0.8932 |
| generated_adder_8 | rewrite | 1 | 15 | 56 | 26.8% | 0.2679 | 0.9682 |
| generated_adder_8 | rewrite | 2 | 15 | 56 | 26.8% | 0.2679 | 0.9682 |
| generated_adder_8 | rewrite | 3 | 15 | 56 | 26.8% | 0.2679 | 0.9682 |
| generated_adder_8 | rewrite | 5 | 15 | 56 | 26.8% | 0.2679 | 0.9682 |
| generated_adder_8 | rewrite_z | 1 | 15 | 56 | 26.8% | 0.2679 | 0.9682 |
| generated_adder_8 | rewrite_z | 2 | 15 | 56 | 26.8% | 0.2679 | 0.9682 |
| generated_adder_8 | rewrite_z | 3 | 15 | 56 | 26.8% | 0.2679 | 0.9682 |
| generated_adder_8 | rewrite_z | 5 | 15 | 56 | 26.8% | 0.2679 | 0.9682 |
| generated_multiplier_2 | balance | 1 | 8 | 8 | 100.0% | 1.0000 | 1.0000 |
| generated_multiplier_2 | balance | 2 | 8 | 8 | 100.0% | 1.0000 | 1.0000 |
| generated_multiplier_2 | balance | 3 | 8 | 8 | 100.0% | 1.0000 | 1.0000 |
| generated_multiplier_2 | balance | 5 | 8 | 8 | 100.0% | 1.0000 | 1.0000 |
| generated_multiplier_2 | compress2rs | 1 | 2 | 4 | 50.0% | 0.5000 | 0.9141 |
| generated_multiplier_2 | compress2rs | 2 | 2 | 4 | 50.0% | 0.5000 | 0.9141 |
| generated_multiplier_2 | compress2rs | 3 | 2 | 4 | 50.0% | 0.5000 | 0.9141 |
| generated_multiplier_2 | compress2rs | 5 | 2 | 4 | 50.0% | 0.5000 | 0.9141 |
| generated_multiplier_2 | dc2 | 1 | 2 | 4 | 50.0% | 0.5000 | 0.8539 |
| generated_multiplier_2 | dc2 | 2 | 2 | 4 | 50.0% | 0.5000 | 0.8539 |
| generated_multiplier_2 | dc2 | 3 | 2 | 4 | 50.0% | 0.5000 | 0.8539 |
| generated_multiplier_2 | dc2 | 5 | 2 | 4 | 50.0% | 0.5000 | 0.8539 |
| generated_multiplier_2 | refactor | 1 | 3 | 6 | 50.0% | 0.5000 | 0.8740 |
| generated_multiplier_2 | refactor | 2 | 3 | 6 | 50.0% | 0.5000 | 0.8740 |
| generated_multiplier_2 | refactor | 3 | 3 | 6 | 50.0% | 0.5000 | 0.8740 |
| generated_multiplier_2 | refactor | 5 | 3 | 6 | 50.0% | 0.5000 | 0.8740 |
| generated_multiplier_2 | refactor_z | 1 | 3 | 6 | 50.0% | 0.5000 | 0.8740 |
| generated_multiplier_2 | refactor_z | 2 | 3 | 6 | 50.0% | 0.5000 | 0.8740 |
| generated_multiplier_2 | refactor_z | 3 | 3 | 6 | 50.0% | 0.5000 | 0.8740 |
| generated_multiplier_2 | refactor_z | 5 | 3 | 6 | 50.0% | 0.5000 | 0.8740 |
| generated_multiplier_2 | resub | 1 | 5 | 5 | 100.0% | 1.0000 | 1.0000 |
| generated_multiplier_2 | resub | 2 | 5 | 5 | 100.0% | 1.0000 | 1.0000 |
| generated_multiplier_2 | resub | 3 | 5 | 5 | 100.0% | 1.0000 | 1.0000 |
| generated_multiplier_2 | resub | 5 | 5 | 5 | 100.0% | 1.0000 | 1.0000 |
| generated_multiplier_2 | resyn | 1 | 5 | 5 | 100.0% | 1.0000 | 1.0000 |
| generated_multiplier_2 | resyn | 2 | 5 | 5 | 100.0% | 1.0000 | 1.0000 |
| generated_multiplier_2 | resyn | 3 | 5 | 5 | 100.0% | 1.0000 | 1.0000 |
| generated_multiplier_2 | resyn | 5 | 5 | 5 | 100.0% | 1.0000 | 1.0000 |
| generated_multiplier_2 | resyn2 | 1 | 2 | 4 | 50.0% | 0.5000 | 0.9141 |
| generated_multiplier_2 | resyn2 | 2 | 2 | 4 | 50.0% | 0.5000 | 0.9141 |
| generated_multiplier_2 | resyn2 | 3 | 2 | 4 | 50.0% | 0.5000 | 0.9141 |
| generated_multiplier_2 | resyn2 | 5 | 2 | 4 | 50.0% | 0.5000 | 0.9141 |
| generated_multiplier_2 | resyn2_like | 1 | 2 | 4 | 50.0% | 0.5000 | 0.9141 |
| generated_multiplier_2 | resyn2_like | 2 | 2 | 4 | 50.0% | 0.5000 | 0.9141 |
| generated_multiplier_2 | resyn2_like | 3 | 2 | 4 | 50.0% | 0.5000 | 0.9141 |
| generated_multiplier_2 | resyn2_like | 5 | 2 | 4 | 50.0% | 0.5000 | 0.9141 |
| generated_multiplier_2 | rewrite | 1 | 5 | 5 | 100.0% | 1.0000 | 1.0000 |
| generated_multiplier_2 | rewrite | 2 | 5 | 5 | 100.0% | 1.0000 | 1.0000 |
| generated_multiplier_2 | rewrite | 3 | 5 | 5 | 100.0% | 1.0000 | 1.0000 |
| generated_multiplier_2 | rewrite | 5 | 5 | 5 | 100.0% | 1.0000 | 1.0000 |
| generated_multiplier_2 | rewrite_z | 1 | 5 | 5 | 100.0% | 1.0000 | 1.0000 |
| generated_multiplier_2 | rewrite_z | 2 | 5 | 5 | 100.0% | 1.0000 | 1.0000 |
| generated_multiplier_2 | rewrite_z | 3 | 5 | 5 | 100.0% | 1.0000 | 1.0000 |
| generated_multiplier_2 | rewrite_z | 5 | 5 | 5 | 100.0% | 1.0000 | 1.0000 |
| generated_multiplier_4 | balance | 1 | 96 | 112 | 85.7% | 0.8571 | 0.9970 |
| generated_multiplier_4 | balance | 2 | 96 | 112 | 85.7% | 0.8571 | 0.9970 |
| generated_multiplier_4 | balance | 3 | 96 | 112 | 85.7% | 0.8571 | 0.9970 |
| generated_multiplier_4 | balance | 5 | 96 | 112 | 85.7% | 0.8571 | 0.9970 |
| generated_multiplier_4 | compress2rs | 1 | 3 | 75 | 4.0% | 0.0400 | 0.9360 |
| generated_multiplier_4 | compress2rs | 2 | 3 | 75 | 4.0% | 0.0400 | 0.9360 |
| generated_multiplier_4 | compress2rs | 3 | 3 | 75 | 4.0% | 0.0400 | 0.9360 |
| generated_multiplier_4 | compress2rs | 5 | 3 | 75 | 4.0% | 0.0400 | 0.9360 |
| generated_multiplier_4 | dc2 | 1 | 3 | 82 | 3.7% | 0.0366 | 0.9330 |
| generated_multiplier_4 | dc2 | 2 | 3 | 82 | 3.7% | 0.0366 | 0.9330 |
| generated_multiplier_4 | dc2 | 3 | 3 | 82 | 3.7% | 0.0366 | 0.9330 |
| generated_multiplier_4 | dc2 | 5 | 3 | 82 | 3.7% | 0.0366 | 0.9330 |
| generated_multiplier_4 | refactor | 1 | 8 | 100 | 8.0% | 0.0800 | 0.9789 |
| generated_multiplier_4 | refactor | 2 | 8 | 100 | 8.0% | 0.0800 | 0.9789 |
| generated_multiplier_4 | refactor | 3 | 8 | 100 | 8.0% | 0.0800 | 0.9789 |
| generated_multiplier_4 | refactor | 5 | 8 | 100 | 8.0% | 0.0800 | 0.9789 |
| generated_multiplier_4 | refactor_z | 1 | 4 | 100 | 4.0% | 0.0400 | 0.9500 |
| generated_multiplier_4 | refactor_z | 2 | 4 | 100 | 4.0% | 0.0400 | 0.9500 |
| generated_multiplier_4 | refactor_z | 3 | 4 | 100 | 4.0% | 0.0400 | 0.9500 |
| generated_multiplier_4 | refactor_z | 5 | 4 | 100 | 4.0% | 0.0400 | 0.9500 |
| generated_multiplier_4 | resub | 1 | 18 | 101 | 17.8% | 0.1782 | 0.9927 |
| generated_multiplier_4 | resub | 2 | 18 | 101 | 17.8% | 0.1782 | 0.9927 |
| generated_multiplier_4 | resub | 3 | 18 | 101 | 17.8% | 0.1782 | 0.9927 |
| generated_multiplier_4 | resub | 5 | 18 | 101 | 17.8% | 0.1782 | 0.9927 |
| generated_multiplier_4 | resyn | 1 | 5 | 83 | 6.0% | 0.0602 | 0.9388 |
| generated_multiplier_4 | resyn | 2 | 5 | 83 | 6.0% | 0.0602 | 0.9388 |
| generated_multiplier_4 | resyn | 3 | 5 | 83 | 6.0% | 0.0602 | 0.9388 |
| generated_multiplier_4 | resyn | 5 | 5 | 83 | 6.0% | 0.0602 | 0.9388 |
| generated_multiplier_4 | resyn2 | 1 | 3 | 82 | 3.7% | 0.0366 | 0.9339 |
| generated_multiplier_4 | resyn2 | 2 | 3 | 82 | 3.7% | 0.0366 | 0.9339 |
| generated_multiplier_4 | resyn2 | 3 | 3 | 82 | 3.7% | 0.0366 | 0.9339 |
| generated_multiplier_4 | resyn2 | 5 | 3 | 82 | 3.7% | 0.0366 | 0.9339 |
| generated_multiplier_4 | resyn2_like | 1 | 3 | 82 | 3.7% | 0.0366 | 0.9339 |
| generated_multiplier_4 | resyn2_like | 2 | 3 | 82 | 3.7% | 0.0366 | 0.9339 |
| generated_multiplier_4 | resyn2_like | 3 | 3 | 82 | 3.7% | 0.0366 | 0.9339 |
| generated_multiplier_4 | resyn2_like | 5 | 3 | 82 | 3.7% | 0.0366 | 0.9339 |
| generated_multiplier_4 | rewrite | 1 | 15 | 85 | 17.6% | 0.1765 | 0.9730 |
| generated_multiplier_4 | rewrite | 2 | 15 | 85 | 17.6% | 0.1765 | 0.9730 |
| generated_multiplier_4 | rewrite | 3 | 15 | 85 | 17.6% | 0.1765 | 0.9730 |
| generated_multiplier_4 | rewrite | 5 | 15 | 85 | 17.6% | 0.1765 | 0.9730 |
| generated_multiplier_4 | rewrite_z | 1 | 5 | 91 | 5.5% | 0.0549 | 0.9337 |
| generated_multiplier_4 | rewrite_z | 2 | 5 | 91 | 5.5% | 0.0549 | 0.9337 |
| generated_multiplier_4 | rewrite_z | 3 | 5 | 91 | 5.5% | 0.0549 | 0.9337 |
| generated_multiplier_4 | rewrite_z | 5 | 5 | 91 | 5.5% | 0.0549 | 0.9337 |
| generated_mux_tree_16 | balance | 1 | 1 | 44 | 2.3% | 0.0227 | 1.0000 |
| generated_mux_tree_16 | balance | 2 | 1 | 44 | 2.3% | 0.0227 | 1.0000 |
| generated_mux_tree_16 | balance | 3 | 1 | 44 | 2.3% | 0.0227 | 1.0000 |
| generated_mux_tree_16 | balance | 5 | 1 | 44 | 2.3% | 0.0227 | 1.0000 |
| generated_mux_tree_16 | compress2rs | 1 | 0 | 44 | 0.0% | 0.0000 | 0.7891 |
| generated_mux_tree_16 | compress2rs | 2 | 0 | 44 | 0.0% | 0.0000 | 0.7891 |
| generated_mux_tree_16 | compress2rs | 3 | 0 | 44 | 0.0% | 0.0000 | 0.7891 |
| generated_mux_tree_16 | compress2rs | 5 | 0 | 44 | 0.0% | 0.0000 | 0.7891 |
| generated_mux_tree_16 | dc2 | 1 | 0 | 44 | 0.0% | 0.0000 | 0.6463 |
| generated_mux_tree_16 | dc2 | 2 | 0 | 44 | 0.0% | 0.0000 | 0.6463 |
| generated_mux_tree_16 | dc2 | 3 | 0 | 44 | 0.0% | 0.0000 | 0.6463 |
| generated_mux_tree_16 | dc2 | 5 | 0 | 44 | 0.0% | 0.0000 | 0.6463 |
| generated_mux_tree_16 | refactor | 1 | 1 | 44 | 2.3% | 0.0227 | 1.0000 |
| generated_mux_tree_16 | refactor | 2 | 1 | 44 | 2.3% | 0.0227 | 1.0000 |
| generated_mux_tree_16 | refactor | 3 | 1 | 44 | 2.3% | 0.0227 | 1.0000 |
| generated_mux_tree_16 | refactor | 5 | 1 | 44 | 2.3% | 0.0227 | 1.0000 |
| generated_mux_tree_16 | refactor_z | 1 | 2 | 44 | 4.5% | 0.0455 | 0.9286 |
| generated_mux_tree_16 | refactor_z | 2 | 2 | 44 | 4.5% | 0.0455 | 0.9286 |
| generated_mux_tree_16 | refactor_z | 3 | 2 | 44 | 4.5% | 0.0455 | 0.9286 |
| generated_mux_tree_16 | refactor_z | 5 | 2 | 44 | 4.5% | 0.0455 | 0.9286 |
| generated_mux_tree_16 | resub | 1 | 1 | 44 | 2.3% | 0.0227 | 1.0000 |
| generated_mux_tree_16 | resub | 2 | 1 | 44 | 2.3% | 0.0227 | 1.0000 |
| generated_mux_tree_16 | resub | 3 | 1 | 44 | 2.3% | 0.0227 | 1.0000 |
| generated_mux_tree_16 | resub | 5 | 1 | 44 | 2.3% | 0.0227 | 1.0000 |
| generated_mux_tree_16 | resyn | 1 | 1 | 44 | 2.3% | 0.0227 | 0.7982 |
| generated_mux_tree_16 | resyn | 2 | 1 | 44 | 2.3% | 0.0227 | 0.7982 |
| generated_mux_tree_16 | resyn | 3 | 1 | 44 | 2.3% | 0.0227 | 0.7982 |
| generated_mux_tree_16 | resyn | 5 | 1 | 44 | 2.3% | 0.0227 | 0.7982 |
| generated_mux_tree_16 | resyn2 | 1 | 0 | 44 | 0.0% | 0.0000 | 0.7891 |
| generated_mux_tree_16 | resyn2 | 2 | 0 | 44 | 0.0% | 0.0000 | 0.7891 |
| generated_mux_tree_16 | resyn2 | 3 | 0 | 44 | 0.0% | 0.0000 | 0.7891 |
| generated_mux_tree_16 | resyn2 | 5 | 0 | 44 | 0.0% | 0.0000 | 0.7891 |
| generated_mux_tree_16 | resyn2_like | 1 | 0 | 44 | 0.0% | 0.0000 | 0.7891 |
| generated_mux_tree_16 | resyn2_like | 2 | 0 | 44 | 0.0% | 0.0000 | 0.7891 |
| generated_mux_tree_16 | resyn2_like | 3 | 0 | 44 | 0.0% | 0.0000 | 0.7891 |
| generated_mux_tree_16 | resyn2_like | 5 | 0 | 44 | 0.0% | 0.0000 | 0.7891 |
| generated_mux_tree_16 | rewrite | 1 | 1 | 44 | 2.3% | 0.0227 | 1.0000 |
| generated_mux_tree_16 | rewrite | 2 | 1 | 44 | 2.3% | 0.0227 | 1.0000 |
| generated_mux_tree_16 | rewrite | 3 | 1 | 44 | 2.3% | 0.0227 | 1.0000 |
| generated_mux_tree_16 | rewrite | 5 | 1 | 44 | 2.3% | 0.0227 | 1.0000 |
| generated_mux_tree_16 | rewrite_z | 1 | 1 | 44 | 2.3% | 0.0227 | 0.8301 |
| generated_mux_tree_16 | rewrite_z | 2 | 1 | 44 | 2.3% | 0.0227 | 0.8301 |
| generated_mux_tree_16 | rewrite_z | 3 | 1 | 44 | 2.3% | 0.0227 | 0.8301 |
| generated_mux_tree_16 | rewrite_z | 5 | 1 | 44 | 2.3% | 0.0227 | 0.8301 |
| generated_mux_tree_4 | balance | 1 | 1 | 8 | 12.5% | 0.1250 | 1.0000 |
| generated_mux_tree_4 | balance | 2 | 1 | 8 | 12.5% | 0.1250 | 1.0000 |
| generated_mux_tree_4 | balance | 3 | 1 | 8 | 12.5% | 0.1250 | 1.0000 |
| generated_mux_tree_4 | balance | 5 | 1 | 8 | 12.5% | 0.1250 | 1.0000 |
| generated_mux_tree_4 | compress2rs | 1 | 0 | 8 | 0.0% | 0.0000 | 0.7250 |
| generated_mux_tree_4 | compress2rs | 2 | 0 | 8 | 0.0% | 0.0000 | 0.7250 |
| generated_mux_tree_4 | compress2rs | 3 | 0 | 8 | 0.0% | 0.0000 | 0.7250 |
| generated_mux_tree_4 | compress2rs | 5 | 0 | 8 | 0.0% | 0.0000 | 0.7250 |
| generated_mux_tree_4 | dc2 | 1 | 1 | 8 | 12.5% | 0.1250 | 0.8883 |
| generated_mux_tree_4 | dc2 | 2 | 1 | 8 | 12.5% | 0.1250 | 0.8883 |
| generated_mux_tree_4 | dc2 | 3 | 1 | 8 | 12.5% | 0.1250 | 0.8883 |
| generated_mux_tree_4 | dc2 | 5 | 1 | 8 | 12.5% | 0.1250 | 0.8883 |
| generated_mux_tree_4 | refactor | 1 | 1 | 8 | 12.5% | 0.1250 | 1.0000 |
| generated_mux_tree_4 | refactor | 2 | 1 | 8 | 12.5% | 0.1250 | 1.0000 |
| generated_mux_tree_4 | refactor | 3 | 1 | 8 | 12.5% | 0.1250 | 1.0000 |
| generated_mux_tree_4 | refactor | 5 | 1 | 8 | 12.5% | 0.1250 | 1.0000 |
| generated_mux_tree_4 | refactor_z | 1 | 0 | 8 | 0.0% | 0.0000 | 0.7250 |
| generated_mux_tree_4 | refactor_z | 2 | 0 | 8 | 0.0% | 0.0000 | 0.7250 |
| generated_mux_tree_4 | refactor_z | 3 | 0 | 8 | 0.0% | 0.0000 | 0.7250 |
| generated_mux_tree_4 | refactor_z | 5 | 0 | 8 | 0.0% | 0.0000 | 0.7250 |
| generated_mux_tree_4 | resub | 1 | 1 | 8 | 12.5% | 0.1250 | 1.0000 |
| generated_mux_tree_4 | resub | 2 | 1 | 8 | 12.5% | 0.1250 | 1.0000 |
| generated_mux_tree_4 | resub | 3 | 1 | 8 | 12.5% | 0.1250 | 1.0000 |
| generated_mux_tree_4 | resub | 5 | 1 | 8 | 12.5% | 0.1250 | 1.0000 |
| generated_mux_tree_4 | resyn | 1 | 1 | 8 | 12.5% | 0.1250 | 0.8109 |
| generated_mux_tree_4 | resyn | 2 | 1 | 8 | 12.5% | 0.1250 | 0.8109 |
| generated_mux_tree_4 | resyn | 3 | 1 | 8 | 12.5% | 0.1250 | 0.8109 |
| generated_mux_tree_4 | resyn | 5 | 1 | 8 | 12.5% | 0.1250 | 0.8109 |
| generated_mux_tree_4 | resyn2 | 1 | 0 | 8 | 0.0% | 0.0000 | 0.7250 |
| generated_mux_tree_4 | resyn2 | 2 | 0 | 8 | 0.0% | 0.0000 | 0.7250 |
| generated_mux_tree_4 | resyn2 | 3 | 0 | 8 | 0.0% | 0.0000 | 0.7250 |
| generated_mux_tree_4 | resyn2 | 5 | 0 | 8 | 0.0% | 0.0000 | 0.7250 |
| generated_mux_tree_4 | resyn2_like | 1 | 0 | 8 | 0.0% | 0.0000 | 0.7250 |
| generated_mux_tree_4 | resyn2_like | 2 | 0 | 8 | 0.0% | 0.0000 | 0.7250 |
| generated_mux_tree_4 | resyn2_like | 3 | 0 | 8 | 0.0% | 0.0000 | 0.7250 |
| generated_mux_tree_4 | resyn2_like | 5 | 0 | 8 | 0.0% | 0.0000 | 0.7250 |
| generated_mux_tree_4 | rewrite | 1 | 1 | 8 | 12.5% | 0.1250 | 1.0000 |
| generated_mux_tree_4 | rewrite | 2 | 1 | 8 | 12.5% | 0.1250 | 1.0000 |
| generated_mux_tree_4 | rewrite | 3 | 1 | 8 | 12.5% | 0.1250 | 1.0000 |
| generated_mux_tree_4 | rewrite | 5 | 1 | 8 | 12.5% | 0.1250 | 1.0000 |
| generated_mux_tree_4 | rewrite_z | 1 | 1 | 8 | 12.5% | 0.1250 | 0.8109 |
| generated_mux_tree_4 | rewrite_z | 2 | 1 | 8 | 12.5% | 0.1250 | 0.8109 |
| generated_mux_tree_4 | rewrite_z | 3 | 1 | 8 | 12.5% | 0.1250 | 0.8109 |
| generated_mux_tree_4 | rewrite_z | 5 | 1 | 8 | 12.5% | 0.1250 | 0.8109 |
| generated_mux_tree_8 | balance | 1 | 1 | 20 | 5.0% | 0.0500 | 1.0000 |
| generated_mux_tree_8 | balance | 2 | 1 | 20 | 5.0% | 0.0500 | 1.0000 |
| generated_mux_tree_8 | balance | 3 | 1 | 20 | 5.0% | 0.0500 | 1.0000 |
| generated_mux_tree_8 | balance | 5 | 1 | 20 | 5.0% | 0.0500 | 1.0000 |
| generated_mux_tree_8 | compress2rs | 1 | 0 | 20 | 0.0% | 0.0000 | 0.8287 |
| generated_mux_tree_8 | compress2rs | 2 | 0 | 20 | 0.0% | 0.0000 | 0.8287 |
| generated_mux_tree_8 | compress2rs | 3 | 0 | 20 | 0.0% | 0.0000 | 0.8287 |
| generated_mux_tree_8 | compress2rs | 5 | 0 | 20 | 0.0% | 0.0000 | 0.8287 |
| generated_mux_tree_8 | dc2 | 1 | 0 | 20 | 0.0% | 0.0000 | 0.5815 |
| generated_mux_tree_8 | dc2 | 2 | 0 | 20 | 0.0% | 0.0000 | 0.5815 |
| generated_mux_tree_8 | dc2 | 3 | 0 | 20 | 0.0% | 0.0000 | 0.5815 |
| generated_mux_tree_8 | dc2 | 5 | 0 | 20 | 0.0% | 0.0000 | 0.5815 |
| generated_mux_tree_8 | refactor | 1 | 1 | 20 | 5.0% | 0.0500 | 1.0000 |
| generated_mux_tree_8 | refactor | 2 | 1 | 20 | 5.0% | 0.0500 | 1.0000 |
| generated_mux_tree_8 | refactor | 3 | 1 | 20 | 5.0% | 0.0500 | 1.0000 |
| generated_mux_tree_8 | refactor | 5 | 1 | 20 | 5.0% | 0.0500 | 1.0000 |
| generated_mux_tree_8 | refactor_z | 1 | 0 | 20 | 0.0% | 0.0000 | 0.8975 |
| generated_mux_tree_8 | refactor_z | 2 | 0 | 20 | 0.0% | 0.0000 | 0.8975 |
| generated_mux_tree_8 | refactor_z | 3 | 0 | 20 | 0.0% | 0.0000 | 0.8975 |
| generated_mux_tree_8 | refactor_z | 5 | 0 | 20 | 0.0% | 0.0000 | 0.8975 |
| generated_mux_tree_8 | resub | 1 | 1 | 20 | 5.0% | 0.0500 | 1.0000 |
| generated_mux_tree_8 | resub | 2 | 1 | 20 | 5.0% | 0.0500 | 1.0000 |
| generated_mux_tree_8 | resub | 3 | 1 | 20 | 5.0% | 0.0500 | 1.0000 |
| generated_mux_tree_8 | resub | 5 | 1 | 20 | 5.0% | 0.0500 | 1.0000 |
| generated_mux_tree_8 | resyn | 1 | 1 | 20 | 5.0% | 0.0500 | 0.8488 |
| generated_mux_tree_8 | resyn | 2 | 1 | 20 | 5.0% | 0.0500 | 0.8488 |
| generated_mux_tree_8 | resyn | 3 | 1 | 20 | 5.0% | 0.0500 | 0.8488 |
| generated_mux_tree_8 | resyn | 5 | 1 | 20 | 5.0% | 0.0500 | 0.8488 |
| generated_mux_tree_8 | resyn2 | 1 | 0 | 20 | 0.0% | 0.0000 | 0.8287 |
| generated_mux_tree_8 | resyn2 | 2 | 0 | 20 | 0.0% | 0.0000 | 0.8287 |
| generated_mux_tree_8 | resyn2 | 3 | 0 | 20 | 0.0% | 0.0000 | 0.8287 |
| generated_mux_tree_8 | resyn2 | 5 | 0 | 20 | 0.0% | 0.0000 | 0.8287 |
| generated_mux_tree_8 | resyn2_like | 1 | 0 | 20 | 0.0% | 0.0000 | 0.8287 |
| generated_mux_tree_8 | resyn2_like | 2 | 0 | 20 | 0.0% | 0.0000 | 0.8287 |
| generated_mux_tree_8 | resyn2_like | 3 | 0 | 20 | 0.0% | 0.0000 | 0.8287 |
| generated_mux_tree_8 | resyn2_like | 5 | 0 | 20 | 0.0% | 0.0000 | 0.8287 |
| generated_mux_tree_8 | rewrite | 1 | 1 | 20 | 5.0% | 0.0500 | 1.0000 |
| generated_mux_tree_8 | rewrite | 2 | 1 | 20 | 5.0% | 0.0500 | 1.0000 |
| generated_mux_tree_8 | rewrite | 3 | 1 | 20 | 5.0% | 0.0500 | 1.0000 |
| generated_mux_tree_8 | rewrite | 5 | 1 | 20 | 5.0% | 0.0500 | 1.0000 |
| generated_mux_tree_8 | rewrite_z | 1 | 1 | 20 | 5.0% | 0.0500 | 0.8488 |
| generated_mux_tree_8 | rewrite_z | 2 | 1 | 20 | 5.0% | 0.0500 | 0.8488 |
| generated_mux_tree_8 | rewrite_z | 3 | 1 | 20 | 5.0% | 0.0500 | 0.8488 |
| generated_mux_tree_8 | rewrite_z | 5 | 1 | 20 | 5.0% | 0.0500 | 0.8488 |
| generated_random_medium | balance | 1 | 17 | 17 | 100.0% | 1.0000 | 1.0000 |
| generated_random_medium | balance | 2 | 17 | 17 | 100.0% | 1.0000 | 1.0000 |
| generated_random_medium | balance | 3 | 17 | 17 | 100.0% | 1.0000 | 1.0000 |
| generated_random_medium | balance | 5 | 17 | 17 | 100.0% | 1.0000 | 1.0000 |
| generated_random_medium | compress2rs | 1 | 5 | 17 | 29.4% | 0.2941 | 0.8466 |
| generated_random_medium | compress2rs | 2 | 5 | 17 | 29.4% | 0.2941 | 0.8466 |
| generated_random_medium | compress2rs | 3 | 5 | 17 | 29.4% | 0.2941 | 0.8466 |
| generated_random_medium | compress2rs | 5 | 5 | 17 | 29.4% | 0.2941 | 0.8466 |
| generated_random_medium | dc2 | 1 | 3 | 17 | 17.6% | 0.1765 | 0.8560 |
| generated_random_medium | dc2 | 2 | 3 | 17 | 17.6% | 0.1765 | 0.8560 |
| generated_random_medium | dc2 | 3 | 3 | 17 | 17.6% | 0.1765 | 0.8560 |
| generated_random_medium | dc2 | 5 | 3 | 17 | 17.6% | 0.1765 | 0.8560 |
| generated_random_medium | refactor | 1 | 17 | 17 | 100.0% | 1.0000 | 1.0000 |
| generated_random_medium | refactor | 2 | 17 | 17 | 100.0% | 1.0000 | 1.0000 |
| generated_random_medium | refactor | 3 | 17 | 17 | 100.0% | 1.0000 | 1.0000 |
| generated_random_medium | refactor | 5 | 17 | 17 | 100.0% | 1.0000 | 1.0000 |
| generated_random_medium | refactor_z | 1 | 8 | 17 | 47.1% | 0.4706 | 0.9216 |
| generated_random_medium | refactor_z | 2 | 8 | 17 | 47.1% | 0.4706 | 0.9216 |
| generated_random_medium | refactor_z | 3 | 8 | 17 | 47.1% | 0.4706 | 0.9216 |
| generated_random_medium | refactor_z | 5 | 8 | 17 | 47.1% | 0.4706 | 0.9216 |
| generated_random_medium | resub | 1 | 17 | 17 | 100.0% | 1.0000 | 1.0000 |
| generated_random_medium | resub | 2 | 17 | 17 | 100.0% | 1.0000 | 1.0000 |
| generated_random_medium | resub | 3 | 17 | 17 | 100.0% | 1.0000 | 1.0000 |
| generated_random_medium | resub | 5 | 17 | 17 | 100.0% | 1.0000 | 1.0000 |
| generated_random_medium | resyn | 1 | 5 | 17 | 29.4% | 0.2941 | 0.8845 |
| generated_random_medium | resyn | 2 | 5 | 17 | 29.4% | 0.2941 | 0.8845 |
| generated_random_medium | resyn | 3 | 5 | 17 | 29.4% | 0.2941 | 0.8845 |
| generated_random_medium | resyn | 5 | 5 | 17 | 29.4% | 0.2941 | 0.8845 |
| generated_random_medium | resyn2 | 1 | 5 | 17 | 29.4% | 0.2941 | 0.8466 |
| generated_random_medium | resyn2 | 2 | 5 | 17 | 29.4% | 0.2941 | 0.8466 |
| generated_random_medium | resyn2 | 3 | 5 | 17 | 29.4% | 0.2941 | 0.8466 |
| generated_random_medium | resyn2 | 5 | 5 | 17 | 29.4% | 0.2941 | 0.8466 |
| generated_random_medium | resyn2_like | 1 | 5 | 17 | 29.4% | 0.2941 | 0.8466 |
| generated_random_medium | resyn2_like | 2 | 5 | 17 | 29.4% | 0.2941 | 0.8466 |
| generated_random_medium | resyn2_like | 3 | 5 | 17 | 29.4% | 0.2941 | 0.8466 |
| generated_random_medium | resyn2_like | 5 | 5 | 17 | 29.4% | 0.2941 | 0.8466 |
| generated_random_medium | rewrite | 1 | 17 | 17 | 100.0% | 1.0000 | 1.0000 |
| generated_random_medium | rewrite | 2 | 17 | 17 | 100.0% | 1.0000 | 1.0000 |
| generated_random_medium | rewrite | 3 | 17 | 17 | 100.0% | 1.0000 | 1.0000 |
| generated_random_medium | rewrite | 5 | 17 | 17 | 100.0% | 1.0000 | 1.0000 |
| generated_random_medium | rewrite_z | 1 | 9 | 17 | 52.9% | 0.5294 | 0.8865 |
| generated_random_medium | rewrite_z | 2 | 9 | 17 | 52.9% | 0.5294 | 0.8865 |
| generated_random_medium | rewrite_z | 3 | 9 | 17 | 52.9% | 0.5294 | 0.8865 |
| generated_random_medium | rewrite_z | 5 | 9 | 17 | 52.9% | 0.5294 | 0.8865 |
| generated_xor_chain_16 | balance | 1 | 44 | 44 | 100.0% | 1.0000 | 1.0000 |
| generated_xor_chain_16 | balance | 2 | 44 | 44 | 100.0% | 1.0000 | 1.0000 |
| generated_xor_chain_16 | balance | 3 | 44 | 44 | 100.0% | 1.0000 | 1.0000 |
| generated_xor_chain_16 | balance | 5 | 44 | 44 | 100.0% | 1.0000 | 1.0000 |
| generated_xor_chain_16 | compress2rs | 1 | 0 | 44 | 0.0% | 0.0000 | 0.5941 |
| generated_xor_chain_16 | compress2rs | 2 | 0 | 44 | 0.0% | 0.0000 | 0.5941 |
| generated_xor_chain_16 | compress2rs | 3 | 0 | 44 | 0.0% | 0.0000 | 0.5941 |
| generated_xor_chain_16 | compress2rs | 5 | 0 | 44 | 0.0% | 0.0000 | 0.5941 |
| generated_xor_chain_16 | dc2 | 1 | 0 | 44 | 0.0% | 0.0000 | 0.5205 |
| generated_xor_chain_16 | dc2 | 2 | 0 | 44 | 0.0% | 0.0000 | 0.5205 |
| generated_xor_chain_16 | dc2 | 3 | 0 | 44 | 0.0% | 0.0000 | 0.5205 |
| generated_xor_chain_16 | dc2 | 5 | 0 | 44 | 0.0% | 0.0000 | 0.5205 |
| generated_xor_chain_16 | refactor | 1 | 44 | 44 | 100.0% | 1.0000 | 1.0000 |
| generated_xor_chain_16 | refactor | 2 | 44 | 44 | 100.0% | 1.0000 | 1.0000 |
| generated_xor_chain_16 | refactor | 3 | 44 | 44 | 100.0% | 1.0000 | 1.0000 |
| generated_xor_chain_16 | refactor | 5 | 44 | 44 | 100.0% | 1.0000 | 1.0000 |
| generated_xor_chain_16 | refactor_z | 1 | 41 | 44 | 93.2% | 0.9318 | 0.9874 |
| generated_xor_chain_16 | refactor_z | 2 | 41 | 44 | 93.2% | 0.9318 | 0.9874 |
| generated_xor_chain_16 | refactor_z | 3 | 41 | 44 | 93.2% | 0.9318 | 0.9874 |
| generated_xor_chain_16 | refactor_z | 5 | 41 | 44 | 93.2% | 0.9318 | 0.9874 |
| generated_xor_chain_16 | resub | 1 | 44 | 44 | 100.0% | 1.0000 | 1.0000 |
| generated_xor_chain_16 | resub | 2 | 44 | 44 | 100.0% | 1.0000 | 1.0000 |
| generated_xor_chain_16 | resub | 3 | 44 | 44 | 100.0% | 1.0000 | 1.0000 |
| generated_xor_chain_16 | resub | 5 | 44 | 44 | 100.0% | 1.0000 | 1.0000 |
| generated_xor_chain_16 | resyn | 1 | 3 | 44 | 6.8% | 0.0682 | 0.6067 |
| generated_xor_chain_16 | resyn | 2 | 3 | 44 | 6.8% | 0.0682 | 0.6067 |
| generated_xor_chain_16 | resyn | 3 | 3 | 44 | 6.8% | 0.0682 | 0.6067 |
| generated_xor_chain_16 | resyn | 5 | 3 | 44 | 6.8% | 0.0682 | 0.6067 |
| generated_xor_chain_16 | resyn2 | 1 | 0 | 44 | 0.0% | 0.0000 | 0.5941 |
| generated_xor_chain_16 | resyn2 | 2 | 0 | 44 | 0.0% | 0.0000 | 0.5941 |
| generated_xor_chain_16 | resyn2 | 3 | 0 | 44 | 0.0% | 0.0000 | 0.5941 |
| generated_xor_chain_16 | resyn2 | 5 | 0 | 44 | 0.0% | 0.0000 | 0.5941 |
| generated_xor_chain_16 | resyn2_like | 1 | 0 | 44 | 0.0% | 0.0000 | 0.5941 |
| generated_xor_chain_16 | resyn2_like | 2 | 0 | 44 | 0.0% | 0.0000 | 0.5941 |
| generated_xor_chain_16 | resyn2_like | 3 | 0 | 44 | 0.0% | 0.0000 | 0.5941 |
| generated_xor_chain_16 | resyn2_like | 5 | 0 | 44 | 0.0% | 0.0000 | 0.5941 |
| generated_xor_chain_16 | rewrite | 1 | 44 | 44 | 100.0% | 1.0000 | 1.0000 |
| generated_xor_chain_16 | rewrite | 2 | 44 | 44 | 100.0% | 1.0000 | 1.0000 |
| generated_xor_chain_16 | rewrite | 3 | 44 | 44 | 100.0% | 1.0000 | 1.0000 |
| generated_xor_chain_16 | rewrite | 5 | 44 | 44 | 100.0% | 1.0000 | 1.0000 |
| generated_xor_chain_16 | rewrite_z | 1 | 3 | 44 | 6.8% | 0.0682 | 0.6067 |
| generated_xor_chain_16 | rewrite_z | 2 | 3 | 44 | 6.8% | 0.0682 | 0.6067 |
| generated_xor_chain_16 | rewrite_z | 3 | 3 | 44 | 6.8% | 0.0682 | 0.6067 |
| generated_xor_chain_16 | rewrite_z | 5 | 3 | 44 | 6.8% | 0.0682 | 0.6067 |
| generated_xor_chain_32 | balance | 1 | 92 | 92 | 100.0% | 1.0000 | 1.0000 |
| generated_xor_chain_32 | balance | 2 | 92 | 92 | 100.0% | 1.0000 | 1.0000 |
| generated_xor_chain_32 | balance | 3 | 92 | 92 | 100.0% | 1.0000 | 1.0000 |
| generated_xor_chain_32 | balance | 5 | 92 | 92 | 100.0% | 1.0000 | 1.0000 |
| generated_xor_chain_32 | compress2rs | 1 | 0 | 92 | 0.0% | 0.0000 | 0.5763 |
| generated_xor_chain_32 | compress2rs | 2 | 0 | 92 | 0.0% | 0.0000 | 0.5763 |
| generated_xor_chain_32 | compress2rs | 3 | 0 | 92 | 0.0% | 0.0000 | 0.5763 |
| generated_xor_chain_32 | compress2rs | 5 | 0 | 92 | 0.0% | 0.0000 | 0.5763 |
| generated_xor_chain_32 | dc2 | 1 | 0 | 92 | 0.0% | 0.0000 | 0.4750 |
| generated_xor_chain_32 | dc2 | 2 | 0 | 92 | 0.0% | 0.0000 | 0.4750 |
| generated_xor_chain_32 | dc2 | 3 | 0 | 92 | 0.0% | 0.0000 | 0.4750 |
| generated_xor_chain_32 | dc2 | 5 | 0 | 92 | 0.0% | 0.0000 | 0.4750 |
| generated_xor_chain_32 | refactor | 1 | 92 | 92 | 100.0% | 1.0000 | 1.0000 |
| generated_xor_chain_32 | refactor | 2 | 92 | 92 | 100.0% | 1.0000 | 1.0000 |
| generated_xor_chain_32 | refactor | 3 | 92 | 92 | 100.0% | 1.0000 | 1.0000 |
| generated_xor_chain_32 | refactor | 5 | 92 | 92 | 100.0% | 1.0000 | 1.0000 |
| generated_xor_chain_32 | refactor_z | 1 | 89 | 92 | 96.7% | 0.9674 | 0.9940 |
| generated_xor_chain_32 | refactor_z | 2 | 89 | 92 | 96.7% | 0.9674 | 0.9940 |
| generated_xor_chain_32 | refactor_z | 3 | 89 | 92 | 96.7% | 0.9674 | 0.9940 |
| generated_xor_chain_32 | refactor_z | 5 | 89 | 92 | 96.7% | 0.9674 | 0.9940 |
| generated_xor_chain_32 | resub | 1 | 92 | 92 | 100.0% | 1.0000 | 1.0000 |
| generated_xor_chain_32 | resub | 2 | 92 | 92 | 100.0% | 1.0000 | 1.0000 |
| generated_xor_chain_32 | resub | 3 | 92 | 92 | 100.0% | 1.0000 | 1.0000 |
| generated_xor_chain_32 | resub | 5 | 92 | 92 | 100.0% | 1.0000 | 1.0000 |
| generated_xor_chain_32 | resyn | 1 | 3 | 92 | 3.3% | 0.0326 | 0.5823 |
| generated_xor_chain_32 | resyn | 2 | 3 | 92 | 3.3% | 0.0326 | 0.5823 |
| generated_xor_chain_32 | resyn | 3 | 3 | 92 | 3.3% | 0.0326 | 0.5823 |
| generated_xor_chain_32 | resyn | 5 | 3 | 92 | 3.3% | 0.0326 | 0.5823 |
| generated_xor_chain_32 | resyn2 | 1 | 0 | 92 | 0.0% | 0.0000 | 0.5763 |
| generated_xor_chain_32 | resyn2 | 2 | 0 | 92 | 0.0% | 0.0000 | 0.5763 |
| generated_xor_chain_32 | resyn2 | 3 | 0 | 92 | 0.0% | 0.0000 | 0.5763 |
| generated_xor_chain_32 | resyn2 | 5 | 0 | 92 | 0.0% | 0.0000 | 0.5763 |
| generated_xor_chain_32 | resyn2_like | 1 | 0 | 92 | 0.0% | 0.0000 | 0.5763 |
| generated_xor_chain_32 | resyn2_like | 2 | 0 | 92 | 0.0% | 0.0000 | 0.5763 |
| generated_xor_chain_32 | resyn2_like | 3 | 0 | 92 | 0.0% | 0.0000 | 0.5763 |
| generated_xor_chain_32 | resyn2_like | 5 | 0 | 92 | 0.0% | 0.0000 | 0.5763 |
| generated_xor_chain_32 | rewrite | 1 | 92 | 92 | 100.0% | 1.0000 | 1.0000 |
| generated_xor_chain_32 | rewrite | 2 | 92 | 92 | 100.0% | 1.0000 | 1.0000 |
| generated_xor_chain_32 | rewrite | 3 | 92 | 92 | 100.0% | 1.0000 | 1.0000 |
| generated_xor_chain_32 | rewrite | 5 | 92 | 92 | 100.0% | 1.0000 | 1.0000 |
| generated_xor_chain_32 | rewrite_z | 1 | 3 | 92 | 3.3% | 0.0326 | 0.5823 |
| generated_xor_chain_32 | rewrite_z | 2 | 3 | 92 | 3.3% | 0.0326 | 0.5823 |
| generated_xor_chain_32 | rewrite_z | 3 | 3 | 92 | 3.3% | 0.0326 | 0.5823 |
| generated_xor_chain_32 | rewrite_z | 5 | 3 | 92 | 3.3% | 0.0326 | 0.5823 |
| generated_xor_chain_8 | balance | 1 | 20 | 20 | 100.0% | 1.0000 | 1.0000 |
| generated_xor_chain_8 | balance | 2 | 20 | 20 | 100.0% | 1.0000 | 1.0000 |
| generated_xor_chain_8 | balance | 3 | 20 | 20 | 100.0% | 1.0000 | 1.0000 |
| generated_xor_chain_8 | balance | 5 | 20 | 20 | 100.0% | 1.0000 | 1.0000 |
| generated_xor_chain_8 | compress2rs | 1 | 0 | 20 | 0.0% | 0.0000 | 0.6257 |
| generated_xor_chain_8 | compress2rs | 2 | 0 | 20 | 0.0% | 0.0000 | 0.6257 |
| generated_xor_chain_8 | compress2rs | 3 | 0 | 20 | 0.0% | 0.0000 | 0.6257 |
| generated_xor_chain_8 | compress2rs | 5 | 0 | 20 | 0.0% | 0.0000 | 0.6257 |
| generated_xor_chain_8 | dc2 | 1 | 0 | 20 | 0.0% | 0.0000 | 0.5678 |
| generated_xor_chain_8 | dc2 | 2 | 0 | 20 | 0.0% | 0.0000 | 0.5678 |
| generated_xor_chain_8 | dc2 | 3 | 0 | 20 | 0.0% | 0.0000 | 0.5678 |
| generated_xor_chain_8 | dc2 | 5 | 0 | 20 | 0.0% | 0.0000 | 0.5678 |
| generated_xor_chain_8 | refactor | 1 | 20 | 20 | 100.0% | 1.0000 | 1.0000 |
| generated_xor_chain_8 | refactor | 2 | 20 | 20 | 100.0% | 1.0000 | 1.0000 |
| generated_xor_chain_8 | refactor | 3 | 20 | 20 | 100.0% | 1.0000 | 1.0000 |
| generated_xor_chain_8 | refactor | 5 | 20 | 20 | 100.0% | 1.0000 | 1.0000 |
| generated_xor_chain_8 | refactor_z | 1 | 17 | 20 | 85.0% | 0.8500 | 0.9719 |
| generated_xor_chain_8 | refactor_z | 2 | 17 | 20 | 85.0% | 0.8500 | 0.9719 |
| generated_xor_chain_8 | refactor_z | 3 | 17 | 20 | 85.0% | 0.8500 | 0.9719 |
| generated_xor_chain_8 | refactor_z | 5 | 17 | 20 | 85.0% | 0.8500 | 0.9719 |
| generated_xor_chain_8 | resub | 1 | 20 | 20 | 100.0% | 1.0000 | 1.0000 |
| generated_xor_chain_8 | resub | 2 | 20 | 20 | 100.0% | 1.0000 | 1.0000 |
| generated_xor_chain_8 | resub | 3 | 20 | 20 | 100.0% | 1.0000 | 1.0000 |
| generated_xor_chain_8 | resub | 5 | 20 | 20 | 100.0% | 1.0000 | 1.0000 |
| generated_xor_chain_8 | resyn | 1 | 3 | 20 | 15.0% | 0.1500 | 0.6538 |
| generated_xor_chain_8 | resyn | 2 | 3 | 20 | 15.0% | 0.1500 | 0.6538 |
| generated_xor_chain_8 | resyn | 3 | 3 | 20 | 15.0% | 0.1500 | 0.6538 |
| generated_xor_chain_8 | resyn | 5 | 3 | 20 | 15.0% | 0.1500 | 0.6538 |
| generated_xor_chain_8 | resyn2 | 1 | 0 | 20 | 0.0% | 0.0000 | 0.6257 |
| generated_xor_chain_8 | resyn2 | 2 | 0 | 20 | 0.0% | 0.0000 | 0.6257 |
| generated_xor_chain_8 | resyn2 | 3 | 0 | 20 | 0.0% | 0.0000 | 0.6257 |
| generated_xor_chain_8 | resyn2 | 5 | 0 | 20 | 0.0% | 0.0000 | 0.6257 |
| generated_xor_chain_8 | resyn2_like | 1 | 0 | 20 | 0.0% | 0.0000 | 0.6257 |
| generated_xor_chain_8 | resyn2_like | 2 | 0 | 20 | 0.0% | 0.0000 | 0.6257 |
| generated_xor_chain_8 | resyn2_like | 3 | 0 | 20 | 0.0% | 0.0000 | 0.6257 |
| generated_xor_chain_8 | resyn2_like | 5 | 0 | 20 | 0.0% | 0.0000 | 0.6257 |
| generated_xor_chain_8 | rewrite | 1 | 20 | 20 | 100.0% | 1.0000 | 1.0000 |
| generated_xor_chain_8 | rewrite | 2 | 20 | 20 | 100.0% | 1.0000 | 1.0000 |
| generated_xor_chain_8 | rewrite | 3 | 20 | 20 | 100.0% | 1.0000 | 1.0000 |
| generated_xor_chain_8 | rewrite | 5 | 20 | 20 | 100.0% | 1.0000 | 1.0000 |
| generated_xor_chain_8 | rewrite_z | 1 | 3 | 20 | 15.0% | 0.1500 | 0.6538 |
| generated_xor_chain_8 | rewrite_z | 2 | 3 | 20 | 15.0% | 0.1500 | 0.6538 |
| generated_xor_chain_8 | rewrite_z | 3 | 3 | 20 | 15.0% | 0.1500 | 0.6538 |
| generated_xor_chain_8 | rewrite_z | 5 | 3 | 20 | 15.0% | 0.1500 | 0.6538 |
| majority3 | balance | 1 | 0 | 4 | 0.0% | 0.0000 | 0.9656 |
| majority3 | balance | 2 | 0 | 4 | 0.0% | 0.0000 | 0.9656 |
| majority3 | balance | 3 | 0 | 4 | 0.0% | 0.0000 | 0.9656 |
| majority3 | balance | 5 | 0 | 4 | 0.0% | 0.0000 | 0.9656 |
| majority3 | compress2rs | 1 | 1 | 3 | 33.3% | 0.3333 | 0.8625 |
| majority3 | compress2rs | 2 | 1 | 3 | 33.3% | 0.3333 | 0.8625 |
| majority3 | compress2rs | 3 | 1 | 3 | 33.3% | 0.3333 | 0.8625 |
| majority3 | compress2rs | 5 | 1 | 3 | 33.3% | 0.3333 | 0.8625 |
| majority3 | dc2 | 1 | 0 | 3 | 0.0% | 0.0000 | 0.8625 |
| majority3 | dc2 | 2 | 0 | 3 | 0.0% | 0.0000 | 0.8625 |
| majority3 | dc2 | 3 | 0 | 3 | 0.0% | 0.0000 | 0.8625 |
| majority3 | dc2 | 5 | 0 | 3 | 0.0% | 0.0000 | 0.8625 |
| majority3 | refactor | 1 | 0 | 3 | 0.0% | 0.0000 | 0.8299 |
| majority3 | refactor | 2 | 0 | 3 | 0.0% | 0.0000 | 0.8299 |
| majority3 | refactor | 3 | 0 | 3 | 0.0% | 0.0000 | 0.8299 |
| majority3 | refactor | 5 | 0 | 3 | 0.0% | 0.0000 | 0.8299 |
| majority3 | refactor_z | 1 | 0 | 3 | 0.0% | 0.0000 | 0.8625 |
| majority3 | refactor_z | 2 | 0 | 3 | 0.0% | 0.0000 | 0.8625 |
| majority3 | refactor_z | 3 | 0 | 3 | 0.0% | 0.0000 | 0.8625 |
| majority3 | refactor_z | 5 | 0 | 3 | 0.0% | 0.0000 | 0.8625 |
| majority3 | resub | 1 | 1 | 4 | 25.0% | 0.2500 | 1.0000 |
| majority3 | resub | 2 | 1 | 4 | 25.0% | 0.2500 | 1.0000 |
| majority3 | resub | 3 | 1 | 4 | 25.0% | 0.2500 | 1.0000 |
| majority3 | resub | 5 | 1 | 4 | 25.0% | 0.2500 | 1.0000 |
| majority3 | resyn | 1 | 0 | 4 | 0.0% | 0.0000 | 0.9656 |
| majority3 | resyn | 2 | 0 | 4 | 0.0% | 0.0000 | 0.9656 |
| majority3 | resyn | 3 | 0 | 4 | 0.0% | 0.0000 | 0.9656 |
| majority3 | resyn | 5 | 0 | 4 | 0.0% | 0.0000 | 0.9656 |
| majority3 | resyn2 | 1 | 1 | 3 | 33.3% | 0.3333 | 0.8625 |
| majority3 | resyn2 | 2 | 1 | 3 | 33.3% | 0.3333 | 0.8625 |
| majority3 | resyn2 | 3 | 1 | 3 | 33.3% | 0.3333 | 0.8625 |
| majority3 | resyn2 | 5 | 1 | 3 | 33.3% | 0.3333 | 0.8625 |
| majority3 | resyn2_like | 1 | 1 | 3 | 33.3% | 0.3333 | 0.8625 |
| majority3 | resyn2_like | 2 | 1 | 3 | 33.3% | 0.3333 | 0.8625 |
| majority3 | resyn2_like | 3 | 1 | 3 | 33.3% | 0.3333 | 0.8625 |
| majority3 | resyn2_like | 5 | 1 | 3 | 33.3% | 0.3333 | 0.8625 |
| majority3 | rewrite | 1 | 1 | 4 | 25.0% | 0.2500 | 1.0000 |
| majority3 | rewrite | 2 | 1 | 4 | 25.0% | 0.2500 | 1.0000 |
| majority3 | rewrite | 3 | 1 | 4 | 25.0% | 0.2500 | 1.0000 |
| majority3 | rewrite | 5 | 1 | 4 | 25.0% | 0.2500 | 1.0000 |
| majority3 | rewrite_z | 1 | 1 | 4 | 25.0% | 0.2500 | 0.9656 |
| majority3 | rewrite_z | 2 | 1 | 4 | 25.0% | 0.2500 | 0.9656 |
| majority3 | rewrite_z | 3 | 1 | 4 | 25.0% | 0.2500 | 0.9656 |
| majority3 | rewrite_z | 5 | 1 | 4 | 25.0% | 0.2500 | 0.9656 |
| mux2 | balance | 1 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| mux2 | balance | 2 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| mux2 | balance | 3 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| mux2 | balance | 5 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| mux2 | compress2rs | 1 | 0 | 2 | 0.0% | 0.0000 | 0.7250 |
| mux2 | compress2rs | 2 | 0 | 2 | 0.0% | 0.0000 | 0.7250 |
| mux2 | compress2rs | 3 | 0 | 2 | 0.0% | 0.0000 | 0.7250 |
| mux2 | compress2rs | 5 | 0 | 2 | 0.0% | 0.0000 | 0.7250 |
| mux2 | dc2 | 1 | 0 | 2 | 0.0% | 0.0000 | 0.7250 |
| mux2 | dc2 | 2 | 0 | 2 | 0.0% | 0.0000 | 0.7250 |
| mux2 | dc2 | 3 | 0 | 2 | 0.0% | 0.0000 | 0.7250 |
| mux2 | dc2 | 5 | 0 | 2 | 0.0% | 0.0000 | 0.7250 |
| mux2 | refactor | 1 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| mux2 | refactor | 2 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| mux2 | refactor | 3 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| mux2 | refactor | 5 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| mux2 | refactor_z | 1 | 0 | 2 | 0.0% | 0.0000 | 0.7250 |
| mux2 | refactor_z | 2 | 0 | 2 | 0.0% | 0.0000 | 0.7250 |
| mux2 | refactor_z | 3 | 0 | 2 | 0.0% | 0.0000 | 0.7250 |
| mux2 | refactor_z | 5 | 0 | 2 | 0.0% | 0.0000 | 0.7250 |
| mux2 | resub | 1 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| mux2 | resub | 2 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| mux2 | resub | 3 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| mux2 | resub | 5 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| mux2 | resyn | 1 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| mux2 | resyn | 2 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| mux2 | resyn | 3 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| mux2 | resyn | 5 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| mux2 | resyn2 | 1 | 0 | 2 | 0.0% | 0.0000 | 0.7250 |
| mux2 | resyn2 | 2 | 0 | 2 | 0.0% | 0.0000 | 0.7250 |
| mux2 | resyn2 | 3 | 0 | 2 | 0.0% | 0.0000 | 0.7250 |
| mux2 | resyn2 | 5 | 0 | 2 | 0.0% | 0.0000 | 0.7250 |
| mux2 | resyn2_like | 1 | 0 | 2 | 0.0% | 0.0000 | 0.7250 |
| mux2 | resyn2_like | 2 | 0 | 2 | 0.0% | 0.0000 | 0.7250 |
| mux2 | resyn2_like | 3 | 0 | 2 | 0.0% | 0.0000 | 0.7250 |
| mux2 | resyn2_like | 5 | 0 | 2 | 0.0% | 0.0000 | 0.7250 |
| mux2 | rewrite | 1 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| mux2 | rewrite | 2 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| mux2 | rewrite | 3 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| mux2 | rewrite | 5 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| mux2 | rewrite_z | 1 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| mux2 | rewrite_z | 2 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| mux2 | rewrite_z | 3 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| mux2 | rewrite_z | 5 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| real_hand_written_comparator_4 | balance | 1 | 1 | 14 | 7.1% | 0.0714 | 0.9741 |
| real_hand_written_comparator_4 | balance | 2 | 1 | 14 | 7.1% | 0.0714 | 0.9741 |
| real_hand_written_comparator_4 | balance | 3 | 1 | 14 | 7.1% | 0.0714 | 0.9741 |
| real_hand_written_comparator_4 | balance | 5 | 1 | 14 | 7.1% | 0.0714 | 0.9741 |
| real_hand_written_comparator_4 | compress2rs | 1 | 1 | 14 | 7.1% | 0.0714 | 0.9741 |
| real_hand_written_comparator_4 | compress2rs | 2 | 1 | 14 | 7.1% | 0.0714 | 0.9741 |
| real_hand_written_comparator_4 | compress2rs | 3 | 1 | 14 | 7.1% | 0.0714 | 0.9741 |
| real_hand_written_comparator_4 | compress2rs | 5 | 1 | 14 | 7.1% | 0.0714 | 0.9741 |
| real_hand_written_comparator_4 | dc2 | 1 | 0 | 14 | 0.0% | 0.0000 | 0.9339 |
| real_hand_written_comparator_4 | dc2 | 2 | 0 | 14 | 0.0% | 0.0000 | 0.9339 |
| real_hand_written_comparator_4 | dc2 | 3 | 0 | 14 | 0.0% | 0.0000 | 0.9339 |
| real_hand_written_comparator_4 | dc2 | 5 | 0 | 14 | 0.0% | 0.0000 | 0.9339 |
| real_hand_written_comparator_4 | refactor | 1 | 2 | 14 | 14.3% | 0.1429 | 1.0000 |
| real_hand_written_comparator_4 | refactor | 2 | 2 | 14 | 14.3% | 0.1429 | 1.0000 |
| real_hand_written_comparator_4 | refactor | 3 | 2 | 14 | 14.3% | 0.1429 | 1.0000 |
| real_hand_written_comparator_4 | refactor | 5 | 2 | 14 | 14.3% | 0.1429 | 1.0000 |
| real_hand_written_comparator_4 | refactor_z | 1 | 0 | 14 | 0.0% | 0.0000 | 0.9741 |
| real_hand_written_comparator_4 | refactor_z | 2 | 0 | 14 | 0.0% | 0.0000 | 0.9741 |
| real_hand_written_comparator_4 | refactor_z | 3 | 0 | 14 | 0.0% | 0.0000 | 0.9741 |
| real_hand_written_comparator_4 | refactor_z | 5 | 0 | 14 | 0.0% | 0.0000 | 0.9741 |
| real_hand_written_comparator_4 | resub | 1 | 2 | 14 | 14.3% | 0.1429 | 1.0000 |
| real_hand_written_comparator_4 | resub | 2 | 2 | 14 | 14.3% | 0.1429 | 1.0000 |
| real_hand_written_comparator_4 | resub | 3 | 2 | 14 | 14.3% | 0.1429 | 1.0000 |
| real_hand_written_comparator_4 | resub | 5 | 2 | 14 | 14.3% | 0.1429 | 1.0000 |
| real_hand_written_comparator_4 | resyn | 1 | 1 | 14 | 7.1% | 0.0714 | 0.8536 |
| real_hand_written_comparator_4 | resyn | 2 | 1 | 14 | 7.1% | 0.0714 | 0.8536 |
| real_hand_written_comparator_4 | resyn | 3 | 1 | 14 | 7.1% | 0.0714 | 0.8536 |
| real_hand_written_comparator_4 | resyn | 5 | 1 | 14 | 7.1% | 0.0714 | 0.8536 |
| real_hand_written_comparator_4 | resyn2 | 1 | 1 | 14 | 7.1% | 0.0714 | 0.9741 |
| real_hand_written_comparator_4 | resyn2 | 2 | 1 | 14 | 7.1% | 0.0714 | 0.9741 |
| real_hand_written_comparator_4 | resyn2 | 3 | 1 | 14 | 7.1% | 0.0714 | 0.9741 |
| real_hand_written_comparator_4 | resyn2 | 5 | 1 | 14 | 7.1% | 0.0714 | 0.9741 |
| real_hand_written_comparator_4 | resyn2_like | 1 | 1 | 14 | 7.1% | 0.0714 | 0.9741 |
| real_hand_written_comparator_4 | resyn2_like | 2 | 1 | 14 | 7.1% | 0.0714 | 0.9741 |
| real_hand_written_comparator_4 | resyn2_like | 3 | 1 | 14 | 7.1% | 0.0714 | 0.9741 |
| real_hand_written_comparator_4 | resyn2_like | 5 | 1 | 14 | 7.1% | 0.0714 | 0.9741 |
| real_hand_written_comparator_4 | rewrite | 1 | 2 | 14 | 14.3% | 0.1429 | 1.0000 |
| real_hand_written_comparator_4 | rewrite | 2 | 2 | 14 | 14.3% | 0.1429 | 1.0000 |
| real_hand_written_comparator_4 | rewrite | 3 | 2 | 14 | 14.3% | 0.1429 | 1.0000 |
| real_hand_written_comparator_4 | rewrite | 5 | 2 | 14 | 14.3% | 0.1429 | 1.0000 |
| real_hand_written_comparator_4 | rewrite_z | 1 | 0 | 14 | 0.0% | 0.0000 | 0.9256 |
| real_hand_written_comparator_4 | rewrite_z | 2 | 0 | 14 | 0.0% | 0.0000 | 0.9256 |
| real_hand_written_comparator_4 | rewrite_z | 3 | 0 | 14 | 0.0% | 0.0000 | 0.9256 |
| real_hand_written_comparator_4 | rewrite_z | 5 | 0 | 14 | 0.0% | 0.0000 | 0.9256 |
| real_hand_written_full_adder | balance | 1 | 5 | 9 | 55.6% | 0.5556 | 0.9847 |
| real_hand_written_full_adder | balance | 2 | 5 | 9 | 55.6% | 0.5556 | 0.9847 |
| real_hand_written_full_adder | balance | 3 | 5 | 9 | 55.6% | 0.5556 | 0.9847 |
| real_hand_written_full_adder | balance | 5 | 5 | 9 | 55.6% | 0.5556 | 0.9847 |
| real_hand_written_full_adder | compress2rs | 1 | 2 | 5 | 40.0% | 0.4000 | 0.9250 |
| real_hand_written_full_adder | compress2rs | 2 | 2 | 5 | 40.0% | 0.4000 | 0.9250 |
| real_hand_written_full_adder | compress2rs | 3 | 2 | 5 | 40.0% | 0.4000 | 0.9250 |
| real_hand_written_full_adder | compress2rs | 5 | 2 | 5 | 40.0% | 0.4000 | 0.9250 |
| real_hand_written_full_adder | dc2 | 1 | 0 | 6 | 0.0% | 0.0000 | 0.8490 |
| real_hand_written_full_adder | dc2 | 2 | 0 | 6 | 0.0% | 0.0000 | 0.8490 |
| real_hand_written_full_adder | dc2 | 3 | 0 | 6 | 0.0% | 0.0000 | 0.8490 |
| real_hand_written_full_adder | dc2 | 5 | 0 | 6 | 0.0% | 0.0000 | 0.8490 |
| real_hand_written_full_adder | refactor | 1 | 3 | 8 | 37.5% | 0.3750 | 0.9531 |
| real_hand_written_full_adder | refactor | 2 | 3 | 8 | 37.5% | 0.3750 | 0.9531 |
| real_hand_written_full_adder | refactor | 3 | 3 | 8 | 37.5% | 0.3750 | 0.9531 |
| real_hand_written_full_adder | refactor | 5 | 3 | 8 | 37.5% | 0.3750 | 0.9531 |
| real_hand_written_full_adder | refactor_z | 1 | 2 | 8 | 25.0% | 0.2500 | 0.9016 |
| real_hand_written_full_adder | refactor_z | 2 | 2 | 8 | 25.0% | 0.2500 | 0.9016 |
| real_hand_written_full_adder | refactor_z | 3 | 2 | 8 | 25.0% | 0.2500 | 0.9016 |
| real_hand_written_full_adder | refactor_z | 5 | 2 | 8 | 25.0% | 0.2500 | 0.9016 |
| real_hand_written_full_adder | resub | 1 | 6 | 9 | 66.7% | 0.6667 | 1.0000 |
| real_hand_written_full_adder | resub | 2 | 6 | 9 | 66.7% | 0.6667 | 1.0000 |
| real_hand_written_full_adder | resub | 3 | 6 | 9 | 66.7% | 0.6667 | 1.0000 |
| real_hand_written_full_adder | resub | 5 | 6 | 9 | 66.7% | 0.6667 | 1.0000 |
| real_hand_written_full_adder | resyn | 1 | 5 | 9 | 55.6% | 0.5556 | 0.9847 |
| real_hand_written_full_adder | resyn | 2 | 5 | 9 | 55.6% | 0.5556 | 0.9847 |
| real_hand_written_full_adder | resyn | 3 | 5 | 9 | 55.6% | 0.5556 | 0.9847 |
| real_hand_written_full_adder | resyn | 5 | 5 | 9 | 55.6% | 0.5556 | 0.9847 |
| real_hand_written_full_adder | resyn2 | 1 | 3 | 8 | 37.5% | 0.3750 | 0.9016 |
| real_hand_written_full_adder | resyn2 | 2 | 3 | 8 | 37.5% | 0.3750 | 0.9016 |
| real_hand_written_full_adder | resyn2 | 3 | 3 | 8 | 37.5% | 0.3750 | 0.9016 |
| real_hand_written_full_adder | resyn2 | 5 | 3 | 8 | 37.5% | 0.3750 | 0.9016 |
| real_hand_written_full_adder | resyn2_like | 1 | 3 | 8 | 37.5% | 0.3750 | 0.9016 |
| real_hand_written_full_adder | resyn2_like | 2 | 3 | 8 | 37.5% | 0.3750 | 0.9016 |
| real_hand_written_full_adder | resyn2_like | 3 | 3 | 8 | 37.5% | 0.3750 | 0.9016 |
| real_hand_written_full_adder | resyn2_like | 5 | 3 | 8 | 37.5% | 0.3750 | 0.9016 |
| real_hand_written_full_adder | rewrite | 1 | 6 | 9 | 66.7% | 0.6667 | 1.0000 |
| real_hand_written_full_adder | rewrite | 2 | 6 | 9 | 66.7% | 0.6667 | 1.0000 |
| real_hand_written_full_adder | rewrite | 3 | 6 | 9 | 66.7% | 0.6667 | 1.0000 |
| real_hand_written_full_adder | rewrite | 5 | 6 | 9 | 66.7% | 0.6667 | 1.0000 |
| real_hand_written_full_adder | rewrite_z | 1 | 6 | 9 | 66.7% | 0.6667 | 0.9847 |
| real_hand_written_full_adder | rewrite_z | 2 | 6 | 9 | 66.7% | 0.6667 | 0.9847 |
| real_hand_written_full_adder | rewrite_z | 3 | 6 | 9 | 66.7% | 0.6667 | 0.9847 |
| real_hand_written_full_adder | rewrite_z | 5 | 6 | 9 | 66.7% | 0.6667 | 0.9847 |
| real_hand_written_mux_4to1 | balance | 1 | 2 | 10 | 20.0% | 0.2000 | 0.9058 |
| real_hand_written_mux_4to1 | balance | 2 | 2 | 10 | 20.0% | 0.2000 | 0.9058 |
| real_hand_written_mux_4to1 | balance | 3 | 2 | 10 | 20.0% | 0.2000 | 0.9058 |
| real_hand_written_mux_4to1 | balance | 5 | 2 | 10 | 20.0% | 0.2000 | 0.9058 |
| real_hand_written_mux_4to1 | compress2rs | 1 | 0 | 8 | 0.0% | 0.0000 | 0.6505 |
| real_hand_written_mux_4to1 | compress2rs | 2 | 0 | 8 | 0.0% | 0.0000 | 0.6505 |
| real_hand_written_mux_4to1 | compress2rs | 3 | 0 | 8 | 0.0% | 0.0000 | 0.6505 |
| real_hand_written_mux_4to1 | compress2rs | 5 | 0 | 8 | 0.0% | 0.0000 | 0.6505 |
| real_hand_written_mux_4to1 | dc2 | 1 | 0 | 8 | 0.0% | 0.0000 | 0.7497 |
| real_hand_written_mux_4to1 | dc2 | 2 | 0 | 8 | 0.0% | 0.0000 | 0.7497 |
| real_hand_written_mux_4to1 | dc2 | 3 | 0 | 8 | 0.0% | 0.0000 | 0.7497 |
| real_hand_written_mux_4to1 | dc2 | 5 | 0 | 8 | 0.0% | 0.0000 | 0.7497 |
| real_hand_written_mux_4to1 | refactor | 1 | 0 | 8 | 0.0% | 0.0000 | 0.7620 |
| real_hand_written_mux_4to1 | refactor | 2 | 0 | 8 | 0.0% | 0.0000 | 0.7620 |
| real_hand_written_mux_4to1 | refactor | 3 | 0 | 8 | 0.0% | 0.0000 | 0.7620 |
| real_hand_written_mux_4to1 | refactor | 5 | 0 | 8 | 0.0% | 0.0000 | 0.7620 |
| real_hand_written_mux_4to1 | refactor_z | 1 | 0 | 8 | 0.0% | 0.0000 | 0.6505 |
| real_hand_written_mux_4to1 | refactor_z | 2 | 0 | 8 | 0.0% | 0.0000 | 0.6505 |
| real_hand_written_mux_4to1 | refactor_z | 3 | 0 | 8 | 0.0% | 0.0000 | 0.6505 |
| real_hand_written_mux_4to1 | refactor_z | 5 | 0 | 8 | 0.0% | 0.0000 | 0.6505 |
| real_hand_written_mux_4to1 | resub | 1 | 1 | 10 | 10.0% | 0.1000 | 1.0000 |
| real_hand_written_mux_4to1 | resub | 2 | 1 | 10 | 10.0% | 0.1000 | 1.0000 |
| real_hand_written_mux_4to1 | resub | 3 | 1 | 10 | 10.0% | 0.1000 | 1.0000 |
| real_hand_written_mux_4to1 | resub | 5 | 1 | 10 | 10.0% | 0.1000 | 1.0000 |
| real_hand_written_mux_4to1 | resyn | 1 | 0 | 8 | 0.0% | 0.0000 | 0.7286 |
| real_hand_written_mux_4to1 | resyn | 2 | 0 | 8 | 0.0% | 0.0000 | 0.7286 |
| real_hand_written_mux_4to1 | resyn | 3 | 0 | 8 | 0.0% | 0.0000 | 0.7286 |
| real_hand_written_mux_4to1 | resyn | 5 | 0 | 8 | 0.0% | 0.0000 | 0.7286 |
| real_hand_written_mux_4to1 | resyn2 | 1 | 0 | 8 | 0.0% | 0.0000 | 0.6505 |
| real_hand_written_mux_4to1 | resyn2 | 2 | 0 | 8 | 0.0% | 0.0000 | 0.6505 |
| real_hand_written_mux_4to1 | resyn2 | 3 | 0 | 8 | 0.0% | 0.0000 | 0.6505 |
| real_hand_written_mux_4to1 | resyn2 | 5 | 0 | 8 | 0.0% | 0.0000 | 0.6505 |
| real_hand_written_mux_4to1 | resyn2_like | 1 | 0 | 8 | 0.0% | 0.0000 | 0.6505 |
| real_hand_written_mux_4to1 | resyn2_like | 2 | 0 | 8 | 0.0% | 0.0000 | 0.6505 |
| real_hand_written_mux_4to1 | resyn2_like | 3 | 0 | 8 | 0.0% | 0.0000 | 0.6505 |
| real_hand_written_mux_4to1 | resyn2_like | 5 | 0 | 8 | 0.0% | 0.0000 | 0.6505 |
| real_hand_written_mux_4to1 | rewrite | 1 | 0 | 8 | 0.0% | 0.0000 | 0.7286 |
| real_hand_written_mux_4to1 | rewrite | 2 | 0 | 8 | 0.0% | 0.0000 | 0.7286 |
| real_hand_written_mux_4to1 | rewrite | 3 | 0 | 8 | 0.0% | 0.0000 | 0.7286 |
| real_hand_written_mux_4to1 | rewrite | 5 | 0 | 8 | 0.0% | 0.0000 | 0.7286 |
| real_hand_written_mux_4to1 | rewrite_z | 1 | 0 | 8 | 0.0% | 0.0000 | 0.7286 |
| real_hand_written_mux_4to1 | rewrite_z | 2 | 0 | 8 | 0.0% | 0.0000 | 0.7286 |
| real_hand_written_mux_4to1 | rewrite_z | 3 | 0 | 8 | 0.0% | 0.0000 | 0.7286 |
| real_hand_written_mux_4to1 | rewrite_z | 5 | 0 | 8 | 0.0% | 0.0000 | 0.7286 |
| real_hand_written_parity_8 | balance | 1 | 20 | 20 | 100.0% | 1.0000 | 1.0000 |
| real_hand_written_parity_8 | balance | 2 | 20 | 20 | 100.0% | 1.0000 | 1.0000 |
| real_hand_written_parity_8 | balance | 3 | 20 | 20 | 100.0% | 1.0000 | 1.0000 |
| real_hand_written_parity_8 | balance | 5 | 20 | 20 | 100.0% | 1.0000 | 1.0000 |
| real_hand_written_parity_8 | compress2rs | 1 | 3 | 20 | 15.0% | 0.1500 | 0.8594 |
| real_hand_written_parity_8 | compress2rs | 2 | 3 | 20 | 15.0% | 0.1500 | 0.8594 |
| real_hand_written_parity_8 | compress2rs | 3 | 3 | 20 | 15.0% | 0.1500 | 0.8594 |
| real_hand_written_parity_8 | compress2rs | 5 | 3 | 20 | 15.0% | 0.1500 | 0.8594 |
| real_hand_written_parity_8 | dc2 | 1 | 1 | 20 | 5.0% | 0.0500 | 0.8071 |
| real_hand_written_parity_8 | dc2 | 2 | 1 | 20 | 5.0% | 0.0500 | 0.8071 |
| real_hand_written_parity_8 | dc2 | 3 | 1 | 20 | 5.0% | 0.0500 | 0.8071 |
| real_hand_written_parity_8 | dc2 | 5 | 1 | 20 | 5.0% | 0.0500 | 0.8071 |
| real_hand_written_parity_8 | refactor | 1 | 20 | 20 | 100.0% | 1.0000 | 1.0000 |
| real_hand_written_parity_8 | refactor | 2 | 20 | 20 | 100.0% | 1.0000 | 1.0000 |
| real_hand_written_parity_8 | refactor | 3 | 20 | 20 | 100.0% | 1.0000 | 1.0000 |
| real_hand_written_parity_8 | refactor | 5 | 20 | 20 | 100.0% | 1.0000 | 1.0000 |
| real_hand_written_parity_8 | refactor_z | 1 | 8 | 20 | 40.0% | 0.4000 | 0.8875 |
| real_hand_written_parity_8 | refactor_z | 2 | 8 | 20 | 40.0% | 0.4000 | 0.8875 |
| real_hand_written_parity_8 | refactor_z | 3 | 8 | 20 | 40.0% | 0.4000 | 0.8875 |
| real_hand_written_parity_8 | refactor_z | 5 | 8 | 20 | 40.0% | 0.4000 | 0.8875 |
| real_hand_written_parity_8 | resub | 1 | 20 | 20 | 100.0% | 1.0000 | 1.0000 |
| real_hand_written_parity_8 | resub | 2 | 20 | 20 | 100.0% | 1.0000 | 1.0000 |
| real_hand_written_parity_8 | resub | 3 | 20 | 20 | 100.0% | 1.0000 | 1.0000 |
| real_hand_written_parity_8 | resub | 5 | 20 | 20 | 100.0% | 1.0000 | 1.0000 |
| real_hand_written_parity_8 | resyn | 1 | 15 | 20 | 75.0% | 0.7500 | 0.9719 |
| real_hand_written_parity_8 | resyn | 2 | 15 | 20 | 75.0% | 0.7500 | 0.9719 |
| real_hand_written_parity_8 | resyn | 3 | 15 | 20 | 75.0% | 0.7500 | 0.9719 |
| real_hand_written_parity_8 | resyn | 5 | 15 | 20 | 75.0% | 0.7500 | 0.9719 |
| real_hand_written_parity_8 | resyn2 | 1 | 3 | 20 | 15.0% | 0.1500 | 0.8594 |
| real_hand_written_parity_8 | resyn2 | 2 | 3 | 20 | 15.0% | 0.1500 | 0.8594 |
| real_hand_written_parity_8 | resyn2 | 3 | 3 | 20 | 15.0% | 0.1500 | 0.8594 |
| real_hand_written_parity_8 | resyn2 | 5 | 3 | 20 | 15.0% | 0.1500 | 0.8594 |
| real_hand_written_parity_8 | resyn2_like | 1 | 3 | 20 | 15.0% | 0.1500 | 0.8594 |
| real_hand_written_parity_8 | resyn2_like | 2 | 3 | 20 | 15.0% | 0.1500 | 0.8594 |
| real_hand_written_parity_8 | resyn2_like | 3 | 3 | 20 | 15.0% | 0.1500 | 0.8594 |
| real_hand_written_parity_8 | resyn2_like | 5 | 3 | 20 | 15.0% | 0.1500 | 0.8594 |
| real_hand_written_parity_8 | rewrite | 1 | 20 | 20 | 100.0% | 1.0000 | 1.0000 |
| real_hand_written_parity_8 | rewrite | 2 | 20 | 20 | 100.0% | 1.0000 | 1.0000 |
| real_hand_written_parity_8 | rewrite | 3 | 20 | 20 | 100.0% | 1.0000 | 1.0000 |
| real_hand_written_parity_8 | rewrite | 5 | 20 | 20 | 100.0% | 1.0000 | 1.0000 |
| real_hand_written_parity_8 | rewrite_z | 1 | 15 | 20 | 75.0% | 0.7500 | 0.9719 |
| real_hand_written_parity_8 | rewrite_z | 2 | 15 | 20 | 75.0% | 0.7500 | 0.9719 |
| real_hand_written_parity_8 | rewrite_z | 3 | 15 | 20 | 75.0% | 0.7500 | 0.9719 |
| real_hand_written_parity_8 | rewrite_z | 5 | 15 | 20 | 75.0% | 0.7500 | 0.9719 |
| real_hand_written_priority_enc_4 | balance | 1 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| real_hand_written_priority_enc_4 | balance | 2 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| real_hand_written_priority_enc_4 | balance | 3 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| real_hand_written_priority_enc_4 | balance | 5 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| real_hand_written_priority_enc_4 | compress2rs | 1 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| real_hand_written_priority_enc_4 | compress2rs | 2 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| real_hand_written_priority_enc_4 | compress2rs | 3 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| real_hand_written_priority_enc_4 | compress2rs | 5 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| real_hand_written_priority_enc_4 | dc2 | 1 | 1 | 2 | 50.0% | 0.5000 | 0.7750 |
| real_hand_written_priority_enc_4 | dc2 | 2 | 1 | 2 | 50.0% | 0.5000 | 0.7750 |
| real_hand_written_priority_enc_4 | dc2 | 3 | 1 | 2 | 50.0% | 0.5000 | 0.7750 |
| real_hand_written_priority_enc_4 | dc2 | 5 | 1 | 2 | 50.0% | 0.5000 | 0.7750 |
| real_hand_written_priority_enc_4 | refactor | 1 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| real_hand_written_priority_enc_4 | refactor | 2 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| real_hand_written_priority_enc_4 | refactor | 3 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| real_hand_written_priority_enc_4 | refactor | 5 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| real_hand_written_priority_enc_4 | refactor_z | 1 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| real_hand_written_priority_enc_4 | refactor_z | 2 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| real_hand_written_priority_enc_4 | refactor_z | 3 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| real_hand_written_priority_enc_4 | refactor_z | 5 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| real_hand_written_priority_enc_4 | resub | 1 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| real_hand_written_priority_enc_4 | resub | 2 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| real_hand_written_priority_enc_4 | resub | 3 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| real_hand_written_priority_enc_4 | resub | 5 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| real_hand_written_priority_enc_4 | resyn | 1 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| real_hand_written_priority_enc_4 | resyn | 2 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| real_hand_written_priority_enc_4 | resyn | 3 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| real_hand_written_priority_enc_4 | resyn | 5 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| real_hand_written_priority_enc_4 | resyn2 | 1 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| real_hand_written_priority_enc_4 | resyn2 | 2 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| real_hand_written_priority_enc_4 | resyn2 | 3 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| real_hand_written_priority_enc_4 | resyn2 | 5 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| real_hand_written_priority_enc_4 | resyn2_like | 1 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| real_hand_written_priority_enc_4 | resyn2_like | 2 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| real_hand_written_priority_enc_4 | resyn2_like | 3 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| real_hand_written_priority_enc_4 | resyn2_like | 5 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| real_hand_written_priority_enc_4 | rewrite | 1 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| real_hand_written_priority_enc_4 | rewrite | 2 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| real_hand_written_priority_enc_4 | rewrite | 3 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| real_hand_written_priority_enc_4 | rewrite | 5 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| real_hand_written_priority_enc_4 | rewrite_z | 1 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| real_hand_written_priority_enc_4 | rewrite_z | 2 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| real_hand_written_priority_enc_4 | rewrite_z | 3 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| real_hand_written_priority_enc_4 | rewrite_z | 5 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| toy_and_or | balance | 1 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| toy_and_or | balance | 2 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| toy_and_or | balance | 3 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| toy_and_or | balance | 5 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| toy_and_or | compress2rs | 1 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| toy_and_or | compress2rs | 2 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| toy_and_or | compress2rs | 3 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| toy_and_or | compress2rs | 5 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| toy_and_or | dc2 | 1 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| toy_and_or | dc2 | 2 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| toy_and_or | dc2 | 3 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| toy_and_or | dc2 | 5 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| toy_and_or | refactor | 1 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| toy_and_or | refactor | 2 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| toy_and_or | refactor | 3 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| toy_and_or | refactor | 5 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| toy_and_or | refactor_z | 1 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| toy_and_or | refactor_z | 2 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| toy_and_or | refactor_z | 3 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| toy_and_or | refactor_z | 5 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| toy_and_or | resub | 1 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| toy_and_or | resub | 2 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| toy_and_or | resub | 3 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| toy_and_or | resub | 5 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| toy_and_or | resyn | 1 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| toy_and_or | resyn | 2 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| toy_and_or | resyn | 3 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| toy_and_or | resyn | 5 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| toy_and_or | resyn2 | 1 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| toy_and_or | resyn2 | 2 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| toy_and_or | resyn2 | 3 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| toy_and_or | resyn2 | 5 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| toy_and_or | resyn2_like | 1 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| toy_and_or | resyn2_like | 2 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| toy_and_or | resyn2_like | 3 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| toy_and_or | resyn2_like | 5 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| toy_and_or | rewrite | 1 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| toy_and_or | rewrite | 2 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| toy_and_or | rewrite | 3 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| toy_and_or | rewrite | 5 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| toy_and_or | rewrite_z | 1 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| toy_and_or | rewrite_z | 2 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| toy_and_or | rewrite_z | 3 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| toy_and_or | rewrite_z | 5 | 2 | 2 | 100.0% | 1.0000 | 1.0000 |
| xor_chain | balance | 1 | 8 | 8 | 100.0% | 1.0000 | 1.0000 |
| xor_chain | balance | 2 | 8 | 8 | 100.0% | 1.0000 | 1.0000 |
| xor_chain | balance | 3 | 8 | 8 | 100.0% | 1.0000 | 1.0000 |
| xor_chain | balance | 5 | 8 | 8 | 100.0% | 1.0000 | 1.0000 |
| xor_chain | compress2rs | 1 | 0 | 8 | 0.0% | 0.0000 | 0.7097 |
| xor_chain | compress2rs | 2 | 0 | 8 | 0.0% | 0.0000 | 0.7097 |
| xor_chain | compress2rs | 3 | 0 | 8 | 0.0% | 0.0000 | 0.7097 |
| xor_chain | compress2rs | 5 | 0 | 8 | 0.0% | 0.0000 | 0.7097 |
| xor_chain | dc2 | 1 | 0 | 8 | 0.0% | 0.0000 | 0.7149 |
| xor_chain | dc2 | 2 | 0 | 8 | 0.0% | 0.0000 | 0.7149 |
| xor_chain | dc2 | 3 | 0 | 8 | 0.0% | 0.0000 | 0.7149 |
| xor_chain | dc2 | 5 | 0 | 8 | 0.0% | 0.0000 | 0.7149 |
| xor_chain | refactor | 1 | 8 | 8 | 100.0% | 1.0000 | 1.0000 |
| xor_chain | refactor | 2 | 8 | 8 | 100.0% | 1.0000 | 1.0000 |
| xor_chain | refactor | 3 | 8 | 8 | 100.0% | 1.0000 | 1.0000 |
| xor_chain | refactor | 5 | 8 | 8 | 100.0% | 1.0000 | 1.0000 |
| xor_chain | refactor_z | 1 | 5 | 8 | 62.5% | 0.6250 | 0.9297 |
| xor_chain | refactor_z | 2 | 5 | 8 | 62.5% | 0.6250 | 0.9297 |
| xor_chain | refactor_z | 3 | 5 | 8 | 62.5% | 0.6250 | 0.9297 |
| xor_chain | refactor_z | 5 | 5 | 8 | 62.5% | 0.6250 | 0.9297 |
| xor_chain | resub | 1 | 8 | 8 | 100.0% | 1.0000 | 1.0000 |
| xor_chain | resub | 2 | 8 | 8 | 100.0% | 1.0000 | 1.0000 |
| xor_chain | resub | 3 | 8 | 8 | 100.0% | 1.0000 | 1.0000 |
| xor_chain | resub | 5 | 8 | 8 | 100.0% | 1.0000 | 1.0000 |
| xor_chain | resyn | 1 | 3 | 8 | 37.5% | 0.3750 | 0.7800 |
| xor_chain | resyn | 2 | 3 | 8 | 37.5% | 0.3750 | 0.7800 |
| xor_chain | resyn | 3 | 3 | 8 | 37.5% | 0.3750 | 0.7800 |
| xor_chain | resyn | 5 | 3 | 8 | 37.5% | 0.3750 | 0.7800 |
| xor_chain | resyn2 | 1 | 0 | 8 | 0.0% | 0.0000 | 0.7097 |
| xor_chain | resyn2 | 2 | 0 | 8 | 0.0% | 0.0000 | 0.7097 |
| xor_chain | resyn2 | 3 | 0 | 8 | 0.0% | 0.0000 | 0.7097 |
| xor_chain | resyn2 | 5 | 0 | 8 | 0.0% | 0.0000 | 0.7097 |
| xor_chain | resyn2_like | 1 | 0 | 8 | 0.0% | 0.0000 | 0.7097 |
| xor_chain | resyn2_like | 2 | 0 | 8 | 0.0% | 0.0000 | 0.7097 |
| xor_chain | resyn2_like | 3 | 0 | 8 | 0.0% | 0.0000 | 0.7097 |
| xor_chain | resyn2_like | 5 | 0 | 8 | 0.0% | 0.0000 | 0.7097 |
| xor_chain | rewrite | 1 | 8 | 8 | 100.0% | 1.0000 | 1.0000 |
| xor_chain | rewrite | 2 | 8 | 8 | 100.0% | 1.0000 | 1.0000 |
| xor_chain | rewrite | 3 | 8 | 8 | 100.0% | 1.0000 | 1.0000 |
| xor_chain | rewrite | 5 | 8 | 8 | 100.0% | 1.0000 | 1.0000 |
| xor_chain | rewrite_z | 1 | 3 | 8 | 37.5% | 0.3750 | 0.7800 |
| xor_chain | rewrite_z | 2 | 3 | 8 | 37.5% | 0.3750 | 0.7800 |
| xor_chain | rewrite_z | 3 | 3 | 8 | 37.5% | 0.3750 | 0.7800 |
| xor_chain | rewrite_z | 5 | 3 | 8 | 37.5% | 0.3750 | 0.7800 |

## Global summary

- **K=1**: 1688/5350 nodes recovered (31.6%)
- **K=2**: 1688/5350 nodes recovered (31.6%)
- **K=3**: 1688/5350 nodes recovered (31.6%)
- **K=5**: 1688/5350 nodes recovered (31.6%)

## Interpretation

**verified_at_k** is the number of optimized nodes for which the ABC-verified match appears within the top-K simulation-ranked candidates.

**recovery_at_k** = verified_at_k / total_nodes. A value of 1.0 at K=1 means the rank-1 candidate was always the formally correct match — the simulation ranking was perfect.

**MRR** (Mean Reciprocal Rank) measures how high the first verified candidate appears on average. MRR=1.0 means every verified match was rank-1; MRR=0.5 means verified matches appeared at rank 2 on average.

**avg_score_at_1** is the mean combined_score of the top-ranked candidate per node. It is available even without SAT results and gives a proxy for how confidently the simulation step selected candidates.
