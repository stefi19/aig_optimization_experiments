# ABC Provenance / Equivalence-Class Investigation

## Motivation

The ABC-native SAT sweeping baseline showed that `fraig` and `&fraig -x` can reduce
redundant structure using ABC's standard AIG/SAT machinery. That is useful as a
classical synthesis/verification baseline, but the correspondence project needs a
different artifact: a mapping from optimized nodes back to original nodes, especially
for critical-path back-mapping.

Carmine's suggestion motivates a follow-up question:

```text
Can ABC-native sweeping expose enough merge provenance or equivalence-class data to
replace, validate, or strengthen the custom correspondence layer?
```

This note records a deliberately small investigation rather than a replacement claim.

## What This Probe Tests

The script `scripts/investigate_abc_provenance.py` creates controlled BLIF examples in a
temporary directory:

- duplicate `a AND b` internal nodes,
- commuted `a AND b` and `b AND a` internal nodes,
- same-support but non-equivalent `a AND b` and `a OR b` internal nodes.

For each example it runs:

```text
read_blif <example>; strash; fraig; write_blif <swept>; ps
read_blif <example>; strash; &get -n; &fraig -x; &put; write_blif <swept>; ps
```

It also runs a light real benchmark sample on `external_iscas85_c432` after a `rewrite`
optimization. This keeps the default target quick while exercising a non-toy circuit.

## What Is Measured

The probe records:

- whether each command or flow is supported by the local ABC build,
- whether sampled internal node names survive in the written swept BLIF,
- before/after `and` and `lev` counts when `ps` statistics are printed,
- whether stdout/stderr or auxiliary output visibly reports merges,
- whether explicit equivalence classes or merge provenance are exposed.

The outputs are:

- `results/abc_provenance_probe.csv`
- `results/abc_provenance_probe.md`
- `results/plots/abc_provenance_summary.png`

The plot is copied into the offline presentation assets when generated.

## Interpretation Rules

This probe is intentionally conservative.

ABC may merge equivalent structure internally while still writing a BLIF that has
renamed nodes or only preserves primary-output-level names. A node name surviving in
the output is therefore only weak evidence. A node name disappearing is also not a
proof that ABC lacks the information internally; it only means ordinary written BLIF
output is not a provenance interface.

Similarly, `ps` and `print_stats` are useful for network-level reduction metrics, but
they do not identify which old node merged into which new node. `cec` can prove whole
network equivalence, but it does not by itself expose internal correspondence classes.

## Research Consequence

If ordinary ABC commands only provide swept networks and aggregate statistics, then
ABC-native FRAIG remains a valuable reference flow, but it does not replace the custom
correspondence pipeline. The custom layer remains necessary for:

- explicit candidate correspondence tables,
- SAT/CEC-proven equivalence after structural mismatch,
- approximate near-match analysis,
- critical-path node back-mapping.

The next deeper ABC integration path would be to investigate commands or
instrumentation that expose equivalence classes, simulation classes, or merge
provenance directly from ABC's FRAIG/SAT-sweeping internals.
