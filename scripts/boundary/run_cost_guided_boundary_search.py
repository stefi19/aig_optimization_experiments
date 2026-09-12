#!/usr/bin/env python3
"""Run the extended-boundary search in cost-guided mode.

This file is intentionally a narrow mode adapter.  The full implementation
lives in :mod:`scripts.boundary.evaluate_extended_boundary_correctness`; keeping
the mode wrapper explicit gives Makefile targets and old experiment notes a
stable name without duplicating the evaluator.
"""

from __future__ import annotations

import runpy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

if __name__ == "__main__":
    sys.argv = [sys.argv[0], "--search-mode", "cost_guided", *sys.argv[1:]]
    runpy.run_module("scripts.boundary.evaluate_extended_boundary_correctness", run_name="__main__")
