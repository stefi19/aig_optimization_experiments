#!/usr/bin/env python3
"""Z3 smoke checks used by Makefile and CI."""

from __future__ import annotations

import sys

import z3


def main() -> int:
    x = z3.BitVec("x", 8)
    sat_solver = z3.Solver()
    sat_solver.add((x + 1) == 6)
    if sat_solver.check() != z3.sat or sat_solver.model()[x].as_long() != 5:
        print("SAT bit-vector smoke check failed", file=sys.stderr)
        return 1

    y = z3.BitVec("y", 8)
    unsat_solver = z3.Solver()
    unsat_solver.add((y + 1) != (1 + y))
    if unsat_solver.check() != z3.unsat:
        print("UNSAT equivalence smoke check failed", file=sys.stderr)
        return 1

    cex_solver = z3.Solver()
    cex_solver.add((x & 0x0F) != x)
    if cex_solver.check() != z3.sat:
        print("counterexample smoke check failed", file=sys.stderr)
        return 1
    print(f"Z3 smoke checks passed: version={z3.get_version_string()} cex_x={cex_solver.model()[x].as_long()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
