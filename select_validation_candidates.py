#!/usr/bin/env python3
"""Build separate SAT validation candidate sets.

The main SAT pipeline checks rank-1 non-exact candidates.  For methodology we
also want two separate checks:

1. exact anchors: already-matched signatures that ABC should verify;
2. top-k non-exact: high-scoring non-exact candidates below rank 1.

Keeping these files separate prevents exact-anchor sanity checks from being
mistaken for recovered non-exact correspondences.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd


TOP_CANDIDATES = Path("results/top_candidates.csv")
EXACT_ANCHORS_OUT = Path("results/sat_exact_anchor_candidates.csv")
TOPK_NONEXACT_OUT = Path("results/sat_topk_nonexact_candidates.csv")

SCORE_THRESHOLD = 0.85
TOPK_MAX_RANK = 10


def _with_sat_paths(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["needs_sat_check"] = True
    df["orig_blif"] = "variants/" + df["benchmark"] + "_original.blif"
    df["opt_blif"] = "variants/" + df["benchmark"] + "_" + df["optimization"] + ".blif"
    return df


def _add_reason(df: pd.DataFrame, reason: str) -> pd.DataFrame:
    df = df.copy()
    df["sat_reason"] = reason + " (score " + df["combined_score"].map("{:.3f}".format) + ")"
    return df


def select_exact_anchors(df: pd.DataFrame) -> pd.DataFrame:
    """Select one exact-anchor candidate per optimized node when available."""
    anchors = df[
        (df["is_exact_signature_match"] == 1)
        & (df["rank"] == 1)
        & (df["combined_score"] >= SCORE_THRESHOLD)
    ].copy()
    anchors["match_category"] = "exact_anchor"
    anchors = _add_reason(anchors, "exact anchor SAT sanity check")
    return _with_sat_paths(anchors)


def select_topk_nonexact(df: pd.DataFrame) -> pd.DataFrame:
    """Select high-score non-exact candidates below rank 1 up to TOPK_MAX_RANK."""
    topk = df[
        (df["is_exact_signature_match"] == 0)
        & (df["rank"] > 1)
        & (df["rank"] <= TOPK_MAX_RANK)
        & (df["combined_score"] >= SCORE_THRESHOLD)
    ].copy()
    topk["match_category"] = "non_exact_candidate"
    topk = _add_reason(topk, f"top-{TOPK_MAX_RANK} non-exact SAT recovery check")
    return _with_sat_paths(topk)


def main() -> None:
    if not TOP_CANDIDATES.exists():
        raise FileNotFoundError(
            f"{TOP_CANDIDATES} not found. Run analyze_blif_matches.py first."
        )

    df = pd.read_csv(TOP_CANDIDATES)
    required = {"is_exact_signature_match", "rank", "combined_score"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(
            f"{TOP_CANDIDATES} is missing columns {sorted(missing)}. "
            "Regenerate results with analyze_blif_matches.py."
        )

    exact = select_exact_anchors(df)
    topk = select_topk_nonexact(df)

    EXACT_ANCHORS_OUT.parent.mkdir(parents=True, exist_ok=True)
    exact.to_csv(EXACT_ANCHORS_OUT, index=False)
    topk.to_csv(TOPK_NONEXACT_OUT, index=False)

    print(f"Wrote {len(exact)} exact-anchor candidates -> {EXACT_ANCHORS_OUT}")
    print(
        f"Wrote {len(topk)} top-{TOPK_MAX_RANK} non-exact candidates "
        f"(rank > 1, score >= {SCORE_THRESHOLD}) -> {TOPK_NONEXACT_OUT}"
    )

    if not topk.empty:
        print("\nTop-k candidate count by rank:")
        print(topk.groupby("rank").size().to_string())


if __name__ == "__main__":
    main()
