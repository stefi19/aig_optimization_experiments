# Timing vs Structural Mapping Comparison

The delay-weighted path uses a configurable proxy delay model over BLIF `.names` nodes.
Treat this as a timing-direction investigation, not library-based static timing analysis.

| circuit | optimization | structural_mapped_fraction | delay_weighted_mapped_fraction | structural_unresolved_fraction | delay_weighted_unresolved_fraction | shared_node_jaccard |
| --- | --- | --- | --- | --- | --- | --- |
| c432 | rewrite | 0.780 | 0.780 | 0.220 | 0.220 | 1.000 |
| c2670 | rewrite | 0.857 | 0.857 | 0.143 | 0.143 | 1.000 |
| c6288 | rewrite | 0.966 | 0.966 | 0.034 | 0.034 | 1.000 |
