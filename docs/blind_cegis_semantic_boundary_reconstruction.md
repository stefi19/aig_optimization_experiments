# Blind CEGIS Semantic Boundary Reconstruction

## Motivation

Aggressive logic synthesis can remove original RTL cut-points. Node-to-node
correspondence is then insufficient: an optimized region may still compute a
compact word-level expression even when no original internal wire survives.

## Research Question

Can a source-blind, counterexample-guided synthesiser recover compact word-level
RTL expressions for optimized regions whose original cut-points were destroyed,
formally prove those expressions, and use them to construct graph-active anchors
that recover valid hierarchical boundaries?

## Threat and Leakage Model

The primary blind mode forbids inference-time access to manifest/evaluation
fields such as `family`, `operator`, `ground_truth_expression`,
`ground_truth_input_buses`, `ground_truth_output_buses`,
`ground_truth_signedness`, manifest `constants`, bus ground-truth labels, and
accuracy/correctness columns. The audit is written to
`results/blind_semantic_cegis/leakage_audit.csv`.

Existing assisted/oracle semantic recovery is retained as an ablation. It is not
the primary result.

## Blind Inference Rules

Blind bus hypotheses are generated from scalar interface order and structural
placeholders only. Ground truth is not joined until evaluation files are written
after prediction/proof files. Signal names can be deterministically anonymised;
semantic expressions are invariant except for renamed operands.

## Parametric Grammar and CEGIS

The bounded grammar records symbolic parameters, domains, width/signedness
constraints, canonical form, RTL text, cost, and evidence. The implemented
families include affine add/sub, constant multiplication, shifted arithmetic,
truncated multiplication, add-add, multiply-accumulate, masks, and shifts.

For each candidate, deterministic examples are checked against the BLIF region.
A returned counterexample is appended to the example set and the disproven
candidate is rejected before the next synthesis iteration.

## Formal Backend

The scalable proof backend is Z3 4.16.0 via `z3-solver>=4.12,<5`. The BLIF-to-Z3
encoder is cross-checked against exhaustive enumeration on supported small
cases before it is used for wider regions. Timeout, unsupported, and error
statuses are unresolved and are never accepted as equivalence.

## Semantic Grafting

A proven expression is not treated as evidence that the original RTL contained
that exact signal. It is only a reconstructed semantic anchor. A graph-active
graft must expose the expression on a valid boundary frontier, reject cycles and
bypasses, preserve primary I/O, and pass global CEC. The current committed run
finds proven expressions but no accepted graph-active grafts; this negative
result is preserved in `results/semantic_grafting/semantic_graft_funnel.csv`.

## Evidence Taxonomy

- `sampled_estimate`: simulation-only evidence.
- `formal_exhaustive`: exact enumeration over the stated region interface.
- `formal_semantic_graft_anchor`: reconstructed expression considered for grafting.
- `proven_expression_unusable_as_boundary_anchor`: expression proof succeeded,
  but no valid active boundary frontier was found.

## Results

Committed CSVs under `results/blind_semantic_cegis/` report 1,860 bounded
parametric candidates in the legacy exhaustive run, 47 legacy CEGIS iterations,
192/192 Z3-versus-exhaustive agreement rows, 379 Z3-backed CEGIS iterations,
and 46 formal SMT expression proofs.

Blind and oracle-bus Z3 modes each attempt 16 unique cases and recover 10. Both
modes attempt and recover 4/4 wide 12/16-bit unique cases.

Committed CSVs under `results/semantic_grafting/` report 276 bounded placement
attempts across six strategies, 46 proven expressions considered, and 0 accepted
graph-active semantic grafts.

The boundary result is negative: proven expressions did not become usable
hierarchical boundary anchors in this lightweight run.

## Validity Threats and Related Work

The blind bus inference is still conservative and may under-group interfaces
that require richer structural dependency evidence. The current graft search
remains a negative result: every bounded strategy is rejected before global CEC
because no legal graph-active frontier is found.

This phase does not claim CEGIS, template matching, SAT sweeping, or
syntax-guided bit-vector synthesis as novel. The defensible contribution is
source-blind, formally verified semantic reconstruction of graph-usable
hierarchical boundaries after aggressive synthesis removes original cut-points.
Relevant comparison areas include template-based circuit understanding/PICEC,
structural and functional netlist reverse engineering, arithmetic-circuit
reverse engineering, hierarchical boundary recovery through SAT sweeping and
logic grafting, and SyGuS-style bit-vector synthesis.

## Reproducibility

```bash
make blind-semantic-cegis-all
make blind-semantic-cegis-scalable-all
make semantic-grafting-all
make semantic-graft-all
make check-z3
make check-blind-semantic-results
make check-semantic-graft-results
pytest -q tests/test_blind_semantic_cegis.py tests/test_semantic_grafting_guards.py
.venv-z3/bin/python -m pytest -q tests/test_z3_backend.py
```
