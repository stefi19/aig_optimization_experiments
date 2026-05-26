ABC_DIR=.abc_build/abc_repo
ABC_BIN=$(ABC_DIR)/abc

.PHONY: all build-abc generate-variants analyze plot test sat-refine clean clean-results

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

clean:
	@echo "Cleaning ABC build (does NOT remove variants/logs/results)"
	@rm -rf $(ABC_DIR)

clean-results:
	@echo "Removing generated results, variants, and logs (keeps benchmarks and scripts)"
	@rm -rf results/summary_metrics.csv results/top_candidates.csv \
		results/sat_refinement_candidates.csv results/plots \
		variants/ logs/
