# Formal Locality-Barrier Certificates

## Motivation

The cross-netlist transplantation phase proved that the controlled construction
works, but the 56 historical diagnostic revisits still produced zero
graph-active transplants.
Those failures were previously labelled as bounded input-interface or
output-window failures. This phase asks a sharper question before adding more
heuristics:

> Is the correspondence missing from the search, or is the required interface
> non-local under the declared universe and bounds?

The object of study is compact, local, source-side functional sufficiency. This
is not a claim that semantic information is absolutely destroyed. For aligned
deterministic combinational circuits, the full primary-input vector determines
every optimized internal node; whole-PI solutions are therefore diagnostics, not
local successes.

## Formal Definitions

For input interfaces, a source signal subset `C` is sufficient for an optimized
target vector `T` iff no two primary-input assignments `Pa` and `Pb` satisfy:

```text
C(Pa) = C(Pb)
T(Pa) != T(Pb)
```

The implementation checks this with an exact two-copy miter. SAT returns a
distinguishability counterexample. UNSAT proves sufficiency for the declared
target, source/optimized artifacts, PI alignment, universe, and bounds.

For each SAT pair, the difference set

```text
D_U(Pa, Pb) = {u in U | u(Pa) != u(Pb)}
```

is a hitting-set constraint: every sufficient interface must intersect it. A
minimum hitting-set lower bound plus a sufficient candidate of the same width is
an exact minimum certificate.

Output-window certificates use the corresponding two-copy condition:

```text
B(Pa) = B(Pb)
Z(Pa) = Z(Pb)
YS(Pa) != YS(Pb)
```

where `B` is an optimized-region output interface, `Z` is residual source
information, and `YS` is the source output frontier.

## Implementation

The phase adds:

- `formal_locality_barriers.py`: data model, deterministic universe hashes,
  exact BLIF evaluation, two-copy sufficiency checks, difference sets, and
  CEGIS-style hitting-set minimum search.
- `scripts/run_formal_locality_barriers.py`: controlled and real experiment
  runner.
- `scripts/check_formal_locality_barrier_results.py`: independent checker.
- `scripts/formal_locality_barrier_plots.py`: reproducible plots.
- `configs/formal_locality_barriers.json`: frozen source-blind configuration.

The BLIF evaluator used by this phase handles ABC's `0`-polarity `.names`
covers, which is required for generated ABC BLIF variants.

## Current Results

Artifacts are under `results/formal_locality_barriers/`.

Controlled exact-minimum cases:

- 6/6 controlled cases match the expected exhaustive minimum.
- Controlled minima cover width 1, width 2, width 3, permutation/inversion,
  nonlinear Boolean, and affine-style Boolean arithmetic.
- All recorded SAT counterexamples replay through concrete evaluators.

Existing 56 historical diagnostic rows:

- 56/56 rows audited.
- 20/20 old output-window rows resolve to source/optimized BLIF artifacts with
  aligned PIs.
- 36/36 fresh `controlled_*__b0` input-interface rows lack enough recorded
  optimized-target provenance for formal cross-netlist analysis and are
  classified as `insufficient_target_provenance`.
- 20/20 resolved output-window rows have compact exact input certificates for
  the optimized target itself.
- Output-window sufficiency is the real blocker for those 20 rows: 17 require a
  residual interface wider than the configured compact bound; 3 have compact
  output interfaces within the declared B/Z universe.
- Target-utility checks find 0 influential output interfaces and 20 interfaces
  where the chosen target is not functionally necessary once the residual
  interface is included.
- Certificate-guided transplantation remains 0 real graph-active transplants
  and 0 real boundaries because certificate existence is not counted as graph
  rewrite success.

The successor provenance-complete necessity-first phase corrects the
denominator: these 56 rows are not 56 eligible real transplantation attempts.
They consist of 36 provenance-incomplete rows and 20 target-irrelevant
diagnostic rows, so the historical eligible graph-rewrite denominator is 0.

These numbers preserve the previous null transplant result. The stronger claim
is that the old labels have been refined into formal provenance, input-minimum,
output-minimum, and target-utility evidence categories.

## Evidence Rules

- Exact minima require UNSAT sufficiency and a matching hitting-set lower bound.
- Lower bounds require replayable difference sets.
- SAT counterexamples are stored as JSON assignments and replayed.
- Whole-PI diagnostics are labelled `global_diagnostic_not_local_success`.
- Certificate-guided rows are not blind transplant successes.
- No boundary is counted without graph activity and both global ABC CEC scopes.
- No timeout or unsupported status is treated as disproval.

## Reproduction

```bash
make formal-locality-all
make check-formal-locality-results
.venv-z3/bin/python -m pytest -q tests/test_formal_locality_barriers.py
```

CI runs lightweight controlled certificate/checker tests in both portable
no-ABC and full-ABC modes.

## Limitations

Certificates apply only to their declared universes and bounds. A
`local_input_universe_formally_insufficient` result would not imply global
semantic impossibility. In the current committed run, the primary real blocker
for the 36 input rows is target provenance, not a proved non-local lower bound.
For the 20 resolved output rows, the exact output-interface search is scoped to
the declared B/Z universe used by the runner.

The next useful research step is provenance repair for the 36 unresolved fresh
targets and a source-blind graph rewrite backend that can propose functionally
necessary output interfaces rather than residual-only quotients.
