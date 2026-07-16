# Formally Verified Direct Semantic Template Recovery

Phase 4 adds a bounded direct-template recovery layer:

```text
validated semantic region
-> inferred buses
-> typed direct templates
-> deterministic simulation filter
-> exhaustive region equivalence
-> verified expression selection
-> Problem-A-inspired RTL cost
```

This phase does **not** implement unrestricted grammar search, coefficient
solving, Gaussian elimination, CEGIS refinement, or logic grafting. A recovered
expression is accepted only when it is formally proven against the gate-level
region. Sampled simulation is a filter, not proof.

## Typed AST

The implementation uses a typed expression AST. Every candidate records:

- operator;
- operands;
- input and output types;
- width;
- signedness;
- extension and truncation mode;
- slice range;
- constant value;
- canonical form;
- emitted RTL text;
- Problem-A-inspired RTL cost.

Signed and unsigned bit-vectors are separate candidate types. Width behavior is
explicit: arithmetic results are masked to the candidate output width, slices
record their range, and zero/sign extension is represented as an AST operator.

## Direct Grammar

The bounded grammar covers direct templates only:

- arithmetic: identity, negation, add, subtract, multiply, add-add, MAC,
  constant arithmetic, shifted arithmetic;
- Boolean: NOT, AND, OR, XOR, XNOR, reductions, parity, majority;
- control: one-bit selector mux templates;
- comparison: equality, inequality, unsigned comparisons, signed comparisons;
- bit manipulation: identity/slice, concat, shifts, masks, zero/sign extension.

The generator canonicalizes commutative operations and removes duplicate
canonical expressions. Distinct width and signedness hypotheses remain distinct.

## Simulation And Formal Proof

The primary simulation filter uses deterministic semantic patterns: zeros,
ones, walking values, boundary values, selector coverage, and deterministic
pseudo-random assignments. A candidate proceeds to formal validation only when
the sampled match rate is 1.0.

Formal validation in this phase is exhaustive region truth-table equivalence for
regions whose scalar input interface fits the configured bound. Accepted rows
are labeled:

```text
formal_status = formally_verified_region
proof_scope = region
formal_evidence_level = formal_exhaustive
```

The result is not labeled global equivalence. Timeout, unsupported support, and
tool/error states are never accepted as recovery.

## Current Results

Default generated results:

```text
eligible regions:              686
regions with direct candidates: 686
generated candidates:        22,728
canonical candidates:           618
simulation checked:          22,728
simulation survivors:         1,560
formal checks:                1,483
verified candidates:          1,483
recovered regions:              418

formal recovery rate:          0.609
exact syntactic recovery rate: 0.261
canonical syntactic rate:      0.045
equivalent-alternative rate:   0.414
```

The arithmetic family remains the main limitation for direct templates:
parameterized constants, affine forms, and wider arithmetic often require
coefficient solving or CEGIS. Comparison, Boolean, and bit-manipulation cases
recover more often under the current grammar.

## Problem-A-Inspired Cost

The cost model is a deterministic proxy, not the official contest scorer. It
counts high-level RTL operations and compares them to the gate-level region node
count:

```text
reduction_rate = (1 - candidate_rtl_cost / input_gate_count) * 100
```

Current verified candidates have mean cost `1.927`, median cost `1.000`, and
mean reduction rate `32.138%`; 460 verified candidates exceed 70% reduction.

## Outputs

Primary files are under `results/semantic_recovery/`:

- `semantic_direct_candidates.csv`
- `semantic_candidate_simulation.csv`
- `semantic_candidate_rankings.csv`
- `semantic_formal_results.csv`
- `semantic_verified_candidates.csv`
- `semantic_best_verified_expressions.csv`
- `semantic_ground_truth_recovery.csv`
- `semantic_output_cone_recovery.csv`
- `semantic_direct_recovery_by_operator.csv`
- `semantic_direct_recovery_by_optimization.csv`
- `semantic_dependency_ranking_ablation.csv`
- `semantic_simulation_filter_ablation.csv`
- `semantic_direct_failure_analysis.csv`
- `semantic_direct_recovery_summary.md`
- `verified_rtl/selected_verified_expressions.v`

Plots are generated under `results/plots/semantic_direct_*.png` and copied into
the offline presentation assets.

## Reproduce

```bash
make semantic-direct-recovery-all
```

## Next Phase

The next step should add parameter and coefficient inference for affine,
constant-multiply, shifted arithmetic, and other cases where direct templates
cannot cover the expression family. CEGIS should use the recorded counterexample
fields once a richer formal backend is added.
