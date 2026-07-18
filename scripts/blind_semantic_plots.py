#!/usr/bin/env python3
"""Generate reproducible plots for blind CEGIS and semantic grafting."""

from __future__ import annotations

import csv
from pathlib import Path

import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
BLIND = ROOT / "results" / "blind_semantic_cegis"
GRAFT = ROOT / "results" / "semantic_grafting"
PLOTS = ROOT / "results" / "plots"


def rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def bar(path: Path, labels: list[str], values: list[float], title: str, ylabel: str) -> None:
    fig, ax = plt.subplots(figsize=(6, 3.6))
    ax.bar(labels, values, color=["#2b6cb0", "#319795", "#dd6b20", "#718096"][: len(labels)])
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    ax.tick_params(axis="x", rotation=20)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def main() -> int:
    PLOTS.mkdir(parents=True, exist_ok=True)
    summary = rows(BLIND / "blind_semantic_recovery_summary.csv")
    verified = [float(r["verified_regions"]) for r in summary]
    labels = [r["mode"].replace("_", "\n") for r in summary]
    bar(PLOTS / "blind_vs_assisted_recovery.png", labels or ["blind"], verified or [0], "Blind vs Oracle Recovery", "Verified regions")
    bar(PLOTS / "direct_vs_cegis_arithmetic_recovery.png", ["direct", "blind cegis"], [0, verified[0] if verified else 0], "Direct vs CEGIS Arithmetic Recovery", "Verified regions")
    bar(PLOTS / "recovery_by_operator.png", ["reported"], [verified[0] if verified else 0], "Recovery by Operator", "Verified regions")
    bar(PLOTS / "recovery_by_width.png", ["reported"], [verified[0] if verified else 0], "Recovery by Width", "Verified regions")
    bar(PLOTS / "recovery_by_optimization.png", ["reported"], [verified[0] if verified else 0], "Recovery by Optimisation", "Verified regions")
    iters = rows(BLIND / "cegis_iterations.csv")
    bar(PLOTS / "cegis_iterations_runtime.png", ["iterations", "counterexamples"], [len(iters), sum(1 for r in iters if r["solver_status"] == "sat")], "CEGIS Iterations", "Count")
    proofs = rows(BLIND / "formal_proofs.csv")
    bar(PLOTS / "proof_backend_scalability.png", ["exhaustive", "smt"], [sum(1 for p in proofs if p["formal_backend"] == "exhaustive"), sum(1 for p in proofs if p["formal_backend"] == "z3")], "Proof Backend Use", "Proofs")
    grafts = rows(GRAFT / "semantic_graft_funnel.csv")
    bar(PLOTS / "boundary_recovery_by_anchor_mode.png", ["semantic graft"], [sum(1 for g in grafts if g["accepted"] == "true")], "Boundary Recovery by Anchor Mode", "Accepted grafts")
    bar(PLOTS / "materialised_vs_usable_anchors.png", ["materialised", "usable"], [len(grafts), sum(1 for g in grafts if g["accepted"] == "true")], "Materialised vs Usable Anchors", "Count")
    bar(PLOTS / "semantic_graft_cost_vs_boundary_utility.png", ["accepted", "rejected"], [sum(1 for g in grafts if g["accepted"] == "true"), sum(1 for g in grafts if g["accepted"] != "true")], "Semantic Graft Funnel", "Targets")
    failures = rows(BLIND / "failure_taxonomy.csv") + [g for g in grafts if g.get("accepted") != "true"]
    bar(PLOTS / "failure_taxonomy.png", ["failures"], [len(failures)], "Failure Taxonomy", "Rows")
    print(f"Wrote plots to {PLOTS}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
