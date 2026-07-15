# Boundary-Recovery Failure Diagnosis Summary

This diagnosis measures why the current formal boundary-recovery prototype succeeds or fails. Region enclosure is not reported as direct node equivalence.

## Identity

- Identity successes / total: 1 / 6
- Zero-extension identity cases: 1
- Identity failures: 5

## Existing Seed Suite

- Successes / total: 8 / 48
- Failures by stage:

| failure_stage | count |
| --- | --- |
| extract_region | 14 |
| load_inputs | 16 |
| validate_cuts | 10 |

- Failures by reason:

| failure_reason | count |
| --- | --- |
| incomplete_ebo_cut | 10 |
| missing_spec_circuit | 16 |
| region_not_enclosed | 10 |
| whole_design_expansion | 4 |

## Anchor Relevance

- Cases where `formal_all` adds global anchors: 0
- Cases where `formal_all` adds relevant anchors: 0
- Cases where `formal_all` adds usable frontier anchors: 0
- Cases where a SAT/CEC anchor is actually selected: 0

## Recovery Progression

| benchmark | coi_name | anchor_mode | first_nonzero_extension_flow | first_recovery_failure_flow | last_successful_flow | maximum_successful_flow |
| --- | --- | --- | --- | --- | --- | --- |
| external_iscas85_c2670 | critical_path_seed_region | formal_all |  | identity |  |  |
| external_iscas85_c432 | manual_small_structural_region | formal_all |  | identity |  |  |
| generated_adder_4 | adder_bit1_carry_sum_region | formal_all |  | identity |  |  |
| generated_multiplier_2 | multiplier_middle_products | formal_all |  | identity |  |  |
| generated_mux_tree_4 | mux_tree_root | formal_all | resyn2 | resyn2 | dc2 | dc2 |
| generated_mux_tree_8 | mux_tree_upper_root | formal_all | resyn2 | identity | compress2rs | compress2rs |

## COI Validity

- Valid COI audit rows: 4
- Invalid COI audit rows: 20

## Critical Path

- Seed COI unresolved critical-path overlap count: 0
- Unresolved path nodes enclosed by valid recovered regions: 0
- Generated path COI rows: 36

## Anchor Selection

- Failed cases where an alternative formal anchor enables recovery: 0
- Alternative-anchor diagnostics are local and bounded; this milestone does not run a combinatorial search.

## Decision Gate

Recommended next milestone from these measurements: **fix recovery semantics or COI specifications**.
