# Proof-Carrying Cross-Netlist Cut Transplantation

## Motivation

The previous phases established two facts that have to be held together.
Z3-backed blind semantic CEGIS can recover and prove optimized arithmetic
expressions, including 12- and 16-bit cases.  But isolated semantic anchors and
additive source-side wires do not restore hierarchy unless they become active
on a legal graph frontier.

This phase replaces the single-anchor requirement with a cross-netlist cut
transplant:

```text
AS,Zin -> Ein -> AI -> cloned optimized RI -> BI,Zout -> Eout -> BS
```

The method is still source-blind during construction.  It may use source and
optimized Boolean behavior at the selected cuts, but it does not use original
RTL expression, operator, family, or manifest constants to choose or rank blind
candidates.

## Research Questions

1. Can bounded relational input adapters align a source cut `AS` with an
   optimized region input cut `AI` when no leaf-wise anchor exists?
2. Can bounded output adapters remove the requirement that an existing source
   consumer window already uses the optimized target?
3. Can a cloned optimized region plus exact adapters create a graph-active
   source counterpart that passes local proof, cross-target proof, and global
   ABC CEC?
4. If real cases remain negative, can the failure be localized to input
   interface sufficiency, output interface sufficiency, region pairing, graph
   rewrite, or global equivalence?

The contribution is proof-carrying cross-netlist cut transplantation with
relational interface synthesis.  It is not a claim that CEGIS, SMT, template
matching, GF(2) solving, or ECO-style graph rewriting is novel.

## Candidate Model

The pipeline records a first-class `CrossNetlistTransplantCandidate` with:

- target identity, split, optimization flow, and deterministic fingerprint;
- optimized region `RI`, optimized input cut `AI`, and optimized output cut
  `BI`;
- source cut `AS`, source output boundary `BS`, input residuals `Zin`, and
  output residuals `Zout`;
- exact input adapter `Ein(AS,Zin) = AI`;
- cloned optimized region nodes `XRI`;
- exact output adapter `Eout(BI,Zout) = BS`;
- local proof, cross-target proof, graph rewrite status, ABC CEC status,
  boundary utility, critical-path utility, durability status, and rejection
  reason.

The model removes two earlier strict assumptions:

- A source leaf does not need to be equivalent to each optimized cut input.
  `Ein` may be a permutation, inversion, XOR basis change, or bounded nonlinear
  Boolean adapter.
- A source consumer window does not need to already contain the optimized
  target.  `Eout` may reconstruct the source boundary outputs from the cloned
  optimized outputs and explicit residual inputs.

## Adapter Synthesis

Adapters are synthesized exactly by two-copy functional consistency over the
declared interface.  For each primary-input assignment, the runner computes the
candidate interface value and requested adapter output.  If two assignments have
the same interface but different required output, the adapter is rejected with a
concretely reproducible counterexample.  Otherwise the exact adapter is emitted
as a BLIF truth-table cover.

The current implementation is deliberately bounded and exact.  Timeouts or
unsupported interface widths are unresolved, never accepted.

Relational interfaces are labelled separately.  They cover cases where the
interface is not simply a leaf-wise source mapping, for example XOR basis or
nonlinear Boolean source cuts.

## Graph Rewrite

For an accepted controlled transplant, the runner:

1. writes the source BLIF;
2. synthesizes `Ein`;
3. writes the optimized region BLIF;
4. synthesizes `Eout`;
5. builds a standalone optimized implementation for cross-CEC;
6. clones `RI` into the source graph using deterministic `xri_` names;
7. connects `Ein` outputs to cloned region inputs;
8. connects cloned region outputs through `Eout` to the original source primary
   outputs;
9. removes only replaced source boundary drivers;
10. validates no dangling fanins, no multiple drivers, no cycles, preserved
    primary I/O, graph activity, and non-vacuous output dependence.

A disconnected wire is never counted as a boundary.  A whole-design transplant
is diagnostic and rejected.

## Formal Proof Stack

Accepted globally valid transplants require:

- input adapter existence proof;
- output adapter existence proof;
- graph rewrite validation;
- local exhaustive primary-output equivalence between `S` and `S'`;
- ABC CEC for `S` versus `S'`;
- ABC CEC for `S'` versus the optimized implementation `I`;
- cross-node proof that cloned `xri_t` is equivalent to optimized `t`;
- graph-active target influence;
- output adapter dependence on the cloned region output;
- boundary restoration row marked selected and usable.

No timeout, unsupported result, failed graph validation, or contextual-only
diagnostic is promoted to a formal global replacement.

## GF(2) Baseline

The Gaussian-elimination baseline is explicitly limited to affine Boolean
adapters over GF(2).  It first proves the adapter truth table is affine, records
rank and coefficients, and rejects nonlinear adapters.  It is not used as a
general nonlinear or arithmetic transplantation method.

Committed result:

- GF(2)-affine adapter rows: 31;
- nonlinear rejected rows: 1;
- unavailable adapter rows: 2.

## Experiments

Run:

```bash
make cross-netlist-transplant-all
make check-cross-netlist-transplant-results
.venv-z3/bin/python -m pytest -q tests/test_cross_netlist_cut_transplantation.py
```

Artifacts are written under:

- `benchmarks/cross_netlist_cut_transplantation/`;
- `results/cross_netlist_cut_transplantation/`;
- `results/plots/cross_netlist_transplant_*.png`;
- `docs/presentation/assets/plots/cross_netlist_transplant_*.png`.

The checker enforces schema presence, blind-result separation from oracle
diagnostics, counterexample reproduction, no timeout-as-proof, graph activity
for every counted boundary, both ABC CEC scopes for accepted rows, negative
control rejection, and the exact 36/20 real-failure revisit counts.

## Controlled Results

Current committed controlled results:

- controlled cases: 17;
- positive controlled cases: 12;
- accepted graph-active controlled transplants: 12;
- negative controls rejected: 5;
- local equivalence proofs for accepted rows: 12;
- `S` versus `S'` ABC CEC passes for accepted rows: 12;
- `S'` versus `I` ABC CEC passes for accepted rows: 12;
- target equivalence proofs for accepted rows: 12;
- controlled recovered boundaries: 12.

Accepted families include permutation/inversion, XOR-basis relational input,
nonlinear Boolean relational input, multi-output region, residual output
adapter, forward-grown region, affine, add-add, bilinear, MAC, mux, and masked
constant-multiply cases.

Negative controls cover no exact input adapter, no exact output adapter, target
not influential, whole-design transplant, and global CEC failure.

## Real-Case Revisit

The real benchmark result remains null.  The phase revisits all active-source
failures:

- 36 rows from `no_globally_anchored_cut`;
- 20 rows from `no_relevant_source_consumer_window_under_bounds`;
- 56 real failures revisited total;
- 0 real graph-active transplants;
- 0 real newly recovered boundaries;
- 0 real critical-path targets resolved.

Failure localization:

- `input_interface_sufficiency`: 36;
- `output_interface_sufficiency`: 20.

This is not an impossibility claim.  It says the evaluated bounded search did
not find a source-blind interface sufficient to connect the real targets.
Oracle-ladder diagnostics are recorded separately in
`oracle_diagnostics.csv` and are not merged into blind headline counts.

## Durability

Durability is measured only for accepted controlled transplants:

- unprotected suffix optimization: 0/12 boundaries remain usable;
- repair-after-pass: 12/12 usable checkpoints;
- bounded pass choice: 12/12 usable checkpoints;
- retransplant-after-pass: 12/12 usable checkpoints.

Repair and pass-choice rows are preservation strategies, not evidence that the
unprotected optimized graph naturally preserves the constructed boundary.

## Evidence Terminology

- `adapter_exists`: exact adapter function exists for the declared interface.
- `relational_mode=true`: the interface is not a strict leaf-wise identity.
- `graph_active=true`: the cloned optimized region drives real source fanout or
  primary-output logic.
- `formal_transplant_and_global_cec`: local proof plus both ABC CEC scopes.
- `controlled_cross_netlist_transplant`: a controlled proof-stack validation
  boundary, not a real held-out restoration.
- `real bounded null`: every real row was attempted under the committed bounds
  and rejected before a legal graph-active transplant.

## Related Work Positioning

This phase combines ideas from PICEC/template-based circuit understanding,
structural and functional netlist reverse engineering, arithmetic recovery,
SyGuS-style bit-vector synthesis, SAT sweeping, logic grafting, and ECO flows.
The specific contribution is a source-blind, proof-carrying cross-netlist
interface and graph-rewrite stack for testing whether optimized regions can be
transplanted back into source-side hierarchy.

## Limitations and Next Step

The controlled positives are exact and proof-carrying, but small.  The real
result is still negative.  The next assumption to test is richer interface
discovery over real source/implementation cuts: multi-output residual search,
bounded window growth around source consumers, and stronger region-pair
proposal operators that can form a sufficient `AS,Zin -> AI` or `BI,Zout -> BS`
adapter without using ground-truth hierarchy.
