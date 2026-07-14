#!/usr/bin/env python3
"""Compare structural and delay-weighted critical-path back-mapping."""

from __future__ import annotations

import argparse
import csv
import shutil
import struct
import sys
import tempfile
import zlib
from dataclasses import asdict, dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from analyze_blif_matches import BlifNetwork, BlifNode, parse_blif  # noqa: E402
from abc_native_sat_sweep_baseline import OPT_COMMANDS  # noqa: E402
from probe_abc_sat_sweeping import find_abc, run_abc_script  # noqa: E402


RESULTS = ROOT / "results"
PLOTS = RESULTS / "plots"
TIMING_PATH_CSV = RESULTS / "timing_path_probe.csv"
TIMING_PATH_MD = RESULTS / "timing_path_probe.md"
COMPARE_CSV = RESULTS / "timing_vs_structural_mapping.csv"
COMPARE_MD = RESULTS / "timing_vs_structural_mapping.md"

TOP_CANDIDATES = RESULTS / "top_candidates.csv"
SAT_CANDIDATES = RESULTS / "sat_verified_candidates.csv"
COMPLEMENT_FILES = [
    RESULTS / "sat_complement_rank1_nonexact.csv",
    RESULTS / "sat_complement_topk_nonexact.csv",
]
APPROX_FILES = [
    RESULTS / "approximate_distance_exact.csv",
    RESULTS / "approximate_distance_sampled.csv",
]

DEFAULT_CIRCUITS = ("c432", "c2670", "c6288")
DEFAULT_OPTIMIZATIONS = ["rewrite"]
DEFAULT_APPROX_THRESHOLD = 0.05


@dataclass(frozen=True)
class DelayPathNode:
    node: str
    path_index: int
    structural_level: int
    node_delay: float
    arrival_time: float


@dataclass(frozen=True)
class MappingChoice:
    category: str
    original_node: str = ""
    confidence: float | None = None
    distance: float | None = None
    explanation: str = ""


@dataclass
class TimingPathRow:
    benchmark: str
    circuit: str
    optimization: str
    path_type: str
    path_length: int
    path_index: int
    optimized_node: str
    structural_level: int
    node_delay: float
    arrival_time: float
    mapped_original_node: str
    mapping_category: str
    confidence: float | None
    distance: float | None
    explanation: str


@dataclass
class TimingComparisonRow:
    benchmark: str
    circuit: str
    optimization: str
    structural_path_length: int
    delay_weighted_path_length: int
    structural_mapped_fraction: float
    delay_weighted_mapped_fraction: float
    structural_unresolved_fraction: float
    delay_weighted_unresolved_fraction: float
    shared_node_count: int
    shared_node_jaccard: float
    delay_path_total_delay: float
    structural_path_total_proxy_delay: float


def maybe_float(value: object) -> float | None:
    if value in (None, "", "nan"):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def maybe_int(value: object) -> int | None:
    if value in (None, "", "nan"):
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def classify_node_delay(node: BlifNode, fanin_penalty: float = 0.2) -> float:
    fanin = len(node.inputs)
    if fanin == 0:
        return 0.0
    if fanin <= 2:
        return 1.0
    return 1.0 + fanin_penalty * max(0, fanin - 2)


def node_lookup(net: BlifNetwork) -> dict[str, BlifNode]:
    return {node.output: node for node in net.nodes}


def compute_levels_and_predecessors(net: BlifNetwork) -> tuple[dict[str, int], dict[str, str | None]]:
    levels: dict[str, int] = {name: 0 for name in net.inputs}
    predecessor: dict[str, str | None] = {name: None for name in net.inputs}
    internal_outputs = {node.output for node in net.nodes}
    for node in net.nodes:
        best_fanin = None
        best_level = -1
        for fanin in node.inputs:
            fanin_level = levels.get(fanin, 0)
            if fanin_level > best_level:
                best_level = fanin_level
                best_fanin = fanin if fanin in internal_outputs else None
        levels[node.output] = max(0, best_level + 1)
        predecessor[node.output] = best_fanin
    return levels, predecessor


def extract_structural_path(net: BlifNetwork, fanin_penalty: float = 0.2) -> list[DelayPathNode]:
    internal_outputs = {node.output for node in net.nodes}
    if not internal_outputs:
        return []
    lookup = node_lookup(net)
    levels, predecessor = compute_levels_and_predecessors(net)
    output_roots = [output for output in net.outputs if output in internal_outputs]
    roots = output_roots or list(internal_outputs)
    sink = max(roots, key=lambda name: (levels.get(name, 0), name))
    path: list[str] = []
    current: str | None = sink
    seen: set[str] = set()
    while current and current in internal_outputs and current not in seen:
        seen.add(current)
        path.append(current)
        current = predecessor.get(current)
    path.reverse()
    return [
        DelayPathNode(
            node=name,
            path_index=index,
            structural_level=levels.get(name, 0),
            node_delay=classify_node_delay(lookup[name], fanin_penalty) if name in lookup else 0.0,
            arrival_time=float(levels.get(name, 0)),
        )
        for index, name in enumerate(path, start=1)
    ]


def compute_delay_weighted_path(net: BlifNetwork, fanin_penalty: float = 0.2) -> list[DelayPathNode]:
    internal_outputs = {node.output for node in net.nodes}
    if not internal_outputs:
        return []
    levels, _ = compute_levels_and_predecessors(net)
    arrival: dict[str, float] = {name: 0.0 for name in net.inputs}
    predecessor: dict[str, str | None] = {name: None for name in net.inputs}
    delay_by_node: dict[str, float] = {}
    for node in net.nodes:
        best_fanin = None
        best_arrival = 0.0
        for fanin in node.inputs:
            fanin_arrival = arrival.get(fanin, 0.0)
            if fanin_arrival > best_arrival:
                best_arrival = fanin_arrival
                best_fanin = fanin if fanin in internal_outputs else None
        delay = classify_node_delay(node, fanin_penalty)
        delay_by_node[node.output] = delay
        arrival[node.output] = best_arrival + delay
        predecessor[node.output] = best_fanin

    output_roots = [output for output in net.outputs if output in internal_outputs]
    roots = output_roots or list(internal_outputs)
    sink = max(roots, key=lambda name: (arrival.get(name, 0.0), levels.get(name, 0), name))
    path: list[str] = []
    current: str | None = sink
    seen: set[str] = set()
    while current and current in internal_outputs and current not in seen:
        seen.add(current)
        path.append(current)
        current = predecessor.get(current)
    path.reverse()
    return [
        DelayPathNode(
            node=name,
            path_index=index,
            structural_level=levels.get(name, 0),
            node_delay=delay_by_node.get(name, 0.0),
            arrival_time=arrival.get(name, 0.0),
        )
        for index, name in enumerate(path, start=1)
    ]


def source_blif_for_benchmark(benchmark: str) -> Path | None:
    if benchmark.startswith("external_iscas85_"):
        circuit = benchmark.replace("external_iscas85_", "")
        path = ROOT / "benchmarks" / "external" / "iscas85" / f"{circuit}.blif"
        return path if path.exists() else None
    path = ROOT / "benchmarks" / f"{benchmark}.blif"
    return path if path.exists() else None


def ensure_optimized_blif(abc_bin: str, benchmark: str, optimization: str, tmp: Path) -> Path | None:
    existing = ROOT / "variants" / f"{benchmark}_{optimization}.blif"
    if existing.exists():
        return existing
    source = source_blif_for_benchmark(benchmark)
    command = OPT_COMMANDS.get(optimization)
    if source is None or command is None:
        return None
    out = tmp / f"{benchmark}_{optimization}.blif"
    if out.exists():
        return out
    exit_code, _output = run_abc_script(
        abc_bin,
        f"read_blif {source}\n{command}\nwrite_blif {out}\n",
        timeout=60,
    )
    return out if exit_code == 0 and out.exists() else None


def load_mapping_tables(threshold: float) -> dict[str, list[dict[str, str]]]:
    exact = [row for row in read_csv_rows(TOP_CANDIDATES) if row.get("match_category") == "exact_anchor"]
    complemented: list[dict[str, str]] = []
    for path in COMPLEMENT_FILES:
        complemented.extend(row for row in read_csv_rows(path) if row.get("complement_status") == "verified")
    sat_verified = [
        row
        for row in read_csv_rows(SAT_CANDIDATES)
        if row.get("sat_status") == "verified" and row.get("match_category") == "non_exact_candidate"
    ]
    approximate: list[dict[str, str]] = []
    for path in APPROX_FILES:
        for row in read_csv_rows(path):
            distance = maybe_float(row.get("distance"))
            if row.get("sat_status") == "rejected" and distance is not None and distance <= threshold:
                approximate.append(row)
    return {"exact": exact, "complemented": complemented, "sat_verified": sat_verified, "approximate": approximate}


def matching_rows(rows: list[dict[str, str]], benchmark: str, optimization: str, optimized_node: str) -> list[dict[str, str]]:
    return [
        row
        for row in rows
        if row.get("benchmark") == benchmark
        and row.get("optimization") == optimization
        and row.get("optimized_node") == optimized_node
    ]


def best_ranked_row(rows: list[dict[str, str]]) -> dict[str, str] | None:
    if not rows:
        return None
    return sorted(
        rows,
        key=lambda row: (
            maybe_int(row.get("rank")) if maybe_int(row.get("rank")) is not None else 10**9,
            -(maybe_float(row.get("combined_score")) or 0.0),
            -(maybe_float(row.get("support_overlap")) or 0.0),
            -(maybe_float(row.get("simulation_similarity")) or 0.0),
        ),
    )[0]


def choice_from_row(category: str, row: dict[str, str], explanation: str) -> MappingChoice:
    distance = maybe_float(row.get("distance"))
    similarity = maybe_float(row.get("similarity"))
    confidence = 1.0 if category in {"exact", "complemented", "sat_verified_nonexact"} else similarity
    if confidence is None:
        confidence = maybe_float(row.get("combined_score"))
    return MappingChoice(category, row.get("original_candidate", ""), confidence, distance, explanation)


def map_node(benchmark: str, optimization: str, optimized_node: str, tables: dict[str, list[dict[str, str]]]) -> MappingChoice:
    row = best_ranked_row(matching_rows(tables["exact"], benchmark, optimization, optimized_node))
    if row is not None:
        return choice_from_row("exact", row, "Exact anchor from top_candidates.")
    row = best_ranked_row(matching_rows(tables["complemented"], benchmark, optimization, optimized_node))
    if row is not None:
        return choice_from_row("complemented", row, "Complemented equivalence was verified.")
    row = best_ranked_row(matching_rows(tables["sat_verified"], benchmark, optimization, optimized_node))
    if row is not None:
        return choice_from_row("sat_verified_nonexact", row, "SAT/CEC verified non-exact correspondence.")
    approx_rows = matching_rows(tables["approximate"], benchmark, optimization, optimized_node)
    if approx_rows:
        row = sorted(approx_rows, key=lambda item: (maybe_float(item.get("distance")) or 1.0, -(maybe_float(item.get("combined_score")) or 0.0)))[0]
        return choice_from_row("approximate_near_match", row, "Closest approximate-distance candidate.")
    return MappingChoice("unresolved", explanation="No exact, complemented, SAT-verified, or near-distance candidate was available.")


def mapped_fraction(categories: list[str]) -> float:
    return sum(category != "unresolved" for category in categories) / len(categories) if categories else 0.0


def path_proxy_delay(path_nodes: list[str], lookup: dict[str, BlifNode], fanin_penalty: float) -> float:
    return sum(classify_node_delay(lookup[name], fanin_penalty) for name in path_nodes if name in lookup)


def rows_for_case(
    abc_bin: str,
    benchmark: str,
    optimization: str,
    tmp: Path,
    tables: dict[str, list[dict[str, str]]],
    fanin_penalty: float,
) -> tuple[list[TimingPathRow], TimingComparisonRow | None]:
    blif = ensure_optimized_blif(abc_bin, benchmark, optimization, tmp)
    if blif is None:
        return [], None
    net = parse_blif(blif)
    lookup = node_lookup(net)
    structural = extract_structural_path(net, fanin_penalty)
    delay_path = compute_delay_weighted_path(net, fanin_penalty)
    rows: list[TimingPathRow] = []
    categories: dict[str, list[str]] = {"structural": [], "delay_weighted": []}
    for path_type, nodes in [("structural", structural), ("delay_weighted", delay_path)]:
        for node in nodes:
            choice = map_node(benchmark, optimization, node.node, tables)
            categories[path_type].append(choice.category)
            rows.append(
                TimingPathRow(
                    benchmark=benchmark,
                    circuit=benchmark.replace("external_iscas85_", ""),
                    optimization=optimization,
                    path_type=path_type,
                    path_length=len(nodes),
                    path_index=node.path_index,
                    optimized_node=node.node,
                    structural_level=node.structural_level,
                    node_delay=node.node_delay,
                    arrival_time=node.arrival_time,
                    mapped_original_node=choice.original_node,
                    mapping_category=choice.category,
                    confidence=choice.confidence,
                    distance=choice.distance,
                    explanation=choice.explanation,
                )
            )

    structural_nodes = [node.node for node in structural]
    delay_nodes = [node.node for node in delay_path]
    shared = set(structural_nodes) & set(delay_nodes)
    union = set(structural_nodes) | set(delay_nodes)
    comparison = TimingComparisonRow(
        benchmark=benchmark,
        circuit=benchmark.replace("external_iscas85_", ""),
        optimization=optimization,
        structural_path_length=len(structural_nodes),
        delay_weighted_path_length=len(delay_nodes),
        structural_mapped_fraction=mapped_fraction(categories["structural"]),
        delay_weighted_mapped_fraction=mapped_fraction(categories["delay_weighted"]),
        structural_unresolved_fraction=1.0 - mapped_fraction(categories["structural"]),
        delay_weighted_unresolved_fraction=1.0 - mapped_fraction(categories["delay_weighted"]),
        shared_node_count=len(shared),
        shared_node_jaccard=len(shared) / len(union) if union else 0.0,
        delay_path_total_delay=max((node.arrival_time for node in delay_path), default=0.0),
        structural_path_total_proxy_delay=path_proxy_delay(structural_nodes, lookup, fanin_penalty),
    )
    return rows, comparison


def run_probe(
    abc_bin: str,
    circuits: list[str],
    optimizations: list[str],
    approx_threshold: float,
    fanin_penalty: float,
) -> tuple[list[TimingPathRow], list[TimingComparisonRow]]:
    tables = load_mapping_tables(approx_threshold)
    path_rows: list[TimingPathRow] = []
    comparisons: list[TimingComparisonRow] = []
    with tempfile.TemporaryDirectory(prefix="timing_path_probe_") as td:
        tmp = Path(td)
        for circuit in circuits:
            benchmark = f"external_iscas85_{circuit}"
            for optimization in optimizations:
                rows, comparison = rows_for_case(abc_bin, benchmark, optimization, tmp, tables, fanin_penalty)
                path_rows.extend(rows)
                if comparison is not None:
                    comparisons.append(comparison)
    return path_rows, comparisons


def write_csvs(path_rows: list[TimingPathRow], comparisons: list[TimingComparisonRow]) -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    with TIMING_PATH_CSV.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(TimingPathRow.__annotations__))
        writer.writeheader()
        for row in path_rows:
            writer.writerow(asdict(row))
    with COMPARE_CSV.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(TimingComparisonRow.__annotations__))
        writer.writeheader()
        for row in comparisons:
            writer.writerow(asdict(row))


def markdown_table(rows: list[dict], columns: list[str]) -> str:
    if not rows:
        return ""
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join("---" for _ in columns) + " |"]
    for row in rows:
        values = []
        for column in columns:
            value = row.get(column, "")
            values.append(f"{value:.3f}" if isinstance(value, float) else str(value))
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def write_markdown(path_rows: list[TimingPathRow], comparisons: list[TimingComparisonRow]) -> None:
    if comparisons:
        mean_struct = sum(row.structural_mapped_fraction for row in comparisons) / len(comparisons)
        mean_delay = sum(row.delay_weighted_mapped_fraction for row in comparisons) / len(comparisons)
        mean_overlap = sum(row.shared_node_jaccard for row in comparisons) / len(comparisons)
    else:
        mean_struct = mean_delay = mean_overlap = 0.0
    case_rows = [
        {
            "circuit": row.circuit,
            "optimization": row.optimization,
            "structural_path_length": row.structural_path_length,
            "delay_weighted_path_length": row.delay_weighted_path_length,
            "structural_mapped_fraction": row.structural_mapped_fraction,
            "delay_weighted_mapped_fraction": row.delay_weighted_mapped_fraction,
            "shared_node_jaccard": row.shared_node_jaccard,
            "delay_path_total_delay": row.delay_path_total_delay,
        }
        for row in comparisons
    ]
    TIMING_PATH_MD.write_text(
        "\n".join(
            [
                "# Timing-Aware Path Probe",
                "",
                "This probe compares the existing structural longest path with a lightweight delay-weighted proxy path.",
                "It does not use real physical timing or a mapped technology library.",
                "",
                f"- Case studies: {len(comparisons)}",
                f"- Mean structural mapped fraction: {mean_struct:.3f}",
                f"- Mean delay-weighted mapped fraction: {mean_delay:.3f}",
                f"- Mean path node Jaccard overlap: {mean_overlap:.3f}",
                "",
                "## Case Summary",
                "",
                markdown_table(
                    case_rows,
                    [
                        "circuit",
                        "optimization",
                        "structural_path_length",
                        "delay_weighted_path_length",
                        "structural_mapped_fraction",
                        "delay_weighted_mapped_fraction",
                        "shared_node_jaccard",
                        "delay_path_total_delay",
                    ],
                ),
                "",
            ]
        ),
        encoding="utf-8",
    )
    COMPARE_MD.write_text(
        "\n".join(
            [
                "# Timing vs Structural Mapping Comparison",
                "",
                "The delay-weighted path uses a configurable proxy delay model over BLIF `.names` nodes.",
                "Treat this as a timing-direction investigation, not library-based static timing analysis.",
                "",
                markdown_table(
                    [
                        {
                            "circuit": row.circuit,
                            "optimization": row.optimization,
                            "structural_mapped_fraction": row.structural_mapped_fraction,
                            "delay_weighted_mapped_fraction": row.delay_weighted_mapped_fraction,
                            "structural_unresolved_fraction": row.structural_unresolved_fraction,
                            "delay_weighted_unresolved_fraction": row.delay_weighted_unresolved_fraction,
                            "shared_node_jaccard": row.shared_node_jaccard,
                        }
                        for row in comparisons
                    ],
                    [
                        "circuit",
                        "optimization",
                        "structural_mapped_fraction",
                        "delay_weighted_mapped_fraction",
                        "structural_unresolved_fraction",
                        "delay_weighted_unresolved_fraction",
                        "shared_node_jaccard",
                    ],
                ),
                "",
            ]
        ),
        encoding="utf-8",
    )


def plot_outputs(path_rows: list[TimingPathRow], comparisons: list[TimingComparisonRow]) -> None:
    if not path_rows or not comparisons:
        return
    PLOTS.mkdir(parents=True, exist_ok=True)
    write_bar_png(
        PLOTS / "timing_vs_structural_path_overlap.png",
        [row.shared_node_jaccard for row in comparisons],
        color=(76, 120, 168),
        max_value=1.0,
    )

    counts: dict[str, int] = {}
    for row in path_rows:
        if row.path_type == "delay_weighted":
            counts[row.mapping_category] = counts.get(row.mapping_category, 0) + 1
    write_bar_png(
        PLOTS / "timing_path_mapping_categories.png",
        [counts[key] for key in sorted(counts)],
        color=(84, 162, 75),
        max_value=max(counts.values()) if counts else 1,
    )

    by_circuit: dict[str, list[TimingComparisonRow]] = {}
    for row in comparisons:
        by_circuit.setdefault(row.circuit, []).append(row)
    circuits = sorted(by_circuit)
    structural_vals = [sum(row.structural_mapped_fraction for row in by_circuit[circuit]) / len(by_circuit[circuit]) for circuit in circuits]
    delay_vals = [sum(row.delay_weighted_mapped_fraction for row in by_circuit[circuit]) / len(by_circuit[circuit]) for circuit in circuits]
    write_grouped_bar_png(
        PLOTS / "timing_path_mapped_fraction_by_circuit.png",
        structural_vals,
        delay_vals,
        max_value=1.0,
    )


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


def set_pixel(pixels: bytearray, width: int, height: int, x: int, y: int, color: tuple[int, int, int]) -> None:
    if 0 <= x < width and 0 <= y < height:
        idx = (y * width + x) * 3
        pixels[idx : idx + 3] = bytes(color)


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
            set_pixel(pixels, width, height, x, y, color)


def write_bar_png(path: Path, values: list[float], color: tuple[int, int, int], max_value: float) -> None:
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
        for i, value in enumerate(values):
            x0 = left + gap + i * (bar_w + gap)
            bar_h = int((bottom - top) * min(value / max_value if max_value else 0, 1.0))
            fill_rect(pixels, width, height, x0, bottom - bar_h, x0 + bar_w, bottom, color)
    write_png(path, width, height, pixels)


def write_grouped_bar_png(path: Path, left_values: list[float], right_values: list[float], max_value: float) -> None:
    width, height = 760, 420
    pixels = bytearray([255] * width * height * 3)
    axis = (45, 55, 72)
    left, right, top, bottom = 58, width - 26, 36, height - 48
    fill_rect(pixels, width, height, left, top, left + 2, bottom, axis)
    fill_rect(pixels, width, height, left, bottom, right, bottom + 2, axis)
    groups = max(len(left_values), 1)
    group_w = (right - left) // groups
    bar_w = max(16, group_w // 4)
    for i, (a, b) in enumerate(zip(left_values, right_values)):
        center = left + i * group_w + group_w // 2
        for value, color, offset in [(a, (76, 120, 168), -bar_w), (b, (245, 133, 24), 2)]:
            bar_h = int((bottom - top) * min(value / max_value if max_value else 0, 1.0))
            fill_rect(pixels, width, height, center + offset, bottom - bar_h, center + offset + bar_w, bottom, color)
    write_png(path, width, height, pixels)


def copy_plots_to_presentation() -> None:
    target = ROOT / "docs" / "presentation" / "assets" / "plots"
    target.mkdir(parents=True, exist_ok=True)
    for name in [
        "timing_vs_structural_path_overlap.png",
        "timing_path_mapping_categories.png",
        "timing_path_mapped_fraction_by_circuit.png",
    ]:
        src = PLOTS / name
        if src.exists():
            shutil.copyfile(src, target / name)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--abc", help="Path to ABC binary. Defaults to $ABC or .abc_build/abc_repo/abc.")
    parser.add_argument("--circuits", nargs="+", default=list(DEFAULT_CIRCUITS))
    parser.add_argument("--optimizations", nargs="+", default=DEFAULT_OPTIMIZATIONS)
    parser.add_argument("--approx-threshold", type=float, default=DEFAULT_APPROX_THRESHOLD)
    parser.add_argument("--fanin-penalty", type=float, default=0.2)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    abc_bin = find_abc(args.abc)
    path_rows, comparisons = run_probe(
        abc_bin=abc_bin,
        circuits=args.circuits,
        optimizations=args.optimizations,
        approx_threshold=args.approx_threshold,
        fanin_penalty=args.fanin_penalty,
    )
    write_csvs(path_rows, comparisons)
    write_markdown(path_rows, comparisons)
    plot_outputs(path_rows, comparisons)
    copy_plots_to_presentation()
    print(f"Wrote {TIMING_PATH_CSV.relative_to(ROOT)}")
    print(f"Wrote {TIMING_PATH_MD.relative_to(ROOT)}")
    print(f"Wrote {COMPARE_CSV.relative_to(ROOT)}")
    print(f"Wrote {COMPARE_MD.relative_to(ROOT)}")
    if comparisons:
        print(f"Case studies: {len(comparisons)}")
        print(f"Mean path overlap: {sum(row.shared_node_jaccard for row in comparisons) / len(comparisons):.3f}")
        print(f"Mean delay-weighted mapped fraction: {sum(row.delay_weighted_mapped_fraction for row in comparisons) / len(comparisons):.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
