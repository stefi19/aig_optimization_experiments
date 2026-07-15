#!/usr/bin/env python3
"""Generate boundary anchor-coverage diagnostics."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from boundary_diagnosis import COVERAGE_COLUMNS, DIAG_RESULTS, run_diagnostic_suite, write_csv  # noqa: E402


def main() -> int:
    DIAG_RESULTS.mkdir(parents=True, exist_ok=True)
    bundle = run_diagnostic_suite()
    write_csv(DIAG_RESULTS / "boundary_anchor_coverage.csv", bundle.coverage, COVERAGE_COLUMNS)
    print(f"Boundary anchor coverage rows: {len(bundle.coverage)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
