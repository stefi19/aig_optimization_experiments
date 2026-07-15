# Boundary-Recovery Semantics Repair Summary

## Canonical Semantics

- Schema: `coi_schema_v1`
- Convention: BI outside R; BO subset of R
- `BI = {u outside R | exists v in R with u -> v}`
- `BO = {u in R | u is a PO or has a fanout outside R}`
- Identity must recover exact BI, exact BO, exact region, and zero extension.

## COI Repair

- Original/micro audit rows: 16
- Finally valid canonical COIs: 14
- Repaired rows: 3
- Excluded rows: 2

## Circuit Eligibility

- Declared circuit rows: 70
- Available rows: 30
- Infrastructure skips: 40

## Identity

- Eligible valid identity cases: 14
- Successes: 14
- Zero-extension cases: 14
- Exact EBI matches: 14
- Exact EBO matches: 14
- Exact region matches: 14

## Corrected Optimized Results

- Valid attempted cases: 32
- Successful cases: 20
- Success rate: 62.5%

Failure taxonomy:

- ebi_mismatch;ebo_mismatch;region_mismatch;bypass_edges: 4
- ebi_mismatch;region_mismatch;bypass_edges: 8

## Critical Path

- Generated COI validation rows: 99
- Valid generated COIs: 0
- Region-level critical-path enclosure is not node equivalence.

## Decision Gate

Identity is perfect on the canonical eligible set. If optimized recovery remains sparse, the next step is ODC-aware or speculative anchor generation, unless future data shows relevant anchors exist but cut search fails.
