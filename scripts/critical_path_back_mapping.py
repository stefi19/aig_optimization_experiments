#!/usr/bin/env python3
"""Prototype critical-path back-mapping from optimized nodes to original nodes."""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from analyze_blif_matches import BlifNetwork, parse_blif  # noqa: E402


RESULTS = ROOT / "results"
PLOTS = RESULTS / "plots"

TOP_CANDIDATES = RESULTS / "top_candidates.csv"
SAT_CANDIDATES = RESULTS / "sat_verified_candidates.csv"
COMPLEMENT_FILES = [
    RESULTS / "sat_complement_rank1_nonexact.csv",
    RESULTS / "sat_complement_topk_nonexact.csv",
]
APPROX_FILES = [
    RESULTS / "approximate_distance_exact.csv",
    RESULTS / "approximate_distance_sampled.csv",
]

MAPPING_CSV = RESULTS / "critical_path_mapping.csv"
MAPPING_MD = RESULTS / "critical_path_mapping.md"

DEFAULT_CIRCUITS = ("c432", "c2670", "c6288")
DEFAULT_APPROX_THRESHOLD = 0.05
MAPPING_PRIORITY = {
    "exact": 0,
    "complemented": 1,
    "sat_verified_nonexact": 2,
    "approximate_near_match": 3,
    "unresolved": 4,
}


@dataclass(frozen=True)
class PathNode:
    node: str
    level: int
    path_index: int


@dataclass(frozen=True)
class MappingChoice:
    category: str
    original_node: str
    confidence: float | None = None
    distance: float | None = None
    combined_score: float | None = None
    support_overlap: float | None = None
    simulation_similarity: float | None = None
    rank: int | None = None
    distance_mode: str = ""
    is_formal_distance: bool | None = None
    explanation: str = ""


def compute_levels_and_predecessors(net: BlifNetwork) -> tuple[dict[str, int], dict[str, str | None]]:
    """Compute structural levels and one deepest predecessor for each BLIF node."""

    levels: dict[str, int] = {name: 0 for name in net.inputs}
    predecessor: dict[str, str | None] = {name: None for name in net.inputs}
    internal_outputs = {node.output for node in net.nodes}

    for node in net.nodes:
        best_fanin = None
        best_level = -1
        for fanin in node.inputs:
            fanin_level = levels.get(fanin, 0)
            if fanin_level > best_level:
                best_level = fanin_level
                best_fanin = fanin if fanin in internal_outputs else None
        levels[node.output] = max(0, best_level + 1)
        predecessor[node.output] = best_fanin

    return levels, predecessor


def extract_longest_internal_path(net: BlifNetwork) -> list[PathNode]:
    """
    Return one deepest structural path through internal nodes.

    This is only a timing proxy. It ignores gate/library delays and chooses the
    deepest fanin chain ending at the deepest primary output driver.
    """

    internal_outputs = {node.output for node in net.nodes}
    if not internal_outputs:
        return []

    levels, predecessor = compute_levels_and_predecessors(net)
    output_roots = [output for output in net.outputs if output in internal_outputs]
    roots = output_roots or list(internal_outputs)
    sink = max(roots, key=lambda name: (levels.get(name, 0), name))

    path: list[str] = []
    current: str | None = sink
    seen: set[str] = set()
    while current and current in internal_outputs and current not in seen:
        seen.add(current)
        path.append(current)
        current = predecessor.get(current)

    path.reverse()
    return [
        PathNode(node=name, level=levels.get(name, 0), path_index=index)
        for index, name in enumerate(path, start=1)
    ]


def row_float(row: pd.Series, column: str) -> float | None:
    if column not in row or pd.isna(row[column]):
        return None
    return float(row[column])


def row_int(row: pd.Series, column: str) -> int | None:
    if column not in row or pd.isna(row[column]):
        return None
    return int(row[column])


def choice_from_row(category: str, row: pd.Series, explanation: str) -> MappingChoice:
    distance = row_float(row, "distance")
    similarity = row_float(row, "similarity")
    if category in {"exact", "complemented", "sat_verified_nonexact"}:
        confidence = 1.0
    elif similarity is not None:
        confidence = similarity
    else:
        confidence = row_float(row, "combined_score")

    return MappingChoice(
        category=category,
        original_node=str(row.get("original_candidate", "")),
        confidence=confidence,
        distance=distance,
        combined_score=row_float(row, "combined_score"),
        support_overlap=row_float(row, "support_overlap"),
        simulation_similarity=row_float(row, "simulation_similarity"),
        rank=row_int(row, "rank"),
        distance_mode=str(row.get("distance_mode", "")),
        is_formal_distance=(
            bool(row["is_formal_distance"])
            if "is_formal_distance" in row and not pd.isna(row["is_formal_distance"])
            else None
        ),
        explanation=explanation,
    )


def best_ranked_row(df: pd.DataFrame) -> pd.Series | None:
    if df.empty:
        return None
    sort_cols = [col for col in ["rank", "combined_score", "support_overlap", "simulation_similarity"] if col in df]
    ascending = [True] + [False] * (len(sort_cols) - 1)
    return df.sort_values(sort_cols, ascending=ascending).iloc[0]


def choose_mapping_for_node(
    benchmark: str,
    optimization: str,
    optimized_node: str,
    exact: pd.DataFrame,
    complemented: pd.DataFrame,
    sat_verified: pd.DataFrame,
    approximate: pd.DataFrame,
) -> MappingChoice:
    key_filter = (
        (exact["benchmark"] == benchmark)
        & (exact["optimization"] == optimization)
        & (exact["optimized_node"] == optimized_node)
    )
    row = best_ranked_row(exact[key_filter])
    if row is not None:
        formal = bool(row.get("is_formal_exact_mode", False))
        return choice_from_row(
            "exact",
            row,
            "Exact anchor from top_candidates "
            + ("in formal truth-table mode." if formal else "in simulation-pattern mode."),
        )

    key_filter = (
        (complemented["benchmark"] == benchmark)
        & (complemented["optimization"] == optimization)
        & (complemented["optimized_node"] == optimized_node)
    )
    row = best_ranked_row(complemented[key_filter])
    if row is not None:
        return choice_from_row(
            "complemented",
            row,
            "Complemented equivalence was verified by the complemented SAT layer.",
        )

    key_filter = (
        (sat_verified["benchmark"] == benchmark)
        & (sat_verified["optimization"] == optimization)
        & (sat_verified["optimized_node"] == optimized_node)
    )
    row = best_ranked_row(sat_verified[key_filter])
    if row is not None:
        return choice_from_row(
            "sat_verified_nonexact",
            row,
            "Same-polarity SAT/CEC verified a non-exact-name correspondence.",
        )

    key_filter = (
        (approximate["benchmark"] == benchmark)
        & (approximate["optimization"] == optimization)
        & (approximate["optimized_node"] == optimized_node)
    )
    rows = approximate[key_filter]
    if not rows.empty:
        rows = rows.sort_values(["distance", "combined_score"], ascending=[True, False])
        row = rows.iloc[0]
        return choice_from_row(
            "approximate_near_match",
            row,
            "Closest approximate-distance candidate below the configured threshold.",
        )

    return MappingChoice(
        category="unresolved",
        original_node="",
        explanation="No exact, complemented, SAT-verified, or near-distance candidate was available.",
    )


def load_exact_candidates() -> pd.DataFrame:
    cols = [
        "benchmark",
        "optimization",
        "optimized_node",
        "rank",
        "original_candidate",
        "combined_score",
        "simulation_similarity",
        "support_overlap",
        "match_category",
        "is_formal_exact_mode",
    ]
    df = pd.read_csv(TOP_CANDIDATES, usecols=cols)
    return df[df["match_category"] == "exact_anchor"].copy()


def load_complemented_candidates() -> pd.DataFrame:
    frames = []
    for path in COMPLEMENT_FILES:
        if not path.exists():
            continue
        df = pd.read_csv(path)
        if "complement_status" not in df:
            continue
        frames.append(df[df["complement_status"] == "verified"].copy())
    if not frames:
        return empty_candidate_frame()
    return pd.concat(frames, ignore_index=True).drop_duplicates(
        ["benchmark", "optimization", "optimized_node", "original_candidate", "rank"]
    )


def load_sat_verified_nonexact() -> pd.DataFrame:
    df = pd.read_csv(SAT_CANDIDATES)
    return df[
        (df["sat_status"] == "verified")
        & (df["match_category"] == "non_exact_candidate")
    ].copy()


def load_approximate_candidates(threshold: float) -> pd.DataFrame:
    frames = [pd.read_csv(path) for path in APPROX_FILES if path.exists()]
    if not frames:
        return empty_candidate_frame()
    df = pd.concat(frames, ignore_index=True)
    return df[
        (df["sat_status"] == "rejected")
        & (df["distance"].notna())
        & (df["distance"] <= threshold)
    ].copy()


def empty_candidate_frame() -> pd.DataFrame:
    return pd.DataFrame(
        columns=[
            "benchmark",
            "optimization",
            "optimized_node",
            "rank",
            "original_candidate",
            "combined_score",
            "support_overlap",
            "simulation_similarity",
        ]
    )


def discover_case_studies(circuits: list[str], optimizations: list[str] | None) -> list[tuple[str, str]]:
    summary_path = RESULTS / "summary_metrics.csv"
    if summary_path.exists():
        summary = pd.read_csv(summary_path, usecols=["benchmark", "optimization"])
        wanted = {f"external_iscas85_{circuit}" for circuit in circuits}
        summary = summary[summary["benchmark"].isin(wanted)]
        summary = summary[summary["optimization"] != "original"]
        if optimizations:
            summary = summary[summary["optimization"].isin(optimizations)]
        return sorted(set(map(tuple, summary[["benchmark", "optimization"]].itertuples(index=False, name=None))))

    pairs = []
    for circuit in circuits:
        benchmark = f"external_iscas85_{circuit}"
        for path in sorted((ROOT / "variants").glob(f"{benchmark}_*.blif")):
            optimization = path.name.removeprefix(f"{benchmark}_").removesuffix(".blif")
            if optimization == "original":
                continue
            if optimizations and optimization not in optimizations:
                continue
            pairs.append((benchmark, optimization))
    return sorted(set(pairs))


def build_mapping_rows(
    case_studies: list[tuple[str, str]],
    threshold: float,
) -> pd.DataFrame:
    exact = load_exact_candidates()
    complemented = load_complemented_candidates()
    sat_verified = load_sat_verified_nonexact()
    approximate = load_approximate_candidates(threshold)

    rows: list[dict] = []
    for benchmark, optimization in case_studies:
        optimized_path = ROOT / "variants" / f"{benchmark}_{optimization}.blif"
        if not optimized_path.exists():
            continue
        path_nodes = extract_longest_internal_path(parse_blif(optimized_path))
        total_nodes = len(path_nodes)
        for path_node in path_nodes:
            choice = choose_mapping_for_node(
                benchmark,
                optimization,
                path_node.node,
                exact,
                complemented,
                sat_verified,
                approximate,
            )
            rows.append(
                {
                    "benchmark": benchmark,
                    "circuit": benchmark.replace("external_iscas85_", ""),
                    "optimization": optimization,
                    "path_length": total_nodes,
                    "path_index": path_node.path_index,
                    "optimized_node": path_node.node,
                    "optimized_depth": path_node.level,
                    "optimized_level": path_node.level,
                    "mapped_original_node": choice.original_node,
                    "mapping_category": choice.category,
                    "confidence": choice.confidence,
                    "distance": choice.distance,
                    "combined_score": choice.combined_score,
                    "support_overlap": choice.support_overlap,
                    "simulation_similarity": choice.simulation_similarity,
                    "rank": choice.rank,
                    "distance_mode": choice.distance_mode,
                    "is_formal_distance": choice.is_formal_distance,
                    "approx_threshold": threshold,
                    "explanation": choice.explanation,
                }
            )
    columns = [
        "benchmark",
        "circuit",
        "optimization",
        "path_length",
        "path_index",
        "optimized_node",
        "optimized_depth",
        "optimized_level",
        "mapped_original_node",
        "mapping_category",
        "confidence",
        "distance",
        "combined_score",
        "support_overlap",
        "simulation_similarity",
        "rank",
        "distance_mode",
        "is_formal_distance",
        "approx_threshold",
        "explanation",
    ]
    return pd.DataFrame(rows, columns=columns)


def summarize_mappings(rows: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    category_order = list(MAPPING_PRIORITY)
    if rows.empty:
        summary = pd.DataFrame(
            columns=[
                "benchmark",
                "circuit",
                "optimization",
                "critical_path_nodes",
                "exact",
                "complemented",
                "sat_verified_nonexact",
                "approximate_near_match",
                "unresolved",
                "mapped_fraction",
                "exact_fraction",
                "approximate_fraction",
                "unresolved_fraction",
            ]
        )
        totals = pd.DataFrame(columns=["mapping_category", "count"])
        return summary, totals

    grouped = (
        rows.groupby(["benchmark", "circuit", "optimization", "mapping_category"])
        .size()
        .unstack("mapping_category", fill_value=0)
    )
    for category in category_order:
        if category not in grouped:
            grouped[category] = 0
    grouped = grouped[category_order].reset_index()
    grouped["critical_path_nodes"] = grouped[category_order].sum(axis=1)
    grouped["mapped_nodes"] = grouped["critical_path_nodes"] - grouped["unresolved"]
    grouped["mapped_fraction"] = grouped["mapped_nodes"] / grouped["critical_path_nodes"]
    grouped["exact_fraction"] = grouped["exact"] / grouped["critical_path_nodes"]
    grouped["approximate_fraction"] = grouped["approximate_near_match"] / grouped["critical_path_nodes"]
    grouped["unresolved_fraction"] = grouped["unresolved"] / grouped["critical_path_nodes"]
    grouped = grouped[
        [
            "benchmark",
            "circuit",
            "optimization",
            "critical_path_nodes",
            *category_order,
            "mapped_fraction",
            "exact_fraction",
            "approximate_fraction",
            "unresolved_fraction",
        ]
    ]

    totals = rows["mapping_category"].value_counts().reindex(category_order, fill_value=0)
    totals = totals.rename_axis("mapping_category").reset_index(name="count")
    return grouped, totals


def write_markdown(rows: pd.DataFrame, summary: pd.DataFrame, totals: pd.DataFrame) -> None:
    total_nodes = int(totals["count"].sum()) if not totals.empty else 0
    unresolved = int(totals.loc[totals["mapping_category"] == "unresolved", "count"].sum()) if total_nodes else 0
    mapped = total_nodes - unresolved
    mapped_fraction = mapped / total_nodes if total_nodes else 0.0
    unresolved_fraction = unresolved / total_nodes if total_nodes else 0.0

    lines = [
        "# Critical-Path Back-Mapping Summary",
        "",
        "This prototype uses structural longest path as a timing proxy, then maps",
        "optimized path nodes back to original nodes using exact anchors,",
        "complemented matches, SAT-verified non-exact matches, and approximate",
        "near-matches in that priority order.",
        "",
        f"- Optimized critical-path nodes analyzed: {total_nodes:,}",
        f"- Mapped nodes: {mapped:,} ({mapped_fraction:.1%})",
        f"- Unresolved nodes: {unresolved:,} ({unresolved_fraction:.1%})",
        "",
        "## Mapping Categories",
        "",
    ]
    if totals.empty:
        lines.append("No mappings were produced.")
    else:
        lines.append(totals.to_markdown(index=False))

    lines.extend(["", "## Per Circuit / Optimization Summary", ""])
    if summary.empty:
        lines.append("No case-study rows were available.")
    else:
        display_cols = [
            "circuit",
            "optimization",
            "critical_path_nodes",
            "exact",
            "complemented",
            "sat_verified_nonexact",
            "approximate_near_match",
            "unresolved",
            "mapped_fraction",
            "unresolved_fraction",
        ]
        lines.append(summary[display_cols].to_markdown(index=False, floatfmt=".3f"))

    lines.extend(["", "## Example Mappings", ""])
    examples = rows[rows["mapping_category"] != "unresolved"].head(12)
    if examples.empty:
        lines.append("No mapped path nodes were available.")
    else:
        display_cols = [
            "circuit",
            "optimization",
            "path_index",
            "optimized_node",
            "mapped_original_node",
            "mapping_category",
            "confidence",
            "distance",
            "combined_score",
        ]
        lines.append(examples[display_cols].to_markdown(index=False, floatfmt=".4f"))

    lines.append("")
    MAPPING_MD.write_text("\n".join(lines), encoding="utf-8")


def plot_outputs(rows: pd.DataFrame, summary: pd.DataFrame, totals: pd.DataFrame) -> None:
    PLOTS.mkdir(parents=True, exist_ok=True)
    if rows.empty:
        return

    colors = {
        "exact": "#4c78a8",
        "complemented": "#72b7b2",
        "sat_verified_nonexact": "#54a24b",
        "approximate_near_match": "#f2a541",
        "unresolved": "#b8b8b8",
    }

    fig, ax = plt.subplots(figsize=(7, 4.5))
    plot_totals = totals[totals["count"] > 0]
    ax.bar(
        plot_totals["mapping_category"],
        plot_totals["count"],
        color=[colors.get(cat, "#777777") for cat in plot_totals["mapping_category"]],
    )
    ax.set_ylabel("critical-path node count")
    ax.set_xlabel("mapping category")
    ax.set_title("Critical-Path Mapping Categories")
    ax.tick_params(axis="x", rotation=25)
    save_plot(PLOTS / "critical_path_mapping_categories.png")

    by_circuit = rows.assign(mapped=rows["mapping_category"] != "unresolved")
    by_circuit = by_circuit.groupby("circuit")["mapped"].mean().sort_index()
    fig, ax = plt.subplots(figsize=(6.5, 4.2))
    by_circuit.plot(kind="bar", ax=ax, color="#4c78a8")
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("mapped fraction")
    ax.set_xlabel("ISCAS-85 circuit")
    ax.set_title("Critical-Path Mapped Fraction by Circuit")
    ax.tick_params(axis="x", rotation=0)
    save_plot(PLOTS / "critical_path_mapped_fraction_by_circuit.png")

    pivot = (
        rows.groupby(["optimization", "mapping_category"])
        .size()
        .unstack("mapping_category", fill_value=0)
    )
    for category in MAPPING_PRIORITY:
        if category not in pivot:
            pivot[category] = 0
    pivot = pivot[list(MAPPING_PRIORITY)]
    ax = pivot.plot(
        kind="bar",
        stacked=True,
        figsize=(9, 4.8),
        color=[colors[category] for category in pivot.columns],
    )
    ax.set_ylabel("critical-path node count")
    ax.set_xlabel("optimization")
    ax.set_title("Critical-Path Mapping by Optimization")
    ax.tick_params(axis="x", rotation=40)
    save_plot(PLOTS / "critical_path_mapping_by_optimization.png")


def save_plot(path: Path) -> None:
    plt.tight_layout()
    plt.savefig(path, dpi=180)
    plt.close()


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--circuits",
        nargs="+",
        default=list(DEFAULT_CIRCUITS),
        help="ISCAS-85 circuit names to analyze, for example c432 c2670 c6288.",
    )
    parser.add_argument(
        "--optimizations",
        nargs="+",
        default=None,
        help="Optional optimization pass filter. Defaults to every non-original pass.",
    )
    parser.add_argument(
        "--approx-threshold",
        type=float,
        default=DEFAULT_APPROX_THRESHOLD,
        help="Maximum approximate distance accepted as a near-match.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    case_studies = discover_case_studies(args.circuits, args.optimizations)
    rows = build_mapping_rows(case_studies, threshold=args.approx_threshold)
    summary, totals = summarize_mappings(rows)

    RESULTS.mkdir(parents=True, exist_ok=True)
    rows.to_csv(MAPPING_CSV, index=False)
    write_markdown(rows, summary, totals)
    plot_outputs(rows, summary, totals)

    print(f"Analyzed {len(case_studies)} circuit/optimization case studies")
    print(f"Critical-path nodes: {len(rows)}")
    if not totals.empty:
        for _, row in totals.iterrows():
            print(f"  {row['mapping_category']}: {int(row['count'])}")
    print(f"Wrote {MAPPING_CSV.relative_to(ROOT)} and {MAPPING_MD.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
