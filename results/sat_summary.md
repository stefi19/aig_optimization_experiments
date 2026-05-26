# SAT Refinement Summary

## Overall result

- **Total candidates checked:** 425
- **Verified by ABC:** 0
- **Rejected by ABC:** 20
- **Inconclusive:** 405
- **Verification rate:** 0.0%

## Match category breakdown

Following Carmine's feedback, candidates are now separated into two categories:

- **`exact_anchor`**: the optimized node and original candidate already had identical Boolean simulation signatures before this SAT check. ABC verifying these is a useful sanity check, but it does **not** represent a newly-recovered correspondence — the match was already known.

- **`non_exact_candidate`**: the optimized node and original candidate did **not** have the same simulation signature. ABC verifying one of these is a genuine refinement result — it means the scoring formula identified a real correspondence that exact signature matching missed.

**non_exact_candidate** (425 candidates): verified 0, rejected 20, inconclusive 405 (verification rate 0.0%)

**exact_anchor**: no candidates.

> **Important:** only `non_exact_candidate` verified results should be interpreted as SAT refinement recovering a correspondence that exact matching missed. `exact_anchor` verified results are expected and do not add new information.

## Recovery method breakdown

Each completed check is tagged with the method used to locate the node in the BLIF file:

- **direct** (425): node name found in the BLIF without any fallback
- **fingerprint** (0): node name was missing; recovered via a unique SHA-256 fingerprint match
- **still inconclusive** (0): node could not be resolved (name missing and fingerprint ambiguous/absent, missing BLIF, ABC timeout, etc.)

## Summary by benchmark and optimization

| benchmark | optimization | verified | rejected | inconclusive | total | verification_rate | rejection_rate | inconclusive_rate | avg_combined_score | direct_name_count | fingerprint_recovered | still_inconclusive |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| generated_multiplier_4 | balance | 0 | 0 | 8 | 8 | 0.00% | 0.00% | 100.00% | 0.9586 | 8 | 0 | 0 |
| generated_multiplier_4 | compress2rs | 0 | 1 | 44 | 45 | 0.00% | 2.22% | 97.78% | 0.9252 | 45 | 0 | 0 |
| generated_multiplier_4 | dc2 | 0 | 1 | 50 | 51 | 0.00% | 1.96% | 98.04% | 0.9224 | 51 | 0 | 0 |
| generated_multiplier_4 | refactor | 0 | 0 | 17 | 17 | 0.00% | 0.00% | 100.00% | 0.9169 | 17 | 0 | 0 |
| generated_multiplier_4 | refactor_z | 0 | 0 | 35 | 35 | 0.00% | 0.00% | 100.00% | 0.9271 | 35 | 0 | 0 |
| generated_multiplier_4 | resub | 0 | 0 | 5 | 5 | 0.00% | 0.00% | 100.00% | 0.9459 | 5 | 0 | 0 |
| generated_multiplier_4 | resyn | 0 | 1 | 48 | 49 | 0.00% | 2.04% | 97.96% | 0.9235 | 49 | 0 | 0 |
| generated_multiplier_4 | resyn2 | 0 | 1 | 48 | 49 | 0.00% | 2.04% | 97.96% | 0.9235 | 49 | 0 | 0 |
| generated_multiplier_4 | resyn2_like | 0 | 1 | 48 | 49 | 0.00% | 2.04% | 97.96% | 0.9235 | 49 | 0 | 0 |
| generated_multiplier_4 | rewrite | 0 | 1 | 24 | 25 | 0.00% | 4.00% | 96.00% | 0.9255 | 25 | 0 | 0 |
| generated_multiplier_4 | rewrite_z | 0 | 4 | 43 | 47 | 0.00% | 8.51% | 91.49% | 0.9250 | 47 | 0 | 0 |
| generated_random_medium | compress2rs | 0 | 1 | 2 | 3 | 0.00% | 33.33% | 66.67% | 0.8838 | 3 | 0 | 0 |
| generated_random_medium | refactor_z | 0 | 0 | 6 | 6 | 0.00% | 0.00% | 100.00% | 0.8708 | 6 | 0 | 0 |
| generated_random_medium | resyn | 0 | 0 | 2 | 2 | 0.00% | 0.00% | 100.00% | 0.8681 | 2 | 0 | 0 |
| generated_random_medium | resyn2 | 0 | 1 | 2 | 3 | 0.00% | 33.33% | 66.67% | 0.8838 | 3 | 0 | 0 |
| generated_random_medium | resyn2_like | 0 | 1 | 2 | 3 | 0.00% | 33.33% | 66.67% | 0.8838 | 3 | 0 | 0 |
| generated_random_medium | rewrite_z | 0 | 0 | 3 | 3 | 0.00% | 0.00% | 100.00% | 0.8708 | 3 | 0 | 0 |
| majority3 | balance | 0 | 1 | 0 | 1 | 0.00% | 100.00% | 0.00% | 0.8625 | 1 | 0 | 0 |
| majority3 | compress2rs | 0 | 0 | 1 | 1 | 0.00% | 0.00% | 100.00% | 0.8625 | 1 | 0 | 0 |
| majority3 | dc2 | 0 | 0 | 1 | 1 | 0.00% | 0.00% | 100.00% | 0.8625 | 1 | 0 | 0 |
| majority3 | refactor_z | 0 | 0 | 1 | 1 | 0.00% | 0.00% | 100.00% | 0.8625 | 1 | 0 | 0 |
| majority3 | resyn | 0 | 1 | 0 | 1 | 0.00% | 100.00% | 0.00% | 0.8625 | 1 | 0 | 0 |
| majority3 | resyn2 | 0 | 0 | 1 | 1 | 0.00% | 0.00% | 100.00% | 0.8625 | 1 | 0 | 0 |
| majority3 | resyn2_like | 0 | 0 | 1 | 1 | 0.00% | 0.00% | 100.00% | 0.8625 | 1 | 0 | 0 |
| majority3 | rewrite_z | 0 | 1 | 0 | 1 | 0.00% | 100.00% | 0.00% | 0.8625 | 1 | 0 | 0 |
| real_hand_written_full_adder | balance | 0 | 1 | 0 | 1 | 0.00% | 100.00% | 0.00% | 0.8625 | 1 | 0 | 0 |
| real_hand_written_full_adder | dc2 | 0 | 0 | 3 | 3 | 0.00% | 0.00% | 100.00% | 0.8750 | 3 | 0 | 0 |
| real_hand_written_full_adder | refactor_z | 0 | 0 | 1 | 1 | 0.00% | 0.00% | 100.00% | 0.8625 | 1 | 0 | 0 |
| real_hand_written_full_adder | resyn | 0 | 1 | 0 | 1 | 0.00% | 100.00% | 0.00% | 0.8625 | 1 | 0 | 0 |
| real_hand_written_full_adder | resyn2 | 0 | 0 | 1 | 1 | 0.00% | 0.00% | 100.00% | 0.8625 | 1 | 0 | 0 |
| real_hand_written_full_adder | resyn2_like | 0 | 0 | 1 | 1 | 0.00% | 0.00% | 100.00% | 0.8625 | 1 | 0 | 0 |
| real_hand_written_full_adder | rewrite_z | 0 | 1 | 0 | 1 | 0.00% | 100.00% | 0.00% | 0.8625 | 1 | 0 | 0 |
| real_hand_written_mux_4to1 | resyn | 0 | 0 | 2 | 2 | 0.00% | 0.00% | 100.00% | 0.8625 | 2 | 0 | 0 |
| real_hand_written_mux_4to1 | rewrite | 0 | 0 | 2 | 2 | 0.00% | 0.00% | 100.00% | 0.8625 | 2 | 0 | 0 |
| real_hand_written_mux_4to1 | rewrite_z | 0 | 0 | 2 | 2 | 0.00% | 0.00% | 100.00% | 0.8625 | 2 | 0 | 0 |
| real_hand_written_parity_8 | dc2 | 0 | 1 | 1 | 2 | 0.00% | 50.00% | 50.00% | 0.8625 | 2 | 0 | 0 |

**Global totals:**

| benchmark | optimization | verified | rejected | inconclusive | total | verification_rate | rejection_rate | inconclusive_rate | avg_combined_score | direct_name_count | fingerprint_recovered | still_inconclusive |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ALL | ALL | 0 | 20 | 405 | 425 | 0.00% | 4.71% | 95.29% | 0.9191 | 425 | 0 | 0 |

## Rejected candidates

ABC found 20 candidate(s) to be **not equivalent**:

| benchmark | optimization | optimized_node | original_candidate | combined_score | abc_result |
| --- | --- | --- | --- | --- | --- |
| generated_multiplier_4 | compress2rs | new_n27 | new_n27 | 0.9656 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | dc2 | new_n27 | new_n27 | 0.9656 | Networks are NOT EQUIVALENT.  Time =     0.00 sec |
| generated_multiplier_4 | resyn | new_n27 | new_n27 | 0.9656 | Networks are NOT EQUIVALENT.  Time =     0.00 sec |
| generated_multiplier_4 | resyn2 | new_n27 | new_n27 | 0.9656 | Networks are NOT EQUIVALENT.  Time =     0.00 sec |
| generated_multiplier_4 | resyn2_like | new_n27 | new_n27 | 0.9656 | Networks are NOT EQUIVALENT.  Time =     0.00 sec |
| generated_multiplier_4 | rewrite | new_n43 | new_n43 | 0.9070 | Networks are NOT EQUIVALENT.  Time =     0.00 sec |
| generated_multiplier_4 | rewrite_z | new_n27 | new_n27 | 0.9656 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | rewrite_z | new_n40 | new_n40 | 0.9656 | Networks are NOT EQUIVALENT.  Time =     0.00 sec |
| generated_multiplier_4 | rewrite_z | new_n70 | new_n70 | 0.9264 | Networks are NOT EQUIVALENT.  Time =     0.00 sec |
| generated_multiplier_4 | rewrite_z | new_n104 | new_n104 | 0.9527 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_random_medium | compress2rs | new_n26 | new_n26 | 0.8562 | Networks are NOT EQUIVALENT.  Time =     0.00 sec |
| generated_random_medium | resyn2 | new_n26 | new_n26 | 0.8562 | Networks are NOT EQUIVALENT.  Time =     0.00 sec |
| generated_random_medium | resyn2_like | new_n26 | new_n26 | 0.8562 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| majority3 | balance | new_n8 | new_n8 | 0.8625 | Networks are NOT EQUIVALENT.  Time =     0.00 sec |
| majority3 | resyn | new_n8 | new_n8 | 0.8625 | Networks are NOT EQUIVALENT.  Time =     0.00 sec |
| majority3 | rewrite_z | new_n8 | new_n8 | 0.8625 | Networks are NOT EQUIVALENT.  Time =     0.00 sec |
| real_hand_written_full_adder | balance | new_n15 | new_n15 | 0.8625 | Networks are NOT EQUIVALENT.  Time =     0.00 sec |
| real_hand_written_full_adder | resyn | new_n15 | new_n15 | 0.8625 | Networks are NOT EQUIVALENT.  Time =     0.00 sec |
| real_hand_written_full_adder | rewrite_z | new_n15 | new_n15 | 0.8625 | Networks are NOT EQUIVALENT.  Time =     0.00 sec |
| real_hand_written_parity_8 | dc2 | new_n28 | new_n28 | 0.8625 | Networks are NOT EQUIVALENT.  Time =     0.00 sec |

A rejected candidate means the simulation ranking assigned a high score to a pair that ABC proved are not logically equivalent. This shows why a formal check is necessary: simulation similarity alone is not a proof of equivalence.

## Inconclusive candidates

405 candidate(s) could not be formally checked.

An inconclusive result means the ABC check could not be completed. Common reasons:

- A node name appears in the candidate list but not in the BLIF file (ABC renames nodes during optimization, so the original and optimized variants may use different names for corresponding nodes).
- A BLIF file was missing.
- ABC timed out.
- Another preparation error occurred.

Inconclusive cases do not mean the candidate is wrong — they mean the current prototype cannot complete the check.

**Inconclusive counts by benchmark/optimization:**

| benchmark | optimization | inconclusive_count |
| --- | --- | --- |
| generated_multiplier_4 | balance | 8 |
| generated_multiplier_4 | compress2rs | 44 |
| generated_multiplier_4 | dc2 | 50 |
| generated_multiplier_4 | refactor | 17 |
| generated_multiplier_4 | refactor_z | 35 |
| generated_multiplier_4 | resub | 5 |
| generated_multiplier_4 | resyn | 48 |
| generated_multiplier_4 | resyn2 | 48 |
| generated_multiplier_4 | resyn2_like | 48 |
| generated_multiplier_4 | rewrite | 24 |
| generated_multiplier_4 | rewrite_z | 43 |
| generated_random_medium | compress2rs | 2 |
| generated_random_medium | refactor_z | 6 |
| generated_random_medium | resyn | 2 |
| generated_random_medium | resyn2 | 2 |
| generated_random_medium | resyn2_like | 2 |
| generated_random_medium | rewrite_z | 3 |
| majority3 | compress2rs | 1 |
| majority3 | dc2 | 1 |
| majority3 | refactor_z | 1 |
| majority3 | resyn2 | 1 |
| majority3 | resyn2_like | 1 |
| real_hand_written_full_adder | dc2 | 3 |
| real_hand_written_full_adder | refactor_z | 1 |
| real_hand_written_full_adder | resyn2 | 1 |
| real_hand_written_full_adder | resyn2_like | 1 |
| real_hand_written_mux_4to1 | resyn | 2 |
| real_hand_written_mux_4to1 | rewrite | 2 |
| real_hand_written_mux_4to1 | rewrite_z | 2 |
| real_hand_written_parity_8 | dc2 | 1 |

## Main interpretation

The SAT refinement step confirms that the simulation-based ranking method is useful but not a proof by itself. Most high-confidence candidates were formally verified by ABC's equivalence checker, which shows the scoring formula produces meaningful rankings. The rejected candidate demonstrates why a formal check is necessary: a high simulation similarity score is not sufficient to guarantee equivalence, and ABC can find a concrete counterexample where the two nodes disagree. Inconclusive cases reveal current prototype limitations, especially around node-name stability between the original and optimized BLIF files and the fact that ABC assigns new internal names during optimization. Reducing the inconclusive rate is the most direct path to making the refinement step more useful in practice.
