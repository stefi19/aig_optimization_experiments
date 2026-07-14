#!/usr/bin/env python3
"""Run contextual output-error analysis for selected internal-node candidates."""

from __future__ import annotations

import argparse
import csv
import shutil
import subprocess
import sys
import tempfile
import time
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from contextual_error_metrics import (  # noqa: E402
    classify_candidate,
    evaluate_contextual_pair,
    run_abc_cec,
    write_blif,
)

RESULTS = ROOT / "results"
PLOTS = RESULTS / "plots"
PRESENTATION_PLOTS = ROOT / "docs" / "presentation" / "assets" / "plots"

DETAIL_CSV = RESULTS / "contextual_error_metrics.csv"
SUMMARY_CSV = RESULTS / "contextual_error_metrics_summary.csv"
SUMMARY_MD = RESULTS / "contextual_error_metrics.md"
CRIT_CSV = RESULTS / "contextual_critical_path_mapping.csv"
CRIT_MD = RESULTS / "contextual_critical_path_mapping.md"

DEFAULT_CIRCUITS = ["c432", "c2670", "c6288"]
DEFAULT_OPTIMIZATIONS = ["dc2", "compress2rs", "resyn", "resyn2", "resyn2_like", "refactor", "refactor_z", "rewrite_z"]
ABC_COMMANDS = {
    "original": "strash",
    "balance": "strash; balance",
    "rewrite": "strash; rewrite",
    "refactor": "strash; refactor",
    "resub": "strash; resub",
    "resyn2_like": "strash; balance; rewrite; refactor; balance; rewrite -z; refactor -z; balance",
    "rewrite_z": "strash; rewrite -z",
    "refactor_z": "strash; refactor -z",
    "resyn": "strash; balance; rewrite; rewrite -z; balance; rewrite; balance",
    "resyn2": "strash; balance; rewrite; refactor; balance; rewrite -z; refactor -z; balance",
    "dc2": "strash; dc2",
    "compress2rs": "strash; balance; rewrite; refactor; resub; balance; rewrite -z; refactor -z; resub; balance",
}

DETAIL_COLUMNS = [
    "circuit",
    "optimization",
    "optimized_node",
    "candidate_original_node",
    "candidate_source",
    "candidate_rank",
    "combined_score",
    "global_error_rate",
    "global_error_mode",
    "global_pattern_count",
    "contextual_output_error_rate",
    "contextual_error_mode",
    "contextual_pattern_count",
    "mean_output_hamming_distance",
    "worst_case_output_hamming_distance",
    "mean_absolute_output_error",
    "worst_case_absolute_output_error",
    "cec_status",
    "classification",
    "is_formal_global",
    "is_formal_contextual",
    "substitution_status",
    "reason",
    "runtime_seconds",
    "seed",
]


@dataclass(frozen=True)
class Candidate:
    benchmark: str
    circuit: str
    optimization: str
    optimized_node: str
    original_candidate: str
    candidate_source: str
    rank: str
    combined_score: str
    orig_blif: Path
    opt_blif: Path


def find_abc() -> str | None:
    env = None
    try:
        import os

        env = os.environ.get("ABC")
    except OSError:
        env = None
    if env and Path(env).exists():
        return env
    default = ROOT / ".abc_build" / "abc_repo" / "abc"
    if default.exists():
        return str(default)
    return shutil.which("abc")


def variant_path(benchmark: str, optimization: str) -> Path:
    return ROOT / "variants" / f"{benchmark}_{optimization}.blif"


def original_variant_path(benchmark: str) -> Path:
    return ROOT / "variants" / f"{benchmark}_original.blif"


def source_blif_for_benchmark(benchmark: str) -> Path | None:
    if benchmark.startswith("external_iscas85_"):
        circuit = benchmark.replace("external_iscas85_", "")
        path = ROOT / "benchmarks" / "external" / "iscas85" / f"{circuit}.blif"
        return path if path.exists() else None
    for path in [
        ROOT / "benchmarks" / f"{benchmark}.blif",
        ROOT / "benchmarks" / "generated" / f"{benchmark.replace('generated_', '')}.blif",
    ]:
        if path.exists():
            return path
    return None


def run_abc_write_blif(abc_bin: str | None, source: Path, optimization: str, out: Path) -> tuple[bool, str]:
    if not abc_bin:
        return False, "ABC binary unavailable for temporary variant generation"
    command = ABC_COMMANDS.get(optimization)
    if command is None:
        return False, f"unsupported optimization {optimization!r}"
    completed = subprocess.run(
        [abc_bin, "-c", f"read_blif {source}; {command}; write_blif {out}"],
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0 or not out.exists():
        snippet = " ".join(((completed.stdout or "") + " " + (completed.stderr or "")).split())[:300]
        return False, f"ABC temporary variant generation failed: {snippet}"
    return True, "temporary variant generated"


def materialize_candidate_paths(candidate: Candidate, tmp: Path, abc_bin: str | None) -> tuple[Path | None, Path | None, str]:
    orig = candidate.orig_blif if candidate.orig_blif.exists() else None
    opt = candidate.opt_blif if candidate.opt_blif.exists() else None
    source = source_blif_for_benchmark(candidate.benchmark)
    if orig is None:
        if source is None:
            return None, None, f"missing original BLIF and no source found for {candidate.benchmark}"
        orig = source
    if opt is None:
        if source is None:
            return None, None, f"missing optimized BLIF and no source found for {candidate.benchmark}"
        out = tmp / f"{candidate.benchmark}_{candidate.optimization}.blif"
        ok, reason = run_abc_write_blif(abc_bin, source, candidate.optimization, out)
        if not ok:
            return orig, None, reason
        opt = out
    return orig, opt, "ok"


def circuit_from_benchmark(benchmark: str) -> str:
    return benchmark.replace("external_iscas85_", "")


def add_candidate(candidates: list[Candidate], seen: set[tuple[str, str, str, str]], row: dict[str, str], source: str) -> None:
    benchmark = row.get("benchmark", "")
    optimization = row.get("optimization", "")
    optimized_node = row.get("optimized_node", "")
    original_candidate = row.get("original_candidate", "")
    if not (benchmark and optimization and optimized_node and original_candidate):
        return
    key = (benchmark, optimization, optimized_node, original_candidate)
    if key in seen:
        return
    seen.add(key)
    orig_path = Path(row.get("orig_blif") or original_variant_path(benchmark))
    opt_path = Path(row.get("opt_blif") or variant_path(benchmark, optimization))
    if not orig_path.is_absolute():
        orig_path = ROOT / orig_path
    if not opt_path.is_absolute():
        opt_path = ROOT / opt_path
    candidates.append(
        Candidate(
            benchmark=benchmark,
            circuit=row.get("circuit") or circuit_from_benchmark(benchmark),
            optimization=optimization,
            optimized_node=optimized_node,
            original_candidate=original_candidate,
            candidate_source=source,
            rank=row.get("rank", ""),
            combined_score=row.get("combined_score", ""),
            orig_blif=orig_path,
            opt_blif=opt_path,
        )
    )


def read_candidate_file(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def select_candidates(circuits: list[str], optimizations: list[str], max_candidates: int) -> list[Candidate]:
    candidates: list[Candidate] = []
    seen: set[tuple[str, str, str, str]] = set()
    wanted_benchmarks = {f"external_iscas85_{circuit}" for circuit in circuits}
    wanted_opts = set(optimizations)

    sources = [
        (RESULTS / "approximate_distance_exact.csv", "approximate_distance_exact"),
        (RESULTS / "approximate_distance_sampled.csv", "approximate_distance_sampled"),
        (RESULTS / "sat_refinement_candidates.csv", "sat_refinement_candidates"),
        (RESULTS / "sat_topk_nonexact_candidates.csv", "sat_topk_nonexact_candidates"),
    ]
    for path, source in sources:
        rows = read_candidate_file(path)
        rows.sort(
            key=lambda row: (
                row.get("sat_status") != "verified",
                -float(row.get("combined_score") or 0),
                float(row.get("rank") or 999),
            )
        )
        for row in rows:
            if row.get("benchmark") not in wanted_benchmarks:
                continue
            if row.get("optimization") not in wanted_opts:
                continue
            add_candidate(candidates, seen, row, source)
            if len(candidates) >= max_candidates:
                return candidates
    return candidates


def empty_detail_row(candidate: Candidate, status: str, reason: str, runtime: float, seed: int) -> dict[str, object]:
    return {
        "circuit": candidate.circuit,
        "optimization": candidate.optimization,
        "optimized_node": candidate.optimized_node,
        "candidate_original_node": candidate.original_candidate,
        "candidate_source": candidate.candidate_source,
        "candidate_rank": candidate.rank,
        "combined_score": candidate.combined_score,
        "global_error_rate": "",
        "global_error_mode": "",
        "global_pattern_count": "",
        "contextual_output_error_rate": "",
        "contextual_error_mode": "",
        "contextual_pattern_count": "",
        "mean_output_hamming_distance": "",
        "worst_case_output_hamming_distance": "",
        "mean_absolute_output_error": "",
        "worst_case_absolute_output_error": "",
        "cec_status": "not_run",
        "classification": "unresolved",
        "is_formal_global": "false",
        "is_formal_contextual": "false",
        "substitution_status": status,
        "reason": reason,
        "runtime_seconds": f"{runtime:.4f}",
        "seed": str(seed),
    }


def analyze_candidate(candidate: Candidate, args: argparse.Namespace, abc_bin: str | None, tmp: Path) -> dict[str, object]:
    start = time.perf_counter()
    orig_path, opt_path, materialize_reason = materialize_candidate_paths(candidate, tmp, abc_bin)
    if orig_path is None or opt_path is None:
        return empty_detail_row(
            candidate,
            "skipped",
            materialize_reason,
            time.perf_counter() - start,
            args.seed,
        )

    metrics, baseline, substituted = evaluate_contextual_pair(
        orig_path,
        opt_path,
        candidate.optimized_node,
        candidate.original_candidate,
        args.exact_support_cap,
        args.sample_count,
        args.seed,
        args.contextual_error_threshold,
    )
    cec_status = "not_run"
    cec_reason = ""
    if metrics.get("substitution_status") == "ok" and baseline is not None and substituted is not None:
        baseline_path = tmp / f"{candidate.circuit}_{candidate.optimization}_{candidate.optimized_node}_baseline.blif"
        substituted_path = tmp / f"{candidate.circuit}_{candidate.optimization}_{candidate.optimized_node}_substituted.blif"
        write_blif(baseline, baseline_path, "baseline")
        write_blif(substituted, substituted_path, "substituted")
        cec_status, cec_reason = run_abc_cec(abc_bin, baseline_path, substituted_path)
        metrics["cec_status"] = cec_status
        metrics["classification"] = classify_candidate(
            float(metrics["global_error_rate"]),
            bool(metrics["is_formal_global"]),
            float(metrics["contextual_output_error_rate"]),
            bool(metrics["is_formal_contextual"]),
            cec_status,
            args.contextual_error_threshold,
            str(metrics["substitution_status"]),
        )
        metrics["reason"] = cec_reason or "substitution constructed and CEC completed"
    else:
        metrics["cec_status"] = "not_run"

    runtime = time.perf_counter() - start
    return {
        "circuit": candidate.circuit,
        "optimization": candidate.optimization,
        "optimized_node": candidate.optimized_node,
        "candidate_original_node": candidate.original_candidate,
        "candidate_source": candidate.candidate_source,
        "candidate_rank": candidate.rank,
        "combined_score": candidate.combined_score,
        "global_error_rate": metrics.get("global_error_rate", ""),
        "global_error_mode": metrics.get("global_error_mode", ""),
        "global_pattern_count": metrics.get("global_pattern_count", ""),
        "contextual_output_error_rate": metrics.get("contextual_output_error_rate", ""),
        "contextual_error_mode": metrics.get("contextual_error_mode", ""),
        "contextual_pattern_count": metrics.get("contextual_pattern_count", ""),
        "mean_output_hamming_distance": metrics.get("mean_output_hamming_distance", ""),
        "worst_case_output_hamming_distance": metrics.get("worst_case_output_hamming_distance", ""),
        "mean_absolute_output_error": metrics.get("mean_absolute_output_error", ""),
        "worst_case_absolute_output_error": metrics.get("worst_case_absolute_output_error", ""),
        "cec_status": metrics.get("cec_status", cec_status),
        "classification": metrics.get("classification", "unresolved"),
        "is_formal_global": str(metrics.get("is_formal_global", False)).lower(),
        "is_formal_contextual": str(metrics.get("is_formal_contextual", False)).lower(),
        "substitution_status": metrics.get("substitution_status", "skipped"),
        "reason": metrics.get("reason", ""),
        "runtime_seconds": f"{runtime:.4f}",
        "seed": str(args.seed),
    }


def write_rows(path: Path, rows: list[dict[str, object]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in columns})


def summarize(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    counters = Counter(str(row.get("classification", "")) for row in rows)
    modes = Counter(str(row.get("contextual_error_mode", "") or "skipped") for row in rows)
    cec = Counter(str(row.get("cec_status", "")) for row in rows)
    out = []
    for kind, counter in [("classification", counters), ("contextual_mode", modes), ("cec_status", cec)]:
        for name, count in sorted(counter.items()):
            out.append({"summary_type": kind, "name": name, "count": count})
    by_circuit = Counter(str(row.get("circuit", "")) for row in rows)
    for circuit, count in sorted(by_circuit.items()):
        out.append({"summary_type": "circuit", "name": circuit, "count": count})
    by_opt = Counter(str(row.get("optimization", "")) for row in rows)
    for opt, count in sorted(by_opt.items()):
        out.append({"summary_type": "optimization", "name": opt, "count": count})
    return out


def write_markdown(rows: list[dict[str, object]], summary_rows: list[dict[str, object]]) -> None:
    classifications = Counter(str(row.get("classification", "")) for row in rows)
    substitutions = Counter(str(row.get("substitution_status", "")) for row in rows)
    modes = Counter(str(row.get("contextual_error_mode", "") or "skipped") for row in rows)
    examples = [
        row for row in rows
        if row.get("classification") in {"odc_valid_correspondence", "contextually_approximate", "unsafe_candidate", "globally_exact"}
    ][:10]
    lines = [
        "# Contextual Error Metrics",
        "",
        "This experiment compares global internal-node distance with output error after contextual substitution.",
        "Exact exhaustive rows are formal for the reported distance. Sampled rows are estimates.",
        "CEC equivalence results are formal when ABC reports equivalence.",
        "",
        f"- Total candidate pairs: `{len(rows)}`",
        f"- Successfully substituted pairs: `{substitutions.get('ok', 0)}`",
        f"- Skipped/unresolved substitutions: `{len(rows) - substitutions.get('ok', 0)}`",
        f"- Globally exact pairs: `{classifications.get('globally_exact', 0)}`",
        f"- ODC-valid correspondences: `{classifications.get('odc_valid_correspondence', 0)}`",
        f"- Contextually approximate pairs: `{classifications.get('contextually_approximate', 0)}`",
        f"- Unsafe candidates: `{classifications.get('unsafe_candidate', 0)}`",
        f"- Unresolved pairs: `{classifications.get('unresolved', 0)}`",
        f"- Exact contextual rows: `{modes.get('exact', 0)}`",
        f"- Sampled contextual rows: `{modes.get('sampled', 0)}`",
        "",
        "## Classification Counts",
        "",
        "| Classification | Count |",
        "| --- | ---: |",
    ]
    for name, count in sorted(classifications.items()):
        lines.append(f"| `{name}` | {count} |")
    lines.extend(["", "## Examples", "", "| Circuit | Optimization | Optimized node | Candidate | Global error | Contextual error | CEC | Classification |", "| --- | --- | --- | --- | ---: | ---: | --- | --- |"])
    for row in examples:
        lines.append(
            f"| `{row.get('circuit')}` | `{row.get('optimization')}` | `{row.get('optimized_node')}` | "
            f"`{row.get('candidate_original_node')}` | {float(row.get('global_error_rate') or 0):.4f} | "
            f"{float(row.get('contextual_output_error_rate') or 0):.4f} | `{row.get('cec_status')}` | `{row.get('classification')}` |"
        )
    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- Numerical output error treats primary outputs as a binary vector in BLIF output order.",
            "- `globally_exact` is assigned only for exhaustive global distance rows.",
            "- `odc_valid_correspondence` requires global error greater than zero and ABC CEC output equivalence.",
            "- Sampled contextual error can rank candidates but is not a formal proof.",
        ]
    )
    SUMMARY_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_png(path: Path, values: list[float], max_value: float = 1.0, color: tuple[int, int, int] = (76, 120, 168)) -> None:
    import struct
    import zlib

    width, height = 760, 420
    pixels = bytearray([255] * width * height * 3)

    def rect(left: int, top: int, right: int, bottom: int, rgb: tuple[int, int, int]) -> None:
        for y in range(max(0, top), min(height, bottom)):
            for x in range(max(0, left), min(width, right)):
                idx = (y * width + x) * 3
                pixels[idx : idx + 3] = bytes(rgb)

    axis = (45, 55, 72)
    grid = (225, 232, 240)
    left, right, top, bottom = 58, width - 26, 36, height - 48
    for frac in [0.25, 0.5, 0.75, 1.0]:
        y = bottom - int((bottom - top) * frac)
        rect(left, y, right, y + 1, grid)
    rect(left, top, left + 2, bottom, axis)
    rect(left, bottom, right, bottom + 2, axis)
    if values:
        gap = 14
        bar_w = max(10, (right - left - gap * (len(values) + 1)) // len(values))
        for i, value in enumerate(values):
            x0 = left + gap + i * (bar_w + gap)
            bar_h = int((bottom - top) * min(value / max_value if max_value else 0.0, 1.0))
            rect(x0, bottom - bar_h, x0 + bar_w, bottom, color)

    def chunk(kind: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)

    raw = bytearray()
    for y in range(height):
        raw.append(0)
        raw.extend(pixels[y * width * 3 : (y + 1) * width * 3])
    path.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(bytes(raw), level=9))
        + chunk(b"IEND", b"")
    )


def write_scatter_png(path: Path, rows: list[dict[str, object]]) -> None:
    import struct
    import zlib

    width, height = 760, 420
    pixels = bytearray([255] * width * height * 3)
    colors = {
        "globally_exact": (84, 162, 75),
        "odc_valid_correspondence": (54, 144, 192),
        "contextually_approximate": (245, 133, 24),
        "unsafe_candidate": (180, 70, 70),
        "unresolved": (145, 145, 145),
    }

    def rect(left: int, top: int, right: int, bottom: int, rgb: tuple[int, int, int]) -> None:
        for y in range(max(0, top), min(height, bottom)):
            for x in range(max(0, left), min(width, right)):
                idx = (y * width + x) * 3
                pixels[idx : idx + 3] = bytes(rgb)

    left, right, top, bottom = 58, width - 26, 36, height - 48
    rect(left, top, left + 2, bottom, (45, 55, 72))
    rect(left, bottom, right, bottom + 2, (45, 55, 72))
    usable = [row for row in rows if row.get("global_error_rate") != "" and row.get("contextual_output_error_rate") != ""]
    max_x = max([float(row["global_error_rate"]) for row in usable] + [0.01])
    max_y = max([float(row["contextual_output_error_rate"]) for row in usable] + [0.01])
    for row in usable:
        x = left + int((right - left) * float(row["global_error_rate"]) / max_x)
        y = bottom - int((bottom - top) * float(row["contextual_output_error_rate"]) / max_y)
        rect(x - 3, y - 3, x + 4, y + 4, colors.get(str(row.get("classification")), (145, 145, 145)))

    def chunk(kind: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)

    raw = bytearray()
    for y in range(height):
        raw.append(0)
        raw.extend(pixels[y * width * 3 : (y + 1) * width * 3])
    path.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(bytes(raw), level=9))
        + chunk(b"IEND", b"")
    )


def plot_outputs(rows: list[dict[str, object]]) -> None:
    PLOTS.mkdir(parents=True, exist_ok=True)
    write_scatter_png(PLOTS / "global_vs_contextual_error.png", rows)
    classes = Counter(str(row.get("classification", "")) for row in rows)
    class_values = [classes[key] for key in sorted(classes)]
    write_png(PLOTS / "contextual_classification_counts.png", class_values, max(class_values) if class_values else 1, (76, 120, 168))
    recoveries = defaultdict(int)
    for row in rows:
        if row.get("classification") in {"odc_valid_correspondence", "contextually_approximate"}:
            recoveries[str(row.get("optimization"))] += 1
    recovery_values = [recoveries[key] for key in sorted(recoveries)]
    write_png(PLOTS / "contextual_recovery_by_optimization.png", recovery_values, max(recovery_values) if recovery_values else 1, (84, 162, 75))
    PRESENTATION_PLOTS.mkdir(parents=True, exist_ok=True)
    for name in [
        "global_vs_contextual_error.png",
        "contextual_classification_counts.png",
        "contextual_recovery_by_optimization.png",
        "critical_path_contextual_recovery.png",
    ]:
        src = PLOTS / name
        if src.exists():
            shutil.copy2(src, PRESENTATION_PLOTS / name)


def contextual_lookup(rows: list[dict[str, object]]) -> dict[tuple[str, str, str], dict[str, object]]:
    best: dict[tuple[str, str, str], dict[str, object]] = {}
    priority = {"odc_valid_correspondence": 0, "contextually_approximate": 1, "globally_exact": 2, "unsafe_candidate": 3, "unresolved": 4}
    for row in rows:
        key = (f"external_iscas85_{row.get('circuit')}", str(row.get("optimization")), str(row.get("optimized_node")))
        current = best.get(key)
        if current is None or priority.get(str(row.get("classification")), 99) < priority.get(str(current.get("classification")), 99):
            best[key] = row
    return best


def write_contextual_critical_path(rows: list[dict[str, object]]) -> None:
    path = RESULTS / "critical_path_mapping.csv"
    if not path.exists():
        write_rows(CRIT_CSV, [], [])
        CRIT_MD.write_text("# Contextual Critical-Path Mapping\n\n`critical_path_mapping.csv` was missing.\n", encoding="utf-8")
        return
    lookup = contextual_lookup(rows)
    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        original_rows = list(reader)
    extra = ["contextual_candidate_original_node", "contextual_classification", "contextual_error_rate", "contextual_cec_status"]
    out_rows = []
    recovered_odc = recovered_approx = still_unresolved = 0
    for row in original_rows:
        out = dict(row)
        key = (row.get("benchmark", ""), row.get("optimization", ""), row.get("optimized_node", ""))
        contextual = lookup.get(key)
        if row.get("mapping_category") in {"unresolved", "approximate_near_match"} and contextual:
            cls = str(contextual.get("classification"))
            if cls == "odc_valid_correspondence":
                out["mapping_category"] = "odc_valid_contextual"
                out["mapped_original_node"] = str(contextual.get("candidate_original_node"))
                recovered_odc += 1
            elif cls == "contextually_approximate":
                out["mapping_category"] = "contextually_approximate"
                out["mapped_original_node"] = str(contextual.get("candidate_original_node"))
                recovered_approx += 1
        if out.get("mapping_category") == "unresolved":
            still_unresolved += 1
        if contextual:
            out["contextual_candidate_original_node"] = contextual.get("candidate_original_node", "")
            out["contextual_classification"] = contextual.get("classification", "")
            out["contextual_error_rate"] = contextual.get("contextual_output_error_rate", "")
            out["contextual_cec_status"] = contextual.get("cec_status", "")
        else:
            out["contextual_candidate_original_node"] = ""
            out["contextual_classification"] = ""
            out["contextual_error_rate"] = ""
            out["contextual_cec_status"] = ""
        out_rows.append(out)
    columns = list(original_rows[0].keys()) + extra if original_rows else extra
    write_rows(CRIT_CSV, out_rows, columns)
    PLOTS.mkdir(parents=True, exist_ok=True)
    write_png(PLOTS / "critical_path_contextual_recovery.png", [recovered_odc, recovered_approx, still_unresolved], max([recovered_odc, recovered_approx, still_unresolved, 1]), (245, 133, 24))
    PRESENTATION_PLOTS.mkdir(parents=True, exist_ok=True)
    shutil.copy2(PLOTS / "critical_path_contextual_recovery.png", PRESENTATION_PLOTS / "critical_path_contextual_recovery.png")
    CRIT_MD.write_text(
        "\n".join(
            [
                "# Contextual Critical-Path Mapping",
                "",
                "This file preserves the existing critical-path mapping and adds contextual classification columns.",
                "",
                f"- Previously unresolved or approximate nodes recovered through ODC-valid matching: `{recovered_odc}`",
                f"- Newly recovered through contextual approximation: `{recovered_approx}`",
                f"- Still unresolved: `{still_unresolved}`",
                "",
                "The result is versioned separately from `critical_path_mapping.csv` to preserve backwards compatibility.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--circuits", nargs="+", default=DEFAULT_CIRCUITS)
    parser.add_argument("--optimizations", nargs="+", default=DEFAULT_OPTIMIZATIONS)
    parser.add_argument("--max-candidates", type=int, default=40)
    parser.add_argument("--exact-support-cap", type=int, default=12)
    parser.add_argument("--sample-count", type=int, default=1024)
    parser.add_argument("--seed", type=int, default=23)
    parser.add_argument("--contextual-error-threshold", type=float, default=0.01)
    parser.add_argument("--output-dir", type=Path, default=RESULTS)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    global DETAIL_CSV, SUMMARY_CSV, SUMMARY_MD, CRIT_CSV, CRIT_MD, PLOTS
    if args.output_dir != RESULTS:
        DETAIL_CSV = args.output_dir / "contextual_error_metrics.csv"
        SUMMARY_CSV = args.output_dir / "contextual_error_metrics_summary.csv"
        SUMMARY_MD = args.output_dir / "contextual_error_metrics.md"
        CRIT_CSV = args.output_dir / "contextual_critical_path_mapping.csv"
        CRIT_MD = args.output_dir / "contextual_critical_path_mapping.md"
        PLOTS = args.output_dir / "plots"

    candidates = select_candidates(args.circuits, args.optimizations, args.max_candidates)
    abc_bin = find_abc()
    rows: list[dict[str, object]] = []
    with tempfile.TemporaryDirectory(prefix="contextual_error_") as tmp_dir:
        tmp = Path(tmp_dir)
        for candidate in candidates:
            rows.append(analyze_candidate(candidate, args, abc_bin, tmp))

    write_rows(DETAIL_CSV, rows, DETAIL_COLUMNS)
    summary_rows = summarize(rows)
    write_rows(SUMMARY_CSV, summary_rows, ["summary_type", "name", "count"])
    write_markdown(rows, summary_rows)
    write_contextual_critical_path(rows)
    plot_outputs(rows)

    print(f"Wrote {DETAIL_CSV.relative_to(ROOT) if DETAIL_CSV.is_relative_to(ROOT) else DETAIL_CSV}")
    print(f"Wrote {SUMMARY_CSV.relative_to(ROOT) if SUMMARY_CSV.is_relative_to(ROOT) else SUMMARY_CSV}")
    print(f"Wrote {SUMMARY_MD.relative_to(ROOT) if SUMMARY_MD.is_relative_to(ROOT) else SUMMARY_MD}")
    print(f"Wrote {CRIT_CSV.relative_to(ROOT) if CRIT_CSV.is_relative_to(ROOT) else CRIT_CSV}")
    print(f"Wrote {CRIT_MD.relative_to(ROOT) if CRIT_MD.is_relative_to(ROOT) else CRIT_MD}")
    print(f"Analyzed candidates: {len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
