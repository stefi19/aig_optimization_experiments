# Formal ODC-Aware Boundary Anchors

This milestone adds a contextual anchor category:

```text
formal_odc_valid_anchor
```

An ODC-valid anchor is not a global equivalence claim. It means the
specification node and implementation node are formally interchangeable only for
a named observation context.

## Context Modes

`global_output_odc` uses every primary output as observable. This is the
strongest contextual mode in this prototype.

`coi_output_odc` uses the canonical COI boundary outputs as the observable set.
This is a weaker, COI-specific experiment. These anchors must not be reused for
another COI or another observable-output set.

## Formal Construction

For a candidate pair `(spec_node, impl_node)`:

1. Parse the original specification BLIF and optimized implementation BLIF.
2. Validate matching primary-input order, node existence, observable outputs,
   and polarity.
3. Build a copy of the implementation where `impl_node` is replaced by the
   cone rooted at `spec_node`.
4. Restrict both circuits to the selected observable outputs.
5. Run ABC `cec` on baseline implementation versus substituted implementation.

If ABC proves the two observable-output circuits equivalent, the row is:

```text
mapping_category = formal_odc_valid_anchor
evidence_level   = formal_contextual
equivalence_scope = contextual
proof_status     = proven_odc_valid
```

Timeouts, tool errors, sampled candidates, and disproven candidates are never
loaded into `formal_plus_odc`.

## Boundary-Level Check

Every boundary that becomes valid through selected ODC anchors is checked again
as a complete contextual replacement over the same observable-output set. The
boundary is counted only when this second proof is also valid.

## Current Result

```text
candidate pairs generated:       164
formal checks attempted:         164
formal ODC anchors proven:        10
candidates disproved:            118
alignment failures:               36
timeouts/tool errors:              0

formal_all baseline:             0 / 24 failed-case rows
formal_plus_odc:                 6 / 24 failed-case rows
global_output_odc rows:          4 successful rows
coi_output_odc rows:             2 successful rows
selected ODC anchors:            16 across recovery rows
unique recovered triples:         3 benchmark/optimization/COI triples
```

The recovered rows are contextual successes, not global internal-node
equivalence. They show that ODC-aware anchors can recover some boundaries that
global formal anchors could not recover, while remaining failures still point to
missing relevant anchors or invalid extended boundaries.
