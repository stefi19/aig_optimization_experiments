# Semantic Functional Refactoring Baseline

Baseline recorded before adding proof-carrying semantic functional decomposition.

- Baseline HEAD: `1739ea690d4dc6c300e711e58497177e43495e13`
- Branch: `main`
- Remote: `origin https://github.com/stefi19/aig_optimization_experiments.git`
- Complete pytest baseline: `720 passed, 4 skipped`
- Z3 smoke: passed, Z3 `4.16.0`
- Exhaustive/Z3 cross-check: `192/192`
- Previous isolated semantic grafting: `276` attempts, `0` graph-active anchors
- Fixed semantic region replacement: `5` controlled restored boundaries
- Joint region/interface discovery: `8` controlled restored boundaries
- Joint real evaluation: `46` prior seeds plus `12` fresh structural seeds, `0` development restorations and `0` held-out restorations

Commands run before this baseline record:

```bash
git pull --ff-only origin main
.venv-z3/bin/python -m pytest -q
make check-z3 check-blind-semantic-results check-semantic-graft-results check-semantic-replacement-results check-joint-region-interface-results
make semantic-z3-crosscheck
```
