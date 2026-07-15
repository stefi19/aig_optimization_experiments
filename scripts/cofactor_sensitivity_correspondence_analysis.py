#!/usr/bin/env python3
"""Compute cofactor and sensitivity features for labeled correspondence candidates."""

from __future__ import annotations

import argparse
import math
import os
import shutil
import subprocess
import tempfile
import time
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from cofactor_analysis import compute_cofactor_features  # noqa: E402
from contextual_error_metrics import normalize_mapping_category  # noqa: E402
from functional_ranking_features import compute_ranking_scores, formal_label, support_bucket  # noqa: E402
from sensitivity_signatures import compare_sensitivity_profiles  # noqa: E402
from scripts.benchmark_id import infer_source_family  # noqa: E402

RESULTS = ROOT / "results"
OUT_DIR = RESULTS / "cofactor_sensitivity"
DEFAULT_INPUT = RESULTS / "sat_verified_candidates.csv"
DEFAULT_CSV = OUT_DIR / "cofactor_sensitivity_features.csv"
DEFAULT_MD = OUT_DIR / "cofactor_sensitivity_summary.md"

DEFAULT_BENCHMARKS = [
    "external_iscas85_c432",
    "external_iscas85_c2670",
    "external_iscas85_c6288",
]
DEFAULT_OPTIMIZATIONS = ["balance", "rewrite", "resyn2", "dc2"]
ABC_COMMANDS = {
    "original": "strash",
    "balance": "strash; balance",
    "rewrite": "strash; rewrite",
    "refactor": "strash; refactor",
    "resub": "strash; resub",
    "resyn2_like": "strash; balance; rewrite; refactor; balance; rewrite -z; refactor -z; balance",
    "rewrite_z": "strash; rewrite -z",
    "refactor_z": "strash; refactor -z",
    "resyn": "strash; balance; rewrite; rewrite -z; balance; rewrite; balance",
    "resyn2": "strash; balance; rewrite; refactor; balance; rewrite -z; refactor -z; balance",
    "dc2": "strash; dc2",
    "compress2rs": "strash; balance; rewrite; refactor; resub; balance; rewrite -z; refactor -z; resub; balance",
}


def variant_path(benchmark: str, optimization: str) -> Path:
    return ROOT / "variants" / f"{benchmark}_{optimization}.blif"


def original_variant_path(benchmark: str) -> Path:
    return ROOT / "variants" / f"{benchmark}_original.blif"


def source_blif_for_benchmark(benchmark: str) -> Path | None:
    if benchmark.startswith("external_iscas85_"):
        circuit = benchmark.replace("external_iscas85_", "")
        path = ROOT / "benchmarks" / "external" / "iscas85" / f"{circuit}.blif"
        return path if path.exists() else None
    for path in [
        ROOT / "benchmarks" / f"{benchmark}.blif",
        ROOT / "benchmarks" / "generated" / f"{benchmark.replace('generated_', '')}.blif",
    ]:
        if path.exists():
            return path
    return None


def find_abc() -> str | None:
    env = os.environ.get("ABC")
    if env and Path(env).exists():
        return env
    default = ROOT / ".abc_build" / "abc_repo" / "abc"
    if default.exists():
        return str(default)
    return shutil.which("abc")


def run_abc_variant(abc_bin: str | None, source: Path, optimization: str, out: Path) -> bool:
    if out.exists():
        return True
    if not abc_bin or optimization not in ABC_COMMANDS:
        return False
    completed = subprocess.run(
        [abc_bin, "-c", f"read_blif {source}; {ABC_COMMANDS[optimization]}; write_blif {out}"],
        capture_output=True,
        text=True,
        check=False,
    )
    return completed.returncode == 0 and out.exists()


def parse_csv_list(value: str | None, default: list[str]) -> list[str]:
    if not value:
        return list(default)
    return [item.strip() for item in value.split(",") if item.strip()]


def load_candidates(path: Path, benchmarks: list[str], optimizations: list[str], top_k: int, max_candidates: int) -> pd.DataFrame:
    df = pd.read_csv(path)
    if "match_category" in df:
        df["match_category"] = df["match_category"].map(normalize_mapping_category)
    df = df[df["benchmark"].isin(benchmarks) & df["optimization"].isin(optimizations)].copy()
    if "rank" in df:
        df = df[pd.to_numeric(df["rank"], errors="coerce").fillna(999999) <= top_k].copy()
    df = df[df["sat_status"].isin(["verified", "rejected", "undecided", "timeout"])].copy()
    df = df.sort_values(
        ["benchmark", "optimization", "optimized_node", "rank", "combined_score", "original_candidate"],
        ascending=[True, True, True, True, False, True],
    )
    if max_candidates > 0 and not df.empty:
        group_count = df[["benchmark", "optimization"]].drop_duplicates().shape[0]
        per_group = max(1, math.ceil(max_candidates / max(1, group_count)))
        df = (
            df.groupby(["benchmark", "optimization"], group_keys=False, sort=True)
            .head(per_group)
            .reset_index(drop=True)
        )
    return df


def materialize_paths(benchmark: str, optimization: str, tmp_dir: Path, abc_bin: str | None) -> tuple[Path | None, Path | None, str, str, str]:
    original = original_variant_path(benchmark)
    optimized = variant_path(benchmark, optimization)
    source = source_blif_for_benchmark(benchmark)
    original_label = str(original.relative_to(ROOT))
    optimized_label = str(optimized.relative_to(ROOT))
    reason = "ok"
    if not original.exists():
        if source is None:
            return None, None, original_label, optimized_label, "missing_original_blif"
        original = source
        original_label = str(source.relative_to(ROOT))
    if not optimized.exists():
        if source is None:
            return original, None, original_label, optimized_label, "missing_optimized_blif"
        generated = tmp_dir / f"{benchmark}_{optimization}.blif"
        if not run_abc_variant(abc_bin, source, optimization, generated):
            return original, None, original_label, optimized_label, "missing_optimized_blif"
        optimized = generated
        optimized_label = f"temporary_abc_variant:{benchmark}_{optimization}.blif"
    return original, optimized, original_label, optimized_label, reason


def analyze_candidate(row: pd.Series, exact_support_limit: int, sample_count: int, seed: int, tmp_dir: Path, abc_bin: str | None) -> dict[str, object]:
    start = time.perf_counter()
    benchmark = str(row["benchmark"])
    optimization = str(row["optimization"])
    original_node = str(row["original_candidate"])
    optimized_node = str(row["optimized_node"])
    original_path, optimized_path, original_label, optimized_label, path_reason = materialize_paths(
        benchmark,
        optimization,
        tmp_dir,
        abc_bin,
    )

    base: dict[str, object] = {
        "benchmark": benchmark,
        "benchmark_family": infer_source_family(benchmark),
        "optimization": optimization,
        "original_node": original_node,
        "optimized_node": optimized_node,
        "candidate_rank": int(row.get("rank", 0)),
        "combined_score": float(row.get("combined_score", 0.0)),
        "support_overlap": row.get("support_overlap", ""),
        "sat_status": row.get("sat_status", ""),
        "formal_label": formal_label(row.to_dict()),
        "match_category": normalize_mapping_category(row.get("match_category", "")),
        "seed": seed,
        "sample_count": sample_count,
        "exact_support_limit": exact_support_limit,
        "original_blif": original_label,
        "optimized_blif": optimized_label,
    }
    if original_path is None or optimized_path is None or not original_path.exists() or not optimized_path.exists():
        base.update(
            {
                "cofactor_status": "skipped",
                "cofactor_skipped_reason": path_reason,
                "cofactor_mode": "unavailable",
                "cofactor_evidence_level": "unresolved",
                "sensitivity_status": "skipped",
                "sensitivity_skipped_reason": "missing_blif",
                "sensitivity_mode": "unavailable",
                "sensitivity_evidence_level": "unresolved",
                "functional_feature_mode": "unavailable",
                "functional_feature_evidence_level": "unresolved",
                "support_size_bucket": "0-4",
                "cofactor_consistency_score": 0.0,
                "mean_cofactor_similarity": 0.0,
                "max_cofactor_error": 0.0,
                "sensitivity_cosine_similarity": 0.0,
                "boolean_difference_similarity": 0.0,
                "dominant_variable_agreement": 0,
                "inactive_variable_agreement": 0.0,
                "original_support_size": 0,
                "optimized_support_size": 0,
                "runtime_seconds": time.perf_counter() - start,
            }
        )
        base.update(compute_ranking_scores(base).as_dict())
        return base

    cofactor = compute_cofactor_features(
        original_path,
        optimized_path,
        original_node,
        optimized_node,
        exact_support_limit=exact_support_limit,
        sample_count=sample_count,
        seed=seed,
    ).as_dict()
    sensitivity = compare_sensitivity_profiles(
        original_path,
        optimized_path,
        original_node,
        optimized_node,
        exact_support_limit=exact_support_limit,
        sample_count=sample_count,
        seed=seed,
    ).as_dict()
    cofactor = {f"cofactor_{key}" if key in {"status", "skipped_reason", "mode", "evidence_level"} else key: value for key, value in cofactor.items()}
    sensitivity = {f"sensitivity_{key}" if key in {"status", "skipped_reason"} else key: value for key, value in sensitivity.items()}
    base.update(cofactor)
    base.update(sensitivity)
    base["functional_feature_mode"] = (
        "exhaustive"
        if base.get("cofactor_evidence_level") == base.get("sensitivity_evidence_level") == "formal_exhaustive"
        else "sampled"
        if "sampled_estimate" in {base.get("cofactor_evidence_level"), base.get("sensitivity_evidence_level")}
        else "unavailable"
    )
    base["functional_feature_evidence_level"] = (
        "formal_exhaustive"
        if base["functional_feature_mode"] == "exhaustive"
        else "sampled_estimate"
        if base["functional_feature_mode"] == "sampled"
        else "unresolved"
    )
    support_size = max(
        int(base.get("original_support_size") or 0),
        int(base.get("optimized_support_size") or 0),
    )
    base["support_size_bucket"] = support_bucket(support_size)
    base["runtime_seconds"] = time.perf_counter() - start
    base.update(compute_ranking_scores(base).as_dict())
    return base


def write_summary(df: pd.DataFrame, path: Path) -> None:
    lines = [
        "# Cofactor- and Sensitivity-Aware Correspondence Features",
        "",
        "This analysis adds heuristic ranking features. SAT/CEC labels remain the formal evidence for equivalence; sampled cofactor and sensitivity rows are estimates only.",
        "",
        f"- Candidate-feature rows: {len(df):,}",
        f"- Unique candidate pairs: {df[['benchmark', 'optimization', 'optimized_node', 'original_node']].drop_duplicates().shape[0]:,}" if not df.empty else "- Unique candidate pairs: 0",
        f"- Seeds: {', '.join(map(str, sorted(df['seed'].unique()))) if not df.empty else 'none'}",
        "",
        "## Evidence Coverage",
        "",
    ]
    if df.empty:
        lines.append("No feature rows were generated.")
    else:
        coverage = df.groupby(["functional_feature_evidence_level", "formal_label"]).size().reset_index(name="rows")
        lines.append(coverage.to_markdown(index=False))
        lines.extend(["", "## Mean Feature Values by Formal Label", ""])
        means = df.groupby("formal_label")[
            [
                "cofactor_consistency_score",
                "mean_cofactor_similarity",
                "max_cofactor_error",
                "sensitivity_cosine_similarity",
                "boolean_difference_similarity",
            ]
        ].mean(numeric_only=True).reset_index()
        lines.append(means.to_markdown(index=False, floatfmt=".4f"))
        lines.extend(["", "## Ranking Modes", ""])
        lines.append(
            "Modes written to the CSV are `baseline`, `cofactor_only`, `sensitivity_only`, `cofactor_plus_sensitivity`, and `full_combined`. These scores are heuristic ranking signals, not proof of correspondence."
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-candidates", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-csv", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--output-summary", type=Path, default=DEFAULT_MD)
    parser.add_argument("--exact-support-limit", type=int, default=8)
    parser.add_argument("--sample-count", type=int, default=256)
    parser.add_argument("--seed", type=int, default=23)
    parser.add_argument("--seeds", default="23,29")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--benchmarks", default=",".join(DEFAULT_BENCHMARKS))
    parser.add_argument("--optimizations", default=",".join(DEFAULT_OPTIMIZATIONS))
    parser.add_argument("--max-candidates", type=int, default=40)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if not args.input_candidates.exists():
        raise SystemExit(f"missing candidate CSV: {args.input_candidates}")
    benchmarks = parse_csv_list(args.benchmarks, DEFAULT_BENCHMARKS)
    optimizations = parse_csv_list(args.optimizations, DEFAULT_OPTIMIZATIONS)
    seeds = [int(seed) for seed in parse_csv_list(args.seeds, [str(args.seed)])]
    candidates = load_candidates(args.input_candidates, benchmarks, optimizations, args.top_k, args.max_candidates)
    abc_bin = find_abc()
    with tempfile.TemporaryDirectory(prefix="cofactor_sensitivity_") as tmp:
        tmp_dir = Path(tmp)
        rows = [
            analyze_candidate(candidate, args.exact_support_limit, args.sample_count, seed, tmp_dir, abc_bin)
            for seed in seeds
            for _, candidate in candidates.iterrows()
        ]
    out = pd.DataFrame(rows)
    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.output_csv, index=False)
    write_summary(out, args.output_summary)
    print(f"Wrote {len(out):,} feature rows to {args.output_csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
