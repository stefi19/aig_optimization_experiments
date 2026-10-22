## Audit and exact measurement integrity

The replay covers 32 historical pairs. All 32 old values reproduce, and all 16 selected verified rows correct to zero and pass fresh CEC. The selected rejected controls remain disproved. The exact global/complement/contextual SMT queries have 0 unknown results in the controlled suite.

| Old label   | Mode    |   Rows |   Old_mean |   Corrected_mean |
|:------------|:--------|-------:|-----------:|-----------------:|
| rejected    | exact   |      8 |      0.011 |            0.011 |
| rejected    | sampled |      8 |      0.001 |            0.001 |
| verified    | exact   |      8 |      0.125 |            0.000 |
| verified    | sampled |      8 |      0.028 |            0.000 |

These sampled audit rows reuse their historical 4,096-pattern streams; the separate calibration experiment uses 1,024 patterns.

## Known-lineage ranking

**Development: 24 queries, 20 positive lineage queries.**

| Method      |   P@1 |   P@5 |   MRR |   Top-5 coverage |
|:------------|------:|------:|------:|-----------------:|
| structural  | 0.375 | 0.167 | 0.542 |            1.000 |
| fingerprint | 0.167 | 0.167 | 0.463 |            1.000 |
| sat_only    | 0.333 | 0.167 | 0.521 |            1.000 |
| global      | 0.167 | 0.133 | 0.392 |            0.800 |
| complement  | 0.208 | 0.133 | 0.397 |            0.800 |
| contextual  | 0.208 | 0.167 | 0.431 |            1.000 |
| hybrid      | 0.208 | 0.167 | 0.431 |            1.000 |

**Heldout: 24 queries, 20 positive lineage queries.**

| Method      |   P@1 |   P@5 |   MRR |   Top-5 coverage |
|:------------|------:|------:|------:|-----------------:|
| structural  | 0.417 | 0.167 | 0.569 |            1.000 |
| fingerprint | 0.333 | 0.167 | 0.566 |            1.000 |
| sat_only    | 0.333 | 0.167 | 0.514 |            1.000 |
| global      | 0.167 | 0.125 | 0.382 |            0.750 |
| complement  | 0.250 | 0.133 | 0.423 |            0.800 |
| contextual  | 0.250 | 0.167 | 0.458 |            1.000 |
| hybrid      | 0.250 | 0.167 | 0.458 |            1.000 |

![Held-out lineage ranking. All methods use the same source-candidate pools.](figures/approximate_correspondence/lineage_ranking.png){width=90%}

The hybrid falls below the structural baseline in held-out Precision@1; added functional features do not improve lineage accuracy on this suite. Complement handling improves some rankings relative to direct distance, but contextual and observability features do not independently improve this suite's headline ranking. Single-feature ablations remain in the full per-family CSVs.

## Context, observability, and formal-gate ablation

![Global versus contextual error for all controlled candidates. Multiple points overlap.](figures/approximate_correspondence/global_contextual.png){width=80%}

| Split       |   Near rows |   Unsafe |   Exact context |   No global match |
|:------------|------------:|---------:|----------------:|------------------:|
| development |          40 |        8 |              32 |                 8 |
| heldout     |          44 |       12 |              32 |                12 |

Near means complement distance at most 5%; unsafe means nonzero best-polarity contextual output error. Removing the formal gate admits these unsafe near rows even though their distance passes the filter. This is candidate-level accounting, not a count of accepted graph rewrites.

## Path diagnostics and sampling calibration

The separate path diagnostic contains 26 targets: 1 lacks any exact or complemented source node in its full internal pool. None adds a nonzero near match within 5%, while 1 has a zero-context-error candidate despite lacking a globally equal/complemented candidate. This gives a small contextual observation and a null result for global near-match path coverage. These targets have no lineage labels.

Across 3,234 pointwise intervals, empirical coverage is 98.98%. Shared cases and streams make these intervals dependent; this percentage is a calibration diagnostic, not a coverage theorem or evidence of exact equality. Error estimates and all seeds are available in the sampling table.

## Matched-budget exact reconstruction

| Split       |   Budget | Enumeration   | Guided    |
|:------------|---------:|:--------------|:----------|
| development |        1 | 0--0 / 10     | 1--1 / 10 |
| development |        4 | 0--0 / 10     | 1--1 / 10 |
| development |       16 | 0--0 / 10     | 1--1 / 10 |
| development |       64 | 1--1 / 10     | 1--1 / 10 |
| development |      176 | 1--1 / 10     | 1--1 / 10 |
| heldout     |        1 | 0--0 / 8      | 1--1 / 8  |
| heldout     |        4 | 0--0 / 8      | 1--1 / 8  |
| heldout     |       16 | 0--0 / 8      | 1--1 / 8  |
| heldout     |       64 | 1--1 / 8      | 1--1 / 8  |
| heldout     |      176 | 1--1 / 8      | 1--1 / 8  |

Counts are the minimum--maximum accepted target counts across the three seeds, with unique target IDs as denominator. At budget one, guided ordering accepts one target in each flow split and enumeration accepts zero. At budgets 64 and 176, both methods accept the same one target per split. Across flows these two target instances share one identical graph artifact (SHA-256 begins `8601cd0c46bd`).

![Exact-check budget versus accepted target instances; shaded ranges show minimum and maximum over three ordering seeds.](figures/approximate_correspondence/reconstruction_budget.png){width=98%}

| Ordering         |   Exact_checks |   CEC_calls |   Total_seconds |
|:-----------------|---------------:|------------:|----------------:|
| enumeration      |           8379 |          12 |           1.230 |
| sampled_distance |           7417 |          12 |           1.238 |

These totals include both flow splits and all three seeds. Exact-check counts fall, while total time remains effectively unchanged at this scale; no runtime advantage is claimed. Every emitted accepted artifact passed both ABC CEC scopes, and the independent checker replays each distinct graph. Most targets remain unresolved under the eight-signal unary/binary pool, or hit a graph-activity gate.

## Paired uncertainty

| Outcome          | A          | B           |    A-B |   95% low |   95% high |
|:-----------------|:-----------|:------------|-------:|----------:|-----------:|
| Lineage P@1      | hybrid     | structural  | -0.167 |    -0.333 |     -0.042 |
| Lineage P@1      | hybrid     | global      |  0.083 |     0.000 |      0.208 |
| Lineage P@1      | complement | global      |  0.083 |     0.000 |      0.208 |
| Graph acceptance | guided     | enumeration |  0.125 |     0.000 |      0.375 |

Bootstrap intervals use 2,000 deterministic paired resamples. Reconstruction first averages ordering seeds within target, so seed repetition does not inflate the independent-unit count. With only eight held-out target IDs, the tight-budget interval includes zero. The finite-suite effect should not be interpreted as a statistically established population improvement.

## Toolchain

The recorded run uses Python 3.11.15, Z3 4.16.0, ABC revision `bcfdf592289a`, uniform PI inputs, and the frozen configuration hash recorded in `provenance.json`. Timeouts are 5 seconds per SMT query and 30 seconds per ABC call. Full version and artifact digests remain machine readable.
