"""Shared helpers and schemas for Phase 4 direct semantic recovery."""

from __future__ import annotations

import csv
import json
import re
from collections import defaultdict
from pathlib import Path

from semantic_ast import SemanticExpr, expr_from_tree
from semantic_grammar import GRAMMAR_FAMILIES
from semantic_region import write_csv


SEMANTIC_DIRECT_SCHEMA_VERSION = "semantic_direct_recovery_v1"

DIRECT_CANDIDATE_FIELDS = [
    "candidate_id",
    "region_id",
    "case_id",
    "family",
    "operator",
    "optimization",
    "source_type",
    "family_order_mode",
    "grammar_family",
    "candidate_rank",
    "ground_truth_family_rank",
    "first_attempted_family",
    "families_attempted",
    "input_bus_count",
    "output_width",
    "expression_id",
    "expression_operator",
    "operands",
    "input_types",
    "output_type",
    "width",
    "signedness",
    "extension_mode",
    "truncation_mode",
    "slice_range",
    "constant_value",
    "expression_depth",
    "canonical_form",
    "rtl_text",
    "rtl_cost",
    "expression_json",
    "schema_version",
]

SIMULATION_FIELDS = [
    "candidate_id",
    "region_id",
    "simulation_filter_mode",
    "sample_count",
    "sample_matches",
    "sample_mismatches",
    "sample_match_rate",
    "first_mismatch_pattern",
    "mismatch_output_bits",
    "simulation_runtime",
    "simulation_status",
    "simulation_evidence_level",
    "schema_version",
]

RANKING_FIELDS = [
    "candidate_id",
    "region_id",
    "candidate_ranking_mode",
    "rank_after_simulation",
    "ranking_score",
    "simulation_status",
    "sample_match_rate",
    "grammar_family",
    "expression_depth",
    "rtl_cost",
]

FORMAL_FIELDS = [
    "candidate_id",
    "region_id",
    "formal_status",
    "proof_scope",
    "formal_evidence_level",
    "formal_patterns",
    "counterexample_available",
    "counterexample_assignment",
    "counterexample_output_difference",
    "counterexample_source",
    "formal_runtime",
    "formal_skip_reason",
    "schema_version",
]

VERIFIED_FIELDS = [
    "candidate_id",
    "region_id",
    "case_id",
    "family",
    "operator",
    "optimization",
    "source_type",
    "grammar_family",
    "classification",
    "proof_scope",
    "canonical_form",
    "rtl_text",
    "candidate_rtl_cost",
    "input_gate_count",
    "reduction_rate",
    "reduction_rate_ge_70",
    "formal_runtime",
]

BEST_FIELDS = VERIFIED_FIELDS + ["selection_rank"]

RECOVERY_FIELDS = [
    "scope",
    "group",
    "eligible_regions",
    "regions_with_direct_candidates",
    "generated_candidates",
    "canonical_candidates",
    "simulation_checked",
    "simulation_survivors",
    "formal_checks",
    "verified_candidates",
    "recovered_regions",
    "formal_recovery_rate",
    "exact_syntactic_recovery_rate",
    "canonical_syntactic_recovery_rate",
    "equivalent_alternative_rate",
    "mean_verified_rtl_cost",
    "median_verified_rtl_cost",
    "mean_reduction_rate",
    "cases_above_70_reduction",
]

FAILURE_FIELDS = ["region_id", "case_id", "optimization", "source_type", "stage", "failure_reason"]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def parse_json(value: str, default):
    if not value:
        return default
    return json.loads(value)


def load_region_rows(result_dir: Path) -> dict[str, dict[str, str]]:
    return {row["region_id"]: row for row in read_csv(result_dir / "semantic_regions.csv") if row["eligible"] == "true"}


def load_manifest(result_dir: Path) -> dict[str, dict[str, str]]:
    return {row["case_id"]: row for row in read_csv(result_dir / "semantic_benchmark_manifest.csv")}


def load_bus_hypotheses(result_dir: Path, *, max_rank: int = 12) -> dict[tuple[str, str], list[dict[str, object]]]:
    grouped: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    for row in read_csv(result_dir / "semantic_bus_hypotheses.csv"):
        if row["inference_mode"] != "inferred_bus_mode" or int(row["rank"]) > max_rank:
            continue
        grouped[(row["region_id"], row["direction"])].append(
            {
                "name": row["ground_truth_bus_name_if_known"] or _name_from_hypothesis(row),
                "role": row["role"],
                "width": int(row["width"]),
                "signed": row["signedness_hypothesis"] == "signed",
                "ordered_member_nodes": tuple(parse_json(row["ordered_member_nodes"], [])),
                "rank": int(row["rank"]),
                "hypothesis_id": row["bus_hypothesis_id"],
            }
        )
    for key in list(grouped):
        grouped[key].sort(key=lambda bus: (int(bus["rank"]), str(bus["name"])))
    return grouped


def _name_from_hypothesis(row: dict[str, str]) -> str:
    members = parse_json(row["ordered_member_nodes"], [])
    if not members:
        return row["bus_hypothesis_id"].split("__")[-1]
    first = str(members[0])
    return first.rsplit("_", 1)[0] if "_" in first else first


def load_family_rankings(result_dir: Path) -> dict[str, list[str]]:
    by_region: dict[str, list[tuple[int, str]]] = defaultdict(list)
    mapping = {
        "arithmetic_add_sub": "arithmetic_direct",
        "arithmetic_multiply": "arithmetic_direct",
        "arithmetic_affine_or_mac": "arithmetic_direct",
        "boolean_bitwise": "boolean_direct",
        "control_mux": "control_direct",
        "comparison": "comparison_direct",
        "bit_manipulation": "bitmanip_direct",
        "unknown": "bitmanip_direct",
    }
    for row in read_csv(result_dir / "semantic_family_rankings.csv"):
        by_region[row["region_id"]].append((int(row["rank"]), mapping.get(row["candidate_family"], "bitmanip_direct")))
    ordered: dict[str, list[str]] = {}
    for region_id, rows in by_region.items():
        seen = []
        for _, family in sorted(rows):
            if family not in seen:
                seen.append(family)
        ordered[region_id] = seen + [family for family in GRAMMAR_FAMILIES if family not in seen]
    return ordered


def fixed_family_order() -> list[str]:
    return list(GRAMMAR_FAMILIES)


def oracle_family_order(row: dict[str, str]) -> list[str]:
    family = {
        "arithmetic": "arithmetic_direct",
        "boolean": "boolean_direct",
        "control": "control_direct",
        "comparison": "comparison_direct",
        "bitmanip": "bitmanip_direct",
    }.get(row["family"], "bitmanip_direct")
    return [family] + [item for item in GRAMMAR_FAMILIES if item != family]


def expr_from_candidate_row(row: dict[str, str]) -> SemanticExpr:
    return expr_from_tree(json.loads(row["expression_json"]))


def normalize_expr_text(value: str) -> str:
    return re.sub(r"\s+", "", value.replace("(", "").replace(")", "")).lower()


def classify_verified_expression(candidate: dict[str, str], region: dict[str, str]) -> str:
    if normalize_expr_text(candidate["rtl_text"]) == normalize_expr_text(region["ground_truth_expression"]):
        return "exact_syntactic_match"
    if region["operator"] in candidate["canonical_form"] or region["operator"] in candidate["grammar_family"]:
        return "canonical_syntactic_match"
    if region.get("ground_truth_expression"):
        return "formally_equivalent_alternative"
    return "formally_verified_but_ground_truth_unavailable"


def candidate_sort_key(row: dict[str, str]) -> tuple[float, int, int, str]:
    return (-float(row.get("sample_match_rate", "0") or 0), int(row.get("expression_depth", "0") or 0), int(row.get("rtl_cost", "0") or 0), row["candidate_id"])
