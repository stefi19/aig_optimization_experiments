# Paper Outline

## Problem

Recovering internal correspondences after logic synthesis is useful for debugging, source mapping, and proof-carrying transformations, but aggressive optimization destroys simple name and structural evidence.

## Threat Model

All headline recovery claims must distinguish controlled generated BLIF, blind generated BLIF, standard netlist diagnostics, oracle diagnostics, historical ineligible rows, and future external RTL work.

## Method

1. Recover candidate internal semantic regions.
2. Refine candidates with counterexamples or exact certificates.
3. Construct source-side counterparts or cross-netlist transplants only when local evidence is strong enough.
4. Require graph activity and global CEC before counting recovered boundaries.

## Evaluation

Use `results/research_wow/recoverability_frontier.csv` as the main table and `results/research_wow/recoverability_frontier.png` as the main figure.

## Failure Taxonomy

Use `results/research_wow/failure_taxonomy.csv` to explain why null results are meaningful: missing provenance, target irrelevance, non-compact interfaces, absent rewrite artifacts, bounded blind CEGIS exhaustion, and formal locality barriers.

## Ablations and Baselines

Use `results/research_wow/ablation_summary.csv` and `results/research_wow/baseline_summary.csv` to show which components move counts and which baselines remain diagnostic.

## Limitations

External RTL claims remain out of scope until a redistributable corpus and pinned Yosys lowering flow are part of the artifact. Oracle rows are diagnostic and must not be merged with blind recoveries.

## Related Work Positioning

Position against equivalence checking, SAT sweeping/FRAIG, observability don't-care optimization, source mapping, and formal artifact evaluation. The novelty is the auditable separation between proofs, diagnostics, graph-active rewrites, and bounded failures.
