#!/usr/bin/env python3
"""Generate lightweight PNG plots for boundary recovery without Matplotlib."""

from __future__ import annotations

import csv
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "results" / "boundary_recovery" / "boundary_recovery_cases.csv"
CRITICAL = ROOT / "results" / "boundary_recovery" / "critical_path_region_recovery.csv"
PLOTS = ROOT / "results" / "plots"


def read_rows(path: Path) -> list[dict[str, str]]:
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
    return str(value).lower() == "true"


def grouped_mean(rows: list[dict[str, str]], key: str, value: str, bool_value: bool = False) -> dict[str, float]:
    groups: dict[str, list[float]] = {}
    for row in rows:
        groups.setdefault(row.get(key, ""), []).append(float(b(row.get(value))) if bool_value else f(row.get(value)))
    return {k: sum(v) / len(v) for k, v in sorted(groups.items())}


def grouped_sum(rows: list[dict[str, str]], key: str, value: str) -> dict[str, float]:
    groups: dict[str, float] = {}
    for row in rows:
        groups[row.get(key, "")] = groups.get(row.get(key, ""), 0.0) + f(row.get(value))
    return dict(sorted(groups.items()))


def grouped_count(rows: list[dict[str, str]], key: str) -> dict[str, float]:
    groups: dict[str, float] = {}
    for row in rows:
        label = row.get(key, "") or "valid"
        groups[label] = groups.get(label, 0.0) + 1.0
    return dict(sorted(groups.items()))


def draw_bar(data: dict[str, float], title: str, ylabel: str, path: Path) -> None:
    width, height = 900, 520
    img = Image.new("RGB", (width, height), "white")
    d = ImageDraw.Draw(img)
    d.text((30, 20), title, fill="black")
    d.text((30, 45), ylabel, fill="#444444")
    if not data:
        d.text((30, 100), "No data", fill="black")
        img.save(path)
        return
    max_value = max(max(data.values()), 1.0)
    left, bottom = 80, 430
    bar_w = max(18, int(700 / max(1, len(data))))
    for idx, (label, value) in enumerate(data.items()):
        x0 = left + idx * bar_w
        h = int((value / max_value) * 320)
        d.rectangle((x0, bottom - h, x0 + bar_w - 8, bottom), fill="#4c78a8")
        d.text((x0, bottom + 10), label[:18], fill="black")
        d.text((x0, bottom - h - 18), f"{value:.2f}", fill="black")
    d.line((left, 100, left, bottom), fill="black")
    d.line((left, bottom, 850, bottom), fill="black")
    img.save(path)


def draw_scatter(rows: list[tuple[float, float]], title: str, xlabel: str, ylabel: str, path: Path) -> None:
    width, height = 700, 520
    img = Image.new("RGB", (width, height), "white")
    d = ImageDraw.Draw(img)
    d.text((30, 20), title, fill="black")
    d.text((300, 485), xlabel, fill="black")
    d.text((20, 250), ylabel, fill="black")
    if not rows:
        d.text((30, 100), "No data", fill="black")
        img.save(path)
        return
    xs = [x for x, _ in rows]
    ys = [y for _, y in rows]
    max_x = max(max(xs), 1.0)
    max_y = max(max(ys), 1.0)
    left, top, right, bottom = 90, 80, 650, 450
    d.rectangle((left, top, right, bottom), outline="black")
    for x, y in rows:
        px = left + int((x / max_x) * (right - left))
        py = bottom - int((y / max_y) * (bottom - top))
        d.ellipse((px - 4, py - 4, px + 4, py + 4), fill="#54a24b")
    img.save(path)


def main() -> int:
    PLOTS.mkdir(parents=True, exist_ok=True)
    rows = read_rows(CASES)
    critical = read_rows(CRITICAL)
    draw_bar(grouped_mean(rows, "optimization", "boundary_extension_ratio"), "Boundary Extension by Optimization", "mean extension ratio", PLOTS / "boundary_extension_by_optimization.png")
    draw_bar(grouped_mean(rows, "anchor_mode", "recovery_success", bool_value=True), "Recovery Success by Anchor Mode", "success rate", PLOTS / "boundary_recovery_success_by_anchor_mode.png")
    draw_bar(grouped_mean(rows, "anchor_mode", "boundary_extension_ratio"), "Exact-only vs Formal-all Extension", "mean extension ratio", PLOTS / "boundary_exact_vs_formal_extension.png")
    draw_scatter([(f(r.get("anchor_count")), f(r.get("boundary_extension_ratio"))) for r in rows], "Anchor Density vs Boundary Extension", "anchor count", "extension", PLOTS / "boundary_anchor_density_vs_extension.png")
    draw_scatter([(f(r.get("coi_node_count")), f(r.get("extended_region_node_count"))) for r in rows], "COI Size vs Extended Region Size", "COI nodes", "region nodes", PLOTS / "boundary_coi_vs_region_size.png")
    draw_bar(grouped_mean(rows, "anchor_mode", "mean_anchor_distance"), "Traversal Distance Distribution", "mean distance", PLOTS / "boundary_traversal_distance_distribution.png")
    draw_bar(grouped_count(rows, "failure_reason"), "Boundary Recovery Failure Reasons", "case count", PLOTS / "boundary_failure_reasons.png")
    draw_bar(grouped_sum(rows, "anchor_mode", "cycle_conflict_count"), "Cycle-Resolution Frequency", "cycle conflicts", PLOTS / "boundary_cycle_resolution_frequency.png")
    draw_scatter([(f(r.get("spec_node_count")), f(r.get("runtime_seconds"))) for r in rows], "Runtime by Circuit Size", "spec nodes", "runtime seconds", PLOTS / "boundary_runtime_by_circuit_size.png")
    draw_bar(grouped_sum(critical, "anchor_mode", "previously_unresolved_nodes_enclosed"), "Critical-Path Nodes Enclosed by Regions", "unresolved nodes enclosed", PLOTS / "boundary_critical_path_enclosed.png")
    print("Boundary recovery plots regenerated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
