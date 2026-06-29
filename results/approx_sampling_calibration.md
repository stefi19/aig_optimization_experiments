# Approximate-Distance Sampling Calibration

This calibration recomputes sampled distances for candidate pairs whose exact
truth-table distance is available. Exact distances are recomputed on the same
currently reproducible BLIF pair used for sampling, so stale generated variants
are skipped instead of mixed into the error estimate. This estimates sampling
error; it does not make sampled rows formal.

- Exact candidate pairs calibrated: 27
- Sample sizes: 128, 512, 1024, 4096, 8192
- Seeds per sample size: 5

## Error by Sample Size

|   sample_size |      rows |   mean_absolute_error |   median_absolute_error |   max_error |   pct_within_1pct_abs_error |   pct_within_2pct_abs_error |   pct_within_5pct_abs_error |   mean_absolute_rank_delta |   mean_spearman_rank_correlation |
|--------------:|----------:|----------------------:|------------------------:|------------:|----------------------------:|----------------------------:|----------------------------:|---------------------------:|---------------------------------:|
|     128.00000 | 135.00000 |               0.02545 |                 0.01562 |     0.09375 |                     0.33333 |                     0.51852 |                     0.83704 |                    2.05185 |                          0.93593 |
|     512.00000 | 135.00000 |               0.01199 |                 0.00977 |     0.05078 |                     0.58519 |                     0.80741 |                     0.99259 |                    1.60000 |                          0.95908 |
|    1024.00000 | 135.00000 |               0.00935 |                 0.00781 |     0.04102 |                     0.62222 |                     0.92593 |                     1.00000 |                    1.45926 |                          0.96726 |
|    4096.00000 | 135.00000 |               0.00473 |                 0.00391 |     0.02246 |                     0.91111 |                     0.99259 |                     1.00000 |                    1.29630 |                          0.97642 |
|    8192.00000 | 135.00000 |               0.00332 |                 0.00232 |     0.01746 |                     0.97037 |                     1.00000 |                     1.00000 |                    1.25926 |                          0.97659 |

## Rank Stability

Rank stability is measured indirectly by ranking the calibrated exact-distance
pairs by exact distance and by sampled distance for each sample-size/seed run.
This is only a local calibration set, not a full replacement for end-to-end
candidate-ranking validation.

|   sample_size |   mean_absolute_rank_delta |   mean_spearman_rank_correlation |
|--------------:|---------------------------:|---------------------------------:|
|     128.00000 |                    2.05185 |                          0.93593 |
|     512.00000 |                    1.60000 |                          0.95908 |
|    1024.00000 |                    1.45926 |                          0.96726 |
|    4096.00000 |                    1.29630 |                          0.97642 |
|    8192.00000 |                    1.25926 |                          0.97659 |

## Interpretation

Small sample sizes can be useful for coarse screening, but the calibration
should be consulted before treating sampled approximate distance as a stable
ranking signal. Exact rows remain formal; sampled rows remain estimates.
