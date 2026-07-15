#!/usr/bin/env python3
"""Check ODC anchor result schemas and evidence semantics."""

from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "odc_anchor_generation"

REQUIRED = {
    "odc_candidate_features.csv": {"case_id", "spec_node", "impl_node", "simulation_filter_status", "sampled_mismatch_rate"},
    "odc_formal_proofs.csv": {"case_id", "proof_status", "mapping_category", "evidence_level", "equivalence_scope", "context_mode"},
    "odc_proven_anchors.csv": {"spec_node", "impl_node", "mapping_category", "evidence_level", "equivalence_scope", "proof_status"},
    "odc_boundary_recovery_cases.csv": {"case_id", "anchor_mode", "context_mode", "success", "selected_odc_anchor_count", "boundary_contextual_validation_status"},
    "odc_anchor_usage.csv": {"context_mode", "anchor_mode", "search_mode", "successes", "selected_odc_anchor_count"},
}


def main() -> int:
    for name, cols in REQUIRED.items():
        path = OUT / name
        if not path.exists():
            raise SystemExit(f"missing {path}")
        with path.open(newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            missing = cols - set(reader.fieldnames or [])
            if missing:
                raise SystemExit(f"{name} missing columns {sorted(missing)}")
            rows = list(reader)
        if name == "odc_formal_proofs.csv":
            for row in rows:
                if row["proof_status"] != "proven_odc_valid" and row["evidence_level"] == "formal_contextual":
                    raise SystemExit("non-proven ODC row labeled formal_contextual")
                if row["mapping_category"] == "formal_odc_valid_anchor" and row["equivalence_scope"] != "contextual":
                    raise SystemExit("ODC anchor mislabeled as non-contextual")
        if name == "odc_proven_anchors.csv":
            for row in rows:
                if row["proof_status"] != "proven_odc_valid":
                    raise SystemExit("unproven row in odc_proven_anchors.csv")
                if row["mapping_category"] != "formal_odc_valid_anchor":
                    raise SystemExit("proven ODC anchor has wrong category")
    identity_path = ROOT / "results" / "boundary_recovery_semantics" / "identity_exact_match_results.csv"
    with identity_path.open(newline="", encoding="utf-8") as fh:
        identity = list(csv.DictReader(fh))
    if len(identity) != 14 or any(r["top_level_classification"] != "success" for r in identity):
        raise SystemExit("identity regression is not perfect")
    print("ODC anchor result check: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
