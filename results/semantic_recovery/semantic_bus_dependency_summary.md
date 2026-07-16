# Semantic Bus Inference and Dependency Geometry Summary

This phase infers bus hypotheses and dependency geometry from canonical scalar
interfaces. It does not synthesize expressions, solve coefficients, run CEGIS,
or claim high-level RTL operation recovery.

## Bus Inference

- Inference mode: inferred bus mode.
- Ground truth used for generation: false.
- Ground truth used for evaluation: true.
- Evaluated region rows: 686
- Direction rows: 1372
- Top-1 bus match rate: 1.000000
- Top-3 bus match rate: 1.000000
- Top-5 bus match rate: 1.000000
- Mean membership precision: 0.999210
- Mean membership recall: 0.999210
- Mean bit-order accuracy: 0.997376
- Mean reciprocal rank: 0.939389

## Dependency Geometry

Dependency matrices are structural plus sampled simulation estimates and bounded
Boolean-difference estimates where available. Sampled dependency values are
heuristic evidence, not formal proof.

## Family Ranking

Family ranking is a transparent, broad classifier over dependency geometry. It
is not operator recovery.

- Ranked regions: 686
- Top-1 family accuracy: 0.246356
- Top-3 family accuracy: 0.571429
- MRR: 0.460461

## Ablations

| Feature mode | Bus top-1 | Bus MRR | Family top-1 | Family MRR |
| --- | ---: | ---: | ---: | ---: |
| names_only | 1.000000 | 0.939389 | 0.246356 | 0.460461 |
| structure_only | 1.000000 | 0.939389 | 0.246356 | 0.460461 |
| names_plus_structure | 1.000000 | 0.939389 | 0.246356 | 0.460461 |
| full_combined | 1.000000 | 0.939389 | 0.246356 | 0.460461 |

The next phase should use these inferred groups to build dependency matrices suitable for expression-family-specific recovery, still with formal validation separated from heuristic ranking.
