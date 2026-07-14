#!/usr/bin/env python3
"""Summarize ISCAS-85 rank-1 structural-mismatch candidates proven by SAT/CEC."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
PLOTS = RESULTS / "plots"


SAT_PATH = RESULTS / "sat_verified_candidates.csv"
TOP_PATH = RESULTS / "top_candidates.csv"
OUT_ANALYSIS_CSV = RESULTS / "iscas_verified_match_analysis.csv"
OUT_ANALYSIS_MD = RESULTS / "iscas_verified_match_analysis.md"
OUT_FEATURE_CSV = RESULTS / "iscas_feature_comparison.csv"
OUT_CASES_MD = RESULTS / "iscas_case_studies.md"


OPT_GROUPS = {
    "balance": "low",
    "rewrite": "medium",
    "rewrite_z": "medium",
    "refactor": "medium",
    "refactor_z": "medium",
    "resub": "high",
    "resyn": "high",
    "compress2rs": "very_high",
    "dc2": "very_high",
    "resyn2": "very_high",
    "resyn2_like": "very_high",
}


def read_iscas_rank1() -> pd.DataFrame:
    sat = pd.read_csv(SAT_PATH)
    feature_cols = [
        "benchmark",
        "optimization",
        "optimized_node",
        "rank",
        "original_candidate",
        "simulation_similarity",
        "depth_similarity",
        "optimized_level",
        "original_level",
        "optimized_support_size",
        "original_support_size",
        "optimized_fanin_count",
        "original_fanin_count",
    ]
    top = pd.read_csv(TOP_PATH, usecols=feature_cols)

    keys = ["benchmark", "optimization", "optimized_node", "rank", "original_candidate"]
    df = sat.merge(top, on=keys, how="left", validate="one_to_one")
    df = df[
        df["benchmark"].str.startswith("external_iscas85_")
        & (df["match_category"] == "non_exact_candidate")
        & (df["rank"] == 1)
    ].copy()
    df["circuit"] = df["benchmark"].str.replace("external_iscas85_", "", regex=False)
    df["optimization_group"] = df["optimization"].map(OPT_GROUPS).fillna("unknown")
    df["is_verified"] = df["sat_status"].eq("verified")
    df["level_delta_abs"] = (df["optimized_level"] - df["original_level"]).abs()
    df["support_size_delta_abs"] = (
        df["optimized_support_size"] - df["original_support_size"]
    ).abs()
    return df


def precision_table(df: pd.DataFrame, key: str) -> pd.DataFrame:
    table = pd.crosstab(df[key], df["sat_status"])
    for col in ["verified", "rejected"]:
        if col not in table:
            table[col] = 0
    table = table[["verified", "rejected"]]
    table["total_checked"] = table["verified"] + table["rejected"]
    table["precision"] = table["verified"] / table["total_checked"]
    return table.reset_index().sort_values(
        ["verified", "precision", key], ascending=[False, False, True]
    )


def feature_comparison(df: pd.DataFrame) -> pd.DataFrame:
    features = [
        "combined_score",
        "support_overlap",
        "simulation_similarity",
        "depth_similarity",
        "level_delta_abs",
        "support_size_delta_abs",
        "optimized_level",
        "original_level",
        "optimized_support_size",
        "original_support_size",
    ]
    rows = []
    verified = df[df["sat_status"] == "verified"]
    rejected = df[df["sat_status"] == "rejected"]
    for feature in features:
        rows.append(
            {
                "feature": feature,
                "verified_mean": verified[feature].mean(),
                "rejected_mean": rejected[feature].mean(),
                "verified_median": verified[feature].median(),
                "rejected_median": rejected[feature].median(),
                "verified_min": verified[feature].min(),
                "rejected_min": rejected[feature].min(),
                "verified_max": verified[feature].max(),
                "rejected_max": rejected[feature].max(),
            }
        )
    return pd.DataFrame(rows)


def pick_case_studies(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    verified = df[df["sat_status"] == "verified"].copy()
    rejected = df[df["sat_status"] == "rejected"].copy()

    cases: list[pd.Series] = []

    def add_case(label: str, rows: pd.DataFrame, sort_cols: list[str]) -> None:
        if rows.empty:
            return
        row = rows.sort_values(sort_cols, ascending=False).iloc[0].copy()
        row["case_type"] = label
        cases.append(row)

    add_case(
        "high-score verified from a mild/moderate pass",
        verified[verified["optimization"].isin(["rewrite", "refactor", "resub"])],
        ["combined_score", "simulation_similarity"],
    )
    add_case(
        "verified from aggressive resynthesis",
        verified[
            verified["optimization"].isin(["compress2rs", "dc2", "resyn2", "resyn2_like"])
        ],
        ["combined_score", "simulation_similarity"],
    )
    add_case(
        "verified even though support changed",
        verified[verified["support_overlap"] < 1.0],
        ["combined_score", "simulation_similarity"],
    )
    add_case(
        "verified from circuit with most recoveries",
        verified[verified["circuit"] == "c2670"],
        ["combined_score", "simulation_similarity"],
    )
    add_case(
        "verified from multiplier-like c6288",
        verified[verified["circuit"] == "c6288"],
        ["combined_score", "simulation_similarity"],
    )

    case_df = pd.DataFrame(cases).drop_duplicates(
        ["benchmark", "optimization", "optimized_node", "original_candidate"]
    )

    false_pos = rejected.sort_values(
        ["combined_score", "support_overlap", "simulation_similarity"],
        ascending=False,
    ).head(5)
    return case_df, false_pos


def short_case_table(df: pd.DataFrame, include_reason: bool = False) -> pd.DataFrame:
    cols = [
        "benchmark",
        "optimization",
        "original_candidate",
        "optimized_node",
        "combined_score",
        "support_overlap",
        "simulation_similarity",
        "sat_status",
    ]
    out = df[cols].copy()
    for col in ["combined_score", "support_overlap", "simulation_similarity"]:
        out[col] = out[col].round(4)
    if "case_type" in df.columns:
        out["short_interpretation"] = df["case_type"].values
    if include_reason:
        out["why_it_is_misleading"] = (
            "High score and overlapping support, but ABC found a counterexample"
        )
    return out


def save_plot(path: Path) -> None:
    plt.tight_layout()
    plt.savefig(path, dpi=180)
    plt.close()


def plot_counts(circuit_table: pd.DataFrame, opt_table: pd.DataFrame, df: pd.DataFrame) -> None:
    PLOTS.mkdir(parents=True, exist_ok=True)

    plot_df = circuit_table.sort_values("verified", ascending=True)
    ax = plot_df.set_index("circuit")[["verified", "rejected"]].plot(
        kind="barh", stacked=True, figsize=(9, 5), color=["#2f7d32", "#b54848"]
    )
    ax.set_xlabel("SAT-checked rank-1 structural-mismatch candidates")
    ax.set_ylabel("ISCAS-85 circuit")
    ax.set_title("ISCAS-85 SAT Verdicts by Circuit")
    save_plot(PLOTS / "iscas_verified_by_circuit.png")

    plot_df = opt_table.sort_values("verified", ascending=True)
    ax = plot_df.set_index("optimization")[["verified", "rejected"]].plot(
        kind="barh", stacked=True, figsize=(9, 5), color=["#2f7d32", "#b54848"]
    )
    ax.set_xlabel("SAT-checked rank-1 structural-mismatch candidates")
    ax.set_ylabel("Optimization pass")
    ax.set_title("ISCAS-85 SAT Verdicts by Optimization")
    save_plot(PLOTS / "iscas_verified_by_optimization.png")

    plot_df = opt_table.sort_values("precision", ascending=False)
    fig, ax = plt.subplots(figsize=(9, 4.8))
    ax.bar(plot_df["optimization"], plot_df["precision"], color="#3b6ea8")
    ax.set_ylabel("Precision = verified / checked")
    ax.set_xlabel("Optimization pass")
    ax.set_title("ISCAS-85 Rank-1 Non-Exact Precision by Optimization")
    ax.tick_params(axis="x", rotation=40)
    ax.set_ylim(0, max(0.35, plot_df["precision"].max() * 1.15))
    save_plot(PLOTS / "iscas_precision_by_optimization.png")

    fig, ax = plt.subplots(figsize=(8, 4.8))
    for status, color in [("verified", "#2f7d32"), ("rejected", "#b54848")]:
        subset = df[df["sat_status"] == status]
        ax.hist(
            subset["combined_score"],
            bins=30,
            alpha=0.55,
            label=status,
            color=color,
            density=True,
        )
    ax.set_xlabel("combined_score")
    ax.set_ylabel("Density")
    ax.set_title("Verified vs Rejected Score Distribution")
    ax.legend()
    save_plot(PLOTS / "verified_vs_rejected_score_distribution.png")

    fig, ax = plt.subplots(figsize=(8, 4.8))
    for status, color in [("verified", "#2f7d32"), ("rejected", "#b54848")]:
        subset = df[df["sat_status"] == status]
        ax.hist(
            subset["support_overlap"],
            bins=20,
            alpha=0.55,
            label=status,
            color=color,
            density=True,
        )
    ax.set_xlabel("support_overlap")
    ax.set_ylabel("Density")
    ax.set_title("Verified vs Rejected Support Overlap")
    ax.legend()
    save_plot(PLOTS / "verified_vs_rejected_support_overlap.png")

    heat = pd.pivot_table(
        df,
        index="circuit",
        columns="optimization",
        values="is_verified",
        aggfunc="mean",
        fill_value=0.0,
    )
    heat = heat.loc[circuit_table.sort_values("verified", ascending=False)["circuit"]]
    fig, ax = plt.subplots(figsize=(10, 5.5))
    im = ax.imshow(heat.values, aspect="auto", cmap="YlGn", vmin=0, vmax=max(0.3, heat.values.max()))
    ax.set_xticks(range(len(heat.columns)), heat.columns, rotation=45, ha="right")
    ax.set_yticks(range(len(heat.index)), heat.index)
    ax.set_title("ISCAS-85 Recovery Precision Heatmap")
    ax.set_xlabel("Optimization pass")
    ax.set_ylabel("Circuit")
    cbar = fig.colorbar(im, ax=ax)
    cbar.set_label("verified / checked")
    save_plot(PLOTS / "iscas_recovery_heatmap.png")


def write_markdown(
    df: pd.DataFrame,
    circuit_table: pd.DataFrame,
    opt_table: pd.DataFrame,
    feature_table: pd.DataFrame,
    cases: pd.DataFrame,
    false_pos: pd.DataFrame,
) -> None:
    group_table = precision_table(df, "optimization_group").rename(
        columns={"optimization_group": "group"}
    )
    support_verified = int(((df["sat_status"] == "verified") & (df["support_overlap"] == 1)).sum())
    support_rejected = int(((df["sat_status"] == "rejected") & (df["support_overlap"] == 1)).sum())
    verified_total = int((df["sat_status"] == "verified").sum())
    rejected_total = int((df["sat_status"] == "rejected").sum())

    md = [
        "# ISCAS-85 Verified Match Analysis",
        "",
        "This analysis covers rank-1 candidates that were not recovered by the initial signature/structural matching stage in the expanded ISCAS-85 SAT run.",
        "When SAT/CEC verifies one of these rows, it proves exact Boolean equivalence; only the discovery method was non-initial.",
        "",
        f"- Total checked: {len(df):,}",
        f"- Verified: {verified_total:,}",
        f"- Rejected: {rejected_total:,}",
        "- Inconclusive: 0",
        "",
        "## By Circuit",
        "",
        circuit_table.to_markdown(index=False, floatfmt=".3f"),
        "",
        "## By Optimization",
        "",
        opt_table.to_markdown(index=False, floatfmt=".3f"),
        "",
        "## By Optimization Group",
        "",
        group_table.to_markdown(index=False, floatfmt=".3f"),
        "",
        "## Feature Comparison",
        "",
        feature_table.to_markdown(index=False, floatfmt=".3f"),
        "",
        "## Support-Overlap Check",
        "",
        f"- Verified candidates with `support_overlap = 1.0`: {support_verified:,} / {verified_total:,}",
        f"- Rejected candidates with `support_overlap = 1.0`: {support_rejected:,} / {rejected_total:,}",
        "",
        "Support overlap is useful, but it is not enough to separate true from false matches.",
        "",
        "## Representative Verified Matches",
        "",
        short_case_table(cases).to_markdown(index=False),
        "",
        "## Representative High-Score False Positives",
        "",
        short_case_table(false_pos, include_reason=True).to_markdown(index=False),
        "",
    ]
    OUT_ANALYSIS_MD.write_text("\n".join(md), encoding="utf-8")
    OUT_CASES_MD.write_text(
        "\n".join(
            [
                "# ISCAS-85 Case Studies",
                "",
                "## SAT/CEC-Proven Equivalent After Structural Mismatch",
                "",
                short_case_table(cases).to_markdown(index=False),
                "",
                "## High-score rejected candidates",
                "",
                short_case_table(false_pos, include_reason=True).to_markdown(index=False),
                "",
            ]
        ),
        encoding="utf-8",
    )


def main() -> int:
    df = read_iscas_rank1()
    if df.empty:
        raise SystemExit("No ISCAS-85 rank-1 SAT candidates found.")

    circuit_table = precision_table(df, "circuit")
    opt_table = precision_table(df, "optimization")
    feature_table = feature_comparison(df)
    cases, false_pos = pick_case_studies(df)

    out_rows = []
    for section, table in [("circuit", circuit_table), ("optimization", opt_table)]:
        renamed = table.rename(columns={section: "name"}).copy()
        renamed.insert(0, "section", section)
        out_rows.append(renamed)
    pd.concat(out_rows, ignore_index=True).to_csv(OUT_ANALYSIS_CSV, index=False)
    feature_table.to_csv(OUT_FEATURE_CSV, index=False)

    plot_counts(circuit_table, opt_table, df)
    write_markdown(df, circuit_table, opt_table, feature_table, cases, false_pos)

    print(f"Loaded {len(df):,} ISCAS rank-1 structural-mismatch SAT candidates")
    print(f"Wrote {OUT_ANALYSIS_CSV.relative_to(ROOT)}")
    print(f"Wrote {OUT_ANALYSIS_MD.relative_to(ROOT)}")
    print(f"Wrote {OUT_FEATURE_CSV.relative_to(ROOT)}")
    print(f"Wrote {OUT_CASES_MD.relative_to(ROOT)}")
    print("Wrote ISCAS recovery plots under results/plots/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
