ABC_DIR=.abc_build/abc_repo
ABC_BIN=$(ABC_DIR)/abc
PYTHON ?= $(shell if [ -x .venv/bin/python ]; then echo .venv/bin/python; else echo python3; fi)

.PHONY: all build-abc generate-benchmarks real-benchmarks generate-all-benchmarks generate-variants analyze check-results plot test sat-refine sat-summary sat-pipeline sat-validation-layers sat-complement topk-eval ablation region cegar-refine hybrid-validate research-plots full-research-pipeline benchmark-manifest list-external import-external start clean clean-results

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

research-plots:
	@echo "Generating research plots → results/plots/"
	@$(PYTHON) research_plots.py

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
		results/topk_recovery.csv results/topk_recovery.md \
		results/ablation_summary.csv results/ablation_summary.md \
		results/region_candidates.csv results/region_summary.csv results/region_summary.md \
		results/cegar_refined_candidates.csv results/cegar_summary.md \
		results/plots \
		results/hybrid \
		variants/ logs/ benchmarks/generated/ benchmarks/real/converted_blif/

# One-command bootstrap: checks prerequisites, then runs the full pipeline.
# Equivalent to running start.sh but usable as a make target.
start:
	@bash ./start.sh
