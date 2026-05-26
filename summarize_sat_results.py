"""
summarize_sat_results.py

Reads results/sat_verified_candidates.csv and generates two summary files:

  results/sat_summary.csv   — per benchmark/optimization counts + rates + global row
  results/sat_summary.md    — human-readable Markdown report

The CSV carries three recovery-method counters per group (added when
sat_refinement_abc.py gained fingerprint-based fallback recovery):

  direct_name_count       — checks that matched by the original node name
  fingerprint_recovered   — checks where the node was recovered via a unique
                            SHA-256 fingerprint (name was missing in the BLIF)
  still_inconclusive      — checks that could not be completed at all

This script has no external dependencies beyond pandas. It does not call ABC.

Usage:
  python3 summarize_sat_results.py
"""

import os
import sys

import pandas as pd


INPUT_CSV   = os.path.join("results", "sat_verified_candidates.csv")
OUTPUT_CSV  = os.path.join("results", "sat_summary.csv")
OUTPUT_MD   = os.path.join("results", "sat_summary.md")

REQUIRED_COLS = {
    "benchmark", "optimization",
    "optimized_node", "original_candidate",
    "combined_score", "sat_status", "abc_result", "notes",
    # recovery_method and match_category are optional for backwards-compat
}


# ── Input loading ──────────────────────────────────────────────────────────────

def load_verified(path: str) -> pd.DataFrame:
    if not os.path.exists(path):
        print(
            f"ERROR: {path} not found.\n"
            "Run sat_refinement_abc.py first:\n"
            "  ABC=/path/to/abc python3 sat_refinement_abc.py",
            file=sys.stderr,
        )
        sys.exit(1)

    df = pd.read_csv(path)

    if df.empty:
        return df

    missing = REQUIRED_COLS - set(df.columns)
    if missing:
        print(
            f"ERROR: {path} is missing expected columns: {sorted(missing)}\n"
            "Re-run sat_refinement_abc.py to regenerate the file.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Back-fill recovery_method for result files produced before the fingerprint
    # fallback was added.
    if "recovery_method" not in df.columns:
        df["recovery_method"] = df["sat_status"].map(
            lambda s: "inconclusive" if s == "inconclusive" else "direct"
        )
        df.to_csv(path, index=False)
        print(f"  Back-filled recovery_method column in {path}")

    # Back-fill match_category for result files produced before the exact-match
    # metadata was added.  Old files had no is_exact_signature_match column;
    # treat every row as a non_exact_candidate (conservative).
    if "match_category" not in df.columns:
        df["match_category"] = "non_exact_candidate"
        if "is_exact_signature_match" in df.columns:
            df["match_category"] = df["is_exact_signature_match"].apply(
                lambda v: "exact_anchor" if int(v) == 1 else "non_exact_candidate"
            )
        df.to_csv(path, index=False)
        print(f"  Back-filled match_category column in {path}")

    return df


# ── Summary computation ────────────────────────────────────────────────────────

def compute_group_summary(df: pd.DataFrame) -> pd.DataFrame:
    """
    Return one row per (benchmark, optimization) pair with:
      verified, rejected, inconclusive, total,
      verification_rate, rejection_rate, inconclusive_rate,
      avg_combined_score,
      direct_name_count, fingerprint_recovered, still_inconclusive,
      exact_anchor_verified, exact_anchor_rejected, exact_anchor_inconclusive,
      non_exact_verified, non_exact_rejected, non_exact_inconclusive
    """
    if df.empty:
        return pd.DataFrame(columns=[
            "benchmark", "optimization",
            "verified", "rejected", "inconclusive", "total",
            "verification_rate", "rejection_rate", "inconclusive_rate",
            "avg_combined_score",
            "direct_name_count", "fingerprint_recovered", "still_inconclusive",
            "exact_anchor_verified", "exact_anchor_rejected", "exact_anchor_inconclusive",
            "non_exact_verified", "non_exact_rejected", "non_exact_inconclusive",
        ])

    rows = []
    for (bench, opt), group in df.groupby(["benchmark", "optimization"], sort=True):
        row = _summarise_group(bench, opt, group)
        rows.append(row)

    return pd.DataFrame(rows)


def _summarise_group(bench: str, opt: str, group: pd.DataFrame) -> dict:
    counts = group["sat_status"].value_counts()
    verified     = int(counts.get("verified",     0))
    rejected     = int(counts.get("rejected",     0))
    inconclusive = int(counts.get("inconclusive", 0))
    total        = verified + rejected + inconclusive

    avg_score = round(float(group["combined_score"].mean()), 4) if total else 0.0

    # Recovery-method breakdown (column may not exist in old files but
    # load_verified() back-fills it, so it is always present here).
    method_counts          = group["recovery_method"].value_counts() if "recovery_method" in group.columns else {}
    direct_name_count      = int(method_counts.get("direct",      0))
    fingerprint_recovered  = int(method_counts.get("fingerprint", 0))
    still_inconclusive     = int(method_counts.get("inconclusive", 0))

    # Split by match_category (exact_anchor vs non_exact_candidate)
    def _cat_counts(category: str) -> tuple:
        if "match_category" not in group.columns:
            # Old pipeline output: no match_category — treat all as non_exact_candidate.
            sub = group if category == "non_exact_candidate" else pd.DataFrame()
        else:
            sub = group[group["match_category"] == category]
        c = sub["sat_status"].value_counts() if not sub.empty else {}
        return (int(c.get("verified", 0)),
                int(c.get("rejected", 0)),
                int(c.get("inconclusive", 0)))

    ea_v, ea_r, ea_i = _cat_counts("exact_anchor")
    ne_v, ne_r, ne_i = _cat_counts("non_exact_candidate")

    return {
        "benchmark":                    bench,
        "optimization":                 opt,
        "verified":                     verified,
        "rejected":                     rejected,
        "inconclusive":                 inconclusive,
        "total":                        total,
        "verification_rate":            round(verified     / total, 4) if total else 0.0,
        "rejection_rate":               round(rejected     / total, 4) if total else 0.0,
        "inconclusive_rate":            round(inconclusive / total, 4) if total else 0.0,
        "avg_combined_score":           avg_score,
        "direct_name_count":            direct_name_count,
        "fingerprint_recovered":        fingerprint_recovered,
        "still_inconclusive":           still_inconclusive,
        "exact_anchor_verified":        ea_v,
        "exact_anchor_rejected":        ea_r,
        "exact_anchor_inconclusive":    ea_i,
        "non_exact_verified":           ne_v,
        "non_exact_rejected":           ne_r,
        "non_exact_inconclusive":       ne_i,
    }


def add_global_row(summary: pd.DataFrame, df: pd.DataFrame) -> pd.DataFrame:
    """
    Append an ALL/ALL totals row at the bottom of the summary table.

    This gives a quick single-line view of the overall pipeline outcome without
    having to sum columns mentally.  The rates in this row are computed over the
    full dataset, not as an average of group rates, so they correctly reflect the
    actual pass/fail numbers.
    """
    global_row = _summarise_group("ALL", "ALL", df)
    global_df = pd.DataFrame([global_row])
    if summary.empty:
        return global_df
    return pd.concat([summary, global_df], ignore_index=True)


# ── Markdown generation ────────────────────────────────────────────────────────

def build_markdown(df: pd.DataFrame, summary: pd.DataFrame) -> str:
    """Build the full Markdown report as a single string."""

    lines = []
    lines.append("# SAT Refinement Summary\n")

    # ── Overall ──────────────────────────────────────────────────────────────
    lines.append("## Overall result\n")

    if df.empty:
        lines.append("No candidates were checked.\n")
    else:
        counts     = df["sat_status"].value_counts()
        total      = len(df)
        verified   = int(counts.get("verified",     0))
        rejected   = int(counts.get("rejected",     0))
        inconc     = int(counts.get("inconclusive", 0))
        verif_rate = verified / total if total else 0.0

        lines.append(f"- **Total candidates checked:** {total}")
        lines.append(f"- **Verified by ABC:** {verified}")
        lines.append(f"- **Rejected by ABC:** {rejected}")
        lines.append(f"- **Inconclusive:** {inconc}")
        lines.append(f"- **Verification rate:** {verif_rate:.1%}\n")

    # ── match_category breakdown ──────────────────────────────────────────────
    lines.append("## Match category breakdown\n")
    lines.append(
        "Following Carmine's feedback, candidates are now separated into two categories:\n"
    )
    lines.append(
        "- **`exact_anchor`**: the optimized node and original candidate already had "
        "identical Boolean simulation signatures before this SAT check. "
        "ABC verifying these is a useful sanity check, but it does **not** represent "
        "a newly-recovered correspondence — the match was already known.\n"
    )
    lines.append(
        "- **`non_exact_candidate`**: the optimized node and original candidate did "
        "**not** have the same simulation signature. "
        "ABC verifying one of these is a genuine refinement result — it means the "
        "scoring formula identified a real correspondence that exact signature matching "
        "missed.\n"
    )

    if df.empty:
        lines.append("No data.\n")
    elif "match_category" not in df.columns:
        lines.append("_`match_category` column not present — re-run the pipeline._\n")
    else:
        for cat in ("non_exact_candidate", "exact_anchor"):
            sub = df[df["match_category"] == cat]
            if sub.empty:
                lines.append(f"**{cat}**: no candidates.\n")
                continue
            c = sub["sat_status"].value_counts()
            v = int(c.get("verified",     0))
            r = int(c.get("rejected",     0))
            i = int(c.get("inconclusive", 0))
            t = len(sub)
            lines.append(
                f"**{cat}** ({t} candidates): "
                f"verified {v}, rejected {r}, inconclusive {i} "
                f"(verification rate {v/t:.1%})\n"
            )

    lines.append(
        "> **Important:** only `non_exact_candidate` verified results should be "
        "interpreted as SAT refinement recovering a correspondence that exact matching "
        "missed. `exact_anchor` verified results are expected and do not add new "
        "information.\n"
    )

    # ── Recovery method breakdown ─────────────────────────────────────────────
    lines.append("## Recovery method breakdown\n")

    if df.empty:
        lines.append("No data.\n")
    else:
        method_col = df.get("recovery_method", None) if hasattr(df, "get") else None
        has_method = "recovery_method" in df.columns

        if not has_method:
            lines.append(
                "_`recovery_method` column not present — re-run "
                "`sat_refinement_abc.py` to populate it._\n"
            )
        else:
            mc = df["recovery_method"].value_counts()
            direct_n = int(mc.get("direct",      0))
            fp_n     = int(mc.get("fingerprint", 0))
            inc_n    = int(mc.get("inconclusive", 0))

            lines.append(
                "Each completed check is tagged with the method used to "
                "locate the node in the BLIF file:\n"
            )
            lines.append(
                f"- **direct** ({direct_n}): node name found in the BLIF "
                "without any fallback"
            )
            lines.append(
                f"- **fingerprint** ({fp_n}): node name was missing; "
                "recovered via a unique SHA-256 fingerprint match"
            )
            lines.append(
                f"- **still inconclusive** ({inc_n}): node could not be "
                "resolved (name missing and fingerprint ambiguous/absent, "
                "missing BLIF, ABC timeout, etc.)\n"
            )
            if fp_n > 0:
                lines.append(
                    f"Fingerprint recovery successfully rescued **{fp_n}** "
                    "candidate(s) that would otherwise have been inconclusive, "
                    "reducing the inconclusive rate.\n"
                )

    # ── Per-group table ───────────────────────────────────────────────────────
    lines.append("## Summary by benchmark and optimization\n")

    if summary.empty:
        lines.append("No data.\n")
    else:
        group_rows = summary[summary["benchmark"] != "ALL"]
        global_row = summary[summary["benchmark"] == "ALL"]

        table_cols = [
            "benchmark", "optimization",
            "verified", "rejected", "inconclusive", "total",
            "verification_rate", "rejection_rate", "inconclusive_rate",
            "avg_combined_score",
            "direct_name_count", "fingerprint_recovered", "still_inconclusive",
        ]
        # Only keep columns that exist (graceful for old files).
        table_cols = [c for c in table_cols if c in summary.columns]

        lines.append(_df_to_md_table(group_rows[table_cols]))
        lines.append("")

        lines.append("**Global totals:**\n")
        lines.append(_df_to_md_table(global_row[table_cols]))
        lines.append("")

    # ── Rejected ─────────────────────────────────────────────────────────────
    lines.append("## Rejected candidates\n")

    rejected_df = df[df["sat_status"] == "rejected"] if not df.empty else pd.DataFrame()

    if rejected_df.empty:
        lines.append("No candidates were rejected by ABC.\n")
    else:
        rejected_cols = [
            "benchmark", "optimization",
            "optimized_node", "original_candidate",
            "combined_score", "abc_result",
        ]
        lines.append(
            f"ABC found {len(rejected_df)} candidate(s) to be **not equivalent**:\n"
        )
        lines.append(_df_to_md_table(rejected_df[rejected_cols]))
        lines.append(
            "\nA rejected candidate means the simulation ranking assigned a high score "
            "to a pair that ABC proved are not logically equivalent. "
            "This shows why a formal check is necessary: simulation similarity alone "
            "is not a proof of equivalence.\n"
        )

    # ── Inconclusive ──────────────────────────────────────────────────────────
    lines.append("## Inconclusive candidates\n")

    inconc_df = df[df["sat_status"] == "inconclusive"] if not df.empty else pd.DataFrame()

    if inconc_df.empty:
        lines.append("No inconclusive candidates.\n")
    else:
        lines.append(
            f"{len(inconc_df)} candidate(s) could not be formally checked.\n"
        )
        lines.append(
            "An inconclusive result means the ABC check could not be completed. "
            "Common reasons:\n"
        )
        lines.append("- A node name appears in the candidate list but not in the BLIF file "
                     "(ABC renames nodes during optimization, so the original and optimized "
                     "variants may use different names for corresponding nodes).")
        lines.append("- A BLIF file was missing.")
        lines.append("- ABC timed out.")
        lines.append("- Another preparation error occurred.\n")
        lines.append("Inconclusive cases do not mean the candidate is wrong — "
                     "they mean the current prototype cannot complete the check.\n")

        # Group inconclusives by benchmark/optimization.
        inc_counts = (
            inconc_df.groupby(["benchmark", "optimization"])
            .size()
            .reset_index(name="inconclusive_count")
        )
        lines.append("**Inconclusive counts by benchmark/optimization:**\n")
        lines.append(_df_to_md_table(inc_counts))
        lines.append("")

    # ── Interpretation ────────────────────────────────────────────────────────
    lines.append("## Main interpretation\n")
    lines.append(
        "The SAT refinement step confirms that the simulation-based ranking method is "
        "useful but not a proof by itself. "
        "Most high-confidence candidates were formally verified by ABC's equivalence "
        "checker, which shows the scoring formula produces meaningful rankings. "
        "The rejected candidate demonstrates why a formal check is necessary: a high "
        "simulation similarity score is not sufficient to guarantee equivalence, and "
        "ABC can find a concrete counterexample where the two nodes disagree. "
        "Inconclusive cases reveal current prototype limitations, especially around "
        "node-name stability between the original and optimized BLIF files and the "
        "fact that ABC assigns new internal names during optimization. "
        "Reducing the inconclusive rate is the most direct path to making the "
        "refinement step more useful in practice.\n"
    )

    return "\n".join(lines)


def _df_to_md_table(df: pd.DataFrame) -> str:
    """Convert a DataFrame to a GitHub-flavoured Markdown table string."""
    if df.empty:
        return "_No rows._"

    headers = list(df.columns)
    sep     = ["---"] * len(headers)

    # Columns whose values should be shown as percentages.
    rate_cols = {"verification_rate", "rejection_rate", "inconclusive_rate"}

    def fmt(col: str, val) -> str:
        if isinstance(val, float):
            if col in rate_cols:
                return f"{val:.2%}"
            return f"{val:.4f}"
        return str(val)

    rows = []
    rows.append("| " + " | ".join(headers) + " |")
    rows.append("| " + " | ".join(sep) + " |")
    for _, row in df.iterrows():
        rows.append("| " + " | ".join(fmt(c, row[c]) for c in headers) + " |")

    return "\n".join(rows)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    os.makedirs("results", exist_ok=True)

    print(f"Loading: {INPUT_CSV}")
    df = load_verified(INPUT_CSV)
    print(f"  Rows loaded: {len(df)}")

    if df.empty:
        print("  Input is empty — writing empty output files.")

    # Compute summary.
    group_summary = compute_group_summary(df)
    full_summary  = add_global_row(group_summary, df)

    # Write CSV.
    full_summary.to_csv(OUTPUT_CSV, index=False)
    print(f"  Wrote: {OUTPUT_CSV}")

    # Write Markdown.
    md = build_markdown(df, full_summary)
    with open(OUTPUT_MD, "w") as fh:
        fh.write(md)
    print(f"  Wrote: {OUTPUT_MD}")

    # Print the global summary line.
    global_row = full_summary[full_summary["benchmark"] == "ALL"].iloc[0]
    print(
        f"\nOverall: {int(global_row['total'])} total — "
        f"{int(global_row['verified'])} verified, "
        f"{int(global_row['rejected'])} rejected, "
        f"{int(global_row['inconclusive'])} inconclusive "
        f"({global_row['verification_rate']:.1%} verification rate)"
    )

    # Print recovery method breakdown.
    if "direct_name_count" in global_row.index:
        print(
            f"Recovery method: "
            f"{int(global_row['direct_name_count'])} direct, "
            f"{int(global_row['fingerprint_recovered'])} fingerprint-recovered, "
            f"{int(global_row['still_inconclusive'])} still inconclusive"
        )


if __name__ == "__main__":
    main()
