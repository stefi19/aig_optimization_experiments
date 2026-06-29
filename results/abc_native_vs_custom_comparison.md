# ABC-Native vs Custom Correspondence Comparison

This comparison is intentionally indirect. ABC-native FRAIG flows report swept
network size changes, while the custom pipeline reports candidate correspondences
and SAT-verified node-pair checks.

Rows compared: 32

| Benchmark | Optimization | Best ABC flow | ABC node delta | Preservation | Non-exact SAT matches | Interpretation |
|---|---|---|---:|---:|---:|---|
| `external_iscas85_c2670` | `balance` | `fraig` | 37 | 0.844 | 0 | ABC reduces while many custom exact signatures remain preserved |
| `external_iscas85_c2670` | `original` | `fraig` | 29 |  |  | ABC reduces this network; custom evidence is indirect or absent |
| `external_iscas85_c2670` | `resyn2` | `fraig` | 1 | 0.122 | 50 | Both flows show recoverable structure, but ABC mapping is not exposed here |
| `external_iscas85_c2670` | `rewrite` | `fraig` | 0 | 0.711 | 0 | ABC sweep did not reduce nodes in this row |
| `external_iscas85_c432` | `balance` | `fraig` | 36 | 0.787 | 0 | ABC reduces while many custom exact signatures remain preserved |
| `external_iscas85_c432` | `original` | `fraig` | 38 |  |  | ABC reduces this network; custom evidence is indirect or absent |
| `external_iscas85_c432` | `resyn2` | `fraig` | 6 | 0.421 | 6 | Both flows show recoverable structure, but ABC mapping is not exposed here |
| `external_iscas85_c432` | `rewrite` | `fraig` | 24 | 0.842 | 11 | ABC reduces while many custom exact signatures remain preserved |
| `external_iscas85_c6288` | `balance` | `fraig` | 3 | 1.000 |  | ABC reduces while many custom exact signatures remain preserved |
| `external_iscas85_c6288` | `original` | `fraig` | 3 |  |  | ABC reduces this network; custom evidence is indirect or absent |
| `external_iscas85_c6288` | `resyn2` | `fraig` | 0 | 0.412 | 16 | ABC sweep did not reduce nodes in this row |
| `external_iscas85_c6288` | `rewrite` | `fraig` | 0 | 0.944 | 37 | ABC sweep did not reduce nodes in this row |
| `generated_multiplier_2` | `balance` | `fraig` | 3 | 1.000 |  | ABC reduces while many custom exact signatures remain preserved |
| `generated_multiplier_2` | `original` | `fraig` | 3 |  |  | ABC reduces this network; custom evidence is indirect or absent |
| `generated_multiplier_2` | `resyn2` | `fraig` | 0 | 0.375 |  | ABC sweep did not reduce nodes in this row |
| `generated_multiplier_2` | `rewrite` | `fraig` | 0 | 0.625 |  | ABC sweep did not reduce nodes in this row |
| `generated_mux_tree_8` | `balance` | `fraig` | 0 | 1.000 |  | ABC sweep did not reduce nodes in this row |
| `generated_mux_tree_8` | `original` | `fraig` | 0 |  |  | ABC sweep did not reduce nodes in this row |
| `generated_mux_tree_8` | `resyn2` | `fraig` | 0 | 0.400 |  | ABC sweep did not reduce nodes in this row |
| `generated_mux_tree_8` | `rewrite` | `fraig` | 0 | 1.000 |  | ABC sweep did not reduce nodes in this row |
| `majority3` | `balance` | `fraig` | 0 | 0.750 | 0 | ABC sweep did not reduce nodes in this row |
| `majority3` | `original` | `fraig` | 0 |  |  | ABC sweep did not reduce nodes in this row |
| `majority3` | `resyn2` | `fraig` | 0 | 0.250 | 0 | ABC sweep did not reduce nodes in this row |
| `majority3` | `rewrite` | `fraig` | 0 | 1.000 |  | ABC sweep did not reduce nodes in this row |
| `mux2` | `balance` | `fraig` | 0 | 1.000 |  | ABC sweep did not reduce nodes in this row |
| `mux2` | `original` | `fraig` | 0 |  |  | ABC sweep did not reduce nodes in this row |
| `mux2` | `resyn2` | `fraig` | 0 | 0.000 |  | ABC sweep did not reduce nodes in this row |
| `mux2` | `rewrite` | `fraig` | 0 | 1.000 |  | ABC sweep did not reduce nodes in this row |
| `toy_and_or` | `balance` | `fraig` | 0 | 1.000 |  | ABC sweep did not reduce nodes in this row |
| `toy_and_or` | `original` | `fraig` | 0 |  |  | ABC sweep did not reduce nodes in this row |

Main caution: this baseline does not prove that ABC produced the same
old-to-new node mappings as the custom flow. Ordinary FRAIG output gives
swept networks and statistics, not correspondence provenance.
