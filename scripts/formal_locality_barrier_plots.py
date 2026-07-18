#!/usr/bin/env python3
"""Generate plots for formal locality-barrier certificate results."""

from __future__ import annotations

import csv
import shutil
from collections import Counter
from pathlib import Path

import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "formal_locality_barriers"
PLOTS = ROOT / "results" / "plots"
ASSETS = ROOT / "docs" / "presentation" / "assets" / "plots"


def main() -> int:
    PLOTS.mkdir(parents=True, exist_ok=True)
    ASSETS.mkdir(parents=True, exist_ok=True)
    dev = _read("development_results.csv")
    exact = _read("input_exact_minimum_certificates.csv")
    lower = _read("input_lower_bound_certificates.csv")
    iters = _read("input_hitting_set_iterations.csv")
    output = _read("output_interface_candidates.csv")
    utility = _read("target_utility_proofs.csv")
    transplants = _read("certificate_guided_transplant_attempts.csv")
    paths = [
        _plot_classification(dev),
        _plot_input_widths(exact, lower),
        _plot_failure_groups(dev),
        _plot_iterations(iters),
        _plot_output_widths(output),
        _plot_utility(utility),
        _plot_transplant_funnel(transplants),
        _plot_runtime(iters),
    ]
    for path in paths:
        shutil.copy2(path, ASSETS / path.name)
    print(f"Generated {len(paths)} formal locality-barrier plots")
    return 0


def _read(name: str) -> list[dict[str, str]]:
    path = OUT / name
    if not path.exists():
        return []
    return list(csv.DictReader(path.open(newline="", encoding="utf-8")))


def _save(name: str) -> Path:
    path = PLOTS / f"formal_locality_{name}.png"
    plt.tight_layout()
    plt.savefig(path, dpi=180)
    plt.close()
    return path


def _bar(title: str, labels: list[str], values: list[float], ylabel: str, name: str) -> Path:
    plt.figure(figsize=(8, 4.8))
    plt.bar(labels, values, color="#246b76")
    plt.title(title)
    plt.ylabel(ylabel)
    plt.xticks(rotation=25, ha="right")
    return _save(name)


def _plot_classification(rows):
    counts = Counter(r["strongest_classification"] for r in rows)
    return _bar("Formal locality classifications for previous failures", list(counts), list(counts.values()), "Targets", "classification")


def _plot_input_widths(exact, lower):
    counts = Counter()
    for row in exact:
        counts[f"exact {row['best_upper_bound']}"] += 1
    for row in lower:
        if row["proved_lower_bound"] and row["proved_lower_bound"] != "0":
            counts[f"lb {row['proved_lower_bound']}"] += 1
    return _bar("Input minima and lower bounds", list(counts), list(counts.values()), "Certificates", "input_widths")


def _plot_failure_groups(rows):
    counts = Counter(r["failure_group"] for r in rows)
    return _bar("36 input versus 20 output failure rows", list(counts), list(counts.values()), "Rows", "failure_groups")


def _plot_iterations(rows):
    by_target = Counter(r["target_id"] for r in rows)
    counts = Counter(min(5, v) for v in by_target.values())
    return _bar("Hitting-set iterations per certificate", [str(k) for k in counts], list(counts.values()), "Certificates", "iterations")


def _plot_output_widths(rows):
    counts = Counter(r["classification"] for r in rows)
    return _bar("Output-interface candidate outcomes", list(counts), list(counts.values()), "Candidates", "output_interface")


def _plot_utility(rows):
    counts = Counter(r["target_influence_status"] for r in rows)
    return _bar("Target utility proofs", list(counts), list(counts.values()), "Interfaces", "target_utility")


def _plot_transplant_funnel(rows):
    counts = Counter(r["attempt_status"] for r in rows)
    return _bar("Certificate-guided transplant funnel", list(counts), list(counts.values()), "Targets", "transplant_funnel")


def _plot_runtime(rows):
    buckets = Counter()
    for row in rows:
        rt = float(row["runtime_s"] or 0.0)
        if rt < 0.001:
            buckets["<1ms"] += 1
        elif rt < 0.01:
            buckets["1-10ms"] += 1
        elif rt < 0.1:
            buckets["10-100ms"] += 1
        else:
            buckets[">=100ms"] += 1
    return _bar("Sufficiency query runtime", list(buckets), list(buckets.values()), "Queries", "runtime")


if __name__ == "__main__":
    raise SystemExit(main())
