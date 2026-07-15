#!/usr/bin/env python3
"""Generate compact plots for ODC anchor experiments."""

from __future__ import annotations

import csv
from collections import Counter, defaultdict
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "odc_anchor_generation"
PLOTS = ROOT / "results" / "plots"


def rows(name):
    path = OUT / name
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def draw_bar(values: dict[str, float], title: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGB", (900, 520), "white")
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default()
    draw.text((40, 24), title, fill="black", font=font)
    if not values:
        draw.text((40, 80), "No data", fill="black", font=font)
        img.save(path)
        return
    labels = list(values)
    max_v = max(max(values.values()), 1.0)
    base = 420
    bar_w = max(24, min(100, 760 // max(1, len(labels)) - 12))
    for i, label in enumerate(labels):
        x = 80 + i * (bar_w + 12)
        h = int(values[label] / max_v * 330)
        draw.rectangle((x, base - h, x + bar_w, base), fill="#59a14f")
        draw.text((x, base + 10), label[:18], fill="black", font=font)
        draw.text((x, base - h - 16), f"{values[label]:.1f}", fill="black", font=font)
    img.save(path)


def main() -> int:
    candidates = rows("odc_candidate_features.csv")
    proofs = rows("odc_formal_proofs.csv")
    recovery = rows("odc_boundary_recovery_cases.csv")
    funnel = {
        "generated": len(candidates),
        "checked": len(proofs),
        "proven": sum(r["proof_status"] == "proven_odc_valid" for r in proofs),
        "disproved": sum(r["proof_status"] == "disproven" for r in proofs),
    }
    draw_bar(funnel, "ODC Candidate Funnel", PLOTS / "odc_candidate_funnel.png")
    draw_bar({k: float(v) for k, v in Counter(r["proof_status"] for r in proofs).items()}, "ODC Proof Outcomes", PLOTS / "odc_proof_outcomes.png")
    grouped = defaultdict(lambda: [0, 0])
    for r in recovery:
        key = r["context_mode"] + "/" + r["anchor_mode"]
        grouped[key][0] += 1
        grouped[key][1] += int(r["success"] == "True")
    draw_bar({k: v[1] / v[0] if v[0] else 0 for k, v in sorted(grouped.items())}, "ODC Recovery by Anchor Mode", PLOTS / "odc_recovery_by_anchor_mode.png")
    draw_bar({k: float(v) for k, v in Counter(r["classification"] for r in recovery if r["success"] != "True").items()}, "ODC Remaining Failure Taxonomy", PLOTS / "odc_remaining_failures.png")
    draw_bar({k: float(v) for k, v in Counter(r["optimization"] for r in recovery if r["success"] == "True").items()}, "ODC Recoveries by Optimization", PLOTS / "odc_recoveries_by_optimization.png")
    draw_bar({k: float(v) for k, v in Counter(r["context_mode"] for r in recovery).items()}, "ODC Rows by Context Mode", PLOTS / "odc_rows_by_context.png")
    print("ODC plots written to results/plots/odc_*")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
