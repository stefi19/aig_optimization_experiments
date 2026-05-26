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

Methodological note (Carmine's feedback)
-----------------------------------------
The primary purpose of SAT refinement is to verify correspondences that
simulation-based exact matching MISSED — i.e., cases where the optimized node
and original candidate do NOT share an identical truth-table signature but still
look like a match from simulation/support scores.

Sending already-exact-signature-match pairs to ABC is useful only as a sanity
check ("ABC should always confirm these"), not as recovery of new correspondences.

By default (INCLUDE_EXACT_ANCHORS = False) this script excludes exact matches
from the SAT candidates so that the output represents genuine non-exact
refinement cases.

Set INCLUDE_EXACT_ANCHORS = True to also include exact-signature pairs, which
will then be tagged as match_category = "exact_anchor" to clearly distinguish
them from the real refinement work.
"""

import os
import pandas as pd

# ── Configuration ─────────────────────────────────────────────────────────────

INPUT_CSV = os.path.join("results", "top_candidates.csv")
OUTPUT_CSV = os.path.join("results", "sat_refinement_candidates.csv")

# Candidates with combined_score >= this threshold are flagged for SAT verification.
SAT_SCORE_THRESHOLD = 0.85

# Only keep the top-ranked candidate per optimized node (rank == 1).
TOP_RANK_ONLY = True

# When False (default): only non-exact-match candidates are selected for SAT.
# When True: exact-signature matches are also included, tagged as "exact_anchor"
# so the downstream summary can separate them from genuine refinement work.
INCLUDE_EXACT_ANCHORS = False


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
      - is_exact_signature_match == 0  (non-exact candidates only, unless
        INCLUDE_EXACT_ANCHORS is True)

    The is_exact_signature_match column is expected from analyze_blif_matches.py.
    If it is absent (e.g. old result file), all rows are treated as non-exact and
    a warning is printed.
    """
    filtered = df.copy()

    if TOP_RANK_ONLY and "rank" in filtered.columns:
        filtered = filtered[filtered["rank"] == 1]

    if "combined_score" in filtered.columns:
        filtered = filtered[filtered["combined_score"] >= SAT_SCORE_THRESHOLD]

    if "is_exact_signature_match" not in filtered.columns:
        print(
            "  WARNING: is_exact_signature_match column not found in top_candidates.csv.\n"
            "  Re-run analyze_blif_matches.py to generate it.\n"
            "  Treating all candidates as non-exact for now."
        )
        filtered["is_exact_signature_match"] = 0

    if not INCLUDE_EXACT_ANCHORS:
        n_before = len(filtered)
        filtered = filtered[filtered["is_exact_signature_match"] == 0]
        n_excluded = n_before - len(filtered)
        if n_excluded:
            print(
                f"  Excluded {n_excluded} exact-signature-match candidates "
                "(they are already confirmed matches — SAT would just be a sanity check).\n"
                "  Set INCLUDE_EXACT_ANCHORS = True in select_sat_candidates.py "
                "to include them as 'exact_anchor' rows."
            )

    return filtered


def annotate(df: pd.DataFrame) -> pd.DataFrame:
    """Add columns that a downstream SAT step would consume."""
    df = df.copy()

    # Flag for downstream tool
    df["needs_sat_check"] = True

    # Ensure match_category is present; derive from is_exact_signature_match if needed.
    if "match_category" not in df.columns:
        if "is_exact_signature_match" in df.columns:
            df["match_category"] = df["is_exact_signature_match"].apply(
                lambda v: "exact_anchor" if int(v) == 1 else "non_exact_candidate"
            )
        else:
            df["match_category"] = "non_exact_candidate"

    # Human-readable reason that explains why this candidate was selected.
    def _reason(row):
        if row.get("match_category") == "exact_anchor":
            return (
                f"exact signature match included only as an anchor/sanity check "
                f"(score {row['combined_score']:.3f})"
            )
        return (
            f"high-confidence non-exact candidate selected for ABC CEC refinement "
            f"(score {row['combined_score']:.3f})"
        )

    df["sat_reason"] = df.apply(_reason, axis=1)

    # BLIF file paths for the ABC CEC step.
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
    n_exact = int((filtered.get("is_exact_signature_match", pd.Series(dtype=int)) == 1).sum()) if "is_exact_signature_match" in filtered.columns else 0
    n_nonexact = len(filtered) - n_exact
    print(
        f"  After filtering (score >= {SAT_SCORE_THRESHOLD}, rank == 1, "
        f"INCLUDE_EXACT_ANCHORS={INCLUDE_EXACT_ANCHORS}): "
        f"{len(filtered)} rows  "
        f"({n_nonexact} non-exact candidates, {n_exact} exact anchors)"
    )

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
