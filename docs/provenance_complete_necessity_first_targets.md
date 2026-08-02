# Provenance-Complete Necessity-First Target Discovery

This phase corrects the denominator used by the earlier real-target
transplantation summaries.  The previous shorthand, "56 real transplantation
attempts, 0 successes", is not a valid scientific claim: most rows never reached
the graph-rewrite stage, and some did not have enough target provenance to be
formally analysed.

## Corrected Interpretation

The committed audit in `results/provenance_eligibility_audit/` preserves every
historical row and reclassifies it by lineage and eligibility:

- 330 historical rows audited across semantic grafting, semantic functional
  refactoring, joint region/interface discovery, active source counterparts,
  cross-netlist transplantation, and formal locality barriers.
- The 56 formal-locality historical rows split into 36 provenance-incomplete
  rows and 20 provenance-complete diagnostic rows.
- The 36 `controlled_*__b0` rows reconstruct only a source BLIF name; they lack
  a committed optimized artifact, deterministic target-generation recipe, and
  target-node identity, so they are excluded from eligible denominators.
- The 20 generated-adder/mux rows resolve to aligned source/optimized BLIF
  artifacts, but formal target-utility evidence shows the selected targets are
  not necessary for the selected output interfaces.
- The corrected historical eligible graph-rewrite denominator is therefore 0.

This does not erase the old results.  It changes their evidence label from
"real transplantation attempts" to "historical diagnostic rows".

## Provenance Requirements

A target is provenance-complete only when the record contains source and
optimized artifacts, circuit hashes, target-node identity, aligned primary
inputs/outputs, source-versus-optimized CEC status, synthesis flow, tool
revision, selection method, source-blind flag, and regeneration command.

The immutable target records are emitted in
`results/necessity_first_target_discovery/target_provenance.csv`.

## Observability And Necessity

The new target filter separates:

- structural fanout to a primary output;
- reachable nonconstant target variation;
- forced-value Boolean-difference observability;
- reachable paired-input dependence at a declared frontier;
- graph-active CEC-backed utility.

Only targets that are provenance-complete, source-blind, nonconstant,
forced-observable, and reachable-necessary are allowed into the eligible target
manifest.  Structural fanout alone is never formal observability.

## Fresh Necessity-First Corpus

The current repository does not contain a pinned redistributable external RTL
corpus or a pinned Yosys flow.  Rather than inventing external results, this
phase creates a provenance-complete non-controlled evaluation corpus from the
existing generated BLIF designs:

- `generated_adder_4`, development split;
- `generated_mux_tree_4`, development split;
- `generated_mux_tree_8`, held-out split.

These are classified as `generated_research_benchmark`, not external real RTL.
The result tables keep controlled, generated, standard-netlist, and external-RTL
classes separate.

## Results

The necessity-first discovery run emits:

- 48 raw optimized internal targets;
- 48 nonconstant, forced-observable, reachable-necessary eligible targets;
- 31 compact exact input interfaces;
- 17 non-compact or unsupported compact-interface cases;
- 31 valid rewrite artifacts emitted;
- 18 graph-active CEC-backed new boundaries;
- 13 emitted artifacts are CEC-equivalent but classified as direct bypasses,
  not graph-active boundary recovery.

The rewrite result is counted in tiers. Artifact emission is not enough for
boundary recovery; a row reaches the strongest tier only when graph activity and
both global CEC scopes pass.

## Reproduction

```bash
make necessity-targets-all
make check-provenance-eligibility-results
make check-necessity-target-results
```

Portable no-ABC CI runs the same checker path in temporary output directories.
Full-formal CI additionally verifies the pinned ABC job remains green.

## Limitations

The 36 historical source-side rows remain irrecoverable until the original
optimized target artifacts or deterministic generation recipes are committed.
The generated BLIF corpus is useful for provenance-complete target discovery,
but it is not an external RTL benchmark.  A future external RTL phase must add a
redistributable source corpus and pinned RTL-to-BLIF toolchain before reporting
external-RTL denominators.
