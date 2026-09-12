# Script Layout

The script implementations are organized by research responsibility. Root-level `scripts/*.py` files are compatibility adapters; new automation should prefer `python -m scripts.<category>.<module>`.

This keeps old reproduction commands stable while making the maintained implementation surface easier to audit. Each category below owns one part of the research workflow, from benchmark construction to proof validation and paper-ready figures.

## `abc/`

ABC/Yosys provenance probes, native SAT sweeping comparisons, and source-map prototypes.

- `abc_native_sat_sweep_baseline.py`
- `abc_sat_sweep_validation.py`
- `build_source_map_prototype.py`
- `compare_abc_native_vs_custom.py`
- `investigate_abc_provenance.py`
- `odc_aware_match_probe.py`
- `probe_abc_sat_sweeping.py`
- `probe_abc_timing_commands.py`
- `probe_yosys_source_metadata.py`

## `analysis/`

Metric calibration, correspondence diagnostics, timing/contextual analysis, and research probes.

- `analyze_boundary_anchor_coverage.py`
- `analyze_iscas_verified_matches.py`
- `approximate_node_distance.py`
- `boundary_recovery_critical_path.py`
- `calibrate_approximate_distance_sampling.py`
- `cofactor_sensitivity_correspondence_analysis.py`
- `compare_functional_ranking_ablations.py`
- `contextual_correspondence_analysis.py`
- `critical_path_back_mapping.py`
- `enhanced_critical_path_mapping.py`
- `generate_critical_path_cois.py`
- `suggest_register_insertion_points.py`
- `timing_aware_path_probe.py`

## `benchmarks/`

Benchmark ingestion, identifier normalization, source-suite generation, and benchmark manifest checks.

- `benchmark_id.py`
- `build_benchmark_manifest.py`
- `check_semantic_recovery_benchmarks.py`
- `generate_semantic_recovery_benchmarks.py`
- `generate_synthetic_benchmarks.py`
- `import_external_benchmarks.py`
- `import_real_benchmarks.py`

## `boundary/`

Boundary recovery experiments, repaired COIs, corrected identity baselines, and extended-boundary diagnostics.

- `compare_boundary_search_strategies.py`
- `diagnose_boundary_recovery_failures.py`
- `evaluate_extended_boundary_correctness.py`
- `generate_boundary_recovery_micro_benchmarks.py`
- `recover_equivalence_anchored_boundaries.py`
- `repair_boundary_recovery_cois.py`
- `run_boundary_recovery_corrected_analysis.py`
- `run_boundary_recovery_critical_path_fixed.py`
- `run_boundary_recovery_identity_baseline.py`
- `run_boundary_recovery_identity_fixed.py`
- `run_cost_guided_boundary_search.py`
- `run_odc_boundary_recovery.py`
- `summarize_boundary_recovery_semantics.py`

## `evidence/`

High-level evidence synthesis and paper-facing evidence advancement builders.

- `build_evidence_advancement.py`
- `build_research_wow.py`

## `materialization/`

Anchor/wire materialization, ODC anchor generation, and materialized-correspondence proof scripts.

- `compare_materialization_ablations.py`
- `compare_odc_anchor_modes.py`
- `enumerate_anchored_cuts.py`
- `extract_anchored_cut_functions.py`
- `generate_odc_anchor_candidates.py`
- `materialize_original_wires.py`
- `prove_materialized_anchors.py`
- `prove_odc_anchors.py`
- `run_materialized_boundary_recovery.py`
- `select_materialization_targets.py`

## `publication/`

Artifact manifests and paper/PDF publication helpers.

- `build_artifact_manifest.py`
- `build_paper_pdf.py`

## `recoverability/`

Current production experiment drivers for recoverability, locality, transplantation, and necessity-first targets.

- `run_active_source_counterpart_refactoring.py`
- `run_cross_netlist_cut_transplantation.py`
- `run_formal_locality_barriers.py`
- `run_joint_region_interface_discovery.py`
- `run_necessity_first_targets.py`
- `run_semantic_functional_refactoring.py`
- `run_semantic_recoverability_frontier.py`

## `semantic/`

Semantic-region construction, blind CEGIS, Z3 cross-checks, semantic grafting, and direct-template pipelines.

- `build_semantic_regions.py`
- `compare_semantic_bus_ablations.py`
- `compare_semantic_direct_ablations.py`
- `compare_semantic_region_sources.py`
- `compute_semantic_dependencies.py`
- `extract_semantic_interfaces.py`
- `generate_semantic_direct_candidates.py`
- `infer_semantic_buses.py`
- `rank_semantic_families.py`
- `run_blind_semantic_cegis.py`
- `run_semantic_grafting.py`
- `run_semantic_region_replacement.py`
- `select_semantic_expressions.py`
- `semantic_z3_cegis_experiment.py`
- `semantic_z3_crosscheck.py`
- `simulate_semantic_candidates.py`
- `verify_semantic_candidates.py`

## `validation/`

Independent result checkers that reject stale, incomplete, or overclaimed artifacts.

- `check_active_source_counterpart_results.py`
- `check_artifact_claims.py`
- `check_blind_semantic_results.py`
- `check_boundary_diagnosis_results.py`
- `check_boundary_recovery_circuits.py`
- `check_boundary_recovery_results.py`
- `check_boundary_recovery_semantics.py`
- `check_cross_netlist_transplant_results.py`
- `check_evidence_advancement.py`
- `check_extended_boundary_results.py`
- `check_formal_locality_barrier_results.py`
- `check_functional_ranking_results.py`
- `check_joint_region_interface_results.py`
- `check_materialized_correspondence_results.py`
- `check_necessity_first_target_results.py`
- `check_odc_anchor_results.py`
- `check_provenance_eligibility_results.py`
- `check_research_wow.py`
- `check_results_freshness.py`
- `check_semantic_bus_dependency_results.py`
- `check_semantic_direct_results.py`
- `check_semantic_functional_refactoring_results.py`
- `check_semantic_graft_results.py`
- `check_semantic_recoverability_results.py`
- `check_semantic_regions.py`
- `check_semantic_replacement_results.py`
- `check_z3.py`

## `visualization/`

Reproducible plotting scripts for figures, presentation assets, and result dashboards.

- `active_source_counterpart_plots.py`
- `blind_semantic_plots.py`
- `boundary_diagnosis_plots.py`
- `boundary_recovery_plots.py`
- `boundary_recovery_semantics_plots.py`
- `cross_netlist_transplant_plots.py`
- `extended_boundary_plots.py`
- `formal_locality_barrier_plots.py`
- `joint_region_interface_plots.py`
- `materialized_correspondence_plots.py`
- `necessity_first_target_plots.py`
- `odc_anchor_plots.py`
- `semantic_dependency_plots.py`
- `semantic_direct_plots.py`
- `semantic_functional_refactoring_plots.py`
- `semantic_recoverability_plots.py`
- `semantic_region_plots.py`
- `semantic_region_replacement_plots.py`
