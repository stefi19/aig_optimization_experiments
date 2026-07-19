# Exact and Approximate Internal Correspondence Recovery After Logic Synthesis Optimization

## 1. Motivation

Logic synthesis optimization changes the internal graph of a circuit while
preserving its primary input/output behavior. This is useful for area and delay,
but it creates a practical debugging problem: the optimized netlist may contain
the critical path, while the hardware engineer understands and edits the
original RTL or unoptimized circuit.

The final use case of this project is therefore a back-mapping problem. Given an
optimized internal point, especially one on a timing-critical path, we want to
map it back to a corresponding or near-corresponding point in the original
circuit. Exact SAT sweeping is a strong starting point, but it is incomplete:
after rewriting, refactoring, resubstitution, and deeper resynthesis, many
internal points no longer match exactly.

The latest phases extend the work from node correspondence to source-blind
semantic reconstruction and proof-carrying graph transformation. The Z3-backed
CEGIS phase asks whether compact word-level expressions can be inferred and
proved from optimized regions. Region replacement and joint region/interface
discovery replace the failed isolated-anchor abstraction with graph-active
semantic modules that physically drive original fanouts. The newest functional
refactoring phase tests a different hypothesis: when no existing semantic
region can be closed, factor an optimized window into a semantic divisor
`M = G(X)` and exact quotient `Y = H(M, Z)`. The recoverability-frontier phase
then studies where these properties appear or disappear across ABC synthesis
checkpoints, with blind and oracle diagnostic rows kept separate. The newest
active source-counterpart phase applies the quotient idea on the source side:
construct a counterpart of an optimized internal target and rewrite source
consumers so the counterpart is graph-active.

## 2. Research Problem

The central research question is:

> After logic synthesis optimization, how much internal-node correspondence is
> preserved, and how can we recover useful correspondences when exact equality
> is lost?

This is different from ordinary equivalence checking. Standard equivalence
checking asks whether the whole optimized circuit has the same primary-output
behavior as the original. This project instead studies internal points: which
nodes survive, which disappear, which new nodes appear, and which optimized
nodes can still be related back to original logic.

## 3. Proposed Layered Flow

The current prototype uses a layered correspondence flow:

```text
exact signature match
-> complemented equivalence
-> SAT/CEC-proven equivalence after structural mismatch
-> ODC-valid contextual correspondence
-> exact contextual approximation
-> sampled contextual approximation
-> global approximate near-match
-> unresolved
```

The blind semantic CEGIS lane is separate:

```text
blind bus/interface hypothesis
-> parametric expression candidate
-> CEGIS counterexample refinement
-> formal region proof
-> closed replacement-region discovery
-> semantic module emission
-> graph-active region replacement
-> ABC global CEC for accepted replacements
-> functional decomposition when no closed semantic region exists
-> semantic divisor plus exact quotient refactoring
-> synthesis-trajectory recoverability frontier
-> active source-side counterpart construction
-> source rewrite plus S/S' and S'/I global CEC
-> formal locality-barrier certificates
-> certificate-guided transplant accounting
```

Ground-truth labels are joined only after prediction/proof files are written.
Sampled simulation remains labelled sampled; timeouts and unsupported proofs are
not accepted.

The scalable version now uses Z3 bit-vector miters for formal expression proof.
The encoder agrees with exhaustive verification on 192/192 supported small
candidate checks. The Z3 CEGIS run attempts 16 unique cases in both blind and
oracle-bus mode, recovers 10 unique cases in each, and formally verifies 4/4
attempted 12/16-bit wide cases in both modes.

The graph-active graft result remains negative but better explained: 46 proven
expressions generated 276 bounded placement attempts across six safe strategies,
and all were rejected before acceptance because no real frontier placement
satisfied the graph-active and proof requirements.

The proof-carrying region-replacement follow-up validates the replacement stack
on controlled cases: 7 controlled attempts produce 6 free-cut SMT-verified
semantic modules, 5 accepted graph-active replacements, 5 ABC-equivalent global
CEC passes, and 5 valid extended controlled boundary restorations. Controlled
affine, add-add, bilinear, and MAC recovery are each 1/1. The historical
benchmark revisit remains a null result: 46 old isolated-anchor diagnostic rows
still yield 0 provenance-complete real restored boundaries because no bounded
closed implementation region can be formed from those candidates.

The joint region/interface phase then allows counterexamples to repair region
and cut choices. It accepts 8 controlled graph-active replacements with ABC
global CEC and restores 8 controlled boundaries, but still restores 0
provenance-complete real boundaries across 46 previous historical
isolated-anchor diagnostic rows plus 12 fresh structural diagnostic seeds.

The newest semantic functional-refactoring phase no longer tries to find an
existing closed semantic subgraph. It proves quotient existence with a two-copy
Z3 miter, synthesizes an exact quotient, verifies `F(X, Z) = H(G(X), Z)`,
rejects identity or `H`-ignores-`M` decompositions, and rewrites the graph so
the semantic divisor is on a real fanout path. The controlled run has 13 cases,
12 decomposable candidates, 12 independently proved quotients, 11 non-vacuous
quotient-depends-on-`M` decompositions, 10 non-identity graph-active
ABC-equivalent refactorings, and 10 restored controlled boundaries. The
58 historical development/held-out diagnostic rows remain unrestored and are
not a corrected provenance-complete real graph-rewrite denominator.

The recoverability-frontier phase records semantic boundaries before synthesis,
saves checkpoints after individual ABC passes, proves checkpoint equivalence,
and compares blind versus oracle recoverability levels. The committed run has 4
designs, 5 source boundaries, 15 trajectories, 60 checkpoints, and 60/60
checkpoint CEC passes. Blind structural/functional-survival rows recover 59/300
rows, while oracle divisor/support/window diagnostics recover 81/180 rows.
Held-out blind recovery is 16 structural/functional-survival rows; held-out
oracle compact decomposition is 12 rows. No graph-active real restoration is
claimed by this phase.

The active source-counterpart phase revisits the 20 proven materialized anchors
and evaluates 36 fresh utility-aware targets. It constructs controlled
optimized targets, builds source-side counterparts, proves counterpart
equivalence, proves exact source-window decompositions, synthesizes quotients,
rewrites the source graph, and requires both `S = S'` and `S' = I` ABC CEC. The
controlled result has 13 cases, 10 graph-active counterparts, 10 source CEC
passes, 10 cross-design CEC passes, and 10 controlled boundaries/critical-path
mappings. The historical development/held-out diagnostic result remains 0
active counterparts and 0 boundaries: old additive anchors lack bounded
relevant source consumer windows, and fresh rows lack complete globally
anchored cuts under bounds.

The formal locality-barrier phase refines that null result instead of adding
another arbitrary interface heuristic. It audits all 56 historical diagnostic rows
with source-blind candidate-signal universes, two-copy sufficiency miters,
replayable distinguishability counterexamples, and minimum hitting-set
certificates. The current run resolves 20/20 old output-window rows to aligned
source/optimized BLIF artifacts and proves compact exact input interfaces for
their optimized targets. Output-window sufficiency remains the blocker: 3 have
compact exact B/Z interfaces, while 17 require residual interfaces wider than
the configured compact bound. Target-utility proofs show 0 functionally
influential target interfaces: all 20 resolved output rows are sufficient only
once residual source information is admitted, so none are counted as useful
local transplants. The 36 fresh
`no_globally_anchored_cut` rows are now classified more precisely as
`insufficient_target_provenance`: the committed rows name `controlled_*__b0`
targets without enough source/optimized target artifact information to build a
valid cross-netlist certificate. Certificate existence is kept separate from
transplantation. The follow-up provenance audit corrects the eligible
historical graph-rewrite denominator to 0 because 36 rows are
provenance-incomplete and 20 rows are target-irrelevant.

Each layer has a different role:

- **Exact signature match** identifies nodes whose signatures or formal truth tables match.
- **Complemented equivalence** checks whether a rejected same-polarity candidate is
  actually equivalent up to inversion.
- **SAT/CEC-proven equivalence after structural mismatch** means the initial
  signature/structural matching stage missed the pair, but ABC CEC/SAT later
  proved exact Boolean equivalence.
- **ODC-valid contextual correspondence** means globally different internal
  functions can be substituted without changing primary outputs.
- **Exact contextual approximation** is non-equivalent substitution with
  exhaustively measured low output error.
- **Sampled contextual approximation** is non-equivalent substitution with low
  observed output error only on sampled patterns.
- **Global approximate near-match** measures truth-table distance for non-equivalent
  candidates, so rejected candidates can still be ranked by functional closeness.
- **Unresolved** means no current layer found a reliable or near correspondence.
  This is not necessarily a failure; it can indicate that context, don't-cares,
  or richer mapping information is needed.

## 4. Experimental Setup

The project works at the BLIF/AIG level and uses ABC optimization passes such as
`balance`, `rewrite`, `refactor`, `resub`, `dc2`, `resyn2`, and `compress2rs`.
The benchmark set now includes toy/generated/custom circuits plus 11 ISCAS-85
combinational benchmarks.

For small circuits, signatures can be computed by exhaustive truth-table
enumeration. For larger circuits, random simulation patterns are used for
ranking, but those results are explicitly labeled as simulation-based rather
than formal. Formal claims come from SAT/CEC validation or exact exhaustive
distance rows.

## 5. Exact Correspondence Results

Exact anchors validate the basic SAT wrapper: known preserved correspondences
are accepted by ABC CEC/SAT. In the exact-anchor sanity check, all selected exact
anchors verified:

```text
3052 verified / 0 rejected / 0 inconclusive
```

This shows that the SAT exposure wrapper is usable for internal-node validation.
It also gives a baseline: when internal nodes truly survive optimization, exact
matching and SAT validation recover them reliably.

The important caveat is that, for large-input circuits, some exact-anchor
labels originate from simulation-pattern signatures rather than exhaustive truth
tables. The result files keep `simulation_mode`, `pattern_count`, and formal-mode
metadata so these cases are not confused with formal truth-table equality.

## 6. ISCAS-85 Non-Exact Recovery Results

Adding ISCAS-85 changed the research story. The original small benchmark set had
no SAT/CEC-proven rank-1 structural-mismatch recoveries, but larger ISCAS
circuits exposed real internally equivalent pairs missed by the initial matcher.

The expanded rank-1 SAT run produced:

```text
609 verified / 9030 rejected / 0 inconclusive
```

For ISCAS-85 only:

```text
609 verified / 8605 rejected / 0 inconclusive
```

The 609 verified recoveries are not spread uniformly. They are concentrated
mainly in:

- `c2670`
- `c6288`
- `c5315`
- `c432`

This means heuristic ranking can recover real SAT/CEC-proven structural-mismatch correspondences on
larger benchmarks, but it is noisy. Many high-score candidates still fail formal
SAT validation, so the heuristic must be treated as a ranking signal rather than
proof.

## 7. Approximate Correspondence Results

Approximate node distance was added to study SAT-rejected high-score candidates.
For two node functions `f` and `g`, the prototype measures:

```text
distance(f, g) = count_x[f(x) != g(x)] / 2^n
similarity(f, g) = 1 - distance(f, g)
```

`global_error_rate` compares the optimized target-node function against the
original candidate-node function under aligned primary-input assignments. It is
independent of the later contextual substitution test.

The current run analyzed 2,609 ISCAS candidate pairs:

```text
545 exact formal distances
2064 sampled distances
0 skipped
```

The key finding is that many SAT-rejected high-score candidates are not random
noise. Some are functionally very close near-correspondences. For example,
rejected candidates in exact mode often have small distance, and many sampled
rejected candidates are extremely close under deterministic simulation.

This explains why the heuristic can look plausible even when SAT rejects exact
equivalence. It also motivates approximate back-mapping: a candidate may not be
equal, but it may still be the closest original explanation point for an
optimized node.

Sampled approximate distances are not formal. Only rows computed by exhaustive
enumeration over small union supports should be described as exact formal
distances.

## 8. Critical-Path Back-Mapping Prototype

The latest prototype connects the correspondence layers to the final use case.
It extracts a structural longest path from optimized BLIFs and maps each path
node back to the original circuit using this priority:

```text
  exact signature match -> complemented equivalence -> SAT/CEC-proven equivalence after structural mismatch -> global approximate near-match -> unresolved
```

This is not a real timing path yet. Structural depth is used as a proxy so the
end-to-end idea can be tested before adding timing reports or RTL source
locations.

On the ISCAS case-study circuits `c432`, `c2670`, and `c6288`, the prototype
analyzed 1,686 structural critical-path nodes:

```text
exact signature match:                      1136  (67.4%)
complemented equivalence:                      0   (0.0%)
SAT/CEC-proven equivalent after mismatch:    145   (8.6%)
global approximate near-match:                 8   (0.5%)
unresolved:                                  397  (23.5%)
```

Overall:

```text
76.5% mapped
23.5% unresolved
```

This demonstrates the first end-to-end version of the intended workflow:
identify important optimized nodes and map most of them back to original-circuit
points using a layered exact/formal/approximate strategy.

## 8.5 Cofactor- and Sensitivity-Aware Ranking

The newest correspondence-ranking milestone adds two functional feature families
without changing the formal evidence model.

Shannon cofactor features compare a candidate pair under:

```text
f_x0 = f with input x fixed to 0
f_x1 = f with input x fixed to 1
```

This can expose pairs that look globally similar but behave differently in
conditioned input regions. Boolean-difference sensitivity features use:

```text
df/dx = f_x1 XOR f_x0
```

to estimate how strongly each primary input affects each node. The feature layer
records cosine similarity, L1/L2 distance, dominant-variable agreement,
inactive-variable agreement, rank correlation, and Boolean-difference signature
similarity.

Evidence labels are explicit. Exhaustive cofactor/sensitivity rows are
`formal_exhaustive` for the evaluated support. Sampled rows are
`sampled_estimate` and are ranking heuristics only. SAT/CEC remains the
authority for exact functional equivalence.

The committed lightweight ablation uses 65 seed-target groups and 88
candidate-feature rows from `c432`, `c2670`, and `c6288` across available
`balance`, `rewrite`, `resyn2`, and `dc2` rows. It compares:

```text
baseline
cofactor_only
sensitivity_only
cofactor_plus_sensitivity
full_combined
```

On this subset, the enhanced rankers tie the baseline rather than improve it:

```text
precision@1:                 0.3385 for every mode
mean reciprocal rank:        1.00 for every mode
mean first verified rank:    1.00 for every mode
verified recoveries budget 5: 22 for every mode
```

This means the current small labeled subset is already saturated by the
baseline. The new contribution is the reusable feature/evidence layer and the
ablation harness needed to test larger or harder candidate pools without
overstating sampled estimates.

## 8.6 Equivalence-Anchored Boundary Recovery

The newest region-level milestone asks a stronger question than node
correspondence:

```text
Can a COI be enclosed by formally equivalent input and output cuts?
```

The prototype defines COIs in JSON, builds a BLIF graph, constructs formal
anchors from exact/interface matches, complemented equivalence, and
SAT/CEC-proven equivalence after structural mismatch, then performs:

```text
backward EBI cut search
forward EBO cut search
input-cut completion
mapped-boundary cycle check
region extraction
```

The key interpretation is conservative. A successful recovered region does not
prove direct equivalence for every internal node. It only means the region is
enclosed by formally anchored cuts.

Current lightweight run:

```text
case/mode rows:                         48
successful recovered boundaries:         8  (16.7%)
exact_only success:                      4 / 24
formal_all success:                      4 / 24
mean extension ratio, exact_only:        0.1123
mean extension ratio, formal_all:        0.1123
cycle conflicts:                         0
unresolved critical-path nodes enclosed: 0
```

The exact-only and formal-all ablation ties on this seed suite, so the current
successful examples are already explained by exact/interface anchors. The
failures are mostly missing ISCAS variants, incomplete output cuts for arithmetic
COIs, and whole-design expansion in conservative validation.

## 8.7 Boundary-Recovery Failure Diagnosis

The follow-up diagnosis milestone explains the 40 failed rows before moving to
logic grafting or arithmetic extraction. It preserves the same formal evidence
semantics: exact/interface anchors, complemented equivalence, and SAT/CEC-proven
equivalence after structural mismatch. Region enclosure remains region-level
evidence, not direct node equivalence.

Current diagnosis outputs under `results/boundary_recovery_diagnosis/` show:

```text
identity successes:                     1 / 6
zero-extension identity cases:          1
seed-suite successes:                   8 / 48
failure stages:                         load_inputs 16, extract_region 14, validate_cuts 10
failure reasons:                        missing_spec_circuit 16,
                                        region_not_enclosed 10,
                                        incomplete_ebo_cut 10,
                                        whole_design_expansion 4
formal_all usable frontier additions:   0
SAT/CEC anchors selected:               0
COI audit rows:                         4 valid, 20 invalid
seed COIs overlapping unresolved paths: 0
generated critical-path COI rows:       36, all skipped for missing external BLIFs
```

The measured decision gate is therefore to fix recovery semantics or COI
definitions first. The data explains why `formal_all` ties `exact_only` in this
seed suite: additional SAT/CEC-proven anchors are not present on usable
frontiers here. This does not prove that SAT/CEC anchors are generally
unhelpful.

## 8.8 Repaired COI Semantics and Identity Baseline

The semantics-repair milestone establishes one canonical COI model:

```text
R  = internal region nodes
BI = nodes outside R with at least one fanout into R
BO = nodes inside R that are primary outputs or have fanout outside R
```

Boundary inputs are outside the region; boundary outputs are region members.
All BI/BO sets are derived from graph connectivity rather than node names. The
pipeline now repairs or excludes legacy COIs, generates micro-benchmark COIs,
checks circuit availability separately, and runs an exact S-versus-S identity
gate before optimized-flow recovery.

Corrected results:

```text
canonical COIs:                         14
micro-benchmark COIs:                   10
COI audit rows:                         16
repaired legacy rows:                    3
excluded rows:                           2
identity successes:                     14 / 14
zero-extension identity cases:          14 / 14
exact EBI matches:                      14 / 14
exact EBO matches:                      14 / 14
exact region matches:                   14 / 14
corrected optimized attempts:           32
corrected optimized successes:          20  (62.5%)
exact_only optimized recovery:          10 / 16
formal_all optimized recovery:          10 / 16
valid generated critical-path COIs:      0 / 99
```

The earlier `8 / 48` result should therefore be read as a pre-repair diagnostic
result, not a clean algorithmic recovery rate. The corrected denominator
excludes invalid COIs and infrastructure skips. Since identity is now perfect on
the canonical eligible set and `formal_all` still ties `exact_only`, the next
useful research step is likely ODC-aware or speculative anchor generation unless
future cases show relevant anchors exist but cut search fails.

## 8.9 Extended-Boundary Correctness and Cost-Guided Search

The extended-boundary milestone keeps the identity gate exact, but changes the
optimized interpretation. Optimized recovery no longer fails merely because the
recovered BI, EBO, or region differs from the original COI. Instead, success
requires the recovered extended region to contain the original COI, have valid
formally anchored input and output cuts, have zero incoming/outgoing bypasses
relative to the recovered region, be cycle-free in the mapped implementation
boundary, and avoid whole-design expansion.

Measured result on the corrected executable set:

```text
strategy rows:                            64
first_frontier valid rows:                20 / 32
cost_guided valid rows:                   20 / 32
exact_only valid rows:                    20 / 32
formal_all valid rows:                    20 / 32
previous strict-equality false negatives:  0
previous failures fixed by cost-guided:    0
selected SAT/CEC frontier anchors:         0
cost-guided search states:               100 total, 17 max
remaining blocked by missing anchors:      22 rows
remaining blocked by extension limits:      2 rows
```

The 12 previous optimized failures are therefore not simply valid extended
boundaries rejected by exact-boundary comparison. Cost-guided search reduces
some incoming-bypass symptoms in the adder rows, but does not produce a valid
formal cut on this subset. The measured next step is still ODC-aware or
speculative anchor generation, not logic grafting.

## 8.10 Formal ODC-Aware Boundary Anchors

The ODC milestone adds formally proven contextual anchors. These anchors are
not global equivalences. A `formal_odc_valid_anchor` is valid only for its
recorded context mode and observable-output set.

The formal query compares the optimized implementation against a version where
one implementation node is replaced by a specification-node cone, then restricts
both circuits to the selected observable outputs and runs ABC CEC. Proven rows
use:

```text
mapping_category  = formal_odc_valid_anchor
evidence_level    = formal_contextual
equivalence_scope = contextual
```

Measured result:

```text
candidate pairs generated:       164
formal checks attempted:         164
formal ODC anchors proven:        10
candidates disproved:            118
alignment failures:               36
timeouts/tool errors:              0
formal_all failed-case rows:       0 / 24
formal_plus_odc rows:              6 / 24
global_output_odc successes:       4 rows
coi_output_odc successes:          2 rows
selected ODC anchors:             16 across recovery rows
unique recovered triples:          3 benchmark/optimization/COI triples
```

Every ODC-enabled success also passed a complete boundary-level contextual
validation under the same observation context. This is the first boundary
milestone where contextual anchors improve the recovered set. The natural next
step is logic grafting with context-appropriate formal validation on the
ODC-recovered subset, while keeping speculative reduction as a fallback for
remaining failures.

### Semantic Recovery Benchmark Suite

The newest milestone adds ground-truth inputs for the next layer of the work:
verified semantic recovery from recovered gate-level regions back toward compact
RTL-like expressions.  The generator creates 258 deterministic RTL cases across
arithmetic, control, Boolean, comparison, and bit-manipulation families.  It
covers the requested widths 2, 3, 4, 6, 8, 12, and 16, with additional 1-bit
control inputs and mixed-width operands where needed.

For bounded cases, it also emits exact source BLIFs and ABC flow variants:

```text
semantic cases:              258
exact source-BLIF cases:     127
variant rows:              2,322
non-identity generated flow variants per flow: 54
ABC variant failures:          0
```

The benchmark layer is intentionally not a semantic-recovery algorithm yet.  It
records source expressions, bus widths, constants, control inputs, and boundary
metadata so future template recovery, CEGIS validation, and cost-aware RTL
selection can be measured against known ground truth.

### Canonical Semantic Regions and Interfaces

The follow-up semantic milestone now extracts canonical semantic regions and
scalar interfaces for the generated benchmark suite.  It reuses the established
COI convention:

```text
R  = internal region nodes
BI = nodes outside R with fanout into R
BO = nodes inside R that are primary outputs or have fanout outside R
```

Two source types are active.  `ground_truth_region` is available for the 127
source identity BLIF cases, and `whole_output_cone` is a structural baseline
computed from the TFI of declared output bits across available generated
variants.  The phase writes canonical region rows, validation rows, scalar
interface rows, ground-truth bus metadata, source-comparison rows, summaries,
and plots under `results/semantic_recovery/` and `results/plots/`.

Current generated results:

```text
declared benchmark cases:          258
available circuit variants:        559
eligible region rows:              686
valid ground-truth regions:        127
valid whole-output-cone regions:   559
infrastructure skips:                0
unsupported rows:                3,958
invalid regions:                     0

exact scalar-interface matches:  581 / 686
mean input precision / recall:   1.000 / 0.934
mean output precision / recall:  1.000 / 1.000
input/output order accuracy:     1.000 / 1.000
```

For the 127 comparable identity rows, ground-truth regions and whole-output
cones are identical (`Jaccard = 1.000`).  Across all valid variants, the mean
output-cone region size is 6.106, and all 559 output-cone baselines are marked
as whole-design regions.  The non-exact scalar-interface rows mainly occur when
optimized output cones no longer depend on some declared input bits.

This is still not expression recovery.  No row claims that a high-level RTL
expression was inferred from gates; the milestone only establishes canonical
regions, boundaries, scalar interfaces, and ground-truth interface comparison
for later inferred bus grouping and dependency analysis.

### Semantic Bus Inference and Dependency Geometry

The next semantic milestone uses the Phase 2 scalar interfaces to infer bus
hypotheses and compute dependency geometry.  The default run uses
`inferred_bus_mode`: ground-truth bus metadata is not used to generate the
hypotheses, only to evaluate them after inference.

The pipeline now writes bus hypotheses, best hypotheses, bus evaluation rows,
input-role rows, bit-order evaluation rows, dependency matrices, dependency
geometry features, broad family rankings, ablation summaries, checks, and
plots under `results/semantic_recovery/` and `results/plots/`.

Current generated results:

```text
eligible region rows:              686
bus direction rows:              1,372
inferred bus hypotheses:         1,712
complete dependency matrices:      686
family ranking rows:             5,488

bus top-1 / top-3 / top-5:       1.000 / 1.000 / 1.000
bus membership precision/recall: 0.999 / 0.999
bit-order accuracy:              0.997
bus MRR:                         0.939

broad family top-1 / top-3:      0.246 / 0.571
broad family MRR:                0.460
```

Dependency matrices include structural reachability, sampled simulation
sensitivity, and bounded Boolean-difference estimates.  Sampled dependency
values are labeled as heuristic estimates and are not formal proof.  The broad
family ranker is intentionally descriptive; it does not recover operators,
templates, coefficients, or RTL expressions.  The generated naming convention
explains the strong bus-grouping result, while the family-ranking result shows
that dependency geometry alone is not enough for robust semantic recovery.

### Formally Verified Direct Semantic Template Recovery

The newest semantic milestone adds bounded direct-template expression recovery
over the inferred buses. It introduces a typed semantic AST, explicit width and
signedness hypotheses, direct grammar families, deterministic semantic-pattern
simulation, exhaustive region-equivalence checking for small interfaces, best
verified-expression selection, and a Problem-A-inspired RTL cost proxy.

The recovery pipeline is:

```text
validated semantic region
-> inferred buses
-> typed direct templates
-> deterministic simulation filter
-> exhaustive region equivalence
-> verified expression selection
```

Accepted rows must have:

```text
formal_status = formally_verified_region
proof_scope = region
formal_evidence_level = formal_exhaustive
```

Sampled simulation remains a filter and is not formal proof. Region proofs are
not labeled global equivalence. Direct recovery is limited to the bounded
grammar; coefficient solving, unrestricted grammar search, and CEGIS remain
future work.

Current generated results:

```text
eligible regions:                  686
regions with direct candidates:     686
generated candidates:            22,728
canonical candidates:               618
simulation checked:              22,728
simulation survivors:             1,560
formal checks:                    1,483
verified candidates:              1,483
recovered regions:                  418

formal recovery rate:              0.609
exact syntactic recovery rate:     0.261
canonical syntactic recovery rate: 0.045
equivalent-alternative rate:       0.414
```

Recovery is strongest for comparison, Boolean, and bit-manipulation rows.
Arithmetic direct-template recovery is lower because many generated arithmetic
cases require parameter or coefficient inference. Verified expressions have
mean Problem-A-inspired RTL cost `1.927`, median cost `1.000`, and mean
reduction rate `32.138%`; 460 verified candidates exceed 70% reduction.

## Phase 5: Correspondence by Construction

The next milestone tests whether a missing optimized-side internal-node
correspondence can be constructed instead of discovered. For selected failed
extended-boundary cases, the pipeline:

```text
unmatched optimized frontier node
-> small optimized-side anchored cut
-> exact target function over cut leaves
-> additive original-side redundant wire
-> exhaustive global proof
-> boundary recovery with materialized anchors
```

The accepted category is explicitly separate from pre-existing node matches:

```text
anchor_origin     = materialized_wire
mapping_category  = formal_materialized_anchor
evidence_level    = formal_exhaustive
equivalence_scope = global
```

Current measured result:

```text
unmatched targets attempted:       20
anchored cuts generated:          128
functions extracted:               20
materialization candidates:        20
formal checks:                     20
proven materialized anchors:       20
usable frontier anchors:            0
selected materialized anchors:      0
newly recovered boundaries:         0
```

This is a useful negative boundary-utility result. Additive materialized wires
can be formally proven equivalent to optimized internal signals on the small
generated cases, but because they are not reconnected into the original
boundary graph, the existing boundary search does not encounter or select them.
The current bottleneck is target placement and graph integration, not formal
proof generation.

## 9. Main Findings

1. Exact matching is reliable when internal nodes survive optimization.
2. ISCAS-85 shows that real SAT/CEC-proven recoveries after structural mismatch do exist.
3. Heuristic ranking is useful but noisy; SAT/CEC validation is necessary before
   claiming exact functional correspondence.
4. Approximate distance explains why some rejected candidates still look
   meaningful: they can be near-correspondences rather than random false
   positives.
5. The critical-path back-mapping prototype shows the first practical use case:
   mapping optimized path nodes back to original-circuit points.
6. The contextual error-metric prototype separates global internal distance from
   output-observable error after substitution. In the lightweight run, it
   analyzed 40 sampled contextual candidates: 35 were below the default output
   error threshold and 5 were unsafe. These are estimates, not formal distance
   proofs.
7. Aggressive optimization still leaves many unresolved nodes, which is useful
   evidence for future ODC-aware and timing-aware work.
8. Cofactor- and sensitivity-aware ranking features are now available, but the
   lightweight ablation ties the baseline on the current small labeled subset.
9. Boundary recovery can enclose some generated MUX-tree regions with formal
   anchors, but this first conservative run does not yet recover arithmetic COIs
   or critical-path unresolved nodes.
10. Boundary-recovery diagnosis showed the identity baseline was not clean; the
    repaired semantics milestone now makes identity exact on 14 / 14 canonical
    eligible COIs.
11. The semantic-recovery benchmark suite provides source-level ground truth for
    later evaluation; by itself it is only infrastructure, not a recovery claim.
12. The canonical semantic-region milestone validates 686 eligible region rows
    and extracts 581 exact scalar-interface matches, establishing the substrate
    for later bus inference and expression recovery without claiming expression
    recovery yet.
13. Anchored-cut materialization can construct formally proven redundant wires,
    but the first additive-only run produced 0 new boundary recoveries because
    the materialized wires are not on usable boundary frontiers.
14. Z3-backed blind semantic CEGIS recovers 10/16 unique cases in blind mode,
    matches oracle-bus recovery on the same 10/16 cases, proves 46 expressions,
    and recovers all attempted 12/16-bit wide cases in the committed run.
15. Isolated semantic grafting is a negative result: 276 bounded attempts over
    46 proven expressions produce 0 graph-active anchors.
16. Closed semantic region replacement works end to end on controlled positive
    cases, restoring 5 graph-active controlled boundaries with ABC global CEC,
    but the historical benchmark revisit still restores 0 provenance-complete
    real boundaries because the old isolated anchors do not define closed
    implementation regions.
17. Joint region/interface discovery removes the fixed-region assumption.  It
    produces 37 candidate states and 14 proof-guided transitions on the
    committed run, accepts 8 controlled graph-active semantic replacements with
    ABC global CEC, restores 8 controlled boundaries, and still restores 0
    provenance-complete real benchmark boundaries from 46 old historical
    isolated-anchor diagnostic seeds plus 12 fresh structural diagnostic seeds.
18. Functional semantic refactoring replaces closed-region search with exact
    decomposition `Y = H(G(X), Z)`. It proves 12/13 controlled decomposability
    candidates, validates 12 exact quotients, rejects controlled negative and
    vacuous cases at the correct stages, restores 10 controlled graph-active
    non-identity boundaries with ABC CEC, and still restores 0
    provenance-complete real boundaries across the historical 49 development
    plus 9 held-out diagnostic rows.
19. The semantic recoverability-frontier phase evaluates 60 CEC-equivalent
    checkpoints across 15 ABC trajectories. It separates blind
    structural/functional survival from oracle compact-decomposition
    diagnostics, shows a blind-oracle gap, and reports pass-level transitions
    without making unsupported causal claims.

## 10. Limitations

- The current critical path is a structural longest path, not a real timing path
  from static timing analysis.
- Approximate distance is global and context-free; it does not account for
  observability don't-cares unless the new contextual substitution prototype is
  used.
- Large-support approximate distances use sampled estimates and must not be
  called formal.
- Contextual output distances in the current lightweight run are sampled
  estimates; only exhaustive rows or ABC CEC equivalence results should be
  described as formal.
- Numerical output error depends on the BLIF primary-output ordering.
- The `exact` mapping category can include sampled-pattern anchors for large
  circuits, so the formal-mode metadata must be checked.
- There is no direct RTL source-location mapping yet.
- Register insertion suggestions are ranked review hints, not automatic RTL
  edits.
- Boundary recovery is region-level evidence, not direct node-level equivalence
  for every internal node.
- The semantic region/interface layer extracts canonical scalar interfaces; it
  does not infer high-level expressions or buses for unknown recovered regions.
- The semantic-recovery suite supplies ground truth and bounded variants; the
  later direct, Z3 CEGIS, and region-replacement phases are the layers that make
  expression-proof claims.
- Materialized-wire anchors are newly constructed redundant signals; they are
  not pre-existing original RTL/netlist nodes. The current additive
  materialization does not reconnect graph fanout, so it may prove anchors that
  are not useful to boundary recovery.
- A proven semantic expression is not enough for hierarchy restoration. The
  replacement phase only counts graph-active inserted modules that drive the
  original fanouts and pass global CEC.
- The current real semantic-region replacement result is still null. The
  controlled micro-benchmarks validate the mechanism, while the real candidates
  are blocked at closed-region discovery and interface alignment.
- The joint region/interface phase improves the controlled abstraction but does
  not yet solve the real hierarchy-restoration problem.  The real blocker is
  now localized to source-blind closed-region/interface formation under bounded
  search, not to Z3 semantic proof or ABC CEC.
- Functional decomposition/refactoring is a controlled positive and a real
  bounded null result. It proves that semantic divisors and exact quotients can
  create graph-active boundaries in distributed controlled logic, but the real
  attempts do not yet find source-blind divisor/window/residual interfaces under
  the evaluated bounds.
- The recoverability-frontier run is a compact trajectory study. Its real rows
  use repository hand-written BLIF and its pass-level results are associations,
  not broad causal claims. The measured quantity is compact local
  recoverability, not absolute preservation of semantic information.
- The active source-counterpart run proves that source-side adaptation works on
  controlled nonlinear/arithmetic cases, but it does not create a real held-out
  active counterpart. Additive, controlled-active, real-active, and durable
  counts are intentionally reported separately.
- The cross-netlist cut-transplant run proves that strict leaf-wise anchors and
  pre-existing source consumer windows can be replaced by exact input/output
  adapters around a cloned optimized region on controlled cases. It still
  restores 0 real boundaries under the bounded search, with failures localized
  to input-interface sufficiency for 36 fresh targets and output-interface
  sufficiency for 20 old additive anchors.
- The method is not exhaustive; it analyzes selected ranked candidates and
  selected case-study circuits.

## 11. Next Steps

The most important next steps are:

1. Add timing-aware path extraction from ABC timing reports or a real STA flow.
2. Deepen observability-don't-care-aware approximate matching beyond the current
   contextual substitution prototype, so context-dependent correspondences can
   be recovered more systematically.
3. Replace or complement sampled approximate distance with a more formal backend
   such as BDDs, exact model counting, or approximate model counting.
4. Connect mapped BLIF/AIG nodes back to RTL or source-level locations.
5. Build a first register-insertion or localized RTL-rewrite suggestion
   prototype using the mapped path.
6. Add EPFL benchmarks after the current ISCAS-based flow is fully documented
   and stable.
7. Broaden source-blind semantic divisor discovery beyond the current ranked
   real seeds while retaining whole-design, bypass, non-vacuity, and cycle
   guards.
8. Extend the recoverability-frontier experiment to larger RTL-derived designs
   once Yosys and source-boundary extraction are available.
9. Add scalable quotient representations beyond bounded exact truth tables,
   such as BDD/AIG quotient synthesis with independent proof.
10. Improve specification-side interface alignment so semantic replacement and
   refactoring can be attempted on real arithmetic COIs rather than only
   controlled cases.
11. Extend compositional CEGIS on the real suite for add-add, bilinear, MAC,
    mixed-width arithmetic, and control-heavy regions without using source
    labels in blind mode.
12. Improve source-side consumer-window discovery for optimized targets whose
    additive counterparts are already proved but graph-inactive.
13. Extend cross-netlist relational interface synthesis beyond exact bounded
    truth-table adapters, especially multi-output residual discovery and
    source/optimized region-pair proposal on real COIs.

## Short Supervisor Summary

This project has evolved from measuring exact internal-node preservation into a
layered correspondence-recovery flow. Exact anchors validate the SAT wrapper,
ISCAS-85 shows that real recoveries after structural mismatch exist, and approximate distance
shows that many SAT-rejected high-score candidates are still functionally close.
The main methodological point is that heuristic similarity is useful for
ranking, but formal SAT/CEC validation is still required for equivalence claims.

Recent iterations extend this toward the final engineering use case. The
critical-path back-mapping prototype uses structural longest paths as a timing
proxy and maps optimized path nodes back to original nodes using exact,
complemented, SAT/CEC-proven, and approximate layers. On `c432`, `c2670`, and
`c6288`, it maps 76.5% of 1,686 structural critical-path nodes.

The semantic layer is now formal rather than only preparatory. The Z3-backed
blind CEGIS run agrees with exhaustive proof on 192/192 small checks, reproduces
186/186 Z3 counterexamples concretely, proves 46 expressions, and recovers
10/16 unique blind cases including all attempted 12/16-bit wide cases. The
oracle-bus ablation recovers the same 10/16 unique cases in the committed run.

The newest recoverability-frontier prototype studies trajectories rather than a
single optimized endpoint. It records five source semantic boundaries, runs 15
ABC trajectories, proves 60/60 checkpoints equivalent, and compares blind
recoverability with oracle divisor/support/window diagnostics. The result is
not a new graph-active real restoration claim: blind held-out rows are
structural/functional survival, while oracle held-out rows diagnose that compact
factorisation can still exist when the true divisor is supplied. This sharpens
the next question from "does semantic information disappear?" to "when does
synthesis remove compact, local, source-blind recoverability?"

The active source-side counterpart phase answers the next controlled question:
can a constructed optimized-target counterpart be made a real source graph
dependency? Yes on controlled cases: 10 graph-active source rewrites pass both
source and cross-design CEC and restore 10 controlled boundaries. No on the
current real bounded run: all 20 prior materialized anchors and 36 fresh targets
fail before legal source-side integration, producing 0 real active counterparts
and 0 real boundaries.

The cross-netlist cut-transplant phase changes the abstraction again:
instead of requiring leaf-wise source anchors or existing source consumers, it
clones an optimized region into the source graph and synthesizes exact adapters
`Ein(AS,Zin)=AI` and `Eout(BI,Zout)=BS`. On controlled benchmarks, 12/12
positive transplants are graph-active, pass local equivalence, pass `S` versus
`S'` and `S'` versus `I` ABC CEC, and restore 12 controlled boundaries; 5/5
negative controls are rejected. The historical 56-row revisit is now treated as
diagnostic rather than as 56 eligible graph-rewrite attempts: a later
provenance audit shows 36 rows are provenance-incomplete and the 20
artifact-resolved rows are target-irrelevant for their selected interfaces.
This is a denominator correction, not an erasure of the old evidence.

The newest provenance-complete necessity-first phase audits 330 historical rows
across the 46/56/58 denominator lineages, records row-level source/optimized
artifact availability, target-node availability, PI alignment, CEC status, and
corrected eligibility, and then runs a source-blind target selector over a
provenance-complete generated BLIF corpus. It emits 48 fresh optimized internal
targets; all 48 are nonconstant, forced-observable, and reachable-necessary,
31 have compact exact input interfaces, and 0 graph rewrites are emitted. The
valid historical eligible transplantation denominator is therefore 0, while the
new generated-research target-discovery denominator is 48. No external RTL
denominator is reported because the repository has no pinned redistributable
external RTL corpus or pinned Yosys lowering flow.

The CI/formal-evidence stabilization after these research phases pins ABC to
revision `bcfdf592289a408cd67ec19260f8a60a37b085b6`, removes hardcoded
`.venv-z3/bin/python` assumptions from tests, and splits validation into a
portable no-ABC schema/rejection job plus a full pinned-ABC formal job.
`--allow-no-abc` remains deliberately weak: it can validate CSV schemas and
negative behavior, but accepted replacements, transplants, active counterparts,
and restored boundaries still require recorded `abc_available=true` and
equivalent global CEC evidence.
