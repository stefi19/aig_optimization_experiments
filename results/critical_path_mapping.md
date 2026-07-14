# Critical-Path Back-Mapping Summary

This prototype uses structural longest path as a timing proxy, then maps
optimized path nodes back to original nodes using signature matches,
complemented equivalence, SAT/CEC-proven equivalence after structural mismatch, and approximate
near-matches in that priority order.

"After structural mismatch" means that the pair was not identified by the initial signature or structural matching stage. SAT/CEC later proved that the two nodes compute the same Boolean function.

- Optimized critical-path nodes analyzed: 1,686
- Mapped nodes: 1,289 (76.5%)
- Unresolved nodes: 397 (23.5%)

## Mapping Categories

| mapping_category                 |   count |
|:---------------------------------|--------:|
| exact_signature_match            |    1136 |
| complemented_equivalence         |       0 |
| sat_cec_proven_equivalent        |     145 |
| odc_valid_correspondence         |       0 |
| contextually_approximate_exact   |       0 |
| contextually_approximate_sampled |       0 |
| global_approximate_near_match    |       8 |
| unresolved                       |     397 |

## Per Circuit / Optimization Summary

| circuit   | optimization   |   critical_path_nodes |   exact_signature_match |   complemented_equivalence |   sat_cec_proven_equivalent |   global_approximate_near_match |   unresolved |   mapped_fraction |   unresolved_fraction |
|:----------|:---------------|----------------------:|------------------------:|---------------------------:|----------------------------:|--------------------------------:|-------------:|------------------:|----------------------:|
| c2670     | balance        |                    17 |                      13 |                          0 |                           0 |                               0 |            4 |             0.765 |                 0.235 |
| c2670     | compress2rs    |                    17 |                       0 |                          0 |                           0 |                               0 |           17 |             0.000 |                 1.000 |
| c2670     | dc2            |                    20 |                       6 |                          0 |                           1 |                               2 |           11 |             0.450 |                 0.550 |
| c2670     | refactor       |                    21 |                       1 |                          0 |                           6 |                               0 |           14 |             0.333 |                 0.667 |
| c2670     | refactor_z     |                    20 |                       1 |                          0 |                           3 |                               0 |           16 |             0.200 |                 0.800 |
| c2670     | resub          |                    21 |                      19 |                          0 |                           0 |                               0 |            2 |             0.905 |                 0.095 |
| c2670     | resyn          |                    17 |                       7 |                          0 |                           0 |                               0 |           10 |             0.412 |                 0.588 |
| c2670     | resyn2         |                    17 |                       0 |                          0 |                           0 |                               0 |           17 |             0.000 |                 1.000 |
| c2670     | resyn2_like    |                    17 |                       0 |                          0 |                           0 |                               0 |           17 |             0.000 |                 1.000 |
| c2670     | rewrite        |                    21 |                      17 |                          0 |                           0 |                               1 |            3 |             0.857 |                 0.143 |
| c2670     | rewrite_z      |                    21 |                      12 |                          0 |                           0 |                               1 |            8 |             0.619 |                 0.381 |
| c432      | balance        |                    25 |                      12 |                          0 |                           0 |                               0 |           13 |             0.480 |                 0.520 |
| c432      | compress2rs    |                    23 |                      11 |                          0 |                           1 |                               0 |           11 |             0.522 |                 0.478 |
| c432      | dc2            |                    26 |                       7 |                          0 |                           0 |                               0 |           19 |             0.269 |                 0.731 |
| c432      | refactor       |                    42 |                      38 |                          0 |                           0 |                               0 |            4 |             0.905 |                 0.095 |
| c432      | refactor_z     |                    33 |                       8 |                          0 |                           0 |                               2 |           23 |             0.303 |                 0.697 |
| c432      | resub          |                    41 |                      20 |                          0 |                           8 |                               0 |           13 |             0.683 |                 0.317 |
| c432      | resyn          |                    25 |                      10 |                          0 |                           1 |                               0 |           14 |             0.440 |                 0.560 |
| c432      | resyn2         |                    25 |                      10 |                          0 |                           1 |                               0 |           14 |             0.440 |                 0.560 |
| c432      | resyn2_like    |                    25 |                      10 |                          0 |                           1 |                               0 |           14 |             0.440 |                 0.560 |
| c432      | rewrite        |                    41 |                      28 |                          0 |                           4 |                               0 |            9 |             0.780 |                 0.220 |
| c432      | rewrite_z      |                    41 |                      24 |                          0 |                           5 |                               2 |           10 |             0.756 |                 0.244 |
| c6288     | balance        |                   120 |                     118 |                          0 |                           0 |                               0 |            2 |             0.983 |                 0.017 |
| c6288     | compress2rs    |                    89 |                      53 |                          0 |                          16 |                               0 |           20 |             0.775 |                 0.225 |
| c6288     | dc2            |                    89 |                      53 |                          0 |                          16 |                               0 |           20 |             0.775 |                 0.225 |
| c6288     | refactor       |                   120 |                     118 |                          0 |                           0 |                               0 |            2 |             0.983 |                 0.017 |
| c6288     | refactor_z     |                   119 |                     117 |                          0 |                           0 |                               0 |            2 |             0.983 |                 0.017 |
| c6288     | resub          |                   120 |                     118 |                          0 |                           0 |                               0 |            2 |             0.983 |                 0.017 |
| c6288     | resyn          |                    89 |                      52 |                          0 |                          16 |                               0 |           21 |             0.764 |                 0.236 |
| c6288     | resyn2         |                    89 |                      53 |                          0 |                          16 |                               0 |           20 |             0.775 |                 0.225 |
| c6288     | resyn2_like    |                    89 |                      53 |                          0 |                          16 |                               0 |           20 |             0.775 |                 0.225 |
| c6288     | rewrite        |                   117 |                      95 |                          0 |                          18 |                               0 |            4 |             0.966 |                 0.034 |
| c6288     | rewrite_z      |                    89 |                      52 |                          0 |                          16 |                               0 |           21 |             0.764 |                 0.236 |

## Example Mappings

| circuit   | optimization   |   path_index | optimized_node   | mapped_original_node   | mapping_category      |   confidence |   distance |   combined_score |
|:----------|:---------------|-------------:|:-----------------|:-----------------------|:----------------------|-------------:|-----------:|-----------------:|
| c2670     | balance        |            1 | new_n264         | new_n264               | exact_signature_match |       1.0000 |        nan |           1.0000 |
| c2670     | balance        |            2 | new_n265         | new_n265               | exact_signature_match |       1.0000 |        nan |           1.0000 |
| c2670     | balance        |            5 | new_n792         | new_n792               | exact_signature_match |       1.0000 |        nan |           0.9500 |
| c2670     | balance        |            6 | new_n795         | new_n796               | exact_signature_match |       1.0000 |        nan |           0.9333 |
| c2670     | balance        |            7 | new_n893         | new_n904               | exact_signature_match |       1.0000 |        nan |           0.9333 |
| c2670     | balance        |            8 | new_n895         | new_n906               | exact_signature_match |       1.0000 |        nan |           0.9333 |
| c2670     | balance        |            9 | new_n896         | new_n907               | exact_signature_match |       1.0000 |        nan |           0.9333 |
| c2670     | balance        |           10 | new_n898         | new_n909               | exact_signature_match |       1.0000 |        nan |           0.9333 |
| c2670     | balance        |           12 | new_n907         | new_n917               | exact_signature_match |       1.0000 |        nan |           0.9333 |
| c2670     | balance        |           13 | new_n912         | new_n922               | exact_signature_match |       1.0000 |        nan |           0.9333 |
| c2670     | balance        |           14 | new_n916         | new_n923               | exact_signature_match |       1.0000 |        nan |           0.9250 |
| c2670     | balance        |           15 | new_n921         | new_n924               | exact_signature_match |       1.0000 |        nan |           0.9200 |
