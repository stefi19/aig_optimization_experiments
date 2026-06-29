# ODC-Aware Matching Probe

This controlled probe asks whether replacing an internal node candidate changes
the primary outputs. It is a small direction-setting experiment, not a general
ODC correspondence engine.

| Example | Global distance | Output observable difference | ABC result | Interpretation |
|---|---:|---:|---|---|
| `masked_and_or` | 0.5000 | false | `equivalent` | Nodes differ globally, but the replacement is not observable at primary outputs in this context. |
| `visible_and_or` | 0.5000 | true | `not_equivalent` | Nodes differ globally and the difference is observable at primary outputs. |
| `equivalent_commuted_and` | 0.0000 | false | `equivalent` | Nodes are globally equivalent; output equivalence is expected. |

Interpretation: global internal-node distance can be too strict when a
difference is hidden by circuit context. The current implementation only
builds controlled original/modified BLIF pairs; general substitution inside
arbitrary optimized networks remains future work.
