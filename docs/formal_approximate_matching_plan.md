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
