# ABC-Native SAT Sweep Baseline

This is an exploratory baseline. ABC is used to sweep one optimized network at a
time; unless ABC exposes classes in the log, this measures structural reductions,
not direct node correspondence mappings.

Rows collected: 64
Completed flow rows: 64

| Flow | Rows | Mean node reduction | Mean level reduction |
|---|---:|---:|---:|
| `amp_fraig_x` | 32 | 5.72 | 0.25 |
| `fraig` | 32 | 5.72 | 0.25 |

## Largest Node Reductions

| Benchmark | Optimization | Flow | Before | After | Delta |
|---|---|---|---:|---:|---:|
| `external_iscas85_c432` | `original` | `fraig` | 209 | 171 | 38 |
| `external_iscas85_c432` | `original` | `amp_fraig_x` | 209 | 171 | 38 |
| `external_iscas85_c2670` | `balance` | `fraig` | 714 | 677 | 37 |
| `external_iscas85_c2670` | `balance` | `amp_fraig_x` | 714 | 677 | 37 |
| `external_iscas85_c432` | `balance` | `fraig` | 209 | 173 | 36 |
| `external_iscas85_c432` | `balance` | `amp_fraig_x` | 209 | 173 | 36 |
| `external_iscas85_c2670` | `original` | `fraig` | 717 | 688 | 29 |
| `external_iscas85_c2670` | `original` | `amp_fraig_x` | 717 | 688 | 29 |
| `external_iscas85_c432` | `rewrite` | `fraig` | 194 | 170 | 24 |
| `external_iscas85_c432` | `rewrite` | `amp_fraig_x` | 194 | 170 | 24 |
| `external_iscas85_c432` | `resyn2` | `fraig` | 136 | 130 | 6 |
| `external_iscas85_c432` | `resyn2` | `amp_fraig_x` | 136 | 130 | 6 |
