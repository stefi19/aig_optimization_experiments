# Contextual Error Metrics

This experiment compares global internal-node distance with output error after contextual substitution.
Exact exhaustive rows are formal for the reported distance. Sampled rows are estimates.
CEC equivalence results are formal when ABC reports equivalence.

Global distance compares the original candidate function and the optimized target function under the same aligned primary-input assignments. It is independent of the subsequent contextual substitution test.

Some candidates produced zero observed contextual error over sampled patterns while ABC CEC still found a counterexample. These rows are classified as sampled contextual approximations, not ODC-valid or output-equivalent correspondences.

- Total candidate pairs: `40`
- Successfully substituted pairs: `40`
- Skipped/unresolved substitutions: `0`
- Globally exact pairs: `0`
- SAT/CEC-proven equivalent after structural mismatch: `0`
- ODC-valid correspondences: `0`
- Exact contextual approximations: `0`
- Sampled contextual approximations: `35`
- Unsafe candidates: `5`
- Unresolved pairs: `0`
- Exact contextual rows: `0`
- Sampled contextual rows: `40`
- Sampled-estimate evidence rows: `40`

## Classification Counts

| Classification | Count |
| --- | ---: |
| Sampled contextual approximation (`contextually_approximate_sampled`) | 35 |
| Unsafe (`unsafe_candidate`) | 5 |

## Evidence Levels

| Evidence level | Count |
| --- | ---: |
| `sampled_estimate` | 40 |

## Examples

| Circuit | Optimization | Optimized node | Candidate | Global error | Contextual error | CEC | Classification | Evidence |
| --- | --- | --- | --- | ---: | ---: | --- | --- | --- |
| `c2670` | `compress2rs` | `new_n693` | `new_n796` | 0.2471 | 0.1240 | `rejected_non_equivalent` | Unsafe (`unsafe_candidate`) | `sampled_estimate` |
| `c2670` | `refactor` | `new_n721` | `new_n796` | 0.2451 | 0.1357 | `rejected_non_equivalent` | Unsafe (`unsafe_candidate`) | `sampled_estimate` |
| `c2670` | `refactor_z` | `new_n719` | `new_n796` | 0.2422 | 0.1416 | `rejected_non_equivalent` | Unsafe (`unsafe_candidate`) | `sampled_estimate` |
| `c2670` | `resyn2` | `new_n694` | `new_n796` | 0.2480 | 0.1143 | `rejected_non_equivalent` | Unsafe (`unsafe_candidate`) | `sampled_estimate` |
| `c2670` | `resyn2_like` | `new_n694` | `new_n796` | 0.2637 | 0.1406 | `rejected_non_equivalent` | Unsafe (`unsafe_candidate`) | `sampled_estimate` |
| `c2670` | `compress2rs` | `new_n486` | `new_n602` | 0.2344 | 0.0000 | `rejected_non_equivalent` | Sampled contextual approximation (`contextually_approximate_sampled`) | `sampled_estimate` |
| `c2670` | `refactor` | `new_n549` | `new_n602` | 0.2607 | 0.0000 | `rejected_non_equivalent` | Sampled contextual approximation (`contextually_approximate_sampled`) | `sampled_estimate` |
| `c2670` | `refactor_z` | `new_n467` | `new_n602` | 0.2568 | 0.0000 | `rejected_non_equivalent` | Sampled contextual approximation (`contextually_approximate_sampled`) | `sampled_estimate` |
| `c2670` | `resyn2` | `new_n487` | `new_n602` | 0.2686 | 0.0000 | `rejected_non_equivalent` | Sampled contextual approximation (`contextually_approximate_sampled`) | `sampled_estimate` |
| `c2670` | `resyn2_like` | `new_n487` | `new_n602` | 0.2695 | 0.0000 | `rejected_non_equivalent` | Sampled contextual approximation (`contextually_approximate_sampled`) | `sampled_estimate` |

## Notes

- Numerical output error treats primary outputs as a binary vector in BLIF output order.
- `globally_exact` is assigned only for exhaustive global distance rows.
- `odc_valid_correspondence` requires global error greater than zero and ABC CEC output equivalence.
- `contextually_approximate_exact` means ABC rejected equivalence and exhaustive contextual output error is below threshold.
- `contextually_approximate_sampled` means ABC rejected equivalence and the sampled contextual output error estimate is below threshold. It is not a formal proof.
