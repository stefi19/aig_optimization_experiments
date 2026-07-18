# Cross-Netlist Cut Transplantation Summary

- Controlled cases: 17
- Controlled accepted transplants: 12
- Real previous failures revisited: 56
- Real new boundaries: 0
- Oracle diagnostic rows: 392

Controlled and real results are intentionally separate.  A controlled transplant clones an optimized RI into a source copy, connects it through exact Ein/Eout adapters, and requires local proof plus both ABC CEC scopes.

## Failure Taxonomy
- controlled / global_cec / global_cec_failed: 1
- controlled / input_adapter / no_exact_input_adapter: 1
- controlled / locality / whole_design_transplant_diagnostic: 1
- controlled / output_adapter / no_exact_output_adapter: 1
- controlled / target_influence / target_does_not_influence_bi: 1
- real / input_interface_sufficiency / no_globally_anchored_cut: 36
- real / output_interface_sufficiency / no_relevant_source_consumer_window_under_bounds: 20
