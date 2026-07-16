# Canonical Semantic Regions and Interfaces

This phase creates the substrate for later verified semantic recovery. It does
not infer high-level RTL expressions, arithmetic templates, coefficients, or
CEGIS solutions. Each row only says that a circuit variant has a canonical
semantic region, a canonical boundary, and an extracted scalar input/output
interface that can be compared with ground-truth bus metadata.

## Region Model

The implementation reuses the canonical COI convention from `coi_model.py`:

```text
R  = internal region nodes
BI = nodes outside R with fanout into R
BO = nodes inside R that are primary outputs or have fanout outside R
```

This convention keeps `BI` outside the region and `BO` inside the region. The
semantic-region schema records the region identity, benchmark metadata,
optimization flow, source and implementation fingerprints, region nodes,
boundary inputs, boundary outputs, observable outputs, ground-truth bus
metadata, status fields, and skip reasons.

Active source types in this phase:

- `ground_truth_region`: available for source identity BLIF cases where the
  generated benchmark metadata supplies known semantic output buses.
- `whole_output_cone`: a structural baseline that takes the union of the TFI
  cones for declared output bits, removes primary inputs, and derives BI/BO
  canonically.

Reserved source types for later phases are included in the schema but not
populated yet: `global_formal_recovered_region`,
`formal_odc_recovered_region`, `critical_path_region`, and
`sliding_structural_cone`.

## Eligibility

Every region row records:

- `declared`
- `circuit_available`
- `region_available`
- `structurally_valid`
- `interface_extractable`
- `eligible`
- `attempted`
- `status`
- `skip_reason`

Top-level statuses are `eligible`, `infrastructure_skip`, `invalid_region`,
`unsupported_case`, and `alignment_failure`. Skipped and invalid rows are not
included in attempted-region denominators.

## Validation

The validator checks that region nodes, BI, and BO exist; BI and BO match the
canonical graph derivation; the region is non-empty; observable outputs are
reachable; incoming and outgoing edges cross the declared boundary; circuit
metadata aligns with the expected benchmark and optimization; and whole-design
regions are explicitly marked.

Important validation fields include:

- `derived_bi`, `derived_bo`
- `missing_bi`, `extra_bi`
- `missing_bo`, `extra_bo`
- `incoming_bypass_edges`, `outgoing_bypass_edges`
- `whole_design_region`
- `region_fraction_of_design`

## Scalar Interface

For each valid region, the interface extractor writes scalar rows for boundary
inputs and boundary outputs. Ordering is deterministic:

1. ground-truth bus metadata when available;
2. explicit bit-index naming;
3. normalized declaration ordering;
4. canonical graph/node ordering as fallback.

The interface layer records raw node names, canonical node identifiers, bus
names, bit indices, roles, input/output counts through row grouping, and
ground-truth bus metadata. This is ground-truth interface extraction and
alignment, not inferred bus grouping.

## Generated Results

Current generated outputs report:

```text
declared benchmark cases:       258
available circuit variants:     559
eligible region rows:           686
valid ground-truth regions:     127
valid whole-output-cone regions:559
infrastructure skips:             0
unsupported rows:             3,958
invalid regions:                  0
```

Scalar-interface alignment:

```text
exact scalar-interface matches: 581 / 686
mean input precision:           1.000
mean input recall:              0.934
mean output precision:          1.000
mean output recall:             1.000
input order accuracy:           1.000
output order accuracy:          1.000
```

The non-exact scalar-interface rows are mainly optimized output-cone rows where
synthesis removed declared input bits that do not affect the optimized output
cone. These are reported as missing declared input bits, not as expression
recovery failures.

Region-source comparison is available for the 127 identity source cases where
both `ground_truth_region` and `whole_output_cone` exist:

```text
comparable pairs:                       127
mean comparable ground-truth size:     4.008
mean comparable output-cone size:      4.008
mean Jaccard overlap:                  1.000
mean valid output-cone size overall:   6.106
whole-design output-cone count:          559
```

The whole-output-cone baseline is allowed to equal the full combinational
design in this phase. It should not be confused with recovered hierarchy.

## How To Run

```bash
make semantic-regions
make semantic-interfaces
make semantic-region-comparison
make semantic-region-plots
make check-semantic-regions
make semantic-regions-all
```

The main generated files are under `results/semantic_recovery/`:

- `semantic_regions.csv`
- `semantic_region_validation.csv`
- `semantic_scalar_interfaces.csv`
- `semantic_bus_ground_truth.csv`
- `semantic_interface_alignment.csv`
- `semantic_region_source_comparison.csv`
- `semantic_region_by_optimization.csv`
- `semantic_region_failures.csv`
- `semantic_region_summary.md`

Plots are written to `results/plots/semantic_*.png` and copied into
`docs/presentation/assets/plots/`.

## Remaining Limitations

This phase does not recover RTL expressions. It does not infer buses for
unknown regions, solve arithmetic coefficients, perform expression-template
selection, or run CEGIS. The recommended next phase is inferred bus grouping and
dependency-matrix extraction over these canonical scalar interfaces.
