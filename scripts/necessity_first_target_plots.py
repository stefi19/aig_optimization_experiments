#!/usr/bin/env python3
"""Generate plots for provenance and necessity-first target discovery."""

from __future__ import annotations

import csv
import shutil
from collections import Counter
from pathlib import Path

import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "results" / "provenance_eligibility_audit"
RESULTS = ROOT / "results" / "necessity_first_target_discovery"
PLOTS = ROOT / "results" / "plots"
ASSETS = ROOT / "docs" / "presentation" / "assets" / "plots"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def bar(counter: Counter, title: str, ylabel: str, filename: str) -> None:
    PLOTS.mkdir(parents=True, exist_ok=True)
    labels = list(counter.keys())
    values = [counter[label] for label in labels]
    fig, ax = plt.subplots(figsize=(8, 4.8))
    ax.bar(labels, values, color="#2f6f73")
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    ax.tick_params(axis="x", rotation=25)
    for idx, value in enumerate(values):
        ax.text(idx, value, str(value), ha="center", va="bottom")
    fig.tight_layout()
    out = PLOTS / filename
    fig.savefig(out, dpi=180)
    plt.close(fig)
    ASSETS.mkdir(parents=True, exist_ok=True)
    shutil.copy2(out, ASSETS / filename)


def main() -> int:
    audit = read_csv(AUDIT / "historical_denominator_audit.csv")
    recon = read_csv(AUDIT / "provenance_reconstruction.csv")
    candidates = read_csv(RESULTS / "raw_target_candidates.csv")
    eligible = read_csv(RESULTS / "eligible_target_manifest.csv")
    forced = read_csv(RESULTS / "forced_observability_proofs.csv")
    necessity = read_csv(RESULTS / "reachable_necessity_proofs.csv")
    locality = read_csv(RESULTS / "formal_locality_results.csv")
    rewrites = read_csv(RESULTS / "graph_rewrites.csv")
    datasets = read_csv(RESULTS / "dataset_classification.csv")
    taxonomy = read_csv(RESULTS / "failure_taxonomy.csv")

    bar(Counter(r["current_eligibility"] for r in audit), "Corrected historical eligibility", "Rows", "necessity_historical_eligibility.png")
    bar(Counter(r["reconstruction_status"] for r in recon), "Historical provenance reconstruction", "Rows", "necessity_provenance_reconstruction.png")
    funnel = Counter(
        {
            "raw": len(candidates),
            "forced": sum(r["status"] == "forced_observable" for r in forced),
            "necessary": sum(r["status"] == "reachable_necessary" for r in necessity),
            "eligible": sum(r["eligibility_status"] == "eligible_target_necessary" for r in eligible),
            "compact": sum(r["compact_interface"] == "true" for r in locality),
            "rewrites": sum(r["rewrite_emitted"] == "true" for r in rewrites),
        }
    )
    bar(funnel, "Necessity-first target funnel", "Targets", "necessity_target_funnel.png")
    bar(Counter(r["status"] for r in forced), "Forced-value observability", "Targets", "necessity_forced_observability.png")
    bar(Counter(r["status"] for r in necessity), "Reachable target necessity", "Targets", "necessity_reachable_dependence.png")
    bar(Counter(r["dataset_class"] for r in datasets), "Benchmark dataset classes", "Design groups", "necessity_dataset_classes.png")
    bar(Counter(r["compact_interface"] for r in locality), "Locality on eligible targets", "Targets", "necessity_locality_results.png")
    bar(Counter({r["category"]: int(r["count"]) for r in taxonomy}), "Necessity-first taxonomy", "Count", "necessity_failure_taxonomy.png")
    print("Generated necessity-first target plots")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
