#!/usr/bin/env python3
"""Compare ABC-native sweep reductions with existing custom correspondence results."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "results"
PLOTS_DIR = RESULTS_DIR / "plots"
BASELINE_CSV = RESULTS_DIR / "abc_native_sweep_baseline.csv"
COMPARISON_CSV = RESULTS_DIR / "abc_native_vs_custom_comparison.csv"
COMPARISON_MD = RESULTS_DIR / "abc_native_vs_custom_comparison.md"


FIELDNAMES = [
    "benchmark",
    "source_family",
    "optimization",
    "best_abc_flow",
    "node_count_before",
    "node_count_after",
    "level_count_before",
    "level_count_after",
    "node_reduction",
    "level_reduction",
    "exact_match_rate",
    "preserved_signature_fraction",
    "optimized_signature_coverage",
    "custom_node_reduction_rate",
    "custom_level_reduction_rate",
    "non_exact_verified",
    "verification_rate",
    "rejection_rate",
    "approx_near_match_available",
    "critical_path_mapped_fraction",
    "interpretation",
]


def read_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def to_float(value: str | None, default: float = 0.0) -> float:
    try:
        if value in (None, ""):
            return default
        return float(value)
    except ValueError:
        return default


def best_abc_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    best: dict[tuple[str, str], dict[str, str]] = {}
    for row in rows:
        key = (row.get("benchmark", ""), row.get("optimization", ""))
        current = best.get(key)
        if current is None or to_float(row.get("node_reduction")) > to_float(current.get("node_reduction")):
            best[key] = row
    out: list[dict[str, str]] = []
    for row in best.values():
        out.append(
            {
                "benchmark": row.get("benchmark", ""),
                "source_family": row.get("source_family", ""),
                "optimization": row.get("optimization", ""),
                "best_abc_flow": row.get("abc_sweep_flow_name", ""),
                "node_count_before": row.get("node_count_before", ""),
                "node_count_after": row.get("node_count_after", ""),
                "level_count_before": row.get("level_count_before", ""),
                "level_count_after": row.get("level_count_after", ""),
                "node_reduction": row.get("node_reduction", ""),
                "level_reduction": row.get("level_reduction", ""),
            }
        )
    return sorted(out, key=lambda r: (r["benchmark"], r["optimization"]))


def keyed(rows: list[dict[str, str]]) -> dict[tuple[str, str], dict[str, str]]:
    return {(r.get("benchmark", ""), r.get("optimization", "")): r for r in rows}


def approx_available(rows: list[dict[str, str]]) -> str:
    for row in rows:
        if row.get("sat_status") == "verified" and to_float(row.get("pct_distance_le_5pct")) > 0:
            return "true"
    return "false" if rows else ""


def critical_path_fraction(rows: list[dict[str, str]]) -> dict[tuple[str, str], str]:
    counts: dict[tuple[str, str], list[int]] = {}
    for row in rows:
        key = (row.get("benchmark", ""), row.get("optimization", ""))
        mapped = 0 if row.get("mapping_category") in ("", "unresolved") else 1
        counts.setdefault(key, []).append(mapped)
    return {
        key: f"{sum(values) / len(values):.4f}"
        for key, values in counts.items()
        if values
    }


def classify(row: dict[str, str]) -> str:
    abc_reduction = to_float(row.get("node_reduction"))
    preservation = row.get("preserved_signature_fraction")
    non_exact = to_float(row.get("non_exact_verified"))
    if preservation not in ("", None) and abc_reduction > 0 and to_float(preservation) > 0.75:
        return "ABC reduces while many custom exact signatures remain preserved"
    if non_exact > 0 and abc_reduction > 0:
        return "Both flows show recoverable structure, but ABC mapping is not exposed here"
    if abc_reduction > 0:
        return "ABC reduces this network; custom evidence is indirect or absent"
    return "ABC sweep did not reduce nodes in this row"


def build_comparison() -> list[dict[str, str]]:
    baseline = best_abc_rows(read_rows(BASELINE_CSV))
    summary = keyed(read_rows(RESULTS_DIR / "summary_metrics.csv"))
    sat = keyed(read_rows(RESULTS_DIR / "sat_summary.csv"))
    approx = approx_available(read_rows(RESULTS_DIR / "approximate_distance_summary.csv"))
    critical = critical_path_fraction(read_rows(RESULTS_DIR / "critical_path_mapping.csv"))

    rows: list[dict[str, str]] = []
    for row in baseline:
        key = (row["benchmark"], row["optimization"])
        merged = {name: "" for name in FIELDNAMES}
        merged.update(row)
        srow = summary.get(key, {})
        merged["exact_match_rate"] = srow.get("exact_match_rate", "")
        merged["preserved_signature_fraction"] = srow.get("preserved_signature_fraction", "")
        merged["optimized_signature_coverage"] = srow.get("optimized_signature_coverage", "")
        merged["custom_node_reduction_rate"] = srow.get("node_reduction_rate", "")
        merged["custom_level_reduction_rate"] = srow.get("level_reduction_rate", "")
        satrow = sat.get(key, {})
        merged["non_exact_verified"] = satrow.get("non_exact_verified", "")
        merged["verification_rate"] = satrow.get("verification_rate", "")
        merged["rejection_rate"] = satrow.get("rejection_rate", "")
        merged["approx_near_match_available"] = approx
        merged["critical_path_mapped_fraction"] = critical.get(key, "")
        merged["interpretation"] = classify(merged)
        rows.append(merged)
    return rows


def write_csv_rows(rows: list[dict[str, str]], path: Path = COMPARISON_CSV) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(rows: list[dict[str, str]], path: Path = COMPARISON_MD) -> None:
    lines = [
        "# ABC-Native vs Custom Correspondence Comparison",
        "",
        "This comparison is intentionally indirect. ABC-native FRAIG flows report swept",
        "network size changes, while the custom pipeline reports candidate correspondences",
        "and SAT-verified node-pair checks.",
        "",
    ]
    if not rows:
        lines.append("No comparison rows were available.")
    else:
        lines.extend([
            f"Rows compared: {len(rows)}",
            "",
            "| Benchmark | Optimization | Best ABC flow | ABC node delta | Preservation | Non-exact SAT matches | Interpretation |",
            "|---|---|---|---:|---:|---:|---|",
        ])
        for row in rows[:30]:
            preservation = row.get("preserved_signature_fraction", "")
            preservation_text = f"{to_float(preservation):.3f}" if preservation else ""
            non_exact = row.get("non_exact_verified", "")
            lines.append(
                f"| `{row['benchmark']}` | `{row['optimization']}` | `{row['best_abc_flow']}` | "
                f"{row['node_reduction']} | {preservation_text} | {non_exact} | {row['interpretation']} |"
            )
        lines.extend([
            "",
            "Main caution: this baseline does not prove that ABC produced the same",
            "old-to-new node mappings as the custom flow. Ordinary FRAIG output gives",
            "swept networks and statistics, not correspondence provenance.",
        ])
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def make_recovery_plot(rows: list[dict[str, str]]) -> str | None:
    if not rows:
        return None
    from PIL import Image, ImageDraw, ImageFont

    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    width, height = 1200, 620
    margin_l, margin_r, margin_t, margin_b = 80, 40, 70, 170
    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default()
    draw.text((margin_l, 25), "Exploratory ABC-native reductions vs custom recovery", fill="black", font=font)
    plot_w = width - margin_l - margin_r
    plot_h = height - margin_t - margin_b
    base_y = margin_t + plot_h
    draw.line((margin_l, margin_t, margin_l, base_y), fill="black")
    draw.line((margin_l, base_y, width - margin_r, base_y), fill="black")
    max_abc = max([to_float(r.get("node_reduction")) for r in rows] + [1])
    max_custom = max([to_float(r.get("preserved_signature_fraction")) * 100 for r in rows] + [1])
    group_w = plot_w / max(len(rows), 1)
    bar_w = max(4, int(group_w * 0.25))
    for i, row in enumerate(rows):
        x = margin_l + i * group_w + group_w * 0.2
        abc_h = int((to_float(row.get("node_reduction")) / max_abc) * (plot_h - 20))
        custom_pct = to_float(row.get("preserved_signature_fraction")) * 100
        custom_h = int((custom_pct / max_custom) * (plot_h - 20))
        draw.rectangle((x, base_y - abc_h, x + bar_w, base_y), fill="#0072B2")
        draw.rectangle((x + bar_w + 3, base_y - custom_h, x + 2 * bar_w + 3, base_y), fill="#E69F00")
        draw.text((x, base_y + 8), f"{row['benchmark']}/{row['optimization']}"[:22], fill="black", font=font)
    draw.rectangle((margin_l, height - 55, margin_l + 12, height - 43), fill="#0072B2")
    draw.text((margin_l + 18, height - 58), "ABC node reduction", fill="black", font=font)
    draw.rectangle((margin_l + 180, height - 55, margin_l + 192, height - 43), fill="#E69F00")
    draw.text((margin_l + 198, height - 58), "Custom preservation %, scaled separately", fill="black", font=font)
    out = PLOTS_DIR / "abc_native_vs_custom_recovery.png"
    img.save(out)
    return out.relative_to(ROOT).as_posix()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args(argv)
    rows = build_comparison()
    write_csv_rows(rows)
    write_markdown(rows)
    plot = make_recovery_plot(rows)
    print(f"Wrote {COMPARISON_CSV.relative_to(ROOT)}")
    print(f"Wrote {COMPARISON_MD.relative_to(ROOT)}")
    if plot:
        print(f"Wrote {plot}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
