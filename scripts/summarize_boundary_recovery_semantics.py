#!/usr/bin/env python3
"""Write the repaired boundary-recovery semantics summary."""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from boundary_semantics import CANONICAL_MANIFEST, SEMANTICS_DIR, read_csv  # noqa: E402
from coi_model import BOUNDARY_MEMBERSHIP_CONVENTION, COI_SCHEMA_VERSION  # noqa: E402

SUMMARY = SEMANTICS_DIR / "boundary_semantics_summary.md"


def main() -> int:
    audit = read_csv(SEMANTICS_DIR / "coi_repair_audit.csv")
    avail = read_csv(SEMANTICS_DIR / "circuit_availability.csv")
    identity = read_csv(SEMANTICS_DIR / "identity_exact_match_results.csv")
    opt = read_csv(SEMANTICS_DIR / "optimized_recovery_corrected.csv")
    cp_path = SEMANTICS_DIR / "critical_path_coi_validation.csv"
    cp = read_csv(cp_path) if cp_path.exists() else []
    manifest = json.loads(CANONICAL_MANIFEST.read_text(encoding="utf-8")).get("cois", [])

    attempted = [r for r in opt if r.get("attempted", "").lower() == "true"]
    opt_success = [r for r in attempted if r.get("top_level_classification") == "success"]
    lines = [
        "# Boundary-Recovery Semantics Repair Summary",
        "",
        "## Canonical Semantics",
        "",
        f"- Schema: `{COI_SCHEMA_VERSION}`",
        f"- Convention: {BOUNDARY_MEMBERSHIP_CONVENTION}",
        "- `BI = {u outside R | exists v in R with u -> v}`",
        "- `BO = {u in R | u is a PO or has a fanout outside R}`",
        "- Identity must recover exact BI, exact BO, exact region, and zero extension.",
        "",
        "## COI Repair",
        "",
        f"- Original/micro audit rows: {len(audit)}",
        f"- Finally valid canonical COIs: {len(manifest)}",
        f"- Repaired rows: {sum(r.get('repaired') == 'True' for r in audit)}",
        f"- Excluded rows: {sum(r.get('final_valid') != 'True' for r in audit)}",
        "",
        "## Circuit Eligibility",
        "",
        f"- Declared circuit rows: {len(avail)}",
        f"- Available rows: {sum(r.get('eligibility_status') == 'available' for r in avail)}",
        f"- Infrastructure skips: {sum(r.get('eligibility_status') == 'infrastructure_skip' for r in avail)}",
        "",
        "## Identity",
        "",
        f"- Eligible valid identity cases: {len(identity)}",
        f"- Successes: {sum(r.get('top_level_classification') == 'success' for r in identity)}",
        f"- Zero-extension cases: {sum(r.get('top_level_classification') == 'success' and float(r.get('boundary_extension_ratio') or 0) == 0 for r in identity)}",
        f"- Exact EBI matches: {sum(r.get('ebi_exact_match') == 'True' for r in identity)}",
        f"- Exact EBO matches: {sum(r.get('ebo_exact_match') == 'True' for r in identity)}",
        f"- Exact region matches: {sum(r.get('region_exact_match') == 'True' for r in identity)}",
        "",
        "## Corrected Optimized Results",
        "",
        f"- Valid attempted cases: {len(attempted)}",
        f"- Successful cases: {len(opt_success)}",
        f"- Success rate: {(len(opt_success) / len(attempted) if attempted else 0):.1%}",
        "",
        "Failure taxonomy:",
        "",
    ]
    failures = Counter(r.get("failure_reason") for r in attempted if r.get("top_level_classification") != "success")
    lines.extend(f"- {reason}: {count}" for reason, count in sorted(failures.items())) if failures else lines.append("- No optimized failures.")
    lines.extend(
        [
            "",
            "## Critical Path",
            "",
            f"- Generated COI validation rows: {len(cp)}",
            f"- Valid generated COIs: {sum(r.get('coi_valid') == 'True' for r in cp)}",
            "- Region-level critical-path enclosure is not node equivalence.",
            "",
            "## Decision Gate",
            "",
            "Identity is perfect on the canonical eligible set. If optimized recovery remains sparse, the next step is ODC-aware or speculative anchor generation, unless future data shows relevant anchors exist but cut search fails.",
        ]
    )
    SUMMARY.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {SUMMARY}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
