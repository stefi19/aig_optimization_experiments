#!/usr/bin/env python3
"""Generate lightweight PNG plots for boundary-recovery diagnosis."""

from __future__ import annotations

import csv
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
DIAG = ROOT / "results" / "boundary_recovery_diagnosis"
PLOTS = ROOT / "results" / "plots"


def read_rows(name: str) -> list[dict[str, str]]:
    path = DIAG / name
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def f(value: object) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def b(value: object) -> bool:
    return str(value).strip().lower() == "true"


def grouped_count(rows: list[dict[str, str]], key: str, *, failed_only: bool = False) -> dict[str, float]:
    out: dict[str, float] = {}
    for row in rows:
        if failed_only and b(row.get("recovery_success")):
            continue
        label = row.get(key, "") or "unknown"
        out[label] = out.get(label, 0.0) + 1.0
    return dict(sorted(out.items()))


def grouped_mean(rows: list[dict[str, str]], key: str, value: str, *, bool_value: bool = False) -> dict[str, float]:
    groups: dict[str, list[float]] = {}
    for row in rows:
        groups.setdefault(row.get(key, "") or "unknown", []).append(float(b(row.get(value))) if bool_value else f(row.get(value)))
    return {k: sum(v) / len(v) for k, v in sorted(groups.items())}


def draw_bar(data: dict[str, float], title: str, ylabel: str, path: Path) -> None:
    width, height = 980, 540
    img = Image.new("RGB", (width, height), "white")
    d = ImageDraw.Draw(img)
    d.text((30, 18), title, fill="black")
    d.text((30, 45), ylabel, fill="#444444")
    if not data:
        d.text((30, 100), "No data", fill="black")
        img.save(path)
        return
    max_value = max(max(data.values()), 1.0)
    left, bottom = 75, 430
    bar_w = max(22, int(820 / max(1, len(data))))
    for idx, (label, value) in enumerate(data.items()):
        x0 = left + idx * bar_w
        h = int((value / max_value) * 320)
        d.rectangle((x0, bottom - h, x0 + bar_w - 8, bottom), fill="#4c78a8")
        d.text((x0, bottom + 8), label[:20], fill="black")
        d.text((x0, bottom - h - 17), f"{value:.2f}", fill="black")
    d.line((left, 90, left, bottom), fill="black")
    d.line((left, bottom, 940, bottom), fill="black")
    img.save(path)


def draw_scatter(rows: list[tuple[float, float, bool]], title: str, xlabel: str, ylabel: str, path: Path) -> None:
    width, height = 760, 540
    img = Image.new("RGB", (width, height), "white")
    d = ImageDraw.Draw(img)
    d.text((30, 18), title, fill="black")
    d.text((315, 500), xlabel, fill="black")
    d.text((18, 250), ylabel, fill="black")
    if not rows:
        d.text((30, 100), "No data", fill="black")
        img.save(path)
        return
    max_x = max(max(x for x, _, _ in rows), 1.0)
    max_y = max(max(y for _, y, _ in rows), 1.0)
    left, top, right, bottom = 90, 80, 710, 455
    d.rectangle((left, top, right, bottom), outline="black")
    for x, y, success in rows:
        px = left + int((x / max_x) * (right - left))
        py = bottom - int((y / max_y) * (bottom - top))
        color = "#54a24b" if success else "#e45756"
        d.ellipse((px - 4, py - 4, px + 4, py + 4), fill=color)
    img.save(path)


def main() -> int:
    PLOTS.mkdir(parents=True, exist_ok=True)
    cases = read_rows("boundary_failure_taxonomy.csv")
    identity = read_rows("boundary_identity_baseline.csv")
    coverage = read_rows("boundary_anchor_coverage.csv")
    diff = read_rows("boundary_anchor_mode_differential.csv")
    coi = read_rows("boundary_coi_audit.csv")
    progression = read_rows("boundary_optimization_progression.csv")
    cp = read_rows("boundary_generated_critical_path_cois.csv")

    draw_bar(grouped_count(cases, "failure_stage", failed_only=True), "Failure Count by Pipeline Stage", "failed case count", PLOTS / "boundary_diag_failure_by_stage.png")
    draw_bar(grouped_count(cases, "failure_reason", failed_only=True), "Failure Count by Reason", "failed case count", PLOTS / "boundary_diag_failure_by_reason.png")
    draw_bar({"identity": sum(b(r.get("recovery_success")) for r in identity), "optimized": sum(b(r.get("recovery_success")) for r in cases)}, "Identity versus Optimized Recovery", "successful rows", PLOTS / "boundary_diag_identity_vs_optimized.png")
    draw_bar(grouped_mean(cases, "optimization", "recovery_success", bool_value=True), "Recovery Success by Optimization Flow", "success rate", PLOTS / "boundary_diag_success_by_optimization.png")
    draw_bar(grouped_mean(cases, "optimization", "boundary_extension_ratio"), "Extension Ratio by Optimization Flow", "mean extension ratio", PLOTS / "boundary_diag_extension_by_optimization.png")
    draw_scatter([(f(r.get("coi_anchor_density")), f(r.get("global_anchor_density")), b(next((c.get("recovery_success") for c in cases if c.get("case_id") == r.get("case_id")), False))) for r in coverage], "Relevant Anchor Density versus Outcome", "COI anchor density", "global anchor density", PLOTS / "boundary_diag_anchor_density_vs_outcome.png")
    draw_bar(grouped_mean(coverage, "anchor_mode", "formal_all_added_relevant_anchors"), "Global versus Relevant SAT/CEC Anchor Additions", "mean added relevant anchors", PLOTS / "boundary_diag_global_vs_relevant_anchors.png")
    draw_scatter([(f(r.get("bi_anchor_distance_mean")), f(r.get("bo_anchor_distance_mean")), b(next((c.get("recovery_success") for c in cases if c.get("case_id") == r.get("case_id")), False))) for r in coverage if r.get("bi_anchor_distance_mean") != "unreachable" and r.get("bo_anchor_distance_mean") != "unreachable"], "Nearest-Anchor Distance by Outcome", "BI distance", "BO distance", PLOTS / "boundary_diag_nearest_anchor_distance.png")
    draw_bar(grouped_count(diff, "differential_classification"), "Exact-only versus Formal-all Differential", "case count", PLOTS / "boundary_diag_exact_vs_formal_differential.png")
    draw_bar(grouped_mean(coi, "coi_source", "coi_valid", bool_value=True), "COI Source versus Validity", "validity rate", PLOTS / "boundary_diag_coi_source_success.png")
    draw_bar(grouped_count(progression, "first_recovery_failure_flow"), "First Failure Flow Distribution", "COI count", PLOTS / "boundary_diag_first_failure_flow.png")
    draw_bar(grouped_mean(cp, "segment_size", "recovery_success", bool_value=True), "Critical-Path COI Recovery by Segment Size", "success rate", PLOTS / "boundary_diag_critical_path_coi_recovery.png")
    print("Boundary diagnosis plots written to results/plots/boundary_diag_*")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
