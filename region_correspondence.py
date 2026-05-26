#!/usr/bin/env python3

"""
region_correspondence.py
=========================
Region-level correspondence baseline for the AIG optimization experiments.

Motivation
----------
analyze_blif_matches.py scores node pairs using global simulation signatures
and full-support Jaccard overlap.  That works well when the original and
optimized networks have similar sizes, but it does not capture *structural
locality*: two nodes that implement the same sub-function should still match
even if they live deep inside very different global networks.

This script adds a complementary region-level view:

  For each internal node, extract its *fanin cone* to depth D (D = 1, 2, 3).
  Score node pairs by how similar their local cones are, using three signals:
    - root_sim_score      : bit-similarity of the ROOT NODE's simulation signature
                             (the same signature used by analyze_blif_matches.py).
                             Note: this is the global simulation of the root node, not
                             a local re-simulation of the cone in isolation.  The name
                             reflects this: it is the *root* node's similarity score,
                             used as a proxy for how similar the cone's function is.
    - cone_support_jaccard: Jaccard overlap of the sets of primary inputs that
                             actually reach each cone
    - cone_size_sim       : 1 / (1 + |size_a - size_b|)  — penalises
                             cones of very different internal complexity

  The combined region score is:
    0.50 * root_sim_score + 0.40 * cone_support_jaccard + 0.10 * cone_size_sim

  For each (benchmark, optimization, optimized_node, depth) tuple we keep
  the TOP_K_REGION best original-node candidates.

Outputs
-------
  results/region_candidates.csv — per-node-per-depth ranked candidates
  results/region_summary.csv    — per (benchmark, optimization, depth) aggregate
  results/region_summary.md     — Markdown table + interpretation

Usage
-----
  python3 region_correspondence.py          # all benchmarks under variants/
  make region                               # same via Makefile

The script runs without any ABC installation.  It only requires the BLIF
variant files produced by run_abc_variants.sh (and analyze_blif_matches.py's
import of parse / simulate helpers is intentionally avoided to keep this module
self-contained — we re-use only the pure-Python parse/simulate logic here).
"""

import csv
import glob
import os
import random
import statistics
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CONE_DEPTHS = [1, 2, 3]        # shallow cone depths to evaluate
TOP_K_REGION = 5                # top candidates kept per (node, depth)
MAX_EXACT_INPUTS = 12           # threshold below which we do exhaustive simulation
RANDOM_PATTERNS = 4096          # patterns used in random-simulation mode
RANDOM_SEED = 7                 # reproducible random seed

# Weights for the combined region score
W_SIM     = 0.50
W_SUPPORT = 0.40
W_SIZE    = 0.10

CANDIDATES_CSV = "results/region_candidates.csv"
SUMMARY_CSV    = "results/region_summary.csv"
SUMMARY_MD     = "results/region_summary.md"


# ---------------------------------------------------------------------------
# Minimal BLIF data structures (self-contained; not imported from other scripts)
# ---------------------------------------------------------------------------

@dataclass
class _Node:
    output: str
    inputs: list[str]
    cover: list[str]


@dataclass
class _Network:
    inputs: list[str]
    outputs: list[str]
    nodes: list[_Node]
    # Populated after parse: maps output name → _Node
    node_map: dict = field(default_factory=dict, repr=False)


# ---------------------------------------------------------------------------
# BLIF parser
# ---------------------------------------------------------------------------

def _read_logical_lines(path: str) -> list[str]:
    """Read BLIF, joining continuation lines ending in '\\'."""
    logical: list[str] = []
    current = ""
    with open(path, "r", encoding="utf-8") as fh:
        for raw in fh:
            line = raw.strip()
            if not line:
                if current:
                    logical.append(current)
                    current = ""
                continue
            if line.endswith("\\"):
                current += line[:-1].strip() + " "
            else:
                current += line
                logical.append(current.strip())
                current = ""
    if current:
        logical.append(current.strip())
    return logical


def _parse_blif(path: str) -> _Network:
    """Parse a BLIF file, returning a _Network with node_map filled in."""
    lines = _read_logical_lines(path)
    net = _Network(inputs=[], outputs=[], nodes=[])

    i = 0
    while i < len(lines):
        line = lines[i]
        if not line or line.startswith("#"):
            i += 1
            continue

        parts = line.split()
        directive = parts[0]

        if directive == ".inputs":
            net.inputs.extend(parts[1:])
            i += 1
        elif directive == ".outputs":
            net.outputs.extend(parts[1:])
            i += 1
        elif directive == ".names":
            names = parts[1:]
            node_out = names[-1]
            node_ins = names[:-1]
            cover: list[str] = []
            i += 1
            while i < len(lines):
                nl = lines[i]
                if not nl or nl.startswith("#"):
                    i += 1
                    continue
                if nl.startswith("."):
                    break
                cover.append(nl)
                i += 1
            node = _Node(node_out, node_ins, cover)
            net.nodes.append(node)
            net.node_map[node_out] = node
        else:
            i += 1

    return net


# ---------------------------------------------------------------------------
# Simulation helpers
# ---------------------------------------------------------------------------

def _make_input_patterns(
    inputs: list[str],
) -> tuple[dict[str, int], int, int]:
    """
    Build simulation bit-vectors for primary inputs.

    Returns (values_dict, mask, total_patterns).
    For ≤ MAX_EXACT_INPUTS inputs: exact enumeration.
    Otherwise: deterministic random simulation.
    """
    random.seed(RANDOM_SEED)
    values: dict[str, int] = {}

    if len(inputs) <= MAX_EXACT_INPUTS:
        total = 1 << len(inputs)
        for idx, name in enumerate(inputs):
            bits = 0
            for assignment in range(total):
                if (assignment >> idx) & 1:
                    bits |= 1 << assignment
            values[name] = bits
    else:
        total = RANDOM_PATTERNS
        for name in inputs:
            bits = 0
            for p in range(total):
                if random.getrandbits(1):
                    bits |= 1 << p
            values[name] = bits

    mask = (1 << total) - 1
    return values, mask, total


def _eval_cover(node: _Node, values: dict[str, int], mask: int) -> int:
    """Evaluate one .names node as sum-of-products."""
    if not node.inputs:
        for row in node.cover:
            if row.strip() == "1":
                return mask
        return 0

    result = 0
    for row in node.cover:
        parts = row.split()
        pattern = parts[0]
        out_val = parts[1] if len(parts) > 1 else "1"
        if out_val != "1":
            continue
        cube = mask
        for ch, inp in zip(pattern, node.inputs):
            if ch == "1":
                cube &= values[inp]
            elif ch == "0":
                cube &= (~values[inp]) & mask
            # "-" → don't care
        result |= cube
    return result


def _simulate_network(
    net: _Network,
) -> tuple[dict[str, int], int, int]:
    """
    Simulate the full network.

    Returns (values, mask, total_patterns) where values maps every node
    (primary inputs + internal + outputs) to its bit-vector.
    """
    values, mask, total = _make_input_patterns(net.inputs)
    for node in net.nodes:
        values[node.output] = _eval_cover(node, values, mask)
    return values, mask, total


# ---------------------------------------------------------------------------
# Cone extraction
# ---------------------------------------------------------------------------

def _fanin_cone(
    root: str,
    net: _Network,
    depth: int,
) -> tuple[set[str], set[str]]:
    """
    Extract the fanin cone of *root* to at most *depth* levels.

    Returns (cone_nodes, cone_pis) where:
      cone_nodes  — set of internal node names inside the cone (excludes root's
                    primary-input boundary; includes root itself if it is internal)
      cone_pis    — set of primary-input names that feed into the cone boundary
                    (either true primary inputs, or nodes cut off by the depth limit)
    """
    cone_nodes: set[str] = set()
    cone_pis: set[str] = set()
    primary_input_set = set(net.inputs)

    def _recurse(name: str, remaining: int) -> None:
        if name in primary_input_set:
            cone_pis.add(name)
            return
        if name not in net.node_map:
            # Unknown name — treat as PI boundary
            cone_pis.add(name)
            return
        cone_nodes.add(name)
        if remaining == 0:
            # Depth limit reached — fanins become boundary PIs
            for fanin in net.node_map[name].inputs:
                cone_pis.add(fanin)
            return
        for fanin in net.node_map[name].inputs:
            if fanin not in cone_nodes:  # avoid revisiting
                _recurse(fanin, remaining - 1)

    _recurse(root, depth)
    return cone_nodes, cone_pis


def _simulate_cone(
    root: str,
    cone_nodes: set[str],
    cone_pis: set[str],
    net: _Network,
    global_values: dict[str, int],
    mask: int,
) -> int:
    """
    Return the simulation bit-vector for *root* by re-evaluating only the
    nodes inside *cone_nodes*, reading boundary values from *global_values*.

    This is already available in global_values because we simulate the full
    network before cone extraction — we just return the pre-computed value.
    The function exists as a clear named interface for future extension.
    """
    return global_values.get(root, 0)


# ---------------------------------------------------------------------------
# Region scoring
# ---------------------------------------------------------------------------

def _cone_size(cone_nodes: set[str]) -> int:
    """Number of internal nodes in the cone (excluding the boundary PIs)."""
    return len(cone_nodes)


def _bit_sim(sig_a: int, sig_b: int, total: int) -> float:
    """Bit-vector similarity in [0, 1]."""
    if total == 0:
        return 0.0
    diff = sig_a ^ sig_b
    return 1.0 - diff.bit_count() / total


def _jaccard(a: set, b: set) -> float:
    """Jaccard similarity of two sets."""
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def _size_sim(size_a: int, size_b: int) -> float:
    """Penalise cones of very different internal complexity."""
    return 1.0 / (1.0 + abs(size_a - size_b))


def region_score(
    cone_sim: float,
    cone_support: float,
    cone_size: float,
) -> float:
    """Weighted combination of the three region signals."""
    return W_SIM * cone_sim + W_SUPPORT * cone_support + W_SIZE * cone_size


# ---------------------------------------------------------------------------
# Per-benchmark analysis
# ---------------------------------------------------------------------------

@dataclass
class _AnalyzedNet:
    path: str
    net: _Network
    values: dict[str, int]
    mask: int
    total_patterns: int
    internal_nodes: list[str]       # names of non-output internal nodes
    # per node, per depth: (cone_nodes, cone_pis)
    cones: dict[tuple[str, int], tuple[set[str], set[str]]] = field(
        default_factory=dict, repr=False
    )


def _analyze(path: str) -> _AnalyzedNet:
    """Parse, simulate, and pre-compute cones for all depths."""
    net = _parse_blif(path)
    values, mask, total = _simulate_network(net)

    output_set = set(net.outputs)
    internal = [
        node.output for node in net.nodes
        if node.output not in output_set
    ]

    cones: dict[tuple[str, int], tuple[set[str], set[str]]] = {}
    for node_name in internal:
        for depth in CONE_DEPTHS:
            cones[(node_name, depth)] = _fanin_cone(node_name, net, depth)

    return _AnalyzedNet(
        path=path,
        net=net,
        values=values,
        mask=mask,
        total_patterns=total,
        internal_nodes=internal,
        cones=cones,
    )


def _score_pairs(
    orig: _AnalyzedNet,
    opt: _AnalyzedNet,
    benchmark: str,
    optimization: str,
) -> list[dict]:
    """
    For each (optimized_node, depth), score every (original_node) and
    keep the top TOP_K_REGION candidates.

    Returns a flat list of candidate dicts ready to write to CSV.
    """
    total = min(orig.total_patterns, opt.total_patterns)
    rows: list[dict] = []

    for opt_node in opt.internal_nodes:
        opt_sig = opt.values.get(opt_node, 0)

        for depth in CONE_DEPTHS:
            opt_cone_nodes, opt_cone_pis = opt.cones.get((opt_node, depth), (set(), set()))
            opt_size = _cone_size(opt_cone_nodes)

            candidates: list[dict] = []

            for orig_node in orig.internal_nodes:
                orig_sig = orig.values.get(orig_node, 0)
                orig_cone_nodes, orig_cone_pis = orig.cones.get(
                    (orig_node, depth), (set(), set())
                )
                orig_size = _cone_size(orig_cone_nodes)

                c_sim  = _bit_sim(opt_sig, orig_sig, total)
                c_sup  = _jaccard(opt_cone_pis, orig_cone_pis)
                c_sz   = _size_sim(opt_size, orig_size)
                r_score = region_score(c_sim, c_sup, c_sz)

                candidates.append({
                    "benchmark":          benchmark,
                    "optimization":       optimization,
                    "depth":              depth,
                    "optimized_node":     opt_node,
                    "original_candidate": orig_node,
                    "region_score":       r_score,
                    "root_sim_score":     c_sim,
                    "cone_support_jaccard": c_sup,
                    "cone_size_sim":      c_sz,
                    "opt_cone_size":      opt_size,
                    "orig_cone_size":     orig_size,
                    "opt_cone_pis":       len(opt_cone_pis),
                    "orig_cone_pis":      len(orig_cone_pis),
                })

            candidates.sort(key=lambda r: r["region_score"], reverse=True)
            for rank, cand in enumerate(candidates[:TOP_K_REGION], start=1):
                cand["rank"] = rank
                rows.append(cand)

    return rows


# ---------------------------------------------------------------------------
# Summary computation
# ---------------------------------------------------------------------------

def _compute_summary(candidate_rows: list[dict]) -> list[dict]:
    """
    Aggregate candidate_rows into one row per (benchmark, optimization, depth).

    Metrics:
      total_opt_nodes          — distinct optimized nodes at this depth
      avg_rank1_region_score   — mean region_score of the rank-1 candidate
      avg_rank1_cone_sim       — mean root_sim_score of the rank-1 candidate
      avg_rank1_cone_support   — mean cone_support_jaccard at rank 1
      avg_rank1_cone_size_sim  — mean cone_size_sim at rank 1
      pct_rank1_above_0_8      — fraction of rank-1 region_scores ≥ 0.8
    """
    # Group rank-1 rows by (benchmark, optimization, depth)
    groups: dict[tuple, list[dict]] = defaultdict(list)
    for row in candidate_rows:
        if row["rank"] == 1:
            key = (row["benchmark"], row["optimization"], row["depth"])
            groups[key].append(row)

    summary: list[dict] = []
    for (bench, opt, depth), r1_rows in sorted(groups.items()):
        scores    = [r["region_score"]         for r in r1_rows]
        sims      = [r["root_sim_score"]        for r in r1_rows]
        supports  = [r["cone_support_jaccard"]  for r in r1_rows]
        size_sims = [r["cone_size_sim"]         for r in r1_rows]

        n = len(scores)
        summary.append({
            "benchmark":             bench,
            "optimization":          opt,
            "depth":                 depth,
            "total_opt_nodes":       n,
            "avg_rank1_region_score":  statistics.mean(scores)    if scores    else 0.0,
            "avg_rank1_cone_sim":      statistics.mean(sims)      if sims      else 0.0,
            "avg_rank1_cone_support":  statistics.mean(supports)  if supports  else 0.0,
            "avg_rank1_cone_size_sim": statistics.mean(size_sims) if size_sims else 0.0,
            "pct_rank1_above_0_8":     sum(1 for s in scores if s >= 0.8) / n if n else 0.0,
        })

    return summary


# ---------------------------------------------------------------------------
# Markdown report
# ---------------------------------------------------------------------------

def _fmt(val, is_rate: bool = False) -> str:
    if isinstance(val, float):
        return f"{val:.1%}" if is_rate else f"{val:.4f}"
    if isinstance(val, int):
        return str(val)
    return str(val)


def _md_table(rows: list[dict], cols: list[str], rate_cols: set[str]) -> str:
    if not rows:
        return "_No data._"
    header = "| " + " | ".join(cols) + " |"
    sep    = "| " + " | ".join(["---"] * len(cols)) + " |"
    lines  = [header, sep]
    for row in rows:
        cells = [_fmt(row.get(c, ""), c in rate_cols) for c in cols]
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def build_markdown(
    candidate_rows: list[dict],
    summary_rows: list[dict],
    variants_available: bool,
) -> str:
    lines: list[str] = []
    lines.append("# Region Correspondence Baseline\n")

    lines.append("## Data availability\n")
    lines.append(
        f"- BLIF variant files: "
        f"{'✅ loaded' if variants_available else '❌ missing — run `./run_abc_variants.sh`'}\n"
    )

    if not variants_available:
        lines.append("> Cannot compute any metrics without variant BLIF files.\n")
        return "\n".join(lines)

    # ── Config ────────────────────────────────────────────────────────────────
    lines.append("## Configuration\n")
    lines.append(
        f"Cone depths evaluated: **{CONE_DEPTHS}**  \n"
        f"Top-K candidates kept per (node, depth): **{TOP_K_REGION}**  \n"
        f"Region score weights: "
        f"sim={W_SIM}, support={W_SUPPORT}, size={W_SIZE}\n"
    )

    # ── Summary table per depth ───────────────────────────────────────────────
    for depth in CONE_DEPTHS:
        depth_rows = [r for r in summary_rows if r["depth"] == depth]
        lines.append(f"## Depth {depth} — per-(benchmark, optimization) summary\n")
        if not depth_rows:
            lines.append("_No data for this depth._\n")
            continue

        cols = [
            "benchmark", "optimization", "total_opt_nodes",
            "avg_rank1_region_score", "avg_rank1_cone_sim",
            "avg_rank1_cone_support", "avg_rank1_cone_size_sim",
            "pct_rank1_above_0_8",
        ]
        rate_cols = {"pct_rank1_above_0_8"}
        lines.append(_md_table(depth_rows, cols, rate_cols))
        lines.append("")

    # ── Cross-depth comparison ────────────────────────────────────────────────
    lines.append("## Cross-depth comparison (averaged over all benchmark/optimization pairs)\n")
    cross: list[dict] = []
    for depth in CONE_DEPTHS:
        depth_rows = [r for r in summary_rows if r["depth"] == depth]
        if not depth_rows:
            cross.append({
                "depth": depth,
                "avg_rank1_region_score": float("nan"),
                "avg_rank1_cone_sim": float("nan"),
                "avg_rank1_cone_support": float("nan"),
                "pct_rank1_above_0_8": float("nan"),
                "n_groups": 0,
            })
        else:
            scores   = [r["avg_rank1_region_score"] for r in depth_rows]
            sims     = [r["avg_rank1_cone_sim"]     for r in depth_rows]
            supports = [r["avg_rank1_cone_support"]  for r in depth_rows]
            above    = [r["pct_rank1_above_0_8"]    for r in depth_rows]
            cross.append({
                "depth": depth,
                "avg_rank1_region_score": statistics.mean(scores),
                "avg_rank1_cone_sim":     statistics.mean(sims),
                "avg_rank1_cone_support": statistics.mean(supports),
                "pct_rank1_above_0_8":   statistics.mean(above),
                "n_groups": len(depth_rows),
            })

    cross_cols = [
        "depth", "n_groups",
        "avg_rank1_region_score", "avg_rank1_cone_sim",
        "avg_rank1_cone_support", "pct_rank1_above_0_8",
    ]
    lines.append(_md_table(cross, cross_cols, rate_cols={"pct_rank1_above_0_8"}))
    lines.append("")

    # ── Interpretation ────────────────────────────────────────────────────────
    lines.append("## Interpretation\n")
    lines.append(
        "**root_sim_score** — bit-similarity of the root node's output under the global "
        "simulation patterns. Identical to the simulation similarity in `top_candidates.csv`; "
        "included here for direct comparison with the region-specific signals.\n"
    )
    lines.append(
        "**cone_support_jaccard** — Jaccard overlap of the *local* primary-input boundaries "
        "of the two cones.  At depth 1 this is the Jaccard overlap of direct fanins; at "
        "depth 3 it approximates the full support overlap but restricted to inputs reachable "
        "within 3 levels.  Higher depth → more inputs visible → scores converge toward the "
        "global support Jaccard.\n"
    )
    lines.append(
        "**cone_size_sim** — penalises cones of very different internal complexity "
        "(node count).  A value near 1.0 means the two cones have about the same number "
        "of internal gates, regardless of what those gates compute.\n"
    )
    lines.append(
        "**pct_rank1_above_0_8** — fraction of optimized nodes whose best-match region "
        "score ≥ 0.8.  This is a useful single-number quality indicator: a value near 1.0 "
        "means almost every optimized node has a structurally similar original counterpart "
        "within the shallow fanin cone.\n"
    )
    lines.append(
        "**Depth effect** — shallower cones (depth 1) capture only the immediate "
        "gate-level structure; deeper cones (depth 3) increasingly resemble the global "
        "support-based matching.  A benchmark where depth-1 scores are already high has "
        "very locally stable structure across optimizations; one where scores only improve "
        "at depth 3 has more global restructuring.\n"
    )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# File I/O helpers
# ---------------------------------------------------------------------------

def _write_csv(path: str, rows: list[dict], fieldnames: list[str]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in fieldnames})


def _group_variant_files() -> dict[str, dict[str, str]]:
    """
    Return {benchmark: {optimization: path}} from variants/*.blif.
    Identical logic to analyze_blif_matches.py's group_variant_files().
    """
    known_opts = [
        "resyn2_like", "compress2rs", "refactor_z", "rewrite_z",
        "resyn2", "resyn", "dc2",
        "original", "balance", "rewrite", "refactor", "resub",
    ]
    grouped: dict[str, dict[str, str]] = defaultdict(dict)
    for path in sorted(glob.glob("variants/*.blif")):
        filename = os.path.basename(path).replace(".blif", "")
        for opt in known_opts:
            if filename.endswith("_" + opt):
                benchmark = filename[: -(len(opt) + 1)]
                grouped[benchmark][opt] = path
                break
    return grouped


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

CANDIDATE_FIELDS = [
    "benchmark", "optimization", "depth",
    "optimized_node", "rank", "original_candidate",
    "region_score", "root_sim_score", "cone_support_jaccard", "cone_size_sim",
    "opt_cone_size", "orig_cone_size", "opt_cone_pis", "orig_cone_pis",
]

SUMMARY_FIELDS = [
    "benchmark", "optimization", "depth", "total_opt_nodes",
    "avg_rank1_region_score", "avg_rank1_cone_sim",
    "avg_rank1_cone_support", "avg_rank1_cone_size_sim",
    "pct_rank1_above_0_8",
]


def main() -> None:
    os.makedirs("results", exist_ok=True)

    grouped = _group_variant_files()

    if not grouped:
        print(
            "No BLIF variant files found under variants/.  "
            "Run ./run_abc_variants.sh first."
        )
        md = build_markdown([], [], variants_available=False)
        with open(SUMMARY_MD, "w", encoding="utf-8") as fh:
            fh.write(md)
        print(f"Wrote {SUMMARY_MD} (no-data placeholder).")
        return

    all_candidates: list[dict] = []

    for benchmark, files in sorted(grouped.items()):
        if "original" not in files:
            print(f"Skipping {benchmark}: no original variant.")
            continue

        print(f"\n{'=' * 70}")
        print(f"Benchmark: {benchmark}")
        print("=" * 70)

        try:
            orig_net = _analyze(files["original"])
        except Exception as exc:
            print(f"  ERROR parsing original: {exc}")
            continue

        for optimization, path in sorted(files.items()):
            if optimization == "original":
                continue

            try:
                opt_net = _analyze(path)
            except Exception as exc:
                print(f"  ERROR parsing {optimization}: {exc}")
                continue

            pairs = _score_pairs(orig_net, opt_net, benchmark, optimization)
            all_candidates.extend(pairs)

            # Quick per-optimization console summary
            for depth in CONE_DEPTHS:
                r1 = [p for p in pairs if p["rank"] == 1 and p["depth"] == depth]
                if r1:
                    avg = statistics.mean(p["region_score"] for p in r1)
                    print(
                        f"  {optimization:20s}  depth={depth}"
                        f"  nodes={len(r1):3d}"
                        f"  avg_rank1_score={avg:.3f}"
                    )

    summary_rows = _compute_summary(all_candidates)
    md_text = build_markdown(all_candidates, summary_rows, variants_available=True)

    _write_csv(CANDIDATES_CSV, all_candidates, CANDIDATE_FIELDS)
    _write_csv(SUMMARY_CSV, summary_rows, SUMMARY_FIELDS)
    with open(SUMMARY_MD, "w", encoding="utf-8") as fh:
        fh.write(md_text)

    print(f"\nSaved:")
    print(f"  {CANDIDATES_CSV}  ({len(all_candidates)} rows)")
    print(f"  {SUMMARY_CSV}  ({len(summary_rows)} rows)")
    print(f"  {SUMMARY_MD}")


if __name__ == "__main__":
    main()
