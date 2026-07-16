#!/usr/bin/env python3
"""Compare ground-truth semantic regions against whole-output-cone regions."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from semantic_region_pipeline import compare_region_sources, summarize_regions


def main() -> int:
    rows = compare_region_sources()
    summarize_regions()
    print(f"Wrote {len(rows)} semantic region source-comparison rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
