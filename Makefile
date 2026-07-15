ABC_DIR=.abc_build/abc_repo
ABC_BIN=$(ABC_DIR)/abc
PYTHON ?= $(shell if [ -x .venv/bin/python ]; then echo .venv/bin/python; else echo python3; fi)

.PHONY: all build-abc generate-benchmarks real-benchmarks generate-all-benchmarks generate-variants analyze check-results plot test sat-refine sat-summary sat-pipeline sat-validation-layers sat-complement topk-eval ablation region cegar-refine hybrid-validate abc-sweep-probe abc-sweep-baseline abc-sweep-compare abc-provenance abc-timing-probe yosys-source-probe source-map-prototype register-suggestions contextual-error-analysis contextual-critical-path-map contextual-research-plots research-plots cofactor-sensitivity-analysis functional-ranking-ablation functional-ranking-plots enhanced-critical-path-map check-functional-ranking-results boundary-recovery-benchmarks boundary-recovery-analysis boundary-recovery-critical-path boundary-recovery-plots check-boundary-recovery-results boundary-recovery boundary-recovery-identity boundary-recovery-diagnosis boundary-recovery-critical-path-cois boundary-recovery-diagnosis-plots check-boundary-recovery-diagnosis boundary-recovery-diagnosis-all boundary-recovery-micro-benchmarks boundary-recovery-repair-cois boundary-recovery-check-circuits boundary-recovery-identity-fixed boundary-recovery-corrected-analysis boundary-recovery-critical-path-fixed boundary-recovery-semantics-plots check-boundary-recovery-semantics boundary-recovery-semantics-all extended-boundary-validation extended-boundary-search extended-boundary-comparison extended-boundary-plots check-extended-boundary-results extended-boundary-all odc-anchor-candidates odc-anchor-proofs odc-boundary-recovery odc-anchor-comparison odc-anchor-plots check-odc-anchor-results odc-anchor-all iscas-analysis approx-distance approx-sampling-calibration odc-probe critical-path-map timing-path-probe full-research-pipeline benchmark-manifest list-external import-external start clean clean-results

all: build-abc generate-variants analyze plot

# Build ABC locally under .abc_build/abc_repo
build-abc:
	@echo "Building ABC into $(ABC_DIR) (this may take a few minutes)..."
	@if [ -d "$(ABC_DIR)" ]; then \
		echo "ABC already cloned, skipping clone"; \
	else \
		git clone https://github.com/berkeley-abc/abc.git $(ABC_DIR); \
	fi
	@cd $(ABC_DIR) && make -j2

# Generate synthetic BLIF benchmarks under benchmarks/generated/
generate-benchmarks:
	@echo "Generating synthetic benchmarks → benchmarks/generated/"
	@$(PYTHON) scripts/generate_synthetic_benchmarks.py

# Convert Verilog sources to BLIF (requires Yosys); gracefully skips if Yosys is absent
real-benchmarks:
	@echo "Converting Verilog examples → BLIF (benchmarks/real/verilog_examples/)"
	@$(PYTHON) scripts/import_real_benchmarks.py --verilog benchmarks/real/verilog_examples/

# Both synthetic and real benchmarks in one shot
generate-all-benchmarks: generate-benchmarks real-benchmarks

# ── Research iteration 2: external benchmarks (ISCAS-85 / EPFL) ───────────────

# List external benchmarks currently placed under benchmarks/external/
list-external:
	@$(PYTHON) scripts/import_external_benchmarks.py --list

# Import external benchmarks from a local dir (no downloads). Example:
#   make import-external FAMILY=iscas85 INPUT_DIR=/path/to/iscas85_blifs
#   make import-external FAMILY=epfl    INPUT_DIR=/path/to/epfl ARGS=--convert-aiger
import-external:
	@if [ -z "$(FAMILY)" ] || [ -z "$(INPUT_DIR)" ]; then \
		echo "Usage: make import-external FAMILY=<iscas85|epfl> INPUT_DIR=<dir> [ARGS=--convert-aiger]"; \
		exit 1; \
	fi
	@$(PYTHON) scripts/import_external_benchmarks.py --family $(FAMILY) --input-dir $(INPUT_DIR) $(ARGS)

# Write results/benchmark_manifest.csv describing every benchmark file present
benchmark-manifest:
	@echo "Building benchmark manifest → results/benchmark_manifest.csv"
	@$(PYTHON) scripts/build_benchmark_manifest.py

# Generate optimized BLIF variants using the built ABC
generate-variants: build-abc
	@echo "Generating BLIF variants using $(ABC_BIN)"
	@ABC=$(PWD)/$(ABC_BIN) bash ./run_abc_variants.sh

analyze:
	@echo "Running analysis"
	@$(PYTHON) analyze_blif_matches.py

check-results:
	@echo "Checking result CSV freshness"
	@$(PYTHON) scripts/check_results_freshness.py

plot:
	@echo "Generating plots"
	@$(PYTHON) visualize_results.py

test:
	@echo "Running unit tests"
	@$(PYTHON) -m pytest tests/ -v

sat-refine: build-abc
	@echo "Running ABC equivalence check on high-confidence candidates"
	@ABC=$(PWD)/$(ABC_BIN) $(PYTHON) sat_refinement_abc.py

sat-summary:
	@echo "Generating SAT refinement summary (CSV + Markdown)"
	@$(PYTHON) summarize_sat_results.py

sat-pipeline: build-abc
	@echo "Running full SAT pipeline: filter → ABC CEC → summary"
	@$(PYTHON) select_sat_candidates.py
	@ABC=$(PWD)/$(ABC_BIN) $(PYTHON) sat_refinement_abc.py
	@$(PYTHON) summarize_sat_results.py

sat-validation-layers: build-abc
	@echo "Running layered SAT validation: exact anchors + rank-1 non-exact + top-k non-exact"
	@$(PYTHON) select_sat_candidates.py
	@$(PYTHON) select_validation_candidates.py
	@ABC=$(PWD)/$(ABC_BIN) $(PYTHON) sat_refinement_abc.py
	@SAT_INPUT_CSV=results/sat_exact_anchor_candidates.csv SAT_OUTPUT_CSV=results/sat_exact_anchor_verified.csv ABC=$(PWD)/$(ABC_BIN) $(PYTHON) sat_refinement_abc.py
	@SAT_INPUT_CSV=results/sat_topk_nonexact_candidates.csv SAT_OUTPUT_CSV=results/sat_topk_nonexact_verified.csv ABC=$(PWD)/$(ABC_BIN) $(PYTHON) sat_refinement_abc.py
	@$(PYTHON) summarize_sat_results.py
	@$(PYTHON) analyze_sat_validation_layers.py

sat-complement: build-abc
	@echo "Running complemented SAT validation on same-polarity rejected non-exact candidates"
	@ABC=$(PWD)/$(ABC_BIN) $(PYTHON) sat_complement_refinement.py

topk-eval:
	@echo "Evaluating top-K recovery (CSV + Markdown → results/topk_recovery.*)"
	@$(PYTHON) evaluate_topk_recovery.py

ablation:
	@echo "Running ablation study over scoring configs (CSV + Markdown → results/ablation_summary.*)"
	@$(PYTHON) ablation_study.py

region:
	@echo "Running region correspondence baseline (CSV + Markdown → results/region_*)"
	@$(PYTHON) region_correspondence.py

cegar-refine:
	@echo "Running CEGAR-style candidate refinement [prototype] (CSV + Markdown → results/cegar_*)"
	@$(PYTHON) counterexample_guided_refinement.py

hybrid-validate: build-abc generate-variants analyze
	@echo "Running hybrid ABC SAT sweep validation (Python ranking + ABC dump_equiv/FRAIG)"
	@ABC=$(PWD)/$(ABC_BIN) $(PYTHON) hybrid_validation.py --top-k-validate 20

abc-sweep-probe:
	@echo "Probing ABC-native SAT sweeping / FRAIG command support"
	@if [ ! -x "$(ABC_BIN)" ] && [ -z "$$ABC" ]; then \
		echo "ABC binary not found. Run 'make build-abc' or set ABC=/path/to/abc"; \
		exit 1; \
	fi
	@PYTHONDONTWRITEBYTECODE=1 ABC=$${ABC:-$(PWD)/$(ABC_BIN)} $(PYTHON) scripts/probe_abc_sat_sweeping.py

abc-sweep-baseline: abc-sweep-probe
	@echo "Running lightweight ABC-native SAT sweeping / FRAIG baseline"
	@if [ ! -x "$(ABC_BIN)" ] && [ -z "$$ABC" ]; then \
		echo "ABC binary not found. Run 'make build-abc' or set ABC=/path/to/abc"; \
		exit 1; \
	fi
	@PYTHONDONTWRITEBYTECODE=1 ABC=$${ABC:-$(PWD)/$(ABC_BIN)} $(PYTHON) scripts/abc_native_sat_sweep_baseline.py

abc-sweep-compare:
	@echo "Comparing ABC-native sweep baseline with custom correspondence results"
	@PYTHONDONTWRITEBYTECODE=1 $(PYTHON) scripts/compare_abc_native_vs_custom.py

abc-provenance:
	@echo "Investigating ABC-native FRAIG provenance / equivalence-class visibility"
	@if [ ! -x "$(ABC_BIN)" ] && [ -z "$$ABC" ]; then \
		echo "ABC binary not found. Run 'make build-abc' or set ABC=/path/to/abc"; \
		exit 1; \
	fi
	@PYTHONDONTWRITEBYTECODE=1 ABC=$${ABC:-$(PWD)/$(ABC_BIN)} $(PYTHON) scripts/investigate_abc_provenance.py

abc-timing-probe:
	@echo "Probing ABC timing / delay / level command support"
	@if [ ! -x "$(ABC_BIN)" ] && [ -z "$$ABC" ]; then \
		echo "ABC binary not found. Run 'make build-abc' or set ABC=/path/to/abc"; \
		exit 1; \
	fi
	@PYTHONDONTWRITEBYTECODE=1 ABC=$${ABC:-$(PWD)/$(ABC_BIN)} $(PYTHON) scripts/probe_abc_timing_commands.py

research-plots:
	@echo "Generating research plots → results/plots/"
	@$(PYTHON) research_plots.py

iscas-analysis:
	@echo "Analyzing SAT/CEC-proven ISCAS-85 structural-mismatch matches"
	@$(PYTHON) scripts/analyze_iscas_verified_matches.py

# Regenerates variants first because the distance script evaluates candidate
# nodes directly from the original and optimized BLIF files.
approx-distance: generate-variants
	@echo "Computing approximate node distances for ISCAS-85 candidates"
	@$(PYTHON) scripts/approximate_node_distance.py

approx-sampling-calibration:
	@echo "Calibrating sampled approximate-distance estimates against exact rows"
	@PYTHONDONTWRITEBYTECODE=1 $(PYTHON) scripts/calibrate_approximate_distance_sampling.py

odc-probe:
	@echo "Running tiny ODC-aware matching probe"
	@if [ ! -x "$(ABC_BIN)" ] && [ -z "$$ABC" ]; then \
		echo "ABC binary not found. Run 'make build-abc' or set ABC=/path/to/abc"; \
		exit 1; \
	fi
	@PYTHONDONTWRITEBYTECODE=1 ABC=$${ABC:-$(PWD)/$(ABC_BIN)} $(PYTHON) scripts/odc_aware_match_probe.py

critical-path-map: approx-distance
	@echo "Mapping structural critical paths back to original ISCAS-85 nodes"
	@$(PYTHON) scripts/critical_path_back_mapping.py

timing-path-probe:
	@echo "Comparing structural and delay-weighted critical-path back-mapping"
	@if [ ! -x "$(ABC_BIN)" ] && [ -z "$$ABC" ]; then \
		echo "ABC binary not found. Run 'make build-abc' or set ABC=/path/to/abc"; \
		exit 1; \
	fi
	@PYTHONDONTWRITEBYTECODE=1 ABC=$${ABC:-$(PWD)/$(ABC_BIN)} $(PYTHON) scripts/timing_aware_path_probe.py

yosys-source-probe:
	@echo "Probing Yosys RTL/source metadata preservation"
	@PYTHONDONTWRITEBYTECODE=1 $(PYTHON) scripts/probe_yosys_source_metadata.py

source-map-prototype:
	@echo "Building tiny RTL/source-map prototype"
	@PYTHONDONTWRITEBYTECODE=1 $(PYTHON) scripts/build_source_map_prototype.py

register-suggestions:
	@echo "Suggesting engineer-review register insertion points from mapped critical paths"
	@PYTHONDONTWRITEBYTECODE=1 $(PYTHON) scripts/suggest_register_insertion_points.py

contextual-error-analysis:
	@echo "Running contextual formal/error-metric correspondence analysis"
	@PYTHONDONTWRITEBYTECODE=1 $(PYTHON) scripts/contextual_correspondence_analysis.py

contextual-critical-path-map: contextual-error-analysis
	@echo "Contextual critical-path mapping written to results/contextual_critical_path_mapping.*"

contextual-research-plots: contextual-error-analysis
	@echo "Contextual plots written to results/plots/contextual_* and results/plots/global_vs_contextual_error.png"

cofactor-sensitivity-analysis:
	@echo "Computing Shannon-cofactor and sensitivity ranking features"
	@PYTHONDONTWRITEBYTECODE=1 $(PYTHON) scripts/cofactor_sensitivity_correspondence_analysis.py

functional-ranking-ablation: cofactor-sensitivity-analysis
	@echo "Comparing functional ranking ablations"
	@PYTHONDONTWRITEBYTECODE=1 $(PYTHON) scripts/compare_functional_ranking_ablations.py

functional-ranking-plots: functional-ranking-ablation
	@echo "Functional ranking plots written to results/plots/functional_*"

enhanced-critical-path-map: cofactor-sensitivity-analysis
	@echo "Joining enhanced ranking features onto critical-path mappings"
	@PYTHONDONTWRITEBYTECODE=1 $(PYTHON) scripts/enhanced_critical_path_mapping.py

check-functional-ranking-results:
	@echo "Checking functional ranking result schemas"
	@PYTHONDONTWRITEBYTECODE=1 $(PYTHON) scripts/check_functional_ranking_results.py

boundary-recovery-benchmarks:
	@echo "Boundary recovery COI specs available under benchmarks/coi_specs/"
	@test -f benchmarks/coi_specs/boundary_recovery_seed_cois.json

boundary-recovery-analysis: boundary-recovery-benchmarks
	@echo "Running equivalence-anchored boundary recovery"
	@PYTHONDONTWRITEBYTECODE=1 $(PYTHON) scripts/recover_equivalence_anchored_boundaries.py

boundary-recovery-critical-path: boundary-recovery-analysis
	@echo "Checking critical-path nodes enclosed by recovered regions"
	@PYTHONDONTWRITEBYTECODE=1 $(PYTHON) scripts/boundary_recovery_critical_path.py

boundary-recovery-plots: boundary-recovery-critical-path
	@echo "Boundary recovery plots written to results/plots/boundary_*"
	@PYTHONDONTWRITEBYTECODE=1 $(PYTHON) scripts/boundary_recovery_plots.py

check-boundary-recovery-results:
	@echo "Checking boundary recovery result schemas"
	@PYTHONDONTWRITEBYTECODE=1 $(PYTHON) scripts/check_boundary_recovery_results.py

boundary-recovery: boundary-recovery-analysis boundary-recovery-critical-path boundary-recovery-plots check-boundary-recovery-results
	@echo "Boundary recovery pipeline complete."

boundary-recovery-identity: boundary-recovery-benchmarks
	@echo "Running identity S-versus-S boundary recovery baseline"
	@PYTHONDONTWRITEBYTECODE=1 $(PYTHON) scripts/run_boundary_recovery_identity_baseline.py

boundary-recovery-diagnosis: boundary-recovery
	@echo "Diagnosing boundary-recovery failures and anchor coverage"
	@PYTHONDONTWRITEBYTECODE=1 $(PYTHON) scripts/diagnose_boundary_recovery_failures.py

boundary-recovery-critical-path-cois:
	@echo "Generating bounded critical-path diagnostic COIs"
	@PYTHONDONTWRITEBYTECODE=1 $(PYTHON) scripts/generate_critical_path_cois.py

boundary-recovery-diagnosis-plots: boundary-recovery-diagnosis
	@echo "Generating boundary diagnosis plots"
	@PYTHONDONTWRITEBYTECODE=1 $(PYTHON) scripts/boundary_diagnosis_plots.py

check-boundary-recovery-diagnosis:
	@echo "Checking boundary diagnosis result schemas"
	@PYTHONDONTWRITEBYTECODE=1 $(PYTHON) scripts/check_boundary_diagnosis_results.py

boundary-recovery-diagnosis-all: boundary-recovery-identity boundary-recovery-diagnosis boundary-recovery-critical-path-cois boundary-recovery-diagnosis-plots check-boundary-recovery-diagnosis
	@echo "Boundary recovery diagnosis pipeline complete."

boundary-recovery-micro-benchmarks:
	@echo "Generating boundary-recovery micro benchmarks and COIs"
	@PYTHONDONTWRITEBYTECODE=1 $(PYTHON) scripts/generate_boundary_recovery_micro_benchmarks.py

boundary-recovery-repair-cois: boundary-recovery-micro-benchmarks
	@echo "Repairing and normalizing COIs under canonical semantics"
	@PYTHONDONTWRITEBYTECODE=1 $(PYTHON) scripts/repair_boundary_recovery_cois.py

boundary-recovery-check-circuits: boundary-recovery-repair-cois
	@echo "Checking canonical COI circuit availability"
	@PYTHONDONTWRITEBYTECODE=1 $(PYTHON) scripts/check_boundary_recovery_circuits.py

boundary-recovery-identity-fixed: boundary-recovery-check-circuits
	@echo "Running fixed exact identity boundary recovery"
	@PYTHONDONTWRITEBYTECODE=1 $(PYTHON) scripts/run_boundary_recovery_identity_fixed.py

boundary-recovery-corrected-analysis: boundary-recovery-identity-fixed
	@echo "Running corrected optimized boundary recovery over eligible COIs"
	@PYTHONDONTWRITEBYTECODE=1 $(PYTHON) scripts/run_boundary_recovery_corrected_analysis.py
	@PYTHONDONTWRITEBYTECODE=1 $(PYTHON) scripts/summarize_boundary_recovery_semantics.py

boundary-recovery-critical-path-fixed: boundary-recovery-identity-fixed
	@echo "Generating canonical critical-path COI validation rows"
	@PYTHONDONTWRITEBYTECODE=1 $(PYTHON) scripts/run_boundary_recovery_critical_path_fixed.py

boundary-recovery-semantics-plots: boundary-recovery-corrected-analysis boundary-recovery-critical-path-fixed
	@echo "Generating repaired boundary semantics plots"
	@PYTHONDONTWRITEBYTECODE=1 $(PYTHON) scripts/summarize_boundary_recovery_semantics.py
	@PYTHONDONTWRITEBYTECODE=1 $(PYTHON) scripts/boundary_recovery_semantics_plots.py

check-boundary-recovery-semantics:
	@echo "Checking repaired boundary semantics outputs"
	@PYTHONDONTWRITEBYTECODE=1 $(PYTHON) scripts/check_boundary_recovery_semantics.py

boundary-recovery-semantics-all: boundary-recovery-micro-benchmarks boundary-recovery-repair-cois boundary-recovery-check-circuits boundary-recovery-identity-fixed boundary-recovery-corrected-analysis boundary-recovery-critical-path-fixed boundary-recovery-semantics-plots check-boundary-recovery-semantics
	@echo "Boundary recovery semantics repair pipeline complete."

extended-boundary-validation: boundary-recovery-identity-fixed boundary-recovery-corrected-analysis
	@echo "Evaluating first-frontier and cost-guided extended-boundary validity"
	@PYTHONDONTWRITEBYTECODE=1 $(PYTHON) scripts/evaluate_extended_boundary_correctness.py

extended-boundary-search: boundary-recovery-identity-fixed boundary-recovery-corrected-analysis
	@echo "Running cost-guided extended-boundary search"
	@PYTHONDONTWRITEBYTECODE=1 $(PYTHON) scripts/evaluate_extended_boundary_correctness.py --search-mode all

extended-boundary-comparison: extended-boundary-search
	@echo "Comparing extended-boundary search strategies"
	@PYTHONDONTWRITEBYTECODE=1 $(PYTHON) scripts/compare_boundary_search_strategies.py

extended-boundary-plots: extended-boundary-comparison
	@echo "Generating extended-boundary plots"
	@PYTHONDONTWRITEBYTECODE=1 $(PYTHON) scripts/extended_boundary_plots.py

check-extended-boundary-results:
	@echo "Checking extended-boundary results"
	@PYTHONDONTWRITEBYTECODE=1 $(PYTHON) scripts/check_extended_boundary_results.py

extended-boundary-all: boundary-recovery-semantics-all extended-boundary-validation extended-boundary-search extended-boundary-comparison extended-boundary-plots check-extended-boundary-results
	@echo "Extended-boundary recovery pipeline complete."

odc-anchor-candidates: extended-boundary-all
	@echo "Generating formal ODC anchor candidates"
	@PYTHONDONTWRITEBYTECODE=1 $(PYTHON) scripts/generate_odc_anchor_candidates.py

odc-anchor-proofs: odc-anchor-candidates
	@echo "Proving formal ODC anchor candidates"
	@PYTHONDONTWRITEBYTECODE=1 $(PYTHON) scripts/prove_odc_anchors.py

odc-boundary-recovery: odc-anchor-proofs
	@echo "Running boundary recovery with formal ODC anchors"
	@PYTHONDONTWRITEBYTECODE=1 $(PYTHON) scripts/run_odc_boundary_recovery.py

odc-anchor-comparison: odc-boundary-recovery
	@echo "Comparing ODC anchor modes"
	@PYTHONDONTWRITEBYTECODE=1 $(PYTHON) scripts/compare_odc_anchor_modes.py

odc-anchor-plots: odc-anchor-comparison
	@echo "Generating ODC anchor plots"
	@PYTHONDONTWRITEBYTECODE=1 $(PYTHON) scripts/odc_anchor_plots.py

check-odc-anchor-results:
	@echo "Checking ODC anchor results"
	@PYTHONDONTWRITEBYTECODE=1 $(PYTHON) scripts/check_odc_anchor_results.py

odc-anchor-all: odc-anchor-candidates odc-anchor-proofs odc-boundary-recovery odc-anchor-comparison odc-anchor-plots check-odc-anchor-results
	@echo "ODC anchor generation pipeline complete."

full-research-pipeline: generate-variants analyze benchmark-manifest sat-pipeline topk-eval ablation region cegar-refine research-plots test
	@echo ""
	@echo "Full research pipeline complete."
	@echo "Plots  : results/plots/"
	@echo "Tables : results/*.csv  results/*.md"

clean:
	@echo "Cleaning ABC build (does NOT remove variants/logs/results)"
	@rm -rf $(ABC_DIR)

clean-results:
	@echo "Removing generated results, variants, and logs (keeps benchmarks and scripts)"
	@rm -rf results/summary_metrics.csv results/top_candidates.csv \
		results/node_fingerprints.csv results/benchmark_manifest.csv \
		results/sat_refinement_candidates.csv results/sat_verified_candidates.csv \
		results/sat_summary.csv results/sat_summary.md \
		results/sat_exact_anchor_candidates.csv results/sat_exact_anchor_verified.csv \
		results/sat_topk_nonexact_candidates.csv results/sat_topk_nonexact_verified.csv \
		results/sat_validation_layers_summary.csv results/sat_validation_layers.md \
		results/sat_complement_rank1_nonexact.csv results/sat_complement_topk_nonexact.csv \
		results/sat_complement_summary.csv results/sat_complement_summary.md \
		results/sat_false_positive_analysis.csv \
		results/approximate_distance_exact.csv results/approximate_distance_sampled.csv \
		results/approximate_distance_skipped.csv results/approximate_distance_summary.csv \
		results/approximate_distance_summary.md \
		results/approx_sampling_calibration.csv results/approx_sampling_calibration.md \
		results/odc_probe_results.csv results/odc_probe_results.md \
		results/critical_path_mapping.csv results/critical_path_mapping.md \
		results/abc_sat_sweeping_capabilities.csv results/abc_sat_sweeping_capabilities.md \
		results/abc_native_sweep_baseline.csv results/abc_native_sweep_baseline.md \
		results/abc_native_vs_custom_comparison.csv results/abc_native_vs_custom_comparison.md \
		results/abc_provenance_probe.csv results/abc_provenance_probe.md \
		results/abc_timing_command_probe.csv results/abc_timing_command_probe.md \
		results/timing_path_probe.csv results/timing_path_probe.md \
		results/timing_vs_structural_mapping.csv results/timing_vs_structural_mapping.md \
		results/yosys_source_metadata_probe.csv results/yosys_source_metadata_probe.md \
		results/source_map_prototype.csv results/source_map_prototype.md \
		results/source_mapping_next_steps.md \
		results/register_insertion_suggestions.csv results/register_insertion_suggestions.md \
		results/contextual_error_metrics.csv results/contextual_error_metrics_summary.csv \
		results/contextual_error_metrics.md results/contextual_critical_path_mapping.csv \
		results/contextual_critical_path_mapping.md \
		results/topk_recovery.csv results/topk_recovery.md \
		results/ablation_summary.csv results/ablation_summary.md \
		results/region_candidates.csv results/region_summary.csv results/region_summary.md \
		results/cegar_refined_candidates.csv results/cegar_summary.md \
		results/plots \
		results/abc_native_inputs results/abc_native_swept \
		results/hybrid \
		variants/ logs/ benchmarks/generated/ benchmarks/real/converted_blif/

# One-command bootstrap: checks prerequisites, then runs the full pipeline.
# Equivalent to running start.sh but usable as a make target.
start:
	@bash ./start.sh
