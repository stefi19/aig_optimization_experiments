#!/usr/bin/env python3
"""
scripts/build_benchmark_manifest.py
-----------------------------------
Scan every BLIF benchmark in the repository and write a manifest CSV that
records *what is actually present on disk*.

Output: results/benchmark_manifest.csv with columns:

    benchmark        – benchmark id (from scripts/benchmark_id.py)
    source_family    – toy | generated | iscas85 | epfl | custom
    path             – path relative to the repo root
    n_inputs         – number of primary inputs (.inputs)
    n_outputs        – number of primary outputs (.outputs)
    n_internal_nodes – number of .names (logic nodes)
    exact_mode_possible – True if 2^n_inputs truth-table enumeration is feasible
                          (n_inputs <= MAX_EXACT_INPUTS), else False
    notes            – short free-text note (e.g. "wide input cone")

This manifest is descriptive metadata about the benchmark *files*, not
experimental results.  It is safe to regenerate at any time and contains no
fabricated data — every row corresponds to a real file.

Usage
=====
    python3 scripts/build_benchmark_manifest.py
    python3 scripts/build_benchmark_manifest.py --benchmarks-dir benchmarks \\
        --output results/benchmark_manifest.csv
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.benchmark_id import blif_to_id, infer_source_family

# Mirror analyze_blif_matches.MAX_EXACT_INPUTS so the manifest's
# exact_mode_possible column agrees with what the analysis actually does.
try:
    from analyze_blif_matches import MAX_EXACT_INPUTS
except Exception:  # pragma: no cover - fallback if analysis module changes
    MAX_EXACT_INPUTS = 12


def parse_blif_stats(path: Path) -> dict:
    """Return {n_inputs, n_outputs, n_internal_nodes} for a BLIF file.

    .inputs / .outputs may be split across several logical lines; each
    contributes its listed signals.  BLIF also allows backslash continuation
    for long lines, so parsing uses logical lines rather than raw file lines.
    Each .names line is one logic node.
    """
    n_in = n_out = n_nodes = 0
    try:
        for line in iter_blif_logical_lines(path):
            if line.startswith(".inputs"):
                n_in += len(line.split()[1:])
            elif line.startswith(".outputs"):
                n_out += len(line.split()[1:])
            elif line.startswith(".names"):
                n_nodes += 1
    except OSError as exc:  # pragma: no cover
        print(f"  WARNING: cannot read {path}: {exc}", file=sys.stderr)
    return {"n_inputs": n_in, "n_outputs": n_out, "n_internal_nodes": n_nodes}


def iter_blif_logical_lines(path: Path):
    """Yield BLIF logical lines, joining lines ending in backslash.

    This is intentionally small and conservative: it strips comments/blank
    lines after joining and keeps normal whitespace tokenization for callers.
    """
    pending = ""
    with path.open(errors="replace") as fh:
        for raw in fh:
            line = raw.rstrip("\n\r").strip()
            if not line:
                continue
            if line.endswith("\\"):
                pending += line[:-1].rstrip() + " "
                continue
            logical = (pending + line).strip()
            pending = ""
            if logical and not logical.startswith("#"):
                yield logical
    if pending.strip():
        yield pending.strip()


def _note_for(stats: dict, exact_ok: bool) -> str:
    notes = []
    if stats["n_internal_nodes"] == 0:
        notes.append("no internal .names nodes")
    if not exact_ok:
        notes.append(
            f"wide input cone ({stats['n_inputs']} inputs) — random simulation only"
        )
    return "; ".join(notes)


def build_manifest(benchmarks_dir: Path) -> list[dict]:
    rows = []
    for blif in sorted(benchmarks_dir.rglob("*.blif")):
        try:
            rel = blif.relative_to(ROOT)
        except ValueError:
            # Benchmark dir outside the repo root (e.g. tests' tmp dirs).
            rel = blif
        bid = blif_to_id(str(blif))
        stats = parse_blif_stats(blif)
        exact_ok = stats["n_inputs"] <= MAX_EXACT_INPUTS
        rows.append({
            "benchmark": bid,
            "source_family": infer_source_family(bid),
            "path": rel.as_posix(),
            "n_inputs": stats["n_inputs"],
            "n_outputs": stats["n_outputs"],
            "n_internal_nodes": stats["n_internal_nodes"],
            "exact_mode_possible": exact_ok,
            "notes": _note_for(stats, exact_ok),
        })
    return rows


FIELDS = [
    "benchmark", "source_family", "path",
    "n_inputs", "n_outputs", "n_internal_nodes",
    "exact_mode_possible", "notes",
]


def write_manifest(rows: list[dict], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def _print_summary(rows: list[dict]) -> None:
    from collections import Counter

    by_family = Counter(r["source_family"] for r in rows)
    print(f"\nIndexed {len(rows)} benchmark file(s):")
    for fam in ("toy", "generated", "custom", "iscas85", "epfl"):
        count = by_family.get(fam, 0)
        marker = "" if count else "   (none present)"
        print(f"  {fam:<10} {count:>3}{marker}")

    if not by_family.get("iscas85") and not by_family.get("epfl"):
        print(
            "\n  NOTE: no external (ISCAS-85 / EPFL) benchmarks found.\n"
            "        See benchmarks/external/README.md to add them."
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--benchmarks-dir", default=str(ROOT / "benchmarks"),
                        help="Root directory to scan (default: benchmarks/).")
    parser.add_argument("--output", default=str(ROOT / "results" / "benchmark_manifest.csv"),
                        help="Output CSV path (default: results/benchmark_manifest.csv).")
    args = parser.parse_args()

    bench_dir = Path(args.benchmarks_dir)
    if not bench_dir.is_dir():
        print(f"ERROR: benchmarks dir not found: {bench_dir}", file=sys.stderr)
        sys.exit(1)

    rows = build_manifest(bench_dir)
    out_path = Path(args.output)
    write_manifest(rows, out_path)
    _print_summary(rows)
    try:
        shown = out_path.relative_to(ROOT)
    except ValueError:
        shown = out_path
    print(f"\nWrote {shown}")


if __name__ == "__main__":
    main()
