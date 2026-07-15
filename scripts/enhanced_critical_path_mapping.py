#!/usr/bin/env python3
"""Join functional ranking features onto critical-path back-mapping rows."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from functional_ranking_features import RANKING_MODES  # noqa: E402

RESULTS = ROOT / "results"
DEFAULT_CRITICAL = RESULTS / "critical_path_mapping.csv"
DEFAULT_FEATURES = RESULTS / "cofactor_sensitivity" / "cofactor_sensitivity_features.csv"
OUT = RESULTS / "ranking_ablation" / "critical_path_enhanced_ranking.csv"
OUT_MD = RESULTS / "ranking_ablation" / "critical_path_enhanced_ranking.md"


def ranks_for_mode(features: pd.DataFrame, mode: str) -> pd.DataFrame:
    df = features.copy()
    df[mode] = pd.to_numeric(df[mode], errors="coerce").fillna(0.0)
    df["candidate_rank"] = pd.to_numeric(df["candidate_rank"], errors="coerce").fillna(999999)
    df = df.sort_values(
        ["benchmark", "optimization", "optimized_node", mode, "candidate_rank", "original_node"],
        ascending=[True, True, True, False, True, True],
    )
    df[f"{mode}_rank"] = df.groupby(["benchmark", "optimization", "optimized_node", "seed"]).cumcount() + 1
    return df[["benchmark", "optimization", "optimized_node", "original_node", "seed", f"{mode}_rank"]]


def build_enhanced_rows(critical: pd.DataFrame, features: pd.DataFrame) -> pd.DataFrame:
    feature_best = features.sort_values("seed").drop_duplicates(
        ["benchmark", "optimization", "optimized_node", "original_node"]
    )
    for mode in ("baseline", "full_combined"):
        ranks = ranks_for_mode(features, mode).sort_values("seed").drop_duplicates(
            ["benchmark", "optimization", "optimized_node", "original_node"]
        )
        feature_best = feature_best.merge(
            ranks,
            on=["benchmark", "optimization", "optimized_node", "original_node", "seed"],
            how="left",
        )
    join = critical.merge(
        feature_best,
        left_on=["benchmark", "optimization", "optimized_node", "mapped_original_node"],
        right_on=["benchmark", "optimization", "optimized_node", "original_node"],
        how="left",
        suffixes=("", "_feature"),
    )
    join["ranking_mode"] = "full_combined"
    join["baseline_rank"] = join.get("baseline_rank")
    join["enhanced_rank"] = join.get("full_combined_rank")
    join["rank_delta"] = join["baseline_rank"] - join["enhanced_rank"]
    join["functional_feature_mode"] = join.get("functional_feature_mode", "unavailable")
    join["functional_feature_evidence_level"] = join.get("functional_feature_evidence_level", "unresolved")
    columns = [
        "benchmark",
        "circuit",
        "optimization",
        "path_length",
        "path_index",
        "optimized_node",
        "mapped_original_node",
        "mapping_category",
        "ranking_mode",
        "baseline_rank",
        "enhanced_rank",
        "rank_delta",
        "cofactor_consistency_score",
        "max_cofactor_error",
        "sensitivity_cosine_similarity",
        "boolean_difference_similarity",
        "functional_feature_mode",
        "functional_feature_evidence_level",
    ]
    for column in columns:
        if column not in join:
            join[column] = ""
    return join[columns]


def write_summary(df: pd.DataFrame, path: Path) -> None:
    unresolved = int((df["mapping_category"] == "unresolved").sum()) if not df.empty else 0
    joined = int(df["enhanced_rank"].notna().sum()) if "enhanced_rank" in df else 0
    lines = [
        "# Enhanced Critical-Path Ranking Join",
        "",
        "This file joins cofactor/sensitivity ranking evidence onto the existing critical-path mapping rows. It does not change mapping-category semantics and does not claim new equivalence without SAT/CEC.",
        "",
        f"- Critical-path rows: {len(df):,}",
        f"- Rows with enhanced rank evidence: {joined:,}",
        f"- Unresolved rows in the existing mapping: {unresolved:,}",
        "",
        "The lightweight run reports rank deltas for already mapped rows. It does not yet rerun SAT/CEC with a new validation budget, so unresolved critical-path recovery is unchanged unless future validation is added.",
    ]
    if not df.empty:
        lines.extend(["", "## Rank Delta Summary", ""])
        lines.append(df[["baseline_rank", "enhanced_rank", "rank_delta"]].describe().reset_index().to_markdown(index=False, floatfmt=".3f"))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--critical-path-csv", type=Path, default=DEFAULT_CRITICAL)
    parser.add_argument("--features-csv", type=Path, default=DEFAULT_FEATURES)
    parser.add_argument("--output-csv", type=Path, default=OUT)
    parser.add_argument("--output-summary", type=Path, default=OUT_MD)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if not args.critical_path_csv.exists():
        raise SystemExit(f"missing critical-path CSV: {args.critical_path_csv}")
    if not args.features_csv.exists():
        raise SystemExit(f"missing feature CSV: {args.features_csv}")
    critical = pd.read_csv(args.critical_path_csv)
    features = pd.read_csv(args.features_csv)
    out = build_enhanced_rows(critical, features)
    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.output_csv, index=False)
    write_summary(out, args.output_summary)
    print(f"Wrote enhanced critical-path ranking rows to {args.output_csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
