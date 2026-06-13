# SAT Validation Layers

## Layer summary

| validation_layer        |   total |   verified |   rejected |   inconclusive | verification_rate   | rejection_rate   | inconclusive_rate   |
|:------------------------|--------:|-----------:|-----------:|---------------:|:--------------------|:-----------------|:--------------------|
| exact_anchor_sanity     |    3052 |       3052 |          0 |              0 | 100.0%              | 0.0%             | 0.0%                |
| rank1_nonexact_recovery |     425 |          0 |        425 |              0 | 0.0%                | 100.0%           | 0.0%                |
| topk_nonexact_recovery  |    1993 |          0 |       1993 |              0 | 0.0%                | 100.0%           | 0.0%                |

## Interpretation

- `exact_anchor_sanity` checks already-preserved signature matches. These should verify; they test whether the SAT pipeline accepts known matches.
- `rank1_nonexact_recovery` is the previous high-confidence rank-1 non-exact check.
- `topk_nonexact_recovery` checks high-score non-exact candidates below rank 1. Verified rows here would be genuine recovered correspondences missed by rank 1.

The same-polarity CEC checks ask whether `f == g`. A separate complemented-equivalence
follow-up retests same-polarity rejected non-exact candidates for `f == NOT g`.

| validation_layer        |   total_same_polarity_rejected |   same_polarity_verified |   complemented_verified |   rejected_both_polarities |   inconclusive |
|:------------------------|-------------------------------:|-------------------------:|------------------------:|---------------------------:|---------------:|
| rank1_nonexact_recovery |                            425 |                        0 |                       0 |                        425 |              0 |
| topk_nonexact_recovery  |                           1993 |                        0 |                       0 |                       1993 |              0 |

This means the selected non-exact candidates are rejected both as same-polarity matches and
as simple complemented matches. The null result is therefore not explained by missing AIG
inverter polarity.

## False-positive analysis

### By optimization

| validation_layer        | dimension    | bucket      |   rejected_count |   avg_combined_score |   avg_support_overlap |
|:------------------------|:-------------|:------------|-----------------:|---------------------:|----------------------:|
| rank1_nonexact_recovery | optimization | balance     |               10 |               0.9394 |                1      |
| rank1_nonexact_recovery | optimization | compress2rs |               49 |               0.9213 |                0.9974 |
| rank1_nonexact_recovery | optimization | dc2         |               57 |               0.9168 |                0.9978 |
| rank1_nonexact_recovery | optimization | refactor    |               17 |               0.9169 |                1      |
| rank1_nonexact_recovery | optimization | refactor_z  |               43 |               0.9162 |                1      |
| rank1_nonexact_recovery | optimization | resub       |                5 |               0.9459 |                1      |
| rank1_nonexact_recovery | optimization | resyn       |               55 |               0.9171 |                0.9977 |
| rank1_nonexact_recovery | optimization | resyn2      |               54 |               0.919  |                0.9977 |
| rank1_nonexact_recovery | optimization | resyn2_like |               54 |               0.919  |                0.9977 |
| rank1_nonexact_recovery | optimization | rewrite     |               27 |               0.9208 |                1      |
| rank1_nonexact_recovery | optimization | rewrite_z   |               54 |               0.9173 |                0.9977 |
| topk_nonexact_recovery  | optimization | balance     |              260 |               0.8954 |                0.9864 |
| topk_nonexact_recovery  | optimization | compress2rs |              147 |               0.8869 |                0.987  |
| topk_nonexact_recovery  | optimization | dc2         |              158 |               0.8907 |                0.9874 |
| topk_nonexact_recovery  | optimization | refactor    |              203 |               0.8961 |                0.986  |
| topk_nonexact_recovery  | optimization | refactor_z  |              184 |               0.8893 |                0.9854 |
| topk_nonexact_recovery  | optimization | resub       |              219 |               0.8913 |                0.9902 |
| topk_nonexact_recovery  | optimization | resyn       |              165 |               0.8889 |                0.9872 |
| topk_nonexact_recovery  | optimization | resyn2      |              161 |               0.8895 |                0.9868 |
| topk_nonexact_recovery  | optimization | resyn2_like |              161 |               0.8895 |                0.9868 |
| topk_nonexact_recovery  | optimization | rewrite     |              171 |               0.8884 |                0.9909 |
| topk_nonexact_recovery  | optimization | rewrite_z   |              164 |               0.8929 |                0.9842 |

### By optimization_group

| validation_layer        | dimension          | bucket     |   rejected_count |   avg_combined_score |   avg_support_overlap |
|:------------------------|:-------------------|:-----------|-----------------:|---------------------:|----------------------:|
| rank1_nonexact_recovery | optimization_group | aggressive |              214 |               0.919  |                0.9977 |
| rank1_nonexact_recovery | optimization_group | mild       |               42 |               0.9282 |                1      |
| rank1_nonexact_recovery | optimization_group | moderate   |              169 |               0.9169 |                0.9985 |
| topk_nonexact_recovery  | optimization_group | aggressive |              627 |               0.8892 |                0.987  |
| topk_nonexact_recovery  | optimization_group | mild       |              650 |               0.8922 |                0.9889 |
| topk_nonexact_recovery  | optimization_group | moderate   |              716 |               0.8919 |                0.9857 |

### By benchmark_family

| validation_layer        | dimension        | bucket            |   rejected_count |   avg_combined_score |   avg_support_overlap |
|:------------------------|:-----------------|:------------------|-----------------:|---------------------:|----------------------:|
| rank1_nonexact_recovery | benchmark_family | generated         |              400 |               0.9225 |                0.9981 |
| rank1_nonexact_recovery | benchmark_family | real_hand_written |               17 |               0.8647 |                1      |
| rank1_nonexact_recovery | benchmark_family | toy               |                8 |               0.8625 |                1      |
| topk_nonexact_recovery  | benchmark_family | generated         |             1991 |               0.8912 |                0.9871 |
| topk_nonexact_recovery  | benchmark_family | real_hand_written |                2 |               0.8625 |                1      |

### By combined_score_bucket

| validation_layer        | dimension             | bucket    |   rejected_count |   avg_combined_score |   avg_support_overlap |
|:------------------------|:----------------------|:----------|-----------------:|---------------------:|----------------------:|
| rank1_nonexact_recovery | combined_score_bucket | 0.85-0.90 |              167 |               0.8731 |                1      |
| rank1_nonexact_recovery | combined_score_bucket | 0.90-0.95 |              148 |               0.9311 |                0.9949 |
| rank1_nonexact_recovery | combined_score_bucket | 0.95-1.00 |              110 |               0.9727 |                1      |
| topk_nonexact_recovery  | combined_score_bucket | 0.85-0.90 |             1251 |               0.8721 |                0.9848 |
| topk_nonexact_recovery  | combined_score_bucket | 0.90-0.95 |              693 |               0.9198 |                0.9904 |
| topk_nonexact_recovery  | combined_score_bucket | 0.95-1.00 |               49 |               0.9737 |                1      |

### By support_overlap_bucket

| validation_layer        | dimension              | bucket    |   rejected_count |   avg_combined_score |   avg_support_overlap |
|:------------------------|:-----------------------|:----------|-----------------:|---------------------:|----------------------:|
| rank1_nonexact_recovery | support_overlap_bucket | 0.75-0.90 |                6 |               0.9383 |                0.875  |
| rank1_nonexact_recovery | support_overlap_bucket | 1.00      |              419 |               0.9188 |                1      |
| topk_nonexact_recovery  | support_overlap_bucket | 0.50-0.75 |                6 |               0.8742 |                0.7143 |
| topk_nonexact_recovery  | support_overlap_bucket | 0.75-0.90 |              147 |               0.882  |                0.8373 |
| topk_nonexact_recovery  | support_overlap_bucket | 1.00      |             1840 |               0.892  |                1      |

## Research conclusion

Mild passes preserve many internal signatures, while aggressive passes destroy large parts of the internal correspondence structure. The heuristic score based on simulation, support overlap, and depth produces plausible candidates, but the SAT results show that plausible is not the same as equivalent. Formal CEC is therefore necessary before claiming recovered internal correspondences. In the current run, the heuristic is best interpreted as a ranking and triage signal, not as a standalone correspondence-recovery method.

One important limitation remains: these checks use global internal-node equivalence. After
aggressive optimization, a candidate may still be meaningful under observability don't-care
conditions even when it is not globally equivalent for all primary-input assignments. Future
work should test ODC-aware correspondence or reuse ABC-native SAT sweeping/FRAIG equivalence
classes instead of relying only on pairwise global CEC.
