#!/usr/bin/env python3
"""Generate compact plots for extended-boundary search results."""

from __future__ import annotations

import csv
from collections import Counter, defaultdict
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "extended_boundary_search"
PLOTS = ROOT / "results" / "plots"


def read_rows(name: str) -> list[dict[str, str]]:
    with (OUT / name).open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def draw_bar(values: dict[str, float], title: str, ylabel: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    width, height = 900, 520
    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default()
    draw.text((40, 24), title, fill="black", font=font)
    if not values:
        draw.text((40, 80), "No data", fill="black", font=font)
        img.save(path)
        return
    labels = list(values)
    max_v = max(max(values.values()), 1.0)
    left, top, bottom = 80, 80, 420
    bar_w = max(24, min(90, (width - left - 40) // max(1, len(labels)) - 12))
    for i, label in enumerate(labels):
        x = left + i * (bar_w + 12)
        h = int((values[label] / max_v) * (bottom - top))
        draw.rectangle((x, bottom - h, x + bar_w, bottom), fill="#4c78a8")
        draw.text((x, bottom + 10), label[:16], fill="black", font=font)
        draw.text((x, bottom - h - 16), f"{values[label]:.2f}", fill="black", font=font)
    draw.text((20, top), ylabel, fill="black", font=font)
    img.save(path)


def grouped_rate(rows: list[dict[str, str]], key: str) -> dict[str, float]:
    grouped = defaultdict(lambda: [0, 0])
    for row in rows:
        grouped[row[key]][0] += 1
        grouped[row[key]][1] += int(row.get("success") == "True")
    return {k: v[1] / v[0] if v[0] else 0.0 for k, v in sorted(grouped.items())}


def grouped_mean(rows: list[dict[str, str]], key: str, value: str) -> dict[str, float]:
    grouped = defaultdict(list)
    for row in rows:
        try:
            grouped[row[key]].append(float(row.get(value) or 0))
        except ValueError:
            pass
    return {k: sum(vals) / len(vals) if vals else 0.0 for k, vals in sorted(grouped.items())}


def main() -> int:
    rows = read_rows("extended_boundary_cases.csv")
    PLOTS.mkdir(parents=True, exist_ok=True)
    draw_bar(grouped_rate(rows, "search_mode"), "Extended Boundary Success by Search Mode", "success rate", PLOTS / "extended_boundary_success_by_search_mode.png")
    draw_bar(grouped_rate(rows, "anchor_mode"), "Exact-only vs Formal-all Extended Recovery", "success rate", PLOTS / "extended_boundary_exact_vs_formal.png")
    draw_bar(grouped_mean(rows, "search_mode", "extension_ratio"), "Extension Ratio by Search Mode", "mean extension ratio", PLOTS / "extended_boundary_extension_ratio.png")
    draw_bar(grouped_mean(rows, "search_mode", "incoming_bypass_count"), "Incoming Bypasses by Search Mode", "mean bypass count", PLOTS / "extended_boundary_incoming_bypasses.png")
    draw_bar(grouped_mean(rows, "search_mode", "outgoing_bypass_count"), "Outgoing Bypasses by Search Mode", "mean bypass count", PLOTS / "extended_boundary_outgoing_bypasses.png")
    draw_bar(grouped_mean(rows, "search_mode", "search_states"), "Search States by Mode", "mean states", PLOTS / "extended_boundary_search_states.png")
    classes = Counter(row["classification"] for row in rows if row.get("success") != "True")
    draw_bar({k: float(v) for k, v in sorted(classes.items())}, "Remaining Failure Classification", "rows", PLOTS / "extended_boundary_remaining_failures.png")
    anchor_usage = {
        row["anchor_mode"] + "/" + row["search_mode"]: float(row.get("selected_sat_cec_anchor_count") or 0)
        for row in read_rows("anchor_usage.csv")
    }
    draw_bar(anchor_usage, "Selected SAT/CEC Anchors", "count", PLOTS / "extended_boundary_anchor_usage.png")
    print("Extended-boundary plots written to results/plots/extended_boundary_*")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
