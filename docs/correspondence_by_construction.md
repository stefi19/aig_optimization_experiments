# Correspondence by Construction Through Anchored-Cut Wire Materialization

This milestone asks whether correspondence can be constructed when an optimized
internal signal has no matching pre-existing node in the original circuit.

The experiment is intentionally Boolean-level and additive:

```text
unmatched optimized frontier node
-> small optimized-side cut
-> globally formal cut-leaf anchors
-> exact target function over the cut
-> transferred original-side redundant wire
-> exhaustive global proof
-> optional boundary-recovery reuse
```

No original outputs are rewired. No existing node is deleted. The materialized
wire is a new redundant original-side signal, not a signal that existed in the
original RTL or original netlist.

## Evidence Model

Accepted materialized anchors use:

```text
anchor_origin = materialized_wire
mapping_category = formal_materialized_anchor
evidence_level = formal_exhaustive
equivalence_scope = global
proof_status = proven_materialized_anchor
```

Sampled simulation is not used as proof. In this first implementation the proof
backend is exhaustive global truth-table comparison over aligned primary inputs
for small circuits. A candidate is rejected or left unsupported if the circuit is
too large for exhaustive checking, if primary-input alignment fails, if hidden
support remains outside the cut, or if the augmented original circuit changes
any original primary output.

## Anchored Cuts

For a target implementation node `i`, the enumerator searches backward through
the implementation graph and stops at globally formal anchors:

- `exact_signature_match`
- `complemented_equivalence`
- `sat_cec_proven_equivalent`

ODC-only contextual anchors are deliberately excluded from the primary global
experiment. Leaf polarity is preserved. If an implementation leaf maps to the
inverted original-side signal, the truth table is transferred with that inversion
applied.

Default limits are small and deterministic: cut sizes up to three, bounded
frontier depth, and bounded cuts per target.

## Function Extraction and Materialization

For each cut, the implementation target is evaluated exhaustively over primary
inputs. The extractor groups assignments by cut-leaf values. If one cut-leaf
assignment can produce two target values, the cut has hidden support and is
rejected.

Accepted functions are materialized as compact BLIF `.names` LUT/SOP nodes in
an augmented copy of the original circuit. The augmented copy preserves the
original primary-output list exactly.

## Current Results

The committed lightweight run reports:

- unmatched targets attempted: 20;
- anchored cuts generated: 128;
- functions extracted: 20;
- materialization candidates: 20;
- formal checks: 20;
- proven materialized anchors: 20;
- usable frontier materialized anchors: 0;
- selected materialized anchors: 0;
- newly recovered boundaries: 0.

The proof phase works on the small generated boundary cases. The boundary-reuse
phase is negative: additive materialized wires are not reconnected into the
original boundary graph, so the current boundary search does not encounter or
select them. The bottleneck is therefore graph integration and target utility,
not proof generation.

## Failure Taxonomy

The current run records two main bottlenecks:

- `hidden_support`: many candidate cuts were too small to fully determine the
  target function;
- `proven_anchor_not_on_usable_frontier`: proven redundant wires were not usable
  by the existing boundary-recovery graph because they are additive and
  disconnected from original fanout.

## Interpretation

This is a useful negative result. It shows that small-cut construction can
produce formally proven redundant wires, but additive construction alone does
not automatically improve boundary recovery. A future phase needs either:

- boundary-utility-aware target selection;
- a non-destructive way to expose materialized wires on relevant cut frontiers;
- semantic-guided materialization for larger or arithmetic-like cuts;
- or destructive-but-equivalent rewriting followed by global CEC.

Do not interpret a materialized anchor as evidence that the wire existed in the
original design.
