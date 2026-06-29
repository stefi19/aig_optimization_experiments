#!/usr/bin/env python3
"""Prototype approximate-distance analysis for internal-node candidates."""

from __future__ import annotations

import argparse
import hashlib
import random
import sys
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from analyze_blif_matches import eval_cover, parse_blif  # noqa: E402


RESULTS = ROOT / "results"
PLOTS = RESULTS / "plots"
plt = None

SAT_CANDIDATES = RESULTS / "sat_verified_candidates.csv"
TOP_CANDIDATES = RESULTS / "top_candidates.csv"

EXACT_OUT = RESULTS / "approximate_distance_exact.csv"
SAMPLED_OUT = RESULTS / "approximate_distance_sampled.csv"
SKIPPED_OUT = RESULTS / "approximate_distance_skipped.csv"
SUMMARY_OUT = RESULTS / "approximate_distance_summary.csv"
SUMMARY_MD = RESULTS / "approximate_distance_summary.md"


DEFAULT_MAX_EXACT_SUPPORT = 12
DEFAULT_SAMPLE_PATTERNS = 4096
DEFAULT_REJECTED_SAMPLE_LIMIT = 2000


@dataclass(frozen=True)
class NodeEval:
    value: int
    support: frozenset[str]
    pattern_count: int
    mode: str


def hamming_distance_fraction(left: int, right: int, pattern_count: int) -> float:
    """Return the fraction of bit positions where two packed signatures differ."""

    if pattern_count <= 0:
        raise ValueError("pattern_count must be positive")
    return (left ^ right).bit_count() / pattern_count


def choose_distance_mode(
    support_size: int, max_exact_support: int, sampled_fallback: bool
) -> str:
    """Choose exact, sampled, or skipped mode for a support size."""

    if support_size <= max_exact_support:
        return "exact"
    if sampled_fallback:
        return "sampled"
    return "skipped"


def exact_pattern_values(all_inputs: list[str], active_support: set[str]) -> tuple[dict[str, int], int, int]:
    """Build exhaustive patterns for active_support; non-support inputs stay zero."""

    ordered_support = sorted(active_support)
    pattern_count = 1 << len(ordered_support)
    values = {name: 0 for name in all_inputs}
    for input_index, name in enumerate(ordered_support):
        bits = 0
        for assignment in range(pattern_count):
            if (assignment >> input_index) & 1:
                bits |= 1 << assignment
        values[name] = bits
    return values, (1 << pattern_count) - 1, pattern_count


def sampled_pattern_values(
    all_inputs: list[str],
    active_support: set[str],
    pattern_count: int,
    seed_key: str,
) -> tuple[dict[str, int], int, int]:
    """Build deterministic random patterns for active_support; non-support inputs stay zero."""

    seed = int(hashlib.sha256(seed_key.encode("utf-8")).hexdigest()[:16], 16)
    rng = random.Random(seed)
    values = {name: 0 for name in all_inputs}
    for name in sorted(active_support):
        bits = 0
        for pattern_index in range(pattern_count):
            if rng.getrandbits(1):
                bits |= 1 << pattern_index
        values[name] = bits
    return values, (1 << pattern_count) - 1, pattern_count


def evaluate_network_with_values(path: Path, values: dict[str, int], mask: int) -> dict[str, NodeEval]:
    """Evaluate a BLIF with prebuilt primary-input bit vectors."""

    net = parse_blif(path)
    missing_inputs = [name for name in net.inputs if name not in values]
    if missing_inputs:
        raise ValueError(f"{path}: missing input pattern values for {missing_inputs}")

    work_values = dict(values)
    support: dict[str, frozenset[str]] = {
        name: frozenset([name]) for name in net.inputs
    }

    for node in net.nodes:
        missing_fanins = [fanin for fanin in node.inputs if fanin not in work_values]
        if missing_fanins:
            raise ValueError(f"{path}: missing fanin values for {missing_fanins}")
        work_values[node.output] = eval_cover(node, work_values, mask)
        node_support: set[str] = set()
        for fanin in node.inputs:
            node_support |= set(support.get(fanin, frozenset()))
        support[node.output] = frozenset(node_support)

    pattern_count = mask.bit_length()
    return {
        name: NodeEval(
            value=value,
            support=support.get(name, frozenset()),
            pattern_count=pattern_count,
            mode="custom",
        )
        for name, value in work_values.items()
    }


def structural_supports(path: Path) -> dict[str, frozenset[str]]:
    """Compute structural support sets without building large truth tables."""

    net = parse_blif(path)
    support: dict[str, frozenset[str]] = {
        name: frozenset([name]) for name in net.inputs
    }
    for node in net.nodes:
        node_support: set[str] = set()
        for fanin in node.inputs:
            node_support |= set(support.get(fanin, frozenset()))
        support[node.output] = frozenset(node_support)
    return support


def variant_path(benchmark: str, optimization: str) -> Path:
    return ROOT / "variants" / f"{benchmark}_{optimization}.blif"


def original_variant_path(benchmark: str) -> Path:
    return ROOT / "variants" / f"{benchmark}_original.blif"


def load_candidate_rows(limit_rejected: int) -> pd.DataFrame:
    sat = pd.read_csv(SAT_CANDIDATES)
    feature_cols = [
        "benchmark",
        "optimization",
        "optimized_node",
        "rank",
        "original_candidate",
        "simulation_similarity",
        "depth_similarity",
        "optimized_level",
        "original_level",
        "optimized_support_size",
        "original_support_size",
    ]
    top = pd.read_csv(TOP_CANDIDATES, usecols=feature_cols)
    keys = ["benchmark", "optimization", "optimized_node", "rank", "original_candidate"]
    df = sat.merge(top, on=keys, how="left", validate="one_to_one")
    df = df[
        df["benchmark"].str.startswith("external_iscas85_")
        & (df["match_category"] == "non_exact_candidate")
        & (df["rank"] == 1)
        & (df["sat_status"].isin(["verified", "rejected"]))
    ].copy()

    verified = df[df["sat_status"] == "verified"]
    rejected = df[df["sat_status"] == "rejected"].sort_values(
        ["combined_score", "support_overlap", "simulation_similarity"],
        ascending=False,
    )
    if limit_rejected > 0:
        rejected = rejected.head(limit_rejected)
    return pd.concat([verified, rejected], ignore_index=True)


def evaluate_candidate_distance(
    row: pd.Series,
    max_exact_support: int,
    sampled_fallback: bool,
    sample_patterns: int,
    support_cache: dict[Path, dict[str, frozenset[str]]],
) -> dict:
    benchmark = row["benchmark"]
    optimization = row["optimization"]
    original_path = original_variant_path(benchmark)
    optimized_path = variant_path(benchmark, optimization)
    original_node = row["original_candidate"]
    optimized_node = row["optimized_node"]

    if not original_path.exists() or not optimized_path.exists():
        return make_result_row(row, "skipped", "missing_variant", None, None, None)

    original_supports = support_cache.setdefault(original_path, structural_supports(original_path))
    optimized_supports = support_cache.setdefault(optimized_path, structural_supports(optimized_path))

    if original_node not in original_supports or optimized_node not in optimized_supports:
        return make_result_row(row, "skipped", "missing_node", None, None, None)

    union_support = set(original_supports[original_node]) | set(optimized_supports[optimized_node])
    mode = choose_distance_mode(len(union_support), max_exact_support, sampled_fallback)
    if mode == "skipped":
        return make_result_row(row, "skipped", "support_too_large", len(union_support), None, None)

    net_inputs = sorted(set(parse_blif(original_path).inputs) | set(parse_blif(optimized_path).inputs))
    if mode == "exact":
        values, mask, pattern_count = exact_pattern_values(net_inputs, union_support)
    else:
        seed_key = f"{benchmark}|{optimization}|{original_node}|{optimized_node}"
        values, mask, pattern_count = sampled_pattern_values(
            net_inputs, union_support, sample_patterns, seed_key
        )

    original_values = evaluate_network_with_values(original_path, values, mask)
    optimized_values = evaluate_network_with_values(optimized_path, values, mask)
    distance = hamming_distance_fraction(
        original_values[original_node].value,
        optimized_values[optimized_node].value,
        pattern_count,
    )
    return make_result_row(
        row,
        mode,
        "ok",
        len(union_support),
        distance,
        pattern_count,
    )


def make_result_row(
    row: pd.Series,
    mode: str,
    reason: str,
    union_support_size: int | None,
    distance: float | None,
    pattern_count: int | None,
) -> dict:
    similarity = None if distance is None else 1.0 - distance
    return {
        "benchmark": row["benchmark"],
        "circuit": str(row["benchmark"]).replace("external_iscas85_", ""),
        "optimization": row["optimization"],
        "optimized_node": row["optimized_node"],
        "original_candidate": row["original_candidate"],
        "rank": int(row["rank"]),
        "sat_status": row["sat_status"],
        "combined_score": row["combined_score"],
        "support_overlap": row["support_overlap"],
        "simulation_similarity": row.get("simulation_similarity"),
        "distance_mode": mode,
        "skip_reason": reason,
        "union_support_size": union_support_size,
        "pattern_count": pattern_count,
        "distance": distance,
        "similarity": similarity,
        "is_formal_distance": mode == "exact",
    }


def summarize_distances(all_rows: pd.DataFrame) -> pd.DataFrame:
    rows = []
    usable = all_rows[all_rows["distance"].notna()].copy()
    for (mode, status), group in usable.groupby(["distance_mode", "sat_status"]):
        rows.append(
            {
                "distance_mode": mode,
                "sat_status": status,
                "count": len(group),
                "mean_distance": group["distance"].mean(),
                "median_distance": group["distance"].median(),
                "min_distance": group["distance"].min(),
                "max_distance": group["distance"].max(),
                "pct_distance_le_1pct": (group["distance"] <= 0.01).mean(),
                "pct_distance_le_5pct": (group["distance"] <= 0.05).mean(),
                "pct_distance_le_10pct": (group["distance"] <= 0.10).mean(),
            }
        )
    columns = [
        "distance_mode",
        "sat_status",
        "count",
        "mean_distance",
        "median_distance",
        "min_distance",
        "max_distance",
        "pct_distance_le_1pct",
        "pct_distance_le_5pct",
        "pct_distance_le_10pct",
    ]
    if not rows:
        return pd.DataFrame(columns=columns)
    return pd.DataFrame(rows, columns=columns).sort_values(["distance_mode", "sat_status"])


def write_markdown_summary(
    summary: pd.DataFrame,
    exact: pd.DataFrame,
    sampled: pd.DataFrame,
    skipped: pd.DataFrame,
) -> None:
    lines = [
        "# Approximate Node Distance Summary",
        "",
        "This prototype measures truth-table distance for ISCAS-85 rank-1 non-exact candidates.",
        "Rows in `exact` mode are formal exhaustive distances over the union support.",
        "Rows in `sampled` mode are estimates and must not be described as formal.",
        "",
        f"- Exact rows: {len(exact):,}",
        f"- Sampled rows: {len(sampled):,}",
        f"- Skipped rows: {len(skipped):,}",
        "",
        "## Distance Summary",
        "",
    ]
    if summary.empty:
        lines.append("No distances were computed.")
    else:
        lines.append(summary.to_markdown(index=False, floatfmt=".4f"))
    lines.extend(
        [
            "",
            "## Close Rejected Candidates",
            "",
        ]
    )
    close = pd.concat([exact, sampled], ignore_index=True)
    close = close[
        (close["sat_status"] == "rejected")
        & (close["distance"].notna())
        & (close["distance"] <= 0.10)
    ].sort_values(["distance", "combined_score"]).head(20)
    if close.empty:
        lines.append("No rejected candidates had distance <= 10% in the analyzed pool.")
    else:
        cols = [
            "distance_mode",
            "benchmark",
            "optimization",
            "original_candidate",
            "optimized_node",
            "combined_score",
            "support_overlap",
            "distance",
            "similarity",
        ]
        lines.append(close[cols].to_markdown(index=False, floatfmt=".4f"))
    lines.append("")
    SUMMARY_MD.write_text("\n".join(lines), encoding="utf-8")


def plot_outputs(all_rows: pd.DataFrame, summary: pd.DataFrame) -> None:
    global plt
    if plt is None:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as _plt
        plt = _plt
    PLOTS.mkdir(parents=True, exist_ok=True)
    usable = all_rows[all_rows["distance"].notna()].copy()
    if usable.empty:
        return

    fig, ax = plt.subplots(figsize=(8, 4.8))
    for status, color in [("verified", "#2f7d32"), ("rejected", "#b54848")]:
        subset = usable[usable["sat_status"] == status]
        if subset.empty:
            continue
        ax.hist(subset["distance"], bins=30, alpha=0.55, label=status, color=color)
    ax.set_xlabel("truth-table distance (exact or sampled, see CSV)")
    ax.set_ylabel("candidate count")
    ax.set_title("Approximate Distance Distribution")
    ax.legend()
    save_plot(PLOTS / "approx_distance_distribution.png")

    fig, ax = plt.subplots(figsize=(7, 4.8))
    sim_data = [
        usable[usable["sat_status"] == status]["similarity"]
        for status in ["verified", "rejected"]
    ]
    ax.boxplot(sim_data, tick_labels=["verified", "rejected"], showmeans=True)
    ax.set_ylabel("approximate similarity = 1 - distance")
    ax.set_title("Approximate Similarity by SAT Status")
    save_plot(PLOTS / "approx_similarity_by_sat_status.png")

    by_circuit = (
        usable.groupby(["circuit", "sat_status"])["distance"]
        .median()
        .unstack("sat_status")
        .sort_index()
    )
    ax = by_circuit.plot(kind="bar", figsize=(9, 4.8), color=["#b54848", "#2f7d32"])
    ax.set_ylabel("median distance")
    ax.set_xlabel("ISCAS-85 circuit")
    ax.set_title("Approximate Distance by Circuit")
    ax.tick_params(axis="x", rotation=35)
    save_plot(PLOTS / "approx_distance_by_circuit.png")

    by_opt = (
        usable.groupby(["optimization", "sat_status"])["distance"]
        .median()
        .unstack("sat_status")
        .sort_index()
    )
    ax = by_opt.plot(kind="bar", figsize=(9, 4.8), color=["#b54848", "#2f7d32"])
    ax.set_ylabel("median distance")
    ax.set_xlabel("optimization")
    ax.set_title("Approximate Distance by Optimization")
    ax.tick_params(axis="x", rotation=40)
    save_plot(PLOTS / "approx_distance_by_optimization.png")


def save_plot(path: Path) -> None:
    plt.tight_layout()
    plt.savefig(path, dpi=180)
    plt.close()


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-exact-support", type=int, default=DEFAULT_MAX_EXACT_SUPPORT)
    parser.add_argument("--sample-patterns", type=int, default=DEFAULT_SAMPLE_PATTERNS)
    parser.add_argument(
        "--limit-rejected",
        type=int,
        default=DEFAULT_REJECTED_SAMPLE_LIMIT,
        help="Analyze all verified rows plus this many highest-score rejected rows; 0 means all rejected.",
    )
    parser.add_argument(
        "--no-sampled-fallback",
        action="store_true",
        help="Skip rows above --max-exact-support instead of writing sampled estimates.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    candidates = load_candidate_rows(limit_rejected=args.limit_rejected)
    support_cache: dict[Path, dict[str, frozenset[str]]] = {}
    rows = [
        evaluate_candidate_distance(
            row,
            max_exact_support=args.max_exact_support,
            sampled_fallback=not args.no_sampled_fallback,
            sample_patterns=args.sample_patterns,
            support_cache=support_cache,
        )
        for _, row in candidates.iterrows()
    ]

    all_rows = pd.DataFrame(rows)
    exact = all_rows[all_rows["distance_mode"] == "exact"].copy()
    sampled = all_rows[all_rows["distance_mode"] == "sampled"].copy()
    skipped = all_rows[all_rows["distance_mode"] == "skipped"].copy()

    exact.to_csv(EXACT_OUT, index=False)
    sampled.to_csv(SAMPLED_OUT, index=False)
    skipped.to_csv(SKIPPED_OUT, index=False)
    summary = summarize_distances(all_rows)
    summary.to_csv(SUMMARY_OUT, index=False)
    write_markdown_summary(summary, exact, sampled, skipped)
    plot_outputs(all_rows, summary)

    print(f"Analyzed {len(all_rows):,} ISCAS candidate pairs")
    print(f"Exact rows: {len(exact):,}")
    print(f"Sampled rows: {len(sampled):,}")
    print(f"Skipped rows: {len(skipped):,}")
    print(f"Wrote {SUMMARY_OUT.relative_to(ROOT)} and {SUMMARY_MD.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
