#!/usr/bin/env python3
"""Compare baseline and functional-feature correspondence ranking modes."""

from __future__ import annotations

import argparse
import math
import statistics
import sys
import time
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from functional_ranking_features import RANKING_MODES, support_bucket  # noqa: E402

RESULTS = ROOT / "results"
FEATURES = RESULTS / "cofactor_sensitivity" / "cofactor_sensitivity_features.csv"
OUT_DIR = RESULTS / "ranking_ablation"
PLOTS = RESULTS / "plots"
GROUP_KEYS = ["benchmark", "optimization", "optimized_node", "seed"]


def checked_label(status: str) -> str:
    if status == "verified_equivalent":
        return "verified"
    if status == "rejected_non_equivalent":
        return "rejected"
    return "unchecked"


def ranked_frame(df: pd.DataFrame, mode: str) -> pd.DataFrame:
    score_col = mode
    ranked = df.copy()
    ranked[score_col] = pd.to_numeric(ranked[score_col], errors="coerce").fillna(0.0)
    ranked["candidate_rank"] = pd.to_numeric(ranked["candidate_rank"], errors="coerce").fillna(999999)
    ranked = ranked.sort_values(
        ["benchmark", "optimization", "optimized_node", score_col, "candidate_rank", "original_node"],
        ascending=[True, True, True, False, True, True],
    )
    ranked["mode_rank"] = ranked.groupby(GROUP_KEYS).cumcount() + 1
    return ranked


def precision_at_k(group: pd.DataFrame, k: int) -> float | None:
    top = group[group["mode_rank"] <= k]
    checked = top[top["formal_label"].isin(["verified_equivalent", "rejected_non_equivalent"])]
    if checked.empty:
        return None
    return float((checked["formal_label"] == "verified_equivalent").sum() / len(checked))


def first_verified_stats(ranked: pd.DataFrame) -> tuple[list[int], list[int]]:
    ranks: list[int] = []
    calls: list[int] = []
    for _, group in ranked.groupby(GROUP_KEYS, sort=False):
        verified = group[group["formal_label"] == "verified_equivalent"]
        if verified.empty:
            continue
        first_rank = int(verified["mode_rank"].iloc[0])
        ranks.append(first_rank)
        checked_before = group[group["mode_rank"] <= first_rank]
        calls.append(int(checked_before["formal_label"].isin(["verified_equivalent", "rejected_non_equivalent"]).sum()))
    return ranks, calls


def aggregate_metrics(df: pd.DataFrame, group_cols: list[str] | None = None) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    group_cols = group_cols or []
    grouped = [((), df)] if not group_cols else df.groupby(group_cols)
    for group_key, subset in grouped:
        key_values = group_key if isinstance(group_key, tuple) else (group_key,)
        key_row = dict(zip(group_cols, key_values))
        for mode in RANKING_MODES:
            start = time.perf_counter()
            ranked = ranked_frame(subset, mode)
            ranks, calls = first_verified_stats(ranked)
            target_count = ranked[GROUP_KEYS].drop_duplicates().shape[0]
            row = {
                **key_row,
                "ranking_mode": mode,
                "candidate_count": len(ranked),
                "target_nodes": target_count,
                "targets_with_verified_candidate": len(ranks),
                "precision_at_1": mean_optional([precision_at_k(g, 1) for _, g in ranked.groupby(GROUP_KEYS)]),
                "precision_at_3": mean_optional([precision_at_k(g, 3) for _, g in ranked.groupby(GROUP_KEYS)]),
                "precision_at_5": mean_optional([precision_at_k(g, 5) for _, g in ranked.groupby(GROUP_KEYS)]),
                "precision_at_10": mean_optional([precision_at_k(g, 10) for _, g in ranked.groupby(GROUP_KEYS)]),
                "mean_reciprocal_rank": statistics.fmean([1.0 / rank for rank in ranks]) if ranks else 0.0,
                "mean_first_verified_rank": statistics.fmean(ranks) if ranks else 0.0,
                "median_first_verified_rank": statistics.median(ranks) if ranks else 0.0,
                "sat_cec_calls_per_verified_recovery": statistics.fmean(calls) if calls else 0.0,
                "runtime_seconds": time.perf_counter() - start,
            }
            for budget in (1, 3, 5, 10):
                row[f"verified_recoveries_budget_{budget}"] = verified_under_budget(ranked, budget)
            rows.append(row)
    return pd.DataFrame(rows)


def mean_optional(values: list[float | None]) -> float:
    filtered = [value for value in values if value is not None]
    return statistics.fmean(filtered) if filtered else 0.0


def verified_under_budget(ranked: pd.DataFrame, budget: int) -> int:
    recovered = 0
    for _, group in ranked.groupby(GROUP_KEYS, sort=False):
        checked = group[group["formal_label"].isin(["verified_equivalent", "rejected_non_equivalent"])].head(budget)
        if (checked["formal_label"] == "verified_equivalent").any():
            recovered += 1
    return recovered


def seed_stability(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    full_ranks = []
    for seed, seed_df in df.groupby("seed"):
        ranked = ranked_frame(seed_df, "full_combined")
        ranked = ranked[ranked["formal_label"] == "verified_equivalent"]
        for _, row in ranked.iterrows():
            full_ranks.append(
                {
                    "benchmark": row["benchmark"],
                    "optimization": row["optimization"],
                    "optimized_node": row["optimized_node"],
                    "original_node": row["original_node"],
                    "seed": seed,
                    "full_combined_rank": row["mode_rank"],
                }
            )
    ranks = pd.DataFrame(full_ranks)
    if ranks.empty:
        return pd.DataFrame(columns=["benchmark", "optimization", "optimized_node", "original_node", "seed_count", "rank_mean", "rank_min", "rank_max", "rank_spread"])
    for key, group in ranks.groupby(["benchmark", "optimization", "optimized_node", "original_node"]):
        values = list(map(int, group["full_combined_rank"]))
        rows.append(
            {
                "benchmark": key[0],
                "optimization": key[1],
                "optimized_node": key[2],
                "original_node": key[3],
                "seed_count": len(values),
                "rank_mean": statistics.fmean(values),
                "rank_min": min(values),
                "rank_max": max(values),
                "rank_spread": max(values) - min(values),
            }
        )
    return pd.DataFrame(rows)


def write_summary(overall: pd.DataFrame, by_opt: pd.DataFrame, stability: pd.DataFrame, path: Path) -> None:
    lines = [
        "# Functional Ranking Ablation Summary",
        "",
        "The ablation compares heuristic ranking modes against existing SAT/CEC-labeled candidates. Precision@K excludes unchecked candidates from the denominator; SAT/CEC remains the authority for equivalence.",
        "",
        "## Overall Metrics",
        "",
        overall.to_markdown(index=False, floatfmt=".4f"),
        "",
        "## By Optimization Flow",
        "",
        by_opt.to_markdown(index=False, floatfmt=".4f"),
        "",
        "## Sampled Seed Stability",
        "",
    ]
    if stability.empty:
        lines.append("No verified candidates were available for seed-stability reporting.")
    else:
        lines.append(
            stability[["seed_count", "rank_spread"]].describe().reset_index().to_markdown(index=False, floatfmt=".4f")
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def make_plots(df: pd.DataFrame, overall: pd.DataFrame, by_opt: pd.DataFrame, by_bucket: pd.DataFrame, stability: pd.DataFrame) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    PLOTS.mkdir(parents=True, exist_ok=True)

    def save(path: Path) -> None:
        plt.tight_layout()
        plt.savefig(path, dpi=180)
        plt.close()

    fig, ax = plt.subplots(figsize=(8, 4.5))
    overall.set_index("ranking_mode")[["precision_at_1", "precision_at_5", "precision_at_10"]].plot(kind="bar", ax=ax)
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("checked-candidate precision")
    ax.set_title("Precision@K by Ranking Mode")
    ax.tick_params(axis="x", rotation=30)
    save(PLOTS / "functional_precision_at_k_by_mode.png")

    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar(overall["ranking_mode"], overall["mean_reciprocal_rank"], color="#4c78a8")
    ax.set_ylabel("MRR")
    ax.set_title("Mean Reciprocal Rank by Ranking Mode")
    ax.tick_params(axis="x", rotation=30)
    save(PLOTS / "functional_mrr_by_mode.png")

    budget_cols = [col for col in overall.columns if col.startswith("verified_recoveries_budget_")]
    fig, ax = plt.subplots(figsize=(8, 4.5))
    for _, row in overall.iterrows():
        ax.plot([int(col.rsplit("_", 1)[1]) for col in budget_cols], [row[col] for col in budget_cols], marker="o", label=row["ranking_mode"])
    ax.set_xlabel("SAT/CEC call budget per target")
    ax.set_ylabel("verified recoveries")
    ax.set_title("Recoveries Under Fixed SAT/CEC Budgets")
    ax.legend(fontsize=8)
    save(PLOTS / "functional_sat_budget_recoveries.png")

    verified = df[df["formal_label"] == "verified_equivalent"].copy()
    if not verified.empty:
        ranked_base = ranked_frame(df, "baseline")[["benchmark", "optimization", "optimized_node", "original_node", "seed", "mode_rank"]].rename(columns={"mode_rank": "baseline_rank"})
        ranked_full = ranked_frame(df, "full_combined")[["benchmark", "optimization", "optimized_node", "original_node", "seed", "mode_rank"]].rename(columns={"mode_rank": "full_rank"})
        ranks = ranked_base.merge(ranked_full, on=["benchmark", "optimization", "optimized_node", "original_node", "seed"])
        ranks = ranks.merge(verified[["benchmark", "optimization", "optimized_node", "original_node", "seed"]].drop_duplicates())
        fig, ax = plt.subplots(figsize=(5.5, 5))
        ax.scatter(ranks["baseline_rank"], ranks["full_rank"], alpha=0.6)
        lim = max(ranks["baseline_rank"].max(), ranks["full_rank"].max(), 1)
        ax.plot([1, lim], [1, lim], color="#999999", linestyle="--")
        ax.set_xlabel("baseline rank")
        ax.set_ylabel("full-combined rank")
        ax.set_title("Verified Candidates: Baseline vs Enhanced Rank")
        save(PLOTS / "functional_baseline_vs_enhanced_verified_rank.png")

    for metric, path, title in [
        ("cofactor_consistency_score", "functional_cofactor_consistency_by_status.png", "Cofactor Consistency by SAT/CEC Label"),
        ("sensitivity_cosine_similarity", "functional_sensitivity_similarity_by_status.png", "Sensitivity Similarity by SAT/CEC Label"),
    ]:
        fig, ax = plt.subplots(figsize=(6.5, 4))
        labels = []
        data = []
        for label, group in df.groupby("formal_label"):
            values = pd.to_numeric(group[metric], errors="coerce").dropna()
            if not values.empty:
                labels.append(label.replace("_", "\n"))
                data.append(values)
        if data:
            ax.boxplot(data, tick_labels=labels)
        ax.set_ylabel(metric)
        ax.set_title(title)
        save(PLOTS / path)

    fig, ax = plt.subplots(figsize=(8, 4.5))
    opt = by_opt[by_opt["ranking_mode"].isin(["baseline", "full_combined"])]
    opt.pivot(index="optimization", columns="ranking_mode", values="mean_reciprocal_rank").plot(kind="bar", ax=ax)
    ax.set_ylabel("MRR")
    ax.set_title("MRR by Optimization Flow")
    ax.tick_params(axis="x", rotation=30)
    save(PLOTS / "functional_improvement_by_optimization.png")

    fig, ax = plt.subplots(figsize=(8, 4.5))
    bucket = by_bucket[by_bucket["ranking_mode"].isin(["baseline", "full_combined"])]
    bucket.pivot(index="support_size_bucket", columns="ranking_mode", values="mean_reciprocal_rank").plot(kind="bar", ax=ax)
    ax.set_ylabel("MRR")
    ax.set_title("MRR by Support-Size Bucket")
    ax.tick_params(axis="x", rotation=0)
    save(PLOTS / "functional_improvement_by_support_bucket.png")

    fig, ax = plt.subplots(figsize=(6.5, 4))
    if not stability.empty:
        ax.hist(stability["rank_spread"], bins=range(0, int(stability["rank_spread"].max()) + 2), color="#4c78a8")
    ax.set_xlabel("rank spread across seeds")
    ax.set_ylabel("verified candidate count")
    ax.set_title("Sampled-Seed Rank Stability")
    save(PLOTS / "functional_seed_rank_stability.png")

    fig, ax = plt.subplots(figsize=(6.5, 4))
    unresolved = pd.DataFrame(
        {
            "mode": overall["ranking_mode"],
            "unresolved_after_budget_5": overall["target_nodes"] - overall["verified_recoveries_budget_5"],
        }
    )
    ax.bar(unresolved["mode"], unresolved["unresolved_after_budget_5"], color="#b8b8b8")
    ax.set_ylabel("targets not recovered")
    ax.set_title("Critical-Path Proxy: Unrecovered Targets at Budget 5")
    ax.tick_params(axis="x", rotation=30)
    save(PLOTS / "functional_critical_path_unresolved_budget.png")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--features-csv", type=Path, default=FEATURES)
    parser.add_argument("--output-dir", type=Path, default=OUT_DIR)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if not args.features_csv.exists():
        raise SystemExit(f"missing feature CSV: {args.features_csv}")
    df = pd.read_csv(args.features_csv)
    if "support_size_bucket" not in df:
        df["support_size_bucket"] = df["optimized_support_size"].map(support_bucket)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    overall = aggregate_metrics(df)
    by_benchmark = aggregate_metrics(df, ["benchmark"])
    by_opt = aggregate_metrics(df, ["optimization"])
    by_bucket = aggregate_metrics(df, ["support_size_bucket"])
    stability = seed_stability(df)
    overall.to_csv(args.output_dir / "ranking_ablation_overall.csv", index=False)
    by_benchmark.to_csv(args.output_dir / "ranking_ablation_by_benchmark.csv", index=False)
    by_opt.to_csv(args.output_dir / "ranking_ablation_by_optimization.csv", index=False)
    by_bucket.to_csv(args.output_dir / "ranking_ablation_by_support_bucket.csv", index=False)
    stability.to_csv(args.output_dir / "ranking_ablation_seed_stability.csv", index=False)
    write_summary(overall, by_opt, stability, args.output_dir / "ranking_ablation_summary.md")
    make_plots(df, overall, by_opt, by_bucket, stability)
    print(f"Wrote ranking ablation outputs to {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
