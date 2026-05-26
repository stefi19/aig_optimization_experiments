"""
select_sat_candidates.py

Selects high-confidence rank-1 candidates from top_candidates.csv and writes
the filtered set to sat_refinement_candidates.csv for the ABC CEC verification step.

Pipeline position:
  analyze_blif_matches.py  →  results/top_candidates.csv
  [this script]            →  results/sat_refinement_candidates.csv
  sat_refinement_abc.py    →  results/sat_verified_candidates.csv
  summarize_sat_results.py →  results/sat_summary.csv / sat_summary.md

This script does NOT call any SAT solver itself.  It only filters candidates
and annotates them with the BLIF file paths that sat_refinement_abc.py will use.
"""

import os
import pandas as pd

# ── Configuration ─────────────────────────────────────────────────────────────

INPUT_CSV = os.path.join("results", "top_candidates.csv")
OUTPUT_CSV = os.path.join("results", "sat_refinement_candidates.csv")

# Candidates with combined_score >= this threshold are flagged for SAT verification.
# 0.85 was chosen so that only the very strong simulation+support matches are forwarded;
# weaker candidates have too high a chance of being false positives to be worth the
# ABC CEC runtime cost.
SAT_SCORE_THRESHOLD = 0.85

# Only keep the top-ranked candidate per optimized node (rank == 1).
# In a real pipeline you might keep top-3 and verify all of them.
TOP_RANK_ONLY = True


def load_candidates(path: str) -> pd.DataFrame:
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Input file not found: {path}\n"
            "Run analyze_blif_matches.py first to generate top_candidates.csv"
        )
    df = pd.read_csv(path)
    return df


def filter_for_sat(df: pd.DataFrame) -> pd.DataFrame:
    """
    Select candidates that are strong enough to be worth checking with a SAT solver.

    Criteria:
      - combined_score >= SAT_SCORE_THRESHOLD
      - rank == 1  (best match per optimized node, if TOP_RANK_ONLY is set)
    """
    filtered = df.copy()

    if TOP_RANK_ONLY and "rank" in filtered.columns:
        filtered = filtered[filtered["rank"] == 1]

    if "combined_score" in filtered.columns:
        filtered = filtered[filtered["combined_score"] >= SAT_SCORE_THRESHOLD]

    return filtered


def annotate(df: pd.DataFrame) -> pd.DataFrame:
    """Add columns that a downstream SAT step would consume."""
    df = df.copy()

    # Flag for downstream tool
    df["needs_sat_check"] = True

    # Human-readable reason
    df["sat_reason"] = df["combined_score"].apply(
        lambda s: f"high simulation+support score ({s:.3f}) — exact equivalence unverified"
    )

    # The analysis script (analyze_blif_matches.py) compares
    # variants/<bench>_original.blif  vs  variants/<bench>_<opt>.blif
    # so the BLIF paths for the SAT check must point to those same files.
    df["orig_blif"] = "variants/" + df["benchmark"] + "_original.blif"
    df["opt_blif"] = (
        "variants/" + df["benchmark"] + "_" + df["optimization"] + ".blif"
    )

    return df


def main():
    print(f"Loading candidates from: {INPUT_CSV}")
    df = load_candidates(INPUT_CSV)
    print(f"  Total candidate rows: {len(df)}")

    filtered = filter_for_sat(df)
    print(f"  After filtering (score >= {SAT_SCORE_THRESHOLD}, rank == 1): {len(filtered)} rows")

    if filtered.empty:
        print("  No candidates met the threshold. Nothing to write.")
        return

    annotated = annotate(filtered)
    os.makedirs("results", exist_ok=True)
    annotated.to_csv(OUTPUT_CSV, index=False)
    print(f"  Wrote: {OUTPUT_CSV}")

    # Summary by benchmark
    print("\nCandidates by benchmark/optimization:")
    summary = (
        annotated.groupby(["benchmark", "optimization"])
        .size()
        .reset_index(name="candidate_count")
    )
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
