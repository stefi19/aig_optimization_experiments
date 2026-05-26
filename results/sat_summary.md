# SAT Refinement Summary

## Overall result

- **Total candidates checked:** 3477
- **Verified by ABC:** 1688
- **Rejected by ABC:** 20
- **Inconclusive:** 1769
- **Verification rate:** 48.5%

## Recovery method breakdown

Each completed check is tagged with the method used to locate the node in the BLIF file:

- **direct** (3477): node name found in the BLIF without any fallback
- **fingerprint** (0): node name was missing; recovered via a unique SHA-256 fingerprint match
- **still inconclusive** (0): node could not be resolved (name missing and fingerprint ambiguous/absent, missing BLIF, ABC timeout, etc.)

## Summary by benchmark and optimization

| benchmark | optimization | verified | rejected | inconclusive | total | verification_rate | rejection_rate | inconclusive_rate | avg_combined_score | direct_name_count | fingerprint_recovered | still_inconclusive |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| generated_adder_4 | balance | 31 | 0 | 0 | 31 | 100.00% | 0.00% | 0.00% | 1.0000 | 31 | 0 | 0 |
| generated_adder_4 | compress2rs | 0 | 0 | 11 | 11 | 0.00% | 0.00% | 100.00% | 1.0000 | 11 | 0 | 0 |
| generated_adder_4 | dc2 | 0 | 0 | 11 | 11 | 0.00% | 0.00% | 100.00% | 1.0000 | 11 | 0 | 0 |
| generated_adder_4 | refactor | 0 | 0 | 11 | 11 | 0.00% | 0.00% | 100.00% | 1.0000 | 11 | 0 | 0 |
| generated_adder_4 | refactor_z | 0 | 0 | 11 | 11 | 0.00% | 0.00% | 100.00% | 1.0000 | 11 | 0 | 0 |
| generated_adder_4 | resub | 31 | 0 | 0 | 31 | 100.00% | 0.00% | 0.00% | 1.0000 | 31 | 0 | 0 |
| generated_adder_4 | resyn | 15 | 0 | 10 | 25 | 60.00% | 0.00% | 40.00% | 1.0000 | 25 | 0 | 0 |
| generated_adder_4 | resyn2 | 0 | 0 | 11 | 11 | 0.00% | 0.00% | 100.00% | 1.0000 | 11 | 0 | 0 |
| generated_adder_4 | resyn2_like | 0 | 0 | 11 | 11 | 0.00% | 0.00% | 100.00% | 1.0000 | 11 | 0 | 0 |
| generated_adder_4 | rewrite | 15 | 0 | 10 | 25 | 60.00% | 0.00% | 40.00% | 1.0000 | 25 | 0 | 0 |
| generated_adder_4 | rewrite_z | 15 | 0 | 10 | 25 | 60.00% | 0.00% | 40.00% | 1.0000 | 25 | 0 | 0 |
| generated_adder_8 | balance | 63 | 0 | 0 | 63 | 100.00% | 0.00% | 0.00% | 1.0000 | 63 | 0 | 0 |
| generated_adder_8 | compress2rs | 0 | 0 | 23 | 23 | 0.00% | 0.00% | 100.00% | 1.0000 | 23 | 0 | 0 |
| generated_adder_8 | dc2 | 0 | 0 | 23 | 23 | 0.00% | 0.00% | 100.00% | 1.0000 | 23 | 0 | 0 |
| generated_adder_8 | refactor | 0 | 0 | 23 | 23 | 0.00% | 0.00% | 100.00% | 1.0000 | 23 | 0 | 0 |
| generated_adder_8 | refactor_z | 0 | 0 | 23 | 23 | 0.00% | 0.00% | 100.00% | 1.0000 | 23 | 0 | 0 |
| generated_adder_8 | resub | 63 | 0 | 0 | 63 | 100.00% | 0.00% | 0.00% | 1.0000 | 63 | 0 | 0 |
| generated_adder_8 | resyn | 15 | 0 | 34 | 49 | 30.61% | 0.00% | 69.39% | 1.0000 | 49 | 0 | 0 |
| generated_adder_8 | resyn2 | 0 | 0 | 23 | 23 | 0.00% | 0.00% | 100.00% | 1.0000 | 23 | 0 | 0 |
| generated_adder_8 | resyn2_like | 0 | 0 | 23 | 23 | 0.00% | 0.00% | 100.00% | 1.0000 | 23 | 0 | 0 |
| generated_adder_8 | rewrite | 15 | 0 | 34 | 49 | 30.61% | 0.00% | 69.39% | 1.0000 | 49 | 0 | 0 |
| generated_adder_8 | rewrite_z | 15 | 0 | 34 | 49 | 30.61% | 0.00% | 69.39% | 1.0000 | 49 | 0 | 0 |
| generated_multiplier_2 | balance | 8 | 0 | 0 | 8 | 100.00% | 0.00% | 0.00% | 1.0000 | 8 | 0 | 0 |
| generated_multiplier_2 | compress2rs | 2 | 0 | 1 | 3 | 66.67% | 0.00% | 33.33% | 1.0000 | 3 | 0 | 0 |
| generated_multiplier_2 | dc2 | 2 | 0 | 0 | 2 | 100.00% | 0.00% | 0.00% | 1.0000 | 2 | 0 | 0 |
| generated_multiplier_2 | refactor | 3 | 0 | 1 | 4 | 75.00% | 0.00% | 25.00% | 1.0000 | 4 | 0 | 0 |
| generated_multiplier_2 | refactor_z | 3 | 0 | 1 | 4 | 75.00% | 0.00% | 25.00% | 1.0000 | 4 | 0 | 0 |
| generated_multiplier_2 | resub | 5 | 0 | 0 | 5 | 100.00% | 0.00% | 0.00% | 1.0000 | 5 | 0 | 0 |
| generated_multiplier_2 | resyn | 5 | 0 | 0 | 5 | 100.00% | 0.00% | 0.00% | 1.0000 | 5 | 0 | 0 |
| generated_multiplier_2 | resyn2 | 2 | 0 | 1 | 3 | 66.67% | 0.00% | 33.33% | 1.0000 | 3 | 0 | 0 |
| generated_multiplier_2 | resyn2_like | 2 | 0 | 1 | 3 | 66.67% | 0.00% | 33.33% | 1.0000 | 3 | 0 | 0 |
| generated_multiplier_2 | rewrite | 5 | 0 | 0 | 5 | 100.00% | 0.00% | 0.00% | 1.0000 | 5 | 0 | 0 |
| generated_multiplier_2 | rewrite_z | 5 | 0 | 0 | 5 | 100.00% | 0.00% | 0.00% | 1.0000 | 5 | 0 | 0 |
| generated_multiplier_4 | balance | 96 | 0 | 16 | 112 | 85.71% | 0.00% | 14.29% | 0.9970 | 112 | 0 | 0 |
| generated_multiplier_4 | compress2rs | 3 | 1 | 68 | 72 | 4.17% | 1.39% | 94.44% | 0.9430 | 72 | 0 | 0 |
| generated_multiplier_4 | dc2 | 3 | 1 | 74 | 78 | 3.85% | 1.28% | 94.87% | 0.9407 | 78 | 0 | 0 |
| generated_multiplier_4 | refactor | 8 | 0 | 89 | 97 | 8.25% | 0.00% | 91.75% | 0.9854 | 97 | 0 | 0 |
| generated_multiplier_4 | refactor_z | 4 | 0 | 88 | 92 | 4.35% | 0.00% | 95.65% | 0.9683 | 92 | 0 | 0 |
| generated_multiplier_4 | resub | 18 | 0 | 83 | 101 | 17.82% | 0.00% | 82.18% | 0.9927 | 101 | 0 | 0 |
| generated_multiplier_4 | resyn | 5 | 1 | 74 | 80 | 6.25% | 1.25% | 92.50% | 0.9432 | 80 | 0 | 0 |
| generated_multiplier_4 | resyn2 | 3 | 1 | 74 | 78 | 3.85% | 1.28% | 94.87% | 0.9417 | 78 | 0 | 0 |
| generated_multiplier_4 | resyn2_like | 3 | 1 | 74 | 78 | 3.85% | 1.28% | 94.87% | 0.9417 | 78 | 0 | 0 |
| generated_multiplier_4 | rewrite | 15 | 1 | 67 | 83 | 18.07% | 1.20% | 80.72% | 0.9767 | 83 | 0 | 0 |
| generated_multiplier_4 | rewrite_z | 5 | 4 | 76 | 85 | 5.88% | 4.71% | 89.41% | 0.9474 | 85 | 0 | 0 |
| generated_mux_tree_16 | balance | 1 | 0 | 43 | 44 | 2.27% | 0.00% | 97.73% | 1.0000 | 44 | 0 | 0 |
| generated_mux_tree_16 | compress2rs | 0 | 0 | 8 | 8 | 0.00% | 0.00% | 100.00% | 1.0000 | 8 | 0 | 0 |
| generated_mux_tree_16 | dc2 | 0 | 0 | 2 | 2 | 0.00% | 0.00% | 100.00% | 1.0000 | 2 | 0 | 0 |
| generated_mux_tree_16 | refactor | 1 | 0 | 43 | 44 | 2.27% | 0.00% | 97.73% | 1.0000 | 44 | 0 | 0 |
| generated_mux_tree_16 | refactor_z | 2 | 0 | 30 | 32 | 6.25% | 0.00% | 93.75% | 1.0000 | 32 | 0 | 0 |
| generated_mux_tree_16 | resub | 1 | 0 | 43 | 44 | 2.27% | 0.00% | 97.73% | 1.0000 | 44 | 0 | 0 |
| generated_mux_tree_16 | resyn | 1 | 0 | 9 | 10 | 10.00% | 0.00% | 90.00% | 1.0000 | 10 | 0 | 0 |
| generated_mux_tree_16 | resyn2 | 0 | 0 | 8 | 8 | 0.00% | 0.00% | 100.00% | 1.0000 | 8 | 0 | 0 |
| generated_mux_tree_16 | resyn2_like | 0 | 0 | 8 | 8 | 0.00% | 0.00% | 100.00% | 1.0000 | 8 | 0 | 0 |
| generated_mux_tree_16 | rewrite | 1 | 0 | 43 | 44 | 2.27% | 0.00% | 97.73% | 1.0000 | 44 | 0 | 0 |
| generated_mux_tree_16 | rewrite_z | 1 | 0 | 13 | 14 | 7.14% | 0.00% | 92.86% | 1.0000 | 14 | 0 | 0 |
| generated_mux_tree_4 | balance | 1 | 0 | 7 | 8 | 12.50% | 0.00% | 87.50% | 1.0000 | 8 | 0 | 0 |
| generated_mux_tree_4 | dc2 | 1 | 0 | 4 | 5 | 20.00% | 0.00% | 80.00% | 1.0000 | 5 | 0 | 0 |
| generated_mux_tree_4 | refactor | 1 | 0 | 7 | 8 | 12.50% | 0.00% | 87.50% | 1.0000 | 8 | 0 | 0 |
| generated_mux_tree_4 | resub | 1 | 0 | 7 | 8 | 12.50% | 0.00% | 87.50% | 1.0000 | 8 | 0 | 0 |
| generated_mux_tree_4 | resyn | 1 | 0 | 1 | 2 | 50.00% | 0.00% | 50.00% | 1.0000 | 2 | 0 | 0 |
| generated_mux_tree_4 | rewrite | 1 | 0 | 7 | 8 | 12.50% | 0.00% | 87.50% | 1.0000 | 8 | 0 | 0 |
| generated_mux_tree_4 | rewrite_z | 1 | 0 | 1 | 2 | 50.00% | 0.00% | 50.00% | 1.0000 | 2 | 0 | 0 |
| generated_mux_tree_8 | balance | 1 | 0 | 19 | 20 | 5.00% | 0.00% | 95.00% | 1.0000 | 20 | 0 | 0 |
| generated_mux_tree_8 | compress2rs | 0 | 0 | 8 | 8 | 0.00% | 0.00% | 100.00% | 1.0000 | 8 | 0 | 0 |
| generated_mux_tree_8 | refactor | 1 | 0 | 19 | 20 | 5.00% | 0.00% | 95.00% | 1.0000 | 20 | 0 | 0 |
| generated_mux_tree_8 | refactor_z | 0 | 0 | 12 | 12 | 0.00% | 0.00% | 100.00% | 1.0000 | 12 | 0 | 0 |
| generated_mux_tree_8 | resub | 1 | 0 | 19 | 20 | 5.00% | 0.00% | 95.00% | 1.0000 | 20 | 0 | 0 |
| generated_mux_tree_8 | resyn | 1 | 0 | 7 | 8 | 12.50% | 0.00% | 87.50% | 1.0000 | 8 | 0 | 0 |
| generated_mux_tree_8 | resyn2 | 0 | 0 | 8 | 8 | 0.00% | 0.00% | 100.00% | 1.0000 | 8 | 0 | 0 |
| generated_mux_tree_8 | resyn2_like | 0 | 0 | 8 | 8 | 0.00% | 0.00% | 100.00% | 1.0000 | 8 | 0 | 0 |
| generated_mux_tree_8 | rewrite | 1 | 0 | 19 | 20 | 5.00% | 0.00% | 95.00% | 1.0000 | 20 | 0 | 0 |
| generated_mux_tree_8 | rewrite_z | 1 | 0 | 7 | 8 | 12.50% | 0.00% | 87.50% | 1.0000 | 8 | 0 | 0 |
| generated_random_medium | balance | 17 | 0 | 0 | 17 | 100.00% | 0.00% | 0.00% | 1.0000 | 17 | 0 | 0 |
| generated_random_medium | compress2rs | 5 | 1 | 3 | 9 | 55.56% | 11.11% | 33.33% | 0.9613 | 9 | 0 | 0 |
| generated_random_medium | dc2 | 3 | 0 | 6 | 9 | 33.33% | 0.00% | 66.67% | 1.0000 | 9 | 0 | 0 |
| generated_random_medium | refactor | 17 | 0 | 0 | 17 | 100.00% | 0.00% | 0.00% | 1.0000 | 17 | 0 | 0 |
| generated_random_medium | refactor_z | 8 | 0 | 6 | 14 | 57.14% | 0.00% | 42.86% | 0.9446 | 14 | 0 | 0 |
| generated_random_medium | resub | 17 | 0 | 0 | 17 | 100.00% | 0.00% | 0.00% | 1.0000 | 17 | 0 | 0 |
| generated_random_medium | resyn | 5 | 0 | 6 | 11 | 45.45% | 0.00% | 54.55% | 0.9760 | 11 | 0 | 0 |
| generated_random_medium | resyn2 | 5 | 1 | 3 | 9 | 55.56% | 11.11% | 33.33% | 0.9613 | 9 | 0 | 0 |
| generated_random_medium | resyn2_like | 5 | 1 | 3 | 9 | 55.56% | 11.11% | 33.33% | 0.9613 | 9 | 0 | 0 |
| generated_random_medium | rewrite | 17 | 0 | 0 | 17 | 100.00% | 0.00% | 0.00% | 1.0000 | 17 | 0 | 0 |
| generated_random_medium | rewrite_z | 9 | 0 | 3 | 12 | 75.00% | 0.00% | 25.00% | 0.9677 | 12 | 0 | 0 |
| generated_xor_chain_16 | balance | 44 | 0 | 0 | 44 | 100.00% | 0.00% | 0.00% | 1.0000 | 44 | 0 | 0 |
| generated_xor_chain_16 | refactor | 44 | 0 | 0 | 44 | 100.00% | 0.00% | 0.00% | 1.0000 | 44 | 0 | 0 |
| generated_xor_chain_16 | refactor_z | 41 | 0 | 0 | 41 | 100.00% | 0.00% | 0.00% | 1.0000 | 41 | 0 | 0 |
| generated_xor_chain_16 | resub | 44 | 0 | 0 | 44 | 100.00% | 0.00% | 0.00% | 1.0000 | 44 | 0 | 0 |
| generated_xor_chain_16 | resyn | 3 | 0 | 0 | 3 | 100.00% | 0.00% | 0.00% | 1.0000 | 3 | 0 | 0 |
| generated_xor_chain_16 | rewrite | 44 | 0 | 0 | 44 | 100.00% | 0.00% | 0.00% | 1.0000 | 44 | 0 | 0 |
| generated_xor_chain_16 | rewrite_z | 3 | 0 | 0 | 3 | 100.00% | 0.00% | 0.00% | 1.0000 | 3 | 0 | 0 |
| generated_xor_chain_32 | balance | 92 | 0 | 0 | 92 | 100.00% | 0.00% | 0.00% | 1.0000 | 92 | 0 | 0 |
| generated_xor_chain_32 | refactor | 92 | 0 | 0 | 92 | 100.00% | 0.00% | 0.00% | 1.0000 | 92 | 0 | 0 |
| generated_xor_chain_32 | refactor_z | 89 | 0 | 0 | 89 | 100.00% | 0.00% | 0.00% | 1.0000 | 89 | 0 | 0 |
| generated_xor_chain_32 | resub | 92 | 0 | 0 | 92 | 100.00% | 0.00% | 0.00% | 1.0000 | 92 | 0 | 0 |
| generated_xor_chain_32 | resyn | 3 | 0 | 0 | 3 | 100.00% | 0.00% | 0.00% | 1.0000 | 3 | 0 | 0 |
| generated_xor_chain_32 | rewrite | 92 | 0 | 0 | 92 | 100.00% | 0.00% | 0.00% | 1.0000 | 92 | 0 | 0 |
| generated_xor_chain_32 | rewrite_z | 3 | 0 | 0 | 3 | 100.00% | 0.00% | 0.00% | 1.0000 | 3 | 0 | 0 |
| generated_xor_chain_8 | balance | 20 | 0 | 0 | 20 | 100.00% | 0.00% | 0.00% | 1.0000 | 20 | 0 | 0 |
| generated_xor_chain_8 | refactor | 20 | 0 | 0 | 20 | 100.00% | 0.00% | 0.00% | 1.0000 | 20 | 0 | 0 |
| generated_xor_chain_8 | refactor_z | 17 | 0 | 0 | 17 | 100.00% | 0.00% | 0.00% | 1.0000 | 17 | 0 | 0 |
| generated_xor_chain_8 | resub | 20 | 0 | 0 | 20 | 100.00% | 0.00% | 0.00% | 1.0000 | 20 | 0 | 0 |
| generated_xor_chain_8 | resyn | 3 | 0 | 0 | 3 | 100.00% | 0.00% | 0.00% | 1.0000 | 3 | 0 | 0 |
| generated_xor_chain_8 | rewrite | 20 | 0 | 0 | 20 | 100.00% | 0.00% | 0.00% | 1.0000 | 20 | 0 | 0 |
| generated_xor_chain_8 | rewrite_z | 3 | 0 | 0 | 3 | 100.00% | 0.00% | 0.00% | 1.0000 | 3 | 0 | 0 |
| majority3 | balance | 0 | 1 | 3 | 4 | 0.00% | 25.00% | 75.00% | 0.9656 | 4 | 0 | 0 |
| majority3 | compress2rs | 1 | 0 | 1 | 2 | 50.00% | 0.00% | 50.00% | 0.9312 | 2 | 0 | 0 |
| majority3 | dc2 | 0 | 0 | 2 | 2 | 0.00% | 0.00% | 100.00% | 0.9312 | 2 | 0 | 0 |
| majority3 | refactor | 0 | 0 | 1 | 1 | 0.00% | 0.00% | 100.00% | 1.0000 | 1 | 0 | 0 |
| majority3 | refactor_z | 0 | 0 | 2 | 2 | 0.00% | 0.00% | 100.00% | 0.9312 | 2 | 0 | 0 |
| majority3 | resub | 1 | 0 | 3 | 4 | 25.00% | 0.00% | 75.00% | 1.0000 | 4 | 0 | 0 |
| majority3 | resyn | 0 | 1 | 3 | 4 | 0.00% | 25.00% | 75.00% | 0.9656 | 4 | 0 | 0 |
| majority3 | resyn2 | 1 | 0 | 1 | 2 | 50.00% | 0.00% | 50.00% | 0.9312 | 2 | 0 | 0 |
| majority3 | resyn2_like | 1 | 0 | 1 | 2 | 50.00% | 0.00% | 50.00% | 0.9312 | 2 | 0 | 0 |
| majority3 | rewrite | 1 | 0 | 3 | 4 | 25.00% | 0.00% | 75.00% | 1.0000 | 4 | 0 | 0 |
| majority3 | rewrite_z | 1 | 1 | 2 | 4 | 25.00% | 25.00% | 50.00% | 0.9656 | 4 | 0 | 0 |
| mux2 | balance | 2 | 0 | 0 | 2 | 100.00% | 0.00% | 0.00% | 1.0000 | 2 | 0 | 0 |
| mux2 | refactor | 2 | 0 | 0 | 2 | 100.00% | 0.00% | 0.00% | 1.0000 | 2 | 0 | 0 |
| mux2 | resub | 2 | 0 | 0 | 2 | 100.00% | 0.00% | 0.00% | 1.0000 | 2 | 0 | 0 |
| mux2 | resyn | 2 | 0 | 0 | 2 | 100.00% | 0.00% | 0.00% | 1.0000 | 2 | 0 | 0 |
| mux2 | rewrite | 2 | 0 | 0 | 2 | 100.00% | 0.00% | 0.00% | 1.0000 | 2 | 0 | 0 |
| mux2 | rewrite_z | 2 | 0 | 0 | 2 | 100.00% | 0.00% | 0.00% | 1.0000 | 2 | 0 | 0 |
| real_hand_written_comparator_4 | balance | 1 | 0 | 12 | 13 | 7.69% | 0.00% | 92.31% | 1.0000 | 13 | 0 | 0 |
| real_hand_written_comparator_4 | compress2rs | 1 | 0 | 12 | 13 | 7.69% | 0.00% | 92.31% | 1.0000 | 13 | 0 | 0 |
| real_hand_written_comparator_4 | dc2 | 0 | 0 | 10 | 10 | 0.00% | 0.00% | 100.00% | 1.0000 | 10 | 0 | 0 |
| real_hand_written_comparator_4 | refactor | 2 | 0 | 12 | 14 | 14.29% | 0.00% | 85.71% | 1.0000 | 14 | 0 | 0 |
| real_hand_written_comparator_4 | refactor_z | 0 | 0 | 13 | 13 | 0.00% | 0.00% | 100.00% | 1.0000 | 13 | 0 | 0 |
| real_hand_written_comparator_4 | resub | 2 | 0 | 12 | 14 | 14.29% | 0.00% | 85.71% | 1.0000 | 14 | 0 | 0 |
| real_hand_written_comparator_4 | resyn | 1 | 0 | 3 | 4 | 25.00% | 0.00% | 75.00% | 1.0000 | 4 | 0 | 0 |
| real_hand_written_comparator_4 | resyn2 | 1 | 0 | 12 | 13 | 7.69% | 0.00% | 92.31% | 1.0000 | 13 | 0 | 0 |
| real_hand_written_comparator_4 | resyn2_like | 1 | 0 | 12 | 13 | 7.69% | 0.00% | 92.31% | 1.0000 | 13 | 0 | 0 |
| real_hand_written_comparator_4 | rewrite | 2 | 0 | 12 | 14 | 14.29% | 0.00% | 85.71% | 1.0000 | 14 | 0 | 0 |
| real_hand_written_comparator_4 | rewrite_z | 0 | 0 | 9 | 9 | 0.00% | 0.00% | 100.00% | 1.0000 | 9 | 0 | 0 |
| real_hand_written_full_adder | balance | 5 | 1 | 3 | 9 | 55.56% | 11.11% | 33.33% | 0.9847 | 9 | 0 | 0 |
| real_hand_written_full_adder | compress2rs | 2 | 0 | 1 | 3 | 66.67% | 0.00% | 33.33% | 1.0000 | 3 | 0 | 0 |
| real_hand_written_full_adder | dc2 | 0 | 0 | 4 | 4 | 0.00% | 0.00% | 100.00% | 0.9062 | 4 | 0 | 0 |
| real_hand_written_full_adder | refactor | 3 | 0 | 3 | 6 | 50.00% | 0.00% | 50.00% | 1.0000 | 6 | 0 | 0 |
| real_hand_written_full_adder | refactor_z | 2 | 0 | 3 | 5 | 40.00% | 0.00% | 60.00% | 0.9725 | 5 | 0 | 0 |
| real_hand_written_full_adder | resub | 6 | 0 | 3 | 9 | 66.67% | 0.00% | 33.33% | 1.0000 | 9 | 0 | 0 |
| real_hand_written_full_adder | resyn | 5 | 1 | 3 | 9 | 55.56% | 11.11% | 33.33% | 0.9847 | 9 | 0 | 0 |
| real_hand_written_full_adder | resyn2 | 3 | 0 | 2 | 5 | 60.00% | 0.00% | 40.00% | 0.9725 | 5 | 0 | 0 |
| real_hand_written_full_adder | resyn2_like | 3 | 0 | 2 | 5 | 60.00% | 0.00% | 40.00% | 0.9725 | 5 | 0 | 0 |
| real_hand_written_full_adder | rewrite | 6 | 0 | 3 | 9 | 66.67% | 0.00% | 33.33% | 1.0000 | 9 | 0 | 0 |
| real_hand_written_full_adder | rewrite_z | 6 | 1 | 2 | 9 | 66.67% | 11.11% | 22.22% | 0.9847 | 9 | 0 | 0 |
| real_hand_written_mux_4to1 | balance | 2 | 0 | 4 | 6 | 33.33% | 0.00% | 66.67% | 1.0000 | 6 | 0 | 0 |
| real_hand_written_mux_4to1 | resub | 1 | 0 | 9 | 10 | 10.00% | 0.00% | 90.00% | 1.0000 | 10 | 0 | 0 |
| real_hand_written_mux_4to1 | resyn | 0 | 0 | 2 | 2 | 0.00% | 0.00% | 100.00% | 0.8625 | 2 | 0 | 0 |
| real_hand_written_mux_4to1 | rewrite | 0 | 0 | 2 | 2 | 0.00% | 0.00% | 100.00% | 0.8625 | 2 | 0 | 0 |
| real_hand_written_mux_4to1 | rewrite_z | 0 | 0 | 2 | 2 | 0.00% | 0.00% | 100.00% | 0.8625 | 2 | 0 | 0 |
| real_hand_written_parity_8 | balance | 20 | 0 | 0 | 20 | 100.00% | 0.00% | 0.00% | 1.0000 | 20 | 0 | 0 |
| real_hand_written_parity_8 | compress2rs | 3 | 0 | 2 | 5 | 60.00% | 0.00% | 40.00% | 1.0000 | 5 | 0 | 0 |
| real_hand_written_parity_8 | dc2 | 1 | 1 | 6 | 8 | 12.50% | 12.50% | 75.00% | 0.9656 | 8 | 0 | 0 |
| real_hand_written_parity_8 | refactor | 20 | 0 | 0 | 20 | 100.00% | 0.00% | 0.00% | 1.0000 | 20 | 0 | 0 |
| real_hand_written_parity_8 | refactor_z | 8 | 0 | 0 | 8 | 100.00% | 0.00% | 0.00% | 1.0000 | 8 | 0 | 0 |
| real_hand_written_parity_8 | resub | 20 | 0 | 0 | 20 | 100.00% | 0.00% | 0.00% | 1.0000 | 20 | 0 | 0 |
| real_hand_written_parity_8 | resyn | 15 | 0 | 2 | 17 | 88.24% | 0.00% | 11.76% | 1.0000 | 17 | 0 | 0 |
| real_hand_written_parity_8 | resyn2 | 3 | 0 | 2 | 5 | 60.00% | 0.00% | 40.00% | 1.0000 | 5 | 0 | 0 |
| real_hand_written_parity_8 | resyn2_like | 3 | 0 | 2 | 5 | 60.00% | 0.00% | 40.00% | 1.0000 | 5 | 0 | 0 |
| real_hand_written_parity_8 | rewrite | 20 | 0 | 0 | 20 | 100.00% | 0.00% | 0.00% | 1.0000 | 20 | 0 | 0 |
| real_hand_written_parity_8 | rewrite_z | 15 | 0 | 2 | 17 | 88.24% | 0.00% | 11.76% | 1.0000 | 17 | 0 | 0 |
| real_hand_written_priority_enc_4 | balance | 2 | 0 | 0 | 2 | 100.00% | 0.00% | 0.00% | 1.0000 | 2 | 0 | 0 |
| real_hand_written_priority_enc_4 | compress2rs | 2 | 0 | 0 | 2 | 100.00% | 0.00% | 0.00% | 1.0000 | 2 | 0 | 0 |
| real_hand_written_priority_enc_4 | dc2 | 1 | 0 | 0 | 1 | 100.00% | 0.00% | 0.00% | 1.0000 | 1 | 0 | 0 |
| real_hand_written_priority_enc_4 | refactor | 2 | 0 | 0 | 2 | 100.00% | 0.00% | 0.00% | 1.0000 | 2 | 0 | 0 |
| real_hand_written_priority_enc_4 | refactor_z | 2 | 0 | 0 | 2 | 100.00% | 0.00% | 0.00% | 1.0000 | 2 | 0 | 0 |
| real_hand_written_priority_enc_4 | resub | 2 | 0 | 0 | 2 | 100.00% | 0.00% | 0.00% | 1.0000 | 2 | 0 | 0 |
| real_hand_written_priority_enc_4 | resyn | 2 | 0 | 0 | 2 | 100.00% | 0.00% | 0.00% | 1.0000 | 2 | 0 | 0 |
| real_hand_written_priority_enc_4 | resyn2 | 2 | 0 | 0 | 2 | 100.00% | 0.00% | 0.00% | 1.0000 | 2 | 0 | 0 |
| real_hand_written_priority_enc_4 | resyn2_like | 2 | 0 | 0 | 2 | 100.00% | 0.00% | 0.00% | 1.0000 | 2 | 0 | 0 |
| real_hand_written_priority_enc_4 | rewrite | 2 | 0 | 0 | 2 | 100.00% | 0.00% | 0.00% | 1.0000 | 2 | 0 | 0 |
| real_hand_written_priority_enc_4 | rewrite_z | 2 | 0 | 0 | 2 | 100.00% | 0.00% | 0.00% | 1.0000 | 2 | 0 | 0 |
| toy_and_or | balance | 2 | 0 | 0 | 2 | 100.00% | 0.00% | 0.00% | 1.0000 | 2 | 0 | 0 |
| toy_and_or | compress2rs | 2 | 0 | 0 | 2 | 100.00% | 0.00% | 0.00% | 1.0000 | 2 | 0 | 0 |
| toy_and_or | dc2 | 2 | 0 | 0 | 2 | 100.00% | 0.00% | 0.00% | 1.0000 | 2 | 0 | 0 |
| toy_and_or | refactor | 2 | 0 | 0 | 2 | 100.00% | 0.00% | 0.00% | 1.0000 | 2 | 0 | 0 |
| toy_and_or | refactor_z | 2 | 0 | 0 | 2 | 100.00% | 0.00% | 0.00% | 1.0000 | 2 | 0 | 0 |
| toy_and_or | resub | 2 | 0 | 0 | 2 | 100.00% | 0.00% | 0.00% | 1.0000 | 2 | 0 | 0 |
| toy_and_or | resyn | 2 | 0 | 0 | 2 | 100.00% | 0.00% | 0.00% | 1.0000 | 2 | 0 | 0 |
| toy_and_or | resyn2 | 2 | 0 | 0 | 2 | 100.00% | 0.00% | 0.00% | 1.0000 | 2 | 0 | 0 |
| toy_and_or | resyn2_like | 2 | 0 | 0 | 2 | 100.00% | 0.00% | 0.00% | 1.0000 | 2 | 0 | 0 |
| toy_and_or | rewrite | 2 | 0 | 0 | 2 | 100.00% | 0.00% | 0.00% | 1.0000 | 2 | 0 | 0 |
| toy_and_or | rewrite_z | 2 | 0 | 0 | 2 | 100.00% | 0.00% | 0.00% | 1.0000 | 2 | 0 | 0 |
| xor_chain | balance | 8 | 0 | 0 | 8 | 100.00% | 0.00% | 0.00% | 1.0000 | 8 | 0 | 0 |
| xor_chain | refactor | 8 | 0 | 0 | 8 | 100.00% | 0.00% | 0.00% | 1.0000 | 8 | 0 | 0 |
| xor_chain | refactor_z | 5 | 0 | 0 | 5 | 100.00% | 0.00% | 0.00% | 1.0000 | 5 | 0 | 0 |
| xor_chain | resub | 8 | 0 | 0 | 8 | 100.00% | 0.00% | 0.00% | 1.0000 | 8 | 0 | 0 |
| xor_chain | resyn | 3 | 0 | 0 | 3 | 100.00% | 0.00% | 0.00% | 1.0000 | 3 | 0 | 0 |
| xor_chain | rewrite | 8 | 0 | 0 | 8 | 100.00% | 0.00% | 0.00% | 1.0000 | 8 | 0 | 0 |
| xor_chain | rewrite_z | 3 | 0 | 0 | 3 | 100.00% | 0.00% | 0.00% | 1.0000 | 3 | 0 | 0 |

**Global totals:**

| benchmark | optimization | verified | rejected | inconclusive | total | verification_rate | rejection_rate | inconclusive_rate | avg_combined_score | direct_name_count | fingerprint_recovered | still_inconclusive |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ALL | ALL | 1688 | 20 | 1769 | 3477 | 48.55% | 0.58% | 50.88% | 0.9885 | 3477 | 0 | 0 |

## Rejected candidates

ABC found 20 candidate(s) to be **not equivalent**:

| benchmark | optimization | optimized_node | original_candidate | combined_score | abc_result |
| --- | --- | --- | --- | --- | --- |
| generated_multiplier_4 | compress2rs | new_n27 | new_n27 | 0.9656 | Networks are NOT EQUIVALENT.  Time =     0.00 sec |
| generated_multiplier_4 | dc2 | new_n27 | new_n27 | 0.9656 | Networks are NOT EQUIVALENT.  Time =     0.00 sec |
| generated_multiplier_4 | resyn | new_n27 | new_n27 | 0.9656 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn2 | new_n27 | new_n27 | 0.9656 | Networks are NOT EQUIVALENT.  Time =     0.00 sec |
| generated_multiplier_4 | resyn2_like | new_n27 | new_n27 | 0.9656 | Networks are NOT EQUIVALENT.  Time =     0.00 sec |
| generated_multiplier_4 | rewrite | new_n43 | new_n43 | 0.9070 | Networks are NOT EQUIVALENT.  Time =     0.00 sec |
| generated_multiplier_4 | rewrite_z | new_n27 | new_n27 | 0.9656 | Networks are NOT EQUIVALENT.  Time =     0.00 sec |
| generated_multiplier_4 | rewrite_z | new_n40 | new_n40 | 0.9656 | Networks are NOT EQUIVALENT.  Time =     0.00 sec |
| generated_multiplier_4 | rewrite_z | new_n70 | new_n70 | 0.9264 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | rewrite_z | new_n104 | new_n104 | 0.9527 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_random_medium | compress2rs | new_n26 | new_n26 | 0.8562 | Networks are NOT EQUIVALENT.  Time =     0.00 sec |
| generated_random_medium | resyn2 | new_n26 | new_n26 | 0.8562 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_random_medium | resyn2_like | new_n26 | new_n26 | 0.8562 | Networks are NOT EQUIVALENT.  Time =     0.00 sec |
| majority3 | balance | new_n8 | new_n8 | 0.8625 | Networks are NOT EQUIVALENT.  Time =     0.00 sec |
| majority3 | resyn | new_n8 | new_n8 | 0.8625 | Networks are NOT EQUIVALENT.  Time =     0.00 sec |
| majority3 | rewrite_z | new_n8 | new_n8 | 0.8625 | Networks are NOT EQUIVALENT.  Time =     0.00 sec |
| real_hand_written_full_adder | balance | new_n15 | new_n15 | 0.8625 | Networks are NOT EQUIVALENT.  Time =     0.00 sec |
| real_hand_written_full_adder | resyn | new_n15 | new_n15 | 0.8625 | Networks are NOT EQUIVALENT.  Time =     0.00 sec |
| real_hand_written_full_adder | rewrite_z | new_n15 | new_n15 | 0.8625 | Networks are NOT EQUIVALENT.  Time =     0.00 sec |
| real_hand_written_parity_8 | dc2 | new_n28 | new_n28 | 0.8625 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |

A rejected candidate means the simulation ranking assigned a high score to a pair that ABC proved are not logically equivalent. This shows why a formal check is necessary: simulation similarity alone is not a proof of equivalence.

## Inconclusive candidates

1769 candidate(s) could not be formally checked.

An inconclusive result means the ABC check could not be completed. Common reasons:

- A node name appears in the candidate list but not in the BLIF file (ABC renames nodes during optimization, so the original and optimized variants may use different names for corresponding nodes).
- A BLIF file was missing.
- ABC timed out.
- Another preparation error occurred.

Inconclusive cases do not mean the candidate is wrong — they mean the current prototype cannot complete the check.

**Inconclusive counts by benchmark/optimization:**

| benchmark | optimization | inconclusive_count |
| --- | --- | --- |
| generated_adder_4 | compress2rs | 11 |
| generated_adder_4 | dc2 | 11 |
| generated_adder_4 | refactor | 11 |
| generated_adder_4 | refactor_z | 11 |
| generated_adder_4 | resyn | 10 |
| generated_adder_4 | resyn2 | 11 |
| generated_adder_4 | resyn2_like | 11 |
| generated_adder_4 | rewrite | 10 |
| generated_adder_4 | rewrite_z | 10 |
| generated_adder_8 | compress2rs | 23 |
| generated_adder_8 | dc2 | 23 |
| generated_adder_8 | refactor | 23 |
| generated_adder_8 | refactor_z | 23 |
| generated_adder_8 | resyn | 34 |
| generated_adder_8 | resyn2 | 23 |
| generated_adder_8 | resyn2_like | 23 |
| generated_adder_8 | rewrite | 34 |
| generated_adder_8 | rewrite_z | 34 |
| generated_multiplier_2 | compress2rs | 1 |
| generated_multiplier_2 | refactor | 1 |
| generated_multiplier_2 | refactor_z | 1 |
| generated_multiplier_2 | resyn2 | 1 |
| generated_multiplier_2 | resyn2_like | 1 |
| generated_multiplier_4 | balance | 16 |
| generated_multiplier_4 | compress2rs | 68 |
| generated_multiplier_4 | dc2 | 74 |
| generated_multiplier_4 | refactor | 89 |
| generated_multiplier_4 | refactor_z | 88 |
| generated_multiplier_4 | resub | 83 |
| generated_multiplier_4 | resyn | 74 |
| generated_multiplier_4 | resyn2 | 74 |
| generated_multiplier_4 | resyn2_like | 74 |
| generated_multiplier_4 | rewrite | 67 |
| generated_multiplier_4 | rewrite_z | 76 |
| generated_mux_tree_16 | balance | 43 |
| generated_mux_tree_16 | compress2rs | 8 |
| generated_mux_tree_16 | dc2 | 2 |
| generated_mux_tree_16 | refactor | 43 |
| generated_mux_tree_16 | refactor_z | 30 |
| generated_mux_tree_16 | resub | 43 |
| generated_mux_tree_16 | resyn | 9 |
| generated_mux_tree_16 | resyn2 | 8 |
| generated_mux_tree_16 | resyn2_like | 8 |
| generated_mux_tree_16 | rewrite | 43 |
| generated_mux_tree_16 | rewrite_z | 13 |
| generated_mux_tree_4 | balance | 7 |
| generated_mux_tree_4 | dc2 | 4 |
| generated_mux_tree_4 | refactor | 7 |
| generated_mux_tree_4 | resub | 7 |
| generated_mux_tree_4 | resyn | 1 |
| generated_mux_tree_4 | rewrite | 7 |
| generated_mux_tree_4 | rewrite_z | 1 |
| generated_mux_tree_8 | balance | 19 |
| generated_mux_tree_8 | compress2rs | 8 |
| generated_mux_tree_8 | refactor | 19 |
| generated_mux_tree_8 | refactor_z | 12 |
| generated_mux_tree_8 | resub | 19 |
| generated_mux_tree_8 | resyn | 7 |
| generated_mux_tree_8 | resyn2 | 8 |
| generated_mux_tree_8 | resyn2_like | 8 |
| generated_mux_tree_8 | rewrite | 19 |
| generated_mux_tree_8 | rewrite_z | 7 |
| generated_random_medium | compress2rs | 3 |
| generated_random_medium | dc2 | 6 |
| generated_random_medium | refactor_z | 6 |
| generated_random_medium | resyn | 6 |
| generated_random_medium | resyn2 | 3 |
| generated_random_medium | resyn2_like | 3 |
| generated_random_medium | rewrite_z | 3 |
| majority3 | balance | 3 |
| majority3 | compress2rs | 1 |
| majority3 | dc2 | 2 |
| majority3 | refactor | 1 |
| majority3 | refactor_z | 2 |
| majority3 | resub | 3 |
| majority3 | resyn | 3 |
| majority3 | resyn2 | 1 |
| majority3 | resyn2_like | 1 |
| majority3 | rewrite | 3 |
| majority3 | rewrite_z | 2 |
| real_hand_written_comparator_4 | balance | 12 |
| real_hand_written_comparator_4 | compress2rs | 12 |
| real_hand_written_comparator_4 | dc2 | 10 |
| real_hand_written_comparator_4 | refactor | 12 |
| real_hand_written_comparator_4 | refactor_z | 13 |
| real_hand_written_comparator_4 | resub | 12 |
| real_hand_written_comparator_4 | resyn | 3 |
| real_hand_written_comparator_4 | resyn2 | 12 |
| real_hand_written_comparator_4 | resyn2_like | 12 |
| real_hand_written_comparator_4 | rewrite | 12 |
| real_hand_written_comparator_4 | rewrite_z | 9 |
| real_hand_written_full_adder | balance | 3 |
| real_hand_written_full_adder | compress2rs | 1 |
| real_hand_written_full_adder | dc2 | 4 |
| real_hand_written_full_adder | refactor | 3 |
| real_hand_written_full_adder | refactor_z | 3 |
| real_hand_written_full_adder | resub | 3 |
| real_hand_written_full_adder | resyn | 3 |
| real_hand_written_full_adder | resyn2 | 2 |
| real_hand_written_full_adder | resyn2_like | 2 |
| real_hand_written_full_adder | rewrite | 3 |
| real_hand_written_full_adder | rewrite_z | 2 |
| real_hand_written_mux_4to1 | balance | 4 |
| real_hand_written_mux_4to1 | resub | 9 |
| real_hand_written_mux_4to1 | resyn | 2 |
| real_hand_written_mux_4to1 | rewrite | 2 |
| real_hand_written_mux_4to1 | rewrite_z | 2 |
| real_hand_written_parity_8 | compress2rs | 2 |
| real_hand_written_parity_8 | dc2 | 6 |
| real_hand_written_parity_8 | resyn | 2 |
| real_hand_written_parity_8 | resyn2 | 2 |
| real_hand_written_parity_8 | resyn2_like | 2 |
| real_hand_written_parity_8 | rewrite_z | 2 |

## Main interpretation

The SAT refinement step confirms that the simulation-based ranking method is useful but not a proof by itself. Most high-confidence candidates were formally verified by ABC's equivalence checker, which shows the scoring formula produces meaningful rankings. The rejected candidate demonstrates why a formal check is necessary: a high simulation similarity score is not sufficient to guarantee equivalence, and ABC can find a concrete counterexample where the two nodes disagree. Inconclusive cases reveal current prototype limitations, especially around node-name stability between the original and optimized BLIF files and the fact that ABC assigns new internal names during optimization. Reducing the inconclusive rate is the most direct path to making the refinement step more useful in practice.
