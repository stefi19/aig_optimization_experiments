#!/usr/bin/env python3
"""Generate active source-counterpart plots from committed CSVs."""

from __future__ import annotations

import csv
import shutil
from collections import Counter
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "active_source_counterpart_refactoring"
PLOTS = ROOT / "results" / "plots"
PRESENTATION = ROOT / "docs" / "presentation" / "assets" / "plots"


def main() -> int:
    PLOTS.mkdir(parents=True, exist_ok=True)
    PRESENTATION.mkdir(parents=True, exist_ok=True)
    controlled = _read("controlled_results.csv")
    development = _read("development_results.csv")
    targets = _read("target_candidates.csv")
    counterpart = _read("counterpart_proofs.csv")
    decomp = _read("decomposition_queries.csv")
    quotient = _read("quotient_synthesis.csv")
    graph = _read("graph_validation.csv")
    cec = _read("global_cec.csv")
    boundary = _read("boundary_recovery.csv")
    failures = _read("failure_taxonomy.csv")
    durability = _read("durability_trajectories.csv")
    preservation = _read("preservation_strategies.csv")
    gf2 = _read("gf2_linear_baseline.csv")
    ablations = _read("ablations.csv")
    baselines = _read("baselines.csv")
    runtime = _read("runtime_timeout_summary.csv")

    paths = [
        _bar("active_source_counterpart_funnel.png", ["targets", "counterparts", "decomp", "quotient", "active", "CEC", "usable", "boundary"], [len(targets), _count(counterpart, "formal_status", "proven_counterpart_equivalent"), _count(decomp, "formal_status", "decomposable"), _count(quotient, "quotient_status", "synthesized_truth_table"), _count(graph, "graph_active", "true"), sum(r["cec_status"] == "equivalent" and r["cec_scope"] == "S_vs_Sprime" for r in cec), _count(boundary, "usable_frontier_anchor", "true"), _count(boundary, "new_recovered_boundary", "true")], "Additive-to-active source construction funnel"),
        _counter("active_source_target_selection.png", Counter(r["target_origin"] for r in targets), "Target sources"),
        _counter("active_source_counterpart_backend.png", Counter(r["backend"] for r in _read("counterpart_synthesis.csv") if r["synthesis_status"] == "generated"), "Counterpart backends used"),
        _counter("active_source_decomposition_status.png", Counter(r["formal_status"] for r in decomp), "Source-window decomposition status"),
        _scatter("active_source_window_size_success.png", _read("source_window_candidates.csv"), "window_size", "selected", "Source-window size and selection"),
        _scatter("active_source_residual_width_success.png", _read("counterpart_candidates.csv"), "residual_interface", "source_window_outputs", "Residual interface and output width"),
        _counter("active_source_failure_taxonomy.png", Counter({f"{r['benchmark_group']}:{r['failure_reason']}": int(r["count"]) for r in failures}), "Failure taxonomy"),
        _bar("active_source_adaptation_cost.png", ["active rewrites", "source CEC", "cross CEC"], [_count(graph, "graph_active", "true"), sum(r["cec_status"] == "equivalent" and r["cec_scope"] == "S_vs_Sprime" for r in cec), sum(r["cec_status"] == "equivalent" and r["cec_scope"] == "Sprime_vs_I" for r in cec)], "Formal source adaptation proof stack"),
        _bar("active_source_boundary_utility.png", ["usable anchors", "selected anchors", "new boundaries", "critical paths"], [_count(boundary, "usable_frontier_anchor", "true"), _count(boundary, "selected_anchor", "true"), _count(boundary, "new_recovered_boundary", "true"), _count(_read("critical_path_utility.csv"), "newly_resolved_critical_path_target", "true")], "Boundary and critical-path utility"),
        _baseline("active_source_old_vs_active.png", baselines),
        _bar("active_source_source_vs_optimized_refactoring.png", [r["baseline"] + ":" + r["benchmark_group"] for r in baselines if "refactoring" in r["baseline"]], [int(r["new_boundaries"]) for r in baselines if "refactoring" in r["baseline"]], "Source-side versus optimized-side refactoring"),
        _counter("active_source_durability_survival.png", Counter({r["strategy"]: int(r["usable_boundary"]) for r in preservation}), "Durability by strategy"),
        _scatter("active_source_area_depth_durability.png", preservation, "mean_area_delta", "usable_boundary", "Area overhead versus durable usability"),
        _bar("active_source_gf2_vs_general.png", ["GF2 affine", "GF2 nonlinear rejected", "general nonlinear accepted"], [_count(gf2, "status", "exact_affine_solution"), _count(gf2, "status", "rejected_nonlinear"), sum(r["final_status"] == "accepted" and r["family"] in {"bilinear", "mac", "mask"} for r in controlled)], "GF(2) baseline versus general decomposition"),
        _bar("active_source_controlled_development_heldout.png", ["controlled accepted", "development real", "held-out real"], [sum(r["final_status"] == "accepted" for r in controlled), sum(r["split"] == "dev" and r["new_recovered_boundary"] == "true" for r in development), sum(r["split"] == "heldout" and r["new_recovered_boundary"] == "true" for r in development)], "Controlled versus development versus held-out"),
        _bar("active_source_ablation_boundaries.png", [r["ablation"] for r in ablations], [int(r["new_boundaries"]) for r in ablations], "Ablation new boundaries"),
        _counter("active_source_runtime.png", Counter({r["stage"]: float(r["total_runtime_seconds"]) for r in runtime}), "Runtime by stage"),
    ]
    for path in paths:
        shutil.copy2(path, PRESENTATION / path.name)
    print(f"Generated {len(paths)} active source-counterpart plots")
    return 0


def _read(name: str) -> list[dict[str, str]]:
    path = OUT / name
    return list(csv.DictReader(path.open())) if path.exists() else []


def _count(rows: list[dict[str, str]], key: str, value: str) -> int:
    return sum(row.get(key) == value for row in rows)


def _bar(name: str, labels: list[str], values: list[int | float], title: str) -> Path:
    fig, ax = plt.subplots(figsize=(8.4, 4.6))
    ax.bar(labels, values, color="#416f73")
    ax.set_title(title)
    ax.set_ylabel("count")
    ax.tick_params(axis="x", rotation=22)
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    return _save(fig, name)


def _counter(name: str, values: Counter, title: str) -> Path:
    items = sorted(values.items(), key=lambda kv: (-float(kv[1]), str(kv[0])))[:14] or [("none", 0)]
    labels, counts = zip(*items)
    fig, ax = plt.subplots(figsize=(8.8, 4.9))
    ax.barh(range(len(labels)), counts, color="#7a7741")
    ax.set_yticks(range(len(labels)), labels)
    ax.invert_yaxis()
    ax.set_title(title)
    ax.set_xlabel("count")
    ax.grid(axis="x", alpha=0.25)
    fig.tight_layout()
    return _save(fig, name)


def _scatter(name: str, rows: list[dict[str, str]], x: str, y: str, title: str) -> Path:
    xs = [_numeric_width(r.get(x, "")) for r in rows]
    ys = [_numeric_width(r.get(y, "")) for r in rows]
    fig, ax = plt.subplots(figsize=(6.4, 4.2))
    ax.scatter(xs, ys, color="#8b5f83")
    ax.set_title(title)
    ax.set_xlabel(x.replace("_", " "))
    ax.set_ylabel(y.replace("_", " "))
    ax.grid(alpha=0.25)
    fig.tight_layout()
    return _save(fig, name)


def _baseline(name: str, rows: list[dict[str, str]]) -> Path:
    labels = [r["baseline"] + ":" + r["benchmark_group"] for r in rows]
    values = [int(r["new_boundaries"]) for r in rows]
    return _bar(name, labels, values, "Old additive versus active source refactoring")


def _numeric_width(value: str) -> float:
    if value in {"true", "false"}:
        return 1.0 if value == "true" else 0.0
    try:
        return float(value)
    except ValueError:
        if value.startswith("["):
            try:
                import json

                return float(len(json.loads(value)))
            except Exception:
                return 0.0
        return 0.0


def _save(fig, name: str) -> Path:
    path = PLOTS / name
    fig.savefig(path, dpi=180)
    plt.close(fig)
    return path


if __name__ == "__main__":
    raise SystemExit(main())
