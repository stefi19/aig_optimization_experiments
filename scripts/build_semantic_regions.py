#!/usr/bin/env python3
"""Build canonical semantic regions from Phase 1 benchmark manifests."""

from __future__ import annotations

import sys
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from semantic_region_pipeline import build_regions, write_region_outputs


def csv_set(value: str | None) -> set[str] | None:
    if not value:
        return None
    return {part.strip() for part in value.split(",") if part.strip()}


def int_csv_set(value: str | None) -> set[int] | None:
    if not value:
        return None
    return {int(part.strip()) for part in value.split(",") if part.strip()}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-type", action="append", choices=["ground_truth_region", "whole_output_cone"], help="Region source type to build. Repeat to select multiple; default builds active sources.")
    parser.add_argument("--families", help="Comma-separated family filter.")
    parser.add_argument("--operators", help="Comma-separated operator filter.")
    parser.add_argument("--widths", help="Comma-separated input/output width filter.")
    parser.add_argument("--optimizations", help="Comma-separated optimization-flow filter.")
    parser.add_argument("--include-output-cones", action="store_true", help="Include whole-output-cone rows when --source-type filters are used.")
    args = parser.parse_args()

    source_types = tuple(args.source_type or ("ground_truth_region", "whole_output_cone"))
    if args.include_output_cones and "whole_output_cone" not in source_types:
        source_types = tuple(source_types) + ("whole_output_cone",)

    regions, validations = build_regions(
        source_types=source_types,
        families=csv_set(args.families),
        operators=csv_set(args.operators),
        widths=int_csv_set(args.widths),
        optimizations=csv_set(args.optimizations),
    )
    write_region_outputs(regions, validations)
    print(f"Wrote {len(regions)} semantic region rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
