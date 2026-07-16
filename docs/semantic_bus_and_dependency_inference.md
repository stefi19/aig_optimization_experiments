# Semantic Bus Inference and Dependency Geometry

This milestone adds the next substrate for verified semantic recovery:

```text
canonical scalar interface
-> inferred bus hypotheses
-> dependency matrices
-> dependency-geometry features
-> broad family ranking
```

It does **not** recover RTL expressions, arithmetic templates, coefficients, or
operators. The outputs are ranking and characterization signals for later
semantic recovery.

## Inferred Versus Ground Truth Mode

The generated benchmark suite contains ground-truth bus metadata. This phase
uses it in two separate ways:

- `ground_truth_bus_mode`: reproduce known bus declarations for checks.
- `inferred_bus_mode`: generate bus hypotheses from scalar names and structure.

The committed default results use `inferred_bus_mode`. Ground truth is not used
to generate inferred hypotheses; it is only used afterward to evaluate them.

## Bus Hypothesis Signals

Each bus hypothesis records:

- direction: input or output;
- inferred role: data operand, control, selector, output, or unknown;
- ordered scalar members;
- bit-order hypothesis;
- grouping, ordering, and role scores;
- evidence sources, such as name prefixes, index contiguity, and structural
  similarity;
- whether ground truth matched exactly, partially, or not at all.

The generated benchmark naming convention is intentionally deterministic, so
name/index grouping is strong in this phase. That is useful for validating the
interface machinery, but it should not be overread as recovery from arbitrary
flattened designs.

## Dependency Matrices

For each eligible region, the dependency layer writes:

- `D_structural`: graph reachability from scalar inputs to scalar outputs;
- `D_simulated`: sampled input-toggle sensitivity;
- `D_boolean_difference`: bounded Boolean-difference estimates or exact values
  when the support is small enough;
- `D_formal_optional`: reserved for a future formal dependency backend.

Sampled dependency values are heuristic estimates, not formal proof. Formal
equivalence or semantic correctness remains a separate SAT/CEC or CEGIS task.

## Dependency Geometry

The feature extractor summarizes each matrix with descriptive geometry:

- dependency density;
- lower/upper triangularity;
- diagonal concentration;
- bandwidth;
- carry-progression score;
- multiplier-style diagonal score;
- operand symmetry;
- locality and regularity.

These features can distinguish broad structural shapes. They do not identify a
specific expression by themselves.

## Broad Family Ranking

The family ranker uses bus and dependency features to rank broad families:

- arithmetic add/sub;
- arithmetic multiply;
- arithmetic affine/MAC;
- Boolean bitwise;
- control mux;
- comparison;
- bit manipulation;
- unknown.

This is not operator recovery. A high rank is only a research signal for the
next phase.

## Current Results

Generated default outputs:

```text
eligible region rows:              686
bus direction rows:              1,372
inferred bus hypotheses:         1,712
dependency matrices:               686
family ranking rows:             5,488

bus top-1 / top-3 / top-5:       1.000 / 1.000 / 1.000
bus membership precision/recall: 0.999 / 0.999
bit-order accuracy:              0.997
bus MRR:                         0.939

family top-1 / top-3:            0.246 / 0.571
family MRR:                      0.460
```

The bus results reflect deterministic generated names and canonical scalar
ordering. The family results are intentionally modest: dependency geometry
separates comparison and some arithmetic cases well, but broad Boolean and bit
manipulation cases remain difficult without expression-level reasoning.

## Outputs

Primary files are under `results/semantic_recovery/`:

- `semantic_bus_hypotheses.csv`
- `semantic_bus_best_hypotheses.csv`
- `semantic_bus_evaluation.csv`
- `semantic_input_roles.csv`
- `semantic_bit_order_evaluation.csv`
- `semantic_dependency_matrices.json`
- `semantic_dependency_features.csv`
- `semantic_family_rankings.csv`
- `semantic_family_evaluation.csv`
- `semantic_bus_ablation.csv`
- `semantic_family_ablation.csv`
- `semantic_bus_dependency_summary.md`

Plots are generated under `results/plots/` and copied to
`docs/presentation/assets/plots/`.

## Reproduce

```bash
make semantic-bus-dependency-all
```

The aggregate target regenerates the semantic benchmark and region prerequisites,
then runs bus inference, dependency extraction, family ranking, ablations, plots,
and schema/evidence checks.

## Next Phase

The next step should build inferred bus grouping into dependency matrices that
support expression-family-specific recovery. That phase should still keep
heuristic ranking separate from formal validation.
