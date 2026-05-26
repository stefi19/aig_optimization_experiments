#!/usr/bin/env python3
"""
scripts/import_real_benchmarks.py
----------------------------------
Helper script for the real benchmark suite.

What it does
============
1. Lists all BLIF files currently available under benchmarks/real/ and
   prints a summary table (name, input count, output count, node count).
2. If --verilog is given and Yosys is available, converts every .v file
   in the specified directory to BLIF and places the results in
   benchmarks/real/converted_blif/.
3. Prints instructions for adding ISCAS-85 benchmarks (which cannot be
   redistributed but are freely downloadable).

Usage
=====
    python3 scripts/import_real_benchmarks.py
    python3 scripts/import_real_benchmarks.py --verilog benchmarks/real/verilog_examples/

After running this script, re-run the pipeline to include the new benchmarks:
    make generate-variants analyze sat-pipeline topk-eval ablation region \\
         cegar-refine research-plots
"""

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

# ── BLIF parser helpers ───────────────────────────────────────────────────────


def _parse_blif_stats(path: Path) -> dict:
    """Return a dict with keys: name, inputs, outputs, nodes."""
    stats = {"name": path.stem, "inputs": 0, "outputs": 0, "nodes": 0}
    with path.open() as fh:
        for line in fh:
            line = line.strip()
            if line.startswith(".inputs"):
                stats["inputs"] += len(line.split()[1:])
            elif line.startswith(".outputs"):
                stats["outputs"] += len(line.split()[1:])
            elif line.startswith(".names"):
                stats["nodes"] += 1  # counts primary outputs too; good enough
    return stats


# ── Verilog → BLIF conversion ─────────────────────────────────────────────────


def _yosys_available() -> bool:
    try:
        subprocess.run(
            ["yosys", "--version"],
            capture_output=True,
            check=True,
        )
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False


def _convert_verilog(verilog_dir: Path, out_dir: Path) -> None:
    """Convert all .v files in verilog_dir to BLIF using Yosys."""
    v_files = list(verilog_dir.glob("*.v"))
    if not v_files:
        print(f"  No .v files found in {verilog_dir}")
        return

    if not _yosys_available():
        print(
            "  ⚠  Yosys not found on PATH — skipping Verilog conversion.\n"
            "      Install Yosys (https://yosyshq.net/yosys/) then re-run:\n"
            f"      python3 scripts/import_real_benchmarks.py --verilog {verilog_dir}"
        )
        return

    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"  Converting {len(v_files)} Verilog file(s) → {out_dir}/")

    for v in v_files:
        # Guess top module from filename (Yosys -top flag)
        module = v.stem
        out_blif = out_dir / f"{module}.blif"

        cmd = [
            "yosys",
            "-p",
            f"read_verilog {v}; synth -top {module}; write_blif {out_blif}",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"    ✓  {v.name}  →  {out_blif.name}")
        else:
            print(f"    ✗  {v.name} failed:\n{result.stderr[:300]}")


# ── Listing ───────────────────────────────────────────────────────────────────


def _list_real_benchmarks(root: Path) -> None:
    blif_files = sorted(root.rglob("*.blif"))
    if not blif_files:
        print("  No BLIF files found under", root)
        return

    header = f"  {'File':<35}  {'Inputs':>7}  {'Outputs':>8}  {'Nodes':>6}"
    print(header)
    print("  " + "-" * (len(header) - 2))
    for bf in blif_files:
        rel = bf.relative_to(root.parent)
        s = _parse_blif_stats(bf)
        print(f"  {str(rel):<35}  {s['inputs']:>7}  {s['outputs']:>8}  {s['nodes']:>6}")
    print(f"\n  Total: {len(blif_files)} BLIF file(s)\n")


# ── ISCAS-85 instructions ─────────────────────────────────────────────────────


ISCAS_MSG = """
ISCAS-85 benchmarks (optional, not included)
============================================
The ISCAS-85 suite (c17, c432, c499, c880, c1355, c1908, c2670, c3540, c5315,
c6288, c7552) is the standard gate-level benchmark set used in synthesis papers.
It cannot be redistributed here but is freely downloadable.

Download steps:
  1. Visit https://ptolemy.berkeley.edu/projects/embedded/pubs/downloads/iscas/
     or search the web for "ISCAS 85 BLIF".
  2. Place the downloaded .blif files in:
       benchmarks/real/iscas85/
  3. Re-run the pipeline:
       make generate-variants analyze sat-pipeline topk-eval ablation \\
            region cegar-refine research-plots

The scripts discover all benchmarks/**/*.blif automatically, so no code changes
are needed.
"""


# ── Main ──────────────────────────────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser(
        description="List and import real BLIF benchmarks.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--verilog",
        metavar="DIR",
        help="Directory of .v files to convert to BLIF via Yosys.",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).parent.parent
    real_dir = repo_root / "benchmarks" / "real"

    print("\n=== Real Benchmark Suite ===\n")
    _list_real_benchmarks(real_dir)

    if args.verilog:
        v_dir = Path(args.verilog)
        if not v_dir.is_dir():
            print(f"ERROR: --verilog path does not exist: {v_dir}", file=sys.stderr)
            sys.exit(1)
        out_dir = real_dir / "converted_blif"
        print(f"Converting Verilog → BLIF  ({v_dir} → {out_dir})")
        _convert_verilog(v_dir, out_dir)
        print("\nUpdated benchmark list:")
        _list_real_benchmarks(real_dir)

    print(ISCAS_MSG)


if __name__ == "__main__":
    main()
