#!/usr/bin/env python3
"""Generate plots for direct semantic template recovery."""

from __future__ import annotations

import csv
import shutil
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


def bar(labels, values, title, ylabel, name, color="#4c78a8"):
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.bar(labels, values, color=color)
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    ax.tick_params(axis="x", rotation=30)
    save(fig, name)


def main() -> int:
    summary = read_csv(RESULT / "semantic_ground_truth_recovery.csv")
    overall = next(row for row in summary if row["scope"] == "overall")
    by_family = [row for row in summary if row["scope"] == "family"]
    by_operator = [row for row in summary if row["scope"] == "operator"]
    by_opt = [row for row in summary if row["scope"] == "optimization"]
    by_source = [row for row in summary if row["scope"] == "source_type"]
    candidates = read_csv(RESULT / "semantic_direct_candidates.csv")
    sim = read_csv(RESULT / "semantic_candidate_simulation.csv")
    formal = read_csv(RESULT / "semantic_formal_results.csv")
    verified = read_csv(RESULT / "semantic_verified_candidates.csv")
    failures = read_csv(RESULT / "semantic_direct_failure_analysis.csv")
    dep_ablation = read_csv(RESULT / "semantic_dependency_ranking_ablation.csv")
    sim_ablation = read_csv(RESULT / "semantic_simulation_filter_ablation.csv")

    bar(["eligible", "candidates", "sim survivors", "formal", "verified", "recovered"], [int(overall["eligible_regions"]), int(overall["generated_candidates"]), int(overall["simulation_survivors"]), int(overall["formal_checks"]), int(overall["verified_candidates"]), int(overall["recovered_regions"])], "Direct recovery candidate funnel", "Count", "semantic_direct_candidate_funnel.png")
    bar([row["group"] for row in by_family], [float(row["formal_recovery_rate"]) for row in by_family], "Formal recovery by family", "Recovery rate", "semantic_direct_recovery_by_family.png", "#59a14f")
    class_counts = Counter(row["classification"] for row in verified)
    bar(list(class_counts), list(class_counts.values()), "Exact vs equivalent verified expressions", "Candidates", "semantic_direct_exact_vs_alternative.png", "#f28e2b")
    bar([row["group"] for row in by_operator[:30]], [float(row["formal_recovery_rate"]) for row in by_operator[:30]], "Direct recovery by operator", "Recovery rate", "semantic_direct_recovery_by_operator.png")
    bar([row["group"] for row in by_opt], [float(row["formal_recovery_rate"]) for row in by_opt], "Direct recovery by optimization", "Recovery rate", "semantic_direct_recovery_by_optimization.png")
    widths: dict[str, list[str]] = defaultdict(list)
    for row in verified:
        width = row["case_id"].rsplit("_w", 1)[-1] if "_w" in row["case_id"] else "unknown"
        widths[width].append(row["region_id"])
    bar(sorted(widths, key=lambda x: int(x) if x.isdigit() else 0), [len(set(widths[k])) for k in sorted(widths, key=lambda x: int(x) if x.isdigit() else 0)], "Recovered regions by width", "Regions", "semantic_direct_recovery_by_width.png")
    signed: dict[str, set[str]] = defaultdict(set)
    for row in verified:
        signed["signed" if "signed" in row["operator"] else "unsigned_or_untyped"].add(row["region_id"])
    bar(list(signed), [len(v) for v in signed.values()], "Recovered regions by signedness class", "Regions", "semantic_direct_recovery_by_signedness.png")
    by_region_counts = Counter(row["region_id"] for row in candidates)
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.hist(list(by_region_counts.values()), bins=20, color="#76b7b2")
    ax.set_title("Candidate count distribution")
    ax.set_xlabel("Candidates per region")
    ax.set_ylabel("Regions")
    save(fig, "semantic_direct_candidate_count_distribution.png")
    calls = Counter(row["region_id"] for row in formal)
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.hist(list(calls.values()), bins=12, color="#b07aa1")
    ax.set_title("Formal calls per recovered search")
    ax.set_xlabel("Formal calls per region")
    ax.set_ylabel("Regions")
    save(fig, "semantic_direct_formal_calls_per_recovery.png")
    bar([row["family_order_mode"] for row in dep_ablation], [float(row["formal_recovery_rate"]) for row in dep_ablation], "Dependency-ranked versus fixed ordering", "Recovery rate", "semantic_direct_dependency_ordering_ablation.png")
    bar([row["simulation_filter_mode"] for row in sim_ablation], [float(row["formal_calls"]) for row in sim_ablation], "Simulation-filter ablation", "Formal calls", "semantic_direct_simulation_filter_ablation.png")
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.hist([float(row["candidate_rtl_cost"]) for row in verified], bins=12, color="#9c755f")
    ax.set_title("Problem-A-inspired RTL cost distribution")
    ax.set_xlabel("Cost")
    ax.set_ylabel("Verified candidates")
    save(fig, "semantic_direct_rtl_cost_distribution.png")
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.hist([float(row["reduction_rate"]) for row in verified], bins=12, color="#edc948")
    ax.set_title("Problem-A-inspired reduction-rate distribution")
    ax.set_xlabel("Reduction rate (%)")
    ax.set_ylabel("Verified candidates")
    save(fig, "semantic_direct_reduction_rate_distribution.png")
    bar([row["group"] for row in by_source], [float(row["formal_recovery_rate"]) for row in by_source], "Ground-truth region versus output cone", "Recovery rate", "semantic_direct_gt_vs_output_cone.png")
    failure_counts = Counter(row["failure_reason"] for row in failures)
    bar(list(failure_counts) or ["none"], list(failure_counts.values()) or [0], "Direct recovery failure taxonomy", "Rows", "semantic_direct_failure_taxonomy.png")
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.scatter([int(Counter(row["region_id"] for row in candidates)[row["region_id"]]) for row in formal], [float(row["formal_runtime"]) for row in formal], s=10, alpha=0.5)
    ax.set_title("Formal runtime versus candidate count")
    ax.set_xlabel("Candidates in region")
    ax.set_ylabel("Formal runtime seconds")
    save(fig, "semantic_direct_runtime_vs_region_size.png")
    print("Semantic direct recovery plots written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
