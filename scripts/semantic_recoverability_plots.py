#!/usr/bin/env python3
"""Generate plots for the semantic recoverability frontier experiment."""

from __future__ import annotations

import csv
import shutil
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "semantic_recoverability_frontier"
PLOTS = ROOT / "results" / "plots"
ASSETS = ROOT / "docs" / "presentation" / "assets" / "plots"


def main() -> int:
    PLOTS.mkdir(parents=True, exist_ok=True)
    ASSETS.mkdir(parents=True, exist_ok=True)
    blind = _read("blind_recovery_results.csv")
    oracle = _read("oracle_ladder_results.csv")
    checkpoints = _read("checkpoint_structural_metrics.csv")
    tradeoffs = _read("optimisation_tradeoffs.csv")
    residual = _read("residual_bounds.csv")
    windows = _read("window_locality_results.csv")
    deltas = _read("pass_level_deltas.csv")
    failures = _read("failure_taxonomy.csv")
    frontiers = _read("method_specific_frontiers.csv")
    durability = _read("boundary_durability_results.csv")

    paths = [
        _plot_recovery_by_checkpoint(blind, oracle),
        _plot_blind_oracle(blind, oracle),
        _plot_heatmap(blind),
        _plot_transitions(frontiers),
        _plot_residual(residual),
        _plot_window(windows),
        _plot_area_tradeoff(tradeoffs),
        _plot_depth_tradeoff(tradeoffs),
        _plot_pass_deltas(deltas),
        _plot_pass_ablation(_read("pass_ablations.csv")),
        _plot_durability(durability),
        _plot_structural_vs_semantic(blind),
        _plot_method_comparison(blind, oracle),
        _plot_split_comparison(blind, oracle),
        _plot_failure_taxonomy(failures),
        _plot_runtime(blind + oracle, checkpoints),
        _plot_oracle_gap(blind, oracle),
        _plot_pareto(tradeoffs),
    ]
    for path in paths:
        shutil.copy2(path, ASSETS / path.name)
    print(f"Generated {len(paths)} semantic recoverability frontier plots")
    return 0


def _read(name: str) -> list[dict[str, str]]:
    with (OUT / name).open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _save(name: str) -> Path:
    path = PLOTS / f"semantic_recoverability_{name}.png"
    plt.tight_layout()
    plt.savefig(path, dpi=180)
    plt.close()
    return path


def _bar(title: str, labels: list[str], values: list[float], ylabel: str, name: str) -> Path:
    plt.figure(figsize=(8, 4.8))
    plt.bar(labels, values, color="#287c8e")
    plt.title(title)
    plt.ylabel(ylabel)
    plt.xticks(rotation=25, ha="right")
    return _save(name)


def _plot_recovery_by_checkpoint(blind, oracle):
    counts = defaultdict(lambda: [0, 0])
    for row in blind + oracle:
        key = int(row["checkpoint_index"])
        counts[key][1] += 1
        if row["recovered"] == "true":
            counts[key][0] += 1
    labels = [str(k) for k in sorted(counts)]
    values = [counts[k][0] / counts[k][1] for k in sorted(counts)]
    return _bar("Recoverability level versus checkpoint", labels, values, "Recovered fraction", "frontier_by_checkpoint")


def _plot_blind_oracle(blind, oracle):
    values = [sum(r["recovered"] == "true" for r in blind) / len(blind), sum(r["recovered"] == "true" for r in oracle) / len(oracle)]
    return _bar("Blind versus oracle recovery curves", ["blind", "oracle"], values, "Recovered fraction", "blind_vs_oracle")


def _plot_heatmap(blind):
    matrix = defaultdict(dict)
    for row in blind:
        matrix[row["boundary_id"]][int(row["checkpoint_index"])] = max(matrix[row["boundary_id"]].get(int(row["checkpoint_index"]), 0), int(row["recovered"] == "true"))
    labels = sorted(matrix)
    xs = sorted({x for values in matrix.values() for x in values})
    plt.figure(figsize=(8, 4.8))
    data = [[matrix[label].get(x, 0) for x in xs] for label in labels]
    plt.imshow(data, aspect="auto", cmap="Blues", vmin=0, vmax=1)
    plt.yticks(range(len(labels)), labels, fontsize=7)
    plt.xticks(range(len(xs)), xs)
    plt.title("Recoverability heatmap by boundary and checkpoint")
    plt.xlabel("Checkpoint index")
    return _save("heatmap")


def _plot_transitions(frontiers):
    values = Counter("non_monotonic" if r["non_monotonic"] == "true" else "monotonic_or_single" for r in frontiers)
    return _bar("First-loss and recovery transitions", list(values), list(values.values()), "Boundary/method frontiers", "transitions")


def _plot_residual(residual):
    values = Counter(r["minimum_status"] for r in residual)
    return _bar("Residual width status across trajectories", list(values), list(values.values()), "Rows", "residual_width")


def _plot_window(windows):
    values = Counter(r["classification"] for r in windows)
    return _bar("Minimum/best-known window size", list(values), list(values.values()), "Rows", "window_locality")


def _plot_area_tradeoff(tradeoffs):
    labels = [r["checkpoint_id"].split("__")[-1] for r in tradeoffs[:40]]
    values = [float(r["recoverable_boundary_fraction"]) for r in tradeoffs[:40]]
    return _bar("Optimisation area versus recoverability", labels, values, "Blind recovered fraction", "area_tradeoff")


def _plot_depth_tradeoff(tradeoffs):
    labels = [r["checkpoint_id"].split("__")[-1] for r in tradeoffs[:40]]
    values = [int(r["depth"]) for r in tradeoffs[:40]]
    return _bar("Depth versus recoverability checkpoints", labels, values, "Depth", "depth_tradeoff")


def _plot_pass_deltas(deltas):
    values = Counter(r["pass_name"] for r in deltas if r["transition_class"] != "unchanged")
    return _bar("Pass-level recoverability deltas", list(values), list(values.values()), "Transitions", "pass_deltas")


def _plot_pass_ablation(ablations):
    return _bar("Pass-omission ablations", [r["changed_pass"] for r in ablations], [float(r["recovery_delta"] or 0) for r in ablations], "Associated transitions", "pass_ablations")


def _plot_durability(durability):
    values = Counter(r["boundary_survives_suffix"] for r in durability)
    return _bar("Boundary durability survival curves", list(values), list(values.values()), "Rows", "durability")


def _plot_structural_vs_semantic(blind):
    values = Counter(r["method"] for r in blind if r["recovered"] == "true")
    return _bar("Structural survival versus semantic recoverability", list(values), list(values.values()), "Recovered rows", "structural_vs_semantic")


def _plot_method_comparison(blind, oracle):
    values = Counter(r["method"] for r in blind + oracle if r["recovered"] == "true")
    return _bar("Method comparison", list(values), list(values.values()), "Recovered rows", "method_comparison")


def _plot_split_comparison(blind, oracle):
    values = Counter((r["split"], r["oracle_mode"] == "blind") for r in blind + oracle if r["recovered"] == "true")
    labels = [f"{split}:{'blind' if is_blind else 'oracle'}" for split, is_blind in values]
    return _bar("Controlled versus development versus held-out", labels, list(values.values()), "Recovered rows", "split_comparison")


def _plot_failure_taxonomy(failures):
    labels = [r["failure_reason"] for r in failures]
    values = [int(r["count"]) for r in failures]
    return _bar("Failure taxonomy", labels, values, "Rows", "failure_taxonomy")


def _plot_runtime(rows, checkpoints):
    values = Counter(r["checkpoint_index"] for r in rows if float(r["runtime_s"] or 0) > 0.0)
    return _bar("Proof runtime versus checkpoint complexity", list(values), list(values.values()), "Proof rows", "runtime_complexity")


def _plot_oracle_gap(blind, oracle):
    blind_by_split = Counter(r["split"] for r in blind if r["recovered"] == "true")
    oracle_by_split = Counter(r["split"] for r in oracle if r["recovered"] == "true")
    labels = sorted(set(blind_by_split) | set(oracle_by_split))
    values = [oracle_by_split[label] - blind_by_split[label] for label in labels]
    return _bar("Blind-oracle gap decomposition", labels, values, "Oracle minus blind recovered rows", "oracle_gap")


def _plot_pareto(tradeoffs):
    plt.figure(figsize=(7, 4.8))
    x = [int(r["node_count"]) for r in tradeoffs]
    y = [float(r["oracle_recoverable_fraction"]) for r in tradeoffs]
    plt.scatter(x, y, color="#287c8e")
    plt.title("Pareto frontier: optimisation quality and semantic recoverability")
    plt.xlabel("Node count")
    plt.ylabel("Oracle recovered fraction")
    return _save("pareto")


if __name__ == "__main__":
    raise SystemExit(main())
