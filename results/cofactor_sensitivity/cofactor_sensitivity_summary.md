# Cofactor- and Sensitivity-Aware Correspondence Features

This analysis adds heuristic ranking features. SAT/CEC labels remain the formal evidence for equivalence; sampled cofactor and sensitivity rows are estimates only.

- Candidate-feature rows: 88
- Unique candidate pairs: 44
- Seeds: 0, 23, 29

## Evidence Coverage

| functional_feature_evidence_level   | formal_label            |   rows |
|:------------------------------------|:------------------------|-------:|
| formal_exhaustive                   | rejected_non_equivalent |     44 |
| sampled_estimate                    | rejected_non_equivalent |     22 |
| sampled_estimate                    | verified_equivalent     |     22 |

## Mean Feature Values by Formal Label

| formal_label            |   cofactor_consistency_score |   mean_cofactor_similarity |   max_cofactor_error |   sensitivity_cosine_similarity |   boolean_difference_similarity |
|:------------------------|-----------------------------:|---------------------------:|---------------------:|--------------------------------:|--------------------------------:|
| rejected_non_equivalent |                       0.8910 |                     0.8416 |               0.1953 |                          0.6861 |                          0.9048 |
| verified_equivalent     |                       0.8974 |                     0.7770 |               0.3754 |                          0.2706 |                          0.9395 |

## Ranking Modes

Modes written to the CSV are `baseline`, `cofactor_only`, `sensitivity_only`, `cofactor_plus_sensitivity`, and `full_combined`. These scores are heuristic ranking signals, not proof of correspondence.
