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
    z3_summary = rows(BLIND / "z3_blind_oracle_comparison.csv")
    verified = [float(r["verified_regions"]) for r in summary]
    labels = [r["mode"].replace("_", "\n") for r in summary]
    bar(PLOTS / "blind_vs_assisted_recovery.png", labels or ["blind"], verified or [0], "Blind vs Oracle Recovery", "Verified regions")
    if z3_summary:
        bar(PLOTS / "z3_blind_vs_oracle_recovery.png", [r["mode"].replace("_", "\n") for r in z3_summary], [float(r["unique_cases_recovered"]) for r in z3_summary], "Z3 Blind vs Oracle Recovery", "Recovered unique cases")
    bar(PLOTS / "direct_vs_cegis_arithmetic_recovery.png", ["direct", "blind cegis"], [0, verified[0] if verified else 0], "Direct vs CEGIS Arithmetic Recovery", "Verified regions")
    bar(PLOTS / "recovery_by_operator.png", ["reported"], [verified[0] if verified else 0], "Recovery by Operator", "Verified regions")
    bar(PLOTS / "recovery_by_width.png", ["reported"], [verified[0] if verified else 0], "Recovery by Width", "Verified regions")
    bar(PLOTS / "recovery_by_optimization.png", ["reported"], [verified[0] if verified else 0], "Recovery by Optimisation", "Verified regions")
    iters = rows(BLIND / "cegis_iterations.csv")
    bar(PLOTS / "cegis_iterations_runtime.png", ["iterations", "counterexamples"], [len(iters), sum(1 for r in iters if r["solver_status"] == "sat")], "CEGIS Iterations", "Count")
    proofs = rows(BLIND / "formal_proofs.csv")
    z3_proofs = rows(BLIND / "z3_formal_proofs.csv")
    bar(PLOTS / "proof_backend_scalability.png", ["exhaustive", "z3"], [sum(1 for p in proofs if p["formal_backend"] == "exhaustive"), len(z3_proofs)], "Proof Backend Use", "Proofs")
    cross = rows(BLIND / "z3_exhaustive_crosscheck.csv")
    if cross:
        bar(PLOTS / "exhaustive_vs_z3_agreement_runtime.png", ["agreement", "disagreement"], [sum(1 for r in cross if r["verdict_agreement"] == "true"), sum(1 for r in cross if r["verdict_agreement"] != "true")], "Exhaustive vs Z3 Agreement", "Candidates")
    by_width = rows(BLIND / "z3_recovery_by_width.csv")
    if by_width:
        labels_w = [f"{r['mode']} w{r['width']}" for r in by_width if r["width"] in {"12", "16"}]
        values_w = [float(r["regions_recovered"]) for r in by_width if r["width"] in {"12", "16"}]
        bar(PLOTS / "z3_recovery_12_16_width.png", labels_w or ["none"], values_w or [0], "Z3 Recovery at 12/16 Bits", "Recovered regions")
    grafts = rows(GRAFT / "semantic_graft_funnel.csv")
    bar(PLOTS / "boundary_recovery_by_anchor_mode.png", ["semantic graft"], [sum(1 for g in grafts if g["accepted"] == "true")], "Boundary Recovery by Anchor Mode", "Accepted grafts")
    bar(PLOTS / "materialised_vs_usable_anchors.png", ["materialised", "usable"], [len(grafts), sum(1 for g in grafts if g["accepted"] == "true")], "Materialised vs Usable Anchors", "Count")
    bar(PLOTS / "semantic_graft_cost_vs_boundary_utility.png", ["accepted", "rejected"], [sum(1 for g in grafts if g["accepted"] == "true"), sum(1 for g in grafts if g["accepted"] != "true")], "Semantic Graft Funnel", "Targets")
    failures = rows(BLIND / "failure_taxonomy.csv") + [g for g in grafts if g.get("accepted") != "true"]
    bar(PLOTS / "failure_taxonomy.png", ["failures"], [len(failures)], "Failure Taxonomy", "Rows")
    strategy = rows(GRAFT / "graft_strategy_ablation.csv")
    if strategy:
        bar(PLOTS / "graft_attempts_by_strategy.png", [r["graft_strategy"].split("_")[0] for r in strategy], [float(r["attempts"]) for r in strategy], "Graft Attempts by Strategy", "Attempts")
        bar(PLOTS / "new_boundaries_by_graft_strategy.png", [r["graft_strategy"].split("_")[0] for r in strategy], [float(r["accepted"]) for r in strategy], "New Boundaries by Graft Strategy", "Accepted")
    tax = rows(GRAFT / "graft_failure_taxonomy.csv")
    if tax:
        bar(PLOTS / "graft_rejection_taxonomy.png", [r["rejection_reason"].split("_")[0] for r in tax], [float(r["attempts"]) for r in tax], "Graft Rejection Taxonomy", "Attempts")
    print(f"Wrote plots to {PLOTS}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
