#!/usr/bin/env python3
"""Generate plots for joint region/interface discovery results."""

from __future__ import annotations

import csv
import shutil
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "joint_region_interface_discovery"
PLOTS = ROOT / "results" / "plots"
PRESENTATION = ROOT / "docs" / "presentation" / "assets" / "plots"


def main() -> int:
    PLOTS.mkdir(parents=True, exist_ok=True)
    PRESENTATION.mkdir(parents=True, exist_ok=True)
    controlled = _read("controlled_benchmark_results.csv")
    real = _read("real_benchmark_results.csv")
    candidates = _read("candidate_state_summary.csv")
    transitions = _read("search_transitions.csv")
    proofs = _read("proof_results.csv")
    boundary = _read("boundary_restoration_results.csv")
    failures = _read("failure_taxonomy.csv")
    baseline = _read("baseline_comparison.csv")
    ablations = _read("ablations.csv")
    runtimes = _read("runtime_timeout_summary.csv")

    paths = [
        _bar("joint_region_interface_funnel.png", ["controlled", "verified", "graph-active", "restored"], [len(controlled), _count(controlled, "verified_module", "true"), _count(controlled, "graph_active_replacement", "true"), _count(controlled, "restored_boundary", "true")], "Controlled proof-carrying replacement funnel"),
        _counter_bar("joint_region_interface_failure_taxonomy.png", Counter(f"{r['benchmark_group']}:{r['failure_reason']}" for r in failures for _ in range(int(r["count"]))), "Failure taxonomy"),
        _bar("joint_region_interface_budget.png", ["states", "transitions", "diagnosed repairs"], [len(candidates), len(transitions), sum(1 for t in transitions if t["counterexample_id"])], "Bounded search work"),
        _scatter_region("joint_region_interface_region_size_cut_width.png", candidates),
        _scatter_proof("joint_region_interface_complexity_proof.png", proofs, candidates),
        _counter_bar("joint_region_interface_runtime.png", Counter({r["stage"]: float(r["total_runtime_seconds"]) for r in runtimes}), "Runtime by stage"),
        _counter_bar("joint_region_interface_counterexamples.png", Counter(t["operation"] for t in transitions if t["counterexample_id"]), "Counterexample-guided repairs"),
        _baseline_plot("joint_region_interface_baseline_comparison.png", baseline),
        _counter_bar("joint_region_interface_seed_family.png", Counter(c["seed_id"].split("__")[0] for c in candidates), "Seed families"),
        _counter_bar("joint_region_interface_grammar_tier.png", Counter(r["formal_evidence_level"] for r in proofs), "Proof evidence levels"),
        _bar("joint_region_interface_controlled_vs_real.png", ["controlled restored", "real restored", "real revisited"], [_count(controlled, "restored_boundary", "true"), 0, len(real)], "Controlled versus real benchmark outcome"),
        _trace_plot("joint_region_interface_trace_evolution.png", candidates),
        _bar("joint_region_interface_restored_boundaries.png", ["restored", "not restored"], [_count(boundary, "newly_recovered_boundary", "true"), len(boundary) - _count(boundary, "newly_recovered_boundary", "true")], "Restored boundaries"),
        _bar("joint_region_interface_ablation.png", [r["ablation"] for r in ablations], [int(r["restored_boundaries"]) for r in ablations], "Replacement ablation"),
    ]
    for path in paths:
        shutil.copy2(path, PRESENTATION / path.name)
    print(f"Generated {len(paths)} joint region/interface plots")
    return 0


def _read(name: str) -> list[dict[str, str]]:
    path = OUT / name
    return list(csv.DictReader(path.open())) if path.exists() else []


def _count(rows: list[dict[str, str]], key: str, value: str) -> int:
    return sum(1 for row in rows if row.get(key) == value)


def _bar(name: str, labels: list[str], values: list[int | float], title: str) -> Path:
    fig, ax = plt.subplots(figsize=(7.0, 4.2))
    ax.bar(labels, values, color=["#315f72", "#789d4a", "#b46b39", "#6d5a8d"][: len(labels)])
    ax.set_title(title)
    ax.set_ylabel("count")
    ax.tick_params(axis="x", rotation=20)
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    path = PLOTS / name
    fig.savefig(path, dpi=180)
    plt.close(fig)
    return path


def _counter_bar(name: str, counter: Counter, title: str) -> Path:
    items = sorted(counter.items(), key=lambda kv: (-float(kv[1]), kv[0]))[:12] or [("none", 0)]
    labels, values = zip(*items)
    fig, ax = plt.subplots(figsize=(8.5, 4.8))
    ax.barh(range(len(labels)), values, color="#466a83")
    ax.set_yticks(range(len(labels)), labels)
    ax.invert_yaxis()
    ax.set_title(title)
    ax.set_xlabel("count")
    ax.grid(axis="x", alpha=0.25)
    fig.tight_layout()
    path = PLOTS / name
    fig.savefig(path, dpi=180)
    plt.close(fig)
    return path


def _scatter_region(name: str, candidates: list[dict[str, str]]) -> Path:
    xs, ys = [], []
    for row in candidates:
        xs.append(_json_len(row.get("implementation_nodes", "[]")))
        ys.append(_json_len(row.get("input_cut", "[]")))
    fig, ax = plt.subplots(figsize=(6.2, 4.2))
    ax.scatter(xs, ys, color="#315f72")
    ax.set_title("Region size versus input-cut width")
    ax.set_xlabel("implementation nodes")
    ax.set_ylabel("input cut bits")
    ax.grid(alpha=0.25)
    fig.tight_layout()
    path = PLOTS / name
    fig.savefig(path, dpi=180)
    plt.close(fig)
    return path


def _scatter_proof(name: str, proofs: list[dict[str, str]], candidates: list[dict[str, str]]) -> Path:
    by_candidate = {row["candidate_id"]: row for row in candidates}
    xs, ys = [], []
    for row in proofs:
        cand = by_candidate.get(row["candidate_id"], {})
        xs.append(_json_len(cand.get("implementation_nodes", "[]")))
        ys.append(float(row.get("runtime_seconds", "0") or 0))
    fig, ax = plt.subplots(figsize=(6.2, 4.2))
    ax.scatter(xs, ys, color="#789d4a")
    ax.set_title("Proof runtime versus region size")
    ax.set_xlabel("implementation nodes")
    ax.set_ylabel("seconds")
    ax.grid(alpha=0.25)
    fig.tight_layout()
    path = PLOTS / name
    fig.savefig(path, dpi=180)
    plt.close(fig)
    return path


def _baseline_plot(name: str, rows: list[dict[str, str]]) -> Path:
    labels = [r["baseline"] for r in rows]
    restored = [int(r["restored_boundaries"]) for r in rows]
    fig, ax = plt.subplots(figsize=(8.0, 4.4))
    ax.bar(labels, restored, color="#6d5a8d")
    ax.set_title("Isolated anchors versus joint region replacement")
    ax.set_ylabel("restored boundaries")
    ax.tick_params(axis="x", rotation=20)
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    path = PLOTS / name
    fig.savefig(path, dpi=180)
    plt.close(fig)
    return path


def _trace_plot(name: str, candidates: list[dict[str, str]]) -> Path:
    counts: dict[str, int] = defaultdict(int)
    for row in candidates:
        counts[row["iteration"]] += 1
    labels = sorted(counts, key=lambda item: int(item))
    return _bar(name, labels, [counts[label] for label in labels], "Candidate states by search iteration")


def _json_len(text: str) -> int:
    import json

    try:
        return len(json.loads(text))
    except Exception:
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
