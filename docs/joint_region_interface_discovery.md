# Counterexample-Guided Joint Region and Interface Discovery

This phase changes the abstraction again.  The previous semantic grafting result
proved that isolated reconstructed expressions are not enough: 46 formal SMT
expressions produced 276 bounded placement attempts and 0 usable graph-active
anchors.  The later closed-region replacement phase validated the graph rewrite
and proof stack on controlled regions, but still assumed the region/interface
was already selected.

The new question is whether region and interface can be discovered jointly,
using proof counterexamples to repair both the selected implementation region
and its input/output cut.

## Research Questions

1. Can source-blind search discover a closed implementation region and the
   corresponding cut interface at the same time?
2. Can counterexamples guide concrete repairs such as adding a missing cut
   input, promoting a missing output, or fixing output-bit order?
3. Once a semantic module is proven, can graph-level replacement restore a
   usable boundary without relying on disconnected anchors?

## Threat Model

The primary search is source-blind.  It records only graph-derived seed state,
cut membership, proof feedback, and deterministic repair operations.  It does
not use source family, operator, expression, bus names, constants, signedness,
or evaluation-derived accuracy fields to generate or rank candidates.

Ground-truth-style expected outcomes appear only in controlled benchmark result
rows so the negative and positive guards can be checked after inference.

## Candidate Model

`JointRegionInterfaceCandidate` records:

- implementation region nodes;
- input cut;
- output cut;
- external fanout edges;
- observable outputs;
- inferred scalar buses;
- semantic hypothesis id;
- free-cut or contextual proof scope;
- closure status;
- last counterexample;
- repair history;
- deterministic fingerprint.

The closure validator requires every incoming edge into the region to originate
in the input cut, every outgoing edge to originate in the output cut, no removed
node to have unaccounted fanout, no removed-node dependency in a replacement
input, and no whole-design expansion.

## Search

The committed experiment uses a deterministic bounded beam over structural
seeds.  The implemented repair operations are:

- add missing cut input;
- promote output-cut node;
- reorder output bits;
- contract irrelevant nodes;
- absorb proof counterexamples into the semantic hypothesis;
- complete the region after interface repair.

Every transition is written to
`results/joint_region_interface_discovery/search_transitions.csv`.  Proof
feedback rows in `counterexample_diagnostics.csv` must set
`counterexample_reproduced=true` and `influenced_next_candidate=true`.

## Proof Stack

An accepted replacement requires:

- closed-region validation;
- multi-output Z3 free-cut proof for the semantic module;
- emitted BLIF checked against the AST-level semantics;
- graph rewrite validation after serialise/reparse;
- graph-active replacement outputs;
- ABC CEC between the original implementation and rewritten implementation;
- boundary-restoration accounting.

No timeout, unsupported proof, contextual-only result, disconnected module, or
ABC failure is counted as a restored boundary.

## Results

Current committed results under `results/joint_region_interface_discovery/`:

- controlled cases attempted: 10;
- candidate states: 37;
- search transitions: 14;
- controlled graph-active replacements accepted: 8;
- controlled boundaries restored: 8;
- controlled affine recovery: 1/1;
- controlled add-add recovery: 1/1;
- controlled bilinear recovery: 1/1;
- controlled MAC recovery: 1/1;
- controlled mux recovery: 1/1;
- negative controls rejected: 2/2;
- prior historical isolated-anchor diagnostic rows revisited: 46;
- fresh source-blind structural diagnostic seeds evaluated: 12;
- development diagnostic split: 49 rows, 0 restorations;
- held-out diagnostic split: 9 rows, 0 restorations;
- provenance-complete real graph-active restorations: 0.

The controlled cases show that the joint abstraction can repair missing
interfaces and then pass the complete proof-carrying replacement stack.  The
historical null result remains: starting from the earlier isolated-anchor
diagnostic seeds, bounded source-blind joint search still does not form legal
closed replacement regions. These rows predate the provenance-first eligibility
audit, so they are diagnostics rather than a corrected denominator of eligible
real graph-rewrite attempts.

## Failure Analysis

The historical diagnostic revisit classifies the old failures into
structural/interface blockers:

- no source-blind closed input cut;
- semantic target outside the closed frontier;
- no legal external-fanout mapping;
- bounded search reaching whole-design risk;
- no legal closed region under the configured bounds.

This is not a semantic-proof failure.  It says the prior real seeds are not
sufficient to define a closed replaceable subgraph.  A future positive real
result likely needs broader structural region enumeration and stronger
specification-side cut alignment, not another isolated anchor placement
heuristic.

## Reproducibility

Run:

```bash
make joint-region-interface-all
make check-joint-region-interface-results
.venv-z3/bin/python -m pytest -q tests/test_joint_region_interface.py
```

Normal CI may run the checker with `--allow-no-abc`; that mode is limited to
schema and rejection checks. The full result uses the pinned repository ABC
binary from `make check-abc`, and every accepted replacement or restored
boundary must record `abc_available=true` plus equivalent global CEC.

## Related Work Positioning

This phase combines ideas from template-based circuit understanding and PICEC,
structural and functional netlist reverse engineering, arithmetic netlist
recovery, SyGuS-style bit-vector synthesis, hierarchical boundary recovery by
SAT sweeping, and logic grafting/ECO flows.  The contribution is the
source-blind, proof-carrying combination for hierarchy restoration after
aggressive synthesis removes original internal cut-points, not CEGIS, SMT, or
grafting in isolation.

## Successor Phase: Functional Refactoring

The joint phase still asks the search to find an existing closed semantic
region.  The follow-up phase in
[`docs/proof_carrying_semantic_functional_refactoring.md`](proof_carrying_semantic_functional_refactoring.md)
tests a different hypothesis: an optimized window may not contain a closed
semantic subgraph, but it may be exactly decomposable as `Y = H(G(X), Z)`.

Current functional-refactoring results:

- 13 controlled decomposition/refactoring cases;
- 12 controlled decomposable candidates;
- 12 exact quotients synthesized and independently Z3-proved;
- 10 controlled graph-active ABC-equivalent refactorings;
- 10 controlled restored semantic boundaries;
- 49 development diagnostic rows and 9 held-out diagnostic rows;
- 0 provenance-complete real graph-active restorations under the bounded
  source-blind search.

This preserves the joint-discovery result as a controlled proof-stack success
while making the next real blocker explicit: source-blind discovery of useful
semantic divisors, quotient windows, and residual interfaces in optimized real
circuits.
