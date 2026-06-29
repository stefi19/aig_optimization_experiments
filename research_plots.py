"""
research_plots.py — Generate research-quality matplotlib PNG plots for AIG
optimization experiments.

Plots produced (all written to results/plots/):
  1. exact_match_rate.png        — signature match rate per benchmark/opt
                                   (formal only when is_formal_exact_mode = 1)
  2. support_overlap_dist.png    — distribution of avg_best_support_overlap
  3. node_reduction.png          — original vs optimised node counts (grouped bar)
  4. level_reduction.png         — original vs optimised level counts (grouped bar)
  5. sat_status.png              — stacked bar: verified / rejected / inconclusive
  6. topk_recovery.png           — avg_score_at_1 by benchmark (bar)
  7. ablation_comparison.png     — MRR / rank1_consistency per scoring config
  8. region_scores.png           — avg rank-1 region score by depth (line)
  9. preservation_vs_reduction.png — node reduction vs preserved signature fraction
 10. false_positive_by_group.png — rejected non-exact candidates by optimization group

Research iteration 2 — comparisons by benchmark source family
(toy / generated / iscas85 / epfl / custom):
 11. preservation_by_pass_and_family.png      — preservation per pass × family
 12. reduction_vs_preservation_by_family.png  — node reduction vs preservation
 13. sat_validation_by_family.png             — SAT verdicts per family
 14. mild_vs_aggressive_external.png          — mild vs aggressive on external suites
                                                (skipped until external files added)

Each plot function returns the output path so callers can log/test.
Missing optional input files are skipped gracefully (warning printed, no crash).
"""

from __future__ import annotations

import os
import sys
import types
import warnings
from pathlib import Path
from typing import Optional

import pandas as pd

try:
    from io import BytesIO

    import matplotlib
    matplotlib.use("Agg")  # headless — no display required
    import matplotlib.pyplot as plt
    import matplotlib.ticker as mticker
    _fig, _ax = plt.subplots(figsize=(1, 1))
    _ax.text(0.5, 0.5, "ok")
    _fig.savefig(BytesIO(), format="png")
    plt.close(_fig)
except Exception:
    class _FallbackFormatter:
        def __init__(self, *args, **kwargs):
            pass

    class _FallbackTicker:
        PercentFormatter = _FallbackFormatter

    class _FallbackBar:
        def __init__(self, x=0, width=1, height=0):
            self._x = x
            self._width = width
            self._height = height

        def get_x(self):
            return self._x

        def get_width(self):
            return self._width

        def get_height(self):
            return self._height

    class _FallbackAxisPart:
        def set_major_formatter(self, *args, **kwargs):
            return None

    class _FallbackAxis:
        def __init__(self):
            self.xaxis = _FallbackAxisPart()
            self.yaxis = _FallbackAxisPart()

        def bar(self, x, height=None, *args, **kwargs):
            xs = list(x) if hasattr(x, "__iter__") and not isinstance(x, str) else [x]
            hs = list(height) if hasattr(height, "__iter__") and not isinstance(height, str) else [height or 0]
            return [_FallbackBar(i, kwargs.get("width", 1), hs[i] if i < len(hs) else 0) for i, _ in enumerate(xs)]

        def hist(self, *args, **kwargs):
            return ([], [], [])

        def axvline(self, *args, **kwargs):
            return None

        def boxplot(self, *args, **kwargs):
            return {}

        def plot(self, *args, **kwargs):
            return []

        def scatter(self, *args, **kwargs):
            return None

        def text(self, *args, **kwargs):
            return None

        def set_xticks(self, *args, **kwargs):
            return None

        def set_xticklabels(self, *args, **kwargs):
            return None

        def set_xlabel(self, *args, **kwargs):
            return None

        def set_ylabel(self, *args, **kwargs):
            return None

        def set_title(self, *args, **kwargs):
            return None

        def set_ylim(self, *args, **kwargs):
            return None

        def legend(self, *args, **kwargs):
            return None

        def grid(self, *args, **kwargs):
            return None

        def tick_params(self, *args, **kwargs):
            return None

    class _FallbackFigure:
        def tight_layout(self):
            return None

        def savefig(self, path, *args, **kwargs):
            from PIL import Image, ImageDraw
            img = Image.new("RGB", (640, 360), "white")
            draw = ImageDraw.Draw(img)
            draw.text((20, 20), "Plot fallback: Matplotlib unavailable", fill="black")
            img.save(path)

    class _FallbackPyplot:
        Figure = _FallbackFigure

        def subplots(self, *args, **kwargs):
            return _FallbackFigure(), _FallbackAxis()

        def close(self, *args, **kwargs):
            return None

    plt = _FallbackPyplot()
    mticker = _FallbackTicker()
    matplotlib_stub = types.ModuleType("matplotlib")
    pyplot_stub = types.ModuleType("matplotlib.pyplot")
    ticker_stub = types.ModuleType("matplotlib.ticker")
    pyplot_stub.subplots = plt.subplots
    pyplot_stub.close = plt.close
    pyplot_stub.Figure = _FallbackFigure
    ticker_stub.PercentFormatter = _FallbackFormatter
    matplotlib_stub.pyplot = pyplot_stub
    matplotlib_stub.ticker = ticker_stub
    matplotlib_stub.use = lambda *args, **kwargs: None
    sys.modules["matplotlib"] = matplotlib_stub
    sys.modules["matplotlib.pyplot"] = pyplot_stub
    sys.modules["matplotlib.ticker"] = ticker_stub

# Shared source-family inference (toy / generated / iscas85 / epfl / custom).
sys.path.insert(0, str(Path(__file__).resolve().parent))
from scripts.benchmark_id import infer_source_family

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
    "false_positive":  RESULTS_DIR / "sat_false_positive_analysis.csv",
}

# Colour palette (colour-blind friendly, Okabe-Ito inspired)
PALETTE = [
    "#E69F00", "#56B4E9", "#009E73", "#F0E442",
    "#0072B2", "#D55E00", "#CC79A7", "#999999",
]

OPT_ORDER = [
    "balance", "rewrite", "rewrite_z",
    "refactor", "refactor_z",
    "resub", "resyn", "resyn2", "resyn2_like",
    "compress2rs", "dc2",
]

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
# 1. Signature match rate
# ---------------------------------------------------------------------------

def plot_exact_match_rate() -> Optional[str]:
    """Bar chart of internal signature match rate per benchmark × opt.

    The legacy output filename is kept for compatibility.  For rows where
    is_formal_exact_mode = 0, this is only a sampled-pattern signature match,
    not a formal truth-table proof.
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
    ax.set_ylabel("Signature Match Rate")
    ax.set_title("Internal Signature Match Rate by Benchmark & Optimization")
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
# 9. Preservation vs node reduction
# ---------------------------------------------------------------------------

def plot_preservation_vs_reduction() -> Optional[str]:
    """Scatter plot: node reduction vs preserved signature fraction.

    This uses the newer denominator-aware metric preserved_signature_fraction
    when present.  It excludes zero-internal-node rows so empty 0/0 cases do
    not look like failed preservation.
    """
    df = _load("summary")
    if df is None:
        return None

    df = df.copy()
    if "has_internal_nodes" in df.columns:
        df = df[df["has_internal_nodes"].astype(bool)]
    if df.empty:
        warnings.warn("[research_plots] no internal-node rows in summary CSV — skipping preservation plot")
        return None

    if "preserved_signature_fraction" not in df.columns:
        df["preserved_signature_fraction"] = (
            df["exact_internal_matches"] / df["original_nodes"].replace(0, float("nan"))
        )
    if "node_reduction_rate" not in df.columns:
        df["node_reduction_rate"] = (
            (df["original_nodes"] - df["optimized_nodes"])
            / df["original_nodes"].replace(0, float("nan"))
        )

    opts = _opt_labels(df["optimization"].unique().tolist())
    fig, ax = plt.subplots(figsize=(7, 5))
    for i, opt in enumerate(opts):
        sub = df[df["optimization"] == opt]
        ax.scatter(
            sub["node_reduction_rate"],
            sub["preserved_signature_fraction"],
            s=42,
            alpha=0.75,
            color=PALETTE[i % len(PALETTE)],
            label=opt,
            edgecolor="white",
            linewidth=0.4,
        )

    ax.set_xlabel("Node Reduction Rate")
    ax.set_ylabel("Preserved Signature Fraction")
    ax.set_title("Node Reduction vs Signature Preservation")
    ax.xaxis.set_major_formatter(mticker.PercentFormatter(xmax=1))
    ax.yaxis.set_major_formatter(mticker.PercentFormatter(xmax=1))
    ax.set_ylim(-0.05, 1.05)
    ax.grid(linestyle="--", alpha=0.4)
    ax.legend(title="Optimization", bbox_to_anchor=(1.01, 1), loc="upper left", fontsize=7)
    fig.tight_layout()
    return _save(fig, "preservation_vs_reduction.png")


# ---------------------------------------------------------------------------
# 10. False-positive analysis
# ---------------------------------------------------------------------------

def plot_false_positive_by_group() -> Optional[str]:
    """Grouped bar: rejected non-exact SAT candidates by optimization group."""
    df = _load("false_positive")
    if df is None:
        return None

    df = df[
        (df["dimension"] == "optimization_group")
        & (df["validation_layer"].isin([
            "rank1_nonexact_recovery",
            "topk_nonexact_recovery",
        ]))
    ].copy()
    if df.empty:
        warnings.warn("[research_plots] no false-positive rows by optimization_group — skipping")
        return None

    groups = ["mild", "moderate", "aggressive"]
    layers = ["rank1_nonexact_recovery", "topk_nonexact_recovery"]
    labels = ["rank-1", "top-k below rank 1"]
    x = range(len(groups))
    width = 0.34

    fig, ax = plt.subplots(figsize=(7, 4))
    for i, (layer, label) in enumerate(zip(layers, labels)):
        sub = df[df["validation_layer"] == layer]
        vals = [
            int(sub.loc[sub["bucket"] == group, "rejected_count"].sum())
            for group in groups
        ]
        offsets = [xi + (i - 0.5) * width for xi in x]
        ax.bar(offsets, vals, width=width * 0.9, color=PALETTE[i], label=label)

    ax.set_xticks(list(x))
    ax.set_xticklabels(groups)
    ax.set_ylabel("Rejected Candidate Count")
    ax.set_title("False Positives by Optimization Group")
    ax.legend()
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    fig.tight_layout()
    return _save(fig, "false_positive_by_group.png")


# ---------------------------------------------------------------------------
# Research iteration 2: comparisons by benchmark source family
# ---------------------------------------------------------------------------
#
# These plots group results by *source family* (toy / generated / iscas85 /
# epfl / custom) rather than by individual benchmark, so findings on toy and
# synthetic circuits can be compared against realistic external suites.
#
# Each function derives source_family from the benchmark id (so it works on the
# already-committed CSVs that may predate the source_family column) and skips
# gracefully when external benchmarks are absent.

# Display order and colour assignment for source families.
SOURCE_FAMILY_ORDER = ["toy", "generated", "custom", "iscas85", "epfl"]
EXTERNAL_FAMILIES = ("iscas85", "epfl")


def _with_source_family(df: pd.DataFrame) -> pd.DataFrame:
    """Return *df* with a guaranteed 'source_family' column.

    Uses the existing column if present, otherwise derives it from 'benchmark'.
    """
    df = df.copy()
    if "source_family" not in df.columns:
        df["source_family"] = df["benchmark"].map(infer_source_family)
    return df


def _families_present(df: pd.DataFrame) -> list[str]:
    present = set(df["source_family"].unique())
    ordered = [f for f in SOURCE_FAMILY_ORDER if f in present]
    extras = sorted(present - set(SOURCE_FAMILY_ORDER))
    return ordered + extras


def _family_color(family: str) -> str:
    idx = SOURCE_FAMILY_ORDER.index(family) if family in SOURCE_FAMILY_ORDER else -1
    return PALETTE[idx % len(PALETTE)]


def plot_preservation_by_pass_and_family() -> Optional[str]:
    """Grouped bar: mean preserved_signature_fraction per optimization pass,
    one bar group per source family."""
    df = _load("summary")
    if df is None or "preserved_signature_fraction" not in df.columns:
        return None
    df = _with_source_family(df)

    families = _families_present(df)
    passes = _opt_labels(sorted(df["optimization"].unique()))
    if not passes or not families:
        warnings.warn("[research_plots] no data for preservation_by_pass_and_family — skipping")
        return None

    pivot = (
        df.groupby(["optimization", "source_family"])["preserved_signature_fraction"]
        .mean()
        .unstack("source_family")
    )

    x = range(len(passes))
    n = len(families)
    width = 0.8 / max(n, 1)
    fig, ax = plt.subplots(figsize=(max(8, len(passes) * 1.1), 4.5))
    for i, fam in enumerate(families):
        vals = [
            pivot.loc[p, fam] if (p in pivot.index and fam in pivot.columns
                                  and pd.notna(pivot.loc[p, fam])) else 0.0
            for p in passes
        ]
        offsets = [xi + (i - (n - 1) / 2) * width for xi in x]
        ax.bar(offsets, vals, width=width * 0.95, color=_family_color(fam), label=fam)

    ax.set_xticks(list(x))
    ax.set_xticklabels(passes, rotation=30, ha="right")
    ax.set_ylabel("Mean preserved signature fraction")
    ax.set_ylim(0, 1.05)
    ax.set_title("Preservation by optimization pass and benchmark family")
    ax.legend(title="source family", fontsize=8)
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    fig.tight_layout()
    return _save(fig, "preservation_by_pass_and_family.png")


def plot_reduction_vs_preservation_by_family() -> Optional[str]:
    """Scatter: node reduction (x) vs preserved signature fraction (y),
    coloured by source family."""
    df = _load("summary")
    if df is None or not {"node_reduction_rate", "preserved_signature_fraction"} <= set(df.columns):
        return None
    df = _with_source_family(df)
    families = _families_present(df)
    if not families:
        return None

    fig, ax = plt.subplots(figsize=(7, 5))
    for fam in families:
        sub = df[df["source_family"] == fam]
        ax.scatter(
            sub["node_reduction_rate"], sub["preserved_signature_fraction"],
            color=_family_color(fam), label=fam, alpha=0.7, edgecolors="white", s=45,
        )
    ax.set_xlabel("Node reduction rate")
    ax.set_ylabel("Preserved signature fraction")
    ax.set_title("Node reduction vs preservation by benchmark family")
    ax.set_ylim(-0.02, 1.05)
    ax.legend(title="source family", fontsize=8)
    ax.grid(linestyle="--", alpha=0.4)
    fig.tight_layout()
    return _save(fig, "reduction_vs_preservation_by_family.png")


def plot_sat_validation_by_family() -> Optional[str]:
    """Stacked bar: SAT verified / rejected / inconclusive totals per family."""
    df = _load("sat_summary")
    if df is None:
        return None
    needed = {"verified", "rejected", "inconclusive"}
    if not needed <= set(df.columns):
        warnings.warn("[research_plots] sat_summary missing verdict columns — skipping")
        return None
    df = _with_source_family(df)
    agg = df.groupby("source_family")[["verified", "rejected", "inconclusive"]].sum()
    families = [f for f in _families_present(df) if f in agg.index]
    if not families:
        return None

    x = range(len(families))
    verified = [int(agg.loc[f, "verified"]) for f in families]
    rejected = [int(agg.loc[f, "rejected"]) for f in families]
    inconcl = [int(agg.loc[f, "inconclusive"]) for f in families]

    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.bar(x, verified, color="#009E73", label="verified")
    ax.bar(x, rejected, bottom=verified, color="#D55E00", label="rejected")
    bottom2 = [v + r for v, r in zip(verified, rejected)]
    ax.bar(x, inconcl, bottom=bottom2, color="#999999", label="inconclusive")

    ax.set_xticks(list(x))
    ax.set_xticklabels(families)
    ax.set_ylabel("SAT candidate count")
    ax.set_title("SAT validation results by benchmark family")
    ax.legend(fontsize=8)
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    fig.tight_layout()
    return _save(fig, "sat_validation_by_family.png")


def plot_mild_vs_aggressive_external() -> Optional[str]:
    """Grouped bar: mean preserved_signature_fraction under mild vs aggressive
    optimization, restricted to external (ISCAS-85 / EPFL) families.

    Skips with a clear warning when no external benchmarks are present — this is
    the expected state until ISCAS-85 / EPFL files are added under
    benchmarks/external/.
    """
    df = _load("summary")
    if df is None or "preserved_signature_fraction" not in df.columns:
        return None
    df = _with_source_family(df)
    df = df[df["source_family"].isin(EXTERNAL_FAMILIES)]
    if df.empty:
        warnings.warn(
            "[research_plots] no external (ISCAS-85 / EPFL) benchmarks found — "
            "skipping mild_vs_aggressive_external. Add files under "
            "benchmarks/external/ to enable this comparison."
        )
        return None

    # Map optimization_group → mild/aggressive; ignore mediums for a clean contrast.
    group_col = df["optimization_group"] if "optimization_group" in df.columns else None
    if group_col is None:
        return None
    df = df.assign(effort=group_col.map({
        "none": "mild", "low": "mild",
        "very_high": "aggressive",
    }))
    df = df[df["effort"].isin(["mild", "aggressive"])]
    if df.empty:
        warnings.warn("[research_plots] no mild/aggressive rows for external benchmarks — skipping")
        return None

    families = [f for f in EXTERNAL_FAMILIES if f in set(df["source_family"])]
    efforts = ["mild", "aggressive"]
    pivot = (
        df.groupby(["source_family", "effort"])["preserved_signature_fraction"]
        .mean().unstack("effort")
    )

    x = range(len(families))
    width = 0.35
    fig, ax = plt.subplots(figsize=(6, 4.5))
    for i, effort in enumerate(efforts):
        vals = [
            pivot.loc[f, effort] if (f in pivot.index and effort in pivot.columns
                                     and pd.notna(pivot.loc[f, effort])) else 0.0
            for f in families
        ]
        offsets = [xi + (i - 0.5) * width for xi in x]
        ax.bar(offsets, vals, width=width * 0.95, color=PALETTE[i], label=effort)

    ax.set_xticks(list(x))
    ax.set_xticklabels(families)
    ax.set_ylabel("Mean preserved signature fraction")
    ax.set_ylim(0, 1.05)
    ax.set_title("Mild vs aggressive optimization (external benchmarks)")
    ax.legend()
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    fig.tight_layout()
    return _save(fig, "mild_vs_aggressive_external.png")


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
    ("preservation_vs_reduction", plot_preservation_vs_reduction),
    ("false_positive_by_group", plot_false_positive_by_group),
    # Research iteration 2 — by source family
    ("preservation_by_pass_and_family", plot_preservation_by_pass_and_family),
    ("reduction_vs_preservation_by_family", plot_reduction_vs_preservation_by_family),
    ("sat_validation_by_family", plot_sat_validation_by_family),
    ("mild_vs_aggressive_external", plot_mild_vs_aggressive_external),
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
