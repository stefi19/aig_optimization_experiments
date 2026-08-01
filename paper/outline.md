# Paper Outline

## Working Title

Recoverability Frontiers for Internal Correspondence After Logic Synthesis.

## Thesis

Internal correspondence after AIG optimization is not a single recovery problem. It is a hierarchy of evidence. Structural similarity, semantic region recognition, exact locality certificates, graph-active rewrites, and global CEC-backed transformations form distinct levels, and the current artifact shows where each level succeeds or fails under controlled, blind, generated, and historical diagnostic denominators.

The cross-netlist ablation refines the thesis: the frontier is parameterized by the admissible interface language. In the controlled experiment, direct adapters recover 9/17 new boundaries, while relational-interface-enabled transplantation recovers 12/17, showing that representation of the boundary can change constructive recoverability.

## Paper Structure

1. Abstract.
2. Introduction and contributions.
3. Background and related work.
4. Problem formulation and evidence model.
5. Framework and algorithms.
6. Experimental methodology.
7. Results by research question.
8. Case studies.
9. Discussion.
10. Threats to validity.
11. Future work.
12. Conclusion.

## Problem

Recovering internal correspondences after logic synthesis is useful for debugging, source mapping, and proof-carrying transformations, but aggressive optimization destroys simple name and structural evidence.

## Threat Model

All headline recovery claims must distinguish controlled generated BLIF, blind generated BLIF, standard netlist diagnostics, oracle diagnostics, historical ineligible rows, pinned RTL-source metadata, and future lowered RTL correspondence work.

## Method

1. Recover candidate internal semantic regions.
2. Refine candidates with counterexamples or exact certificates.
3. Construct source-side counterparts or cross-netlist transplants only when local evidence is strong enough.
4. Require graph activity and global CEC before counting recovered boundaries.

## Evaluation

Use `results/research_wow/recoverability_frontier.csv` as the main table and `results/research_wow/recoverability_frontier.png` as the main figure. Use the supporting figures in `paper/figures/` to show the problem setup, evidence hierarchy, methodology pipeline, failure taxonomy, and case-study trace.

Use `paper/figures/interface_ablation.png` as the targeted cross-netlist ablation figure.

Use `results/evidence_advancement/evidence_advancement_summary.csv` to describe next-step promotions without changing headline recovery counts.

## Failure Taxonomy

Use `results/research_wow/failure_taxonomy.csv` to explain why null results are meaningful: missing provenance, target irrelevance, non-compact interfaces, absent rewrite artifacts, bounded blind CEGIS exhaustion, and formal locality barriers.

## Ablations and Baselines

Use `results/research_wow/ablation_summary.csv` and `results/research_wow/baseline_summary.csv` to show which components move counts and which baselines remain diagnostic.

## Limitations

RTL recovery claims remain out of scope. The artifact now commits a tiny CC0 RTL seed corpus with source-location metadata, but successful Yosys lowering is tool-dependent and is recorded as `tool_missing` on machines without Yosys. Oracle rows are diagnostic and must not be merged with blind recoveries.

## Related Work Positioning

Position against equivalence checking, SAT sweeping/FRAIG, observability don't-care optimization, source mapping, and formal artifact evaluation. The novelty is the auditable separation between proofs, diagnostics, graph-active rewrites, and bounded failures.
