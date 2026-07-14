# Timing-Aware Path Probe

This probe compares the existing structural longest path with a lightweight delay-weighted proxy path.
It does not use real physical timing or a mapped technology library.

- Case studies: 3
- Mean structural mapped fraction: 0.868
- Mean delay-weighted mapped fraction: 0.868
- Mean path node Jaccard overlap: 1.000

## Case Summary

| circuit | optimization | structural_path_length | delay_weighted_path_length | structural_mapped_fraction | delay_weighted_mapped_fraction | shared_node_jaccard | delay_path_total_delay |
| --- | --- | --- | --- | --- | --- | --- | --- |
| c432 | rewrite | 41 | 41 | 0.780 | 0.780 | 1.000 | 41.000 |
| c2670 | rewrite | 21 | 21 | 0.857 | 0.857 | 1.000 | 21.000 |
| c6288 | rewrite | 117 | 117 | 0.966 | 0.966 | 1.000 | 117.000 |
