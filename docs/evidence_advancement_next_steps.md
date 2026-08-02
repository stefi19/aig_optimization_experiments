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
| Source-blind source-side counterpart inference | 0 / 56 | Bounded exact-node placement now attempts all 20 semantic-only rows; no row has an exact source counterpart node under the support bound, so no graph-active CEC-backed recovery is promoted. |
| Graph-active rewrites from compact exact generated interfaces | 22 / 48 | 31 compact exact interfaces emit valid rewrite artifacts; bounded fanout-frontier expansion promotes 4 additional rows, while 9 emitted artifacts remain identical-driver non-active rewrites. |
| Bounded CEGIS grammar completeness | 4 / 12 | Only `sign_extend` and `zero_extend` are complete for attempted blind and oracle-bus rows. |
| Pinned redistributable RTL corpus | 3 / 3 | Three CC0 Verilog modules are committed with source-location metadata; local Yosys lowering is recorded as `tool_missing`. |
| ODC-aware placement | 0 / 10 | Ten formal contextual ODC anchors exist, but none is graph-active or globally CEC-backed. |
| Machine-checkable locality proof objects | 57 / 57 | JSON proof objects mirror exact-minimum locality certificate rows. |

## Evidence Rules

- Semantic counterpart evidence is not graph-active recovery.
- Compact exact locality is not graph rewrite emission.
- A bounded grammar is marked complete only for an operator/mode group where all
  attempted rows are recovered.
- A pinned RTL source is not a lowered netlist unless the Yosys command succeeds
  and the lowered BLIF exists.
- ODC validity is contextual; graph-active ODC placement still needs an emitted
  graph edit and global CEC.
- Locality proof objects currently mirror replayable CSV evidence. They are
  machine-checkable metadata objects, not independently checkable UNSAT proof
  traces.

## Next Promotions

The next publishable improvements are to move rows across these exact gates:

- extend source-blind placement beyond exact source-node matching to bounded
  source windows or synthesized source-side expressions, then emit
  graph-active CEC-backed rewrites only when the same gates pass;
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
