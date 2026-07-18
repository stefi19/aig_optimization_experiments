# Active Source-Counterpart Baseline

- Baseline commit: `efaf4ecc919d3d49d1d9789280d197432c826fd7`
- Python: `.venv-z3` Python `3.11.15`
- Z3: `4.16.0`
- ABC: `ABC 1.01`, compiled `Jul 18 2026 19:53:19`
- Yosys: unavailable in this environment
- Baseline tests: `.venv-z3/bin/python -m pytest -q` -> `734 passed, 4 skipped`
- Baseline checkers: `make check-z3 semantic-z3-crosscheck check-blind-semantic-results check-semantic-graft-results check-semantic-replacement-results check-joint-region-interface-results check-semantic-functional-refactoring-results check-semantic-recoverability-results` -> passed

## Preserved Prior Metrics

- Additive materialization targets: 20
- Anchored cuts generated: 128
- Cut functions extracted: 128
- Materialized wire candidates: 20
- Formal materialized-anchor checks: 20
- Proven materialized anchors: 20
- Usable frontier materialized anchors: 0
- Selected materialized anchors: 0
- Newly recovered materialized boundaries: 0
- Controlled semantic functional-refactoring cases: 13
- Exact decompositions: 12
- Exact quotients synthesized: 12
- Graph-active controlled functional refactorings: 10
- Controlled semantic boundaries restored: 10
- Recoverability-frontier CEC-equivalent checkpoints: 60/60
- Failure-to-success recoverability transitions: 11
- Boundaries surviving subsequent unprotected optimization: 0/57

These are baseline measurements for the active source-side counterpart phase. They preserve the earlier conclusion that additive wires can be formally equivalent yet graph-inactive.
