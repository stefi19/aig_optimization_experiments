# Evidence Advancement Next Steps

This layer implements the next research step as evidence accounting, not count
inflation. Run:

```bash
make evidence-advancement
make check-evidence-advancement
```

The generator writes `results/evidence_advancement/`; the checker verifies that
rows move to stronger evidence levels only when the corresponding proof object,
graph artifact, tool metadata, or CEC obligation is present.

## Current Checked State

| Direction | Promoted rows | Interpretation |
|---|---:|---|
| Source-blind source-side counterpart inference | 14 / 56 | Exact-node source-blind placement remains 0/56, but bounded window/expression placement promotes 14/56 with emitted graph-active rewrites and both CEC scopes. The checker now replays each non-empty expression witness against the source and optimized BLIF truth vectors, selected support, target hash, and source-graph-only policy, including nested negated source literals. The remaining prior semantic rows are 6 identical-driver no-ops: three direct no-ops plus three rows whose former no-expression failures now replay as `nor(data,not(selector))` but do not pass the graph-active gate. |
| Proof-carrying virtual anchor synthesis | 20 / 56 | The generator enumerates a bounded latent source cut bank, decomposes replayable optimized targets against source cuts and PI truth-table anchors, emits JSON proof objects, and validates graph-active replacement artifacts with both CEC scopes. The 6 former identical-driver rows are recovered by a constructive expanded-support objective; the remaining 36 rows are blocked by missing materialized source/optimized replay pairs rather than by anchor search. |
| Constructive virtual-anchor rewrites | 20 / 56 | Multi-objective rewrite selection requires source/PI derivation, exact support accounting, graph activity, and global CEC. It uses minimal exact support when graph-active, and expands support by one irrelevant PI only when needed to turn semantic equality into a non-identical graph edit. |
| Graph-active rewrites from compact exact generated interfaces | 22 / 48 | 31 compact exact interfaces emit valid rewrite artifacts; bounded fanout-frontier expansion promotes 4 additional rows, while 9 emitted artifacts remain identical-driver non-active rewrites. The evidence checker cross-links each row to necessity-first provenance, graph-rewrite, boundary, and CEC-scope tables, and revalidates emitted BLIF artifacts. |
| Bounded CEGIS grammar completeness | 4 / 12 | Only `sign_extend` and `zero_extend` are complete for attempted blind and oracle-bus rows. The checker recomputes grouped recovery counts, formal-SMT proof row counts, and proof hashes from the Z3 CEGIS source tables. |
| Pinned redistributable RTL corpus | 3 / 3 | Three CC0 Verilog modules are committed with source-location metadata; local Yosys lowering is recorded as `tool_missing`. The checker verifies the expected design set, SPDX/module shape, source hashes, source-location metadata, and Yosys/lowered-BLIF provenance boundaries. |
| ODC-aware placement | 0 / 10 | Ten formal contextual ODC anchors exist, but none is graph-active or globally CEC-backed. The checker ties each accounting row back to proven-anchor and selected boundary-case source tables, preserving the distinction between contextual boundary candidates and emitted global graph rewrites. |
| Machine-checkable locality proof objects | 57 / 57 | JSON proof objects mirror exact-minimum locality certificate rows. The checker regenerates the expected proof-object id set from the source locality tables, rejects missing or extra objects, and verifies each object's source family, table, row hash, predicate, interface, and bounds. |

## Evidence Rules

- Semantic counterpart evidence is not graph-active recovery.
- Source-blind window/expression promotion requires a replayable expression
  witness over source graph signals only, matching the optimized target truth
  vector under the declared bounded support.
- Proof-carrying virtual-anchor promotion requires a generated certificate whose
  source row, support, target truth hash, source/PI-only decomposition, emitted
  replacement artifact, graph activity, and both CEC scopes replay under the
  checker.
- Compact exact locality is not graph rewrite emission.
- Compact-interface graph-rewrite promotion must remain consistent with the
  necessity-first provenance, graph-rewrite, boundary-recovery, and global-CEC
  source tables.
- A bounded grammar is marked complete only for an operator/mode group where all
  attempted rows are recovered, and those recovered rows are backed by accepted
  Z3 `formal_smt` proof rows.
- A pinned RTL source is not a lowered netlist unless the Yosys command succeeds
  and the lowered BLIF exists. The pinned-corpus claim is limited to the three
  expected CC0 RTL modules with matching source metadata.
- ODC validity is contextual; graph-active ODC placement still needs an emitted
  graph edit and global CEC. Contextual boundary successes remain blocked at
  `boundary_candidate_requires_graph_cec`.
- Locality proof objects currently mirror replayable CSV evidence. They are
  machine-checkable metadata objects, not independently checkable UNSAT proof
  traces. The checked scope is complete object accounting over eligible
  exact-minimum source rows.

## Next Promotions

The next publishable improvements are to move rows across these exact gates:

- materialize replayable source/optimized BLIF pairs for the 36 fresh utility
  targets currently blocked at `unsupported_no_replay_artifacts`;
- lift proof-carrying anchors from PI truth-table fallback into reusable
  source-cut decompositions with smaller certificates and better durability;
- extend blind CEGIS templates and add completeness proofs for selected
  operator families beyond the attempted `sign_extend` and `zero_extend` rows;
- install and pin Yosys so the CC0 RTL corpus lowers to BLIF with source
  metadata;
- place ODC-aware candidates as graph-active edits and discharge global CEC;
- replace mirrored locality proof objects with solver-native or replayable proof
  certificates.
