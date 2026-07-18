# Proof-Carrying Active Source-Side Counterpart Construction

This phase studies the source-side dual of proof-carrying semantic functional
refactoring.  Earlier materialization proved that a new source-side wire can be
equivalent to an optimized internal target, but the wire was additive and had no
source-side consumers.  It therefore produced 20 formally proven anchors and 0
usable boundary anchors.

The new question is stricter: can an adapted source circuit `S'` expose a
constructed counterpart `w` for an optimized target `t`, make existing source
logic consume `w`, preserve the primary-output behavior of both `S` and `I`,
and improve boundary or critical-path utility?

## Terminology

Use `constructed source-side counterpart`, `active materialized counterpart`,
or `source-equivalent refactoring`.  Do not call the constructed wire a
recovered original RTL signal.  It is new logic inserted into an adapted source
graph.

The distinction is:

```text
old additive materialization:
    w = G(L_source)
    fanout(w) = empty

active source refactoring:
    w = G(L_source)
    Y_source = H(w, Z)
    fanout(w) includes preserved source-side consumers
```

## Method

For each candidate optimized target, the pipeline records an
`ActiveSourceCounterpartCandidate` containing the target, formally mapped cut
leaves, source counterpart, selected source consumer window, residual interface,
quotient, graph rewrite, CEC results, activity proof, boundary result, durability
result, and failure reason.

The accepted proof stack requires:

- formal leaf-anchor accounting;
- target/counterpart function extraction;
- `w_source = t_optimized` proof;
- exact source-window decomposability proof for `F(L,Z) = H(w,Z)`;
- exact quotient synthesis and independent quotient proof;
- proof that `H` depends on `w`;
- rejection of identity and bypassed rewrites;
- valid graph rewrite with no dangling nets, multiple drivers, or cycles;
- ABC CEC for `S = S'`;
- ABC CEC for `S' = I`;
- graph activity and functional influence;
- boundary and critical-path utility accounting.

Timeouts and unsupported solver or ABC results are unresolved, never accepted.

## Implemented Backends

The controlled construction uses semantic-expression materialization for the
counterpart, exact truth-table quotient synthesis for bounded interfaces, Z3
decomposability and quotient proofs, exhaustive internal-node miters for
counterpart equivalence, and ABC CEC for complete source and cross-design
equivalence.  The result files also record truth-table LUT, structural cone
transfer, Z3 Boolean miter, and ABC internal-node exposure as backend ablation
categories.

The GF(2) Gaussian-elimination-style baseline is labelled only as
`gf2_linear_special_case`.  It first proves affinity over GF(2), rejects
nonlinear cases, records the coefficient/rank data, and does not replace the
general functional-decomposition method.

## Results

Current checked CSVs are under
`results/active_source_counterpart_refactoring/`.

- targets considered: 69;
- previous materialized anchors revisited: 20;
- fresh utility-aware targets evaluated: 36;
- controlled cases: 13;
- controlled graph-active accepted counterparts: 10;
- counterpart equivalence proofs: 10;
- decomposable source windows: 12/13;
- exact quotients synthesized/proved: 12/12;
- graph-active rewrites: 10;
- `S` versus `S'` ABC CEC passes: 10;
- `S'` versus `I` ABC CEC passes: 10;
- controlled usable anchors/new boundaries: 10;
- real development/held-out active counterparts: 0;
- real new boundaries: 0;
- unprotected durability survival: 0;
- repair-after-pass usable controlled boundaries: 10;
- bounded pass-choice usable controlled boundaries: 10;
- GF(2)-affine accepted baseline rows: 11;
- GF(2) nonlinear rejections: 2.

The controlled positives include affine, add-add, bilinear, MAC, Boolean
nonlinear, multi-output, residual-interface, and source-window-growth style
cases inherited from the functional-refactoring benchmarks.  The negative
controls reject non-decomposable, quotient-ignores-`w`, and identity/vacuous
cases.

## Real-Case Outcome

The real result remains null under the bounded search:

- 20 old additive anchors are revisited and still fail at source-window
  discovery because no relevant source consumer window is found under bounds;
- 36 fresh utility targets fail before active construction because no complete
  globally anchored cut is available under bounds;
- no real row is counted as a usable anchor, selected anchor, recovered
  boundary, or resolved critical-path target.

This is not reported as impossible.  It is a bounded failure taxonomy:

- `no_relevant_source_consumer_window_under_bounds`: 20;
- `no_globally_anchored_cut`: 36.

## Durability

Unprotected ABC suffix optimization removes the constructed counterpart names in
the controlled cases, even while preserving primary-output equivalence.  This
matches the recoverability-frontier durability null result.  Two bounded
preservation strategies are measured separately:

- `repair_after_pass`: reconstruct the active counterpart after the destructive
  suffix;
- `bounded_pass_choice`: select an equivalent no-op/pass-choice checkpoint that
  preserves the active graph.

These are not merged into unprotected survival.

## Reproducibility

```bash
make active-source-counterparts-all
make check-active-source-counterpart-results
.venv-z3/bin/python -m pytest -q tests/test_active_source_counterpart_refactoring.py
```

The full local run uses Z3 4.16.0 and the pinned repository ABC binary at
`.abc_build/abc_repo/abc` (`make check-abc`). Tests use the active Python
interpreter rather than a hardcoded `.venv-z3` path. `--allow-no-abc` is only a
portable schema/rejection mode: no active source-side counterpart is accepted
unless both global CEC rows record `abc_available=true` and `equivalent`. Yosys
was unavailable for this run.

## Supported Claim

The phase demonstrates proof-carrying active source-side counterpart
construction on controlled nonlinear and arithmetic cases.  A constructed
source-side counterpart can be made graph-active, can feed preserved source
consumers through an exact quotient, and can pass both source and cross-design
global CEC.

The phase does not demonstrate a real held-out source-side boundary recovery.
On the current real target set, bounded search fails before legal source-side
integration: old materialized anchors lack a relevant source consumer window,
and fresh targets lack complete globally anchored cuts.

## Successor Phase: Cross-Netlist Cut Transplantation

The follow-up phase in
[`docs/proof_carrying_cross_netlist_cut_transplantation.md`](proof_carrying_cross_netlist_cut_transplantation.md)
removes two assumptions that blocked this phase: strict leaf-wise cut anchors
and pre-existing source consumer windows. It clones an optimized region into a
source copy and synthesizes exact adapters:

```text
AS,Zin -> Ein -> AI -> cloned RI -> BI,Zout -> Eout -> BS
```

The committed run accepts 12/12 positive controlled transplants with graph
activity, local proof, target proof, and both ABC CEC scopes. The same run
revisits all 56 real active-source failures and still restores 0 real
boundaries. The 36 fresh targets remain blocked by input-interface sufficiency,
and the 20 old additive anchors remain blocked by output-interface sufficiency
under the bounded adapter search.

The next locality-certificate phase in
[`docs/formal_locality_barriers.md`](formal_locality_barriers.md) refines these
bounded labels. It proves exact input minima where artifacts resolve, records
output B/Z minima and target utility, and classifies the 36 fresh rows as
`insufficient_target_provenance` rather than as a proved non-locality result.

## Related Work Positioning

The method combines ideas from template-based circuit understanding,
functional netlist reverse engineering, arithmetic recovery, functional
decomposition, SyGuS-style bit-vector synthesis, SAT sweeping, and ECO-style
logic rewriting.  The contribution is the proof-carrying source adaptation
stack and the separation between wire equivalence, graph activity, boundary
utility, and durability.
