#!/usr/bin/env python3
"""Run corrected optimized boundary recovery over eligible canonical COIs."""

from __future__ import annotations

import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from boundary_graph import CircuitGraph  # noqa: E402
from boundary_semantics import (  # noqa: E402
    OPTIMIZATIONS,
    SEMANTICS_DIR,
    load_canonical_manifest,
    load_formal_anchors,
    original_path,
    recover_semantic_boundary,
    variant_path,
    write_csv,
)
from coi_model import validate_coi  # noqa: E402

OUT = SEMANTICS_DIR / "optimized_recovery_corrected.csv"
SUMMARY = SEMANTICS_DIR / "optimized_recovery_corrected_summary.md"


def main() -> int:
    rows = []
    for coi in load_canonical_manifest():
        spec_path = original_path(coi.benchmark)
        if not spec_path.exists():
            continue
        spec = CircuitGraph.from_blif(spec_path)
        if not validate_coi(spec, coi).valid:
            continue
        for opt in OPTIMIZATIONS:
            impl_path = variant_path(coi.benchmark, opt)
            for mode in ["exact_only", "formal_all"]:
                case = {
                    "case_id": f"{coi.benchmark}|{coi.coi_name}|{opt}|{mode}",
                    "benchmark": coi.benchmark,
                    "coi_name": coi.coi_name,
                    "optimization": opt,
                    "anchor_mode": mode,
                    "eligible": True,
                    "executable": impl_path.exists(),
                    "structurally_valid": True,
                    "attempted": False,
                    "algorithmic_success": False,
                    "top_level_classification": "infrastructure_skip" if not impl_path.exists() else "algorithmic_failure",
                    "boundary_extension_ratio": "",
                    "failure_reason": "missing_impl_circuit" if not impl_path.exists() else "",
                }
                if impl_path.exists():
                    impl = CircuitGraph.from_blif(impl_path)
                    anchors = load_formal_anchors(coi.benchmark, opt, mode, spec, impl)
                    result = recover_semantic_boundary(spec, coi, anchors)
                    case.update(
                        {
                            "attempted": True,
                            "algorithmic_success": result.success,
                            "top_level_classification": "success" if result.success else "algorithmic_failure",
                            "boundary_extension_ratio": result.boundary_extension_ratio,
                            "failure_reason": result.failure_reason,
                        }
                    )
                rows.append(case)
    write_csv(OUT, rows)
    SUMMARY.write_text(summary(rows), encoding="utf-8")
    print(f"Wrote corrected optimized recovery rows: {len(rows)}")
    return 0


def summary(rows):
    attempted = [r for r in rows if str(r["attempted"]).lower() == "true"]
    successes = [r for r in attempted if r["top_level_classification"] == "success"]
    by_mode = defaultdict(lambda: [0, 0])
    for row in attempted:
        by_mode[row["anchor_mode"]][0] += 1
        by_mode[row["anchor_mode"]][1] += int(row["top_level_classification"] == "success")
    failures = Counter(row["failure_reason"] for row in attempted if row["top_level_classification"] != "success")
    lines = [
        "# Corrected Optimized Boundary-Recovery Summary",
        "",
        f"- Valid attempted cases: {len(attempted)}",
        f"- Successful cases: {len(successes)}",
        f"- Success rate: {(len(successes) / len(attempted) if attempted else 0):.1%}",
        "",
        "## Exact-only vs Formal-all",
        "",
    ]
    for mode, (total, success) in sorted(by_mode.items()):
        lines.append(f"- `{mode}`: {success} / {total}")
    lines.extend(["", "## Failure Taxonomy", ""])
    if failures:
        lines.extend(f"- {reason}: {count}" for reason, count in sorted(failures.items()))
    else:
        lines.append("No optimized algorithmic failures.")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
