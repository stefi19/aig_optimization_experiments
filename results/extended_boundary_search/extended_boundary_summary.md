# Extended-Boundary Search Summary

## Identity Regression

- Identity remains enforced by `make boundary-recovery-identity-fixed`: 14 / 14 identity success, zero extension, exact EBI, exact EBO, exact region.

## Optimized Extended-Boundary Validity

- Valid extended boundaries: 40 / 64 rows

## Strategy Comparison

- `cost_guided`: 20 / 32
- `first_frontier`: 20 / 32

## Anchor Modes

- `exact_only`: 20 / 32; selected SAT/CEC anchors: 0
- `formal_all`: 20 / 32; selected SAT/CEC anchors: 0

## Previous Failures

- Previous false negatives under extended validation: 0
- Fixed by cost-guided search: 0

## Remaining Bottleneck

- blocked_by_extension_limit: 2
- blocked_by_missing_relevant_anchors: 22

Extended-boundary success means the original COI is contained in a non-whole-design recovered region with formally anchored input/output cuts and no bypasses relative to that recovered region. It does not imply internal-node equivalence for every node in the region.
