# Proof-Carrying Semantic Functional Refactoring

This phase tests a different hypothesis from isolated grafting, closed-region
replacement, and joint region/interface discovery.  The previous real benchmark
results suggest that an explicit semantic subgraph often no longer exists after
aggressive synthesis.  Semantic functionality may be distributed through
reconvergent consumers, bypasses, and shared output cones.

The new question is whether a graph-active semantic boundary can be created by
formally decomposing an optimized logic window:

```text
Y = F(X, Z)
M = G(X)
Y = H(M, Z)
```

## Decomposition Model

The implementation introduces:

- `SemanticDivisor`: a source-blind semantic term or term DAG implementing
  `M = G(X)`;
- `RefactoringWindow`: the optimized BLIF window computing `Y = F(X, Z)`;
- `FunctionalDecompositionCandidate`: a divisor/window/residual-interface
  proposal;
- `QuotientFunction`: exact truth-table quotient `H(M, Z)`;
- `SemanticRefactoringResult`: final proof/rewrite/CEC status.

For a chosen divisor and residual set, quotient existence is proved by a
two-copy miter:

```text
M_a = G(X_a)
M_b = G(X_b)
Y_a = F(X_a, Z_a)
Y_b = F(X_b, Z_b)

constrain M_a = M_b and Z_a = Z_b
ask SAT for Y_a != Y_b
```

SAT is a concrete decomposition counterexample.  UNSAT proves that an exact
quotient exists for this `G/Z/window` configuration.  Every SAT counterexample
is replayed through the concrete BLIF evaluator before it is recorded.

## Quotient Synthesis

The committed backend constructs exact truth-table quotients for bounded
interfaces.  It records a completion policy for unreachable `(M, Z)` inputs:
`zero_completion_for_unreachable_mz`.  Quotient construction is not accepted on
its own; the emitted quotient is independently proved with Z3 against the
original window:

```text
F(X, Z) = H(G(X), Z)
```

## Non-Vacuity

Accepted refactorings must satisfy:

- `H` depends on at least one bit of `M`;
- the divisor is not an identity copy of all original inputs;
- the rewritten graph has a real consumer of the divisor output;
- ABC global CEC proves the rewritten BLIF equivalent to the original;
- resynthesis-survival metadata records that the graph-active semantic path is
  still present after the required serialization/proof flow.

## Controlled Benchmarks

The controlled suite contains distributed functions where no original BLIF node
named `M` is present.  Positive cases cover:

- distributed affine divisor;
- shared add-add divisor;
- bilinear divisor;
- MAC divisor;
- reordered multi-output divisor;
- Boolean-obscured divisor;
- a case where closed-region replacement is labeled as failed but
  decomposition succeeds;
- a case where joint region/interface search is labeled as failed by bypasses
  but decomposition succeeds;
- a case requiring a residual variable;
- a case requiring multi-output `M`.

Negative controls cover:

- formally non-decomposable selected divisor/residual/window;
- quotient that ignores `M`;
- identity/vacuous divisor.

## Results

Current committed results under `results/semantic_functional_refactoring/`:

- controlled experiments: 13;
- controlled decomposable candidates: 12;
- decomposition counterexamples: 1, reproduced 1/1;
- exact quotients synthesized and independently proved: 12;
- quotient-depends-on-`M` decompositions: 11;
- non-identity accepted decompositions: 10;
- controlled graph-active ABC-equivalent refactorings: 10;
- controlled restored boundaries: 10;
- real attempts: 58;
- development real attempts: 49, restored 0;
- held-out real attempts: 9, restored 0;
- real source-blind held-out semantic boundaries created: 0.

Baseline comparison:

- isolated semantic grafting: 276 real attempts, 0 restorations;
- fixed semantic region replacement: 5 controlled restorations;
- joint region/interface discovery: 8 controlled restorations;
- semantic functional refactoring: 10 controlled restorations, 0 real
  restorations.

## Failure Taxonomy

Controlled failures:

- formally non-decomposable for selected `G/Z/window`: 1;
- quotient ignores `M`: 1;
- identity/vacuous decomposition: 1.

Real failures:

- no semantic divisor/window/interface under bounds: 23;
- no relevant consumer window or verified divisor under bounds: 12;
- distributed consumers with no bounded quotient window: 8;
- window exceeds bounds or whole-design risk: 8;
- no exact non-vacuous decomposition found under bounds: 7.

These are bounded-search outcomes, not mathematical impossibility claims.

## Reproducibility

```bash
make semantic-functional-refactoring-all
make check-semantic-functional-refactoring-results
.venv-z3/bin/python -m pytest -q tests/test_semantic_functional_refactoring.py
```

The result checker rejects restored-boundary rows that lack UNSAT
decomposability proof, independent quotient proof, non-vacuity, graph-active
divisor consumers, ABC global CEC, and resynthesis-survival evidence.

## Supported Claim

The phase demonstrates source-blind, proof-carrying semantic functional
decomposition and graph-active refactoring on controlled distributed-logic
benchmarks.  It does not yet create a real held-out semantic boundary.  The
principal remaining limitation is real-window/divisor discovery under bounded
source-blind search, not the controlled quotient proof or graph rewrite stack.

## Related Work Positioning

This phase connects template-based circuit understanding, structural and
functional netlist reverse engineering, arithmetic recovery, functional
decomposition, SyGuS-style bit-vector synthesis, SAT sweeping, and ECO-style
logic rewriting.  The contribution is the proof-carrying combination for
creating graph-active semantic boundaries after aggressive synthesis has removed
or distributed the original cut-points.

## Successor Phase: Recoverability Frontier

The functional-refactoring phase proves that the divisor/quotient/refactoring
mechanism works when a useful divisor and window are found, but it leaves the
real null result unresolved. The successor phase in
[`docs/semantic_recoverability_frontier.md`](semantic_recoverability_frontier.md)
therefore studies entire ABC synthesis trajectories. It records source
boundaries before optimisation, saves CEC-equivalent checkpoints after passes,
and compares blind recoverability against oracle divisor/support/window
diagnostics.

The committed frontier run has 4 designs, 5 boundaries, 12 trajectories, and
60 CEC-equivalent checkpoints. It records 59/300 blind structural or functional
survival rows and 81/180 oracle decomposition rows. This is not a new
graph-active real restoration claim; it localizes the question to compact,
local, source-blind recoverability along optimisation trajectories.
