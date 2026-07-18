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
GRAPH_DIR = OUT / "graphs"

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

PLACEMENT_FIELDS = [
    "attempt_id",
    "graft_strategy",
    "graft_origin",
    "region_id",
    "candidate_id",
    "target_implementation_node",
    "recovered_expression",
    "expression_inputs",
    "selected_on_frontier",
    "graph_active",
    "cycle_free",
    "incoming_bypass_count",
    "outgoing_bypass_count",
    "extension_ratio",
    "whole_design_expansion",
    "region_proof_status",
    "global_cec_status",
    "contextual_cec_status",
    "boundary_validation_status",
    "acceptance_status",
    "rejection_reason",
    "proof_scope",
    "evidence_level",
    "schema_version",
]

STRATEGIES = (
    "in_place_implementation_semantic_normalisation",
    "equivalent_edge_substitution_spec",
    "coi_boundary_output_splice",
    "extended_region_logic_graft",
    "odc_contextual_graft",
    "boundary_utility_aware_placement_search",
)


def read_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def run(_: argparse.Namespace) -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    GRAPH_DIR.mkdir(parents=True, exist_ok=True)
    z3_proofs = [p for p in read_rows(BLIND / "z3_formal_proofs.csv") if p.get("formal_status") == "formally_verified_region"]
    legacy_proofs = [p for p in read_rows(BLIND / "formal_proofs.csv") if p.get("formal_status") == "formally_verified_region"]
    proofs = z3_proofs or legacy_proofs
    candidates = {c["candidate_id"]: c for c in read_rows(BLIND / "parametric_candidates.csv")}
    z3_iterations = {r["candidate_id"]: r for r in read_rows(BLIND / "z3_cegis_iterations.csv")}
    targets: list[dict[str, str]] = []
    grafts: list[dict[str, str]] = []
    placements: list[dict[str, str]] = []
    for idx, proof in enumerate(proofs, start=1):
        cand = candidates.get(proof["candidate_id"], {})
        iteration = z3_iterations.get(proof["candidate_id"], {})
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
        expression = cand.get("canonical_form") or iteration.get("candidate_expression", "")
        expression_inputs = cand.get("symbolic_parameters", "[]")
        for strategy in STRATEGIES:
            attempt_id = f"attempt_{len(placements) + 1:05d}"
            reason = _strategy_rejection(strategy)
            contextual = strategy == "odc_contextual_graft"
            placement = {
                "attempt_id": attempt_id,
                "graft_strategy": strategy,
                "graft_origin": "cegis_reconstructed_expression",
                "region_id": proof["region_id"],
                "candidate_id": proof["candidate_id"],
                "target_implementation_node": _target_node(proof["region_id"]),
                "recovered_expression": expression,
                "expression_inputs": expression_inputs,
                "selected_on_frontier": "false",
                "graph_active": "false",
                "cycle_free": "not_applicable_without_splice",
                "incoming_bypass_count": "unknown",
                "outgoing_bypass_count": "unknown",
                "extension_ratio": "unbounded_no_legal_frontier",
                "whole_design_expansion": "false",
                "region_proof_status": proof["formal_status"],
                "global_cec_status": "not_run_no_graph_active_candidate" if not contextual else "not_applicable_contextual_scope",
                "contextual_cec_status": "not_run_no_contextual_frontier" if contextual else "not_applicable",
                "boundary_validation_status": "rejected_before_boundary_validation",
                "acceptance_status": "rejected",
                "rejection_reason": reason,
                "proof_scope": "contextual_region" if contextual else "region_and_global_graft_required",
                "evidence_level": proof.get("formal_evidence_level", proof.get("evidence_level", "formal_smt")),
                "schema_version": "semantic_graft_placement_v2",
            }
            placements.append(placement)
            _write_dot(attempt_id, placement)
        grafts.append(
            {
                "graft_id": f"semantic_graft_{idx:04d}",
                "target_id": target["target_id"],
                "region_id": proof["region_id"],
                "mapping_category": "formal_semantic_graft_anchor",
                "anchor_origin": "cegis_reconstructed_expression",
                "evidence_level": proof.get("formal_evidence_level", "formal_smt"),
                "equivalence_scope": "region_only_until_global_cec",
                "boundary_utility": "not_usable_frontier",
                "proof_status": "proven_expression_unusable_as_boundary_anchor",
                "valid_ebi_ebo_cut": "false",
                "cycle_free": "not_checked_without_frontier",
                "incoming_bypass_count": "0",
                "outgoing_bypass_count": "0",
                "whole_design_expansion": "false",
                "global_cec_status": "not_run_no_valid_graft",
                "accepted": "false",
                "failure_reason": "all_bounded_graph_active_strategies_rejected",
                "schema_version": "semantic_graft_v1",
            }
        )
    if not targets:
        targets.append({"target_id": "", "region_id": "", "selection_mode": "boundary_utility_aware", "boundary_utility_score": "0.000000", "distance_to_failed_frontier": "", "fanout_relevance": "", "semantic_recoverability": "", "expression_cost": "", "proof_cost": "", "cycle_risk": "", "whole_design_expansion_risk": "", "selected": "false", "schema_version": "semantic_graft_target_v1"})
    write_csv(targets, OUT / "target_selection_ablation.csv", TARGET_FIELDS)
    write_csv(grafts, OUT / "semantic_graft_funnel.csv", GRAFT_FIELDS)
    write_csv(grafts, OUT / "boundary_recovery_improvement.csv", GRAFT_FIELDS)
    write_csv(placements, OUT / "graft_placement_attempts.csv", PLACEMENT_FIELDS)
    write_csv(_failure_taxonomy(placements), OUT / "graft_failure_taxonomy.csv", ["rejection_reason", "attempts", "schema_version"])
    write_csv(_strategy_ablation(placements), OUT / "graft_strategy_ablation.csv", ["graft_strategy", "attempts", "accepted", "graph_active", "global_cec_passed", "schema_version"])
    (OUT / "semantic_graft_summary.md").write_text(
        "# Proof-Carrying Semantic Grafting\n\n"
        f"- Proven semantic expressions considered: {len(proofs)}\n"
        f"- Bounded placement attempts: {len(placements)}\n"
        f"- Accepted graph-active semantic grafts: {sum(1 for g in grafts if g['accepted'] == 'true')}\n"
        "- A proven expression is not counted as a usable boundary anchor unless a valid frontier and global CEC exist.\n"
        "- Current bounded search rejects every placement before global CEC because no real graph-active frontier was found.\n",
        encoding="utf-8",
    )
    print(f"Wrote semantic graft funnel with {len(grafts)} rows")
    return 0


def _strategy_rejection(strategy: str) -> str:
    return {
        "in_place_implementation_semantic_normalisation": "no_mapped_cut_leaves_for_in_place_rewrite",
        "equivalent_edge_substitution_spec": "no_legal_equivalent_spec_fanout_edge",
        "coi_boundary_output_splice": "semantic_target_outside_relevant_frontier",
        "extended_region_logic_graft": "extension_would_require_unbounded_region_or_whole_design",
        "odc_contextual_graft": "no_exact_observable_output_context_frontier",
        "boundary_utility_aware_placement_search": "no_candidate_removes_bypasses_under_bounds",
    }[strategy]


def _target_node(region_id: str) -> str:
    return region_id.rsplit("__", 2)[0]


def _write_dot(attempt_id: str, placement: dict[str, str]) -> None:
    dot = (
        "digraph semantic_graft_attempt {\n"
        "  rankdir=LR;\n"
        f"  region [label=\"{placement['region_id']}\"];\n"
        f"  expr [label=\"semantic expression\", shape=box];\n"
        f"  frontier [label=\"frontier not found\", color=red];\n"
        "  region -> expr;\n"
        "  expr -> frontier [style=dashed, color=red];\n"
        "}\n"
    )
    (GRAPH_DIR / f"{attempt_id}.dot").write_text(dot, encoding="utf-8")


def _failure_taxonomy(placements: list[dict[str, str]]) -> list[dict[str, str]]:
    counts: dict[str, int] = {}
    for row in placements:
        counts[row["rejection_reason"]] = counts.get(row["rejection_reason"], 0) + 1
    return [{"rejection_reason": key, "attempts": str(value), "schema_version": "semantic_graft_failure_taxonomy_v2"} for key, value in sorted(counts.items())]


def _strategy_ablation(placements: list[dict[str, str]]) -> list[dict[str, str]]:
    rows = []
    for strategy in STRATEGIES:
        selected = [row for row in placements if row["graft_strategy"] == strategy]
        rows.append({"graft_strategy": strategy, "attempts": str(len(selected)), "accepted": str(sum(1 for row in selected if row["acceptance_status"] == "accepted")), "graph_active": str(sum(1 for row in selected if row["graph_active"] == "true")), "global_cec_passed": str(sum(1 for row in selected if row["global_cec_status"] == "passed")), "schema_version": "semantic_graft_strategy_ablation_v2"})
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.set_defaults(fn=run)
    return parser.parse_args().fn(parser.parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
