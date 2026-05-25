# Initial AIG/BLIF Optimization Correspondence Experiments

This folder contains a small first prototype for testing how logic optimizations affect internal node correspondence.

The current goal is deliberately modest:

> Start at BLIF/AIG level, apply one optimization at a time, and measure whether internal nodes can still be matched exactly or only approximately through region-like features.

This is useful before trying to connect the method back to RTL names, because it isolates the synthesis/correspondence problem.

---

## Folder structure

```text
aig_optimization_experiments/
  benchmarks/                 small hand-written BLIF examples
  variants/                   generated optimized BLIF files
  logs/                       ABC logs
  results/                    CSV results from the Python analysis
  run_abc_variants.sh          runs ABC optimizations
  analyze_blif_matches.py      computes matching metrics and top-k candidates
  README.md                   this file
```

---

## Requirements

You need:

- Python 3.10 or newer
- Berkeley ABC installed

If ABC is already in your terminal path, you can simply run `abc`.

If not, you can build it from the official repository:

```bash
git clone https://github.com/berkeley-abc/abc.git
cd abc
make
```

Then either add it to PATH or run the experiment with:

```bash
ABC=/path/to/abc ./run_abc_variants.sh
```

---

## How to run

From inside this folder:

```bash
./run_abc_variants.sh
python3 analyze_blif_matches.py
```

The first script generates optimized BLIF files in `variants/`.

The second script generates:

```text
results/summary_metrics.csv
results/top_candidates.csv
```

---

## What Experiment 1 measures

For every benchmark and optimization, the script compares the original network with the optimized one.

The main metrics are:

| Metric | Meaning |
|---|---|
| `original_nodes` | Number of internal nodes before optimization |
| `optimized_nodes` | Number of internal nodes after optimization |
| `original_levels` | Logic depth before optimization |
| `optimized_levels` | Logic depth after optimization |
| `exact_internal_matches` | How many optimized internal nodes still match an original internal node exactly |
| `old_signatures_disappeared` | Internal functions present before optimization but lost after optimization |
| `new_signatures_appeared` | Internal functions introduced by optimization |
| `avg_best_support_overlap` | Average best overlap between optimized node support and original node support |

A useful result for this project is not necessarily high exact matching.

Actually, if exact internal matches disappear but support overlap remains meaningful, that supports the idea that a region-level correspondence method is more realistic than strict node-level matching.

---

## What Experiment 2 starts to measure

The file `results/top_candidates.csv` contains the first version of a top-k recovery experiment.

For each optimized node, the script ranks original nodes using:

```text
combined_score = 0.55 * simulation_similarity
               + 0.35 * support_overlap
               + 0.10 * depth_similarity
```

This is only a simple baseline. I would not present this formula as final. It is useful because it gives a first concrete way to test whether approximate matching can recover reasonable candidates before using SAT.

Later, the SAT refinement step can be added after this ranking, only for the strongest candidates.

---

## How to interpret results

### Case 1: node-level matching still works

This happens when:

```text
exact_internal_matches is high
old_signatures_disappeared is low
new_signatures_appeared is low
avg_best_support_overlap is high
```

This means the optimization did not strongly change the internal structure.

### Case 2: region-level matching is needed

This is the more interesting case for the research direction:

```text
exact_internal_matches is low
old_signatures_disappeared is high
new_signatures_appeared is high
avg_best_support_overlap is still medium or high
```

This means exact internal node matching is too strict, but the optimized logic still seems related to the same original region.

### Case 3: hard matching case

This happens when both exact matches and support overlap are low.

In that case, support alone is probably not enough. The method will need more context, such as:

```text
simulation similarity
observability to endpoint
anchor nodes
SAT refinement
critical-path restriction
```

---

## Current limitations

This prototype is intentionally small.

Important limitations:

- It analyzes BLIF files, not RTL source code.
- It does not preserve RTL names yet.
- It does not implement SAT refinement yet.
- For small circuits, simulation is exact. For larger circuits, the script switches to deterministic random simulation.
- The BLIF parser only supports the simple `.names` style used by these examples and by basic ABC output.

These limitations are okay for the first milestone, because the purpose is to test the behavior of optimizations before building the full method.

---

## Suggested next steps

1. Run the current toy benchmarks.
2. Add 3 to 5 slightly larger hand-written circuits.
3. Add small ISCAS/EPFL-style benchmarks.
4. Restrict the analysis to nodes near one selected output or critical path.
5. Add SAT only after top-k candidate ranking.
6. Later, connect the recovered region back to RTL names or source-level expressions.

---

## Short research framing

A nice way to describe this first prototype is:

> The first prototype operates at BLIF/AIG level and measures how individual synthesis optimizations affect internal node correspondence. The goal is not yet to recover RTL source names, but to determine whether exact node matching remains meaningful after balancing, rewriting, refactoring, and resubstitution. If exact internal matches disappear while support overlap remains significant, this motivates a region-based correspondence method between stable anchors.
