# Cross-Netlist Cut Transplantation Baseline

- Baseline commit: `a5a7b155ce33190acfe653c81ef67e5ae2f1aece`
- Python: `.venv-z3` Python `3.11.15`
- Z3: `4.16.0`
- ABC: `ABC 1.01`, compiled `Jul 18 2026 19:53:19`
- Yosys: unavailable in this environment
- Baseline tests: `.venv-z3/bin/python -m pytest -q` -> `740 passed, 4 skipped`
- Baseline checkers: `make check-z3 check-blind-semantic-results check-semantic-graft-results check-semantic-replacement-results check-joint-region-interface-results check-semantic-functional-refactoring-results check-semantic-recoverability-results check-active-source-counterpart-results` -> passed

## Preserved Active Source-Counterpart Metrics

- Optimized targets considered: 69
- Old materialized anchors revisited: 20
- Fresh utility-aware targets: 36
- Anchored cut rows: 69
- Fully formal-leaf cuts: 33
- Target functions extracted: 33/69
- Formally proved source counterparts: 10/13
- Source windows evaluated: 13
- Exact decompositions: 12
- Exact quotients synthesized and proved: 12/12
- Active controlled source rewrites: 10
- `S` versus `S'` CEC passes: 10
- `S'` versus `I` CEC passes: 10
- Usable controlled frontier anchors: 10
- Controlled recovered boundaries: 10
- Real active counterparts: 0
- Real recovered boundaries: 0

## Real Failure Groups For Revisit

- `no_globally_anchored_cut`: 36
- `no_relevant_source_consumer_window_under_bounds`: 20

The cross-netlist transplantation phase starts from this baseline and tests
whether synthesized source/optimized-region input and output adapters can move
past both old blockers without relying on individual leaf anchors or a
pre-existing source consumer factorizable through a single constructed wire.
