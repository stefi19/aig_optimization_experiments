#!/usr/bin/env python3
"""Compile the paper markdown into a PDF artifact."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "paper" / "paper.md"
BIB = ROOT / "paper" / "references.bib"
OUT = ROOT / "output" / "pdf" / "aig_internal_correspondence_artifact.pdf"


def main() -> int:
    pandoc = shutil.which("pandoc")
    pdflatex = shutil.which("pdflatex")
    if not pandoc:
        print("ERROR: pandoc is required to compile paper/paper.md into PDF", file=sys.stderr)
        return 1
    if not pdflatex:
        print("ERROR: pdflatex is required as the Pandoc PDF engine", file=sys.stderr)
        return 1
    subprocess.check_call([sys.executable, str(ROOT / "scripts" / "build_research_wow.py")], cwd=ROOT)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        pandoc,
        str(PAPER),
        "--from",
        "markdown",
        "--pdf-engine",
        "pdflatex",
        "--resource-path",
        str(ROOT / "paper"),
        "--citeproc",
        "--bibliography",
        str(BIB),
        "-o",
        str(OUT),
    ]
    subprocess.check_call(cmd, cwd=ROOT)
    print(f"Wrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
