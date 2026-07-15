#!/usr/bin/env python3
"""Run the identity S-versus-S boundary-recovery baseline."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from boundary_diagnosis import CASE_COLUMNS, DIAG_RESULTS, run_diagnostic_suite, write_csv  # noqa: E402


def main() -> int:
    DIAG_RESULTS.mkdir(parents=True, exist_ok=True)
    bundle = run_diagnostic_suite(optimizations=["identity"], anchor_modes=["exact_only"])
    write_csv(DIAG_RESULTS / "boundary_identity_baseline.csv", bundle.cases, CASE_COLUMNS)
    total = len(bundle.cases)
    success = sum(str(row.get("recovery_success")).lower() == "true" for row in bundle.cases)
    print(f"Identity boundary baseline: {success}/{total} successful")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
