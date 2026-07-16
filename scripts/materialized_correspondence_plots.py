#!/usr/bin/env python3
"""Generate compact plots for anchored-cut materialization results."""

from __future__ import annotations

import csv
import shutil
from collections import Counter
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "materialized_correspondence"
PLOTS = ROOT / "results" / "plots"
ASSETS = ROOT / "docs" / "presentation" / "assets" / "plots"


def main() -> int:
    targets = rows("materialization_targets.csv")
    cuts = rows("anchored_cut_candidates.csv")
    functions = rows("cut_function_extraction.csv")
    wires = rows("materialized_wires.csv")
    proofs = rows("materialized_anchor_formal_results.csv")
    proven = rows("proven_materialized_anchors.csv")
    usage = rows("materialized_anchor_usage.csv")
    boundary = rows("materialized_boundary_recovery.csv")
    failures = rows("materialized_failure_analysis.csv")
    plots = {
        "materialized_pipeline_funnel.png": {
            "targets": len(targets),
            "cuts": len(cuts),
            "functions": sum(r["extraction_status"] == "extracted" for r in functions),
            "wires": sum(r["generation_status"] == "generated" for r in wires),
            "proven": len(proven),
            "selected": sum(r.get("selected_by_boundary") == "True" for r in usage),
        },
        "materialized_cut_size_distribution.png": Counter(r["cut_size"] for r in cuts),
        "materialized_proof_outcomes.png": Counter(r["proof_status"] for r in proofs),
        "materialized_added_gate_cost.png": Counter(r["added_gate_count"] for r in wires if r.get("added_gate_count")),
        "materialized_proven_vs_useful.png": {
            "proven": len(proven),
            "usable": sum(r.get("usable_for_boundary") == "True" for r in usage),
            "selected": sum(r.get("selected_by_boundary") == "True" for r in usage),
        },
        "materialized_boundary_recovery.png": {
            "baseline_success": sum(r["baseline_success"] == "True" for r in boundary),
            "materialized_success": sum(r["materialized_success"] == "True" for r in boundary),
            "new": sum(r["newly_recovered_boundary"] == "True" for r in boundary),
        },
        "materialized_by_optimization.png": Counter(r["optimization"] for r in proven),
        "materialized_failure_taxonomy.png": {f"{r['stage']}:{r['failure_reason']}"[:28]: int(r["count"]) for r in failures},
    }
    for name, values in plots.items():
        draw_bar({str(k): float(v) for k, v in values.items()}, name.replace("_", " ").replace(".png", "").title(), PLOTS / name)
        ASSETS.mkdir(parents=True, exist_ok=True)
        shutil.copy2(PLOTS / name, ASSETS / name)
    print("Materialized correspondence plots written")
    return 0


def draw_bar(values: dict[str, float], title: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGB", (980, 560), "white")
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default()
    draw.text((36, 24), title, fill="black", font=font)
    if not values:
        draw.text((36, 88), "No data", fill="black", font=font)
        img.save(path)
        return
    labels = list(values)
    max_v = max(max(values.values()), 1.0)
    base = 440
    bar_w = max(22, min(90, 860 // max(1, len(labels)) - 12))
    for idx, label in enumerate(labels):
        x = 60 + idx * (bar_w + 12)
        h = int(values[label] / max_v * 340)
        draw.rectangle((x, base - h, x + bar_w, base), fill="#4e79a7")
        draw.text((x, base + 12), label[:22], fill="black", font=font)
        draw.text((x, base - h - 16), f"{values[label]:.0f}", fill="black", font=font)
    img.save(path)


def rows(name: str) -> list[dict[str, str]]:
    path = OUT / name
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


if __name__ == "__main__":
    raise SystemExit(main())
