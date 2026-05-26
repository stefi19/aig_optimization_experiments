ABC_DIR=.abc_build/abc_repo
ABC_BIN=$(ABC_DIR)/abc

.PHONY: all build-abc generate-benchmarks real-benchmarks generate-all-benchmarks generate-variants analyze plot test sat-refine sat-summary sat-pipeline topk-eval ablation region cegar-refine research-plots full-research-pipeline start clean clean-results

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
	@python3 scripts/generate_synthetic_benchmarks.py

# Convert Verilog sources to BLIF (requires Yosys); gracefully skips if Yosys is absent
real-benchmarks:
	@echo "Converting Verilog examples → BLIF (benchmarks/real/verilog_examples/)"
	@python3 scripts/import_real_benchmarks.py --verilog benchmarks/real/verilog_examples/

# Both synthetic and real benchmarks in one shot
generate-all-benchmarks: generate-benchmarks real-benchmarks

# Generate optimized BLIF variants using the built ABC
generate-variants: build-abc
	@echo "Generating BLIF variants using $(ABC_BIN)"
	@ABC=$(PWD)/$(ABC_BIN) bash ./run_abc_variants.sh

analyze:
	@echo "Running analysis"
	@python3 analyze_blif_matches.py

plot:
	@echo "Generating plots"
	@python3 visualize_results.py

test:
	@echo "Running unit tests"
	@python3 -m pytest tests/ -v

sat-refine:
	@echo "Running ABC equivalence check on high-confidence candidates"
	@python3 sat_refinement_abc.py

sat-summary:
	@echo "Generating SAT refinement summary (CSV + Markdown)"
	@python3 summarize_sat_results.py

sat-pipeline:
	@echo "Running full SAT pipeline: filter → ABC CEC → summary"
	@python3 select_sat_candidates.py
	@python3 sat_refinement_abc.py
	@python3 summarize_sat_results.py

topk-eval:
	@echo "Evaluating top-K recovery (CSV + Markdown → results/topk_recovery.*)"
	@python3 evaluate_topk_recovery.py

ablation:
	@echo "Running ablation study over scoring configs (CSV + Markdown → results/ablation_summary.*)"
	@python3 ablation_study.py

region:
	@echo "Running region correspondence baseline (CSV + Markdown → results/region_*)"
	@python3 region_correspondence.py

cegar-refine:
	@echo "Running CEGAR-style candidate refinement [prototype] (CSV + Markdown → results/cegar_*)"
	@python3 counterexample_guided_refinement.py

research-plots:
	@echo "Generating research plots → results/plots/"
	@python3 research_plots.py

full-research-pipeline: generate-variants analyze sat-pipeline topk-eval ablation region cegar-refine research-plots test
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
		results/node_fingerprints.csv \
		results/sat_refinement_candidates.csv results/sat_verified_candidates.csv \
		results/sat_summary.csv results/sat_summary.md \
		results/topk_recovery.csv results/topk_recovery.md \
		results/ablation_summary.csv results/ablation_summary.md \
		results/region_candidates.csv results/region_summary.csv results/region_summary.md \
		results/cegar_refined_candidates.csv results/cegar_summary.md \
		results/plots \
		variants/ logs/ benchmarks/generated/ benchmarks/real/converted_blif/

# One-command bootstrap: checks prerequisites, then runs the full pipeline.
# Equivalent to running start.sh but usable as a make target.
start:
	@bash ./start.sh
