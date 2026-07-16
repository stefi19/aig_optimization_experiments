# Anchored-Cut Wire Materialization Summary

This experiment constructs redundant original-side wires from small globally anchored cuts. A materialized anchor is not a pre-existing original node.

All accepted materialized anchors require `proof_status=proven_materialized_anchor`, `mapping_category=formal_materialized_anchor`, `anchor_origin=materialized_wire`, `evidence_level=formal_exhaustive`, and `equivalence_scope=global`. No sampled result is used as proof.

## Pipeline Funnel

- Unmatched targets attempted: 20
- Anchored cuts generated: 128
- Functions extracted: 20
- Materialization candidates: 20
- Formal checks: 20
- Proven materialized anchors: 20
- Usable frontier materialized anchors: 0
- Selected materialized anchors: 0
- Newly recovered boundaries: 0

## Cost and Runtime

- Mean added gate count: 1.700000
- Mean proof runtime seconds: 0.001422

## Cut Sizes

- cut size 1: 54
- cut size 2: 52
- cut size 3: 22

## Results by Optimization

- dc2: 11 proven anchors; 0 new boundary recoveries
- resyn2: 9 proven anchors; 0 new boundary recoveries

## Boundary Utility

The current materialized wires are additive and are not reconnected into the original boundary graph. If no selected anchors are reported, this is evidence that target selection or graph integration, not proof generation, is the bottleneck.

## Failure Taxonomy

- function_extraction / hidden_support: 108
- boundary_utility / proven_anchor_not_on_usable_frontier: 20
