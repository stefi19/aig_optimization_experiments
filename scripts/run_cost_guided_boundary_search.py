#!/usr/bin/env python3
"""Run cost-guided extended-boundary search."""

from __future__ import annotations

import runpy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

if __name__ == "__main__":
    sys.argv = [sys.argv[0], "--search-mode", "cost_guided", *sys.argv[1:]]
    runpy.run_path(str(ROOT / "scripts" / "evaluate_extended_boundary_correctness.py"), run_name="__main__")
