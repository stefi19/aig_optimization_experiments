# Approximate Node Distance Summary

This prototype measures truth-table distance for ISCAS-85 rank-1 non-exact candidates.
Rows in `exact` mode are formal exhaustive distances over the union support.
Rows in `sampled` mode are estimates and must not be described as formal.

- Exact rows: 545
- Sampled rows: 2,064
- Skipped rows: 0

## Distance Summary

| distance_mode   | sat_status   |   count |   mean_distance |   median_distance |   min_distance |   max_distance |   pct_distance_le_1pct |   pct_distance_le_5pct |   pct_distance_le_10pct |
|:----------------|:-------------|--------:|----------------:|------------------:|---------------:|---------------:|-----------------------:|-----------------------:|------------------------:|
| exact           | rejected     |     463 |          0.0603 |            0.0625 |         0.0010 |         0.1172 |                 0.1274 |                 0.3585 |                  0.9762 |
| exact           | verified     |      82 |          0.1357 |            0.1250 |         0.0625 |         0.2500 |                 0.0000 |                 0.0000 |                  0.0610 |
| sampled         | rejected     |    1537 |          0.0247 |            0.0132 |         0.0002 |         0.1316 |                 0.3318 |                 0.8308 |                  0.9805 |
| sampled         | verified     |     527 |          0.0530 |            0.0310 |         0.0000 |         0.2678 |                 0.1879 |                 0.6452 |                  0.7932 |

## Close Rejected Candidates

| distance_mode   | benchmark              | optimization   | original_candidate   | optimized_node   |   combined_score |   support_overlap |   distance |   similarity |
|:----------------|:-----------------------|:---------------|:---------------------|:-----------------|-----------------:|------------------:|-----------:|-------------:|
| sampled         | external_iscas85_c1908 | compress2rs    | new_n280             | new_n320         |           0.9390 |            0.9697 |     0.0002 |       0.9998 |
| sampled         | external_iscas85_c1908 | compress2rs    | new_n291             | new_n293         |           0.9996 |            1.0000 |     0.0002 |       0.9998 |
| sampled         | external_iscas85_c1908 | refactor_z     | new_n292             | new_n294         |           0.9996 |            1.0000 |     0.0002 |       0.9998 |
| sampled         | external_iscas85_c1908 | rewrite_z      | new_n291             | new_n296         |           0.9996 |            1.0000 |     0.0002 |       0.9998 |
| sampled         | external_iscas85_c1908 | dc2            | new_n301             | new_n284         |           0.9997 |            1.0000 |     0.0002 |       0.9998 |
| sampled         | external_iscas85_c1908 | resyn          | new_n283             | new_n278         |           0.9997 |            1.0000 |     0.0002 |       0.9998 |
| sampled         | external_iscas85_c1908 | rewrite_z      | new_n317             | new_n308         |           0.9997 |            1.0000 |     0.0002 |       0.9998 |
| sampled         | external_iscas85_c7552 | balance        | new_n1720            | new_n1709        |           0.9429 |            0.9821 |     0.0005 |       0.9995 |
| sampled         | external_iscas85_c2670 | rewrite        | new_n594             | new_n603         |           0.9444 |            0.9848 |     0.0005 |       0.9995 |
| sampled         | external_iscas85_c1908 | resyn2         | new_n301             | new_n355         |           0.9483 |            1.0000 |     0.0005 |       0.9995 |
| sampled         | external_iscas85_c1908 | resyn          | new_n315             | new_n294         |           0.9764 |            0.9375 |     0.0005 |       0.9995 |
| sampled         | external_iscas85_c7552 | rewrite_z      | new_n1720            | new_n1519        |           0.9929 |            0.9821 |     0.0005 |       0.9995 |
| sampled         | external_iscas85_c499  | balance        | new_n347             | new_n349         |           0.9992 |            1.0000 |     0.0005 |       0.9995 |
| sampled         | external_iscas85_c1908 | dc2            | new_n270             | new_n267         |           0.9995 |            1.0000 |     0.0005 |       0.9995 |
| sampled         | external_iscas85_c1908 | dc2            | new_n270             | new_n273         |           0.9996 |            1.0000 |     0.0005 |       0.9995 |
| sampled         | external_iscas85_c1908 | dc2            | new_n292             | new_n290         |           0.9996 |            1.0000 |     0.0005 |       0.9995 |
| sampled         | external_iscas85_c1908 | resyn          | new_n270             | new_n271         |           0.9996 |            1.0000 |     0.0005 |       0.9995 |
| sampled         | external_iscas85_c1908 | rewrite_z      | new_n270             | new_n273         |           0.9996 |            1.0000 |     0.0005 |       0.9995 |
| sampled         | external_iscas85_c1908 | rewrite_z      | new_n291             | new_n287         |           0.9996 |            1.0000 |     0.0005 |       0.9995 |
| sampled         | external_iscas85_c1908 | resyn          | new_n317             | new_n300         |           0.9997 |            1.0000 |     0.0005 |       0.9995 |
