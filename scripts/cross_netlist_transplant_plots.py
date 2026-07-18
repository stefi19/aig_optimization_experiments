#!/usr/bin/env python3
"""Generate plots for cross-netlist cut transplantation."""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "cross_netlist_cut_transplantation"
PLOTS = ROOT / "results" / "plots"
PRESENTATION = ROOT / "docs" / "presentation" / "assets" / "plots"


def main() -> int:
    PLOTS.mkdir(parents=True, exist_ok=True)
    PRESENTATION.mkdir(parents=True, exist_ok=True)
    controlled = _rows("controlled_results.csv")
    development = _rows("development_results.csv")
    adapters = _rows("adapter_proofs.csv")
    gf2 = _rows("gaussian_baseline.csv")
    durability = _rows("durability.csv")
    failure = _rows("failure_taxonomy.csv")
    oracle = _rows("oracle_diagnostics.csv")

    accepted = sum(r["final_status"] == "accepted" for r in controlled)
    _bar("cross_netlist_transplant_funnel.png", ["positive\ncontrols", "accepted\ncontrols", "real\nrevisited", "real\nboundaries"], [sum(r["expected_outcome"].startswith("positive") for r in controlled), accepted, len(development), sum(r["new_recovered_boundary"] == "true" for r in development)], "Cross-Netlist Transplant Funnel", "Count")

    by_family = Counter(r["family"] for r in controlled if r["final_status"] == "accepted")
    _bar("cross_netlist_transplant_controlled_by_family.png", list(by_family), list(by_family.values()), "Accepted Controlled Transplants", "Accepted")

    adapter_status = Counter((r["adapter_kind"], r["formal_status"]) for r in adapters)
    labels = [f"{kind}\n{status}" for (kind, status), _ in sorted(adapter_status.items())]
    _bar("cross_netlist_transplant_adapter_proofs.png", labels, [v for _, v in sorted(adapter_status.items())], "Adapter Proof Results", "Adapters")

    real_failures = Counter(r["failure_stage"] for r in development)
    _bar("cross_netlist_transplant_real_blockers.png", list(real_failures), list(real_failures.values()), "Real Failure Blockers", "Targets")

    gf2_status = Counter(r["linearity_status"] for r in gf2)
    _bar("cross_netlist_transplant_gf2_baseline.png", list(gf2_status), list(gf2_status.values()), "GF(2) Adapter Baseline", "Adapters")

    dur = Counter((r["strategy"], r["usable_boundary"]) for r in durability)
    strategies = sorted({k for k, _ in dur})
    _bar("cross_netlist_transplant_durability.png", [s.replace("_", "\n") for s in strategies], [dur[(s, "true")] for s in strategies], "Durable Boundaries by Preservation Strategy", "Usable checkpoints")

    top_failures = sorted(failure, key=lambda r: int(r["count"]), reverse=True)[:10]
    _bar("cross_netlist_transplant_failure_taxonomy.png", [r["failure_reason"][:22].replace("_", "\n") for r in top_failures], [int(r["count"]) for r in top_failures], "Cross-Netlist Failure Taxonomy", "Cases")

    oracle_modes = Counter(r["localized_blocker"] for r in oracle)
    _bar("cross_netlist_transplant_oracle_ladder.png", [k[:22].replace("_", "\n") for k in oracle_modes], list(oracle_modes.values()), "Oracle Ladder Localized Blockers", "Diagnostic rows")

    print(f"Wrote cross-netlist transplant plots to {PLOTS}")
    return 0


def _rows(name: str) -> list[dict[str, str]]:
    path = OUT / name
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _bar(filename: str, labels: list[str], values: list[int], title: str, ylabel: str) -> None:
    if not labels:
        labels, values = ["none"], [0]
    fig, ax = plt.subplots(figsize=(7.4, 4.2))
    colors = ["#2563eb", "#059669", "#dc2626", "#7c3aed", "#d97706", "#0891b2", "#64748b", "#be123c"]
    ax.bar(labels, values, color=colors[: len(labels)])
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    ax.tick_params(axis="x", rotation=24)
    ax.grid(axis="y", linewidth=0.4, alpha=0.35)
    fig.tight_layout()
    for directory in (PLOTS, PRESENTATION):
        fig.savefig(directory / filename, dpi=180)
    plt.close(fig)


if __name__ == "__main__":
    raise SystemExit(main())
