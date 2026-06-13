#!/usr/bin/env python3
"""
scripts/import_external_benchmarks.py
-------------------------------------
Import standard external benchmark suites (ISCAS-85, EPFL) into
benchmarks/external/<family>/ so the existing pipeline can run on them.

Design constraints (research iteration 2)
=========================================
* NEVER downloads anything. You point it at files you already have locally.
* No hardcoded absolute paths — you pass --input-dir explicitly.
* Accepts BLIF directly, and converts AIGER (.aig/.aag/.aiger), Verilog (.v)
  and SystemVerilog (.sv) using documented ABC / Yosys commands (see below).
* Scans --input-dir recursively, so it can point at a suite root containing
  nested category folders.
* Files are validated (BLIF) and copied/converted into the documented folder
  benchmarks/external/<family>/, where discovery picks them up automatically.

Conversion commands used
========================
AIGER  → BLIF   (requires ABC on PATH, or $ABC):
    abc -c "read_aiger <in>.aig; strash; write_blif <out>.blif"

Verilog/SystemVerilog → BLIF  (requires Yosys on PATH):
    yosys -p "read_verilog <in>.v; synth -top <top>; write_blif <out>.blif"

Usage
=====
    # Show what is already present under benchmarks/external/:
    python3 scripts/import_external_benchmarks.py --list

    # Import BLIF files you already have locally:
    python3 scripts/import_external_benchmarks.py \\
        --family iscas85 --input-dir /path/to/iscas85_blifs/

    # Import + convert AIGER files (e.g. the EPFL suite) via ABC:
    python3 scripts/import_external_benchmarks.py \\
        --family epfl --input-dir /path/to/epfl/ --convert-aiger

    # Convert Verilog via Yosys:
    python3 scripts/import_external_benchmarks.py \\
        --family iscas85 --input-dir /path/to/verilog/ --convert-verilog

After importing, rebuild the manifest and run the pipeline:
    python3 scripts/build_benchmark_manifest.py
    make generate-variants analyze sat-pipeline research-plots
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXTERNAL_ROOT = ROOT / "benchmarks" / "external"
SUPPORTED_FAMILIES = ("iscas85", "epfl")

REQUIRED_BLIF_KEYWORDS = {".model", ".inputs", ".outputs", ".end"}

BLIF_EXTENSIONS = {".blif"}
AIGER_EXTENSIONS = {".aig", ".aag", ".aiger"}
VERILOG_EXTENSIONS = {".v", ".sv"}


# ── validation ────────────────────────────────────────────────────────────────

def validate_blif(path: Path) -> list[str]:
    """Return a list of validation errors ([] means OK)."""
    try:
        text = path.read_text(errors="replace")
    except OSError as exc:
        return [f"cannot read file: {exc}"]
    return [f"missing keyword: {kw}" for kw in REQUIRED_BLIF_KEYWORDS if kw not in text]


# ── tool discovery ────────────────────────────────────────────────────────────

def _abc_bin() -> str:
    return os.environ.get("ABC", "abc")


def _tool_available(cmd: list[str]) -> bool:
    try:
        subprocess.run(cmd, capture_output=True, check=False)
        return True
    except FileNotFoundError:
        return False


def _is_hidden_or_cache(path: Path) -> bool:
    """Skip files under hidden/cache directories while scanning suite roots."""
    ignored = {"__pycache__", ".pytest_cache", ".mypy_cache", ".matplotlib-cache"}
    return any(part.startswith(".") or part in ignored for part in path.parts)


def _discover_files(input_dir: Path, extensions: set[str]) -> list[Path]:
    """Recursively find files with matching extensions in deterministic order."""
    files = [
        p for p in input_dir.rglob("*")
        if p.is_file()
        and p.suffix.lower() in extensions
        and not _is_hidden_or_cache(p.relative_to(input_dir))
    ]
    return sorted(files, key=lambda p: p.relative_to(input_dir).as_posix().lower())


# ── converters ────────────────────────────────────────────────────────────────

def convert_aiger(src: Path, dst: Path) -> bool:
    """AIGER → BLIF via ABC. Returns True on success."""
    abc = _abc_bin()
    if not _tool_available([abc, "-h"]):
        print(
            f"  ⚠  ABC not found (tried '{abc}'). Set $ABC or build via 'make build-abc'.\n"
            f"     Manual command: {abc} -c \"read_aiger {src}; strash; write_blif {dst}\""
        )
        return False
    cmd = [abc, "-c", f"read_aiger {src}; strash; write_blif {dst}"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"    ✗  {src.name} (ABC failed):\n{result.stderr[:300]}")
        return False
    return True


def convert_verilog(src: Path, dst: Path) -> bool:
    """Verilog/SystemVerilog → BLIF via Yosys. Returns True on success."""
    if not _tool_available(["yosys", "--version"]):
        print(
            "  ⚠  Yosys not found on PATH — cannot convert Verilog/SystemVerilog.\n"
            f"     Manual command: yosys -p \"read_verilog {src}; "
            f"synth -top {src.stem}; write_blif {dst}\""
        )
        return False
    read_cmd = f"read_verilog {'-sv ' if src.suffix.lower() == '.sv' else ''}{src}"
    cmd = ["yosys", "-p", f"{read_cmd}; synth -top {src.stem}; write_blif {dst}"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"    ✗  {src.name} (Yosys failed):\n{result.stderr[:300]}")
        return False
    return True


# ── import ────────────────────────────────────────────────────────────────────

def import_family(family: str, input_dir: Path, convert_aiger_flag: bool,
                  convert_verilog_flag: bool) -> int:
    """Import all matching files from *input_dir* into benchmarks/external/<family>/.

    Returns the number of files successfully placed.
    """
    out_dir = EXTERNAL_ROOT / family
    out_dir.mkdir(parents=True, exist_ok=True)

    blifs = _discover_files(input_dir, BLIF_EXTENSIONS)
    aigs = _discover_files(input_dir, AIGER_EXTENSIONS) if convert_aiger_flag else []
    verilogs = (
        _discover_files(input_dir, VERILOG_EXTENSIONS) if convert_verilog_flag else []
    )

    if not (blifs or aigs or verilogs):
        print(f"  No importable files found in {input_dir}")
        print("  Expected recursive .blif files (always) plus .aig/.aag/.aiger "
              "(--convert-aiger) or .v/.sv (--convert-verilog).")
        return 0

    placed = 0

    for bf in blifs:
        errors = validate_blif(bf)
        if errors:
            print(f"  ✗  {bf.name}: {'; '.join(errors)}")
            continue
        shutil.copy2(bf, out_dir / bf.name)
        rel = bf.relative_to(input_dir).as_posix()
        print(f"  ✓  {rel} → benchmarks/external/{family}/{bf.name}")
        placed += 1

    for af in aigs:
        dst = out_dir / f"{af.stem}.blif"
        if convert_aiger(af, dst) and not validate_blif(dst):
            print(f"  ✓  {af.name} → benchmarks/external/{family}/{dst.name} (AIGER→BLIF)")
            placed += 1

    for vf in verilogs:
        dst = out_dir / f"{vf.stem}.blif"
        if convert_verilog(vf, dst) and not validate_blif(dst):
            print(f"  ✓  {vf.name} → benchmarks/external/{family}/{dst.name} (Verilog→BLIF)")
            placed += 1

    return placed


def list_external() -> None:
    print("\n=== benchmarks/external/ ===")
    any_found = False
    for family in SUPPORTED_FAMILIES:
        fam_dir = EXTERNAL_ROOT / family
        blifs = sorted(fam_dir.glob("*.blif")) if fam_dir.is_dir() else []
        print(f"\n  {family}/  ({len(blifs)} BLIF file(s))")
        for bf in blifs:
            any_found = True
            print(f"    {bf.name}")
    if not any_found:
        print("\n  No external benchmarks present yet.")
        print("  See benchmarks/external/README.md for how to add ISCAS-85 / EPFL files.")
    print()


# ── main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--family", choices=SUPPORTED_FAMILIES,
                        help="External suite to import into.")
    parser.add_argument("--input-dir", metavar="DIR",
                        help="Local root directory; files are discovered recursively.")
    parser.add_argument("--convert-aiger", action="store_true",
                        help="Also convert .aig/.aag/.aiger files via ABC.")
    parser.add_argument("--convert-verilog", action="store_true",
                        help="Also convert .v/.sv files via Yosys.")
    parser.add_argument("--list", action="store_true",
                        help="List external benchmarks already present and exit.")
    args = parser.parse_args()

    if args.list or not args.family:
        list_external()
        if not args.family:
            if not args.list:
                parser.print_help()
            return

    if not args.input_dir:
        parser.error("--family requires --input-dir")
    in_dir = Path(args.input_dir)
    if not in_dir.is_dir():
        print(f"ERROR: --input-dir does not exist: {in_dir}", file=sys.stderr)
        sys.exit(1)

    print(f"\nImporting {args.family} benchmarks from {in_dir} ...")
    placed = import_family(args.family, in_dir, args.convert_aiger, args.convert_verilog)
    print(f"\nPlaced {placed} file(s) under benchmarks/external/{args.family}/.")
    if placed:
        print("\nNext steps:")
        print("  python3 scripts/build_benchmark_manifest.py")
        print("  make generate-variants analyze sat-pipeline research-plots")
    list_external()


if __name__ == "__main__":
    main()
