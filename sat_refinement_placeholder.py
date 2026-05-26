"""
sat_refinement_placeholder.py

Filters the top-K candidate matches produced by analyze_blif_matches.py and writes
a CSV of high-confidence candidates that would be submitted to a SAT solver in a
full implementation.

NOTE: This script does NOT call any SAT solver. The actual SAT-based verification step
is not yet implemented. This placeholder marks where that step belongs in the pipeline
and produces the input file it would consume.

Intended future pipeline:
  analyze_blif_matches.py  →  top_candidates.csv
                           →  [this script]  →  sat_refinement_candidates.csv
                           →  [SAT solver]   →  verified correspondences
"""

import os
import pandas as pd

# ── Configuration ─────────────────────────────────────────────────────────────

INPUT_CSV = os.path.join("results", "top_candidates.csv")
OUTPUT_CSV = os.path.join("results", "sat_refinement_candidates.csv")

# Candidates with combined_score >= this threshold are flagged for SAT verification.
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

    # Placeholder: a real implementation would populate these columns with
    # the BLIF file paths and node names needed to construct the SAT instance.
    df["orig_blif"] = "benchmarks/" + df["benchmark"] + ".blif"
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
    cols = [c for c in ["benchmark", "optimization", "combined_score", "needs_sat_check"]
            if c in annotated.columns]
    summary = (
        annotated.groupby(["benchmark", "optimization"])
        .size()
        .reset_index(name="candidate_count")
    )
    print(summary.to_string(index=False))

    print(
        "\nNOTE: SAT verification is NOT implemented. "
        "sat_refinement_candidates.csv marks candidates for a future SAT step."
    )


if __name__ == "__main__":
    main()
