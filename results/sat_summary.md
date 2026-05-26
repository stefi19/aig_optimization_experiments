# SAT Refinement Summary

## Overall result

- **Total candidates checked:** 65
- **Verified by ABC:** 53
- **Rejected by ABC:** 1
- **Inconclusive:** 11
- **Verification rate:** 81.5%

## Summary by benchmark and optimization

| benchmark | optimization | verified | rejected | inconclusive | total | verification_rate | rejection_rate | inconclusive_rate | avg_combined_score |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| majority3 | balance | 0 | 1 | 3 | 4 | 0.00% | 25.00% | 75.00% | 0.9656 |
| majority3 | refactor | 0 | 0 | 1 | 1 | 0.00% | 0.00% | 100.00% | 1.0000 |
| majority3 | resub | 1 | 0 | 3 | 4 | 25.00% | 0.00% | 75.00% | 1.0000 |
| majority3 | resyn2_like | 1 | 0 | 1 | 2 | 50.00% | 0.00% | 50.00% | 0.9312 |
| majority3 | rewrite | 1 | 0 | 3 | 4 | 25.00% | 0.00% | 75.00% | 1.0000 |
| mux2 | balance | 2 | 0 | 0 | 2 | 100.00% | 0.00% | 0.00% | 1.0000 |
| mux2 | refactor | 2 | 0 | 0 | 2 | 100.00% | 0.00% | 0.00% | 1.0000 |
| mux2 | resub | 2 | 0 | 0 | 2 | 100.00% | 0.00% | 0.00% | 1.0000 |
| mux2 | rewrite | 2 | 0 | 0 | 2 | 100.00% | 0.00% | 0.00% | 1.0000 |
| toy_and_or | balance | 2 | 0 | 0 | 2 | 100.00% | 0.00% | 0.00% | 1.0000 |
| toy_and_or | refactor | 2 | 0 | 0 | 2 | 100.00% | 0.00% | 0.00% | 1.0000 |
| toy_and_or | resub | 2 | 0 | 0 | 2 | 100.00% | 0.00% | 0.00% | 1.0000 |
| toy_and_or | resyn2_like | 2 | 0 | 0 | 2 | 100.00% | 0.00% | 0.00% | 1.0000 |
| toy_and_or | rewrite | 2 | 0 | 0 | 2 | 100.00% | 0.00% | 0.00% | 1.0000 |
| xor_chain | balance | 8 | 0 | 0 | 8 | 100.00% | 0.00% | 0.00% | 1.0000 |
| xor_chain | refactor | 8 | 0 | 0 | 8 | 100.00% | 0.00% | 0.00% | 1.0000 |
| xor_chain | resub | 8 | 0 | 0 | 8 | 100.00% | 0.00% | 0.00% | 1.0000 |
| xor_chain | rewrite | 8 | 0 | 0 | 8 | 100.00% | 0.00% | 0.00% | 1.0000 |

**Global totals:**

| benchmark | optimization | verified | rejected | inconclusive | total | verification_rate | rejection_rate | inconclusive_rate | avg_combined_score |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ALL | ALL | 53 | 1 | 11 | 65 | 81.54% | 1.54% | 16.92% | 0.9958 |

## Rejected candidates

ABC found 1 candidate(s) to be **not equivalent**:

| benchmark | optimization | optimized_node | original_candidate | combined_score | abc_result |
| --- | --- | --- | --- | --- | --- |
| majority3 | balance | new_n8 | new_n8 | 0.8625 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |

A rejected candidate means the simulation ranking assigned a high score to a pair that ABC proved are not logically equivalent. This shows why a formal check is necessary: simulation similarity alone is not a proof of equivalence.

## Inconclusive candidates

11 candidate(s) could not be formally checked.

An inconclusive result means the ABC check could not be completed. Common reasons:

- A node name appears in the candidate list but not in the BLIF file (ABC renames nodes during optimization, so the original and optimized variants may use different names for corresponding nodes).
- A BLIF file was missing.
- ABC timed out.
- Another preparation error occurred.

Inconclusive cases do not mean the candidate is wrong — they mean the current prototype cannot complete the check.

**Inconclusive counts by benchmark/optimization:**

| benchmark | optimization | inconclusive_count |
| --- | --- | --- |
| majority3 | balance | 3 |
| majority3 | refactor | 1 |
| majority3 | resub | 3 |
| majority3 | resyn2_like | 1 |
| majority3 | rewrite | 3 |

## Main interpretation

The SAT refinement step confirms that the simulation-based ranking method is useful but not a proof by itself. Most high-confidence candidates were formally verified by ABC's equivalence checker, which shows the scoring formula produces meaningful rankings. The rejected candidate demonstrates why a formal check is necessary: a high simulation similarity score is not sufficient to guarantee equivalence, and ABC can find a concrete counterexample where the two nodes disagree. Inconclusive cases reveal current prototype limitations, especially around node-name stability between the original and optimized BLIF files and the fact that ABC assigns new internal names during optimization. Reducing the inconclusive rate is the most direct path to making the refinement step more useful in practice.
