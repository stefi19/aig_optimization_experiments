# Contextual Error Metrics

This experiment compares global internal-node distance with output error after contextual substitution.
Exact exhaustive rows are formal for the reported distance. Sampled rows are estimates.
CEC equivalence results are formal when ABC reports equivalence.

- Total candidate pairs: `40`
- Successfully substituted pairs: `40`
- Skipped/unresolved substitutions: `0`
- Globally exact pairs: `0`
- ODC-valid correspondences: `0`
- Contextually approximate pairs: `35`
- Unsafe candidates: `5`
- Unresolved pairs: `0`
- Exact contextual rows: `0`
- Sampled contextual rows: `40`

## Classification Counts

| Classification | Count |
| --- | ---: |
| `contextually_approximate` | 35 |
| `unsafe_candidate` | 5 |

## Examples

| Circuit | Optimization | Optimized node | Candidate | Global error | Contextual error | CEC | Classification |
| --- | --- | --- | --- | ---: | ---: | --- | --- |
| `c2670` | `compress2rs` | `new_n693` | `new_n796` | 0.2725 | 0.1533 | `rejected_non_equivalent` | `unsafe_candidate` |
| `c2670` | `refactor` | `new_n721` | `new_n796` | 0.2324 | 0.1318 | `rejected_non_equivalent` | `unsafe_candidate` |
| `c2670` | `refactor_z` | `new_n719` | `new_n796` | 0.2383 | 0.1338 | `rejected_non_equivalent` | `unsafe_candidate` |
| `c2670` | `resyn2` | `new_n694` | `new_n796` | 0.2432 | 0.1309 | `rejected_non_equivalent` | `unsafe_candidate` |
| `c2670` | `resyn2_like` | `new_n694` | `new_n796` | 0.2529 | 0.1318 | `rejected_non_equivalent` | `unsafe_candidate` |
| `c2670` | `compress2rs` | `new_n486` | `new_n602` | 0.2285 | 0.0000 | `rejected_non_equivalent` | `contextually_approximate` |
| `c2670` | `refactor` | `new_n549` | `new_n602` | 0.2568 | 0.0000 | `rejected_non_equivalent` | `contextually_approximate` |
| `c2670` | `refactor_z` | `new_n467` | `new_n602` | 0.2344 | 0.0000 | `rejected_non_equivalent` | `contextually_approximate` |
| `c2670` | `resyn2` | `new_n487` | `new_n602` | 0.2422 | 0.0000 | `rejected_non_equivalent` | `contextually_approximate` |
| `c2670` | `resyn2_like` | `new_n487` | `new_n602` | 0.2588 | 0.0000 | `rejected_non_equivalent` | `contextually_approximate` |

## Notes

- Numerical output error treats primary outputs as a binary vector in BLIF output order.
- `globally_exact` is assigned only for exhaustive global distance rows.
- `odc_valid_correspondence` requires global error greater than zero and ABC CEC output equivalence.
- Sampled contextual error can rank candidates but is not a formal proof.
