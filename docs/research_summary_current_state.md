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

The newest contextual error-metric prototype builds experimental substituted
circuits and compares global internal-node distance with output-observable
error. The committed lightweight run analyzes 40 selected ISCAS candidates with
sampled contextual patterns: 35 fall below the default contextual error
threshold and 5 are unsafe. No ODC-valid CEC-equivalent correspondence was found
in this lightweight run, and no critical-path nodes were newly recovered. The
result is still valuable because it formalizes the next question: which
globally rejected internal correspondences are harmless or low-error in their
circuit context?
