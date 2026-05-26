"""
research_plots.py — Generate research-quality matplotlib PNG plots for AIG
optimization experiments.

Plots produced (all written to results/plots/):
  1. exact_match_rate.png        — exact internal match rate per benchmark/opt
                                   (denominator = optimized_nodes, consistent with
                                   analyze_blif_matches.py)
  2. support_overlap_dist.png    — distribution of avg_best_support_overlap
  3. node_reduction.png          — original vs optimised node counts (grouped bar)
  4. level_reduction.png         — original vs optimised level counts (grouped bar)
  5. sat_status.png              — stacked bar: verified / rejected / inconclusive
  6. topk_recovery.png           — avg_score_at_1 by benchmark (bar)
  7. ablation_comparison.png     — MRR / rank1_consistency per scoring config
  8. region_scores.png           — avg rank-1 region score by depth (line)

Each plot function returns the output path so callers can log/test.
Missing optional input files are skipped gracefully (warning printed, no crash).
"""

from __future__ import annotations

import os
import warnings
from pathlib import Path
from typing import Optional

import matplotlib
matplotlib.use("Agg")  # headless — no display required
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import pandas as pd

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

RESULTS_DIR = Path("results")
PLOTS_DIR = RESULTS_DIR / "plots"

# Input CSVs — keyed by short name for graceful-skip logic
CSV = {
    "summary":         RESULTS_DIR / "summary_metrics.csv",
    "top_candidates":  RESULTS_DIR / "top_candidates.csv",
    "sat_summary":     RESULTS_DIR / "sat_summary.csv",
    "topk_recovery":   RESULTS_DIR / "topk_recovery.csv",
    "ablation":        RESULTS_DIR / "ablation_summary.csv",
    "region_summary":  RESULTS_DIR / "region_summary.csv",
    "cegar":           RESULTS_DIR / "cegar_refined_candidates.csv",
}

# Colour palette (colour-blind friendly, Okabe-Ito inspired)
PALETTE = [
    "#E69F00", "#56B4E9", "#009E73", "#F0E442",
    "#0072B2", "#D55E00", "#CC79A7", "#999999",
]

OPT_ORDER = ["balance", "refactor", "resub", "resyn2_like", "rewrite"]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _ensure_plots_dir() -> None:
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)


def _load(key: str) -> Optional[pd.DataFrame]:
    """Load a CSV by key; return None (with warning) if file is absent."""
    path = CSV[key]
    if not path.exists():
        warnings.warn(f"[research_plots] optional file not found, skipping: {path}")
        return None
    return pd.read_csv(path)


def _save(fig: plt.Figure, name: str) -> str:
    """Save figure to PLOTS_DIR/<name>, close it, return output path string."""
    _ensure_plots_dir()
    out = str(PLOTS_DIR / name)
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return out


def _benchmarks(df: pd.DataFrame) -> list[str]:
    return sorted(df["benchmark"].unique())


def _opt_labels(optimizations: list[str]) -> list[str]:
    """Return optimizations in canonical order, any extras appended."""
    ordered = [o for o in OPT_ORDER if o in optimizations]
    extras = [o for o in optimizations if o not in ordered]
    return ordered + extras


# ---------------------------------------------------------------------------
# 1. Exact match rate
# ---------------------------------------------------------------------------

def plot_exact_match_rate() -> Optional[str]:
    """Bar chart of exact internal match rate per benchmark × opt.

    Uses the pre-computed 'exact_match_rate' column from summary_metrics.csv if
    present (it is computed as exact_internal_matches / optimized_nodes by
    analyze_blif_matches.py).  Falls back to recomputing with the same denominator
    (optimized_nodes) so the chart is always consistent with the analysis script.
    We deliberately do NOT divide by original_nodes because the denominator should
    be the set of nodes we are trying to match — the optimized ones.
    """
    df = _load("summary")
    if df is None:
        return None

    df = df.copy()
    if "exact_match_rate" in df.columns:
        # Use the pre-computed column — already exact_internal_matches / optimized_nodes
        pass
    else:
        # Fallback: compute on the fly with the same denominator
        df["exact_match_rate"] = (
            df["exact_internal_matches"]
            / df["optimized_nodes"].replace(0, float("nan"))
        )

    benchmarks = _benchmarks(df)
    opts = _opt_labels(df["optimization"].unique().tolist())
    n_opts = len(opts)
    x = range(len(benchmarks))
    width = 0.8 / n_opts

    fig, ax = plt.subplots(figsize=(9, 5))
    for i, opt in enumerate(opts):
        sub = df[df["optimization"] == opt]
        rates = [
            sub.loc[sub["benchmark"] == bm, "exact_match_rate"].values[0]
            if bm in sub["benchmark"].values else float("nan")
            for bm in benchmarks
        ]
        offsets = [xi + (i - n_opts / 2 + 0.5) * width for xi in x]
        ax.bar(offsets, rates, width=width * 0.9,
               color=PALETTE[i % len(PALETTE)], label=opt)

    ax.set_xticks(list(x))
    ax.set_xticklabels(benchmarks, rotation=15, ha="right")
    ax.set_ylabel("Exact Match Rate")
    ax.set_title("Exact Internal Match Rate by Benchmark & Optimization")
    ax.yaxis.set_major_formatter(mticker.PercentFormatter(xmax=1))
    ax.set_ylim(0, 1.1)
    ax.legend(title="Optimization", bbox_to_anchor=(1.01, 1), loc="upper left")
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    fig.tight_layout()
    return _save(fig, "exact_match_rate.png")


# ---------------------------------------------------------------------------
# 2. Support overlap distribution
# ---------------------------------------------------------------------------

def plot_support_overlap_dist() -> Optional[str]:
    """Histogram of support_overlap values across all rank-1 top candidates."""
    df = _load("top_candidates")
    if df is None:
        return None

    rank1 = df[df["rank"] == 1]["support_overlap"].dropna()
    if rank1.empty:
        warnings.warn("[research_plots] no rank-1 rows in top_candidates.csv — skipping support overlap plot")
        return None

    fig, ax = plt.subplots(figsize=(7, 4))
    ax.hist(rank1, bins=20, color=PALETTE[1], edgecolor="white", linewidth=0.6)
    ax.axvline(rank1.mean(), color=PALETTE[5], linestyle="--", linewidth=1.5,
               label=f"mean = {rank1.mean():.3f}")
    ax.set_xlabel("Support Overlap (rank-1 candidates)")
    ax.set_ylabel("Count")
    ax.set_title("Distribution of Support Overlap — Rank-1 Candidates")
    ax.legend()
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    fig.tight_layout()
    return _save(fig, "support_overlap_dist.png")


# ---------------------------------------------------------------------------
# 3. Node reduction
# ---------------------------------------------------------------------------

def plot_node_reduction() -> Optional[str]:
    """Grouped bar: original vs optimised node count per benchmark × opt."""
    df = _load("summary")
    if df is None:
        return None

    benchmarks = _benchmarks(df)
    opts = _opt_labels(df["optimization"].unique().tolist())
    n_opts = len(opts)
    x = range(len(benchmarks))
    group_width = 0.85
    bar_width = group_width / (2 * n_opts)

    fig, ax = plt.subplots(figsize=(10, 5))
    for i, opt in enumerate(opts):
        sub = df[df["optimization"] == opt]
        orig = [sub.loc[sub["benchmark"] == bm, "original_nodes"].values[0]
                if bm in sub["benchmark"].values else float("nan") for bm in benchmarks]
        opt_nodes = [sub.loc[sub["benchmark"] == bm, "optimized_nodes"].values[0]
                     if bm in sub["benchmark"].values else float("nan") for bm in benchmarks]
        base_offset = (i - n_opts / 2 + 0.5) * 2 * bar_width
        ax.bar([xi + base_offset - bar_width / 2 for xi in x], orig,
               width=bar_width * 0.9, color=PALETTE[i % len(PALETTE)],
               alpha=0.5, label=f"{opt} (orig)")
        ax.bar([xi + base_offset + bar_width / 2 for xi in x], opt_nodes,
               width=bar_width * 0.9, color=PALETTE[i % len(PALETTE)],
               alpha=1.0, label=f"{opt} (opt)")

    ax.set_xticks(list(x))
    ax.set_xticklabels(benchmarks, rotation=15, ha="right")
    ax.set_ylabel("Node Count")
    ax.set_title("Node Count: Original (light) vs Optimised (solid) by Benchmark & Optimization")
    ax.legend(title="Optimization", bbox_to_anchor=(1.01, 1), loc="upper left",
              fontsize=7, ncol=2)
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    fig.tight_layout()
    return _save(fig, "node_reduction.png")


# ---------------------------------------------------------------------------
# 4. Level reduction
# ---------------------------------------------------------------------------

def plot_level_reduction() -> Optional[str]:
    """Grouped bar: original vs optimised level count per benchmark × opt."""
    df = _load("summary")
    if df is None:
        return None

    benchmarks = _benchmarks(df)
    opts = _opt_labels(df["optimization"].unique().tolist())
    n_opts = len(opts)
    x = range(len(benchmarks))
    group_width = 0.85
    bar_width = group_width / (2 * n_opts)

    fig, ax = plt.subplots(figsize=(10, 5))
    for i, opt in enumerate(opts):
        sub = df[df["optimization"] == opt]
        orig_lvl = [sub.loc[sub["benchmark"] == bm, "original_levels"].values[0]
                    if bm in sub["benchmark"].values else float("nan") for bm in benchmarks]
        opt_lvl = [sub.loc[sub["benchmark"] == bm, "optimized_levels"].values[0]
                   if bm in sub["benchmark"].values else float("nan") for bm in benchmarks]
        base_offset = (i - n_opts / 2 + 0.5) * 2 * bar_width
        ax.bar([xi + base_offset - bar_width / 2 for xi in x], orig_lvl,
               width=bar_width * 0.9, color=PALETTE[i % len(PALETTE)],
               alpha=0.5, label=f"{opt} (orig)")
        ax.bar([xi + base_offset + bar_width / 2 for xi in x], opt_lvl,
               width=bar_width * 0.9, color=PALETTE[i % len(PALETTE)],
               alpha=1.0, label=f"{opt} (opt)")

    ax.set_xticks(list(x))
    ax.set_xticklabels(benchmarks, rotation=15, ha="right")
    ax.set_ylabel("Level Count")
    ax.set_title("Level Count: Original (light) vs Optimised (solid) by Benchmark & Optimization")
    ax.legend(title="Optimization", bbox_to_anchor=(1.01, 1), loc="upper left",
              fontsize=7, ncol=2)
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    fig.tight_layout()
    return _save(fig, "level_reduction.png")


# ---------------------------------------------------------------------------
# 5. SAT status
# ---------------------------------------------------------------------------

def plot_sat_status() -> Optional[str]:
    """Stacked bar: verified / rejected / inconclusive counts per benchmark × opt."""
    df = _load("sat_summary")
    if df is None:
        return None

    # Drop the summary ALL row if present
    df = df[df["benchmark"] != "ALL"].copy()

    benchmarks = _benchmarks(df)
    opts = _opt_labels(df["optimization"].unique().tolist())
    n_opts = len(opts)
    x = range(len(benchmarks))
    width = 0.8 / n_opts

    status_cols = ["verified", "rejected", "inconclusive"]
    status_colors = [PALETTE[2], PALETTE[5], PALETTE[7]]

    fig, ax = plt.subplots(figsize=(10, 5))
    for i, opt in enumerate(opts):
        sub = df[df["optimization"] == opt]
        bottoms = [0.0] * len(benchmarks)
        for sc, color in zip(status_cols, status_colors):
            vals = [
                float(sub.loc[sub["benchmark"] == bm, sc].values[0])
                if bm in sub["benchmark"].values else 0.0
                for bm in benchmarks
            ]
            offsets = [xi + (i - n_opts / 2 + 0.5) * width for xi in x]
            ax.bar(offsets, vals, width=width * 0.9, bottom=bottoms,
                   color=color, label=sc if i == 0 else "_nolegend_")
            bottoms = [b + v for b, v in zip(bottoms, vals)]
        # Print opt label below bars
        for xi, bm in zip(x, benchmarks):
            offset = xi + (i - n_opts / 2 + 0.5) * width
            ax.text(offset, -0.3, opt[:3], ha="center", va="top",
                    fontsize=6, rotation=45)

    ax.set_xticks(list(x))
    ax.set_xticklabels(benchmarks, rotation=15, ha="right")
    ax.set_ylabel("Candidate Count")
    ax.set_title("SAT Verification Status by Benchmark & Optimization")
    ax.legend(title="Status", loc="upper right")
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    fig.tight_layout()
    return _save(fig, "sat_status.png")


# ---------------------------------------------------------------------------
# 6. Top-K recovery
# ---------------------------------------------------------------------------

def plot_topk_recovery() -> Optional[str]:
    """Bar chart of avg_score_at_1 per benchmark (averaged across optimizations)."""
    df = _load("topk_recovery")
    if df is None:
        return None

    # avg_score_at_1 is constant across k rows — take k=1 rows to avoid duplicates
    k1 = df[df["k"] == 1].copy()
    if k1.empty:
        warnings.warn("[research_plots] no k=1 rows in topk_recovery.csv — skipping topk plot")
        return None

    # Mean avg_score_at_1 per benchmark
    grouped = k1.groupby("benchmark")["avg_score_at_1"].mean().reset_index()
    grouped = grouped.sort_values("benchmark")

    fig, ax = plt.subplots(figsize=(7, 4))
    bars = ax.bar(grouped["benchmark"], grouped["avg_score_at_1"],
                  color=PALETTE[:len(grouped)], edgecolor="white")
    for bar, val in zip(bars, grouped["avg_score_at_1"]):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.01,
                f"{val:.3f}", ha="center", va="bottom", fontsize=9)
    ax.set_xlabel("Benchmark")
    ax.set_ylabel("Avg Score @ Rank-1")
    ax.set_title("Top-K Recovery — Average Score at Rank-1 by Benchmark")
    ax.set_ylim(0, 1.15)
    ax.yaxis.set_major_formatter(mticker.PercentFormatter(xmax=1))
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    fig.tight_layout()
    return _save(fig, "topk_recovery.png")


# ---------------------------------------------------------------------------
# 7. Ablation comparison
# ---------------------------------------------------------------------------

def plot_ablation_comparison() -> Optional[str]:
    """Grouped bar: avg rank1_consistency and avg MRR per scoring config."""
    df = _load("ablation")
    if df is None:
        return None

    needed = {"config", "rank1_consistency"}
    if not needed.issubset(df.columns):
        warnings.warn(f"[research_plots] ablation CSV missing columns {needed - set(df.columns)} — skipping")
        return None

    configs = df["config"].unique().tolist()
    has_mrr = "mrr" in df.columns

    metrics: list[tuple[str, str]] = [("rank1_consistency", PALETTE[0])]
    if has_mrr and df["mrr"].notna().any():
        metrics.append(("mrr", PALETTE[1]))

    n_metrics = len(metrics)
    x = range(len(configs))
    width = 0.8 / n_metrics

    fig, ax = plt.subplots(figsize=(9, 5))
    for i, (metric, color) in enumerate(metrics):
        vals = df.groupby("config")[metric].mean().reindex(configs).tolist()
        offsets = [xi + (i - n_metrics / 2 + 0.5) * width for xi in x]
        ax.bar(offsets, vals, width=width * 0.9, color=color, label=metric)

    ax.set_xticks(list(x))
    ax.set_xticklabels(configs, rotation=20, ha="right")
    ax.set_ylabel("Score (mean across benchmarks × optimizations)")
    ax.set_title("Ablation Study — Rank-1 Consistency & MRR per Scoring Config")
    ax.set_ylim(0, 1.1)
    ax.legend()
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    fig.tight_layout()
    return _save(fig, "ablation_comparison.png")


# ---------------------------------------------------------------------------
# 8. Region scores
# ---------------------------------------------------------------------------

def plot_region_scores() -> Optional[str]:
    """Line plot: avg rank-1 region score by fanin-cone depth, per benchmark."""
    df = _load("region_summary")
    if df is None:
        return None

    benchmarks = _benchmarks(df)
    depths = sorted(df["depth"].unique())

    fig, ax = plt.subplots(figsize=(7, 4))
    for i, bm in enumerate(benchmarks):
        sub = df[df["benchmark"] == bm]
        # Mean over optimizations for each depth
        means = sub.groupby("depth")["avg_rank1_region_score"].mean()
        ax.plot(means.index, means.values, marker="o",
                color=PALETTE[i % len(PALETTE)], label=bm, linewidth=1.8)

    ax.set_xticks(depths)
    ax.set_xlabel("Fanin Cone Depth")
    ax.set_ylabel("Avg Rank-1 Region Score")
    ax.set_title("Region Correspondence — Avg Rank-1 Score by Cone Depth")
    ax.set_ylim(0, 1.05)
    ax.legend(title="Benchmark")
    ax.grid(linestyle="--", alpha=0.4)
    fig.tight_layout()
    return _save(fig, "region_scores.png")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

ALL_PLOTS = [
    ("exact_match_rate",      plot_exact_match_rate),
    ("support_overlap_dist",  plot_support_overlap_dist),
    ("node_reduction",        plot_node_reduction),
    ("level_reduction",       plot_level_reduction),
    ("sat_status",            plot_sat_status),
    ("topk_recovery",         plot_topk_recovery),
    ("ablation_comparison",   plot_ablation_comparison),
    ("region_scores",         plot_region_scores),
]


def run_all() -> dict[str, Optional[str]]:
    """Run every plot function; return {name: output_path_or_None}."""
    _ensure_plots_dir()
    results: dict[str, Optional[str]] = {}
    for name, fn in ALL_PLOTS:
        try:
            path = fn()
            results[name] = path
            status = f"→ {path}" if path else "SKIPPED (missing input)"
            print(f"  [{name}] {status}")
        except Exception as exc:  # pragma: no cover
            warnings.warn(f"[research_plots] {name} raised {exc!r} — skipping")
            results[name] = None
    return results


if __name__ == "__main__":
    print(f"Generating research plots → {PLOTS_DIR}/")
    saved = run_all()
    n_saved = sum(1 for v in saved.values() if v is not None)
    print(f"\nDone: {n_saved}/{len(saved)} plots written.")
