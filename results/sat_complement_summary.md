# Complemented SAT Validation Summary

The normal SAT validation checks same-polarity equivalence (`f == g`). This follow-up retests same-polarity rejected non-exact candidates for complemented equivalence (`f == NOT g`).

| validation_layer        |   total_same_polarity_rejected |   same_polarity_verified |   complemented_verified |   rejected_both_polarities |   inconclusive | complemented_verification_rate   |
|:------------------------|-------------------------------:|-------------------------:|------------------------:|---------------------------:|---------------:|:---------------------------------|
| rank1_nonexact_recovery |                            425 |                        0 |                       0 |                        425 |              0 | 0.0%                             |
| topk_nonexact_recovery  |                           1993 |                        0 |                       0 |                       1993 |              0 | 0.0%                             |

A complemented verification would mean the candidate was not same-polarity equivalent, but did match after inverting the optimized node. These results remain separate from exact-anchor sanity checks and same-polarity recovery.
