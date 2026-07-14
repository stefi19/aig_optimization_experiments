# ABC-Native SAT Sweeping / FRAIG Baseline Plan

This iteration adds an exploratory baseline around ABC's own SAT sweeping and
FRAIG machinery. The motivation comes from Carmine's suggestion that the current
custom validation flow should be compared against the native tools ABC already
uses internally for simulation-guided SAT refinement.

## Why This Matters

The current project has a custom correspondence pipeline:

- compute exact internal-node signatures where feasible,
- rank non-exact candidates with support and sampled simulation similarity,
- validate selected pairs with SAT/CEC,
- add approximate node-distance and critical-path back-mapping analyses.

That pipeline is useful because it produces explicit candidate mappings between
old and optimized nodes. However, it is pairwise and external to ABC's normal
optimization flow. ABC's `fraig` and related SAT-sweeping commands are built for
the same general problem of proving internal equivalences and merging redundant
AIG nodes efficiently. A native ABC baseline can therefore tell us whether the
custom flow is finding correspondences in the same regions where ABC can also
prove and merge redundancy.

## How ABC-Native Sweeping Differs

The custom flow asks many targeted questions: does original node `u` correspond
to optimized node `v`, possibly after complementation? It is mapping-oriented.

The ABC-native baseline asks a different question: after ABC reads one optimized
network, strashes it, and runs `fraig`, how much of that network can ABC merge or
reduce using its internal simulation and SAT machinery? It is reduction-oriented.

That distinction is important. A smaller swept network does not directly say
which optimized node came from which original node. It only says ABC found
provable redundancy inside the network being swept. Commands such as `cec` and
`dump_equiv` can expose more formal equivalence information, but ordinary
`fraig` logs may only expose node/level statistics.

## What We Hope To Compare

For each selected benchmark and optimization, the baseline records:

- node and level counts before ABC-native sweeping,
- node and level counts after `fraig`-style sweeping,
- runtime,
- whether the ABC command completed or failed,
- available ABC log/statistics snippets,
- the swept BLIF path.

The comparison script then joins these rows to existing custom results:

- preservation rate from exact/sampled signature matching,
- SAT/CEC-proven equivalences after structural mismatch,
- approximate near-match availability,
- critical-path mapped fraction when present.

The central exploratory question is:

> Does ABC-native SAT sweeping reduce or merge the same kinds of structures where
> the custom flow finds correspondences?

At this stage, the answer is indirect. Alignment means the same
benchmark/optimization row shows both ABC-native reductions and custom recovery
evidence. It does not mean ABC directly returned the same node mapping.

## ABC Commands To Probe

The capability probe checks whether the local ABC binary supports:

- `fraig`
- `fraig -x`
- `fraig -y`
- `&get`
- `&fraig -x`
- `cec`
- `print_stats`
- `ps`
- `write_blif`

The `&` command space is build-dependent. `fraig -y` is also treated as
optional because not all ABC builds expose the same flags. Unsupported commands
are recorded as unsupported rather than treated as fatal failures.

## What ABC May Not Expose Directly

ABC can prove equivalences internally while sweeping, but the standard `fraig`
flow may not print equivalence classes or old-to-new node mappings. In that
case, this baseline can still compare network-level reductions, but it cannot
replace the mapping-oriented custom pipeline.

If direct class extraction becomes necessary, future work should investigate:

- `dump_equiv` for cross-network equivalence classes,
- verbose FRAIG logs and available print commands,
- ABC source-level instrumentation around SAT sweeping classes,
- whether `cec` side outputs can be used as a stable public interface.

## Relation To Carmine's Suggestion

Carmine's suggestion is best interpreted as: use ABC's own SAT sweeping behavior
as a serious baseline before investing further in custom SAT validation. This
iteration follows that advice conservatively. It probes what the local ABC build
exposes, runs small native sweep flows, compares them to existing custom
correspondence results, and documents the boundary between network reduction and
explicit node correspondence.
