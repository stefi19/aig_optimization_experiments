#!/usr/bin/env python3
"""Generate semantic functional refactoring plots from committed CSVs."""

from __future__ import annotations

import csv
import shutil
from collections import Counter
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "semantic_functional_refactoring"
PLOTS = ROOT / "results" / "plots"
PRESENTATION = ROOT / "docs" / "presentation" / "assets" / "plots"


def main() -> int:
    PLOTS.mkdir(parents=True, exist_ok=True)
    PRESENTATION.mkdir(parents=True, exist_ok=True)
    controlled = _read("controlled_experiments.csv")
    decomp = _read("decomposability_queries.csv")
    quotient = _read("quotient_synthesis.csv")
    rewrites = _read("graph_rewrites.csv")
    cec = _read("global_abc_cec.csv")
    boundary = _read("boundary_restoration.csv")
    failures = _read("failure_taxonomy.csv")
    utility = _read("interface_utility.csv")
    baselines = _read("baselines.csv")
    ablations = _read("ablations.csv")
    runtime = _read("runtime.csv")
    real = _read("development_experiments.csv")
    heldout = _read("heldout_experiments.csv")

    paths = [
        _bar("semantic_functional_refactoring_funnel.png", ["divisors", "windows", "decomp", "quotient", "graph", "CEC", "active", "restored"], [len(_read("divisor_candidates.csv")), len(_read("window_candidates.csv")), _count(decomp, "formal_status", "decomposable"), _count(quotient, "quotient_status", "synthesized_truth_table"), _count(rewrites, "graph_rewrite_status", "valid"), _count(cec, "global_cec_status", "equivalent"), _count(rewrites, "graph_active", "true"), _count(boundary, "restored_boundary", "true")], "Functional refactoring proof funnel"),
        _counter("semantic_functional_refactoring_decomposition_status.png", Counter(r["formal_status"] for r in decomp), "Decomposability outcomes"),
        _counter("semantic_functional_refactoring_failure_taxonomy.png", Counter({f"{r['benchmark_group']}:{r['failure_reason']}": int(r["count"]) for r in failures}), "Failure taxonomy"),
        _scatter("semantic_functional_refactoring_residual_width_success.png", utility, "residual_width", "interface_compression", "Residual width versus compression"),
        _scatter("semantic_functional_refactoring_window_size_success.png", utility, "original_node_count", "area_delta", "Original window size versus area delta"),
        _scatter("semantic_functional_refactoring_semantic_width_compression.png", utility, "semantic_width", "interface_compression", "Semantic width versus interface compression"),
        _scatter("semantic_functional_refactoring_area_delta.png", utility, "original_node_count", "refactored_node_count", "Original versus refactored node count"),
        _counter("semantic_functional_refactoring_quotient_complexity.png", Counter({r["benchmark"]: int(r["rows"]) for r in quotient}), "Quotient rows by controlled case"),
        _bar("semantic_functional_refactoring_counterexample_repairs.png", ["counterexamples", "repair transitions"], [len(_read("counterexamples.csv")), len(_read("repair_transitions.csv"))], "Counterexamples and repairs"),
        _baseline("semantic_functional_refactoring_baseline_comparison.png", baselines),
        _bar("semantic_functional_refactoring_controlled_vs_real.png", ["controlled restored", "dev real restored", "heldout real restored"], [_count(controlled, "restored_boundary", "true"), sum(int(r["restored_boundaries"]) for r in heldout if r["split"] == "dev"), sum(int(r["restored_boundaries"]) for r in heldout if r["split"] == "heldout")], "Controlled versus real result"),
        _counter("semantic_functional_refactoring_budget.png", Counter({r["stage"]: float(r["total_runtime_seconds"]) for r in runtime}), "Runtime by stage"),
        _bar("semantic_functional_refactoring_real_split.png", [r["split"] for r in heldout], [int(r["attempted"]) for r in heldout], "Real dev/held-out attempts"),
        _bar("semantic_functional_refactoring_ablation.png", [r["ablation"] for r in ablations], [int(r["restored_boundaries"]) for r in ablations], "Ablation restored boundaries"),
    ]
    for path in paths:
        shutil.copy2(path, PRESENTATION / path.name)
    print(f"Generated {len(paths)} semantic functional refactoring plots")
    return 0


def _read(name: str) -> list[dict[str, str]]:
    path = OUT / name
    return list(csv.DictReader(path.open())) if path.exists() else []


def _count(rows: list[dict[str, str]], key: str, value: str) -> int:
    return sum(1 for row in rows if row.get(key) == value)


def _bar(name: str, labels: list[str], values: list[int | float], title: str) -> Path:
    fig, ax = plt.subplots(figsize=(8.2, 4.5))
    ax.bar(labels, values, color="#3f6f7f")
    ax.set_title(title)
    ax.set_ylabel("count")
    ax.tick_params(axis="x", rotation=20)
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    return _save(fig, name)


def _counter(name: str, values: Counter, title: str) -> Path:
    items = sorted(values.items(), key=lambda kv: (-float(kv[1]), kv[0]))[:12] or [("none", 0)]
    labels, counts = zip(*items)
    fig, ax = plt.subplots(figsize=(8.5, 4.8))
    ax.barh(range(len(labels)), counts, color="#7b8f45")
    ax.set_yticks(range(len(labels)), labels)
    ax.invert_yaxis()
    ax.set_title(title)
    ax.set_xlabel("count")
    ax.grid(axis="x", alpha=0.25)
    fig.tight_layout()
    return _save(fig, name)


def _scatter(name: str, rows: list[dict[str, str]], x: str, y: str, title: str) -> Path:
    fig, ax = plt.subplots(figsize=(6.2, 4.2))
    ax.scatter([float(r[x]) for r in rows], [float(r[y]) for r in rows], color="#8b5f83")
    ax.set_title(title)
    ax.set_xlabel(x.replace("_", " "))
    ax.set_ylabel(y.replace("_", " "))
    ax.grid(alpha=0.25)
    fig.tight_layout()
    return _save(fig, name)


def _baseline(name: str, rows: list[dict[str, str]]) -> Path:
    labels = [r["baseline"] for r in rows]
    restored = [int(r["restored_boundaries"]) for r in rows]
    return _bar(name, labels, restored, "Baseline comparison")


def _save(fig, name: str) -> Path:
    path = PLOTS / name
    fig.savefig(path, dpi=180)
    plt.close(fig)
    return path


if __name__ == "__main__":
    raise SystemExit(main())
