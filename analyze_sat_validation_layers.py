#!/usr/bin/env python3
"""Summarize SAT validation layers and false positives.

Inputs are kept separate on purpose:
- rank-1 non-exact recovery: results/sat_verified_candidates.csv
- exact-anchor sanity check: results/sat_exact_anchor_verified.csv
- below-rank-1 top-k non-exact recovery: results/sat_topk_nonexact_verified.csv
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd


RANK1 = Path("results/sat_verified_candidates.csv")
EXACT = Path("results/sat_exact_anchor_verified.csv")
TOPK = Path("results/sat_topk_nonexact_verified.csv")

OUT_SUMMARY_CSV = Path("results/sat_validation_layers_summary.csv")
OUT_FALSE_POS_CSV = Path("results/sat_false_positive_analysis.csv")
OUT_MD = Path("results/sat_validation_layers.md")


def benchmark_family(name: str) -> str:
    if name.startswith("generated_"):
        return "generated"
    if name.startswith("real_"):
        return "real_hand_written"
    return "toy"


def optimization_group(opt: str) -> str:
    if opt in {"balance", "rewrite", "resub"}:
        return "mild"
    if opt in {"refactor", "refactor_z", "rewrite_z", "resyn"}:
        return "moderate"
    return "aggressive"


def score_bucket(value: float) -> str:
    if value < 0.85:
        return "<0.85"
    if value < 0.90:
        return "0.85-0.90"
    if value < 0.95:
        return "0.90-0.95"
    return "0.95-1.00"


def support_bucket(value: float | None) -> str:
    if pd.isna(value):
        return "unknown"
    if value < 0.50:
        return "<0.50"
    if value < 0.75:
        return "0.50-0.75"
    if value < 0.90:
        return "0.75-0.90"
    if value < 1.0:
        return "0.90-1.00"
    return "1.00"


def load(path: Path, layer: str) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path)
    df["validation_layer"] = layer
    df["benchmark_family"] = df["benchmark"].map(benchmark_family)
    df["optimization_group"] = df["optimization"].map(optimization_group)
    df["combined_score_bucket"] = df["combined_score"].map(score_bucket)
    return df


def summarize_layer(df: pd.DataFrame, layer: str) -> dict:
    if df.empty:
        return {
            "validation_layer": layer,
            "total": 0,
            "verified": 0,
            "rejected": 0,
            "inconclusive": 0,
            "verification_rate": 0.0,
            "rejection_rate": 0.0,
            "inconclusive_rate": 0.0,
        }
    counts = df["sat_status"].value_counts()
    total = len(df)
    verified = int(counts.get("verified", 0))
    rejected = int(counts.get("rejected", 0))
    inconclusive = int(counts.get("inconclusive", 0))
    return {
        "validation_layer": layer,
        "total": total,
        "verified": verified,
        "rejected": rejected,
        "inconclusive": inconclusive,
        "verification_rate": verified / total if total else 0.0,
        "rejection_rate": rejected / total if total else 0.0,
        "inconclusive_rate": inconclusive / total if total else 0.0,
    }


def false_positive_tables(rank1: pd.DataFrame, topk: pd.DataFrame) -> pd.DataFrame:
    rejected = pd.concat([rank1, topk], ignore_index=True)
    rejected = rejected[rejected["sat_status"] == "rejected"].copy()
    if rejected.empty:
        return pd.DataFrame()

    # support_overlap is not in the SAT output, so join it back from top_candidates.
    top_candidates = pd.read_csv("results/top_candidates.csv")
    keys = ["benchmark", "optimization", "optimized_node", "original_candidate", "rank"]
    if "rank" not in rejected.columns:
        # Old rank-1 SAT files do not carry rank; recover it by node/candidate.
        rejected = rejected.merge(
            top_candidates[keys],
            on=["benchmark", "optimization", "optimized_node", "original_candidate"],
            how="left",
        )

    if "support_overlap" not in rejected.columns:
        rejected = rejected.merge(
            top_candidates[keys + ["support_overlap"]],
            on=keys,
            how="left",
        )
    rejected["support_overlap_bucket"] = rejected["support_overlap"].map(support_bucket)

    rows = []
    dimensions = [
        "optimization",
        "optimization_group",
        "benchmark_family",
        "combined_score_bucket",
        "support_overlap_bucket",
    ]
    for dim in dimensions:
        grouped = rejected.groupby(["validation_layer", dim], dropna=False)
        for (layer, value), group in grouped:
            rows.append({
                "validation_layer": layer,
                "dimension": dim,
                "bucket": value,
                "rejected_count": len(group),
                "avg_combined_score": group["combined_score"].mean(),
                "avg_support_overlap": group["support_overlap"].mean(),
            })
    return pd.DataFrame(rows)


def fmt_pct(value: float) -> str:
    return f"{value:.1%}"


def to_md(df: pd.DataFrame) -> str:
    if df.empty:
        return "_No rows._"
    return df.to_markdown(index=False)


def build_markdown(summary: pd.DataFrame, false_pos: pd.DataFrame) -> str:
    lines = ["# SAT Validation Layers\n"]
    lines.append("## Layer summary\n")
    display = summary.copy()
    for col in ["verification_rate", "rejection_rate", "inconclusive_rate"]:
        display[col] = display[col].map(fmt_pct)
    lines.append(to_md(display))
    lines.append("")

    lines.append("## Interpretation\n")
    lines.append(
        "- `exact_anchor_sanity` checks already-preserved signature matches. "
        "These should verify; they test whether the SAT pipeline accepts known matches."
    )
    lines.append(
        "- `rank1_nonexact_recovery` is the previous high-confidence rank-1 non-exact check."
    )
    lines.append(
        "- `topk_nonexact_recovery` checks high-score non-exact candidates below rank 1. "
        "Verified rows here would be genuine recovered correspondences missed by rank 1.\n"
    )

    lines.append("## False-positive analysis\n")
    if false_pos.empty:
        lines.append("No rejected non-exact candidates were available for analysis.\n")
    else:
        for dim in [
            "optimization",
            "optimization_group",
            "benchmark_family",
            "combined_score_bucket",
            "support_overlap_bucket",
        ]:
            lines.append(f"### By {dim}\n")
            sub = false_pos[false_pos["dimension"] == dim].copy()
            sub["avg_combined_score"] = sub["avg_combined_score"].map(lambda x: f"{x:.4f}")
            sub["avg_support_overlap"] = sub["avg_support_overlap"].map(
                lambda x: "n/a" if pd.isna(x) else f"{x:.4f}"
            )
            lines.append(to_md(sub))
            lines.append("")

    lines.append("## Research conclusion\n")
    lines.append(
        "Mild passes preserve many internal signatures, while aggressive passes destroy "
        "large parts of the internal correspondence structure. The heuristic score based "
        "on simulation, support overlap, and depth produces plausible candidates, but the "
        "SAT results show that plausible is not the same as equivalent. Formal CEC is "
        "therefore necessary before claiming recovered internal correspondences. In the "
        "current run, the heuristic is best interpreted as a ranking and triage signal, "
        "not as a standalone correspondence-recovery method.\n"
    )
    return "\n".join(lines)


def main() -> None:
    rank1 = load(RANK1, "rank1_nonexact_recovery")
    exact = load(EXACT, "exact_anchor_sanity")
    topk = load(TOPK, "topk_nonexact_recovery")

    summary = pd.DataFrame([
        summarize_layer(exact, "exact_anchor_sanity"),
        summarize_layer(rank1, "rank1_nonexact_recovery"),
        summarize_layer(topk, "topk_nonexact_recovery"),
    ])
    false_pos = false_positive_tables(rank1, topk)

    OUT_SUMMARY_CSV.parent.mkdir(parents=True, exist_ok=True)
    summary.to_csv(OUT_SUMMARY_CSV, index=False)
    false_pos.to_csv(OUT_FALSE_POS_CSV, index=False)
    OUT_MD.write_text(build_markdown(summary, false_pos), encoding="utf-8")

    print(f"Wrote {OUT_SUMMARY_CSV}")
    print(f"Wrote {OUT_FALSE_POS_CSV}")
    print(f"Wrote {OUT_MD}")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
