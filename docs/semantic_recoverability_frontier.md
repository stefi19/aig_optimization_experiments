# Semantic Recoverability Frontier

## Motivation

The previous phases showed that the full proof-carrying mechanism works when a
useful semantic divisor, quotient window, and interface are available. They also
preserved a real null result: isolated grafting, closed region replacement,
joint region/interface discovery, and functional refactoring do not yet restore
real benchmark boundaries under the bounded source-blind searches.

This phase asks a different question: when along a synthesis trajectory does a
known semantic boundary stop being compactly and locally recoverable, and does
oracle diagnostic information reveal a blind-search gap or a locality gap?

The precise object is not absolute semantic information. Combinational
equivalence preserves the full primary-input/primary-output function. The
studied quantity is compact, local, exploitable semantic recoverability inside
the optimized network.

## Research Questions

1. At which checkpoints do structural, functional, blind, and oracle recovery
   levels succeed or fail?
2. When blind recovery fails, does an oracle semantic divisor still admit a
   compact exact decomposition?
3. Does failure localize to divisor discovery, support discovery, consumer
   window discovery, residual selection, quotient proof, graph rewriting, or
   durability?
4. Which synthesis passes are associated with recoverability transitions?
5. Is recoverability monotonic, or can later passes recreate recoverable
   structure?
6. What trade-off appears between node/depth reduction and recoverability?
7. If a boundary is present at one checkpoint, does it survive later passes?

## Benchmark Manifest

The committed run uses three controlled diagnostic BLIF designs and one
repository-authored real BLIF design:

- `controlled_xor_factor`;
- `controlled_and_factor`;
- `controlled_nonmonotonic_factor`;
- `benchmarks/real/hand_written/full_adder.blif`.

The real design is repository-local hand-written BLIF. No new third-party source
is imported. Source and licence/provenance rows are in
`results/semantic_recoverability_frontier/benchmark_sources_licenses.csv`.

Ground-truth boundary records are written before optimisation to
`ground_truth_boundary_manifest.csv`. They include boundary IDs, source
locations, operator labels, support, output function, fanout properties, and
eligibility. These fields are not present in blind prediction rows.

## Blind and Oracle Separation

Blind predictions are written to `blind_candidate_predictions.csv`; those rows
contain checkpoint-local node observations and no operator label, source
support, oracle divisor, original bus mapping, or source hierarchy. The leakage
audit in `leakage_audit_results.csv` checks this mechanically.

Oracle rows are physically separate in `oracle_ladder_results.csv`. They are
diagnostic, not blind recovery. The ladder currently records:

- `oracle_divisor`;
- `oracle_divisor_support`;
- `oracle_window`.

Each oracle row uses the same two-copy decomposability obligation used by the
functional-refactoring phase.

## Synthesis Trajectories

Each benchmark is run through three deterministic ABC pass trajectories:

- `strash; balance; rewrite`;
- `strash; rewrite; balance`;
- `strash; refactor; dc2`.

The runner saves a checkpoint after every pass, records command prefixes,
hashes each BLIF, extracts structural metrics, and runs ABC CEC from each
checkpoint back to the reference. The committed run has 12 trajectories and 60
checkpoints, with 60/60 checkpoint CEC equivalence.

Yosys is unavailable in the current environment, so no RTL-to-BLIF trajectory is
claimed in this phase.

## Recoverability Levels

The result tables use the following levels:

- `R0_structural_survival`: the original semantic signal name survives.
- `R1_functional_internal_survival`: an internal checkpoint signal is
  exhaustively equivalent to the boundary function.
- `R2_blind_semantic_reconstruction`: reserved for source-blind CEGIS rows.
- `R3_blind_closed_region_replacement`: reserved for graph-active blind
  replacement rows.
- `R4_blind_functional_refactoring`: reserved for blind divisor/window/quotient
  discovery.
- `R5_oracle_divisor_compact_decomposition`: true `G` supplied, compact
  quotient exists.
- `R6_oracle_divisor_support_decomposition`: true `G` and support supplied.
- `R7_oracle_window_decomposition`: true `G` and evaluation window supplied.
- `R8_non_local_global_factorisation`: exact but too non-local to count as
  local recovery.
- `R9_unresolved`: no proof, no supported recovery, timeout, or budget failure.

Whole-design factorisation is diagnostic only and is not counted as local
semantic recovery.

## Residual and Window Analysis

`residual_selection_iterations.csv` performs cardinality-ordered residual
search on small interfaces. SAT rows are decomposition counterexamples and are
replayed concretely. UNSAT rows establish decomposability for that residual set.
`residual_bounds.csv` labels exact minima only when lower and upper bounds
match.

`window_locality_results.csv` separates immediate, bounded, and whole-design
diagnostic windows. Whole-design rows are explicitly labelled
`whole_design_diagnostic_not_local_success`.

## Results

Current committed results under `results/semantic_recoverability_frontier/`:

- designs: 4;
- ground-truth boundaries: 5;
- trajectories: 12;
- checkpoints: 60;
- checkpoint CEC equivalent: 60/60;
- blind recovered rows: 59/300;
- oracle recovered rows: 81/180;
- held-out blind recovered rows: 16;
- held-out oracle recovered rows: 12;
- real graph-active boundary restoration: not claimed in this phase.

The held-out blind recoveries are structural/functional-survival rows on the
repository hand-written full-adder boundary. They are not graph-active semantic
refactoring successes and are not merged with oracle decomposition counts.

## Failure Taxonomy

The main failure modes are:

- blind divisor not discovered;
- no exact or complemented internal survivor;
- no formally equivalent internal signal under exhaustive small check;
- exact decomposition disproved for the selected `G/Z/window`;
- only non-local decomposition established.

No row uses a generic "semantic information lost" label.

## Pass-Level Analysis

`pass_level_deltas.csv` records transitions immediately after each pass. The
language is intentionally associative: every non-unchanged row sets
`causal_claim=not_claimed_controlled_ablation_required`. `pass_ablations.csv`
contains pass-omission diagnostic rows but does not claim causal proof in this
small run.

## Durability

`boundary_durability_results.csv` tests whether an oracle-recovered semantic
boundary remains visible at the next suffix checkpoint. In this run, recovered
oracle decompositions do not survive as textually present or graph-active
semantic boundaries after subsequent optimisation. This is a durability null
result, not a CEC failure.

## Reproducibility

```bash
make semantic-recoverability-all
make check-semantic-recoverability-results
.venv-z3/bin/python -m pytest -q tests/test_semantic_recoverability_frontier.py
```

The full local run requires the repository ABC binary at
`.abc_build/abc_repo/abc`. CI may use `--allow-no-abc` for lightweight schema
checking when ABC is unavailable.

## Supported Claim

The phase establishes a reproducible, formally checked trajectory-frontier
methodology. It shows that structural/functional recoverability can disappear
after early passes while oracle compact decompositions still succeed on some
checkpoints, giving a measurable blind-oracle gap. It also records that
whole-design/non-local factorisation is distinct from local recoverability, and
that restored semantic boundaries are fragile under subsequent optimisation in
the evaluated small trajectories.

## Limitations

The dataset is intentionally compact. The "real" rows use repository
hand-written BLIF, not newly imported industrial or open-source RTL. Yosys was
unavailable, so RTL trajectory extraction is not claimed. Pass-level findings
are associations unless controlled omission/reordering establishes a causal
difference. Bounded search failures are not mathematical impossibility claims.

## Related Work Positioning

This phase connects structural and functional netlist reverse engineering,
template-based circuit understanding, arithmetic netlist recovery, functional
decomposition, SyGuS-style bit-vector synthesis, SAT sweeping, and ECO-style
logic rewriting. The contribution is the measurement framework for
source-blind versus oracle semantic recoverability across synthesis
trajectories, not ABC, CEGIS, SMT, or functional decomposition in isolation.
