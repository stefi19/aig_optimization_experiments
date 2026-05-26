"""
ablation_study.py

Re-scores the top-candidates list under six alternative weighting schemes to
quantify how much each individual signal (simulation, support, depth) contributes
to ranking quality.

Input files (both optional — the script degrades gracefully when missing):
  results/top_candidates.csv       — full ranked candidate list
  results/sat_verified_candidates.csv — ABC verdicts (needed for quality metrics)

Output files:
  results/ablation_summary.csv  — one row per (config, benchmark, optimization)
  results/ablation_summary.md   — human-readable Markdown report

Scoring configurations evaluated
---------------------------------
Each config is a (w_sim, w_support, w_depth) triple; they must sum to 1.0.

  baseline   0.55  0.35  0.10  — production weights from analyze_blif_matches.py
  sim_only   1.00  0.00  0.00  — pure simulation similarity
  support_only 0.00 1.00 0.00  — pure support (structural) overlap
  depth_only 0.00  0.00  1.00  — pure logic-depth proximity
  sim_sup    0.50  0.50  0.00  — simulation + support, no depth
  sim_dep    0.70  0.00  0.30  — simulation + depth, no support

Quality metrics (require SAT data):
  rank1_precision   — fraction of rank-1 candidates (under this config) that
                      are ABC-verified
  mrr               — Mean Reciprocal Rank of the first verified candidate per node

Simulation-only metrics (always available):
  avg_rank1_score   — mean re-scored combined_score at rank 1
  rank1_consistency — fraction of nodes whose rank-1 choice agrees with baseline

Graceful degradation
--------------------
- If top_candidates.csv is missing: writes empty outputs with a clear message.
- If sat_verified_candidates.csv is missing: quality columns filled with NaN.

Usage:
  python3 ablation_study.py
"""

import os
import sys
from dataclasses import dataclass

import pandas as pd

# ── Configuration ──────────────────────────────────────────────────────────────

CANDIDATES_CSV = os.path.join("results", "top_candidates.csv")
VERIFIED_CSV   = os.path.join("results", "sat_verified_candidates.csv")
OUTPUT_CSV     = os.path.join("results", "ablation_summary.csv")
OUTPUT_MD      = os.path.join("results", "ablation_summary.md")


@dataclass(frozen=True)
class ScoringConfig:
    name:      str
    w_sim:     float
    w_support: float
    w_depth:   float

    def score(self, sim: float, support: float, depth: float) -> float:
        return self.w_sim * sim + self.w_support * support + self.w_depth * depth

    def label(self) -> str:
        return (
            f"sim={self.w_sim:.2f} sup={self.w_support:.2f} dep={self.w_depth:.2f}"
        )


CONFIGS: list[ScoringConfig] = [
    ScoringConfig("baseline",     0.55, 0.35, 0.10),
    ScoringConfig("sim_only",     1.00, 0.00, 0.00),
    ScoringConfig("support_only", 0.00, 1.00, 0.00),
    ScoringConfig("depth_only",   0.00, 0.00, 1.00),
    ScoringConfig("sim_sup",      0.50, 0.50, 0.00),
    ScoringConfig("sim_dep",      0.70, 0.00, 0.30),
]

# ── Data loading ───────────────────────────────────────────────────────────────

def load_candidates(path: str) -> pd.DataFrame | None:
    if not os.path.exists(path):
        return None
    df = pd.read_csv(path)
    required = {
        "benchmark", "optimization", "optimized_node",
        "original_candidate", "rank", "combined_score",
        "simulation_similarity", "support_overlap", "depth_similarity",
    }
    if not required.issubset(df.columns):
        print(
            f"WARNING: {path} is missing required columns "
            f"({required - set(df.columns)}). Re-run analyze_blif_matches.py.",
            file=sys.stderr,
        )
        return None
    return df


def load_verified(path: str) -> pd.DataFrame | None:
    if not os.path.exists(path):
        return None
    df = pd.read_csv(path)
    required = {"benchmark", "optimization", "optimized_node",
                "original_candidate", "sat_status"}
    if not required.issubset(df.columns):
        return None
    return df


# ── Re-ranking ─────────────────────────────────────────────────────────────────

def rerank_with_config(df: pd.DataFrame, cfg: ScoringConfig) -> pd.DataFrame:
    """
    Add a 'new_score' column and recompute 'new_rank' for each optimized node
    under the given scoring configuration.

    The output DataFrame has all original columns plus:
      new_score  — re-scored combined score under cfg
      new_rank   — rank within the node's candidate list (1 = best)
    """
    df = df.copy()
    df["new_score"] = (
        cfg.w_sim     * df["simulation_similarity"]
        + cfg.w_support * df["support_overlap"]
        + cfg.w_depth   * df["depth_similarity"]
    )

    # Compute new_rank per (benchmark, optimization, optimized_node).
    df["new_rank"] = (
        df.groupby(["benchmark", "optimization", "optimized_node"])["new_score"]
        .rank(method="first", ascending=False)
        .astype(int)
    )

    return df


# ── Group metrics ──────────────────────────────────────────────────────────────

def compute_group_metrics(
    group: pd.DataFrame,         # rows for one (benchmark, opt) pair, re-ranked
    baseline_rank1: dict[str, str],   # {optimized_node: original_candidate} at baseline rank-1
    verified_set: set | None,
    bench: str,
    opt: str,
) -> dict:
    """
    Compute ablation metrics for one (benchmark, optimization) group under one config.

    baseline_rank1
        The rank-1 choices under the baseline config for this group, used to
        compute rank1_consistency.
    """
    # Rank-1 rows under this config.
    rank1 = group[group["new_rank"] == 1]
    total_nodes = group["optimized_node"].nunique()

    avg_rank1_score = float(rank1["new_score"].mean()) if len(rank1) else float("nan")

    # rank1_consistency: fraction of nodes where this config's rank-1 == baseline rank-1.
    consistent = 0
    for node, cand in zip(rank1["optimized_node"], rank1["original_candidate"]):
        if baseline_rank1.get(node) == cand:
            consistent += 1
    rank1_consistency = consistent / total_nodes if total_nodes else float("nan")

    if verified_set is None:
        return {
            "total_nodes":       total_nodes,
            "avg_rank1_score":   avg_rank1_score,
            "rank1_consistency": rank1_consistency,
            "rank1_precision":   float("nan"),
            "mrr":               float("nan"),
        }

    # rank1_precision: fraction of rank-1 candidates that are ABC-verified.
    verified_at_1 = 0
    for _, row in rank1.iterrows():
        key = (bench, opt, row["optimized_node"], row["original_candidate"])
        if key in verified_set:
            verified_at_1 += 1
    rank1_precision = verified_at_1 / len(rank1) if len(rank1) else float("nan")

    # MRR: for each node, reciprocal rank of the first verified candidate.
    rr_list: list[float] = []
    for node, node_group in group.groupby("optimized_node"):
        node_sorted = node_group.sort_values("new_rank")
        for _, row in node_sorted.iterrows():
            key = (bench, opt, node, row["original_candidate"])
            if key in verified_set:
                rr_list.append(1.0 / row["new_rank"])
                break
    mrr = sum(rr_list) / total_nodes if total_nodes else float("nan")

    return {
        "total_nodes":       total_nodes,
        "avg_rank1_score":   avg_rank1_score,
        "rank1_consistency": rank1_consistency,
        "rank1_precision":   rank1_precision,
        "mrr":               mrr,
    }


def compute_ablation_table(
    candidates: pd.DataFrame,
    verified_set: set | None,
    configs: list[ScoringConfig],
) -> pd.DataFrame:
    """
    Return a DataFrame with one row per (config_name, benchmark, optimization).
    """
    # Pre-compute baseline rank-1 choices per (benchmark, optimization, node).
    baseline_cfg = next(c for c in configs if c.name == "baseline")
    baseline_reranked = rerank_with_config(candidates, baseline_cfg)
    baseline_rank1: dict[tuple[str, str], dict[str, str]] = {}
    for (bench, opt), grp in baseline_reranked.groupby(["benchmark", "optimization"]):
        r1 = grp[grp["new_rank"] == 1]
        baseline_rank1[(bench, opt)] = dict(
            zip(r1["optimized_node"], r1["original_candidate"])
        )

    rows = []
    for cfg in configs:
        reranked = rerank_with_config(candidates, cfg)
        for (bench, opt), group in reranked.groupby(
            ["benchmark", "optimization"], sort=True
        ):
            metrics = compute_group_metrics(
                group,
                baseline_rank1.get((bench, opt), {}),
                verified_set,
                bench,
                opt,
            )
            rows.append({
                "config":       cfg.name,
                "weights":      cfg.label(),
                "benchmark":    bench,
                "optimization": opt,
                **metrics,
            })

    cols = [
        "config", "weights", "benchmark", "optimization",
        "total_nodes", "avg_rank1_score", "rank1_consistency",
        "rank1_precision", "mrr",
    ]
    if not rows:
        return pd.DataFrame(columns=cols)
    return pd.DataFrame(rows, columns=cols)


# ── Config-level rollup ────────────────────────────────────────────────────────

def rollup_by_config(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate ablation_summary rows to one row per config (global averages).
    """
    if df.empty:
        return pd.DataFrame(columns=[
            "config", "weights", "avg_rank1_score",
            "rank1_consistency", "rank1_precision", "mrr",
        ])

    agg = (
        df.groupby(["config", "weights"], sort=False)
        .agg(
            avg_rank1_score   =("avg_rank1_score",   "mean"),
            rank1_consistency =("rank1_consistency", "mean"),
            rank1_precision   =("rank1_precision",   "mean"),
            mrr               =("mrr",               "mean"),
        )
        .reset_index()
    )
    # Preserve declaration order of configs.
    config_order = [c.name for c in CONFIGS]
    agg["_order"] = agg["config"].map({n: i for i, n in enumerate(config_order)})
    return agg.sort_values("_order").drop(columns=["_order"]).reset_index(drop=True)


# ── Markdown report ────────────────────────────────────────────────────────────

def _fmt(val, is_rate: bool = False) -> str:
    if pd.isna(val):
        return "n/a"
    if isinstance(val, float):
        if is_rate:
            return f"{val:.1%}"
        return f"{val:.4f}"
    if isinstance(val, int):
        return str(val)
    return str(val)


def _md_table(df: pd.DataFrame, rate_cols: set[str] | None = None) -> str:
    if df.empty:
        return "_No data._"
    rc = rate_cols or set()
    headers = list(df.columns)
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for _, row in df.iterrows():
        cells = [_fmt(row[c], c in rc) for c in headers]
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def build_markdown(
    ablation_df: pd.DataFrame,
    rollup_df: pd.DataFrame,
    candidates_available: bool,
    verified_available: bool,
) -> str:
    lines: list[str] = []
    lines.append("# Ablation Study: Scoring Weight Sensitivity\n")

    lines.append("## Data availability\n")
    lines.append(
        f"- `top_candidates.csv`: "
        f"{'✅ loaded' if candidates_available else '❌ missing — run `analyze_blif_matches.py`'}"
    )
    lines.append(
        f"- `sat_verified_candidates.csv`: "
        f"{'✅ loaded' if verified_available else '❌ missing — run `sat_refinement_abc.py`'}\n"
    )
    if not candidates_available:
        lines.append("> Cannot compute any metrics without `top_candidates.csv`.\n")
        return "\n".join(lines)

    if not verified_available:
        lines.append(
            "> `rank1_precision` and `mrr` require SAT results and are shown as **n/a**.\n"
        )

    # ── Scoring configs ───────────────────────────────────────────────────────
    lines.append("## Scoring configurations\n")
    cfg_rows = [{"config": c.name, "w_sim": c.w_sim,
                 "w_support": c.w_support, "w_depth": c.w_depth}
                for c in CONFIGS]
    cfg_df = pd.DataFrame(cfg_rows)
    lines.append(_md_table(cfg_df))
    lines.append("")

    # ── Global rollup ─────────────────────────────────────────────────────────
    lines.append("## Global summary (averaged over all benchmark/optimization pairs)\n")
    lines.append(_md_table(
        rollup_df,
        rate_cols={"rank1_consistency", "rank1_precision"},
    ))
    lines.append("")

    # ── Per-group detail ──────────────────────────────────────────────────────
    lines.append("## Per-group detail\n")
    rate_cols = {"rank1_consistency", "rank1_precision"}
    lines.append(_md_table(ablation_df, rate_cols=rate_cols))
    lines.append("")

    # ── Interpretation ────────────────────────────────────────────────────────
    lines.append("## Interpretation\n")
    lines.append(
        "**avg_rank1_score** — mean re-scored value of the rank-1 candidate under "
        "each config. A higher score does not necessarily mean better ranking quality; "
        "configs that use fewer signals can achieve artificially high scores if that "
        "signal happens to be large for all nodes.\n"
    )
    lines.append(
        "**rank1_consistency** — fraction of nodes where this config's rank-1 choice "
        "agrees with the baseline (0.55/0.35/0.10) choice. "
        "A value near 1.0 means removing or down-weighting this signal does not "
        "change the top candidate; a low value means that signal is a decisive "
        "tie-breaker.\n"
    )
    lines.append(
        "**rank1_precision** — fraction of rank-1 candidates that were formally "
        "verified by ABC. The config with the highest precision places the correct "
        "match at rank 1 most often.\n"
    )
    lines.append(
        "**mrr** (Mean Reciprocal Rank) — how high the first verified match appears "
        "on average. MRR=1.0 means verified matches were always rank 1.\n"
    )
    if not verified_available:
        lines.append(
            "> To compute rank1_precision and MRR, first run the SAT pipeline:\n"
            "> ```\n"
            "> python3 sat_refinement_placeholder.py\n"
            "> ABC=/path/to/abc python3 sat_refinement_abc.py\n"
            "> ```\n"
        )

    return "\n".join(lines)


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    os.makedirs("results", exist_ok=True)

    candidates = load_candidates(CANDIDATES_CSV)
    verified_df = load_verified(VERIFIED_CSV)

    candidates_available = candidates is not None
    verified_available   = verified_df is not None

    if not candidates_available:
        print(
            f"WARNING: {CANDIDATES_CSV} not found.\n"
            "  Run analyze_blif_matches.py first.\n"
            "  Writing empty output files."
        )
        ablation_df = pd.DataFrame(columns=[
            "config", "weights", "benchmark", "optimization",
            "total_nodes", "avg_rank1_score", "rank1_consistency",
            "rank1_precision", "mrr",
        ])
        rollup_df = rollup_by_config(ablation_df)
    else:
        print(f"Loaded {len(candidates)} candidate rows from {CANDIDATES_CSV}")

        verified_set = None
        if verified_available:
            from evaluate_topk_recovery import build_verified_set
            verified_set = build_verified_set(verified_df)
            print(
                f"Loaded {len(verified_df)} SAT rows "
                f"({len(verified_set)} verified pairs)"
            )
        else:
            print(
                f"Note: {VERIFIED_CSV} not found — "
                "rank1_precision and MRR will be n/a."
            )

        ablation_df = compute_ablation_table(candidates, verified_set, CONFIGS)
        rollup_df   = rollup_by_config(ablation_df)

    # Write outputs.
    ablation_df.to_csv(OUTPUT_CSV, index=False)
    print(f"\nWrote {OUTPUT_CSV}")

    md = build_markdown(ablation_df, rollup_df, candidates_available, verified_available)
    with open(OUTPUT_MD, "w") as fh:
        fh.write(md)
    print(f"Wrote {OUTPUT_MD}")

    # Print the rollup table inline.
    if not rollup_df.empty:
        print("\nGlobal ablation rollup:")
        rate_cols = {"rank1_consistency", "rank1_precision"}
        col_w = 18
        header = "  " + "  ".join(f"{c:<{col_w}}" for c in rollup_df.columns)
        print(header)
        for _, row in rollup_df.iterrows():
            cells = [
                _fmt(row[c], c in rate_cols)
                for c in rollup_df.columns
            ]
            print("  " + "  ".join(f"{v:<{col_w}}" for v in cells))


if __name__ == "__main__":
    main()
