# Paper Tables

## Recoverability Frontier

| result_family                         | denominator_class                | success_count | denominator | success_rate | evidence_level                       |
| ------------------------------------- | -------------------------------- | ------------- | ----------- | ------------ | ------------------------------------ |
| controlled_active_source_counterparts | controlled_generated_blif        | 10            | 10          | 1.000000     | formal_exhaustive_plus_abc_cec       |
| controlled_cross_netlist_transplants  | controlled_generated_blif        | 12            | 12          | 1.000000     | formal_exhaustive_plus_abc_cec       |
| blind_parametric_cegis                | blind_generated_blif             | 3             | 24          | 0.125000     | formal_exhaustive                    |
| necessity_first_compact_interfaces    | generated_research_benchmark     | 31            | 48          | 0.645833     | exact_minimum_certificate            |
| necessity_first_graph_rewrites        | generated_research_benchmark     | 18            | 48          | 0.375000     | truth_table_rewrite_plus_abc_cec     |
| formal_locality_previous_failures     | historical_diagnostic            | 26            | 56          | 0.464286     | exact_minimum_certificate_diagnostic |
| historical_cross_netlist_recovery     | historical_ineligible_diagnostic | 0             | 56          | 0.000000     | corrected_denominator_audit          |

## Cross-Netlist Interface Ablation

| ablation                     | new_boundaries | attempted | relational_interfaces | graph_valid_transplants | global_cec_passes |
| ---------------------------- | -------------- | --------- | --------------------- | ----------------------- | ----------------- |
| direct_adapter_only          | 9              | 17        | 0                     | 12                      | 10                |
| relational_interface_enabled | 12             | 17        | 3                     | 15                      | 13                |

## Top Failure Classes

| failure_class                                                                                                                                                        | denominator_class                               | count | evidence_file                                                        | implication                                                                          |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------- | ----- | -------------------------------------------------------------------- | ------------------------------------------------------------------------------------ |
| missing_optimized_artifact                                                                                                                                           | historical_ineligible_diagnostic                | 36    | results/provenance_eligibility_audit/provenance_reconstruction.csv   | Historical rows cannot support transplantation or recovery claims.                   |
| active_source_counterpart::real::anchored_cut_discovery::no_globally_anchored_cut                                                                                    | real                                            | 36    | results/active_source_counterpart_refactoring/failure_taxonomy.csv   | Keep this blocker separate from accepted controlled proof claims.                    |
| cross_netlist_transplant::real::input_interface_sufficiency::no_globally_anchored_cut                                                                                | real                                            | 36    | results/cross_netlist_cut_transplantation/failure_taxonomy.csv       | Keep this blocker separate from accepted controlled proof claims.                    |
| formal_locality_barrier::no_globally_anchored_cut::insufficient_target_provenance::insufficient_target_provenance                                                    | no_globally_anchored_cut                        | 36    | results/formal_locality_barriers/failure_taxonomy.csv                | Keep this blocker separate from accepted controlled proof claims.                    |
| blind_cegis::cegis::no_candidate_satisfies_examples                                                                                                                  | blind_generated_blif                            | 21    | results/blind_semantic_cegis/failure_taxonomy.csv                    | Blind success rates must be reported separately from oracle and controlled settings. |
| historical_target_irrelevant_after_reconstruction                                                                                                                    | historical_diagnostic                           | 20    | results/provenance_eligibility_audit/provenance_reconstruction.csv   | The corrected historical eligible transplantation denominator remains zero.          |
| active_source_counterpart::real::source_window_discovery::no_relevant_source_consumer_window_under_bounds                                                            | real                                            | 20    | results/active_source_counterpart_refactoring/failure_taxonomy.csv   | Keep this blocker separate from accepted controlled proof claims.                    |
| cross_netlist_transplant::real::output_interface_sufficiency::no_relevant_source_consumer_window_under_bounds                                                        | real                                            | 20    | results/cross_netlist_cut_transplantation/failure_taxonomy.csv       | Keep this blocker separate from accepted controlled proof claims.                    |
| non_compact_exact_input_interface                                                                                                                                    | generated_research_benchmark                    | 17    | results/necessity_first_target_discovery/formal_locality_results.csv | Locality, not solver soundness, blocks many generated targets.                       |
| no_validated_graph_rewrite_artifact                                                                                                                                  | generated_research_benchmark                    | 17    | results/necessity_first_target_discovery/graph_rewrites.csv          | Non-compact interfaces still block the bounded rewrite language.                     |
| formal_locality_barrier::no_relevant_source_consumer_window_under_bounds::output_residual_minimum_above_previous_bound::output_residual_minimum_above_previous_bound | no_relevant_source_consumer_window_under_bounds | 17    | results/formal_locality_barriers/failure_taxonomy.csv                | Keep this blocker separate from accepted controlled proof claims.                    |
| rewrite_artifact_not_graph_active                                                                                                                                    | generated_research_benchmark                    | 13    | results/necessity_first_target_discovery/graph_rewrites.csv          | Artifact emission is kept separate from constructive boundary recovery.              |

## Ablations

| experiment_family         | ablation                         | success_count | denominator | success_rate | success_metric        |
| ------------------------- | -------------------------------- | ------------- | ----------- | ------------ | --------------------- |
| active_source_counterpart | old_target_selection             | 0             | 20          | 0.000000     | new boundaries        |
| active_source_counterpart | proof_easiness_ranking           | 0             | 20          | 0.000000     | new boundaries        |
| active_source_counterpart | boundary_utility_aware_ranking   | 10            | 69          | 0.144928     | new boundaries        |
| active_source_counterpart | gf2_linear_special_case          | 0             | 13          | 0.000000     | new boundaries        |
| cross_netlist_transplant  | old_target_ranking               | 0             | 20          | 0.000000     | new boundaries        |
| cross_netlist_transplant  | direct_adapter_only              | 9             | 17          | 0.529412     | new boundaries        |
| cross_netlist_transplant  | relational_interface_enabled     | 12            | 17          | 0.705882     | new boundaries        |
| cross_netlist_transplant  | gf2_linear_relational_baseline   | 0             | 34          | 0.000000     | new boundaries        |
| formal_locality_barrier   | anchored_only_U0                 | 20            | 20          | 1.000000     | exact minima          |
| formal_locality_barrier   | all_primary_inputs_U6_diagnostic | 0             | 0           | 0.000000     | exact minima          |
| formal_locality_barrier   | output_BZ_declared_universe      | 3             | 20          | 0.150000     | exact minima          |
| ranking_baseline          | baseline                         | 0.000000      | 220         | 0.000000     | mean rank-1 precision |
| ranking_baseline          | depth_only                       | 0.000000      | 220         | 0.000000     | mean rank-1 precision |
| ranking_baseline          | sim_dep                          | 0.000000      | 220         | 0.000000     | mean rank-1 precision |
| ranking_baseline          | sim_only                         | 0.000000      | 220         | 0.000000     | mean rank-1 precision |
| ranking_baseline          | sim_sup                          | 0.000000      | 220         | 0.000000     | mean rank-1 precision |
| ranking_baseline          | support_only                     | 0.000000      | 220         | 0.000000     | mean rank-1 precision |

## Baselines

| experiment_family         | baseline                                  | success_count | denominator | success_rate | success_metric |
| ------------------------- | ----------------------------------------- | ------------- | ----------- | ------------ | -------------- |
| active_source_counterpart | no_materialization                        | 0             | 20          | 0.000000     | new boundaries |
| active_source_counterpart | old_additive_materialization              | 0             | 20          | 0.000000     | new boundaries |
| active_source_counterpart | optimized_side_functional_refactoring     | 10            | 13          | 0.769231     | new boundaries |
| active_source_counterpart | active_source_counterpart_refactoring     | 10            | 13          | 0.769231     | new boundaries |
| active_source_counterpart | active_source_counterpart_refactoring     | 0             | 56          | 0.000000     | new boundaries |
| cross_netlist_transplant  | no_construction                           | 0             | 56          | 0.000000     | new boundaries |
| cross_netlist_transplant  | additive_materialization                  | 0             | 20          | 0.000000     | new boundaries |
| cross_netlist_transplant  | active_source_quotient                    | 10            | 13          | 0.769231     | new boundaries |
| cross_netlist_transplant  | cross_netlist_transplant                  | 12            | 17          | 0.705882     | new boundaries |
| cross_netlist_transplant  | cross_netlist_transplant                  | 0             | 56          | 0.000000     | new boundaries |
| formal_locality_barrier   | previous_cross_netlist_fixed_width_search | 0             | 56          | 0.000000     | successes      |
| formal_locality_barrier   | formal_locality_hitting_set_certificates  | 20            | 56          | 0.357143     | successes      |
| formal_locality_barrier   | certificate_guided_transplant_accounting  | 0             | 56          | 0.000000     | successes      |
