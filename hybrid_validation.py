"""
hybrid_validation.py

Hybrid node-correspondence validation: Python simulation ranking + ABC SAT sweep.

The Python ranking (Stage 1) is already implemented in analyze_blif_matches.py.
It's fast and gives good approximate results — but it can't *prove* equivalence.

This script adds Stage 2: for the top-K candidates from the Python ranking,
we call ABC's `dump_equiv` command which uses FRAIG (simulation + SAT internally)
to compute formally-proven cross-network node equivalence classes.  If a top
candidate pair lands in the same ABC equivalence class, we know for certain that
those two nodes compute the same Boolean function.

The mentor's exact feedback:
  "Another thing to look into is directly using the SAT sweeping tool inside ABC
  in order to identify exact matches and to get already simulations that have been
  used by this tool. [...] it would make sense to re-use already what is present
  in ABC. It would be a little bit harder to code into it but it would make the
  execution more efficient and faster."

How the hybrid flow works:
  1. Read top_candidates.csv  (Python simulation ranking, already done)
  2. For each unique (benchmark, optimization) pair:
       a. Run ABC dump_equiv on (original BLIF, optimised BLIF)
          → ABC computes equivalence classes via simulation + SAT
       b. Index the result as a set of (orig_node, opt_node) proven matches
  3. For each candidate row, check if (original_candidate, optimised_node)
     is in the ABC proven-match set
  4. Write hybrid_validated_candidates.csv with:
       - all original Python columns
       - abc_validated  (True / False)
       - abc_complement (True if the match is a Boolean complement)
       - abc_result     (human-readable verdict)
       - abc_log_file   (path to ABC log for debugging)

Usage:
  python3 hybrid_validation.py \\
      --abc-path .abc_build/abc_repo/abc \\
      --top-k-validate 20 \\
      --output-dir results/hybrid

  python3 hybrid_validation.py \\
      --abc-path .abc_build/abc_repo/abc \\
      --top-k-validate 20 \\
      --candidates results/sat_refinement_candidates.csv  # use already-filtered set

  # Run without --abc-path (uses $ABC env var or 'abc' on PATH):
  python3 hybrid_validation.py --top-k-validate 50
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path
from typing import Optional

import pandas as pd

# --- import the core sweep module from scripts/ --------------------------------
# We add the scripts/ directory to sys.path so you don't have to install anything.
_REPO_ROOT = Path(__file__).parent
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from abc_sat_sweep_validation import (
    find_abc,
    validate_blif_pair,
    EquivPair,
)


# ---------------------------------------------------------------------------
# Configuration defaults
# ---------------------------------------------------------------------------

DEFAULT_CANDIDATES_CSV = os.path.join("results", "top_candidates.csv")
DEFAULT_OUTPUT_DIR     = os.path.join("results", "hybrid")
DEFAULT_TOP_K          = 20          # validate the top-K candidates per (bench, opt)
DEFAULT_MIN_SCORE      = 0.70        # only bother checking candidates with this score or above


# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------

def load_candidates(csv_path: str, top_k: int, min_score: float) -> pd.DataFrame:
    """
    Load the candidate CSV and filter to the top-K per (benchmark, optimization).

    We use top_candidates.csv (the full ranked list) by default.  You can also
    pass the already-filtered sat_refinement_candidates.csv if you want to run
    hybrid validation on exactly the same set that sat_refinement_abc.py used.

    The min_score filter cuts out low-confidence candidates that probably
    aren't worth spending SAT time on.
    """
    if not os.path.exists(csv_path):
        raise FileNotFoundError(
            f"Candidate CSV not found: {csv_path}\n"
            "Run analyze_blif_matches.py first to generate top_candidates.csv"
        )

    df = pd.read_csv(csv_path)

    # Score filter
    if "combined_score" in df.columns:
        before = len(df)
        df = df[df["combined_score"] >= min_score]
        print(f"  Score filter (>= {min_score}): {before} → {len(df)} candidates")

    # Rank filter: keep only top-K per (benchmark, optimization)
    if "rank" in df.columns:
        df = df[df["rank"] <= top_k]
        print(f"  Rank filter (<= {top_k}): {len(df)} candidates remaining")
    else:
        # No rank column: sort by score and take top-K per group
        df = (
            df.sort_values("combined_score", ascending=False)
              .groupby(["benchmark", "optimization"], group_keys=False)
              .head(top_k)
        )
        print(f"  Top-{top_k} per group (no rank column): {len(df)} candidates remaining")

    return df.reset_index(drop=True)


def build_abc_match_index(
    benchmark: str,
    optimization: str,
    orig_blif: str,
    opt_blif: str,
    abc_bin: str,
    outdir: str,
) -> tuple[set[tuple[str, str]], set[tuple[str, str]], str]:
    """
    Run ABC dump_equiv for one (benchmark, optimization) pair and return
    two lookup sets for fast candidate validation:

      proven_matches    : set of (orig_node, opt_node) pairs proven equivalent
      complement_matches: set of (orig_node, opt_node) pairs proven complementary

    Also returns the path to the output directory (for the log_file column).

    The result is cached on disk (abc_equiv_matches.csv) so we only call ABC
    once per pair even if multiple candidates share the same BLIF pair.
    """
    pair_outdir = os.path.join(outdir, "abc_sweep", benchmark, optimization)

    result = validate_blif_pair(
        orig_blif = orig_blif,
        opt_blif  = opt_blif,
        abc_bin   = abc_bin,
        outdir    = pair_outdir,
        run_fraig = True,
    )

    proven:     set[tuple[str, str]] = set()
    complement: set[tuple[str, str]] = set()

    for pair in result["equiv_pairs"]:
        key = (pair.original_node, pair.optimised_node)
        if pair.is_complement:
            complement.add(key)
        else:
            proven.add(key)

    return proven, complement, pair_outdir


def annotate_candidates(
    df: pd.DataFrame,
    abc_bin: str,
    outdir: str,
) -> pd.DataFrame:
    """
    Add abc_validated, abc_complement, abc_result, and abc_log_file columns
    to the candidate DataFrame by running ABC dump_equiv for each unique
    (benchmark, optimization) pair.

    We process all candidates for a given BLIF pair in one ABC call, which
    is much more efficient than calling ABC once per candidate row (which is
    what sat_refinement_abc.py does for its CEC-per-node approach).  This is
    the main efficiency gain from reusing ABC's internal sweeper.
    """
    # New columns, defaulting to "not checked"
    df = df.copy()
    df["abc_validated"]  = False
    df["abc_complement"] = False
    df["abc_result"]     = "not_checked"
    df["abc_log_file"]   = ""

    # Figure out BLIF path columns — they differ between top_candidates.csv
    # (which doesn't have them) and sat_refinement_candidates.csv (which does).
    has_blif_cols = "orig_blif" in df.columns and "opt_blif" in df.columns

    groups = df.groupby(["benchmark", "optimization"])
    n_groups = len(groups)
    print(f"\n  Running ABC dump_equiv for {n_groups} (benchmark × optimization) pairs...")

    for idx, ((benchmark, optimization), group_df) in enumerate(groups, 1):
        print(f"  [{idx}/{n_groups}] {benchmark} / {optimization}", end="  ")
        t0 = time.time()

        # Get BLIF paths for this group
        if has_blif_cols:
            orig_blif = group_df["orig_blif"].iloc[0]
            opt_blif  = group_df["opt_blif"].iloc[0]
        else:
            # Reconstruct paths the same way select_sat_candidates.py does.
            orig_blif = os.path.join("variants", f"{benchmark}_original.blif")
            opt_blif  = os.path.join("variants", f"{benchmark}_{optimization}.blif")

        if not os.path.exists(orig_blif) or not os.path.exists(opt_blif):
            print(f"[SKIP — BLIF not found]")
            df.loc[group_df.index, "abc_result"] = "blif_not_found"
            continue

        try:
            proven, complement, pair_outdir = build_abc_match_index(
                benchmark, optimization, orig_blif, opt_blif, abc_bin, outdir
            )
        except Exception as exc:
            print(f"[ERROR — {exc}]")
            df.loc[group_df.index, "abc_result"] = f"error: {exc}"
            continue

        log_file_rel = os.path.join(pair_outdir, "dump_equiv.log")

        # Annotate every row in this group
        for row_idx in group_df.index:
            row = df.loc[row_idx]
            orig_cand = str(row.get("original_candidate", ""))
            opt_node  = str(row.get("optimized_node",    ""))

            # The Python ranking uses "optimized_node" (American spelling)
            # and "original_candidate" — we just need to look them up.
            key = (orig_cand, opt_node)
            if key in proven:
                df.loc[row_idx, "abc_validated"]  = True
                df.loc[row_idx, "abc_complement"] = False
                df.loc[row_idx, "abc_result"]     = "sat_proven_equivalent"
            elif key in complement:
                df.loc[row_idx, "abc_validated"]  = True
                df.loc[row_idx, "abc_complement"] = True
                df.loc[row_idx, "abc_result"]     = "sat_proven_complement"
            else:
                df.loc[row_idx, "abc_result"]     = "not_in_equiv_class"
            df.loc[row_idx, "abc_log_file"] = log_file_rel

        n_found = sum(1 for i in group_df.index
                      if df.loc[i, "abc_validated"])
        elapsed = time.time() - t0
        print(f"{n_found}/{len(group_df)} validated  ({elapsed:.1f}s)")

    return df


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

# Columns we want in the final hybrid CSV.
# The Python ranking columns are included first so the file is self-contained.
HYBRID_COLS = [
    "benchmark", "optimization",
    "optimized_node", "original_candidate",
    "rank", "combined_score",
    "simulation_similarity", "support_overlap", "depth_similarity",
    "is_exact_signature_match", "match_category",
    # ABC hybrid columns
    "abc_validated", "abc_complement", "abc_result", "abc_log_file",
]


def write_hybrid_csv(df: pd.DataFrame, csv_path: str) -> None:
    os.makedirs(os.path.dirname(csv_path) or ".", exist_ok=True)
    # Keep only the hybrid columns that actually exist in df
    cols = [c for c in HYBRID_COLS if c in df.columns]
    df[cols].to_csv(csv_path, index=False)
    print(f"\n  Wrote: {csv_path}")


def write_hybrid_markdown(df: pd.DataFrame, md_path: str) -> None:
    """
    Write a short human-readable Markdown summary of the hybrid validation run.
    This is the kind of summary you'd show a mentor or put in a research report.
    """
    os.makedirs(os.path.dirname(md_path) or ".", exist_ok=True)

    total = len(df)
    n_validated  = int(df["abc_validated"].sum())  if "abc_validated"  in df.columns else 0
    n_complement = int(df["abc_complement"].sum())  if "abc_complement" in df.columns else 0
    n_not_found  = int((df["abc_result"] == "not_in_equiv_class").sum()) if "abc_result" in df.columns else 0
    n_skipped    = total - n_validated - n_not_found - int((df["abc_result"].str.startswith("error") if "abc_result" in df.columns else pd.Series(dtype=bool)).sum())

    lines = [
        "# Hybrid Validation Summary\n",
        "This report combines the Python simulation ranking (Stage 1) with "
        "ABC SAT sweep / `dump_equiv` validation (Stage 2).\n",
        "## What is Stage 2 (ABC validation)?",
        "ABC's `dump_equiv` command builds a combined miter AIG from both networks, "
        "then runs FRAIG (simulation + SAT) internally to prove which nodes in the "
        "original and optimised circuits compute the same Boolean function. "
        "Any pair marked `abc_validated = True` is a **formally-proven** "
        "correspondence — not just a simulation estimate.\n",
        "## Result summary\n",
        f"| Metric | Value |",
        f"|---|---|",
        f"| Total candidates checked | {total} |",
        f"| ABC-validated (proven equivalent) | {n_validated} |",
        f"| ABC-validated (complement — same function, negated) | {n_complement} |",
        f"| Not in any ABC equivalence class | {n_not_found} |",
        f"| Skipped (BLIF not found / ABC error) | {n_skipped} |",
        "",
        "## Interpretation",
        "",
        "- **`abc_validated = True`** means ABC's SAT engine proved the two nodes "
          "compute the same function. This is stronger than a simulation match.",
        "- **`abc_result = not_in_equiv_class`** means the candidate pair appeared "
          "promising to the Python ranker, but ABC could not prove equivalence. "
          "This could mean they are genuinely not equivalent, or that ABC's SAT "
          "budget was exceeded (inconclusive).",
        "- **`abc_result = sat_proven_complement`** is an interesting case: the "
          "nodes are equivalent up to Boolean complementation — a sign that ABC "
          "re-encoded the logic with an inverted polarity.",
        "",
        "> **Note on efficiency:** this approach runs ABC once per (benchmark, optimization) "
        "pair and gets equivalences for ALL node pairs in one shot.  The previous "
        "`sat_refinement_abc.py` ran ABC once *per candidate pair*, which is much slower "
        "for large circuits with many candidates.",
    ]

    with open(md_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print(f"  Wrote: {md_path}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _parse_args(argv=None):
    p = argparse.ArgumentParser(
        description="Hybrid Python + ABC node-correspondence validation.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument(
        "--abc-path", default=None, metavar="PATH",
        help="Path to ABC binary (default: $ABC env var, then 'abc' on PATH)",
    )
    p.add_argument(
        "--candidates", default=DEFAULT_CANDIDATES_CSV, metavar="CSV",
        help=f"Input candidate CSV (default: {DEFAULT_CANDIDATES_CSV})",
    )
    p.add_argument(
        "--top-k-validate", type=int, default=DEFAULT_TOP_K, metavar="K",
        help=f"Validate top-K candidates per (benchmark, optimization) (default: {DEFAULT_TOP_K})",
    )
    p.add_argument(
        "--min-score", type=float, default=DEFAULT_MIN_SCORE, metavar="S",
        help=f"Minimum combined_score to consider (default: {DEFAULT_MIN_SCORE})",
    )
    p.add_argument(
        "--output-dir", default=DEFAULT_OUTPUT_DIR, metavar="DIR",
        help=f"Output directory (default: {DEFAULT_OUTPUT_DIR})",
    )
    return p.parse_args(argv)


def main(argv=None):
    args = _parse_args(argv)

    # --- Find ABC -------------------------------------------------------
    try:
        abc_bin = find_abc(args.abc_path)
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        print("\nHint: build ABC with:", file=sys.stderr)
        print("  make build-abc", file=sys.stderr)
        print("  then: ABC=$(pwd)/.abc_build/abc_repo/abc python3 hybrid_validation.py", file=sys.stderr)
        sys.exit(1)

    print(f"\nHybrid Validation")
    print(f"  ABC binary   : {abc_bin}")
    print(f"  Candidates   : {args.candidates}")
    print(f"  Top-K        : {args.top_k_validate}")
    print(f"  Min score    : {args.min_score}")
    print(f"  Output dir   : {args.output_dir}")

    # --- Load candidates ------------------------------------------------
    try:
        df = load_candidates(args.candidates, args.top_k_validate, args.min_score)
    except FileNotFoundError as exc:
        print(f"\nERROR: {exc}", file=sys.stderr)
        sys.exit(1)

    if df.empty:
        print("\nNo candidates after filtering — nothing to validate.")
        sys.exit(0)

    print(f"\n  Loaded {len(df)} candidates across "
          f"{df.groupby(['benchmark','optimization']).ngroups} (benchmark × optimization) pairs")

    # --- Run ABC validation ---------------------------------------------
    df = annotate_candidates(df, abc_bin=abc_bin, outdir=args.output_dir)

    # --- Write outputs --------------------------------------------------
    csv_path = os.path.join(args.output_dir, "hybrid_validated_candidates.csv")
    md_path  = os.path.join(args.output_dir, "hybrid_validation_summary.md")
    write_hybrid_csv(df, csv_path)
    write_hybrid_markdown(df, md_path)

    n_val = int(df["abc_validated"].sum()) if "abc_validated" in df.columns else 0
    print(f"\n  Done.  {n_val} / {len(df)} candidates formally validated by ABC.\n")


if __name__ == "__main__":
    main()
