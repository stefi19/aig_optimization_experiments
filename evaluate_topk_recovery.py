"""
evaluate_topk_recovery.py

Measures how well the simulation-based ranking recovers the "true" node
correspondences that ABC subsequently verified.

Input files (both optional — the script degrades gracefully when missing):
  results/top_candidates.csv       — full ranked candidate list (all K ranks)
  results/sat_verified_candidates.csv — ABC verdicts for high-confidence pairs

Output files:
  results/topk_recovery.csv  — per-(benchmark, optimization, K) metrics
  results/topk_recovery.md   — human-readable Markdown report

Metrics computed per (benchmark, optimization) group:
  verified_at_k   — number of optimized nodes whose rank-1…K set contains
                    at least one ABC-verified match
  total_nodes     — number of optimized nodes that had SAT candidates
  recovery_at_k   — verified_at_k / total_nodes  (the main headline metric)
  mrr             — Mean Reciprocal Rank: for each node, 1/rank of the first
                    verified candidate; averaged over all nodes with any
                    verified match
  avg_score_at_1  — mean combined_score of the rank-1 candidate per node

K values evaluated: 1, 2, 3, 5  (configurable via TOP_K_VALUES below)

Graceful degradation
--------------------
- If top_candidates.csv is missing the script prints a clear message and
  writes empty output files rather than crashing.
- If sat_verified_candidates.csv is missing, verified@K / MRR cannot be
  computed; those columns are filled with NaN and the report notes this.

Usage:
  python3 evaluate_topk_recovery.py
"""

import os
import sys

import pandas as pd

# ── Configuration ──────────────────────────────────────────────────────────────

CANDIDATES_CSV = os.path.join("results", "top_candidates.csv")
VERIFIED_CSV   = os.path.join("results", "sat_verified_candidates.csv")
OUTPUT_CSV     = os.path.join("results", "topk_recovery.csv")
OUTPUT_MD      = os.path.join("results", "topk_recovery.md")

TOP_K_VALUES   = [1, 2, 3, 5]


# ── Data loading ───────────────────────────────────────────────────────────────

def load_candidates(path: str) -> pd.DataFrame | None:
    """Return the top-candidates DataFrame, or None if the file is missing."""
    if not os.path.exists(path):
        return None
    df = pd.read_csv(path)
    required = {"benchmark", "optimization", "optimized_node",
                "original_candidate", "rank", "combined_score"}
    if not required.issubset(df.columns):
        print(
            f"WARNING: {path} is missing expected columns "
            f"({required - set(df.columns)}). "
            "Re-run analyze_blif_matches.py.",
            file=sys.stderr,
        )
        return None
    return df


def load_verified(path: str) -> pd.DataFrame | None:
    """Return the verified-candidates DataFrame, or None if the file is missing."""
    if not os.path.exists(path):
        return None
    df = pd.read_csv(path)
    required = {"benchmark", "optimization", "optimized_node",
                "original_candidate", "sat_status"}
    if not required.issubset(df.columns):
        print(
            f"WARNING: {path} is missing expected columns. "
            "Re-run sat_refinement_abc.py.",
            file=sys.stderr,
        )
        return None
    return df


# ── Core metrics ───────────────────────────────────────────────────────────────

def build_verified_set(verified_df: pd.DataFrame) -> set[tuple[str, str, str, str]]:
    """
    Return the set of (benchmark, optimization, optimized_node, original_candidate)
    tuples where sat_status == 'verified' AND match_category == 'non_exact_candidate'.

    Exact-anchor rows (where the candidate was already an exact signature match)
    are excluded by default.  ABC confirming an exact anchor is a sanity check,
    not a recovery of a missed correspondence.  Top-K recovery metrics should
    only count genuinely new discoveries.

    If the match_category column is absent (old result file), all verified rows
    are included with a warning.
    """
    mask = verified_df["sat_status"] == "verified"
    vdf = verified_df[mask].copy()

    if "match_category" in vdf.columns:
        n_anchors = int((vdf["match_category"] == "exact_anchor").sum())
        vdf = vdf[vdf["match_category"] == "non_exact_candidate"]
        if n_anchors:
            print(
                f"  Top-K: excluded {n_anchors} exact_anchor verified rows from "
                "recovery metrics (they are already-known matches, not new discoveries)."
            )
    else:
        print(
            "  WARNING: match_category column missing from SAT results. "
            "All verified rows included (re-run pipeline for accurate results)."
        )

    rows = vdf[["benchmark", "optimization", "optimized_node", "original_candidate"]]
    return set(map(tuple, rows.values))


def compute_recovery_for_group(
    group: pd.DataFrame,
    verified_set: set | None,
    k: int,
) -> dict:
    """
    Compute verified@K and reciprocal rank for a single (benchmark, opt) group.

    Parameters
    ----------
    group
        Rows from top_candidates.csv for one (benchmark, optimization) pair.
        Must have columns: optimized_node, original_candidate, rank, combined_score.
    verified_set
        Set of (benchmark, opt, opt_node, orig_candidate) tuples that ABC verified.
        None if SAT results are unavailable.
    k
        The cutoff rank to evaluate at.

    Returns a dict with keys:
        verified_at_k, total_nodes, recovery_at_k, mrr, avg_score_at_1
    """
    nodes = group["optimized_node"].unique()
    total_nodes = len(nodes)

    # avg combined_score of rank-1 candidates
    rank1 = group[group["rank"] == 1]
    avg_score_at_1 = float(rank1["combined_score"].mean()) if len(rank1) else float("nan")

    if verified_set is None:
        return {
            "verified_at_k": float("nan"),
            "total_nodes":   total_nodes,
            "recovery_at_k": float("nan"),
            "mrr":           float("nan"),
            "avg_score_at_1": avg_score_at_1,
        }

    bench = group["benchmark"].iloc[0]
    opt   = group["optimization"].iloc[0]

    verified_count = 0
    reciprocal_ranks: list[float] = []

    for node, node_group in group.groupby("optimized_node"):
        # Candidates at ranks 1..k
        top_k = node_group[node_group["rank"] <= k].sort_values("rank")

        has_verified_in_k = False
        best_rr = 0.0

        for _, row in top_k.iterrows():
            key = (bench, opt, node, row["original_candidate"])
            if key in verified_set:
                has_verified_in_k = True
                # MRR uses rank from top_candidates, not the truncated window
                rr = 1.0 / row["rank"]
                if rr > best_rr:
                    best_rr = rr

        if has_verified_in_k:
            verified_count += 1

        # MRR: include the node only when it has any verified candidate
        # (across ALL ranks, not just top-k — so we don't penalise for k being small)
        all_node_rows = node_group.sort_values("rank")
        for _, row in all_node_rows.iterrows():
            key = (bench, opt, node, row["original_candidate"])
            if key in verified_set:
                reciprocal_ranks.append(1.0 / row["rank"])
                break  # only the first/best verified rank contributes

    mrr = float(sum(reciprocal_ranks) / total_nodes) if total_nodes else float("nan")
    recovery = verified_count / total_nodes if total_nodes else float("nan")

    return {
        "verified_at_k":  verified_count,
        "total_nodes":    total_nodes,
        "recovery_at_k":  recovery,
        "mrr":            mrr,
        "avg_score_at_1": avg_score_at_1,
    }


def compute_topk_table(
    candidates: pd.DataFrame,
    verified_set: set | None,
    k_values: list[int],
) -> pd.DataFrame:
    """
    Return a DataFrame with one row per (benchmark, optimization, k).
    """
    rows = []
    for (bench, opt), group in candidates.groupby(
        ["benchmark", "optimization"], sort=True
    ):
        for k in k_values:
            metrics = compute_recovery_for_group(group, verified_set, k)
            rows.append({
                "benchmark":    bench,
                "optimization": opt,
                "k":            k,
                **metrics,
            })

    cols = [
        "benchmark", "optimization", "k",
        "verified_at_k", "total_nodes", "recovery_at_k",
        "mrr", "avg_score_at_1",
    ]
    if not rows:
        return pd.DataFrame(columns=cols)
    return pd.DataFrame(rows, columns=cols)


# ── Markdown report ────────────────────────────────────────────────────────────

def _fmt(val, is_rate: bool = False) -> str:
    if pd.isna(val):
        return "n/a"
    if isinstance(val, float):
        if is_rate:
            return f"{val:.1%}"
        return f"{val:.4f}"
    if isinstance(val, (int,)):
        return str(val)
    return str(val)


def _md_table(df: pd.DataFrame, rate_cols: set[str] | None = None) -> str:
    if df.empty:
        return "_No data._"
    rc = rate_cols or set()
    headers = list(df.columns)
    lines = ["| " + " | ".join(headers) + " |",
             "| " + " | ".join(["---"] * len(headers)) + " |"]
    for _, row in df.iterrows():
        cells = [_fmt(row[c], c in rc) for c in headers]
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def build_markdown(
    topk_df: pd.DataFrame,
    candidates_available: bool,
    verified_available: bool,
) -> str:
    lines: list[str] = []
    lines.append("# Top-K Recovery Evaluation\n")

    # ── Status ────────────────────────────────────────────────────────────────
    lines.append("## Data availability\n")
    lines.append(
        f"- `top_candidates.csv`: {'✅ loaded' if candidates_available else '❌ missing — run `analyze_blif_matches.py`'}"
    )
    lines.append(
        f"- `sat_verified_candidates.csv`: "
        f"{'✅ loaded' if verified_available else '❌ missing — run `sat_refinement_abc.py`'}\n"
    )
    if not candidates_available:
        lines.append(
            "> Cannot compute any metrics without `top_candidates.csv`.\n"
        )
        return "\n".join(lines)

    if not verified_available:
        lines.append(
            "> `recovery_at_k` and `mrr` require SAT results and are shown as **n/a**.\n"
            "> `avg_score_at_1` is computed from simulation scores alone.\n"
        )

    # ── Summary table at K=1 ─────────────────────────────────────────────────
    lines.append("## Recovery at K=1 (rank-1 candidate only)\n")
    k1 = topk_df[topk_df["k"] == 1].drop(columns=["k"])
    lines.append(_md_table(
        k1,
        rate_cols={"recovery_at_k"},
    ))
    lines.append("")

    # ── Full table ────────────────────────────────────────────────────────────
    lines.append("## Full results (all K values)\n")
    lines.append(_md_table(topk_df, rate_cols={"recovery_at_k"}))
    lines.append("")

    # ── Global summary ────────────────────────────────────────────────────────
    if not topk_df.empty and verified_available:
        lines.append("## Global summary\n")
        for k in sorted(topk_df["k"].unique()):
            kdf = topk_df[topk_df["k"] == k]
            total_nodes   = int(kdf["total_nodes"].sum())
            total_verified = kdf["verified_at_k"].dropna()
            total_v = int(total_verified.sum()) if len(total_verified) else 0
            rate = total_v / total_nodes if total_nodes else float("nan")
            lines.append(
                f"- **K={k}**: {total_v}/{total_nodes} nodes recovered "
                f"({_fmt(rate, is_rate=True)})"
            )
        lines.append("")

    # ── Interpretation ────────────────────────────────────────────────────────
    lines.append("## Interpretation\n")
    lines.append(
        "**Note on exact anchors:** The verified set used for these metrics "
        "excludes `exact_anchor` rows (candidates that were already confirmed as "
        "exact Boolean signature matches before the SAT step). "
        "Only `non_exact_candidate` verified rows are counted here, because those "
        "represent correspondences that SAT refinement genuinely recovered beyond "
        "what exact matching found. "
        "Re-run with the full SAT results to see anchor counts separately.\n"
    )
    lines.append(
        "**verified_at_k** is the number of optimized nodes for which the "
        "ABC-verified match appears within the top-K simulation-ranked candidates.\n"
    )
    lines.append(
        "**recovery_at_k** = verified_at_k / total_nodes. "
        "A value of 1.0 at K=1 means the rank-1 candidate was always the "
        "formally correct match — the simulation ranking was perfect.\n"
    )
    lines.append(
        "**MRR** (Mean Reciprocal Rank) measures how high the first verified "
        "candidate appears on average. MRR=1.0 means every verified match was "
        "rank-1; MRR=0.5 means verified matches appeared at rank 2 on average.\n"
    )
    lines.append(
        "**avg_score_at_1** is the mean combined_score of the top-ranked "
        "candidate per node. It is available even without SAT results and gives "
        "a proxy for how confidently the simulation step selected candidates.\n"
    )
    if not verified_available:
        lines.append(
            "> To compute recovery_at_k and MRR, first run the SAT pipeline:\n"
            "> ```\n"
            "> python3 sat_refinement_placeholder.py\n"
            "> ABC=/path/to/abc python3 sat_refinement_abc.py\n"
            "> ```\n"
        )

    return "\n".join(lines)


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    os.makedirs("results", exist_ok=True)

    # Load inputs (both optional).
    candidates = load_candidates(CANDIDATES_CSV)
    verified_df = load_verified(VERIFIED_CSV)

    candidates_available = candidates is not None
    verified_available   = verified_df is not None

    if not candidates_available:
        print(
            f"WARNING: {CANDIDATES_CSV} not found.\n"
            "  Run analyze_blif_matches.py first to generate it.\n"
            "  Writing empty output files."
        )
        topk_df = pd.DataFrame(columns=[
            "benchmark", "optimization", "k",
            "verified_at_k", "total_nodes", "recovery_at_k",
            "mrr", "avg_score_at_1",
        ])
    else:
        print(f"Loaded {len(candidates)} candidate rows from {CANDIDATES_CSV}")

        verified_set = None
        if verified_available:
            verified_set = build_verified_set(verified_df)
            print(
                f"Loaded {len(verified_df)} SAT rows from {VERIFIED_CSV} "
                f"({len(verified_set)} verified pairs)"
            )
        else:
            print(
                f"Note: {VERIFIED_CSV} not found — "
                "recovery_at_k and MRR will be n/a.\n"
                "  Run sat_refinement_abc.py to enable formal recovery metrics."
            )

        topk_df = compute_topk_table(candidates, verified_set, TOP_K_VALUES)

    # Write CSV.
    topk_df.to_csv(OUTPUT_CSV, index=False)
    print(f"\nWrote {OUTPUT_CSV}")

    # Write Markdown.
    md = build_markdown(topk_df, candidates_available, verified_available)
    with open(OUTPUT_MD, "w") as fh:
        fh.write(md)
    print(f"Wrote {OUTPUT_MD}")

    # Print inline summary.
    if candidates_available and not topk_df.empty:
        print("\nRecovery summary:")
        for k in TOP_K_VALUES:
            kdf = topk_df[topk_df["k"] == k]
            if kdf.empty:
                continue
            total_nodes = int(kdf["total_nodes"].sum())
            if verified_available:
                total_v = int(kdf["verified_at_k"].dropna().sum())
                rate    = total_v / total_nodes if total_nodes else float("nan")
                print(
                    f"  K={k}: {total_v}/{total_nodes} nodes recovered "
                    f"({rate:.1%})"
                )
            else:
                avg_s = kdf["avg_score_at_1"].mean()
                print(
                    f"  K={k}: {total_nodes} nodes, "
                    f"avg rank-1 score = {avg_s:.4f} (no SAT data)"
                )


if __name__ == "__main__":
    main()
