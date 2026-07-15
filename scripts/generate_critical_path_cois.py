#!/usr/bin/env python3
"""Generate bounded diagnostic COIs from structural critical-path segments."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from boundary_diagnosis import DIAG_RESULTS, generated_critical_path_coi_rows, write_csv  # noqa: E402


def parse_sizes(value: str) -> list[int]:
    return [int(item.strip()) for item in value.split(",") if item.strip()]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--critical-path-segment-sizes", default="3,5,8")
    args = parser.parse_args()
    rows = generated_critical_path_coi_rows(parse_sizes(args.critical_path_segment_sizes))
    DIAG_RESULTS.mkdir(parents=True, exist_ok=True)
    write_csv(DIAG_RESULTS / "boundary_generated_critical_path_cois.csv", rows)
    print(f"Generated critical-path diagnostic COI rows: {len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
