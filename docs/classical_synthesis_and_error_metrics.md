# Classical Synthesis Context and Error Metrics

This project studies internal-node correspondence after logic synthesis. The current ABC
flows are built from classical synthesis ideas rather than arbitrary graph mutations.

This note gives context without inventing citations. Exact bibliographic details should be
filled in later from locally verified sources. TODO citations: De Micheli, Brayton/ABC
documentation, Espresso/don't-care optimization literature, and approximate-computing error
metric surveys.

## Classical Transformations

Boolean minimization reduces a Boolean expression while preserving its input/output
function. A minimized expression may remove intermediate terms that used to exist as named
signals.

Decomposition breaks a large function into smaller subfunctions. This can introduce new
shared internal nodes that had no one-to-one counterpart in the original circuit.

Factoring rewrites expressions to expose common structure. For example, `ab + ac` may become
`a(b + c)`. Output behavior is preserved, but internal functions change.

Resubstitution expresses one node using other existing nodes. A node may disappear because
its logic is now represented through a different shared subfunction.

Redundancy removal eliminates logic that is not needed to preserve primary-output behavior.
This can destroy a local internal correspondence even when the whole circuit remains
equivalent.

Multi-level restructuring applies combinations of decomposition, factoring, rewriting, and
resubstitution across several logic levels. ABC flows such as `rewrite`, `refactor`,
`resyn`, `resyn2`, `dc2`, and `compress2rs` can be interpreted through this lens.

Don't-care optimization uses input or observability conditions where a local value does not
affect the final outputs. This directly motivates contextual error metrics: globally
different internal functions can be interchangeable in a particular circuit context.

Technology-independent rewriting transforms the Boolean network before mapping to a physical
cell library. These rewrites preserve primary-output behavior but can preserve, complement,
remove, or invent internal functions.

## Effects on Internal Correspondence

A synthesis pass may:

- preserve an internal function exactly;
- preserve the complement of an internal function;
- remove an internal function entirely;
- introduce a new shared subfunction;
- duplicate a function into multiple cones;
- preserve output behavior while destroying one-to-one internal correspondence.

Traditional combinational equivalence checking focuses on primary outputs. This project asks
a different question: how much internal structure can still be related back to the original
design, and what kind of error is introduced if we use a near correspondence?

## Why Error Metrics Matter

Approximate-computing metrics provide language for non-identical functions:

- global truth-table distance measures how often two internal node functions differ;
- contextual output error measures how often a substitution changes primary outputs;
- output Hamming distance counts how many output bits change;
- absolute numeric error treats ordered output bits as a binary number.

The numerical metrics depend on the chosen output order. In this repository, the order is the
BLIF primary-output order.

The key distinction is:

```text
global internal distance asks whether f and g differ as standalone functions;
contextual output distance asks whether replacing f with g changes circuit outputs.
```

In the result files, `global_error_rate` compares the optimized target-node
function against the original candidate-node function under the same aligned
primary-input assignments. It is independent of the subsequent contextual
substitution test.

This connects classical don't-care optimization to the correspondence problem. A node pair
can fail global equivalence but still be valid under observability don't-cares, or it can be
approximately safe if the output error is small and explicitly labeled as an estimate or an
exhaustive result.

## Current Terminology

| Term | Meaning |
| --- | --- |
| Exact signature match | Same function identified directly through exhaustive or sampled signature matching, with formal status recorded separately |
| SAT/CEC-proven equivalent after structural mismatch | Not recovered by the initial matching stage, but later formally proven functionally equivalent |
| ODC-valid contextual correspondence | Globally different internal functions whose substitution preserves primary outputs |
| Exact contextual approximation | Non-equivalent substitution with exhaustively measured low output error |
| Sampled contextual approximation | Non-equivalent substitution with low observed error only on sampled patterns |
