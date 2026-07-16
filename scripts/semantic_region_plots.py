#!/usr/bin/env python3
"""Generate compact plots for semantic-region/interface Phase 2 outputs."""

from __future__ import annotations

import csv
import json
import shutil
import sys
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
RESULT = ROOT / "results" / "semantic_recovery"
PLOT_DIR = ROOT / "results" / "plots"
ASSET_DIR = ROOT / "docs" / "presentation" / "assets" / "plots"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def save(fig, name: str) -> None:
    PLOT_DIR.mkdir(parents=True, exist_ok=True)
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    path = PLOT_DIR / name
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    shutil.copyfile(path, ASSET_DIR / name)


def bar(counter: dict[str, int], title: str, ylabel: str, name: str) -> None:
    fig, ax = plt.subplots(figsize=(8, 4.5))
    keys = list(counter)
    ax.bar(keys, [counter[k] for k in keys], color="#4c78a8")
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    ax.tick_params(axis="x", rotation=30)
    save(fig, name)


def main() -> int:
    regions = read_csv(RESULT / "semantic_regions.csv")
    align = read_csv(RESULT / "semantic_interface_alignment.csv")
    comp = read_csv(RESULT / "semantic_region_source_comparison.csv")
    validation = {r["region_id"]: r for r in read_csv(RESULT / "semantic_region_validation.csv")}
    eligible = [r for r in regions if r["eligible"] == "true"]

    bar(dict(Counter(r["status"] for r in regions)), "Semantic region pipeline funnel", "Rows", "semantic_region_pipeline_funnel.png")
    bar(dict(Counter(r["family"] for r in eligible)), "Valid semantic regions by family", "Valid rows", "semantic_valid_regions_by_family.png")
    op_sizes: dict[str, list[int]] = defaultdict(list)
    for r in eligible:
        op_sizes[r["operator"]].append(len(json.loads(r["region_nodes"])))
    bar({k: int(sum(v) / len(v)) for k, v in sorted(op_sizes.items())[:25]}, "Mean region size by operator", "Nodes", "semantic_region_size_by_operator.png")

    fig, ax = plt.subplots(figsize=(6, 5))
    ax.scatter([int(r["ground_truth_region_nodes"]) for r in comp], [int(r["output_cone_region_nodes"]) for r in comp], s=24, alpha=0.7)
    ax.set_title("Ground-truth region vs output-cone size")
    ax.set_xlabel("Ground-truth region nodes")
    ax.set_ylabel("Output-cone region nodes")
    save(fig, "semantic_gt_vs_output_cone_size.png")

    fig, ax = plt.subplots(figsize=(7, 4))
    ax.hist([float(r["jaccard_similarity"]) for r in comp], bins=10, color="#59a14f")
    ax.set_title("Region overlap distribution")
    ax.set_xlabel("Jaccard similarity")
    ax.set_ylabel("Rows")
    save(fig, "semantic_region_overlap_distribution.png")

    match_by_family: dict[str, list[int]] = defaultdict(list)
    family_by_region = {r["region_id"]: r["family"] for r in regions}
    for r in align:
        match_by_family[family_by_region.get(r["region_id"], "unknown")].append(1 if r["exact_scalar_interface_match"] == "true" else 0)
    bar({k: int(100 * sum(v) / max(1, len(v))) for k, v in sorted(match_by_family.items())}, "Exact scalar-interface match by family", "Percent", "semantic_exact_interface_match_by_family.png")

    by_opt: dict[str, list[int]] = defaultdict(list)
    opt_by_region = {r["region_id"]: r["optimization"] for r in regions}
    for r in align:
        by_opt[opt_by_region.get(r["region_id"], "unknown")].append(1 if r["exact_scalar_interface_match"] == "true" else 0)
    bar({k: int(100 * sum(v) / max(1, len(v))) for k, v in sorted(by_opt.items())}, "Interface extraction by optimization", "Exact match percent", "semantic_interface_by_optimization.png")

    cone_rows = [r for r in eligible if r["source_type"] == "whole_output_cone"]
    whole_by_opt: dict[str, list[int]] = defaultdict(list)
    for r in cone_rows:
        whole_by_opt[r["optimization"]].append(1 if validation.get(r["region_id"], {}).get("whole_design_region") == "true" else 0)
    bar({k: int(100 * sum(v) / max(1, len(v))) for k, v in sorted(whole_by_opt.items())}, "Whole-design output-cone rate", "Percent", "semantic_whole_design_output_cone_rate.png")

    fig, ax = plt.subplots(figsize=(7, 4))
    ax.hist([len(json.loads(r["boundary_inputs"])) for r in eligible], alpha=0.7, label="BI")
    ax.hist([len(json.loads(r["boundary_outputs"])) for r in eligible], alpha=0.7, label="BO")
    ax.set_title("Boundary input/output counts")
    ax.set_xlabel("Count")
    ax.set_ylabel("Rows")
    ax.legend()
    save(fig, "semantic_boundary_io_counts.png")

    failures = [r for r in regions if r["eligible"] != "true"]
    bar(dict(Counter(r["status"] for r in failures)), "Semantic region failures and skips", "Rows", "semantic_region_failures_and_skips.png")
    print("Semantic region plots written to results/plots/semantic_* and presentation assets")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
