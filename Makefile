ABC_DIR=.abc_build/abc_repo
ABC_REV ?= bcfdf592289a408cd67ec19260f8a60a37b085b6
ABC_BIN=$(ABC_DIR)/abc
PYTHON = $(shell if [ -x .venv-z3/bin/python ]; then echo .venv-z3/bin/python; elif [ -x .venv/bin/python ]; then echo .venv/bin/python; else echo python3; fi)
Z3_PYTHON = $(shell if [ -x .venv-z3/bin/python ]; then echo .venv-z3/bin/python; else echo $(PYTHON); fi)

.PHONY: all install-z3 check-z3 build-abc check-abc generate-benchmarks real-benchmarks generate-all-benchmarks generate-variants semantic-benchmarks semantic-benchmarks-check semantic-regions semantic-interfaces semantic-region-comparison semantic-region-plots check-semantic-regions semantic-regions-all semantic-bus-inference semantic-dependency semantic-family-ranking semantic-bus-ablation semantic-dependency-plots check-semantic-bus-dependency semantic-bus-dependency-all semantic-direct-candidates semantic-direct-simulation semantic-direct-verification semantic-direct-selection semantic-direct-ablation semantic-direct-plots check-semantic-direct-results semantic-direct-recovery-all semantic-z3-crosscheck semantic-wide-benchmarks semantic-z3-cegis semantic-blind-oracle-ablation semantic-scalability-analysis semantic-graft-diagnosis semantic-graft-normalization semantic-graft-edge-substitution semantic-graft-coi-splice semantic-graft-extended-region semantic-graft-odc semantic-graft-strategy-ablation semantic-graft-all check-semantic-z3-results blind-semantic-cegis-scalable-all blind-semantic-audit blind-semantic-buses semantic-parametric-candidates semantic-cegis semantic-smt-proofs semantic-cegis-evaluation semantic-graft-targets semantic-graft-build semantic-graft-proofs semantic-graft-boundary-recovery semantic-graft-ablation semantic-graft-plots check-blind-semantic-results check-semantic-graft-results blind-semantic-cegis-all semantic-grafting-all analyze check-results plot test sat-refine sat-summary sat-pipeline sat-validation-layers sat-complement topk-eval ablation region cegar-refine hybrid-validate abc-sweep-probe abc-sweep-baseline abc-sweep-compare abc-provenance abc-timing-probe yosys-source-probe source-map-prototype register-suggestions contextual-error-analysis contextual-critical-path-map contextual-research-plots research-plots cofactor-sensitivity-analysis functional-ranking-ablation functional-ranking-plots enhanced-critical-path-map check-functional-ranking-results boundary-recovery-benchmarks boundary-recovery-analysis boundary-recovery-critical-path boundary-recovery-plots check-boundary-recovery-results boundary-recovery boundary-recovery-identity boundary-recovery-diagnosis boundary-recovery-critical-path-cois boundary-recovery-diagnosis-plots check-boundary-recovery-diagnosis boundary-recovery-diagnosis-all boundary-recovery-micro-benchmarks boundary-recovery-repair-cois boundary-recovery-check-circuits boundary-recovery-identity-fixed boundary-recovery-corrected-analysis boundary-recovery-critical-path-fixed boundary-recovery-semantics-plots check-boundary-recovery-semantics boundary-recovery-semantics-all extended-boundary-validation extended-boundary-search extended-boundary-comparison extended-boundary-plots check-extended-boundary-results extended-boundary-all odc-anchor-candidates odc-anchor-proofs odc-boundary-recovery odc-anchor-comparison odc-anchor-plots check-odc-anchor-results odc-anchor-all materialization-targets anchored-cuts anchored-cut-functions materialized-wires materialized-anchor-proofs materialized-boundary-recovery materialized-ablation materialized-plots check-materialized-results materialized-correspondence-all iscas-analysis approx-distance approx-sampling-calibration odc-probe critical-path-map timing-path-probe full-research-pipeline benchmark-manifest list-external import-external start clean clean-results
.PHONY: joint-region-interface joint-region-interface-controlled joint-region-interface-real joint-region-interface-heldout joint-region-interface-ablations joint-region-interface-plots check-joint-region-interface-results joint-region-interface-all
.PHONY: semantic-functional-refactoring-controlled semantic-functional-refactoring-development semantic-functional-refactoring-heldout semantic-functional-refactoring-ablations semantic-functional-refactoring-plots check-semantic-functional-refactoring-results semantic-functional-refactoring-all
.PHONY: semantic-recoverability-benchmarks semantic-recoverability-trajectories semantic-recoverability-controlled semantic-recoverability-development semantic-recoverability-heldout semantic-recoverability-oracle semantic-recoverability-pass-ablations semantic-recoverability-durability semantic-recoverability-plots check-semantic-recoverability-results semantic-recoverability-all
.PHONY: active-source-counterparts-controlled active-source-counterparts-development active-source-counterparts-heldout active-source-counterparts-durability active-source-counterparts-ablations active-source-counterparts-plots check-active-source-counterpart-results active-source-counterparts-all
.PHONY: cross-netlist-transplant-controlled cross-netlist-transplant-development cross-netlist-transplant-heldout cross-netlist-transplant-oracle cross-netlist-transplant-durability cross-netlist-transplant-ablations cross-netlist-transplant-plots check-cross-netlist-transplant-results cross-netlist-transplant-all

all: build-abc generate-variants analyze plot

install-z3:
	@echo "Installing Z3 solver dependency"
	@if [ ! -x ".venv-z3/bin/python" ]; then python3.11 -m venv .venv-z3; fi
	@.venv-z3/bin/python -m pip install --disable-pip-version-check --no-cache-dir -r requirements.txt

check-z3: install-z3
	@echo "Checking Z3 bit-vector solver"
	@PYTHONDONTWRITEBYTECODE=1 $(Z3_PYTHON) scripts/check_z3.py

# Build ABC locally under .abc_build/abc_repo
build-abc:
	@echo "Building ABC $(ABC_REV) into $(ABC_DIR) (this may take a few minutes)..."
	@if [ -d "$(ABC_DIR)" ]; then \
		echo "ABC already cloned, skipping clone"; \
	else \
		git clone https://github.com/berkeley-abc/abc.git $(ABC_DIR); \
	fi
	@git -C $(ABC_DIR) fetch origin $(ABC_REV) || git -C $(ABC_DIR) fetch origin
	@git -C $(ABC_DIR) checkout --detach $(ABC_REV)
	@cd $(ABC_DIR) && make ABC_USE_NO_READLINE=1 -j2

check-abc: build-abc
	@echo "Checking pinned ABC binary"
	@$(ABC_BIN) -c "version"

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

# Generate source-level semantic-recovery benchmark cases and bounded BLIF/ABC variants.
semantic-benchmarks:
	@echo "Generating semantic-recovery benchmark suite"
	@PYTHONDONTWRITEBYTECODE=1 ABC=$${ABC:-$(PWD)/$(ABC_BIN)} $(PYTHON) scripts/generate_semantic_recovery_benchmarks.py

semantic-benchmarks-check:
	@echo "Checking semantic-recovery benchmark suite"
	@PYTHONDONTWRITEBYTECODE=1 $(PYTHON) scripts/check_semantic_recovery_benchmarks.py

semantic-regions: semantic-benchmarks semantic-benchmarks-check
	@echo "Building canonical semantic regions"
	@PYTHONDONTWRITEBYTECODE=1 $(PYTHON) scripts/build_semantic_regions.py

semantic-interfaces: semantic-regions
	@echo "Extracting canonical scalar semantic interfaces"
	@PYTHONDONTWRITEBYTECODE=1 $(PYTHON) scripts/extract_semantic_interfaces.py

semantic-region-comparison: semantic-interfaces
	@echo "Comparing semantic region sources"
	@PYTHONDONTWRITEBYTECODE=1 $(PYTHON) scripts/compare_semantic_region_sources.py

semantic-region-plots: semantic-region-comparison
	@echo "Generating semantic region/interface plots"
	@PYTHONDONTWRITEBYTECODE=1 $(PYTHON) scripts/semantic_region_plots.py

check-semantic-regions:
	@echo "Checking semantic region/interface outputs"
	@PYTHONDONTWRITEBYTECODE=1 $(PYTHON) scripts/check_semantic_regions.py

semantic-regions-all: semantic-benchmarks semantic-benchmarks-check semantic-regions semantic-interfaces semantic-region-comparison semantic-region-plots check-semantic-regions
	@echo "Semantic region and interface pipeline complete."

semantic-bus-inference: semantic-regions-all
	@echo "Inferring semantic bus hypotheses from scalar interfaces"
	@PYTHONDONTWRITEBYTECODE=1 $(PYTHON) scripts/infer_semantic_buses.py

semantic-dependency: semantic-bus-inference
	@echo "Computing semantic dependency matrices and geometry features"
	@PYTHONDONTWRITEBYTECODE=1 $(PYTHON) scripts/compute_semantic_dependencies.py

semantic-family-ranking: semantic-dependency
	@echo "Ranking broad semantic families from bus/dependency features"
	@PYTHONDONTWRITEBYTECODE=1 $(PYTHON) scripts/rank_semantic_families.py

semantic-bus-ablation: semantic-family-ranking
	@echo "Comparing semantic bus and family-ranking ablations"
	@PYTHONDONTWRITEBYTECODE=1 $(PYTHON) scripts/compare_semantic_bus_ablations.py

semantic-dependency-plots: semantic-bus-ablation
	@echo "Generating semantic bus/dependency plots"
	@PYTHONDONTWRITEBYTECODE=1 $(PYTHON) scripts/semantic_dependency_plots.py

check-semantic-bus-dependency:
	@echo "Checking semantic bus/dependency outputs"
	@PYTHONDONTWRITEBYTECODE=1 $(PYTHON) scripts/check_semantic_bus_dependency_results.py

semantic-bus-dependency-all: semantic-regions-all semantic-bus-inference semantic-dependency semantic-family-ranking semantic-bus-ablation semantic-dependency-plots check-semantic-bus-dependency
	@echo "Semantic bus inference and dependency geometry pipeline complete."

semantic-direct-candidates: semantic-bus-dependency-all
	@echo "Generating typed direct semantic template candidates"
	@PYTHONDONTWRITEBYTECODE=1 $(PYTHON) scripts/generate_semantic_direct_candidates.py

semantic-direct-simulation: semantic-direct-candidates
	@echo "Simulating direct semantic candidates with deterministic semantic patterns"
	@PYTHONDONTWRITEBYTECODE=1 $(PYTHON) scripts/simulate_semantic_candidates.py

semantic-direct-verification: semantic-direct-simulation
	@echo "Formally verifying simulation-surviving direct semantic candidates"
	@PYTHONDONTWRITEBYTECODE=1 $(PYTHON) scripts/verify_semantic_candidates.py

semantic-direct-selection: semantic-direct-verification
	@echo "Selecting best formally verified direct semantic expressions"
	@PYTHONDONTWRITEBYTECODE=1 $(PYTHON) scripts/select_semantic_expressions.py

semantic-direct-ablation: semantic-direct-selection
	@echo "Comparing direct semantic recovery ablations"
	@PYTHONDONTWRITEBYTECODE=1 $(PYTHON) scripts/compare_semantic_direct_ablations.py

semantic-direct-plots: semantic-direct-ablation
	@echo "Generating direct semantic recovery plots"
	@PYTHONDONTWRITEBYTECODE=1 $(PYTHON) scripts/semantic_direct_plots.py

check-semantic-direct-results:
	@echo "Checking direct semantic recovery outputs"
	@PYTHONDONTWRITEBYTECODE=1 $(PYTHON) scripts/check_semantic_direct_results.py

semantic-direct-recovery-all: semantic-benchmarks semantic-benchmarks-check semantic-regions-all semantic-bus-dependency-all semantic-direct-candidates semantic-direct-simulation semantic-direct-verification semantic-direct-selection semantic-direct-ablation semantic-direct-plots check-semantic-direct-results
	@echo "Direct semantic template recovery pipeline complete."

blind-semantic-audit:
	@echo "Auditing inference-time semantic ground-truth leakage"
	@PYTHONDONTWRITEBYTECODE=1 $(PYTHON) scripts/run_blind_semantic_cegis.py audit

blind-semantic-buses: blind-semantic-audit
	@echo "Inferring source-blind bus/interface hypotheses"
	@PYTHONDONTWRITEBYTECODE=1 $(PYTHON) scripts/run_blind_semantic_cegis.py buses

semantic-parametric-candidates: blind-semantic-buses
	@echo "Enumerating blind parametric semantic candidates"
	@PYTHONDONTWRITEBYTECODE=1 $(PYTHON) scripts/run_blind_semantic_cegis.py cegis

semantic-cegis: semantic-parametric-candidates
	@echo "Running bounded blind CEGIS loop"
	@PYTHONDONTWRITEBYTECODE=1 $(PYTHON) scripts/run_blind_semantic_cegis.py cegis

semantic-smt-proofs: semantic-cegis
	@echo "Checking formal proof metadata"
	@PYTHONDONTWRITEBYTECODE=1 $(PYTHON) scripts/check_blind_semantic_results.py

semantic-z3-crosscheck: check-z3 semantic-cegis
	@echo "Cross-checking Z3 region proofs against exhaustive verification"
	@PYTHONDONTWRITEBYTECODE=1 $(Z3_PYTHON) scripts/semantic_z3_crosscheck.py

semantic-z3-cegis: semantic-z3-crosscheck
	@echo "Running Z3-backed blind and oracle-bus CEGIS"
	@PYTHONDONTWRITEBYTECODE=1 $(Z3_PYTHON) scripts/semantic_z3_cegis_experiment.py

semantic-blind-oracle-ablation: semantic-z3-cegis
	@echo "Blind/oracle Z3 CEGIS comparison written to results/blind_semantic_cegis/z3_blind_oracle_comparison.csv"

semantic-wide-benchmarks: semantic-z3-cegis
	@echo "Wide semantic attempts are included in z3_recovery_by_width.csv"

semantic-scalability-analysis: semantic-wide-benchmarks semantic-blind-oracle-ablation
	@echo "Scalability analysis rows are in results/blind_semantic_cegis/z3_recovery_by_width.csv"

blind-semantic-cegis-scalable-all: semantic-z3-crosscheck semantic-z3-cegis semantic-blind-oracle-ablation semantic-wide-benchmarks semantic-scalability-analysis check-semantic-z3-results
	@echo "Scalable blind semantic CEGIS pipeline complete."

check-semantic-z3-results:
	@echo "Checking Z3 semantic result outputs"
	@PYTHONDONTWRITEBYTECODE=1 $(PYTHON) scripts/check_blind_semantic_results.py

semantic-cegis-evaluation: semantic-smt-proofs
	@echo "Joining evaluation-only labels after blind predictions"
	@PYTHONDONTWRITEBYTECODE=1 $(PYTHON) scripts/run_blind_semantic_cegis.py evaluate

semantic-graft-targets: semantic-cegis-evaluation
	@echo "Selecting boundary-utility-aware semantic graft targets"
	@PYTHONDONTWRITEBYTECODE=1 $(PYTHON) scripts/run_semantic_grafting.py

semantic-graft-build: semantic-graft-targets
	@echo "Building semantic graft candidates"
	@PYTHONDONTWRITEBYTECODE=1 $(PYTHON) scripts/run_semantic_grafting.py

semantic-graft-proofs: semantic-graft-build
	@echo "Checking semantic graft proof funnel"
	@PYTHONDONTWRITEBYTECODE=1 $(PYTHON) scripts/check_semantic_graft_results.py

semantic-graft-boundary-recovery: semantic-graft-proofs
	@echo "Semantic graft boundary-recovery rows are in results/semantic_grafting/"

semantic-graft-ablation: semantic-graft-boundary-recovery
	@echo "Semantic graft ablation rows are in results/semantic_grafting/target_selection_ablation.csv"

semantic-graft-diagnosis: semantic-graft-targets
	@echo "Semantic graft diagnosis rows are in results/semantic_grafting/graft_placement_attempts.csv"

semantic-graft-normalization: semantic-graft-diagnosis
	@echo "In-place normalization attempts recorded."

semantic-graft-edge-substitution: semantic-graft-diagnosis
	@echo "Equivalent-edge substitution attempts recorded."

semantic-graft-coi-splice: semantic-graft-diagnosis
	@echo "COI boundary-output splice attempts recorded."

semantic-graft-extended-region: semantic-graft-diagnosis
	@echo "Extended-region graft attempts recorded."

semantic-graft-odc: semantic-graft-diagnosis
	@echo "ODC contextual graft attempts recorded."

semantic-graft-strategy-ablation: semantic-graft-normalization semantic-graft-edge-substitution semantic-graft-coi-splice semantic-graft-extended-region semantic-graft-odc
	@echo "Semantic graft strategy ablation complete."

semantic-graft-all: semantic-graft-strategy-ablation semantic-graft-plots check-semantic-graft-results
	@echo "All semantic graft strategies evaluated."

semantic-region-candidates:
	@echo "Enumerating semantic replacement regions"
	@PYTHONDONTWRITEBYTECODE=1 $(Z3_PYTHON) scripts/run_semantic_region_replacement.py

semantic-region-closure: semantic-region-candidates
	@echo "Closed-region validation complete."

semantic-compositional-cegis: semantic-region-closure
	@echo "Compositional CEGIS results are in results/semantic_region_replacement/"

semantic-module-proofs: semantic-compositional-cegis
	@echo "Semantic module proof results are in compositional_formal_results.csv"

semantic-module-synthesis: semantic-module-proofs
	@echo "Replacement module synthesis/emission results are in replacement_module_synthesis.csv"

semantic-region-replace: semantic-module-synthesis
	@echo "Graph-level region replacement attempts are in replacement_attempts.csv"

semantic-replacement-cec: semantic-region-replace
	@echo "Global CEC results are in implementation_global_cec.csv"

semantic-boundary-restore: semantic-replacement-cec
	@echo "Boundary restoration results are in boundary_restoration_results.csv"

semantic-replacement-ablation: semantic-boundary-restore
	@echo "Replacement ablation results are in replacement_strategy_ablation.csv"

semantic-replacement-plots: semantic-replacement-ablation
	@echo "Generating semantic replacement plots"
	@PYTHONDONTWRITEBYTECODE=1 $(PYTHON) scripts/semantic_region_replacement_plots.py

check-semantic-replacement-results:
	@echo "Checking semantic region replacement results"
	@PYTHONDONTWRITEBYTECODE=1 $(PYTHON) scripts/check_semantic_replacement_results.py

semantic-region-replacement-all: semantic-region-candidates semantic-region-closure semantic-compositional-cegis semantic-module-proofs semantic-module-synthesis semantic-region-replace semantic-replacement-cec semantic-boundary-restore semantic-replacement-ablation semantic-replacement-plots check-semantic-replacement-results
	@echo "Semantic region replacement pipeline complete."

joint-region-interface:
	@echo "Running joint region/interface discovery"
	@PYTHONDONTWRITEBYTECODE=1 $(Z3_PYTHON) scripts/run_joint_region_interface_discovery.py --mode all

joint-region-interface-controlled:
	@echo "Running controlled joint region/interface discovery"
	@PYTHONDONTWRITEBYTECODE=1 $(Z3_PYTHON) scripts/run_joint_region_interface_discovery.py --mode controlled --max-real-seeds 0

joint-region-interface-real:
	@echo "Revisiting real isolated-anchor failures with bounded joint search"
	@PYTHONDONTWRITEBYTECODE=1 $(Z3_PYTHON) scripts/run_joint_region_interface_discovery.py --mode real --max-real-seeds 46

joint-region-interface-heldout:
	@echo "Writing deterministic dev/heldout joint-discovery split"
	@PYTHONDONTWRITEBYTECODE=1 $(Z3_PYTHON) scripts/run_joint_region_interface_discovery.py --mode heldout --max-real-seeds 46

joint-region-interface-ablations: joint-region-interface
	@echo "Joint region/interface ablations are in results/joint_region_interface_discovery/ablations.csv"

joint-region-interface-plots: joint-region-interface
	@echo "Generating joint region/interface plots"
	@PYTHONDONTWRITEBYTECODE=1 $(PYTHON) scripts/joint_region_interface_plots.py

check-joint-region-interface-results:
	@echo "Checking joint region/interface discovery results"
	@PYTHONDONTWRITEBYTECODE=1 $(Z3_PYTHON) scripts/check_joint_region_interface_results.py

joint-region-interface-all: joint-region-interface joint-region-interface-ablations joint-region-interface-plots check-joint-region-interface-results
	@echo "Joint region/interface discovery pipeline complete."

semantic-functional-refactoring-controlled:
	@echo "Running controlled semantic functional refactoring"
	@PYTHONDONTWRITEBYTECODE=1 $(Z3_PYTHON) scripts/run_semantic_functional_refactoring.py --mode controlled

semantic-functional-refactoring-development:
	@echo "Running development semantic functional refactoring accounting"
	@PYTHONDONTWRITEBYTECODE=1 $(Z3_PYTHON) scripts/run_semantic_functional_refactoring.py --mode development

semantic-functional-refactoring-heldout:
	@echo "Running held-out semantic functional refactoring accounting"
	@PYTHONDONTWRITEBYTECODE=1 $(Z3_PYTHON) scripts/run_semantic_functional_refactoring.py --mode heldout

semantic-functional-refactoring-ablations:
	@echo "Running semantic functional refactoring ablations"
	@PYTHONDONTWRITEBYTECODE=1 $(Z3_PYTHON) scripts/run_semantic_functional_refactoring.py --mode all

semantic-functional-refactoring-plots: semantic-functional-refactoring-ablations
	@echo "Generating semantic functional refactoring plots"
	@PYTHONDONTWRITEBYTECODE=1 $(PYTHON) scripts/semantic_functional_refactoring_plots.py

check-semantic-functional-refactoring-results:
	@echo "Checking semantic functional refactoring results"
	@PYTHONDONTWRITEBYTECODE=1 $(Z3_PYTHON) scripts/check_semantic_functional_refactoring_results.py

semantic-functional-refactoring-all: semantic-functional-refactoring-ablations semantic-functional-refactoring-plots check-semantic-functional-refactoring-results
	@echo "Semantic functional refactoring pipeline complete."

semantic-recoverability-benchmarks:
	@echo "Generating semantic recoverability benchmark manifest"
	@PYTHONDONTWRITEBYTECODE=1 $(Z3_PYTHON) scripts/run_semantic_recoverability_frontier.py --mode controlled

semantic-recoverability-trajectories:
	@echo "Generating semantic recoverability synthesis trajectories"
	@PYTHONDONTWRITEBYTECODE=1 $(Z3_PYTHON) scripts/run_semantic_recoverability_frontier.py --mode all

semantic-recoverability-controlled:
	@echo "Running controlled semantic recoverability frontier"
	@PYTHONDONTWRITEBYTECODE=1 $(Z3_PYTHON) scripts/run_semantic_recoverability_frontier.py --mode controlled

semantic-recoverability-development:
	@echo "Running development semantic recoverability frontier"
	@PYTHONDONTWRITEBYTECODE=1 $(Z3_PYTHON) scripts/run_semantic_recoverability_frontier.py --mode development

semantic-recoverability-heldout:
	@echo "Running held-out semantic recoverability frontier"
	@PYTHONDONTWRITEBYTECODE=1 $(Z3_PYTHON) scripts/run_semantic_recoverability_frontier.py --mode heldout

semantic-recoverability-oracle:
	@echo "Running oracle diagnostic semantic recoverability frontier"
	@PYTHONDONTWRITEBYTECODE=1 $(Z3_PYTHON) scripts/run_semantic_recoverability_frontier.py --mode oracle

semantic-recoverability-pass-ablations:
	@echo "Running semantic recoverability pass ablations"
	@PYTHONDONTWRITEBYTECODE=1 $(Z3_PYTHON) scripts/run_semantic_recoverability_frontier.py --mode pass-ablations

semantic-recoverability-durability:
	@echo "Running semantic recoverability durability diagnostics"
	@PYTHONDONTWRITEBYTECODE=1 $(Z3_PYTHON) scripts/run_semantic_recoverability_frontier.py --mode durability

semantic-recoverability-plots: semantic-recoverability-trajectories
	@echo "Generating semantic recoverability frontier plots"
	@PYTHONDONTWRITEBYTECODE=1 $(PYTHON) scripts/semantic_recoverability_plots.py

check-semantic-recoverability-results:
	@echo "Checking semantic recoverability frontier results"
	@PYTHONDONTWRITEBYTECODE=1 $(Z3_PYTHON) scripts/check_semantic_recoverability_results.py

semantic-recoverability-all: semantic-recoverability-trajectories semantic-recoverability-plots check-semantic-recoverability-results
	@echo "Semantic recoverability frontier pipeline complete."

active-source-counterparts-controlled:
	@echo "Running controlled active source-counterpart refactoring"
	@PYTHONDONTWRITEBYTECODE=1 $(Z3_PYTHON) scripts/run_active_source_counterpart_refactoring.py --mode controlled

active-source-counterparts-development:
	@echo "Revisiting development active source-counterpart targets"
	@PYTHONDONTWRITEBYTECODE=1 $(Z3_PYTHON) scripts/run_active_source_counterpart_refactoring.py --mode development

active-source-counterparts-heldout:
	@echo "Running held-out active source-counterpart accounting"
	@PYTHONDONTWRITEBYTECODE=1 $(Z3_PYTHON) scripts/run_active_source_counterpart_refactoring.py --mode heldout

active-source-counterparts-durability:
	@echo "Running active source-counterpart durability strategies"
	@PYTHONDONTWRITEBYTECODE=1 $(Z3_PYTHON) scripts/run_active_source_counterpart_refactoring.py --mode durability

active-source-counterparts-ablations:
	@echo "Running active source-counterpart baselines and ablations"
	@PYTHONDONTWRITEBYTECODE=1 $(Z3_PYTHON) scripts/run_active_source_counterpart_refactoring.py --mode all

active-source-counterparts-plots: active-source-counterparts-ablations
	@echo "Generating active source-counterpart plots"
	@PYTHONDONTWRITEBYTECODE=1 $(PYTHON) scripts/active_source_counterpart_plots.py

check-active-source-counterpart-results:
	@echo "Checking active source-counterpart results"
	@PYTHONDONTWRITEBYTECODE=1 $(Z3_PYTHON) scripts/check_active_source_counterpart_results.py

active-source-counterparts-all: active-source-counterparts-ablations active-source-counterparts-plots check-active-source-counterpart-results
	@echo "Active source-counterpart refactoring pipeline complete."

cross-netlist-transplant-controlled:
	@echo "Running controlled cross-netlist cut transplantation"
	@PYTHONDONTWRITEBYTECODE=1 $(Z3_PYTHON) scripts/run_cross_netlist_cut_transplantation.py --mode controlled

cross-netlist-transplant-development:
	@echo "Revisiting real cross-netlist cut transplantation targets"
	@PYTHONDONTWRITEBYTECODE=1 $(Z3_PYTHON) scripts/run_cross_netlist_cut_transplantation.py --mode development

cross-netlist-transplant-heldout:
	@echo "Running held-out cross-netlist cut transplantation accounting"
	@PYTHONDONTWRITEBYTECODE=1 $(Z3_PYTHON) scripts/run_cross_netlist_cut_transplantation.py --mode heldout

cross-netlist-transplant-oracle:
	@echo "Running cross-netlist oracle-ladder diagnostics"
	@PYTHONDONTWRITEBYTECODE=1 $(Z3_PYTHON) scripts/run_cross_netlist_cut_transplantation.py --mode oracle

cross-netlist-transplant-durability:
	@echo "Running cross-netlist transplant durability strategies"
	@PYTHONDONTWRITEBYTECODE=1 $(Z3_PYTHON) scripts/run_cross_netlist_cut_transplantation.py --mode durability

cross-netlist-transplant-ablations:
	@echo "Running cross-netlist transplant baselines and ablations"
	@PYTHONDONTWRITEBYTECODE=1 $(Z3_PYTHON) scripts/run_cross_netlist_cut_transplantation.py --mode all

cross-netlist-transplant-plots: cross-netlist-transplant-ablations
	@echo "Generating cross-netlist transplant plots"
	@PYTHONDONTWRITEBYTECODE=1 $(PYTHON) scripts/cross_netlist_transplant_plots.py

check-cross-netlist-transplant-results:
	@echo "Checking cross-netlist transplant results"
	@PYTHONDONTWRITEBYTECODE=1 $(Z3_PYTHON) scripts/check_cross_netlist_transplant_results.py

cross-netlist-transplant-all: cross-netlist-transplant-ablations cross-netlist-transplant-plots check-cross-netlist-transplant-results
	@echo "Cross-netlist cut transplantation pipeline complete."

semantic-graft-plots: semantic-graft-ablation
	@echo "Generating blind CEGIS and semantic graft plots"
	@PYTHONDONTWRITEBYTECODE=1 $(PYTHON) scripts/blind_semantic_plots.py

check-blind-semantic-results:
	@echo "Checking blind semantic CEGIS outputs"
	@PYTHONDONTWRITEBYTECODE=1 $(PYTHON) scripts/check_blind_semantic_results.py

check-semantic-graft-results:
	@echo "Checking semantic graft outputs"
	@PYTHONDONTWRITEBYTECODE=1 $(PYTHON) scripts/check_semantic_graft_results.py

blind-semantic-cegis-all: blind-semantic-audit blind-semantic-buses semantic-parametric-candidates semantic-cegis semantic-smt-proofs semantic-cegis-evaluation check-blind-semantic-results
	@echo "Blind semantic CEGIS pipeline complete."

semantic-grafting-all: blind-semantic-cegis-all semantic-graft-targets semantic-graft-build semantic-graft-proofs semantic-graft-boundary-recovery semantic-graft-ablation semantic-graft-plots check-semantic-graft-results
	@echo "Proof-carrying semantic grafting pipeline complete."

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

materialization-targets: extended-boundary-all
	@echo "Selecting unmatched optimized-side targets for anchored-cut materialization"
	@PYTHONDONTWRITEBYTECODE=1 $(PYTHON) scripts/select_materialization_targets.py

anchored-cuts: materialization-targets
	@echo "Enumerating globally anchored optimized-side cuts"
	@PYTHONDONTWRITEBYTECODE=1 $(PYTHON) scripts/enumerate_anchored_cuts.py

anchored-cut-functions: anchored-cuts
	@echo "Extracting exact target functions over anchored cuts"
	@PYTHONDONTWRITEBYTECODE=1 $(PYTHON) scripts/extract_anchored_cut_functions.py

materialized-wires: anchored-cut-functions
	@echo "Materializing additive original-side redundant wires"
	@PYTHONDONTWRITEBYTECODE=1 $(PYTHON) scripts/materialize_original_wires.py

materialized-anchor-proofs: materialized-wires
	@echo "Formally proving materialized-wire anchors"
	@PYTHONDONTWRITEBYTECODE=1 $(PYTHON) scripts/prove_materialized_anchors.py

materialized-boundary-recovery: materialized-anchor-proofs
	@echo "Rerunning boundary recovery with materialized anchors"
	@PYTHONDONTWRITEBYTECODE=1 $(PYTHON) scripts/run_materialized_boundary_recovery.py

materialized-ablation: materialized-boundary-recovery
	@echo "Comparing materialization ablations and utility"
	@PYTHONDONTWRITEBYTECODE=1 $(PYTHON) scripts/compare_materialization_ablations.py

materialized-plots: materialized-ablation
	@echo "Generating materialized correspondence plots"
	@PYTHONDONTWRITEBYTECODE=1 $(PYTHON) scripts/materialized_correspondence_plots.py

check-materialized-results:
	@echo "Checking materialized correspondence outputs"
	@PYTHONDONTWRITEBYTECODE=1 $(PYTHON) scripts/check_materialized_correspondence_results.py

materialized-correspondence-all: extended-boundary-all materialization-targets anchored-cuts anchored-cut-functions materialized-wires materialized-anchor-proofs materialized-boundary-recovery materialized-ablation materialized-plots check-materialized-results
	@echo "Anchored-cut materialized correspondence pipeline complete."

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
