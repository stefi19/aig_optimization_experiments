#!/usr/bin/env python3
"""Calibrate sampled approximate-distance estimates against exact distances."""

from __future__ import annotations

import argparse
import csv
import math
import sys
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.approximate_node_distance import (  # noqa: E402
    evaluate_network_with_values,
    exact_pattern_values,
    hamming_distance_fraction,
    original_variant_path,
    sampled_pattern_values,
    structural_supports,
    variant_path,
)
from scripts.abc_native_sat_sweep_baseline import OPT_COMMANDS  # noqa: E402
from scripts.probe_abc_sat_sweeping import find_abc, run_abc_script  # noqa: E402
from analyze_blif_matches import parse_blif  # noqa: E402


RESULTS = ROOT / "results"
PLOTS = RESULTS / "plots"
EXACT_INPUT = RESULTS / "approximate_distance_exact.csv"
CALIBRATION_CSV = RESULTS / "approx_sampling_calibration.csv"
CALIBRATION_MD = RESULTS / "approx_sampling_calibration.md"

SAMPLE_SIZES = [128, 512, 1024, 4096, 8192]
SEEDS = [0, 1, 2, 3, 4]
DEFAULT_MAX_ROWS = 40
DEFAULT_MAX_EXACT_SUPPORT = 12


@dataclass
class CalibrationRow:
    benchmark: str
    optimization: str
    optimized_node: str
    original_candidate: str
    sat_status: str
    union_support_size: int
    exact_distance: float
    sample_size: int
    seed: int
    sampled_distance: float
    absolute_error: float
    exact_rank: float
    sampled_rank: float
    absolute_rank_delta: float


def select_exact_rows(exact: pd.DataFrame, max_rows: int) -> pd.DataFrame:
    usable = exact[
        (exact["distance_mode"] == "exact")
        & (exact["skip_reason"] == "ok")
        & exact["distance"].notna()
    ].copy()
    usable = usable.sort_values(
        [
            "benchmark",
            "optimization",
            "union_support_size",
            "optimized_node",
            "original_candidate",
        ],
        ascending=[True, True, True, True, True],
    )
    if max_rows <= 0 or len(usable) <= max_rows:
        return usable.reset_index(drop=True)
    per_bucket = max(1, math.ceil(max_rows / max(usable["union_support_size"].nunique(), 1)))
    selected = (
        usable.groupby("union_support_size", group_keys=False)
        .head(per_bucket)
        .head(max_rows)
    )
    if len(selected) < max_rows:
        remaining = usable.drop(selected.index).head(max_rows - len(selected))
        selected = pd.concat([selected, remaining], ignore_index=False)
    return selected.reset_index(drop=True)


def spearman_rank_correlation(left: list[float], right: list[float]) -> float | None:
    if len(left) < 2 or len(right) < 2:
        return None
    mean_left = sum(left) / len(left)
    mean_right = sum(right) / len(right)
    cov = sum((a - mean_left) * (b - mean_right) for a, b in zip(left, right))
    var_left = sum((a - mean_left) ** 2 for a in left)
    var_right = sum((b - mean_right) ** 2 for b in right)
    if var_left == 0 or var_right == 0:
        return None
    return cov / math.sqrt(var_left * var_right)


def compute_sampled_distance(
    row: pd.Series,
    original_path: Path,
    optimized_path: Path,
    sample_size: int,
    seed: int,
    support_cache: dict[Path, dict[str, frozenset[str]]],
    input_cache: dict[Path, list[str]],
) -> float:
    original_node = row["original_candidate"]
    optimized_node = row["optimized_node"]

    original_supports = support_cache.setdefault(original_path, structural_supports(original_path))
    optimized_supports = support_cache.setdefault(optimized_path, structural_supports(optimized_path))
    union_support = set(original_supports[original_node]) | set(optimized_supports[optimized_node])

    if original_path not in input_cache:
        input_cache[original_path] = parse_blif(original_path).inputs
    if optimized_path not in input_cache:
        input_cache[optimized_path] = parse_blif(optimized_path).inputs
    net_inputs = sorted(set(input_cache[original_path]) | set(input_cache[optimized_path]))

    seed_key = (
        f"{row['benchmark']}|{row['optimization']}|{original_node}|"
        f"{optimized_node}|samples={sample_size}|seed={seed}"
    )
    values, mask, pattern_count = sampled_pattern_values(
        net_inputs, union_support, sample_size, seed_key
    )
    original_values = evaluate_network_with_values(original_path, values, mask)
    optimized_values = evaluate_network_with_values(optimized_path, values, mask)
    return hamming_distance_fraction(
        original_values[original_node].value,
        optimized_values[optimized_node].value,
        pattern_count,
    )


def compute_exact_distance(
    row: pd.Series,
    original_path: Path,
    optimized_path: Path,
    support_cache: dict[Path, dict[str, frozenset[str]]],
    input_cache: dict[Path, list[str]],
    max_exact_support: int,
) -> tuple[float, int]:
    original_node = row["original_candidate"]
    optimized_node = row["optimized_node"]

    original_supports = support_cache.setdefault(original_path, structural_supports(original_path))
    optimized_supports = support_cache.setdefault(optimized_path, structural_supports(optimized_path))
    union_support = set(original_supports[original_node]) | set(optimized_supports[optimized_node])
    if len(union_support) > max_exact_support:
        raise ValueError("recomputed support too large for exact calibration")

    if original_path not in input_cache:
        input_cache[original_path] = parse_blif(original_path).inputs
    if optimized_path not in input_cache:
        input_cache[optimized_path] = parse_blif(optimized_path).inputs
    net_inputs = sorted(set(input_cache[original_path]) | set(input_cache[optimized_path]))

    values, mask, pattern_count = exact_pattern_values(net_inputs, union_support)
    original_values = evaluate_network_with_values(original_path, values, mask)
    optimized_values = evaluate_network_with_values(optimized_path, values, mask)
    return (
        hamming_distance_fraction(
            original_values[original_node].value,
            optimized_values[optimized_node].value,
            pattern_count,
        ),
        len(union_support),
    )


def source_blif_for_benchmark(benchmark: str) -> Path | None:
    if benchmark.startswith("external_iscas85_"):
        circuit = benchmark.replace("external_iscas85_", "")
        path = ROOT / "benchmarks" / "external" / "iscas85" / f"{circuit}.blif"
        return path if path.exists() else None
    path = ROOT / "benchmarks" / f"{benchmark}.blif"
    if path.exists():
        return path
    generated = ROOT / "benchmarks" / "generated" / f"{benchmark}.blif"
    return generated if generated.exists() else None


def ensure_blif_paths(
    row: pd.Series,
    tmp: Path,
    abc_bin: str | None,
    generated_cache: dict[tuple[str, str], Path],
) -> tuple[Path | None, Path | None, str]:
    benchmark = row["benchmark"]
    optimization = row["optimization"]
    original_path = original_variant_path(benchmark)
    optimized_path = variant_path(benchmark, optimization)
    if original_path.exists() and optimized_path.exists():
        return original_path, optimized_path, "tracked_variants"

    source = source_blif_for_benchmark(benchmark)
    if source is None:
        return None, None, "missing_source_blif"
    original = original_path if original_path.exists() else source
    if optimized_path.exists():
        return original, optimized_path, "tracked_optimized_variant"

    command = OPT_COMMANDS.get(optimization)
    if command is None:
        return None, None, f"unknown_optimization:{optimization}"
    if abc_bin is None:
        return None, None, "missing_abc_for_temp_variant"

    key = (benchmark, optimization)
    if key not in generated_cache:
        out = tmp / f"{benchmark}_{optimization}.blif"
        script = f"read_blif {source}\n{command}\nwrite_blif {out}\n"
        exit_code, output = run_abc_script(abc_bin, script, timeout=60)
        if exit_code != 0 or not out.exists():
            return None, None, "abc_variant_generation_failed"
        generated_cache[key] = out
    return original, generated_cache[key], "temporary_optimized_variant"


def add_rank_columns(rows: list[dict]) -> list[dict]:
    df = pd.DataFrame(rows)
    if df.empty:
        return rows
    df["pair_id"] = (
        df["benchmark"]
        + "|"
        + df["optimization"]
        + "|"
        + df["optimized_node"]
        + "|"
        + df["original_candidate"]
    )
    exact_ranks = (
        df[["pair_id", "exact_distance"]]
        .drop_duplicates()
        .assign(exact_rank=lambda x: x["exact_distance"].rank(method="average", ascending=True))
    )
    df = df.drop(columns=["exact_rank", "sampled_rank", "absolute_rank_delta"], errors="ignore")
    df = df.merge(exact_ranks[["pair_id", "exact_rank"]], on="pair_id", how="left")
    df["sampled_rank"] = df.groupby(["sample_size", "seed"])["sampled_distance"].rank(
        method="average", ascending=True
    )
    df["absolute_rank_delta"] = (df["sampled_rank"] - df["exact_rank"]).abs()
    return df.drop(columns=["pair_id"]).to_dict("records")


def calibrate(
    max_rows: int = DEFAULT_MAX_ROWS,
    abc_bin: str | None = None,
    max_exact_support: int = DEFAULT_MAX_EXACT_SUPPORT,
) -> list[CalibrationRow]:
    exact = pd.read_csv(EXACT_INPUT)
    selected = select_exact_rows(exact, max_rows)
    support_cache: dict[Path, dict[str, frozenset[str]]] = {}
    input_cache: dict[Path, list[str]] = {}
    raw_rows: list[dict] = []
    generated_cache: dict[tuple[str, str], Path] = {}
    with tempfile.TemporaryDirectory(prefix="approx_sampling_calibration_") as td:
        tmp = Path(td)
        for _, row in selected.iterrows():
            original_path, optimized_path, _source = ensure_blif_paths(
                row, tmp, abc_bin, generated_cache
            )
            if original_path is None or optimized_path is None:
                continue
            try:
                exact_distance, union_support_size = compute_exact_distance(
                    row,
                    original_path,
                    optimized_path,
                    support_cache,
                    input_cache,
                    max_exact_support,
                )
            except (KeyError, ValueError):
                continue
            for sample_size in SAMPLE_SIZES:
                for seed in SEEDS:
                    try:
                        sampled = compute_sampled_distance(
                            row,
                            original_path,
                            optimized_path,
                            sample_size,
                            seed,
                            support_cache,
                            input_cache,
                        )
                    except KeyError:
                        break
                    raw_rows.append(
                        {
                            "benchmark": row["benchmark"],
                            "optimization": row["optimization"],
                            "optimized_node": row["optimized_node"],
                            "original_candidate": row["original_candidate"],
                            "sat_status": row["sat_status"],
                            "union_support_size": union_support_size,
                            "exact_distance": exact_distance,
                            "sample_size": sample_size,
                            "seed": seed,
                            "sampled_distance": sampled,
                            "absolute_error": abs(sampled - exact_distance),
                            "exact_rank": 0.0,
                            "sampled_rank": 0.0,
                            "absolute_rank_delta": 0.0,
                        }
                    )
    return [CalibrationRow(**row) for row in add_rank_columns(raw_rows)]


def summarize(rows: list[CalibrationRow]) -> pd.DataFrame:
    df = pd.DataFrame([asdict(row) for row in rows])
    columns = [
        "sample_size",
        "rows",
        "mean_absolute_error",
        "median_absolute_error",
        "max_error",
        "pct_within_1pct_abs_error",
        "pct_within_2pct_abs_error",
        "pct_within_5pct_abs_error",
        "mean_absolute_rank_delta",
        "mean_spearman_rank_correlation",
    ]
    if df.empty:
        return pd.DataFrame(columns=columns)
    spearman_rows = []
    for (sample_size, seed), group in df.groupby(["sample_size", "seed"]):
        corr = spearman_rank_correlation(
            group["exact_rank"].tolist(), group["sampled_rank"].tolist()
        )
        if corr is not None:
            spearman_rows.append(
                {
                    "sample_size": sample_size,
                    "seed": seed,
                    "spearman_rank_correlation": corr,
                }
            )
    spearman = pd.DataFrame(spearman_rows)
    summary = (
        df.groupby("sample_size")
        .agg(
            rows=("absolute_error", "size"),
            mean_absolute_error=("absolute_error", "mean"),
            median_absolute_error=("absolute_error", "median"),
            max_error=("absolute_error", "max"),
            pct_within_1pct_abs_error=("absolute_error", lambda x: (x <= 0.01).mean()),
            pct_within_2pct_abs_error=("absolute_error", lambda x: (x <= 0.02).mean()),
            pct_within_5pct_abs_error=("absolute_error", lambda x: (x <= 0.05).mean()),
            mean_absolute_rank_delta=("absolute_rank_delta", "mean"),
        )
        .reset_index()
    )
    if spearman.empty:
        summary["mean_spearman_rank_correlation"] = None
    else:
        summary = summary.merge(
            spearman.groupby("sample_size")["spearman_rank_correlation"].mean().reset_index(
                name="mean_spearman_rank_correlation"
            ),
            on="sample_size",
            how="left",
        )
    return summary[columns]


def write_csv(rows: list[CalibrationRow], path: Path = CALIBRATION_CSV) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(CalibrationRow.__annotations__)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))


def write_markdown(rows: list[CalibrationRow], path: Path = CALIBRATION_MD) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame([asdict(row) for row in rows])
    summary = summarize(rows)
    selected_pairs = 0 if df.empty else df[
        ["benchmark", "optimization", "optimized_node", "original_candidate"]
    ].drop_duplicates().shape[0]
    lines = [
        "# Approximate-Distance Sampling Calibration",
        "",
        "This calibration recomputes sampled distances for candidate pairs whose exact",
        "truth-table distance is available. Exact distances are recomputed on the same",
        "currently reproducible BLIF pair used for sampling, so stale generated variants",
        "are skipped instead of mixed into the error estimate. This estimates sampling",
        "error; it does not make sampled rows formal.",
        "",
        f"- Exact candidate pairs calibrated: {selected_pairs}",
        f"- Sample sizes: {', '.join(str(size) for size in SAMPLE_SIZES)}",
        f"- Seeds per sample size: {len(SEEDS)}",
        "",
        "## Error by Sample Size",
        "",
    ]
    if summary.empty:
        lines.append("No calibration rows were produced.")
    else:
        lines.append(summary.to_markdown(index=False, floatfmt=".5f"))
    lines.extend(
        [
            "",
            "## Rank Stability",
            "",
            "Rank stability is measured indirectly by ranking the calibrated exact-distance",
            "pairs by exact distance and by sampled distance for each sample-size/seed run.",
            "This is only a local calibration set, not a full replacement for end-to-end",
            "candidate-ranking validation.",
            "",
        ]
    )
    if not summary.empty:
        rank_cols = [
            "sample_size",
            "mean_absolute_rank_delta",
            "mean_spearman_rank_correlation",
        ]
        lines.append(summary[rank_cols].to_markdown(index=False, floatfmt=".5f"))
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "Small sample sizes can be useful for coarse screening, but the calibration",
            "should be consulted before treating sampled approximate distance as a stable",
            "ranking signal. Exact rows remain formal; sampled rows remain estimates.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def plot_outputs(rows: list[CalibrationRow]) -> None:
    if not rows:
        return
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    PLOTS.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame([asdict(row) for row in rows])
    summary = summarize(rows)

    fig, ax = plt.subplots(figsize=(7.2, 4.6))
    ax.plot(summary["sample_size"], summary["mean_absolute_error"], marker="o", label="mean")
    ax.plot(summary["sample_size"], summary["max_error"], marker="o", label="max")
    ax.set_xscale("log", base=2)
    ax.set_xlabel("sample size")
    ax.set_ylabel("absolute distance error")
    ax.set_title("Sampled Distance Error by Sample Size")
    ax.grid(True, alpha=0.3)
    ax.legend()
    save_plot(plt, PLOTS / "approx_sampling_error_by_sample_size.png")

    largest = max(SAMPLE_SIZES)
    fig, ax = plt.subplots(figsize=(5.8, 5.4))
    subset = df[df["sample_size"] == largest]
    ax.scatter(subset["exact_distance"], subset["sampled_distance"], alpha=0.45, s=18)
    ax.plot([0, 1], [0, 1], color="#b54848", linewidth=1.2)
    ax.set_xlim(-0.02, max(0.12, subset["exact_distance"].max() + 0.03))
    ax.set_ylim(-0.02, max(0.12, subset["sampled_distance"].max() + 0.03))
    ax.set_xlabel("exact distance")
    ax.set_ylabel(f"sampled distance ({largest} patterns)")
    ax.set_title("Exact vs Sampled Approximate Distance")
    ax.grid(True, alpha=0.3)
    save_plot(plt, PLOTS / "approx_sampling_exact_vs_sampled.png")

    fig, ax = plt.subplots(figsize=(7.2, 4.6))
    ax.plot(
        summary["sample_size"],
        summary["mean_spearman_rank_correlation"],
        marker="o",
        color="#2f7d32",
    )
    ax.set_xscale("log", base=2)
    ax.set_ylim(0, 1.02)
    ax.set_xlabel("sample size")
    ax.set_ylabel("mean Spearman rank correlation")
    ax.set_title("Sampled Ranking Stability on Exact-Distance Rows")
    ax.grid(True, alpha=0.3)
    save_plot(plt, PLOTS / "approx_sampling_rank_stability.png")


def save_plot(plt, path: Path) -> None:
    plt.tight_layout()
    plt.savefig(path, dpi=180)
    plt.close()


def copy_plots_to_presentation() -> None:
    src_names = [
        "approx_sampling_error_by_sample_size.png",
        "approx_sampling_exact_vs_sampled.png",
        "approx_sampling_rank_stability.png",
    ]
    target_dir = ROOT / "docs" / "presentation" / "assets" / "plots"
    target_dir.mkdir(parents=True, exist_ok=True)
    for name in src_names:
        src = PLOTS / name
        if src.exists():
            (target_dir / name).write_bytes(src.read_bytes())


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--max-rows",
        type=int,
        default=DEFAULT_MAX_ROWS,
        help="Maximum exact-distance candidate pairs to calibrate; 0 means all exact rows.",
    )
    parser.add_argument("--abc", help="Path to ABC binary for temporary missing variants.")
    parser.add_argument("--max-exact-support", type=int, default=DEFAULT_MAX_EXACT_SUPPORT)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    abc_bin = None
    try:
        abc_bin = find_abc(args.abc)
    except FileNotFoundError:
        abc_bin = None
    rows = calibrate(
        max_rows=args.max_rows,
        abc_bin=abc_bin,
        max_exact_support=args.max_exact_support,
    )
    write_csv(rows)
    write_markdown(rows)
    plot_outputs(rows)
    copy_plots_to_presentation()
    summary = summarize(rows)
    print(f"Wrote {CALIBRATION_CSV.relative_to(ROOT)}")
    print(f"Wrote {CALIBRATION_MD.relative_to(ROOT)}")
    for plot in [
        PLOTS / "approx_sampling_error_by_sample_size.png",
        PLOTS / "approx_sampling_exact_vs_sampled.png",
        PLOTS / "approx_sampling_rank_stability.png",
    ]:
        if plot.exists():
            print(f"Wrote {plot.relative_to(ROOT)}")
    if not summary.empty:
        best = summary.sort_values("sample_size").tail(1).iloc[0]
        print(
            "Largest sample size MAE="
            f"{best['mean_absolute_error']:.5f}, max_error={best['max_error']:.5f}, "
            f"rank_corr={best['mean_spearman_rank_correlation']:.5f}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
