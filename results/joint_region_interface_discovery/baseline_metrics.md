# Joint Region/Interface Discovery Baseline

Baseline was recorded before introducing the joint discovery implementation.

- Branch: `main`
- Baseline HEAD: `84d1d788bf7413756b65cac90fe382ad6d068d23`
- Remote: `origin https://github.com/stefi19/aig_optimization_experiments.git`
- Z3 smoke: passed, Z3 `4.16.0`
- Complete pytest baseline: `713 passed, 4 skipped`
- Exhaustive/Z3 agreement: `192/192`
- Z3 counterexamples reproduced: `186/186`
- Prior Z3 CEGIS iterations: `379`
- Prior formal SMT proofs: `46`
- Prior blind unique recovery: `10/16`
- Prior oracle-bus unique recovery: `10/16`
- Prior 12-bit and 16-bit blind region-row recovery: `4/4` each
- Prior isolated semantic graft attempts: `276`
- Prior graph-active graft anchors: `0`
- Prior newly recovered boundaries: `0`

The first local `semantic-region-replacement-all` attempt after a clean checkout
failed because ABC was unavailable.  ABC was then built locally with
`make build-abc`, producing `.abc_build/abc_repo/abc`, and the previous
semantic region replacement checker passed with ABC CEC enabled.
