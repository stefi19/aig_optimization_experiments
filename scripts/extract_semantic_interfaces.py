#!/usr/bin/env python3
"""Extract canonical scalar interfaces for valid semantic regions."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from semantic_region_pipeline import summarize_regions, write_interface_outputs


def main() -> int:
    write_interface_outputs()
    summarize_regions()
    print("Wrote semantic scalar interfaces and bus metadata")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
