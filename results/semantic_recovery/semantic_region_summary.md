# Semantic Regions and Interfaces

This phase establishes canonical regions, boundaries, scalar interfaces, and ground-truth interface alignment. It does not infer or recover high-level RTL expressions.

## Funnel

- Declared benchmark cases: 258
- Available circuit variants: 559
- Eligible region rows: 686
- Valid ground-truth regions: 127
- Valid whole-output-cone regions: 559
- Infrastructure skips: 0
- Unsupported rows: 3958
- Invalid regions: 0

## Scalar Interface

- Exact scalar-interface matches: 581 / 686
- Mean input precision: 1.000
- Mean input recall: 0.934
- Mean output precision: 1.000
- Mean output recall: 1.000
- Mean input order accuracy: 1.000
- Mean output order accuracy: 1.000

## Region Source Comparison

- Comparable ground-truth/output-cone pairs: 127
- Mean comparable ground-truth region size: 4.008
- Mean comparable output-cone region size: 4.008
- Mean Jaccard overlap: 1.000
- Mean valid ground-truth region size: 4.008
- Mean valid output-cone region size across all variants: 6.106
- Whole-design output-cone count: 559

## Valid Regions by Family

| Family | Valid rows |
| --- | ---: |
| arithmetic | 176 |
| bitmanip | 252 |
| boolean | 138 |
| comparison | 104 |
| control | 16 |

## Results by Optimization

| Optimization | Available | Valid | Exact interface | Whole-design output cones | Skips |
| --- | ---: | ---: | ---: | ---: | ---: |
| balance | 54 | 54 | 44 | 54 | 462 |
| compress2rs | 54 | 54 | 39 | 54 | 462 |
| dc2 | 54 | 54 | 39 | 54 | 462 |
| identity | 127 | 254 | 254 | 127 | 262 |
| refactor | 54 | 54 | 39 | 54 | 462 |
| resub | 54 | 54 | 39 | 54 | 462 |
| resyn | 54 | 54 | 44 | 54 | 462 |
| resyn2 | 54 | 54 | 39 | 54 | 462 |
| rewrite | 54 | 54 | 44 | 54 | 462 |

## Limitation

No row in this phase represents recovered RTL. Region and interface extraction only prepares the substrate for later semantic inference.
