#!/usr/bin/env python3
"""Validate semantic region replacement result schemas and proof gates."""

from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "semantic_region_replacement"

REQUIRED = {
    "region_candidates.csv",
    "region_closure_validation.csv",
    "region_interface_hypotheses.csv",
    "compositional_cegis_candidates.csv",
    "compositional_cegis_iterations.csv",
    "compositional_formal_results.csv",
    "verified_semantic_modules.csv",
    "replacement_module_synthesis.csv",
    "replacement_port_mappings.csv",
    "replacement_attempts.csv",
    "graph_rewrite_validation.csv",
    "implementation_global_cec.csv",
    "specification_global_cec.csv",
    "boundary_restoration_results.csv",
    "replacement_strategy_ablation.csv",
    "semantic_recovery_by_operator.csv",
    "semantic_recovery_by_width.csv",
    "semantic_recovery_by_optimisation.csv",
    "failure_taxonomy.csv",
}


def rows(name: str) -> list[dict[str, str]]:
    with (OUT / name).open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def main() -> int:
    problems = []
    for name in REQUIRED:
        if not (OUT / name).exists():
            problems.append(f"missing {name}")
    if problems:
        print("\n".join(problems), file=sys.stderr)
        return 1
    attempts = rows("replacement_attempts.csv")
    rewrites = {r["attempt_id"]: r for r in rows("graph_rewrite_validation.csv")}
    cecs = {r["attempt_id"]: r for r in rows("implementation_global_cec.csv")}
    boundaries = {r["attempt_id"]: r for r in rows("boundary_restoration_results.csv")}
    for attempt in attempts:
        aid = attempt["attempt_id"]
        if attempt["accepted"] == "true":
            if attempt["graph_active"] != "true":
                problems.append(f"{aid}: accepted without graph_active")
            if rewrites.get(aid, {}).get("graph_rewrite_status") != "valid":
                problems.append(f"{aid}: accepted without valid rewrite")
            if cecs.get(aid, {}).get("implementation_global_cec") != "equivalent":
                problems.append(f"{aid}: accepted without ABC CEC equivalence")
            if boundaries.get(aid, {}).get("newly_recovered_boundary") != "true":
                problems.append(f"{aid}: accepted without restored boundary row")
    if not any(a["accepted"] == "true" for a in attempts):
        problems.append("no controlled positive replacement accepted")
    if problems:
        print("\n".join(problems), file=sys.stderr)
        return 1
    print("Semantic region replacement result checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
