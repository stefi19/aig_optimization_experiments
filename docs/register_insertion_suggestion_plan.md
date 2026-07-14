# Register Insertion Suggestion Prototype Plan

The final engineering direction of this project is not only to explain where optimized
critical-path nodes came from. The practical goal is to help an engineer decide where a
pipeline register might be inserted to reduce a long delay path.

This iteration is a small research prototype. It does not rewrite RTL, insert registers, or
claim correctness. It demonstrates how the correspondence flow can produce a ranked list of
candidate original nodes for human review.

## Why Registers Break Long Paths

Digital designs run on a clock. Between two clock edges, a signal must pass through
combinational logic and settle before the next register samples it. If the logic chain is too
long, the clock has to be slower.

Engineers often add pipeline registers to split one long path into two shorter paths:

```text
before:  register -> long combinational path -> register
after:   register -> shorter logic -> new register -> shorter logic -> register
```

The best insertion point is usually near the timing middle of the path, but it also has to be
semantically valid. A register changes latency, so correctness is a design-level question.

## Why Back-Mapping Matters

The critical path found after optimization is expressed in optimized BLIF/internal nodes.
Those names are not where an engineer edits the design. The correspondence layers let the
tool translate a path node back toward the original design:

```text
optimized path node -> original BLIF node -> future RTL/source location
```

That mapping is the bridge between synthesis analysis and an actionable source-level
suggestion.

## What A Good Suggestion Should Include

A useful candidate row should report:

- candidate original node;
- optimized path node that motivated the suggestion;
- path index and path length;
- estimated before/after split balance;
- mapping category: exact signature, complemented, SAT/CEC-proven, approximate, or unresolved;
- confidence score;
- approximate distance when applicable;
- unresolved risk around the candidate;
- plain-language caveats.

The current prototype uses the existing `results/critical_path_mapping.csv` rows. It avoids
unresolved nodes, prefers higher-confidence mapping categories, and ranks mapped nodes near
the middle of each path.

## Prototype Scoring

The score is intentionally simple and inspectable:

```text
score = 0.45 * split_balance
      + 0.40 * mapping_category_confidence
      + 0.10 * existing_confidence
      + 0.05 * heuristic_support
      - distance_penalty
```

Where:

- `split_balance` is highest at the middle of the path;
- exact and complemented mappings receive the highest category confidence;
- SAT/CEC-proven equivalent mappings after structural mismatch are preferred over approximate near-matches;
- approximate matches are penalized by their distance;
- unresolved nodes are excluded.

This is a ranking heuristic, not proof that a register can be inserted there.

## Why Correctness Requires More Work

Real register insertion requires:

- preserving sequential semantics;
- updating RTL, not only BLIF;
- handling latency changes explicitly;
- verifying sequential equivalence or a latency-aware contract;
- considering control/data dependencies;
- checking reset, enable, and handshake behavior;
- rerunning timing analysis after the edit.

The prototype output should therefore be read as:

```text
candidate locations for engineer review
```

not automatic transformations.
