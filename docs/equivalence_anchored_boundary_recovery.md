# Equivalence-Anchored Boundary Recovery

This milestone moves from independent node correspondence toward coherent
region recovery.

```text
node correspondence:
one optimized node <-> one original node

boundary recovery:
a region is enclosed by formally equivalent input/output cuts
```

The first implementation is intentionally combinational and BLIF-level. It does
not attempt RTL decompilation, arithmetic operator extraction, ECO patching, or
automatic register insertion.

## Graph Model

For each parsed BLIF circuit, the prototype builds:

```text
Nodes(G)  = primary inputs, .names outputs, and primary-output names
FI(n)     = direct fanins from the .names statement
FO(n)     = direct fanouts induced by FI
TFI(n)    = transitive fanin cone including n
TFO(n)    = transitive fanout cone including n
```

Boundary convention:

- Extended boundary inputs are cut nodes outside the recovered region.
- Extended boundary outputs are included as region sink nodes.
- Primary inputs may be formal interface anchors when names align.
- Primary outputs may be formal interface anchors when names align.
- BLIF cover polarity is not represented on graph edges.
- Complemented-equivalence anchors carry explicit `polarity = inverted`.
- Multiple anchors are preserved; deterministic selection is recorded.

## COI Format

COIs are JSON rows under `benchmarks/coi_specs/`.

```json
{
  "benchmark": "generated_mux_tree_4",
  "optimization": "*",
  "coi_name": "mux_tree_root",
  "coi_internal_nodes": ["new_n14", "new_n15", "out"],
  "boundary_inputs": ["s0", "new_n10", "new_n13"],
  "boundary_outputs": ["out"],
  "source": "generated_ground_truth"
}
```

Malformed COIs are rejected with explicit reasons such as `missing_node`,
`invalid_boundary_input`, `invalid_boundary_output`, or `invalid_coi`.

## Algorithm

```text
anchor discovery
-> backward EBI cut search
-> forward EBO cut search
-> input-cut completion
-> cycle validation
-> region extraction
```

Anchor modes:

- `exact_only`: formal exact-signature/interface anchors only.
- `exact_plus_complemented`: exact plus complemented-equivalence anchors.
- `formal_all`: exact, complemented, and SAT/CEC-proven anchors.

Sampled or approximate anchors are not used for formal recovery.

## Interpretation

A successful recovered boundary means the COI is enclosed by formally anchored
cuts. It does **not** mean every internal node in the region has a direct
node-level correspondence.

If a previously unresolved critical-path node is inside a recovered region, the
correct wording is:

```text
enclosed by a formally anchored recovered region
```

not:

```text
formally matched node
```

## Current Results

The committed lightweight suite contains 48 case/mode rows from generated COIs
and ISCAS manual placeholders. It recovers 8 formally anchored boundaries
(16.7%). `exact_only` and `formal_all` tie on this suite: each recovers 4 of 24
rows with mean boundary-extension ratio 0.1123.

No mapped-boundary cycle conflicts were observed. The critical-path enclosure
probe found 0 previously unresolved critical-path nodes inside recovered
regions.

The failures are useful: missing ISCAS variants are recorded explicitly, and
several generated arithmetic COIs expose incomplete output cuts or whole-design
expansion. This is expected for a first conservative prototype.

## Failure Diagnosis Milestone

The follow-up diagnosis asks why 40 of 48 seed rows fail before implementing
logic grafting. The new outputs live under
`results/boundary_recovery_diagnosis/` and add:

- stage-by-stage failure taxonomy;
- identity S-versus-S baseline;
- progressive optimization-flow summary;
- global versus relevant-cone anchor coverage;
- exact-only versus formal-all differential analysis;
- deterministic anchor-selection audit;
- COI quality audit;
- benchmark/variant alignment checks;
- input-cut completion diagnosis;
- critical-path seed overlap and bounded generated path COIs.

The stage taxonomy uses stable stages:

```text
load_inputs
validate_coi
load_anchors
align_variants
analyze_relevant_cones
recover_ebi
recover_ebo
complete_input_cut
validate_cuts
detect_cycles
extract_region
compute_metrics
success
```

Current measured diagnosis:

```text
identity successes:                   1 / 6
zero-extension identity cases:        1
seed-suite successes:                 8 / 48
failure stages:                       load_inputs 16, extract_region 14, validate_cuts 10
failure reasons:                      missing_spec_circuit 16,
                                      region_not_enclosed 10,
                                      incomplete_ebo_cut 10,
                                      whole_design_expansion 4
formal_all usable frontier additions: 0
SAT/CEC anchors selected:             0
```

The anchor-coverage diagnosis separates:

- **global anchor density**: formally anchored nodes anywhere in the circuit;
- **relevant-cone anchor density**: formally anchored nodes inside the COI's
  TFI/TFO-related cones;
- **usable frontier anchors**: anchors positioned where EBI/EBO cut search can
  actually select them.

This matters because `formal_all` can add proven correspondences somewhere in a
network without helping a particular COI boundary. In the current seed suite,
`formal_all` adds no usable frontier anchors and selects no SAT/CEC-proven
anchors, so its tie with `exact_only` is expected.

The identity baseline is the primary decision gate. Since identity recovery is
not effectively perfect, the next implementation step should fix COI definitions
or recovery semantics before interpreting optimized-flow failures as evidence
that formal anchors are insufficient.
