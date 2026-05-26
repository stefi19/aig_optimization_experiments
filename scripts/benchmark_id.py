"""
scripts/benchmark_id.py
-----------------------
Converts a BLIF file path to a safe benchmark identifier that can be used as
a filename prefix without collisions across subdirectories.

Rules
-----
- Strip the leading "benchmarks/" prefix (if present).
- Strip the ".blif" suffix.
- Replace every path separator (/) and any non-alphanumeric character (except
  underscores) with a single underscore.
- Top-level benchmarks (benchmarks/majority3.blif) keep their basename unchanged.

Examples
--------
  benchmarks/majority3.blif                  → majority3
  benchmarks/generated/xor_chain_8.blif      → generated_xor_chain_8
  benchmarks/real/hand_written/full_adder.blif → real_hand_written_full_adder
  benchmarks/real/iscas85/c432.blif           → real_iscas85_c432

Usage as a CLI tool (called by run_abc_variants.sh)
---------------------------------------------------
  python3 scripts/benchmark_id.py benchmarks/real/hand_written/full_adder.blif
  # prints: real_hand_written_full_adder

Usage as a library (used by tests)
------------------------------------
  from scripts.benchmark_id import blif_to_id
  blif_to_id("benchmarks/real/hand_written/full_adder.blif")  # "real_hand_written_full_adder"
"""

import re
import sys
from pathlib import Path


_BENCH_PREFIX = "benchmarks/"


def blif_to_id(path: str) -> str:
    """Return a safe, collision-free benchmark identifier for *path*.

    Parameters
    ----------
    path:
        Path to a .blif file.  Can be relative (as produced by find(1)) or
        absolute.  Both forward and backward slashes are handled.

    Returns
    -------
    str
        A string consisting only of [a-zA-Z0-9_], suitable for use as a
        filename prefix.
    """
    # Normalise separators and strip leading ./
    p = Path(path).as_posix()
    if p.startswith("./"):
        p = p[2:]

    # Strip everything up to and including the benchmarks/ segment so we
    # encode only the meaningful part.  Handles both relative and absolute paths.
    bench_idx = p.find(_BENCH_PREFIX)
    if bench_idx != -1:
        p = p[bench_idx + len(_BENCH_PREFIX):]

    # Strip .blif suffix (case-insensitive, just in case)
    if p.lower().endswith(".blif"):
        p = p[:-5]

    # Replace every non-alphanumeric character (including /) with underscore,
    # then collapse consecutive underscores and strip leading/trailing ones.
    safe = re.sub(r"[^a-zA-Z0-9]+", "_", p).strip("_")

    return safe


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/benchmark_id.py <path-to-blif>", file=sys.stderr)
        sys.exit(1)
    print(blif_to_id(sys.argv[1]))
