# Register Insertion Suggestion Prototype

These rows are candidate locations for engineer review. They are not automatic RTL edits.

- Suggestions generated: `30`
- Scoring favors path-midpoint balance, exact/SAT-backed mappings, existing confidence, and support/simulation signals.
- Unresolved path nodes are excluded.

## Example Suggestions

| Benchmark | Optimization | Original node | Optimized node | Path position | Category | Score |
| --- | --- | --- | --- | --- | --- | --- |
| `external_iscas85_c2670` | `resub` | `new_n856` | `new_n793` | `11/21` | `exact` | `1.000` |
| `external_iscas85_c2670` | `rewrite_z` | `new_n856` | `new_n729` | `11/21` | `exact` | `1.000` |
| `external_iscas85_c432` | `resub` | `new_n114` | `new_n128` | `21/41` | `exact` | `1.000` |
| `external_iscas85_c432` | `rewrite` | `new_n114` | `new_n144` | `21/41` | `exact` | `1.000` |
| `external_iscas85_c6288` | `rewrite` | `new_n1143` | `new_n1143` | `59/117` | `exact` | `1.000` |

## Caveat

A real register insertion must update RTL and verify the resulting sequential behavior.
This prototype only ranks places on mapped critical paths where an engineer might start looking.
