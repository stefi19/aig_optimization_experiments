# Equivalence-Anchored Boundary Recovery Summary

This prototype recovers coherent regions enclosed by formally anchored input and output cuts. It does not claim direct node equivalence for every internal node in a recovered region.

- Cases: 48
- Successful recovered boundaries: 8 (16.7%)
- Failure / skipped rows: 40

## Overall by Anchor Mode

| anchor_mode | cases | cycle_conflict_count | mean_boundary_extension_ratio | mean_extended_region_node_count | recovery_success_count | recovery_success_rate |
| --- | --- | --- | --- | --- | --- | --- |
| exact_only | 24 | 0 | 0.11233660130718955 | 3.2916666666666665 | 4 | 0.16666666666666666 |
| formal_all | 24 | 0 | 0.11233660130718955 | 3.2916666666666665 | 4 | 0.16666666666666666 |

## Failure Reasons

| failure_reason | count |
| --- | --- |
| COI nodes are not enclosed by recovered region | 10 |
| missing_spec_circuit | 16 |
| not every fanout path from 'new_n10' crosses EBO | 4 |
| not every fanout path from 'new_n23' crosses EBO | 6 |
| recovered region expands to nearly the whole design | 4 |

## Interpretation

A successful row means the COI is enclosed by selected formal anchors at the recovered cuts. It does not mean every node inside the region has a direct node-level match.
