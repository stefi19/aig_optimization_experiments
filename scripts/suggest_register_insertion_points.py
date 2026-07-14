#!/usr/bin/env python3
"""Suggest engineer-review register insertion points from mapped critical paths."""

from __future__ import annotations

import argparse
import csv
import math
import shutil
import struct
import sys
import zlib
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from contextual_error_metrics import category_display_label, normalize_mapping_category  # noqa: E402

RESULTS = ROOT / "results"
PLOTS = RESULTS / "plots"
PRESENTATION_PLOTS = ROOT / "docs" / "presentation" / "assets" / "plots"

INPUT_CSV = RESULTS / "critical_path_mapping.csv"
SUGGESTIONS_CSV = RESULTS / "register_insertion_suggestions.csv"
SUGGESTIONS_MD = RESULTS / "register_insertion_suggestions.md"

OUTPUT_COLUMNS = [
    "benchmark",
    "optimization",
    "suggested_original_node",
    "optimized_path_node",
    "path_index",
    "path_length",
    "split_balance_score",
    "mapping_category",
    "confidence_score",
    "explanation",
    "caveats",
]

CATEGORY_CONFIDENCE = {
    "exact_signature_match": 1.00,
    "complemented_equivalence": 0.95,
    "sat_cec_proven_equivalent": 0.90,
    "odc_valid_correspondence": 0.85,
    "contextually_approximate_exact": 0.75,
    "contextually_approximate_sampled": 0.60,
    "global_approximate_near_match": 0.55,
    "unresolved": 0.00,
}

CATEGORY_LABEL = {
    "exact_signature_match": "signature match",
    "complemented_equivalence": "complemented equivalence",
    "sat_cec_proven_equivalent": "SAT/CEC-proven equivalent correspondence",
    "odc_valid_correspondence": "ODC-valid contextual correspondence",
    "contextually_approximate_exact": "exact contextual approximation",
    "contextually_approximate_sampled": "sampled contextual approximation",
    "global_approximate_near_match": "global approximate near-match",
}


@dataclass(frozen=True)
class Suggestion:
    benchmark: str
    optimization: str
    suggested_original_node: str
    optimized_path_node: str
    path_index: int
    path_length: int
    split_balance_score: float
    mapping_category: str
    confidence_score: float
    explanation: str
    caveats: str

    def as_row(self) -> dict[str, str]:
        return {
            "benchmark": self.benchmark,
            "optimization": self.optimization,
            "suggested_original_node": self.suggested_original_node,
            "optimized_path_node": self.optimized_path_node,
            "path_index": str(self.path_index),
            "path_length": str(self.path_length),
            "split_balance_score": f"{self.split_balance_score:.3f}",
            "mapping_category": self.mapping_category,
            "confidence_score": f"{self.confidence_score:.3f}",
            "explanation": self.explanation,
            "caveats": self.caveats,
        }


def parse_float(value: str | None, default: float = 0.0) -> float:
    if value is None or value == "":
        return default
    try:
        parsed = float(value)
    except ValueError:
        return default
    if math.isnan(parsed) or math.isinf(parsed):
        return default
    return parsed


def parse_int(value: str | None, default: int = 0) -> int:
    if value is None or value == "":
        return default
    try:
        return int(float(value))
    except ValueError:
        return default


def split_balance_score(path_index: int, path_length: int) -> float:
    """Return 1 near the middle of the path and 0 near either end."""
    if path_length <= 1:
        return 0.0
    left = max(path_index - 1, 0)
    right = max(path_length - path_index, 0)
    smaller = min(left, right)
    larger = max(left, right)
    if larger == 0:
        return 0.0
    return smaller / larger


def category_confidence(category: str) -> float:
    return CATEGORY_CONFIDENCE.get(normalize_mapping_category(category), 0.0)


def heuristic_support(row: dict[str, str]) -> float:
    values = [
        parse_float(row.get("combined_score")),
        parse_float(row.get("support_overlap")),
        parse_float(row.get("simulation_similarity")),
    ]
    present = [value for value in values if value > 0]
    if not present:
        return 0.0
    return max(0.0, min(sum(present) / len(present), 1.0))


def score_candidate(row: dict[str, str]) -> float:
    category = normalize_mapping_category(row.get("mapping_category", ""))
    if category == "unresolved" or not row.get("mapped_original_node"):
        return 0.0
    path_index = parse_int(row.get("path_index"))
    path_length = parse_int(row.get("path_length"))
    balance = split_balance_score(path_index, path_length)
    category_score = category_confidence(category)
    existing_confidence = max(0.0, min(parse_float(row.get("confidence")), 1.0))
    support_score = heuristic_support(row)
    distance = parse_float(row.get("distance"), default=0.0)
    distance_penalty = min(max(distance, 0.0), 1.0) * 0.15 if category == "global_approximate_near_match" else 0.0
    score = (
        0.45 * balance
        + 0.40 * category_score
        + 0.10 * existing_confidence
        + 0.05 * support_score
        - distance_penalty
    )
    return max(0.0, min(score, 1.0))


def candidate_caveats(row: dict[str, str]) -> str:
    category = normalize_mapping_category(row.get("mapping_category", ""))
    caveats = [
        "Research prototype only; no RTL rewrite or sequential verification performed.",
        "Engineer must check latency, control/data dependencies, reset, and enables.",
    ]
    if category in {"contextually_approximate_sampled", "global_approximate_near_match"}:
        caveats.append("Mapping is approximate and should not be treated as proof.")
    if row.get("distance"):
        caveats.append(f"Approximate/global distance recorded as {row['distance']}.")
    return " ".join(caveats)


def candidate_explanation(row: dict[str, str], score: float) -> str:
    path_index = parse_int(row.get("path_index"))
    path_length = parse_int(row.get("path_length"))
    balance = split_balance_score(path_index, path_length)
    category = normalize_mapping_category(row.get("mapping_category", ""))
    label = CATEGORY_LABEL.get(category, category or "mapped")
    return (
        f"Candidate is near the path midpoint ({path_index}/{path_length}, "
        f"balance {balance:.3f}) and has {label}; prototype score {score:.3f}."
    )


def group_key(row: dict[str, str]) -> tuple[str, str]:
    return row.get("benchmark", ""), row.get("optimization", "")


def load_mapping_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def build_suggestions(rows: list[dict[str, str]], top_per_path: int = 1, min_path_length: int = 4) -> list[Suggestion]:
    grouped: dict[tuple[str, str], list[dict[str, str]]] = {}
    for row in rows:
        path_length = parse_int(row.get("path_length"))
        if path_length < min_path_length:
            continue
        row["mapping_category"] = normalize_mapping_category(row.get("mapping_category", ""))
        if row.get("mapping_category") == "unresolved" or not row.get("mapped_original_node"):
            continue
        grouped.setdefault(group_key(row), []).append(row)

    suggestions: list[Suggestion] = []
    for key in sorted(grouped):
        candidates = grouped[key]
        ranked = sorted(
            candidates,
            key=lambda row: (
                score_candidate(row),
                split_balance_score(parse_int(row.get("path_index")), parse_int(row.get("path_length"))),
                category_confidence(row.get("mapping_category", "")),
            ),
            reverse=True,
        )
        for row in ranked[:top_per_path]:
            score = score_candidate(row)
            path_index = parse_int(row.get("path_index"))
            path_length = parse_int(row.get("path_length"))
            suggestions.append(
                Suggestion(
                    benchmark=row.get("benchmark", ""),
                    optimization=row.get("optimization", ""),
                    suggested_original_node=row.get("mapped_original_node", ""),
                    optimized_path_node=row.get("optimized_node", ""),
                    path_index=path_index,
                    path_length=path_length,
                    split_balance_score=split_balance_score(path_index, path_length),
                    mapping_category=normalize_mapping_category(row.get("mapping_category", "")),
                    confidence_score=score,
                    explanation=candidate_explanation(row, score),
                    caveats=candidate_caveats(row),
                )
            )
    suggestions.sort(key=lambda item: (item.confidence_score, item.split_balance_score), reverse=True)
    return suggestions


def write_csv(suggestions: list[Suggestion], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        for suggestion in suggestions:
            writer.writerow(suggestion.as_row())


def write_markdown(suggestions: list[Suggestion], path: Path, example_count: int = 5) -> None:
    lines = [
        "# Register Insertion Suggestion Prototype",
        "",
        "These rows are candidate locations for engineer review. They are not automatic RTL edits.",
        "",
        f"- Suggestions generated: `{len(suggestions)}`",
        "- Scoring favors path-midpoint balance, formal or higher-confidence mappings, existing confidence, and support/simulation signals.",
        "- Unresolved path nodes are excluded.",
        "",
        "## Example Suggestions",
        "",
        "| Benchmark | Optimization | Original node | Optimized node | Path position | Category | Score |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for suggestion in suggestions[:example_count]:
        lines.append(
            f"| `{suggestion.benchmark}` | `{suggestion.optimization}` | "
            f"`{suggestion.suggested_original_node}` | `{suggestion.optimized_path_node}` | "
            f"`{suggestion.path_index}/{suggestion.path_length}` | {category_display_label(suggestion.mapping_category)} (`{suggestion.mapping_category}`) | "
            f"`{suggestion.confidence_score:.3f}` |"
        )
    if not suggestions:
        lines.append("| n/a | n/a | n/a | n/a | n/a | n/a | n/a |")
    lines.extend(
        [
            "",
            "## Caveat",
            "",
            "A real register insertion must update RTL and verify the resulting sequential behavior.",
            "This prototype only ranks places on mapped critical paths where an engineer might start looking.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_png(path: Path, width: int, height: int, pixels: bytearray) -> None:
    def chunk(kind: bytes, data: bytes) -> bytes:
        return (
            struct.pack(">I", len(data))
            + kind
            + data
            + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
        )

    raw = bytearray()
    row_bytes = width * 3
    for y in range(height):
        raw.append(0)
        start = y * row_bytes
        raw.extend(pixels[start : start + row_bytes])
    path.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(bytes(raw), level=9))
        + chunk(b"IEND", b"")
    )


def fill_rect(
    pixels: bytearray,
    width: int,
    height: int,
    left: int,
    top: int,
    right: int,
    bottom: int,
    color: tuple[int, int, int],
) -> None:
    for y in range(max(0, top), min(height, bottom)):
        for x in range(max(0, left), min(width, right)):
            idx = (y * width + x) * 3
            pixels[idx : idx + 3] = bytes(color)


def write_bar_png(path: Path, values: list[float], max_value: float, color: tuple[int, int, int]) -> None:
    width, height = 760, 420
    pixels = bytearray([255] * width * height * 3)
    axis = (45, 55, 72)
    grid = (225, 232, 240)
    left, right, top, bottom = 58, width - 26, 36, height - 48
    for frac in [0.25, 0.5, 0.75, 1.0]:
        y = bottom - int((bottom - top) * frac)
        fill_rect(pixels, width, height, left, y, right, y + 1, grid)
    fill_rect(pixels, width, height, left, top, left + 2, bottom, axis)
    fill_rect(pixels, width, height, left, bottom, right, bottom + 2, axis)
    if values:
        gap = 16
        bar_w = max(18, (right - left - gap * (len(values) + 1)) // len(values))
        for idx, value in enumerate(values):
            x0 = left + gap + idx * (bar_w + gap)
            bar_h = int((bottom - top) * min(value / max_value if max_value else 0.0, 1.0))
            fill_rect(pixels, width, height, x0, bottom - bar_h, x0 + bar_w, bottom, color)
    write_png(path, width, height, pixels)


def write_plots(suggestions: list[Suggestion]) -> list[Path]:
    PLOTS.mkdir(parents=True, exist_ok=True)
    category_counts: dict[str, int] = {}
    for suggestion in suggestions:
        category_counts[suggestion.mapping_category] = category_counts.get(suggestion.mapping_category, 0) + 1
    category_values = [category_counts[key] for key in sorted(category_counts)]
    category_plot = PLOTS / "register_suggestion_categories.png"
    write_bar_png(category_plot, category_values, max(category_values) if category_values else 1, (76, 120, 168))

    confidence_values = [suggestion.confidence_score for suggestion in suggestions[:20]]
    confidence_plot = PLOTS / "register_suggestion_confidence.png"
    write_bar_png(confidence_plot, confidence_values, 1.0, (84, 162, 75))

    PRESENTATION_PLOTS.mkdir(parents=True, exist_ok=True)
    for plot in [category_plot, confidence_plot]:
        shutil.copy2(plot, PRESENTATION_PLOTS / plot.name)
    return [category_plot, confidence_plot]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=INPUT_CSV)
    parser.add_argument("--csv", type=Path, default=SUGGESTIONS_CSV)
    parser.add_argument("--md", type=Path, default=SUGGESTIONS_MD)
    parser.add_argument("--top-per-path", type=int, default=1)
    parser.add_argument("--min-path-length", type=int, default=4)
    args = parser.parse_args()

    rows = load_mapping_rows(args.input)
    suggestions = build_suggestions(rows, top_per_path=args.top_per_path, min_path_length=args.min_path_length)
    write_csv(suggestions, args.csv)
    write_markdown(suggestions, args.md)
    plots = write_plots(suggestions)
    print(f"Wrote {args.csv}")
    print(f"Wrote {args.md}")
    for plot in plots:
        print(f"Wrote {plot}")
    print(f"Suggestions generated: {len(suggestions)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
