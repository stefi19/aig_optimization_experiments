# CI and Formal Evidence Stabilization Baseline

This file records the stabilization baseline for the portability and evidence
checking phase. It does not reinterpret earlier semantic or graft evidence.

## Baseline before fixes

- Main suite reported by the prior phase: 706 passed, 5 skipped.
- Z3 version: 4.16.0.
- Exhaustive/Z3 agreement: 192/192.
- Z3 counterexamples concretely reproduced: 186/186.
- Z3 CEGIS iterations: 379.
- Counterexamples incorporated: 219.
- Formal SMT semantic proofs: 46.
- Blind unique semantic cases recovered: 10/16.
- Oracle-bus unique semantic cases recovered: 10/16.
- Semantic graft placement attempts: 276.
- Graph-active graft anchors: 0.
- Newly recovered boundaries: 0.

## Reproduced CI failures

- Active source-counterpart tests invoked `.venv-z3/bin/python` directly, which
  fails on clean CI checkouts without that local virtualenv.
- Cross-netlist transplantation tests expected accepted controlled families even
  when ABC was intentionally absent and global CEC could not run.
- Semantic recoverability frontier tests attempted to parse checkpoint BLIF files
  that were never materialized after missing ABC checkpoint generation.

## Stabilization policy

- Tests invoke `sys.executable` so the active Python selected by CI or the user
  is honored.
- `--allow-no-abc` is schema/no-global-acceptance mode only. It never allows an
  accepted rewrite, transplant, or restored boundary without recorded
  `abc_available=true` and equivalent global CEC evidence.
- Recoverability checkpoints carry explicit `artifact_status`,
  `artifact_exists`, and `parse_status`. Non-materialized or non-equivalent
  checkpoints are excluded from downstream semantic and boundary analysis.
- CI now has separate no-ABC and full-ABC jobs, uses isolated temporary output
  directories, and pins ABC to `bcfdf592289a408cd67ec19260f8a60a37b085b6`.
