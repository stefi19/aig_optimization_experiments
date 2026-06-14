# ISCAS-85 Verified Match Analysis

This analysis covers rank-1 non-exact candidates from the expanded ISCAS-85 SAT run.

- Total checked: 9,214
- Verified: 609
- Rejected: 8,605
- Inconclusive: 0

## By Circuit

| circuit   |   verified |   rejected |   total_checked |   precision |
|:----------|-----------:|-----------:|----------------:|------------:|
| c2670     |        302 |        392 |             694 |       0.435 |
| c6288     |        133 |       1810 |            1943 |       0.068 |
| c5315     |         90 |        885 |             975 |       0.092 |
| c432      |         84 |         64 |             148 |       0.568 |
| c1355     |          0 |        772 |             772 |       0.000 |
| c1908     |          0 |        567 |             567 |       0.000 |
| c3540     |          0 |       1076 |            1076 |       0.000 |
| c499      |          0 |        557 |             557 |       0.000 |
| c7552     |          0 |       2211 |            2211 |       0.000 |
| c880      |          0 |        271 |             271 |       0.000 |

## By Optimization

| optimization   |   verified |   rejected |   total_checked |   precision |
|:---------------|-----------:|-----------:|----------------:|------------:|
| refactor       |         99 |        470 |             569 |       0.174 |
| resyn2         |         83 |        997 |            1080 |       0.077 |
| resyn2_like    |         83 |        997 |            1080 |       0.077 |
| compress2rs    |         81 |        981 |            1062 |       0.076 |
| rewrite        |         73 |        653 |             726 |       0.101 |
| refactor_z     |         59 |        674 |             733 |       0.080 |
| resub          |         43 |        115 |             158 |       0.272 |
| dc2            |         34 |       1072 |            1106 |       0.031 |
| rewrite_z      |         31 |       1219 |            1250 |       0.025 |
| resyn          |         23 |        992 |            1015 |       0.023 |
| balance        |          0 |        435 |             435 |       0.000 |

## By Optimization Group

| group     |   verified |   rejected |   total_checked |   precision |
|:----------|-----------:|-----------:|----------------:|------------:|
| very_high |        281 |       4047 |            4328 |       0.065 |
| medium    |        262 |       3016 |            3278 |       0.080 |
| high      |         66 |       1107 |            1173 |       0.056 |
| low       |          0 |        435 |             435 |       0.000 |

## Feature Comparison

| feature                |   verified_mean |   rejected_mean |   verified_median |   rejected_median |   verified_min |   rejected_min |   verified_max |   rejected_max |
|:-----------------------|----------------:|----------------:|------------------:|------------------:|---------------:|---------------:|---------------:|---------------:|
| combined_score         |           0.899 |           0.905 |             0.901 |             0.896 |          0.850 |          0.850 |          0.998 |          1.000 |
| support_overlap        |           0.995 |           0.969 |             1.000 |             1.000 |          0.688 |          0.600 |          1.000 |          1.000 |
| simulation_similarity  |           0.935 |           0.915 |             0.964 |             0.931 |          0.728 |          0.728 |          1.000 |          1.000 |
| depth_similarity       |           0.370 |           0.631 |             0.333 |             0.500 |          0.032 |          0.033 |          1.000 |          1.000 |
| level_delta_abs        |           6.512 |           1.956 |             2.000 |             1.000 |          0.000 |          0.000 |         30.000 |         29.000 |
| support_size_delta_abs |           0.330 |           0.610 |             0.000 |             0.000 |          0.000 |          0.000 |         20.000 |         24.000 |
| optimized_level        |          26.969 |          14.623 |            11.000 |            12.000 |          3.000 |          2.000 |        110.000 |         90.000 |
| original_level         |          33.478 |          16.205 |            12.000 |            13.000 |          3.000 |          2.000 |        113.000 |        117.000 |
| optimized_support_size |          24.810 |          21.064 |            22.000 |            14.000 |          4.000 |          2.000 |         78.000 |        124.000 |
| original_support_size  |          25.140 |          20.852 |            22.000 |            14.000 |          4.000 |          2.000 |         78.000 |        124.000 |

## Support-Overlap Check

- Verified candidates with `support_overlap = 1.0`: 598 / 609
- Rejected candidates with `support_overlap = 1.0`: 6,046 / 8,605

Support overlap is useful, but it is not enough to separate true from false matches.

## Representative Verified Matches

| benchmark              | optimization   | original_candidate   | optimized_node   |   combined_score |   support_overlap |   simulation_similarity | sat_status   | short_interpretation                          |
|:-----------------------|:---------------|:---------------------|:-----------------|-----------------:|------------------:|------------------------:|:-------------|:----------------------------------------------|
| external_iscas85_c5315 | refactor       | new_n1392            | new_n1243        |           0.9981 |             1     |                  0.9966 | verified     | high-score verified from a mild/moderate pass |
| external_iscas85_c2670 | compress2rs    | new_n883             | new_n729         |           0.9297 |             1     |                  0.9934 | verified     | verified from aggressive resynthesis          |
| external_iscas85_c5315 | resub          | new_n1560            | new_n1478        |           0.878  |             0.697 |                  0.9709 | verified     | verified even though support changed          |
| external_iscas85_c2670 | refactor       | new_n925             | new_n825         |           0.9828 |             1     |                  0.9688 | verified     | verified from circuit with most recoveries    |
| external_iscas85_c6288 | rewrite        | new_n2293            | new_n2261        |           0.9249 |             1     |                  0.9998 | verified     | verified from multiplier-like c6288           |

## Representative High-Score False Positives

| benchmark              | optimization   | original_candidate   | optimized_node   |   combined_score |   support_overlap |   simulation_similarity | sat_status   | why_it_is_misleading                                               |
|:-----------------------|:---------------|:---------------------|:-----------------|-----------------:|------------------:|------------------------:|:-------------|:-------------------------------------------------------------------|
| external_iscas85_c1908 | refactor_z     | new_n277             | new_n273         |           0.9999 |                 1 |                  0.9998 | rejected     | High score and overlapping support, but ABC found a counterexample |
| external_iscas85_c1908 | refactor_z     | new_n274             | new_n276         |           0.9999 |                 1 |                  0.9998 | rejected     | High score and overlapping support, but ABC found a counterexample |
| external_iscas85_c1908 | balance        | new_n283             | new_n283         |           0.9997 |                 1 |                  0.9995 | rejected     | High score and overlapping support, but ABC found a counterexample |
| external_iscas85_c1908 | balance        | new_n291             | new_n296         |           0.9997 |                 1 |                  0.9995 | rejected     | High score and overlapping support, but ABC found a counterexample |
| external_iscas85_c1908 | dc2            | new_n301             | new_n284         |           0.9997 |                 1 |                  0.9995 | rejected     | High score and overlapping support, but ABC found a counterexample |
