# Claims to Tables

| Paper claim | Primary table | Checker |
|---|---|---|
| Controlled source-side counterparts can be graph-active and CEC-backed. | `results/research_wow/recoverability_frontier.csv` | `python scripts/check_research_wow.py` |
| Cross-netlist transplantation succeeds on controlled positives but not historical diagnostic rows. | `results/research_wow/recoverability_frontier.csv` | `python scripts/check_cross_netlist_transplant_results.py` |
| Necessity-first generated targets separate exact interface existence from graph rewrite recovery. | `results/research_wow/failure_taxonomy.csv` | `python scripts/check_necessity_first_target_results.py` |
| Blind CEGIS has both verified regions and replayable counterexample-refinement failures. | `results/research_wow/demo_trace.csv` | `python scripts/check_blind_semantic_results.py` |
| Historical null results are explained by provenance and target-necessity audits. | `results/research_wow/failure_taxonomy.csv` | `python scripts/check_provenance_eligibility_results.py` |
