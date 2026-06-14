# Formal Approximate Matching Plan

## Motivation

The long-term goal of this project is to map points in an optimized circuit back
to meaningful points in the original RTL or unoptimized circuit. This matters in
a normal hardware-debug workflow: the optimized netlist may contain the critical
path or the failing implementation detail, but the engineer understands and edits
the original RTL.

Exact correspondence is useful, but it is not enough. Classical synthesis can
rewrite, balance, resubstitute, refactor, and exploit don't-cares in ways that
preserve the primary outputs while changing many internal node functions. Exact
SAT sweeping can identify identical internal points, but it leaves many optimized
nodes unmatched.

The next research step is a formal approximate correspondence layer. Instead of
asking only whether two internal nodes are identical, we also ask how far apart
their Boolean functions are.

```text
Exact match:        f == g
Complemented match: f == NOT g
Approximate match: f and g differ on only a small fraction of input assignments
```

## Connection to Approximate Computing

This is closely related to approximate computing and to work such as "Formal
Methods for Exact Analysis of Approximate Circuits". In that setting, formal
methods are used to compute exact error metrics between an approximate circuit
and an exact specification. Here the objects are internal nodes rather than whole
circuits, but the idea is similar: a formal method can measure not only equality,
but also distance.

For correspondence recovery, this gives a more informative answer than SAT/CEC
alone:

- SAT says: these two nodes are equal or not equal.
- Approximate distance says: these two nodes differ on 0.3% of assignments, or
  48% of assignments.

That distinction is important when trying to map an optimized critical-path node
back to the original circuit. The best explanation point may not be exactly
equivalent, but it may be the closest original internal function.

## Distance Metric

For two Boolean node functions `f` and `g`, evaluated over their common input
domain, define:

```text
distance(f, g) = count_x[f(x) != g(x)] / 2^n
similarity(f, g) = 1 - distance(f, g)
```

In this prototype, `n` is the size of the union of the two nodes' support sets.
Using the union support avoids hiding differences that appear only through an
input used by one node but not the other.

If the union support is small enough, the distance can be computed exactly by
exhaustive truth-table enumeration. This is a formal distance for the two node
functions.

If the support is too large, exhaustive enumeration is not practical. In that
case the prototype may compute a sampled estimate, but it must be labeled as
sampled. A sampled distance is useful for exploration, but it is not a formal
claim.

## Prototype Scope

The first prototype focuses on existing ISCAS-85 rank-1 SAT candidates:

- SAT-verified non-exact matches, to confirm that exact-equivalent nodes have
  distance 0.
- SAT-rejected high-score candidates, to ask whether false positives are still
  approximately close.

The intended outputs are compact summaries, not another huge candidate table:

- exact-distance rows for small-support candidates,
- sampled-distance rows for large-support candidates,
- skipped rows when sampled fallback is disabled,
- summary tables and plots by SAT status, circuit, and optimization pass.

## Research Questions

1. Do SAT-rejected candidates sometimes have very low approximate distance?
2. Does approximate distance explain why high-score false positives looked
   plausible?
3. Are some circuits or optimization passes more likely to produce approximate
   near-correspondences?
4. Can approximate distance become a better ranking signal for mapping optimized
   critical-path nodes back to the original circuit?

## Limitations

The exact distance calculation is currently limited by support size. Large
support functions require either sampling, symbolic methods, or a more scalable
formal technique such as BDDs, SAT-based model counting, or approximate-counting
variants.

Also, this metric checks global Boolean distance. A node can still be useful
under observability don't-care conditions even if its global truth-table distance
is not small. A mature correspondence method should eventually combine exact
equivalence, complemented equivalence, approximate distance, and ODC-aware
validation.

## Critical-Path Back-Mapping Prototype

The final use case is not only to say whether two internal nodes are equal. The
practical goal is to help an engineer understand an optimized implementation in
terms of the original RTL or unoptimized circuit. If the optimized circuit has a
critical path, the engineer needs to know which original logic points correspond
to the nodes on that path.

Exact SAT sweeping is a strong first layer, but it is insufficient by itself.
Classical synthesis can rewrite, refactor, resubstitute, and balance logic so
that many optimized internal nodes no longer have an identical original node.
Those nodes can still be meaningful descendants of original logic, or very close
approximations of it.

The first back-mapping prototype therefore uses the correspondence layers in a
fixed priority order:

```text
1. exact match
2. complemented match
3. SAT-verified non-exact match
4. approximate-distance near-match
5. unresolved
```

For now, the "critical path" is a structural proxy: the script extracts the
deepest fanin chain in the optimized BLIF network. This is not a physical timing
path, but it is enough to test the end-to-end idea before adding libraries,
placement, routing, or STA reports.

Approximate correspondence helps because it gives a fallback for path nodes that
are not SAT-equivalent to any original node. A near-match with small truth-table
distance is not a proof of equality, but it can still be a useful explanation
point: "this optimized node behaves like original node X on about 98% of sampled
or enumerated assignments."

Future work should replace the structural proxy with real timing reports, attach
mapped nodes back to RTL source locations, and eventually use the mapping for
optimization guidance such as register insertion or localized RTL rewrites.
Another important extension is observability don't-care awareness: a node may be
a better path explanation under circuit context than its global truth-table
distance suggests.
