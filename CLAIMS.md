# Claims Ledger

This ledger maps headline claims to committed evidence files and checker
commands. Counts from controlled, generated BLIF, standard netlist, external
RTL, blind, and oracle rows must not be merged unless a table explicitly does
so.

## Headline Claims

| Claim | Evidence | Checker |
|---|---|---|
| Exact internal correspondences often survive mild synthesis but degrade under aggressive flows. | `results/summary_metrics.csv`, `results/top_candidates.csv` | `python -m scripts.validation.check_results_freshness` |
| Blind CEGIS contains replayable counterexample refinement before accepted proofs. | `results/blind_semantic_cegis/cegis_iterations.csv`, `results/blind_semantic_cegis/formal_proofs.csv` | `python -m scripts.validation.check_blind_semantic_results` |
| Controlled active source-side counterpart construction accepts 10 graph-active CEC-backed cases. | `results/active_source_counterpart_refactoring/controlled_results.csv` | `python -m scripts.validation.check_active_source_counterpart_results` |
| Controlled accepted graph-active counterparts: 10. | `results/active_source_counterpart_refactoring/controlled_results.csv` | `python -m scripts.validation.check_artifact_claims` |
| Cross-netlist cut transplantation accepts 12 controlled positive transplants and rejects negative controls. | `results/cross_netlist_cut_transplantation/controlled_results.csv` | `python -m scripts.validation.check_cross_netlist_transplant_results` |
| Controlled accepted transplants: 12. | `results/cross_netlist_cut_transplantation/controlled_results.csv` | `python -m scripts.validation.check_artifact_claims` |
| The 56 historical transplant rows are diagnostic rows, not eligible graph-rewrite attempts. | `results/provenance_eligibility_audit/historical_denominator_audit.csv` | `python -m scripts.validation.check_provenance_eligibility_results` |
| corrected historical eligible transplantation denominator: 0. | `results/necessity_first_target_discovery/corrected_scientific_claims.csv` | `python -m scripts.validation.check_artifact_claims` |
| 48 fresh provenance-complete generated-research targets pass the necessity-first filter. | `results/necessity_first_target_discovery/eligible_target_manifest.csv` | `python -m scripts.validation.check_necessity_first_target_results` |
| 31/48 have compact exact input interfaces. | `results/necessity_first_target_discovery/formal_locality_results.csv` | `python -m scripts.validation.check_artifact_claims` |
| Necessity-first compact interfaces emit 31/48 valid rewrite artifacts; bounded fanout-frontier expansion promotes 22/48 graph-active CEC-backed new boundaries. | `results/necessity_first_target_discovery/rewrite_function_synthesis.csv`, `results/necessity_first_target_discovery/rewrite_frontier_expansion.csv`, `results/necessity_first_target_discovery/boundary_recovery.csv` | `python -m scripts.validation.check_necessity_first_target_results` |
| The main paper figure keeps controlled, blind, generated, formal-diagnostic, and historical denominators separate. | `results/research_wow/recoverability_frontier.csv`, `results/research_wow/recoverability_frontier.png` | `python -m scripts.validation.check_research_wow` |
| The failure taxonomy explains null results with auditable blocker classes rather than counting them as failed recoveries. | `results/research_wow/failure_taxonomy.csv` | `python -m scripts.validation.check_research_wow` |
| The demo report contains both a successful graph-active proof path and a blind CEGIS counterexample-refinement trace. | `results/research_wow/demo_trace.csv`, `results/research_wow/demo_report.md` | `python -m scripts.validation.check_research_wow` |
| Evidence-advancement promoted rows: source-blind graph-active 14/56; compact interface new boundaries 22/48; bounded grammar completeness 4/12; pinned RTL corpus 3/3; ODC graph-active placement 0/10; locality proof objects 57/57. | `results/evidence_advancement/evidence_advancement_summary.csv`, `results/evidence_advancement/source_blind_counterpart_placement.csv`, `results/evidence_advancement/source_blind_window_expression_placement.csv`, `results/evidence_advancement/locality_proof_objects.csv` | `python -m scripts.validation.check_evidence_advancement` |
| Proof-carrying virtual-anchor synthesis promotes 56/56 source-blind rows after repairing the 36 fresh utility rows into checkpoint-derived replay pairs; 6 former identical-driver cases still require constructive expanded-support graph edits. | `results/evidence_advancement/materialized_replay_pairs.csv`, `results/evidence_advancement/latent_source_cut_bank.csv`, `results/evidence_advancement/optimized_target_decompositions.csv`, `results/evidence_advancement/virtual_anchor_certificates.csv`, `results/evidence_advancement/constructive_rewrite_selection.csv` | `python -m scripts.validation.check_evidence_advancement` |

## Evidence Rules

- Formal equivalence claims require a successful proof row or ABC CEC row.
- Sampled approximate distances remain sampled evidence and must not be called
  formal.
- Oracle diagnostics are diagnostic only and must not be counted as blind
  recoveries.
- Semantic-only counterparts, compact exact interfaces, contextual ODC anchors,
  and pinned RTL sources are separate evidence levels. They are not graph-active
  recovery unless a graph artifact and required global CEC evidence exist.
- `--allow-no-abc` validates schemas and rejection behavior only; accepted
  graph rewrites, transplants, and restored boundaries still require
  `abc_available=true` and equivalent CEC evidence.

## Related Work Positioning

This artifact sits between classical equivalence checking and debug/source
mapping. It uses ideas adjacent to SAT sweeping/FRAIG, internal signal
correspondence, observability don't-care reasoning, formal approximate
matching, and source-level back-mapping. The current contribution is the
evidence discipline around what can be proved, what is only diagnostic, and
where bounded source-blind recovery fails.

## Formal approximate-correspondence extension (22 October 2026)

The old approximate-distance CSVs are preserved historical measurements. Their
shared evaluator ignored output-0 BLIF covers. Treat the old quantitative
approximate-distance, fingerprint-derived, and approximate-path conclusions as
requiring a separately versioned full regeneration; the new audit replays a
fixed 32-row subset only.

| New supported claim | Evidence under `results/formal_approximate_correspondence/` | Checker |
|---|---|---|
| All 32 selected legacy values reproduce; 16 selected verified rows correct to zero and pass fresh CEC. | `audit/replay.csv`, `audit/*_cec.log` | `make check-approx-correspondence` |
| The 48 controlled algebraic-rewrite cases contain 472 candidate rows; low distance does not establish lineage. | `cases.csv`, `candidates.csv`, `ranking_queries.csv`, `ranking_summary.csv` | Independent scalar oracle and exact-status/counterexample replay |
| Held-out structural P@1 is 10/24; hybrid/contextual is 6/24; global is 4/24. | `ranking_summary.csv`, `paired_comparisons.csv` | Frozen same-pool comparison; designated algebraic lineage independent of score |
| The 26 path diagnostics include one context-only exact candidate and zero additional nonzero near matches within 5%. | `critical_path_diagnostics.csv` | Exact bounded PI enumeration; no ancestry precision claim |
| Guided ordering reaches one accepted target per flow split at budget one; full-budget accepted sets are unchanged. | `reconstruction.csv`, `reconstruction/*.blif` | Identical pools and budgets, exact equality, graph activity, both ABC CEC scopes |
| The two accepted flow instances share one distinct graph artifact; no full-budget new boundary or runtime advantage is claimed. | `reconstruction.csv`, artifact SHA-256 fields | Independent expression/graph replay and fresh CEC per distinct graph |

The new rows are not added to any previous source-side counterpart, transplant,
necessity-first boundary, or virtual-anchor denominator. Full methodology and
limitations: `docs/approximate_computing_correspondence_research.md`.
