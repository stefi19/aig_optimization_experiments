# ABC SAT Sweeping / Hybrid Validation — Design Notes

> **Status:** prototype extension, added after mentor feedback in May 2026.

---

## What the previous implementation did

The first version of this project performed node-correspondence matching
entirely in Python:

1. **ABC** was used as a black box to generate optimised circuit variants
   (`run_abc_variants.sh`).  Python never looked inside how ABC works.
2. **Python** parsed the BLIF files, simulated each node with random input
   patterns, and built Boolean signature fingerprints.
3. **Python** ranked candidate correspondences using a weighted score:

   ```
   combined_score = 0.55 × simulation_similarity
                  + 0.35 × support_overlap
                  + 0.10 × depth_similarity
   ```

4. For the top candidates, **Python** called `abc cec` once *per candidate
   pair* (via `sat_refinement_abc.py`) to get a yes/no equivalence verdict.
   This was slow because it spawned a separate ABC process for every pair.

The approach works.  But it duplicates simulation work that ABC already does
internally, and it misses an opportunity to get much richer equivalence
information (whole equivalence classes, not just pairwise verdicts) efficiently.

---

## The mentor's feedback

> "Another thing to look into is directly using the SAT sweeping tool inside
> ABC in order to identify exact matches and to get already simulations that
> have been used by this tool.  I think what you implemented works but it
> would make sense to re-use already what is present in ABC.  It would be a
> little bit harder to code into it but it would make the execution more
> efficient and faster."

The key phrase is **re-use what is present in ABC**.  ABC already has:

- **`fraig`**: a FRAIG (Functionally Reduced AIG) algorithm that internally
  runs simulation + SAT to find and merge all equivalent nodes inside one
  network.  It's written in optimised C and is very fast.
- **`dump_equiv`**: a command that takes *two* BLIF files, builds a combined
  AIG miter, runs FRAIG-style sweeping, and writes out the cross-network
  equivalence classes to a text file.

`dump_equiv` is exactly what we need: it gives us a formal, SAT-proven mapping
from optimised nodes to original nodes in one shot, instead of requiring
one ABC call per candidate pair.

---

## Why ABC SAT sweeping / FRAIG is better than our Python simulation

| Aspect | Python simulation | ABC FRAIG / dump_equiv |
|---|---|---|
| **Provability** | Approximate — can only test finite input patterns | Formal — SAT proves equivalence for all inputs |
| **Efficiency** | One ABC call per candidate pair (N × subprocess overhead) | One ABC call per (benchmark, optimisation) pair — covers all nodes at once |
| **Simulation quality** | 4096 random patterns (good but not exhaustive) | ABC uses adaptive simulation that refines patterns guided by SAT results |
| **Completeness** | Only checks pre-selected candidates | Considers ALL node pairs in both networks simultaneously |
| **False positives** | Possible (high sim score ≠ equivalence) | None — SAT proof is exact |

The Python ranking is still useful because:
- It's fast and runs without ABC on the critical path.
- It provides a ranked list that guides *which* pairs to care about.
- It includes support overlap and depth similarity — metrics ABC doesn't directly expose.

So the hybrid flow keeps both stages.

---

## How the hybrid flow works

```
Stage 1: Python simulation ranking  (existing, unchanged)
  analyze_blif_matches.py
    → results/top_candidates.csv   (all ranked candidates, fast)

Stage 2: ABC dump_equiv validation  (new)
  hybrid_validation.py
    for each (benchmark, optimisation) pair:
      abc dump_equiv original.blif optimised.blif → equiv_classes.txt
      [ONE ABC call covers ALL node pairs in the two networks]
    cross-reference top-K candidates with ABC equiv classes
    → results/hybrid/hybrid_validated_candidates.csv

Output columns added in Stage 2:
  abc_validated   — True if ABC proved the correspondence
  abc_complement  — True if the match is a Boolean complement
  abc_result      — human-readable verdict
  abc_log_file    — path to ABC log for inspection
```

The key improvement: Stage 2 calls ABC once *per BLIF pair*, not once per
candidate row.  For a benchmark with 50 top candidates, this reduces ABC
subprocess calls from 50 to 1.

---

## Implementation notes

### `dump_equiv` output format

ABC writes lines like:

```
<class_id>:<model_name>:<node_name>
<class_id>:<model_name>:NOT:<node_name>   ← complement
```

Nodes from both the original and optimised network appear in the same class
if ABC proved them equivalent.  Since both BLIFs usually share the same
`.model` name, we can't distinguish network origin from the model name alone.
The parser (`parse_dump_equiv_file`) cross-references with node sets from each
BLIF file:

- A node that exists **only** in the original BLIF → from the original network
- A node that exists **only** in the optimised BLIF → from the optimised network
- A node that exists in **both** → position-based heuristic (first occurrence =
  original, second = optimised)

For aggressive optimisations that rename all internal nodes, the first two
cases cover everything unambiguously.  For mild optimisations (like `balance`)
that preserve names, the position heuristic is needed.

### `fraig_stats` sanity check

In addition to `dump_equiv`, the sweep module also runs
`strash → fraig → print_stats` on the original network alone.  This tells
us how many nodes ABC considers redundant within a single network — a useful
sanity check.  If fraig eliminates many nodes, the original synthesis left
redundant logic that our Python analysis was treating as distinct nodes.

### Defensive error handling

Every ABC call is wrapped with:
- a configurable timeout (`ABC_TIMEOUT = 60s`)
- error log written to disk regardless of success/failure
- structured error fields in the result objects so the caller can continue
  processing other pairs rather than crashing

---

## Current limitations

1. **`dump_equiv` with identical model names:** when both BLIFs use the same
   `.model` name (which ABC always writes when optimising from the same source),
   the cross-network node attribution relies on our BLIF-parsing heuristic.
   This works well in practice but could theoretically misattribute a node in
   edge cases where the original and optimised networks have exactly the same
   set of internal node names after a mild optimisation.

2. **SAT budget:** `dump_equiv` uses a conflict limit (default 1000) per node.
   For large circuits with complex logic, some pairs will time out at the SAT
   level.  Those aren't reported as matches — they fall through to the
   `not_in_equiv_class` bucket.

3. **No complement recovery in the Python ranking:** when ABC reports a
   complement match (`abc_result = sat_proven_complement`), the Python ranking
   would have given it a *low* simulation score (because the node outputs the
   opposite bit pattern).  This is an interesting case: the nodes are logically
   equivalent up to a polarity flip — something our simulation-based score
   completely misses.

4. **Per-node CEC fallback (sat_refinement_abc.py) still exists:** the old
   approach is kept as a baseline and is still run by the default `sat-pipeline`
   Makefile target.  The hybrid flow is invoked separately via `make hybrid-validate`.

---

## Future work: direct access to ABC's internal structures

The current implementation is "ABC as a subprocess": we pass text in, get text
out.  A deeper integration would involve modifying ABC's C source code to:

1. Export the FRAIG equivalence classes directly as a structured file (JSON or
   CSV) from inside the tool.  This would remove the need to parse the human-
   readable `dump_equiv` text format.

2. Re-use the simulation patterns ABC already generated during FRAIG sweeping
   to populate our Python `simulation_similarity` scores, so we don't simulate
   twice.

3. Access ABC's internal **AIG node IDs** across the original and optimised
   networks to build a precise correspondence map at the AIG level rather than
   BLIF node-name level.

These would be significant C-level changes to ABC but would remove the
Python-level BLIF parsing entirely and make the tool faster and more accurate.
This is left as future work.

---

## Example commands

```bash
# Run the full hybrid validation (top-20 candidates per pair):
ABC=.abc_build/abc_repo/abc python3 hybrid_validation.py --top-k-validate 20

# Run on the already-filtered sat_refinement_candidates.csv:
ABC=.abc_build/abc_repo/abc python3 hybrid_validation.py \
    --candidates results/sat_refinement_candidates.csv \
    --top-k-validate 50

# Run the single-pair SAT sweep tool directly (for one BLIF pair):
python3 scripts/abc_sat_sweep_validation.py \
    --orig  variants/majority3_original.blif \
    --opt   variants/majority3_balance.blif  \
    --abc   .abc_build/abc_repo/abc

# Via Makefile:
make hybrid-validate
```

---

*Written May 2026 as part of the AIG Optimization Experiments prototype.*
