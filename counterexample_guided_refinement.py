#!/usr/bin/env python3

"""
counterexample_guided_refinement.py
=====================================
Prototype CEGAR-style refinement of node-level correspondence candidates.

Motivation
----------
After ABC equivalence checking (sat_refinement_abc.py), some rank-1 candidates
are marked *rejected* — ABC formally proved the two nodes compute different
Boolean functions.  Standard top-K ranking ignores these rejections entirely:
the next run of analyze_blif_matches.py would score the same candidate at the
same high rank without any memory of the failed check.

This script implements a lightweight prototype of the *counterexample-guided
abstraction refinement* (CEGAR) loop idea applied to candidate ranking:

  "A rejected candidate is evidence that the local feature space (simulation
   similarity, support overlap, depth similarity) around that candidate is
   *misleading*.  Other candidates for the same optimized node that have
   similar feature vectors to the rejected one should be penalised."

The word "counterexample" is used loosely here.  In classical CEGAR a
counterexample is a concrete input assignment that distinguishes two states.
Here the "counterexample" is the rejection decision itself: ABC's CEC proved
non-equivalence, which means the score vector of the rejected pair is a
*spurious high-score region* — a region of feature space where the ranking
metric confidently but incorrectly predicted equivalence.

The prototype is intentionally simple and transparent:

  1.  Load top_candidates.csv (all ranked candidates).
  2.  Load sat_verified_candidates.csv (with sat_status column).
  3.  For each rejected pair (optimized_node, rejected_original):
        - Look up its feature vector v_rej = (sim, support, depth).
        - For every other candidate of the same optimized node:
            penalty_i += REJECTION_WEIGHT * feature_sim(v_rej, v_i)
  4.  Compute a refined score:
        refined_score = max(0, original_combined_score - penalty)
  5.  Re-rank candidates per optimized node by refined_score.
  6.  Write results/cegar_refined_candidates.csv and cegar_summary.md.

Feature similarity between two score vectors is computed as:
  feature_sim(a, b) = 1 - ||a - b||_1 / 3
  where the 3 components are (simulation_similarity, support_overlap,
  depth_similarity), each in [0, 1], so the L1 distance is bounded by 3.

This gives feature_sim = 1.0 for identical vectors and 0.0 for maximally
distant ones.  A candidate is penalised most heavily when it looks exactly
like a rejected one; the penalty decays linearly as the feature vectors
diverge.

Limitations (known, by design)
-------------------------------
- The penalty is additive across multiple rejections for the same node.  If
  there are many rejected candidates, total penalties can exceed the original
  score even for clearly good candidates.  REJECTION_WEIGHT is set
  conservatively (0.20) to limit this.
- This prototype never re-queries ABC.  A real CEGAR loop would verify the
  new rank-1 candidate, potentially generating another rejection, and iterate.
  That extension is left for a future script (cegar_loop.py).
- Inconclusive candidates are treated as neutral (no penalty, no bonus).
- Only rank-1 rejections from the SAT stage are currently available (because
  sat_refinement_placeholder.py forwards only rank == 1 above the score
  threshold).  Rejected rank-2/3 candidates would further improve the
  penalty signal.

Outputs
-------
  results/cegar_refined_candidates.csv
      All original candidates with added columns:
        penalty          — total penalty applied to this candidate
        refined_score    — max(0, combined_score - penalty)
        cegar_rank       — new rank after re-scoring (per optimized node)
        rank_change      — original rank - cegar_rank (positive = rose, negative = fell)
        is_rejected_pair — True if this exact pair was marked rejected by ABC

  results/cegar_summary.md
      Markdown report with:
        - data availability and config section
        - per-(benchmark, optimization) table: nodes affected, rank changes,
          refined rank-1 score
        - global rollup
        - interpretation

Usage
-----
  python3 counterexample_guided_refinement.py
  make cegar-refine
"""

import csv
import math
import os
import statistics
from collections import defaultdict

import pandas as pd

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

CANDIDATES_CSV = os.path.join("results", "top_candidates.csv")
SAT_CSV        = os.path.join("results", "sat_verified_candidates.csv")

OUTPUT_CSV = os.path.join("results", "cegar_refined_candidates.csv")
OUTPUT_MD  = os.path.join("results", "cegar_summary.md")

# Weight applied to the penalty term for each rejected candidate.
# Must be in (0, 1].  Lower → more conservative penalisation.
# 0.20 means a candidate identical to a rejected one loses 20% of its score.
REJECTION_WEIGHT: float = 0.20

# Feature columns used to compute similarity between candidates.
# All three are in [0, 1], so L1 distance is bounded by len(FEATURE_COLS) = 3.
FEATURE_COLS: list[str] = [
    "simulation_similarity",
    "support_overlap",
    "depth_similarity",
]


# ---------------------------------------------------------------------------
# I/O helpers
# ---------------------------------------------------------------------------

def load_candidates(path: str) -> pd.DataFrame | None:
    """Load top_candidates.csv.  Returns None if the file is missing."""
    if not os.path.exists(path):
        print(f"  [warn] Candidates file not found: {path}")
        print("         Run analyze_blif_matches.py first.")
        return None
    df = pd.read_csv(path)
    # Validate required columns
    required = {"benchmark", "optimization", "optimized_node",
                "original_candidate", "rank", "combined_score"} | set(FEATURE_COLS)
    missing = required - set(df.columns)
    if missing:
        print(f"  [warn] Missing columns in {path}: {missing}")
        return None
    return df


def load_sat_results(path: str) -> pd.DataFrame | None:
    """Load sat_verified_candidates.csv.  Returns None if the file is missing."""
    if not os.path.exists(path):
        print(f"  [info] SAT results not found: {path}")
        print("         No rejections available; CEGAR penalties will be zero.")
        return None
    df = pd.read_csv(path)
    required = {"benchmark", "optimization", "optimized_node",
                "original_candidate", "sat_status"}
    missing = required - set(df.columns)
    if missing:
        print(f"  [warn] Missing columns in {path}: {missing}")
        return None
    return df


# ---------------------------------------------------------------------------
# Rejection index
# ---------------------------------------------------------------------------

def build_rejection_index(
    candidates: pd.DataFrame,
    sat_df: pd.DataFrame | None,
) -> dict[tuple[str, str, str], list[dict[str, float]]]:
    """
    For each (benchmark, optimization, optimized_node) that has at least one
    rejected SAT result, return the list of rejected candidate feature vectors.

    Each feature vector is a dict {col: value} for cols in FEATURE_COLS,
    looked up from candidates (which has the detailed score columns that
    sat_verified_candidates.csv does not carry).

    Returns
    -------
    Dict mapping (benchmark, optimization, optimized_node) →
        [{"simulation_similarity": ..., "support_overlap": ..., "depth_similarity": ...}, ...]
    """
    if sat_df is None:
        return {}

    rejected = sat_df[sat_df["sat_status"] == "rejected"].copy()
    if rejected.empty:
        return {}

    # Build a lookup from (bench, opt, opt_node, orig_cand) → feature row in candidates
    cand_lookup: dict[tuple, dict[str, float]] = {}
    for _, row in candidates.iterrows():
        key = (
            row["benchmark"], row["optimization"],
            row["optimized_node"], row["original_candidate"],
        )
        cand_lookup[key] = {col: float(row[col]) for col in FEATURE_COLS}

    index: dict[tuple[str, str, str], list[dict[str, float]]] = defaultdict(list)

    for _, rej_row in rejected.iterrows():
        key4 = (
            rej_row["benchmark"], rej_row["optimization"],
            rej_row["optimized_node"], rej_row["original_candidate"],
        )
        features = cand_lookup.get(key4)
        if features is None:
            # Rejected pair not found in top_candidates (e.g. it was above
            # threshold but not kept in top-K for this view); skip.
            print(
                f"  [info] Rejected pair not found in top_candidates: "
                f"{rej_row['optimized_node']} → {rej_row['original_candidate']} "
                f"({rej_row['benchmark']}/{rej_row['optimization']})"
            )
            continue

        node_key = (rej_row["benchmark"], rej_row["optimization"], rej_row["optimized_node"])
        index[node_key].append(features)

    return dict(index)


# ---------------------------------------------------------------------------
# Feature similarity
# ---------------------------------------------------------------------------

def feature_sim(v_a: dict[str, float], v_b: dict[str, float]) -> float:
    """
    Similarity between two feature vectors in [0, 1].

    Defined as 1 - L1_distance(a, b) / len(FEATURE_COLS).

    Both vectors are expected to have keys equal to FEATURE_COLS.
    Each component is in [0, 1], so the L1 distance is bounded by
    len(FEATURE_COLS) and the result is always in [0, 1].
    """
    l1 = sum(abs(v_a[col] - v_b[col]) for col in FEATURE_COLS)
    return 1.0 - l1 / len(FEATURE_COLS)


# ---------------------------------------------------------------------------
# Penalty computation
# ---------------------------------------------------------------------------

def compute_penalty(
    candidate_features: dict[str, float],
    rejected_vectors: list[dict[str, float]],
) -> float:
    """
    Total penalty for a candidate given a list of rejected feature vectors.

    penalty = REJECTION_WEIGHT * max over rejected vectors of feature_sim

    We use the *maximum* (not the sum) so that having many rejected
    candidates with similar feature vectors does not unfairly amplify
    the penalty beyond what a single highly-similar rejection already
    implies.  The maximum captures "this candidate looks like the most
    suspicious rejected one".
    """
    if not rejected_vectors:
        return 0.0
    sims = [feature_sim(candidate_features, rv) for rv in rejected_vectors]
    return REJECTION_WEIGHT * max(sims)


# ---------------------------------------------------------------------------
# Core refinement
# ---------------------------------------------------------------------------

def refine(
    candidates: pd.DataFrame,
    rejection_index: dict[tuple, list[dict]],
    sat_df: pd.DataFrame | None,
) -> pd.DataFrame:
    """
    Apply CEGAR penalties and re-rank.

    Adds columns:
        penalty, refined_score, cegar_rank, rank_change, is_rejected_pair

    Returns the augmented DataFrame, sorted by
    (benchmark, optimization, optimized_node, cegar_rank).
    """
    df = candidates.copy()

    # Build set of rejected (bench, opt, opt_node, orig_cand) for is_rejected_pair flag
    rejected_pairs: set[tuple] = set()
    if sat_df is not None:
        rej = sat_df[sat_df["sat_status"] == "rejected"]
        for _, r in rej.iterrows():
            rejected_pairs.add(
                (r["benchmark"], r["optimization"],
                 r["optimized_node"], r["original_candidate"])
            )

    penalties: list[float] = []
    refined_scores: list[float] = []
    is_rejected: list[bool] = []

    for _, row in df.iterrows():
        node_key = (row["benchmark"], row["optimization"], row["optimized_node"])
        rejected_vecs = rejection_index.get(node_key, [])

        cand_feats = {col: float(row[col]) for col in FEATURE_COLS}
        pen = compute_penalty(cand_feats, rejected_vecs)

        pair_key = (
            row["benchmark"], row["optimization"],
            row["optimized_node"], row["original_candidate"],
        )
        is_rej = pair_key in rejected_pairs

        penalties.append(pen)
        refined_scores.append(max(0.0, float(row["combined_score"]) - pen))
        is_rejected.append(is_rej)

    df["penalty"]          = penalties
    df["refined_score"]    = refined_scores
    df["is_rejected_pair"] = is_rejected

    # Re-rank per (benchmark, optimization, optimized_node) by refined_score desc.
    # Ties broken by original rank (ascending) so that prior evidence is respected.
    df = df.sort_values(
        ["benchmark", "optimization", "optimized_node", "refined_score", "rank"],
        ascending=[True, True, True, False, True],
    )

    cegar_ranks: list[int] = []
    current_node = None
    node_counter = 0

    for _, row in df.iterrows():
        node_id = (row["benchmark"], row["optimization"], row["optimized_node"])
        if node_id != current_node:
            current_node = node_id
            node_counter = 0
        node_counter += 1
        cegar_ranks.append(node_counter)

    df["cegar_rank"]  = cegar_ranks
    df["rank_change"] = df["rank"].astype(int) - df["cegar_rank"]

    return df.reset_index(drop=True)


# ---------------------------------------------------------------------------
# Summary computation
# ---------------------------------------------------------------------------

def compute_summary(refined_df: pd.DataFrame) -> list[dict]:
    """
    Compute per-(benchmark, optimization) summary metrics.

    Metrics
    -------
    total_nodes          — distinct optimized nodes
    nodes_with_penalty   — nodes that had at least one rejected candidate
    nodes_rank1_changed  — nodes whose cegar_rank-1 candidate differs from original rank-1
    avg_refined_rank1    — mean refined_score of the new rank-1 candidate
    avg_original_rank1   — mean combined_score of the original rank-1 candidate
    avg_penalty_rank1    — mean penalty applied to the new rank-1 candidate
    n_rejected_pairs     — total rejected pairs in this group
    """
    rows: list[dict] = []

    for (bench, opt), group in refined_df.groupby(["benchmark", "optimization"]):
        orig_r1  = group[group["rank"]       == 1]
        cegar_r1 = group[group["cegar_rank"] == 1]

        total_nodes = group["optimized_node"].nunique()

        nodes_with_penalty = (
            group[group["penalty"] > 0]["optimized_node"].nunique()
        )

        # A node's rank-1 changed if the cegar_rank-1 original_candidate ≠ rank-1 one
        orig_r1_map  = dict(zip(orig_r1["optimized_node"],  orig_r1["original_candidate"]))
        cegar_r1_map = dict(zip(cegar_r1["optimized_node"], cegar_r1["original_candidate"]))

        changed = sum(
            1 for node in cegar_r1_map
            if cegar_r1_map[node] != orig_r1_map.get(node)
        )

        n_rejected = int(group["is_rejected_pair"].sum())

        rows.append({
            "benchmark":           bench,
            "optimization":        opt,
            "total_nodes":         total_nodes,
            "nodes_with_penalty":  nodes_with_penalty,
            "nodes_rank1_changed": changed,
            "avg_refined_rank1":   (
                float(cegar_r1["refined_score"].mean())
                if not cegar_r1.empty else float("nan")
            ),
            "avg_original_rank1":  (
                float(orig_r1["combined_score"].mean())
                if not orig_r1.empty else float("nan")
            ),
            "avg_penalty_rank1":   (
                float(cegar_r1["penalty"].mean())
                if not cegar_r1.empty else float("nan")
            ),
            "n_rejected_pairs":    n_rejected,
        })

    return rows


# ---------------------------------------------------------------------------
# Markdown report
# ---------------------------------------------------------------------------

def _fmt(val, is_rate: bool = False) -> str:
    if isinstance(val, float):
        if math.isnan(val):
            return "n/a"
        return f"{val:.1%}" if is_rate else f"{val:.4f}"
    if isinstance(val, int):
        return str(val)
    return str(val)


def _md_table(rows: list[dict], cols: list[str], rate_cols: set[str] = frozenset()) -> str:
    if not rows:
        return "_No data._"
    header = "| " + " | ".join(cols) + " |"
    sep    = "| " + " | ".join(["---"] * len(cols)) + " |"
    lines  = [header, sep]
    for row in rows:
        cells = [_fmt(row.get(c, ""), c in rate_cols) for c in cols]
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def build_markdown(
    summary_rows: list[dict],
    refined_df: pd.DataFrame | None,
    candidates_available: bool,
    sat_available: bool,
    n_rejected: int,
) -> str:
    lines: list[str] = []
    lines.append("# CEGAR-Style Candidate Refinement — Prototype\n")

    lines.append(
        "> **Prototype notice**: This script implements a lightweight approximation of "
        "counterexample-guided refinement.  It does *not* call ABC or any SAT solver; "
        "it uses previously recorded ABC rejections as penalty signals.  "
        "A real CEGAR loop would iteratively re-verify the new rank-1 candidate "
        "after each refinement step.  See the module docstring for known limitations.\n"
    )

    # ── Data availability ─────────────────────────────────────────────────────
    lines.append("## Data availability\n")
    lines.append(
        f"- `top_candidates.csv`: "
        f"{'✅ loaded' if candidates_available else '❌ missing — run `analyze_blif_matches.py`'}"
    )
    lines.append(
        f"- `sat_verified_candidates.csv`: "
        f"{'✅ loaded' if sat_available else '❌ missing — run `sat_refinement_abc.py`'}"
    )
    lines.append(
        f"- Rejected pairs used as penalty sources: **{n_rejected}**\n"
    )

    if not candidates_available:
        lines.append("> Cannot compute any metrics without `top_candidates.csv`.\n")
        return "\n".join(lines)

    if not sat_available or n_rejected == 0:
        lines.append(
            "> No rejected candidates available.  "
            "All CEGAR penalties are zero — refined scores equal original scores.  "
            "Re-run after ABC equivalence checking produces at least one rejection.\n"
        )

    # ── Configuration ─────────────────────────────────────────────────────────
    lines.append("## Configuration\n")
    lines.append(
        f"- `REJECTION_WEIGHT` = **{REJECTION_WEIGHT}** — "
        f"fraction of original score a candidate identical to a rejected one loses\n"
        f"- Feature space: `{FEATURE_COLS}`\n"
        f"- Penalty formula: `penalty = {REJECTION_WEIGHT} × max_over_rejections(feature_sim)`\n"
        f"- Refined score: `max(0, combined_score − penalty)`\n"
        f"- Similarity metric: `1 − L1_distance / {len(FEATURE_COLS)}`\n"
    )

    # ── Per-group summary ─────────────────────────────────────────────────────
    lines.append("## Per-(benchmark, optimization) summary\n")
    cols = [
        "benchmark", "optimization",
        "total_nodes", "nodes_with_penalty", "nodes_rank1_changed",
        "n_rejected_pairs",
        "avg_original_rank1", "avg_refined_rank1", "avg_penalty_rank1",
    ]
    lines.append(_md_table(summary_rows, cols))
    lines.append("")

    # ── Global rollup ─────────────────────────────────────────────────────────
    if summary_rows:
        lines.append("## Global rollup\n")
        total_nodes     = sum(r["total_nodes"]         for r in summary_rows)
        penalized_nodes = sum(r["nodes_with_penalty"]  for r in summary_rows)
        changed_nodes   = sum(r["nodes_rank1_changed"] for r in summary_rows)
        total_rejected  = sum(r["n_rejected_pairs"]    for r in summary_rows)

        orig_r1_scores  = [r["avg_original_rank1"] for r in summary_rows
                           if not math.isnan(r["avg_original_rank1"])]
        ref_r1_scores   = [r["avg_refined_rank1"]  for r in summary_rows
                           if not math.isnan(r["avg_refined_rank1"])]

        rollup = [{
            "total_nodes":            total_nodes,
            "nodes_with_penalty":     penalized_nodes,
            "pct_penalized":          penalized_nodes / total_nodes if total_nodes else 0.0,
            "nodes_rank1_changed":    changed_nodes,
            "pct_rank1_changed":      changed_nodes / total_nodes if total_nodes else 0.0,
            "n_rejected_pairs":       total_rejected,
            "avg_original_rank1":     statistics.mean(orig_r1_scores) if orig_r1_scores else float("nan"),
            "avg_refined_rank1":      statistics.mean(ref_r1_scores)  if ref_r1_scores  else float("nan"),
        }]
        rollup_cols = [
            "total_nodes", "nodes_with_penalty", "pct_penalized",
            "nodes_rank1_changed", "pct_rank1_changed",
            "n_rejected_pairs",
            "avg_original_rank1", "avg_refined_rank1",
        ]
        lines.append(_md_table(rollup, rollup_cols, rate_cols={"pct_penalized", "pct_rank1_changed"}))
        lines.append("")

    # ── Rank changes ─────────────────────────────────────────────────────────
    if refined_df is not None and not refined_df.empty:
        promoted = refined_df[refined_df["rank_change"] > 0]
        demoted  = refined_df[refined_df["rank_change"] < 0]
        lines.append("## Rank changes\n")
        lines.append(
            f"- **{len(promoted)}** candidate rows moved to a higher rank (rank_change > 0)\n"
            f"- **{len(demoted)}** candidate rows moved to a lower rank (rank_change < 0)\n"
            f"- **{len(refined_df) - len(promoted) - len(demoted)}** rows unchanged\n"
        )

        # Show the most impactful demotions (largest rank_change magnitude)
        demoted_top = (
            demoted.sort_values("rank_change")
            .head(10)[["benchmark", "optimization", "optimized_node",
                        "original_candidate", "combined_score",
                        "penalty", "refined_score", "rank", "cegar_rank"]]
        )
        if not demoted_top.empty:
            lines.append("### Most penalised candidates (largest rank drops)\n")
            lines.append(demoted_top.to_markdown(index=False))
            lines.append("")

    # ── Interpretation ────────────────────────────────────────────────────────
    lines.append("## Interpretation\n")
    lines.append(
        "**What the penalty signal captures**: when ABC proves two nodes are *not* "
        "equivalent, the feature vector of that rejected pair identifies a region of "
        "score space where the simulation / support / depth signals are collectively "
        "misleading.  Other candidates for the same optimised node that fall in the "
        "same region are penalised, under the hypothesis that the misleading pattern "
        "is local to that region.\n"
    )
    lines.append(
        "**When penalties are zero**: if no ABC rejections are available "
        "(e.g. the SAT stage has not been run, or all checked candidates were verified), "
        "the refined ranking is identical to the original ranking.  "
        "This is the correct behaviour — without evidence of spurious regions, "
        "no adjustment is warranted.\n"
    )
    lines.append(
        "**`nodes_rank1_changed`**: the most actionable metric.  "
        "A value > 0 means CEGAR refinement re-ordered the top candidate for at least "
        "one node.  In a full iterative loop these new rank-1 candidates would be "
        "submitted to ABC next; the loop terminates when no new rejections appear.\n"
    )
    lines.append(
        "**Known limitations of this prototype**:\n"
        "1. Penalties are not iterated — a single refinement pass is performed.\n"
        "2. Only rank-1 ABC results are currently available as rejection sources.\n"
        "3. The feature similarity is a coarse L1 proxy; a learned distance metric "
        "would be more precise.\n"
        "4. `refined_score` is clipped at 0 and may not preserve the relative ordering "
        "of heavily penalised candidates well.\n"
    )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CSV writer
# ---------------------------------------------------------------------------

OUTPUT_FIELDS = [
    "benchmark", "optimization", "optimized_node", "rank",
    "original_candidate", "combined_score",
    "simulation_similarity", "support_overlap", "depth_similarity",
    "optimized_level", "original_level",
    "penalty", "refined_score", "cegar_rank", "rank_change",
    "is_rejected_pair",
]


def _write_csv(path: str, df: pd.DataFrame, fields: list[str]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    # Only write columns that actually exist in df
    cols = [c for c in fields if c in df.columns]
    df[cols].to_csv(path, index=False)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    os.makedirs("results", exist_ok=True)

    print("=" * 70)
    print("CEGAR-style candidate refinement  [prototype]")
    print("=" * 70)

    # ── Load inputs ───────────────────────────────────────────────────────────
    print("\nLoading candidates …")
    candidates = load_candidates(CANDIDATES_CSV)

    print("Loading SAT results …")
    sat_df = load_sat_results(SAT_CSV)

    if candidates is None:
        md = build_markdown(
            summary_rows=[], refined_df=None,
            candidates_available=False, sat_available=(sat_df is not None),
            n_rejected=0,
        )
        with open(OUTPUT_MD, "w", encoding="utf-8") as fh:
            fh.write(md)
        print(f"\nWrote placeholder report → {OUTPUT_MD}")
        return

    # ── Count rejections ──────────────────────────────────────────────────────
    n_rejected = 0
    if sat_df is not None:
        n_rejected = int((sat_df["sat_status"] == "rejected").sum())
    print(f"\nRejected pairs available: {n_rejected}")

    # ── Build rejection index ─────────────────────────────────────────────────
    print("Building rejection index …")
    rejection_index = build_rejection_index(candidates, sat_df)
    n_nodes_with_rejections = len(rejection_index)
    print(f"Optimised nodes with ≥1 rejection: {n_nodes_with_rejections}")

    # ── Refine ────────────────────────────────────────────────────────────────
    print("Applying CEGAR penalties and re-ranking …")
    refined = refine(candidates, rejection_index, sat_df)

    # ── Console summary ───────────────────────────────────────────────────────
    penalized = (refined["penalty"] > 0).sum()
    changed   = (refined["rank_change"] != 0).sum()
    rank1_changed = (
        refined[refined["cegar_rank"] == 1]["rank_change"].abs() > 0
    ).sum()
    print(f"\nResults:")
    print(f"  Total candidate rows : {len(refined)}")
    print(f"  Rows with penalty > 0: {penalized}")
    print(f"  Rows with rank change: {changed}")
    print(f"  Nodes where rank-1 changed: {rank1_changed}")

    # ── Summary + report ──────────────────────────────────────────────────────
    summary_rows = compute_summary(refined)
    md_text = build_markdown(
        summary_rows=summary_rows,
        refined_df=refined,
        candidates_available=True,
        sat_available=(sat_df is not None),
        n_rejected=n_rejected,
    )

    # ── Write outputs ─────────────────────────────────────────────────────────
    _write_csv(OUTPUT_CSV, refined, OUTPUT_FIELDS)
    with open(OUTPUT_MD, "w", encoding="utf-8") as fh:
        fh.write(md_text)

    print(f"\nSaved:")
    print(f"  {OUTPUT_CSV}  ({len(refined)} rows)")
    print(f"  {OUTPUT_MD}")


if __name__ == "__main__":
    main()
