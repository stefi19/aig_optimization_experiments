# Semantic Recoverability Frontier Baseline

Baseline commit before implementing the synthesis-trajectory recoverability
frontier phase:

```text
6e6d129f16a65ada7f0a01e57cb17abdca35d944
```

Commands run from a clean `main` worktree:

```bash
git pull --ff-only origin main
.venv-z3/bin/python -m pytest -q
make check-z3
make check-blind-semantic-results check-semantic-graft-results check-semantic-replacement-results check-joint-region-interface-results check-semantic-functional-refactoring-results
```

Observed baseline:

- full test suite: 727 passed, 4 skipped;
- Z3 smoke: passed, Z3 4.16.0;
- ABC: UC Berkeley ABC 1.01, local source revision
  `bcfdf592289a408cd67ec19260f8a60a37b085b6`;
- Yosys: unavailable in this environment;
- exhaustive/Z3 agreement preserved: 192/192;
- blind semantic recovery preserved: 10/16 unique cases;
- formal SMT semantic expression proofs preserved: 46;
- isolated semantic grafting preserved: 276 attempts, 0 accepted graph-active
  anchors;
- fixed semantic region replacement preserved: 5 controlled restored
  boundaries;
- joint region/interface discovery preserved: 8 controlled restored
  boundaries;
- functional refactoring preserved: 13 controlled experiments, 12 exact
  quotients, 11 quotient-depends-on-`M` decompositions, 10 accepted
  non-identity graph-active ABC-equivalent controlled refactorings, 10
  controlled restored boundaries, and 0/58 real restored boundaries.

This file is a baseline record only. It is not an additional recoverability
frontier result.
