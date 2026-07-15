# Enhanced Critical-Path Ranking Join

This file joins cofactor/sensitivity ranking evidence onto the existing critical-path mapping rows. It does not change mapping-category semantics and does not claim new equivalence without SAT/CEC.

- Critical-path rows: 1,686
- Rows with enhanced rank evidence: 2
- Unresolved rows in the existing mapping: 397

The lightweight run reports rank deltas for already mapped rows. It does not yet rerun SAT/CEC with a new validation budget, so unresolved critical-path recovery is unchanged unless future validation is added.

## Rank Delta Summary

| index   |   baseline_rank |   enhanced_rank |   rank_delta |
|:--------|----------------:|----------------:|-------------:|
| count   |           2.000 |           2.000 |        2.000 |
| mean    |           1.000 |           1.000 |        0.000 |
| std     |           0.000 |           0.000 |        0.000 |
| min     |           1.000 |           1.000 |        0.000 |
| 25%     |           1.000 |           1.000 |        0.000 |
| 50%     |           1.000 |           1.000 |        0.000 |
| 75%     |           1.000 |           1.000 |        0.000 |
| max     |           1.000 |           1.000 |        0.000 |
