# Proof-Carrying Semantic Region Replacement

## Motivation

The previous blind CEGIS phase showed that source-blind Z3-backed recovery can
prove compact expressions for optimized regions, including 12- and 16-bit
cases. It also showed that isolated anchors are the wrong graph abstraction for
hierarchy restoration: 46 proven expressions produced 276 bounded placement
attempts, but none became legal graph-active boundary anchors.

This phase changes the object being reconstructed. Instead of proving one
isolated signal and trying to place it later, it reconstructs a closed
implementation region and replaces that region with a proof-carrying semantic
module whose outputs drive the original external fanouts.

## Research Questions

1. Can source-blind CEGIS recover compact compositional word-level expressions
   for arithmetic and control regions after aggressive synthesis destroys the
   original internal structure?
2. Can a formally verified semantic module replace an optimized implementation
   region, preserve global circuit behavior, and reintroduce a graph-active
   boundary corresponding to the original specification hierarchy?
3. When semantic region replacement fails, is the failure caused by semantic
   recovery, cut discovery, interface alignment, graph closure, or global
   equivalence?

The contribution is not CEGIS, SMT, template matching, or logic grafting by
themselves. The defensible contribution is source-blind semantic
reconstruction of optimized regions followed by proof-carrying graph-level
region replacement.

## Region Model

A semantic replacement region is represented explicitly as:

- `RI`: internal implementation nodes selected for replacement;
- `CI`: implementation input cut, containing nodes outside `RI` that drive `RI`;
- `CO`: implementation output cut, containing nodes inside `RI` with fanout
  outside `RI` or primary-output status;
- `FO`: external fanout edges driven by `CO`;
- `M`: recovered semantic module implementing `CO = M(CI)`.

The implementation records deterministic region IDs, cut membership, external
fanout edges, inferred input/output buses, recovered expressions, proof scope,
graph-closure status, replacement cost, and schema version in
`results/semantic_region_replacement/region_candidates.csv` and
`region_closure_validation.csv`.

Closure checks require complete incoming cuts, complete outgoing fanout
accounting, deterministic output-cut mappings, no removed-node fanout leaks, no
replacement input depending on a removed node, no combinational cycle, preserved
primary I/O, and no silent whole-design expansion.

## Semantic Modules

`SemanticModule` supports multiple scalar outputs, output buses, one typed AST
per output, shared subexpression accounting, canonical module form, deterministic
Verilog emission, and BLIF emission. The controlled benchmark suite currently
exercises:

- two-output full adder sum/carry;
- affine arithmetic with coefficients 5 and 7;
- add-add;
- bilinear arithmetic;
- MAC arithmetic;
- negative dangling-fanin and multiple-driver guards.

The emitted BLIF is generated from the typed AST over the declared scalar
inputs. The replacement reuses output-cut names when safe so the module is
graph-active by construction.

## Formal Proof Stack

An accepted replacement must pass:

- closed-region validation;
- blind interface extraction for the region interface;
- Z3 free-cut semantic proof for every output-cut expression;
- deterministic semantic Verilog and BLIF emission;
- graph rewrite validation after serialise/reparse;
- ABC CEC between the original implementation and the rewritten implementation;
- boundary restoration validation.

The committed implementation keeps contextual evidence separate. No timeout,
unsupported result, graph-invalid rewrite, or contextual-only check is promoted
to a global-equivalence replacement.

## Reproducibility

Run:

```bash
make semantic-region-replacement-all
make check-semantic-replacement-results
.venv-z3/bin/python -m pytest -q tests/test_semantic_region_replacement.py tests/test_z3_backend.py
```

The new artifacts are written under:

- `benchmarks/semantic_region_replacement/`
- `results/semantic_region_replacement/`
- `results/plots/semantic_region_replacement_*.png`
- `results/plots/isolated_anchor_vs_region_replacement.png`

## Results

Current committed results:

- controlled replacement attempts: 7;
- free-cut SMT-verified semantic modules: 6;
- accepted graph-active controlled replacements: 5;
- ABC implementation global CEC passes: 5;
- restored controlled boundaries: 5;
- controlled affine recovery: 1/1;
- controlled add-add recovery: 1/1;
- controlled bilinear recovery: 1/1;
- controlled MAC recovery: 1/1;
- negative guard replacements rejected: 2/2;
- real isolated-anchor failures revisited: 46;
- real benchmark region-replacement restorations: 0.

The controlled positives prove the replacement abstraction works end to end:
region discovery, multi-output semantic proof, module emission, graph rewrite,
global CEC, and boundary-restoration accounting all pass on cases with known
legal replacements.

The real benchmark result remains negative. The old isolated-anchor candidates
do not define closed implementation regions under the deterministic bounds, so
they fail before module emission or global CEC. This is different from the
previous zero-graft result: the failure stage is now classified as closed-region
discovery rather than isolated fanout placement.

## Failure Taxonomy

The real-case revisit records these closed-region blockers:

- `extension_would_require_unbounded_region_or_whole_design`: 8;
- `no_candidate_removes_bypasses_under_bounds`: 7;
- `no_exact_observable_output_context_frontier`: 7;
- `no_legal_equivalent_spec_fanout_edge`: 8;
- `no_mapped_cut_leaves_for_in_place_rewrite`: 8;
- `semantic_target_outside_relevant_frontier`: 8.

Controlled negative guards add one `invalid_dangling_fanin` and one
`invalid_multiple_driver` rejection.

## Evidence Terminology

- `formal_region_free_cut`: local proof where the input-cut signals are free
  variables.
- `formal_global_context`: whole-circuit proof after graph replacement.
- `graph_active=true`: replacement outputs drive the original fanout or primary
  output interface.
- `valid_extended_boundary_restoration`: the restored boundary is valid but is
  not claimed to be the exact original hierarchy.
- `invalid_or_unresolved`: graph/proof/boundary checks did not justify a
  restored boundary.

## Limitations

The controlled positives are small deterministic BLIF cases. They validate the
proof stack and graph rewrite engine, but they do not establish a positive
real-benchmark hierarchy restoration. The current real-case search starts from
the previous isolated-anchor failures and remains bounded; broader region
enumeration, richer cut alignment, and specification-side closed-region mapping
are the next needed assumptions for a real positive restoration.

## Related Work Positioning

This phase sits between template-based circuit understanding/PICEC,
structural and functional netlist reverse engineering, structural arithmetic
recovery, SyGuS-style bit-vector synthesis, SAT-sweeping-based hierarchical
boundary recovery, and logic grafting/ECO flows. The project combines these
ideas for a specific recovery goal: source-blind, formally checked semantic
replacement of optimized graph regions to recover usable hierarchy.
