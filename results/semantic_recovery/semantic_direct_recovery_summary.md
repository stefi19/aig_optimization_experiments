# Direct Semantic Template Recovery Summary

This phase recovers only expressions contained in the bounded direct-template grammar. Parameterized coefficient solving and CEGIS refinement remain future work.

Every accepted expression below is `formally_verified_region` using exhaustive region truth-table comparison. Sampled simulation is used only as a filter and is not formal proof. Region equivalence is not labeled global equivalence.

## Candidate Funnel

- Eligible regions: 686
- Regions with direct candidates: 686
- Generated candidates: 22728
- Canonical candidates: 618
- Simulation checked: 22728
- Simulation survivors: 1560
- Formal checks: 1483
- Verified candidates: 1483
- Recovered regions: 418

## Recovery

- Formal recovery rate: 0.609329
- Exact syntactic recovery rate: 0.260933
- Canonical syntactic recovery rate: 0.045190
- Equivalent-alternative rate: 0.413994

## Problem-A-Inspired RTL Cost

- Mean verified RTL cost: 1.926500
- Median verified RTL cost: 1.000000
- Mean reduction rate: 32.137680
- Cases above 70% reduction: 460
