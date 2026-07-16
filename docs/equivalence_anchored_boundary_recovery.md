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

## Repaired Canonical COI Semantics

The semantics-repair milestone introduces schema `coi_schema_v1` and makes the
region convention explicit:

```text
R  = internal region nodes
BI = nodes outside R with at least one fanout into R
BO = nodes inside R that are primary outputs or have fanout outside R
```

Under this convention, `BI ∩ R = ∅` and `BO ⊆ R`. The reusable derivation
functions are:

```text
derive_boundary_inputs(graph, region_nodes)
derive_boundary_outputs(graph, region_nodes)
normalize_coi(graph, region_nodes)
validate_coi(graph, coi)
extract_region_from_boundaries(graph, ebi, ebo, required_nodes)
```

The fixed identity baseline uses identity anchors with `proof_mode = identity`
and still runs through anchor selection, EBI/EBO discovery, region extraction,
and exact-match validation. It does not return the original COI directly.

Current repaired results:

```text
canonical COIs:                    14
identity successes:                14 / 14
zero-extension identity cases:     14 / 14
exact EBI matches:                 14 / 14
exact EBO matches:                 14 / 14
exact region matches:              14 / 14
corrected optimized attempts:      32
corrected optimized successes:     20 / 32
exact_only:                        10 / 16
formal_all:                        10 / 16
```

The old `8 / 48` number remains useful as a diagnostic artifact, but it mixed
algorithmic attempts with invalid COIs and missing circuit infrastructure. The
corrected recovery rate is computed only over valid, executable, attempted
cases.

## Extended-Boundary Validation Under Optimization

Identity recovery keeps the strict contract:

```text
recovered EBI    = original BI
recovered EBO    = original BO
recovered region = original region
extension ratio  = 0
```

Optimized recovery uses a different validation profile. A recovered boundary may
be larger than the original COI boundary if it is a valid extended boundary:

```text
original COI region is contained in the extended region
all incoming edges into the extended region cross recovered EBI
all outgoing edges from the extended region exit through recovered EBO
all recovered boundary nodes are formally anchored
mapped implementation boundary is cycle-free
extended region is non-empty and not the whole design
```

Bypass validation is relative to the recovered extended region:

```text
incoming bypass = u -> v, u outside extended region, v inside, u not in EBI
outgoing bypass = u -> v, u inside extended region, v outside, u not in EBO
```

The cost-guided search keeps the old `first_frontier` mode as a baseline and
adds bounded candidate-frontier enumeration. Candidate cuts are ordered
lexicographically by extension node count, total boundary distance, boundary
node count, complemented-anchor count, and canonical node names.

Current measured result:

```text
first_frontier:                    20 / 32
cost_guided:                       20 / 32
exact_only:                        20 / 32
formal_all:                        20 / 32
strict-equality false negatives:    0
fixed by cost-guided search:        0
selected SAT/CEC frontier anchors:  0
```

The result does not justify logic grafting yet. The remaining failures are
better explained by missing relevant formal anchors or extension-limit/whole
design candidates than by strict-boundary equality alone.

## ODC-Aware Contextual Anchors

The `formal_plus_odc` anchor mode extends `formal_all` with proven contextual
anchors:

```text
mapping_category  = formal_odc_valid_anchor
evidence_level    = formal_contextual
equivalence_scope = contextual
```

These anchors are not global equivalences. They are valid only for the recorded
benchmark, optimization, COI, context mode, observable outputs, polarity, and
circuit fingerprints.

The primary proof mode is a replacement miter:

```text
baseline implementation
vs.
implementation with impl_node replaced by the spec_node cone
```

Both sides are restricted to either all primary outputs (`global_output_odc`) or
the fixed COI boundary outputs (`coi_output_odc`). ABC CEC must prove the two
observable-output circuits equivalent. A second complete boundary-level
contextual validation is required before any ODC-enabled recovered boundary is
counted.

Current result:

```text
formal ODC anchors proven: 10
formal_all failed-case rows: 0 / 24
formal_plus_odc rows:        6 / 24
selected ODC anchors:       16 across recovery rows
unique recovered triples:    3
```

## Materialized-Wire Anchors

The correspondence-by-construction milestone adds a global anchor category that
is neither an existing-node match nor an ODC contextual replacement:

```text
anchor_origin     = materialized_wire
mapping_category  = formal_materialized_anchor
evidence_level    = formal_exhaustive
equivalence_scope = global
```

A materialized anchor is a newly introduced redundant original-side signal
constructed from a small optimized-side cut whose leaves already have global
formal anchors. It is not claimed to have existed in the original RTL or
original BLIF.

The first additive-only run proved 20 materialized anchors from 20 exhaustive
global checks, while preserving original primary outputs. However, the
materialized wires are appended and not reconnected into the original boundary
graph. As a result, `formal_plus_materialized` selected 0 materialized anchors
in boundary recovery and recovered 0 new boundaries. This points to boundary
utility and graph integration as the next bottleneck, not proof generation.
