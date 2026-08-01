# Claims to Tables

| Paper claim | Primary table or figure | Evidence class | Checker |
|---|---|---|---|
| Aggressive logic synthesis preserves whole-design equivalence while eroding direct internal correspondences. | `results/sat_validation_layers_summary.csv`; `results/summary_metrics.csv` | structural and ABC CEC diagnostic | `python scripts/check_results_freshness.py` |
| Controlled source-side counterparts can be graph-active and CEC-backed. | `results/research_wow/recoverability_frontier.csv` | controlled generated BLIF | `python scripts/check_active_source_counterpart_results.py` |
| Cross-netlist transplantation succeeds on controlled positives but not historical diagnostic rows. | `results/research_wow/recoverability_frontier.csv` | controlled generated BLIF; historical diagnostic | `python scripts/check_cross_netlist_transplant_results.py` |
| Blind CEGIS has both verified regions and replayable counterexample-refinement failures. | `results/blind_semantic_cegis/blind_semantic_recovery_summary.csv`; `results/research_wow/demo_trace.csv` | blind generated BLIF | `python scripts/check_blind_semantic_results.py` |
| Necessity-first generated targets separate exact interface existence from graph rewrite recovery. | `results/necessity_first_target_discovery/formal_locality_results.csv`; `results/necessity_first_target_discovery/graph_rewrites.csv` | generated research benchmark | `python scripts/check_necessity_first_target_results.py` |
| Historical null results are explained by provenance and target-necessity audits, not by a 56-row eligible graph-rewrite denominator. | `results/provenance_eligibility_audit/provenance_reconstruction.csv`; `results/research_wow/failure_taxonomy.csv` | historical diagnostic | `python scripts/check_provenance_eligibility_results.py` |
| The artifact's headline figure is generated from committed evidence and does not merge blind, oracle, controlled, generated, and historical denominators. | `paper/figures/recoverability_frontier.png`; `results/research_wow/recoverability_frontier.csv` | artifact-derived summary | `python scripts/check_research_wow.py` |
