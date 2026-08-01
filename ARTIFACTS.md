# Artifact Guide

This repository is a research prototype and artifact for internal
correspondence recovery after logic synthesis. The artifact is organized around
committed evidence tables under `results/`, reproducibility scripts under
`scripts/`, and focused checkers that reject stale or overclaimed results.

## Quick Start

```bash
python -m pip install -r requirements.txt
make artifact-check
```

`make artifact-check` is the reviewer-safe entrypoint. It validates committed
tables, schemas, headline claims, and evidence labels without rebuilding ABC or
rerunning every expensive experiment.

## Validation Tiers

- `make smoke`: fast dependency and unit checks for the most important formal
  helpers and artifact contracts.
- `make portable-no-abc`: CI-style checks that must pass when ABC is absent;
  these validate schemas, rejection paths, and no-ABC behavior.
- `make artifact-check`: validates committed result freshness, blind CEGIS,
  active-source, cross-netlist, locality, provenance, necessity-first, and the
  research-facing derived artifacts and claims ledger.
- `make evidence-advancement`: builds the checked next-step evidence layer
  without promoting rows past their proof, graph, tool, or CEC obligations.
- `make check-evidence-advancement`: validates those next-step tables and
  proof objects.
- `make formal-abc`: builds/checks pinned ABC and runs the full unit suite plus
  artifact claims.
- `make reproduce-paper-tables`: rebuilds the canonical artifact manifest and
  validates committed paper tables and headline claims.
- `make demo-wow`: prints a reviewer-safe mini-report that combines a controlled
  graph-active proof path with a blind CEGIS counterexample-refinement trace.
- `make paper-pdf`: compiles `paper/paper.md` into
  `output/pdf/aig_internal_correspondence_artifact.pdf`.

## Tool Assumptions

- Python 3.11 or newer is expected. The current local validation also passes on
  Python 3.13 after installing `requirements.txt`.
- `z3-solver` is required for formal semantic proofs and some tests.
- ABC is pinned to revision `bcfdf592289a408cd67ec19260f8a60a37b085b6`.
- Yosys is optional for the committed BLIF-only artifact. The repository now
  includes a tiny pinned CC0 RTL corpus with source-location metadata, but local
  validation records Yosys lowering as `tool_missing` unless Yosys is installed.

## Committed Evidence Policy

The committed result tables are review evidence, not scratch output. Regenerable
large artifacts should stay outside the core review path unless they are needed
to support a specific claim.

Current committed headline counts:

- Controlled accepted graph-active counterparts: 10.
- Controlled accepted transplants: 12.
- 48 fresh provenance-complete generated-research targets.
- 31/48 have compact exact input interfaces.
- corrected historical eligible transplantation denominator: 0.
- Evidence-advancement promoted rows: source-blind graph-active 0/56; compact
  interface rewrites 0/48; bounded grammar completeness 4/12; pinned RTL corpus
  3/3; ODC graph-active placement 0/10; locality proof objects 57/57.

## Expected Runtime

- `make smoke`: usually under a minute after dependencies are installed.
- `make artifact-check`: usually seconds to a few minutes; it does not rebuild
  ABC.
- `make formal-abc`: can take several minutes because it builds/checks ABC and
  runs the full suite.
- Full research pipelines are intentionally separate from artifact validation
  because they rewrite large result directories.

## Artifact Manifest

Run:

```bash
make build-artifact-manifest
```

This writes `results/artifact_manifest.csv`, including the primary artifact,
SHA-256 digest, row count, reproduction command, git SHA, config hash,
Python/Z3 versions, ABC revision, dataset classes, and schema version for each
major result family.

## Research-Wow Layer

Run:

```bash
make research-wow
make check-research-wow
make paper-pdf
```

This derives the paper-facing layer from committed evidence:

- `results/research_wow/recoverability_frontier.csv`
- `results/research_wow/failure_taxonomy.csv`
- `results/research_wow/ablation_summary.csv`
- `results/research_wow/baseline_summary.csv`
- `results/research_wow/demo_trace.csv`
- `results/research_wow/recoverability_frontier.png`
- `paper/outline.md`
- `paper/claims_to_tables.md`
- `paper/tables/research_wow_tables.md`
- `paper/case_studies/counterpart_and_blind_cegis.md`

## Evidence-Advancement Layer

Run:

```bash
make evidence-advancement
make check-evidence-advancement
```

This writes:

- `results/evidence_advancement/source_blind_counterpart_inference.csv`
- `results/evidence_advancement/compact_interface_rewrite_attempts.csv`
- `results/evidence_advancement/grammar_completeness_certificates.csv`
- `results/evidence_advancement/rtl_corpus_manifest.csv`
- `results/evidence_advancement/odc_placement_accounting.csv`
- `results/evidence_advancement/locality_proof_objects.csv`
- `results/evidence_advancement/proof_objects/locality/*.json`

The dedicated guide is
[`docs/evidence_advancement_next_steps.md`](docs/evidence_advancement_next_steps.md).
