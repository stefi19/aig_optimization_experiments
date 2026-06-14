# ISCAS-85 Case Studies

## Verified non-exact correspondences

| benchmark              | optimization   | original_candidate   | optimized_node   |   combined_score |   support_overlap |   simulation_similarity | sat_status   | short_interpretation                          |
|:-----------------------|:---------------|:---------------------|:-----------------|-----------------:|------------------:|------------------------:|:-------------|:----------------------------------------------|
| external_iscas85_c5315 | refactor       | new_n1392            | new_n1243        |           0.9981 |             1     |                  0.9966 | verified     | high-score verified from a mild/moderate pass |
| external_iscas85_c2670 | compress2rs    | new_n883             | new_n729         |           0.9297 |             1     |                  0.9934 | verified     | verified from aggressive resynthesis          |
| external_iscas85_c5315 | resub          | new_n1560            | new_n1478        |           0.878  |             0.697 |                  0.9709 | verified     | verified even though support changed          |
| external_iscas85_c2670 | refactor       | new_n925             | new_n825         |           0.9828 |             1     |                  0.9688 | verified     | verified from circuit with most recoveries    |
| external_iscas85_c6288 | rewrite        | new_n2293            | new_n2261        |           0.9249 |             1     |                  0.9998 | verified     | verified from multiplier-like c6288           |

## High-score rejected candidates

| benchmark              | optimization   | original_candidate   | optimized_node   |   combined_score |   support_overlap |   simulation_similarity | sat_status   | why_it_is_misleading                                               |
|:-----------------------|:---------------|:---------------------|:-----------------|-----------------:|------------------:|------------------------:|:-------------|:-------------------------------------------------------------------|
| external_iscas85_c1908 | refactor_z     | new_n277             | new_n273         |           0.9999 |                 1 |                  0.9998 | rejected     | High score and overlapping support, but ABC found a counterexample |
| external_iscas85_c1908 | refactor_z     | new_n274             | new_n276         |           0.9999 |                 1 |                  0.9998 | rejected     | High score and overlapping support, but ABC found a counterexample |
| external_iscas85_c1908 | balance        | new_n283             | new_n283         |           0.9997 |                 1 |                  0.9995 | rejected     | High score and overlapping support, but ABC found a counterexample |
| external_iscas85_c1908 | balance        | new_n291             | new_n296         |           0.9997 |                 1 |                  0.9995 | rejected     | High score and overlapping support, but ABC found a counterexample |
| external_iscas85_c1908 | dc2            | new_n301             | new_n284         |           0.9997 |                 1 |                  0.9995 | rejected     | High score and overlapping support, but ABC found a counterexample |
