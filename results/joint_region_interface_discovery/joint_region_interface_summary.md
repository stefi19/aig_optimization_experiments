# Joint Region/Interface Discovery Summary

This phase replaces isolated semantic anchors with proof-carrying closed-region replacement.
The primary implementation path is source-blind: candidate search records structural seeds, proof-guided repairs, and post-inference evaluation only.

- Controlled cases attempted: 10
- Controlled graph-active replacements accepted: 8
- Controlled boundaries restored: 8
- Prior real isolated-anchor attempts revisited: 46
- Fresh source-blind structural real seeds evaluated: 12
- Real benchmark graph-active restorations: 0
- Real failure interpretation: bounded joint search still cannot form legal closed implementation regions from the prior isolated-anchor seeds; this separates graph/interface failure from semantic expression proof.

## Evidence Rules

- `newly_recovered_boundary=true` requires `graph_active=true` and `implementation_global_cec=equivalent`.
- Contextual or unresolved rows are never promoted to global equivalence.
- Ground-truth labels are not used by the joint candidate generator.

## Failure Taxonomy

- controlled / replacement / invalid_unaccounted_external_fanout: 1
- controlled / replacement / semantic_region_not_proven: 1
- real / joint_region_interface_discovery / bounded_search_reaches_whole_design_risk: 8
- real / joint_region_interface_discovery / no_candidate_removes_bypasses_under_bounds: 7
- real / joint_region_interface_discovery / no_legal_external_fanout_mapping: 8
- real / joint_region_interface_discovery / no_source_blind_closed_input_cut: 8
- real / joint_region_interface_discovery / semantic_target_outside_closed_frontier: 15
- real_fresh_seed / semantic_module_synthesis / fresh_seed_no_verified_multi_output_semantic_module_under_bounds: 12
