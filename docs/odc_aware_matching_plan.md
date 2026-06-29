# Toward ODC-Aware Approximate Matching

## What Observability Don't-Care Means

An internal circuit node can compute a different Boolean function without that difference
being visible at the primary outputs. The input assignments where the difference cannot be
observed are called observability don't-cares, or ODCs.

In plain terms:

```text
f and g may disagree internally,
but the rest of the circuit may hide that disagreement before it reaches an output.
```

## Why Global Equivalence Can Be Too Strict

The current SAT/CEC correspondence layer asks whether two internal nodes are globally
equivalent for all primary-input assignments. That is a clean and formal test, but it can
reject a useful correspondence when the node is only observed in a restricted context.

Beginner-friendly example:

```text
f = a AND b
g = a OR b
z = 0
y = f AND z
```

Globally, `f` and `g` are different. But `y` is always zero because it is masked by `z`.
Replacing `f` with `g` in this circuit does not change the primary output `y`.

This is an ODC-style situation: the local node difference exists, but the circuit context
makes it unobservable.

## Why This Matters For Critical-Path Back-Mapping

The project wants to map optimized critical-path nodes back to meaningful nodes in the
original circuit. If an optimized node is not globally equivalent to an original node, the
current exact/SAT layer rejects it. Approximate distance can still say the node is close,
but that distance is global and context-free.

An ODC-aware layer asks a different question:

```text
If this candidate replacement is made in context, do the primary outputs change?
```

That question is closer to what matters for circuit behavior and may recover useful
correspondences that global internal-node equivalence misses.

## Connection To Approximate Matching

Approximate matching currently measures how often two internal-node functions differ over
input assignments. It is useful as a ranking signal after exact and SAT-verified recovery
fail, but it does not know whether the differences are observable.

ODC-aware approximate matching would combine both ideas:

- use approximate distance to propose close candidates,
- use a context-aware miter to test whether differences affect primary outputs,
- distinguish globally different but output-hidden candidates from truly behavior-changing
  candidates.

## Current Probe

The script `scripts/odc_aware_match_probe.py` implements only tiny controlled examples:

- `masked_and_or`: `a AND b` versus `a OR b`, hidden by a constant-zero output context,
- `visible_and_or`: the same difference observed directly at the output,
- `equivalent_commuted_and`: a sanity case where the two nodes are globally equivalent.

For each example, the script computes the exact global node distance and uses ABC `cec` on
an original/modified BLIF pair to check whether the primary outputs differ.

Outputs:

- `results/odc_probe_results.csv`
- `results/odc_probe_results.md`
- `results/plots/odc_probe_summary.png`

## Limitations And Next Steps

This is not yet a general ODC correspondence engine. The hard next step is automatic
substitution of candidate nodes inside arbitrary original/optimized networks while
preserving names and primary-output alignment. Once that exists, the project can evaluate
whether approximate near-matches that fail global SAT equivalence are still valid under
observability don't-care conditions.
