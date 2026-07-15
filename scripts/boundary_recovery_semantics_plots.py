#!/usr/bin/env python3
"""Generate compact plots for repaired boundary-recovery semantics."""

from __future__ import annotations

import csv
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
SEM = ROOT / "results" / "boundary_recovery_semantics"
PLOTS = ROOT / "results" / "plots"


def rows(name: str) -> list[dict[str, str]]:
    path = SEM / name
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def draw_bar(data: dict[str, float], title: str, ylabel: str, out: Path) -> None:
    img = Image.new("RGB", (920, 520), "white")
    d = ImageDraw.Draw(img)
    d.text((30, 20), title, fill="black")
    d.text((30, 45), ylabel, fill="#444")
    if not data:
        d.text((30, 100), "No data", fill="black")
        img.save(out)
        return
    max_v = max(max(data.values()), 1.0)
    left, bottom = 75, 430
    width = max(24, int(780 / len(data)))
    for i, (label, value) in enumerate(data.items()):
        x = left + i * width
        h = int(value / max_v * 320)
        d.rectangle((x, bottom - h, x + width - 8, bottom), fill="#4c78a8")
        d.text((x, bottom + 8), label[:18], fill="black")
        d.text((x, bottom - h - 18), f"{value:.2f}", fill="black")
    img.save(out)


def main() -> int:
    PLOTS.mkdir(parents=True, exist_ok=True)
    audit = rows("coi_repair_audit.csv")
    identity = rows("identity_exact_match_results.csv")
    avail = rows("circuit_availability.csv")
    opt = rows("optimized_recovery_corrected.csv")
    cp = rows("critical_path_coi_validation.csv")
    draw_bar(
        {
            "original_valid": sum(r.get("original_valid") == "True" for r in audit),
            "final_valid": sum(r.get("final_valid") == "True" for r in audit),
        },
        "COI Validity Before versus After Repair",
        "COI count",
        PLOTS / "boundary_sem_coi_validity_repair.png",
    )
    draw_bar(
        {
            "success": sum(r.get("top_level_classification") == "success" for r in identity),
            "EBI match": sum(r.get("ebi_exact_match") == "True" for r in identity),
            "EBO match": sum(r.get("ebo_exact_match") == "True" for r in identity),
            "region match": sum(r.get("region_exact_match") == "True" for r in identity),
        },
        "Identity Exact-Match Rates",
        "case count",
        PLOTS / "boundary_sem_identity_exact_match.png",
    )
    draw_bar(
        {
            "declared": len(avail),
            "eligible": sum(r.get("eligibility_status") == "available" for r in avail),
            "attempted": sum(r.get("attempted") == "True" for r in opt),
        },
        "Declared versus Eligible versus Attempted",
        "row count",
        PLOTS / "boundary_sem_eligibility_accounting.png",
    )
    by_opt: dict[str, list[int]] = {}
    for r in opt:
        if r.get("attempted") == "True":
            by_opt.setdefault(r["optimization"], [0, 0])
            by_opt[r["optimization"]][0] += 1
            by_opt[r["optimization"]][1] += int(r.get("top_level_classification") == "success")
    draw_bar({k: v[1] / v[0] for k, v in sorted(by_opt.items())}, "Corrected Recovery by Optimization", "success rate", PLOTS / "boundary_sem_success_by_optimization.png")
    failures: dict[str, float] = {}
    for r in opt:
        if r.get("attempted") == "True" and r.get("top_level_classification") != "success":
            failures[r.get("failure_reason", "unknown")] = failures.get(r.get("failure_reason", "unknown"), 0) + 1
    draw_bar(dict(sorted(failures.items())), "Corrected Failure Taxonomy", "case count", PLOTS / "boundary_sem_failure_taxonomy.png")
    draw_bar({r["case_id"][:18]: float(r.get("boundary_extension_ratio") or 0) for r in opt if r.get("top_level_classification") == "success"}, "Extension Ratio for Successful Valid Cases", "extension ratio", PLOTS / "boundary_sem_extension_successes.png")
    by_size: dict[str, list[int]] = {}
    for r in cp:
        by_size.setdefault(r["segment_size"], [0, 0])
        by_size[r["segment_size"]][0] += 1
        by_size[r["segment_size"]][1] += int(r.get("coi_valid") == "True")
    draw_bar({k: v[1] / v[0] for k, v in sorted(by_size.items())}, "Critical-Path COI Validity by Segment Size", "valid rate", PLOTS / "boundary_sem_critical_path_validity.png")
    print("Boundary semantics plots written to results/plots/boundary_sem_*")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
