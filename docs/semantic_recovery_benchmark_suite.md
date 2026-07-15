# Semantic Recovery Benchmark Suite

This milestone adds the first ground-truth benchmark layer for future semantic
recovery.  The goal is to move from gate-level correspondence toward verified
RTL-expression reconstruction without claiming that reconstruction is solved
yet.

## What the Suite Contains

The generator writes deterministic RTL sources under
`benchmarks/semantic_recovery/rtl/` and records each case in
`results/semantic_recovery/semantic_benchmark_manifest.csv`.

The current suite contains 258 cases across:

- arithmetic expressions such as addition, subtraction, multiplication,
  multiply-accumulate, affine forms, shifted addition, constant multiplication,
  and mixed-width addition;
- control expressions such as `mux2`, nested muxes, arithmetic selected by
  control, one-hot muxes, and priority muxes;
- Boolean expressions such as bitwise AND/OR/XOR/XNOR, parity, majority, and
  masked operations;
- comparisons such as equality, inequality, unsigned/signed less-than,
  less-or-equal, and range checks;
- bit manipulation such as concat, slice, zero/sign extension, shifts, masks,
  and rotations.

The manifest covers input widths 2, 3, 4, 6, 8, 12, and 16.  Additional 1-bit
and 7-bit entries appear as control inputs and mixed-width operands.

## Bounded BLIF and ABC Variants

For cases with at most eight flat input bits, the generator emits exact
truth-table BLIFs under `benchmarks/semantic_recovery/blif/source/`.

For ABC optimization variants, the default bound is stricter: non-identity ABC
flows are generated only for cases with at most four flat input bits.  This keeps
the benchmark suite lightweight and avoids asking ABC to optimize dense
truth-table encodings that are exact but not representative of a normal lowered
netlist.

The current run records 2,322 variant rows:

- 127 identity BLIF variants;
- 54 generated variants for each non-identity ABC flow;
- 73 exact-BLIF cases skipped per non-identity flow because they exceed the
  default variant bound;
- 131 RTL-only cases skipped per flow because exact truth-table BLIF generation
  is intentionally bounded.

The supported flow names are `identity`, `balance`, `rewrite`, `refactor`,
`resub`, `resyn`, `resyn2`, `dc2`, and `compress2rs`.  `compress2rs` is expanded
to the same explicit command sequence used elsewhere in the repository rather
than relying on an ABC alias.

## Why This Matters

The existing project can map optimized gate-level nodes back to original
gate-level nodes or regions.  The final engineering use case needs one more
semantic layer:

```text
optimized critical-path region
-> recovered original BLIF/COI region
-> verified RTL-like expression
-> engineer-reviewed rewrite or register suggestion
```

This benchmark suite provides known source expressions, bus widths, constants,
control inputs, and boundary metadata for that later recovery step.

## What It Does Not Claim

This phase does not infer RTL from gates, does not perform CEGIS, and does not
choose a minimal expression.  It only creates reproducible ground truth and
bounded synthesized variants so later phases can measure those algorithms.

