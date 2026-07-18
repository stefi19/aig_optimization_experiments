#!/usr/bin/env python3
"""Generate plots for proof-carrying semantic region replacement."""

from __future__ import annotations

import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "semantic_region_replacement"
PLOTS = ROOT / "results" / "plots"


def rows(name: str) -> list[dict[str, str]]:
    path = OUT / name
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def bar(path: Path, labels: list[str], values: list[float], title: str, ylabel: str) -> None:
    fig, ax = plt.subplots(figsize=(7, 3.8))
    colors = ["#2b6cb0", "#319795", "#dd6b20", "#805ad5", "#718096", "#c53030", "#38a169"]
    ax.bar(labels, values, color=colors[: len(labels)])
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    ax.tick_params(axis="x", rotation=24)
    ax.grid(axis="y", linewidth=0.35, alpha=0.35)
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def main() -> int:
    PLOTS.mkdir(parents=True, exist_ok=True)

    by_operator = rows("semantic_recovery_by_operator.csv")
    bar(
        PLOTS / "semantic_region_replacement_operator_recovery.png",
        [r["operator"].replace("_", "\n") for r in by_operator],
        [float(r["regions_recovered"]) for r in by_operator],
        "Semantic Region Recovery by Operator",
        "Recovered regions",
    )

    by_width = rows("semantic_recovery_by_width.csv")
    bar(
        PLOTS / "semantic_region_replacement_width_recovery.png",
        [f"w{r['width']}" for r in by_width],
        [float(r["regions_recovered"]) for r in by_width],
        "Semantic Region Recovery by Width",
        "Recovered regions",
    )

    candidates = rows("region_candidates.csv")
    closed = rows("region_closure_validation.csv")
    modules = rows("verified_semantic_modules.csv")
    attempts = rows("replacement_attempts.csv")
    cecs = rows("implementation_global_cec.csv")
    boundaries = rows("boundary_restoration_results.csv")
    bar(
        PLOTS / "semantic_region_replacement_funnel.png",
        ["candidates", "closed", "modules", "attempts", "accepted", "boundaries"],
        [
            len(candidates),
            sum(1 for r in closed if r["closure_status"] == "closed"),
            len(modules),
            len(attempts),
            sum(1 for r in attempts if r["accepted"] == "true"),
            sum(1 for r in boundaries if r["newly_recovered_boundary"] == "true"),
        ],
        "Semantic Region Replacement Funnel",
        "Count",
    )

    bar(
        PLOTS / "semantic_region_replacement_cec.png",
        ["equivalent", "disproved", "not run", "other"],
        [
            sum(1 for r in cecs if r["implementation_global_cec"] == "equivalent"),
            sum(1 for r in cecs if r["implementation_global_cec"] == "disproved"),
            sum(1 for r in cecs if r["implementation_global_cec"].startswith("not_run")),
            sum(1 for r in cecs if r["implementation_global_cec"] not in {"equivalent", "disproved"} and not r["implementation_global_cec"].startswith("not_run")),
        ],
        "Implementation Global CEC",
        "Attempts",
    )

    strategy = rows("replacement_strategy_ablation.csv")
    if strategy:
        bar(
            PLOTS / "semantic_region_replacement_boundaries.png",
            [r["strategy"].replace("_", "\n") for r in strategy],
            [float(r["boundaries_restored"]) for r in strategy],
            "Restored Boundaries by Replacement Strategy",
            "Boundaries",
        )

    failures = rows("failure_taxonomy.csv")
    top_failures = sorted(failures, key=lambda r: int(r["count"]), reverse=True)[:8]
    if top_failures:
        bar(
            PLOTS / "semantic_region_replacement_failure_taxonomy.png",
            [r["failure_reason"][:18].replace("_", "\n") for r in top_failures],
            [float(r["count"]) for r in top_failures],
            "Semantic Region Replacement Failures",
            "Cases",
        )

    synthesis = rows("replacement_module_synthesis.csv")
    if synthesis:
        bar(
            PLOTS / "semantic_region_replacement_cost.png",
            [r["region_id"].replace("controlled_", "").replace("_", "\n") for r in synthesis],
            [float(r["node_count"]) for r in synthesis],
            "Replacement Module BLIF Cost",
            "Nodes",
        )

    bar(
        PLOTS / "isolated_anchor_vs_region_replacement.png",
        ["old isolated\nanchors", "region\nreplacement"],
        [0, sum(1 for r in boundaries if r["newly_recovered_boundary"] == "true")],
        "Boundary Recovery: Anchor vs Region",
        "Recovered boundaries",
    )

    print(f"Wrote semantic region replacement plots to {PLOTS}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
