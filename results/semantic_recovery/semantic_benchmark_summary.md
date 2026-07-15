# Semantic Recovery Benchmark Suite

This generated suite is a ground-truth source-level benchmark layer for future RTL-expression recovery experiments. RTL is generated for every case. Exact BLIF and ABC flow variants are generated only for cases whose flat input space is small enough for deterministic truth-table emission.

- Schema version: `semantic_recovery_benchmark_v1`
- Generation seed: `20260716`
- Cases: 258
- Families: arithmetic=73, bitmanip=56, boolean=52, comparison=42, control=35
- Input widths covered: 1, 2, 3, 4, 6, 7, 8, 12, 16
- Exact source BLIF cases: 127
- Variant rows: 2322

## Flow Status

| Flow | Generated | Skipped RTL-only | Skipped too large | Skipped no ABC | Failed |
| --- | ---: | ---: | ---: | ---: | ---: |
| `identity` | 127 | 131 | 0 | 0 | 0 |
| `balance` | 54 | 131 | 73 | 0 | 0 |
| `rewrite` | 54 | 131 | 73 | 0 | 0 |
| `refactor` | 54 | 131 | 73 | 0 | 0 |
| `resub` | 54 | 131 | 73 | 0 | 0 |
| `resyn` | 54 | 131 | 73 | 0 | 0 |
| `resyn2` | 54 | 131 | 73 | 0 | 0 |
| `dc2` | 54 | 131 | 73 | 0 | 0 |
| `compress2rs` | 54 | 131 | 73 | 0 | 0 |

## Interpretation

These benchmarks do not claim recovered RTL yet. They provide known source expressions, bus metadata, and bounded gate-level implementations so later phases can test semantic template recovery, CEGIS validation, and cost-aware RTL selection against ground truth.
