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
| Source-blind source-side counterpart inference | 14 / 56 | Exact-node source-blind placement remains 0/56, but bounded window/expression placement promotes 14/56 with emitted graph-active rewrites and both CEC scopes. The checker now replays each non-empty expression witness against the source and optimized BLIF truth vectors, selected support, target hash, and source-graph-only policy. The remaining prior semantic rows are 3 identical-driver no-ops and 3 no-expression-under-bound failures. |
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

- extend source-blind placement beyond the current unary/binary/mux expression
  language to larger source windows, while preserving emitted-artifact,
  graph-activity, CEC, and leakage-audit gates;
- extend the rewrite language beyond radius-1 fanout-frontier replacement so
  remaining identical-driver artifacts can become constructive graph-active
  boundaries when supported;
- extend blind CEGIS templates and add completeness proofs for selected
  operator families beyond the attempted `sign_extend` and `zero_extend` rows;
- install and pin Yosys so the CC0 RTL corpus lowers to BLIF with source
  metadata;
- place ODC-aware candidates as graph-active edits and discharge global CEC;
- replace mirrored locality proof objects with solver-native or replayable proof
  certificates.
