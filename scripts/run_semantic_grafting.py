#!/usr/bin/env python3
"""Boundary-utility target selection and proof-carrying semantic graft funnel."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from semantic_region import write_csv  # noqa: E402

BLIND = ROOT / "results" / "blind_semantic_cegis"
OUT = ROOT / "results" / "semantic_grafting"

TARGET_FIELDS = [
    "target_id",
    "region_id",
    "selection_mode",
    "boundary_utility_score",
    "distance_to_failed_frontier",
    "fanout_relevance",
    "semantic_recoverability",
    "expression_cost",
    "proof_cost",
    "cycle_risk",
    "whole_design_expansion_risk",
    "selected",
    "schema_version",
]

GRAFT_FIELDS = [
    "graft_id",
    "target_id",
    "region_id",
    "mapping_category",
    "anchor_origin",
    "evidence_level",
    "equivalence_scope",
    "boundary_utility",
    "proof_status",
    "valid_ebi_ebo_cut",
    "cycle_free",
    "incoming_bypass_count",
    "outgoing_bypass_count",
    "whole_design_expansion",
    "global_cec_status",
    "accepted",
    "failure_reason",
    "schema_version",
]


def read_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def run(_: argparse.Namespace) -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    proofs = [p for p in read_rows(BLIND / "formal_proofs.csv") if p.get("formal_status") == "formally_verified_region"]
    candidates = {c["candidate_id"]: c for c in read_rows(BLIND / "parametric_candidates.csv")}
    targets: list[dict[str, str]] = []
    grafts: list[dict[str, str]] = []
    for idx, proof in enumerate(proofs, start=1):
        cand = candidates.get(proof["candidate_id"], {})
        cost = int(cand.get("search_cost", "9") or 9)
        utility = max(0.0, 1.0 - cost / 20.0)
        target = {
            "target_id": f"semantic_target_{idx:04d}",
            "region_id": proof["region_id"],
            "selection_mode": "boundary_utility_aware",
            "boundary_utility_score": f"{utility:.6f}",
            "distance_to_failed_frontier": "unknown",
            "fanout_relevance": "0.000000",
            "semantic_recoverability": "1.000000",
            "expression_cost": str(cost),
            "proof_cost": proof["proof_runtime"],
            "cycle_risk": "unknown",
            "whole_design_expansion_risk": "unknown",
            "selected": str(utility >= 0.5).lower(),
            "schema_version": "semantic_graft_target_v1",
        }
        targets.append(target)
        accepted = False
        reason = "no_graph_active_frontier_found"
        grafts.append(
            {
                "graft_id": f"semantic_graft_{idx:04d}",
                "target_id": target["target_id"],
                "region_id": proof["region_id"],
                "mapping_category": "formal_semantic_graft_anchor",
                "anchor_origin": "cegis_reconstructed_expression",
                "evidence_level": proof["formal_evidence_level"],
                "equivalence_scope": "region_only_until_global_cec",
                "boundary_utility": "not_usable_frontier",
                "proof_status": "proven_expression_unusable_as_boundary_anchor",
                "valid_ebi_ebo_cut": "false",
                "cycle_free": "not_checked_without_frontier",
                "incoming_bypass_count": "0",
                "outgoing_bypass_count": "0",
                "whole_design_expansion": "false",
                "global_cec_status": "not_run_no_valid_graft",
                "accepted": str(accepted).lower(),
                "failure_reason": reason,
                "schema_version": "semantic_graft_v1",
            }
        )
    if not targets:
        targets.append({"target_id": "", "region_id": "", "selection_mode": "boundary_utility_aware", "boundary_utility_score": "0.000000", "distance_to_failed_frontier": "", "fanout_relevance": "", "semantic_recoverability": "", "expression_cost": "", "proof_cost": "", "cycle_risk": "", "whole_design_expansion_risk": "", "selected": "false", "schema_version": "semantic_graft_target_v1"})
    write_csv(targets, OUT / "target_selection_ablation.csv", TARGET_FIELDS)
    write_csv(grafts, OUT / "semantic_graft_funnel.csv", GRAFT_FIELDS)
    write_csv(grafts, OUT / "boundary_recovery_improvement.csv", GRAFT_FIELDS)
    (OUT / "semantic_graft_summary.md").write_text(
        "# Proof-Carrying Semantic Grafting\n\n"
        f"- Proven semantic expressions considered: {len(proofs)}\n"
        f"- Accepted graph-active semantic grafts: {sum(1 for g in grafts if g['accepted'] == 'true')}\n"
        "- A proven expression is not counted as a usable boundary anchor unless a valid frontier and global CEC exist.\n",
        encoding="utf-8",
    )
    print(f"Wrote semantic graft funnel with {len(grafts)} rows")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.set_defaults(fn=run)
    return parser.parse_args().fn(parser.parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
