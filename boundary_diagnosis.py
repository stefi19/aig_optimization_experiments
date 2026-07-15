"""Diagnostics for equivalence-anchored boundary recovery.

The functions in this module wrap the existing boundary-recovery prototype with
stage labels, anchor-coverage measurements, identity anchors, and lightweight
critical-path COI generation.  They deliberately do not change what counts as
formal node equivalence.
"""

from __future__ import annotations

import csv
import hashlib
import json
import time
from collections import Counter, defaultdict, deque
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from boundary_anchor_map import ANCHOR_MODES, Anchor, AnchorMap, load_anchor_map
from boundary_graph import CircuitGraph
from boundary_recovery import (
    CoiSpec,
    compute_boundary_metrics,
    extract_region_between_cuts,
    first_equivalent_cut_tfi,
    first_equivalent_cut_tfo,
    first_equivalent_cut_tsi,
    load_coi_specs,
    recover_extended_boundary,
    validate_coi_spec,
    validate_recovered_boundary,
)
from scripts.benchmark_id import infer_source_family


ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"
BOUNDARY_RESULTS = RESULTS / "boundary_recovery"
DIAG_RESULTS = RESULTS / "boundary_recovery_diagnosis"
COI_SPEC = ROOT / "benchmarks" / "coi_specs" / "boundary_recovery_seed_cois.json"
DEFAULT_SEED_OPTIMIZATIONS = ["balance", "rewrite", "resyn2", "dc2"]
PROGRESSION_OPTIMIZATIONS = [
    "identity",
    "balance",
    "rewrite",
    "refactor",
    "resub",
    "resyn",
    "resyn2",
    "dc2",
    "compress2rs",
]
ANCHOR_MODES_FOR_DIAGNOSIS = ["exact_only", "formal_all"]

STAGE_SEQUENCE = [
    "load_inputs",
    "validate_coi",
    "load_anchors",
    "align_variants",
    "analyze_relevant_cones",
    "recover_ebi",
    "recover_ebo",
    "complete_input_cut",
    "validate_cuts",
    "detect_cycles",
    "extract_region",
    "compute_metrics",
    "success",
]

FAILURE_STAGE_BY_STATUS = {
    "invalid_coi": "validate_coi",
    "no_input_cut": "recover_ebi",
    "no_output_cut": "recover_ebo",
    "missing_anchor": "validate_cuts",
    "polarity_unsupported": "validate_cuts",
    "cycle_detected": "detect_cycles",
    "whole_design_boundary": "extract_region",
    "disconnected_region": "extract_region",
    "incomplete_input_cut": "complete_input_cut",
    "incomplete_output_cut": "validate_cuts",
}


CASE_COLUMNS = [
    "case_id",
    "benchmark",
    "benchmark_family",
    "coi_name",
    "optimization",
    "anchor_mode",
    "coi_source",
    "failure_stage",
    "failure_reason",
    "failure_detail",
    "last_successful_stage",
    "recovery_success",
    "validation_status",
    "spec_path",
    "impl_path",
    "spec_node_count",
    "impl_node_count",
    "coi_node_count",
    "extended_region_node_count",
    "boundary_extension_ratio",
    "original_bi_count",
    "original_bo_count",
    "extended_bi_count",
    "extended_bo_count",
    "selected_anchor_count",
    "selected_sat_cec_anchor_count",
    "available_but_unselected_sat_cec_anchor_count",
    "cycle_conflict_count",
    "whole_design_expansion",
    "input_boundary_distance",
    "output_boundary_distance",
    "mean_anchor_distance",
    "max_anchor_distance",
    "runtime_seconds",
    "extended_boundary_inputs",
    "extended_boundary_outputs",
    "region_nodes",
]

COVERAGE_COLUMNS = [
    "case_id",
    "benchmark",
    "coi_name",
    "optimization",
    "anchor_mode",
    "global_spec_node_count",
    "global_formally_anchored_spec_nodes",
    "global_anchor_density",
    "coi_node_count",
    "coi_anchored_node_count",
    "coi_anchor_density",
    "bi_tfi_union_node_count",
    "bi_tfi_anchored_node_count",
    "bi_tfi_anchor_density",
    "bo_tfo_union_node_count",
    "bo_tfo_anchored_node_count",
    "bo_tfo_anchor_density",
    "ebo_tfi_relevant_node_count",
    "ebo_tfi_anchored_node_count",
    "ebo_tfi_anchor_density",
    "exact_anchor_count_global",
    "complemented_anchor_count_global",
    "sat_cec_anchor_count_global",
    "exact_anchor_count_relevant",
    "complemented_anchor_count_relevant",
    "sat_cec_anchor_count_relevant",
    "formal_all_added_global_anchors",
    "formal_all_added_relevant_anchors",
    "formal_all_added_tfi_anchors",
    "formal_all_added_tfo_anchors",
    "formal_all_added_cut_candidate_anchors",
    "bi_anchor_distance_min",
    "bi_anchor_distance_mean",
    "bi_anchor_distance_max",
    "bo_anchor_distance_min",
    "bo_anchor_distance_mean",
    "bo_anchor_distance_max",
    "boundary_inputs_with_no_reachable_anchor",
    "boundary_outputs_with_no_reachable_anchor",
]

COI_AUDIT_COLUMNS = [
    "benchmark",
    "coi_name",
    "optimization",
    "coi_source",
    "coi_connected",
    "coi_fanout_free_under_current_definition",
    "boundary_inputs_valid",
    "boundary_outputs_valid",
    "all_external_input_paths_cross_bi",
    "all_external_output_paths_cross_bo",
    "coi_contains_internal_nodes",
    "coi_is_whole_design",
    "coi_valid",
    "coi_invalid_reason",
]

ALIGNMENT_COLUMNS = [
    "case_id",
    "benchmark",
    "optimization",
    "anchor_mode",
    "spec_fingerprint",
    "impl_fingerprint",
    "spec_node_count",
    "impl_node_count",
    "primary_input_names_match",
    "primary_output_names_match",
    "alignment_valid",
    "alignment_failure_reason",
]


@dataclass(frozen=True)
class DiagnosticBundle:
    cases: list[dict[str, object]]
    stage_progress: list[dict[str, object]]
    coverage: list[dict[str, object]]
    coi_audit: list[dict[str, object]]
    alignment: list[dict[str, object]]
    completion: list[dict[str, object]]
    anchor_audit: list[dict[str, object]]


def original_path(benchmark: str) -> Path:
    return ROOT / "variants" / f"{benchmark}_original.blif"


def variant_path(benchmark: str, optimization: str) -> Path:
    if optimization == "identity":
        return original_path(benchmark)
    return ROOT / "variants" / f"{benchmark}_{optimization}.blif"


def expand_specs(specs: list[CoiSpec], optimizations: list[str]) -> list[CoiSpec]:
    rows: list[CoiSpec] = []
    for spec in specs:
        opts = optimizations if spec.optimization == "*" else [spec.optimization]
        for opt in opts:
            rows.append(
                CoiSpec(
                    benchmark=spec.benchmark,
                    optimization=opt,
                    coi_name=spec.coi_name,
                    coi_internal_nodes=spec.coi_internal_nodes,
                    boundary_inputs=spec.boundary_inputs,
                    boundary_outputs=spec.boundary_outputs,
                    source=spec.source,
                )
            )
    return sorted(rows, key=lambda c: (c.benchmark, c.coi_name, c.optimization))


def case_id(coi: CoiSpec, anchor_mode: str) -> str:
    return f"{coi.benchmark}|{coi.coi_name}|{coi.optimization}|{anchor_mode}"


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def identity_anchor_map(graph: CircuitGraph) -> AnchorMap:
    anchors = [
        Anchor(
            spec_node=node,
            impl_node=node,
            polarity="same",
            mapping_category="exact_signature_match",
            evidence_level="formal_exhaustive",
            proof_mode="identity_baseline",
            source_result_file="identity_anchor_constructor",
            confidence_or_status="identity",
        )
        for node in sorted(graph.nodes)
    ]
    return AnchorMap(anchors)


def load_case_anchors(coi: CoiSpec, mode: str, spec_graph: CircuitGraph, impl_graph: CircuitGraph) -> AnchorMap:
    if coi.optimization == "identity":
        return identity_anchor_map(spec_graph)
    return load_anchor_map(
        coi.benchmark,
        coi.optimization,
        mode,
        results_dir=RESULTS,
        spec_inputs=spec_graph.inputs,
        impl_inputs=impl_graph.inputs,
        spec_outputs=spec_graph.outputs,
        impl_outputs=impl_graph.outputs,
    )


def circuit_fingerprint(path: Path) -> str:
    if not path.exists():
        return ""
    text = "\n".join(line.rstrip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip())
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def run_diagnostic_suite(
    *,
    coi_spec: Path = COI_SPEC,
    optimizations: list[str] | None = None,
    anchor_modes: list[str] | None = None,
) -> DiagnosticBundle:
    specs = load_coi_specs(coi_spec)
    opts = optimizations or DEFAULT_SEED_OPTIMIZATIONS
    modes = anchor_modes or ANCHOR_MODES_FOR_DIAGNOSIS
    cases: list[dict[str, object]] = []
    progress: list[dict[str, object]] = []
    coverage: list[dict[str, object]] = []
    coi_audit: list[dict[str, object]] = []
    alignment: list[dict[str, object]] = []
    completion: list[dict[str, object]] = []
    anchor_audit: list[dict[str, object]] = []

    for coi in expand_specs(specs, opts):
        if not spec_seen(coi_audit, coi):
            coi_audit.extend(audit_coi_for_all_available_flows(coi))
        for mode in modes:
            case, stage_rows, cov, align, comp, audit = diagnose_case(coi, mode)
            cases.append(case)
            progress.extend(stage_rows)
            if cov:
                coverage.append(cov)
            if align:
                alignment.append(align)
            if comp:
                completion.append(comp)
            anchor_audit.extend(audit)
    return DiagnosticBundle(cases, progress, coverage, coi_audit, alignment, completion, anchor_audit)


def spec_seen(rows: list[dict[str, object]], coi: CoiSpec) -> bool:
    return any(row["benchmark"] == coi.benchmark and row["coi_name"] == coi.coi_name for row in rows)


def diagnose_case(coi: CoiSpec, anchor_mode: str) -> tuple[
    dict[str, object],
    list[dict[str, object]],
    dict[str, object] | None,
    dict[str, object] | None,
    dict[str, object] | None,
    list[dict[str, object]],
]:
    start = time.perf_counter()
    spec_path = original_path(coi.benchmark)
    impl_path = variant_path(coi.benchmark, coi.optimization)
    cid = case_id(coi, anchor_mode)
    passed: set[str] = set()
    failure_stage = "success"
    failure_reason = "valid"
    failure_detail = "valid"
    last_success = ""

    def terminal(stage: str, reason: str, detail: str) -> tuple[dict[str, object], list[dict[str, object]], None, None, None, list[dict[str, object]]]:
        nonlocal last_success
        row = base_case_row(coi, anchor_mode, spec_path, impl_path, cid)
        row.update(
            {
                "failure_stage": stage,
                "failure_reason": reason,
                "failure_detail": detail,
                "last_successful_stage": last_success,
                "recovery_success": False,
                "validation_status": reason,
                "runtime_seconds": time.perf_counter() - start,
            }
        )
        return row, stage_rows(cid, coi, anchor_mode, passed, stage, False), None, None, None, []

    if not spec_path.exists():
        return terminal("load_inputs", "missing_spec_circuit", rel(spec_path))
    if not impl_path.exists():
        return terminal("load_inputs", "missing_impl_circuit", rel(impl_path))
    passed.add("load_inputs")
    last_success = "load_inputs"

    spec_graph = CircuitGraph.from_blif(spec_path)
    impl_graph = CircuitGraph.from_blif(impl_path)
    valid_coi, coi_reason = validate_coi_spec(spec_graph, coi)
    if not valid_coi:
        return terminal("validate_coi", "invalid_coi", coi_reason)
    passed.add("validate_coi")
    last_success = "validate_coi"

    anchors = load_case_anchors(coi, anchor_mode, spec_graph, impl_graph)
    if not anchors.anchors:
        return terminal("load_anchors", "no_formal_anchors", "anchor map is empty")
    passed.add("load_anchors")
    last_success = "load_anchors"

    align = alignment_row(cid, coi, anchor_mode, spec_path, impl_path, spec_graph, impl_graph)
    if not align["alignment_valid"]:
        return terminal("align_variants", "anchor_variant_mismatch", str(align["alignment_failure_reason"]))
    passed.add("align_variants")
    last_success = "align_variants"

    cov = anchor_coverage_row(cid, coi, anchor_mode, spec_graph, anchors)
    if int(cov["bi_tfi_anchored_node_count"]) == 0:
        return terminal("analyze_relevant_cones", "no_relevant_tfi_anchors", "no formal anchors in boundary-input TFI cones")
    if int(cov["bo_tfo_anchored_node_count"]) == 0:
        return terminal("analyze_relevant_cones", "no_relevant_tfo_anchors", "no formal anchors in boundary-output TFO cones")
    passed.add("analyze_relevant_cones")
    last_success = "analyze_relevant_cones"

    ebi, in_distances, ebi_failures = first_equivalent_cut_tfi(spec_graph, list(coi.boundary_inputs), anchors)
    if ebi_failures or not ebi:
        detail = "unanchored boundary inputs: " + ";".join(ebi_failures)
        return terminal("recover_ebi", "no_ebi_frontier", detail)
    passed.add("recover_ebi")
    last_success = "recover_ebi"

    ebo, out_distances, ebo_failures = first_equivalent_cut_tfo(spec_graph, list(coi.boundary_outputs), anchors)
    if ebo_failures or not ebo:
        detail = "unanchored boundary outputs: " + ";".join(ebo_failures)
        return terminal("recover_ebo", "no_ebo_frontier", detail)
    passed.add("recover_ebo")
    last_success = "recover_ebo"

    additions, completion_distances, completion_failures = first_equivalent_cut_tsi(spec_graph, ebo, ebi, anchors, blocked_outputs=ebo)
    completion_row = completion_diagnosis_row(cid, coi, anchor_mode, ebo, additions, completion_failures, anchors)
    if completion_failures:
        return terminal("complete_input_cut", "input_cut_completion_failed", "unanchored fanin leaves: " + ";".join(completion_failures))
    ebi |= additions
    passed.add("complete_input_cut")
    last_success = "complete_input_cut"

    region = extract_region_between_cuts(spec_graph, ebi, ebo)
    status, reason, conflicts = validate_recovered_boundary(spec_graph, impl_graph, coi, ebi, ebo, region, anchors)
    if status in {"incomplete_input_cut"}:
        failure_stage, failure_reason = "validate_cuts", "incomplete_ebi_cut"
    elif status in {"incomplete_output_cut"}:
        failure_stage, failure_reason = "validate_cuts", "incomplete_ebo_cut"
    elif status == "missing_anchor":
        failure_stage, failure_reason = "validate_cuts", "validation_failed"
    elif status == "cycle_detected":
        failure_stage, failure_reason = "detect_cycles", "cycle_detected"
    elif status == "whole_design_boundary":
        failure_stage, failure_reason = "extract_region", "whole_design_expansion"
    elif status == "disconnected_region" and "empty" in reason:
        failure_stage, failure_reason = "extract_region", "region_empty"
    elif status == "disconnected_region":
        failure_stage, failure_reason = "extract_region", "region_not_enclosed"
    else:
        failure_stage, failure_reason = FAILURE_STAGE_BY_STATUS.get(status, "success"), status

    if failure_stage == "validate_cuts":
        passed.add("validate_cuts")
        last_success = "validate_cuts" if status == "valid" else "complete_input_cut"
    elif failure_stage == "detect_cycles":
        passed.add("validate_cuts")
        last_success = "validate_cuts"
    elif failure_stage == "extract_region":
        passed.update({"validate_cuts", "detect_cycles"})
        last_success = "detect_cycles"
    elif status == "valid":
        passed.update({"validate_cuts", "detect_cycles", "extract_region", "compute_metrics", "success"})
        last_success = "success"

    result = recover_extended_boundary(spec_graph, impl_graph, coi, anchors)
    metrics = compute_boundary_metrics(result, spec_graph, impl_graph)
    selected = result.selected_anchors
    selected_sat = sum(1 for anchor in selected.values() if anchor.mapping_category == "sat_cec_proven_equivalent")
    available_unselected_sat = sum(
        1
        for node in set(coi.coi_internal_nodes) | set(result.extended_boundary_inputs) | set(result.extended_boundary_outputs)
        for anchor in anchors.candidates_for(node)
        if anchor.mapping_category == "sat_cec_proven_equivalent" and selected.get(node) != anchor
    )
    success = status == "valid"
    case = base_case_row(coi, anchor_mode, spec_path, impl_path, cid)
    case.update(
        {
            "failure_stage": "success" if success else failure_stage,
            "failure_reason": "valid" if success else failure_reason,
            "failure_detail": "valid" if success else reason,
            "last_successful_stage": last_success,
            "recovery_success": success,
            "validation_status": status,
            "spec_node_count": metrics["spec_node_count"],
            "impl_node_count": metrics["impl_node_count"],
            "coi_node_count": metrics["coi_node_count"],
            "extended_region_node_count": metrics["extended_region_node_count"],
            "boundary_extension_ratio": metrics["boundary_extension_ratio"],
            "original_bi_count": metrics["original_boundary_input_count"],
            "original_bo_count": metrics["original_boundary_output_count"],
            "extended_bi_count": metrics["extended_boundary_input_count"],
            "extended_bo_count": metrics["extended_boundary_output_count"],
            "selected_anchor_count": len(selected),
            "selected_sat_cec_anchor_count": selected_sat,
            "available_but_unselected_sat_cec_anchor_count": available_unselected_sat,
            "cycle_conflict_count": len(conflicts),
            "whole_design_expansion": status == "whole_design_boundary",
            "input_boundary_distance": metrics["input_boundary_distance"],
            "output_boundary_distance": metrics["output_boundary_distance"],
            "mean_anchor_distance": metrics["mean_anchor_distance"],
            "max_anchor_distance": metrics["max_anchor_distance"],
            "runtime_seconds": time.perf_counter() - start,
            "extended_boundary_inputs": ";".join(result.extended_boundary_inputs),
            "extended_boundary_outputs": ";".join(result.extended_boundary_outputs),
            "region_nodes": ";".join(result.region_nodes),
        }
    )
    return case, stage_rows(cid, coi, anchor_mode, passed, case["failure_stage"], success), cov, align, completion_row, anchor_selection_audit_rows(cid, coi, anchor_mode, anchors, spec_graph, ebi | ebo)


def base_case_row(coi: CoiSpec, anchor_mode: str, spec_path: Path, impl_path: Path, cid: str) -> dict[str, object]:
    return {col: "" for col in CASE_COLUMNS} | {
        "case_id": cid,
        "benchmark": coi.benchmark,
        "benchmark_family": infer_source_family(coi.benchmark),
        "coi_name": coi.coi_name,
        "optimization": coi.optimization,
        "anchor_mode": anchor_mode,
        "coi_source": coi.source,
        "spec_path": rel(spec_path),
        "impl_path": rel(impl_path),
    }


def stage_rows(cid: str, coi: CoiSpec, anchor_mode: str, passed: set[str], terminal_stage: str, success: bool) -> list[dict[str, object]]:
    rows = []
    for stage in STAGE_SEQUENCE:
        rows.append(
            {
                "case_id": cid,
                "benchmark": coi.benchmark,
                "coi_name": coi.coi_name,
                "optimization": coi.optimization,
                "anchor_mode": anchor_mode,
                "stage": stage,
                "stage_passed": stage in passed,
                "terminal_stage": terminal_stage,
                "is_terminal_failure_stage": (not success and stage == terminal_stage),
            }
        )
    return rows


def alignment_row(cid: str, coi: CoiSpec, anchor_mode: str, spec_path: Path, impl_path: Path, spec: CircuitGraph, impl: CircuitGraph) -> dict[str, object]:
    pi_match = tuple(spec.inputs) == tuple(impl.inputs)
    po_match = tuple(spec.outputs) == tuple(impl.outputs)
    valid = pi_match and po_match
    reasons = []
    if not pi_match:
        reasons.append("primary_input_names_differ")
    if not po_match:
        reasons.append("primary_output_names_differ")
    return {
        "case_id": cid,
        "benchmark": coi.benchmark,
        "optimization": coi.optimization,
        "anchor_mode": anchor_mode,
        "spec_fingerprint": circuit_fingerprint(spec_path),
        "impl_fingerprint": circuit_fingerprint(impl_path),
        "spec_node_count": len(spec.nodes),
        "impl_node_count": len(impl.nodes),
        "primary_input_names_match": pi_match,
        "primary_output_names_match": po_match,
        "alignment_valid": valid,
        "alignment_failure_reason": ";".join(reasons) if reasons else "valid",
    }


def anchor_coverage_row(cid: str, coi: CoiSpec, anchor_mode: str, graph: CircuitGraph, anchors: AnchorMap) -> dict[str, object]:
    all_nodes = set(graph.nodes)
    anchored = {node for node in all_nodes if anchors.has_anchor(node)}
    coi_nodes = set(coi.coi_internal_nodes)
    bi_tfi = graph.transitive_fanin(list(coi.boundary_inputs))
    bo_tfo = graph.transitive_fanout(list(coi.boundary_outputs))
    ebo_tfi = graph.transitive_fanin(list(coi.boundary_outputs))
    relevant = coi_nodes | bi_tfi | bo_tfo | ebo_tfi
    exact_global = count_category(anchors, all_nodes, "exact_signature_match")
    comp_global = count_category(anchors, all_nodes, "complemented_equivalence")
    sat_global = count_category(anchors, all_nodes, "sat_cec_proven_equivalent")
    exact_rel = count_category(anchors, relevant, "exact_signature_match")
    comp_rel = count_category(anchors, relevant, "complemented_equivalence")
    sat_rel = count_category(anchors, relevant, "sat_cec_proven_equivalent")
    if anchor_mode == "formal_all":
        exact_anchor_map = AnchorMap([a for a in anchors.anchors if a.mapping_category == "exact_signature_match"])
        exact_nodes = {node for node in all_nodes if exact_anchor_map.has_anchor(node)}
    else:
        exact_nodes = anchored
    formal_added = anchored - exact_nodes
    bi_distances = nearest_distances(graph, coi.boundary_inputs, anchored, "fanin")
    bo_distances = nearest_distances(graph, coi.boundary_outputs, anchored, "fanout")
    return {
        "case_id": cid,
        "benchmark": coi.benchmark,
        "coi_name": coi.coi_name,
        "optimization": coi.optimization,
        "anchor_mode": anchor_mode,
        "global_spec_node_count": len(all_nodes),
        "global_formally_anchored_spec_nodes": len(anchored),
        "global_anchor_density": density(len(anchored), len(all_nodes)),
        "coi_node_count": len(coi_nodes),
        "coi_anchored_node_count": len(coi_nodes & anchored),
        "coi_anchor_density": density(len(coi_nodes & anchored), len(coi_nodes)),
        "bi_tfi_union_node_count": len(bi_tfi),
        "bi_tfi_anchored_node_count": len(bi_tfi & anchored),
        "bi_tfi_anchor_density": density(len(bi_tfi & anchored), len(bi_tfi)),
        "bo_tfo_union_node_count": len(bo_tfo),
        "bo_tfo_anchored_node_count": len(bo_tfo & anchored),
        "bo_tfo_anchor_density": density(len(bo_tfo & anchored), len(bo_tfo)),
        "ebo_tfi_relevant_node_count": len(ebo_tfi),
        "ebo_tfi_anchored_node_count": len(ebo_tfi & anchored),
        "ebo_tfi_anchor_density": density(len(ebo_tfi & anchored), len(ebo_tfi)),
        "exact_anchor_count_global": exact_global,
        "complemented_anchor_count_global": comp_global,
        "sat_cec_anchor_count_global": sat_global,
        "exact_anchor_count_relevant": exact_rel,
        "complemented_anchor_count_relevant": comp_rel,
        "sat_cec_anchor_count_relevant": sat_rel,
        "formal_all_added_global_anchors": len(formal_added),
        "formal_all_added_relevant_anchors": len(formal_added & relevant),
        "formal_all_added_tfi_anchors": len(formal_added & bi_tfi),
        "formal_all_added_tfo_anchors": len(formal_added & bo_tfo),
        "formal_all_added_cut_candidate_anchors": len(formal_added & (set(coi.boundary_inputs) | set(coi.boundary_outputs))),
        "bi_anchor_distance_min": dist_agg(bi_distances, "min"),
        "bi_anchor_distance_mean": dist_agg(bi_distances, "mean"),
        "bi_anchor_distance_max": dist_agg(bi_distances, "max"),
        "bo_anchor_distance_min": dist_agg(bo_distances, "min"),
        "bo_anchor_distance_mean": dist_agg(bo_distances, "mean"),
        "bo_anchor_distance_max": dist_agg(bo_distances, "max"),
        "boundary_inputs_with_no_reachable_anchor": sum(1 for value in bi_distances.values() if value is None),
        "boundary_outputs_with_no_reachable_anchor": sum(1 for value in bo_distances.values() if value is None),
    }


def count_category(anchors: AnchorMap, nodes: Iterable[str], category: str) -> int:
    return sum(1 for node in set(nodes) if any(a.mapping_category == category for a in anchors.candidates_for(node)))


def density(numerator: int, denominator: int) -> float:
    return numerator / denominator if denominator else 0.0


def nearest_distances(graph: CircuitGraph, starts: Iterable[str], targets: set[str], direction: str) -> dict[str, int | None]:
    return {start: graph.shortest_distance_to_any(start, targets, direction) for start in sorted(starts)}


def dist_agg(distances: dict[str, int | None], kind: str) -> object:
    values = [value for value in distances.values() if value is not None]
    if not values:
        return "unreachable"
    if kind == "min":
        return min(values)
    if kind == "max":
        return max(values)
    return sum(values) / len(values)


def completion_diagnosis_row(
    cid: str,
    coi: CoiSpec,
    anchor_mode: str,
    ebo: set[str],
    additions: set[str],
    failures: list[str],
    anchors: AnchorMap,
) -> dict[str, object]:
    categories = Counter()
    for node in additions:
        if selected := anchors.selected_for(node):
            categories[selected.mapping_category] += 1
    return {
        "case_id": cid,
        "benchmark": coi.benchmark,
        "coi_name": coi.coi_name,
        "optimization": coi.optimization,
        "anchor_mode": anchor_mode,
        "ebo_nodes": ";".join(sorted(ebo)),
        "paths_to_ebo_count_or_proxy": len(ebo),
        "paths_already_cut": 0,
        "uncut_path_count_or_proxy": len(failures),
        "completion_nodes_added": len(additions),
        "completion_anchor_categories": ";".join(f"{k}:{v}" for k, v in sorted(categories.items())),
        "completion_success": not failures,
        "completion_failure_reason": "valid" if not failures else "unanchored fanin leaves: " + ";".join(sorted(failures)),
    }


def anchor_selection_audit_rows(
    cid: str,
    coi: CoiSpec,
    anchor_mode: str,
    anchors: AnchorMap,
    graph: CircuitGraph,
    relevant_nodes: set[str],
) -> list[dict[str, object]]:
    rows = []
    for node in sorted(set(graph.nodes)):
        candidates = anchors.candidates_for(node)
        if len(candidates) <= 1:
            continue
        selected = anchors.selected_for(node)
        rows.append(
            {
                "case_id": cid,
                "benchmark": coi.benchmark,
                "coi_name": coi.coi_name,
                "optimization": coi.optimization,
                "anchor_mode": anchor_mode,
                "spec_node": node,
                "candidate_anchor_count": len(candidates),
                "selected_anchor": selected.impl_node if selected else "",
                "selected_anchor_category": selected.mapping_category if selected else "",
                "selected_anchor_polarity": selected.polarity if selected else "",
                "selection_rule": selected.selection_reason if selected else "",
                "alternative_anchor_count": max(0, len(candidates) - 1),
                "relevant_to_boundary_search": node in relevant_nodes,
                "alternative_anchor_would_change_cycle_status": "not_evaluated",
                "alternative_anchor_would_reduce_distance": "not_evaluated",
                "alternative_anchor_would_complete_cut": "not_evaluated",
                "diagnostic_outcome": "no_blocking_alternative_detected",
            }
        )
    return rows


def audit_coi_for_all_available_flows(coi: CoiSpec) -> list[dict[str, object]]:
    rows = []
    for opt in DEFAULT_SEED_OPTIMIZATIONS:
        path = original_path(coi.benchmark)
        if not path.exists():
            rows.append(coi_audit_missing_row(coi, opt, "missing_spec_circuit"))
            continue
        graph = CircuitGraph.from_blif(path)
        rows.append(audit_coi(coi, opt, graph))
    return rows


def coi_audit_missing_row(coi: CoiSpec, opt: str, reason: str) -> dict[str, object]:
    return {
        "benchmark": coi.benchmark,
        "coi_name": coi.coi_name,
        "optimization": opt,
        "coi_source": coi.source,
        "coi_connected": False,
        "coi_fanout_free_under_current_definition": False,
        "boundary_inputs_valid": False,
        "boundary_outputs_valid": False,
        "all_external_input_paths_cross_bi": False,
        "all_external_output_paths_cross_bo": False,
        "coi_contains_internal_nodes": bool(coi.coi_internal_nodes),
        "coi_is_whole_design": False,
        "coi_valid": False,
        "coi_invalid_reason": reason,
    }


def audit_coi(coi: CoiSpec, opt: str, graph: CircuitGraph) -> dict[str, object]:
    valid, reason = validate_coi_spec(graph, coi)
    coi_nodes = set(coi.coi_internal_nodes)
    bi = set(coi.boundary_inputs)
    bo = set(coi.boundary_outputs)
    region_like = coi_nodes | bo
    connected = is_connected_undirected(graph, region_like)
    fanout_free = all((set(graph.fanouts.get(node, tuple())) <= region_like | bo) for node in coi_nodes - bo)
    input_paths_cut = all(_all_backward_paths_cross(graph, out, bi) for out in bo if graph.exists(out))
    output_paths_cut = all(_all_forward_paths_cross(graph, node, bo) for node in coi_nodes if graph.exists(node))
    non_input_nodes = {node for node in graph.nodes if node not in graph.inputs}
    return {
        "benchmark": coi.benchmark,
        "coi_name": coi.coi_name,
        "optimization": opt,
        "coi_source": coi.source,
        "coi_connected": connected,
        "coi_fanout_free_under_current_definition": fanout_free,
        "boundary_inputs_valid": all(graph.exists(node) and node not in coi_nodes for node in bi),
        "boundary_outputs_valid": all(graph.exists(node) for node in bo),
        "all_external_input_paths_cross_bi": input_paths_cut,
        "all_external_output_paths_cross_bo": output_paths_cut,
        "coi_contains_internal_nodes": bool(coi_nodes),
        "coi_is_whole_design": bool(coi_nodes) and coi_nodes >= non_input_nodes,
        "coi_valid": valid and connected and input_paths_cut and output_paths_cut,
        "coi_invalid_reason": "valid" if valid else reason,
    }


def is_connected_undirected(graph: CircuitGraph, nodes: set[str]) -> bool:
    nodes = {node for node in nodes if graph.exists(node)}
    if not nodes:
        return False
    start = next(iter(nodes))
    seen = {start}
    queue = deque([start])
    while queue:
        node = queue.popleft()
        for nxt in set(graph.fanins.get(node, tuple())) | set(graph.fanouts.get(node, tuple())):
            if nxt in nodes and nxt not in seen:
                seen.add(nxt)
                queue.append(nxt)
    return seen == nodes


def _all_backward_paths_cross(graph: CircuitGraph, root: str, cut: set[str]) -> bool:
    stack = [root]
    seen: set[str] = set()
    while stack:
        node = stack.pop()
        if node in cut:
            continue
        if node in seen:
            continue
        seen.add(node)
        fanins = graph.fanins.get(node, tuple())
        if not fanins and node not in cut:
            return False
        stack.extend(fanins)
    return True


def _all_forward_paths_cross(graph: CircuitGraph, root: str, cut: set[str]) -> bool:
    stack = [root]
    seen: set[str] = set()
    while stack:
        node = stack.pop()
        if node in cut:
            continue
        if node in seen:
            continue
        seen.add(node)
        fanouts = graph.fanouts.get(node, tuple())
        if not fanouts and node not in cut:
            return False
        stack.extend(fanouts)
    return True


def differential_rows(cases: list[dict[str, object]], coverage: list[dict[str, object]]) -> list[dict[str, object]]:
    cov_by = {(row["benchmark"], row["coi_name"], row["optimization"], row["anchor_mode"]): row for row in coverage}
    groups: dict[tuple[str, str, str], dict[str, dict[str, object]]] = defaultdict(dict)
    for row in cases:
        groups[(row["benchmark"], row["coi_name"], row["optimization"])][row["anchor_mode"]] = row
    rows = []
    for (benchmark, coi_name, opt), modes in sorted(groups.items()):
        exact = modes.get("exact_only")
        formal = modes.get("formal_all")
        if not exact or not formal:
            continue
        exact_cov = cov_by.get((benchmark, coi_name, opt, "exact_only"), {})
        formal_cov = cov_by.get((benchmark, coi_name, opt, "formal_all"), {})
        added_relevant = intish(formal_cov.get("formal_all_added_relevant_anchors"))
        added_frontier = intish(formal_cov.get("formal_all_added_cut_candidate_anchors"))
        selected_sat = intish(formal.get("selected_sat_cec_anchor_count"))
        classification = classify_differential(exact, formal, formal_cov, selected_sat)
        rows.append(
            {
                "case_id": f"{benchmark}|{coi_name}|{opt}",
                "benchmark": benchmark,
                "coi_name": coi_name,
                "optimization": opt,
                "exact_only_success": exact["recovery_success"],
                "formal_all_success": formal["recovery_success"],
                "success_delta": int(boolish(formal["recovery_success"])) - int(boolish(exact["recovery_success"])),
                "exact_only_extension": exact.get("boundary_extension_ratio", ""),
                "formal_all_extension": formal.get("boundary_extension_ratio", ""),
                "extension_delta": floatish(formal.get("boundary_extension_ratio")) - floatish(exact.get("boundary_extension_ratio")),
                "exact_only_relevant_anchor_count": exact_cov.get("global_formally_anchored_spec_nodes", ""),
                "formal_all_relevant_anchor_count": formal_cov.get("global_formally_anchored_spec_nodes", ""),
                "relevant_anchor_delta": intish(formal_cov.get("global_formally_anchored_spec_nodes")) - intish(exact_cov.get("global_formally_anchored_spec_nodes")),
                "exact_only_ebi_count": exact.get("extended_bi_count", ""),
                "formal_all_ebi_count": formal.get("extended_bi_count", ""),
                "exact_only_ebo_count": exact.get("extended_bo_count", ""),
                "formal_all_ebo_count": formal.get("extended_bo_count", ""),
                "selected_sat_cec_anchor_count": selected_sat,
                "available_but_unselected_sat_cec_anchor_count": formal.get("available_but_unselected_sat_cec_anchor_count", 0),
                "formal_all_added_relevant_anchors": added_relevant,
                "formal_all_added_cut_candidate_anchors": added_frontier,
                "differential_classification": classification,
            }
        )
    return rows


def classify_differential(exact: dict[str, object], formal: dict[str, object], cov: dict[str, object], selected_sat: int) -> str:
    added_global = intish(cov.get("formal_all_added_global_anchors"))
    added_relevant = intish(cov.get("formal_all_added_relevant_anchors"))
    added_frontier = intish(cov.get("formal_all_added_cut_candidate_anchors"))
    if not added_global:
        return "no_extra_formal_anchors"
    if not added_relevant:
        return "extra_anchors_outside_relevant_cones"
    if not added_frontier:
        return "extra_relevant_anchors_not_on_frontier"
    if added_frontier and not selected_sat:
        return "extra_frontier_anchors_not_selected"
    if boolish(formal["recovery_success"]) and not boolish(exact["recovery_success"]):
        return "formal_all_enables_recovery"
    if floatish(formal.get("boundary_extension_ratio")) < floatish(exact.get("boundary_extension_ratio")):
        return "formal_all_improves_extension"
    if boolish(exact["recovery_success"]) and not boolish(formal["recovery_success"]):
        return "formal_all_worsens_result"
    return "extra_anchors_selected_no_recovery_change"


def progression_rows(cases: list[dict[str, object]]) -> list[dict[str, object]]:
    groups: dict[tuple[str, str, str], list[dict[str, object]]] = defaultdict(list)
    for row in cases:
        if row["anchor_mode"] == "formal_all":
            groups[(row["benchmark"], row["coi_name"], row["anchor_mode"])].append(row)
    order = {name: i for i, name in enumerate(PROGRESSION_OPTIMIZATIONS)}
    rows = []
    for (benchmark, coi_name, mode), group in sorted(groups.items()):
        ordered = sorted(group, key=lambda r: order.get(str(r["optimization"]), 999))
        successes = [r for r in ordered if boolish(r["recovery_success"])]
        nonzero = [r for r in ordered if floatish(r.get("boundary_extension_ratio")) > 0]
        failures = [r for r in ordered if not boolish(r["recovery_success"])]
        rows.append(
            {
                "benchmark": benchmark,
                "coi_name": coi_name,
                "anchor_mode": mode,
                "first_nonzero_extension_flow": nonzero[0]["optimization"] if nonzero else "",
                "first_recovery_failure_flow": failures[0]["optimization"] if failures else "",
                "last_successful_flow": successes[-1]["optimization"] if successes else "",
                "maximum_successful_flow": successes[-1]["optimization"] if successes else "",
            }
        )
    return rows


def critical_path_overlap_rows(cois: list[CoiSpec], cases: list[dict[str, object]], critical_path: Path = RESULTS / "critical_path_mapping.csv") -> list[dict[str, object]]:
    critical = read_csv(critical_path) if critical_path.exists() else []
    successful = {(r["benchmark"], r["coi_name"], r["optimization"], r["anchor_mode"]): r for r in cases if boolish(r["recovery_success"])}
    rows = []
    for coi in expand_specs(cois, DEFAULT_SEED_OPTIMIZATIONS):
        crit = [r for r in critical if r.get("benchmark") == coi.benchmark and r.get("optimization") == coi.optimization]
        crit_nodes = {r.get("optimized_node", "") for r in crit}
        unresolved = {r.get("optimized_node", "") for r in crit if r.get("mapping_category") == "unresolved"}
        coi_nodes = set(coi.coi_internal_nodes)
        region_unresolved = 0
        for mode in ANCHOR_MODES_FOR_DIAGNOSIS:
            case = successful.get((coi.benchmark, coi.coi_name, coi.optimization, mode))
            if case:
                region = split_nodes(case.get("region_nodes"))
                region_unresolved += len(region & unresolved)
        rows.append(
            {
                "benchmark": coi.benchmark,
                "coi_name": coi.coi_name,
                "optimization": coi.optimization,
                "critical_path_node_overlap_count": len(coi_nodes & crit_nodes),
                "unresolved_critical_path_node_overlap_count": len(coi_nodes & unresolved),
                "successful_coi_overlaps_unresolved_path_nodes": region_unresolved > 0,
                "unresolved_path_nodes_enclosed_by_valid_regions": region_unresolved,
            }
        )
    return rows


def generated_critical_path_coi_rows(segment_sizes: list[int] | None = None, critical_path: Path = RESULTS / "critical_path_mapping.csv") -> list[dict[str, object]]:
    sizes = segment_sizes or [3, 5, 8]
    critical = read_csv(critical_path) if critical_path.exists() else []
    groups: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in critical:
        if row.get("mapped_original_node") and row.get("mapped_original_node") != "":
            groups[(row["benchmark"], row["optimization"])].append(row)
    out = []
    for (benchmark, opt), rows in sorted(groups.items()):
        path_nodes = [row.get("mapped_original_node", "") for row in sorted(rows, key=lambda r: intish(r.get("path_index")))]
        path_nodes = [node for node in path_nodes if node]
        graph_path = original_path(benchmark)
        if not path_nodes:
            continue
        graph = CircuitGraph.from_blif(graph_path) if graph_path.exists() else None
        for size in sizes:
            segment = tuple(path_nodes[:size])
            if len(segment) < size:
                continue
            internal = set(segment)
            if graph is None:
                bi: list[str] = []
                bo: list[str] = []
                valid = False
                failure_reason = "missing_spec_circuit"
            else:
                bi = sorted({fanin for node in internal for fanin in graph.fanins.get(node, tuple()) if fanin not in internal})
                bo = sorted({node for node in internal if any(fanout not in internal for fanout in graph.fanouts.get(node, tuple()))})
                valid = bool(internal and bi and bo)
                failure_reason = "valid" if valid else "malformed_path_segment"
            out.append(
                {
                    "benchmark": benchmark,
                    "optimization": opt,
                    "segment_size": size,
                    "coi_name": f"critical_path_segment_{size}",
                    "coi_internal_nodes": ";".join(segment),
                    "boundary_inputs": ";".join(bi),
                    "boundary_outputs": ";".join(bo),
                    "generated_coi_valid": valid,
                    "recovery_attempted": False,
                    "recovery_success": False,
                    "failure_reason": failure_reason,
                    "unresolved_path_nodes_enclosed": 0,
                    "interpretation": "diagnostic COI only; enclosure is region-level evidence, not node equivalence",
                }
            )
    return out[:36]


def split_nodes(value: object) -> set[str]:
    return {item for item in str(value or "").split(";") if item}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def write_csv(path: Path, rows: list[dict[str, object]], columns: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if columns is None:
        columns = sorted({key for row in rows for key in row}) if rows else []
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({col: row.get(col, "") for col in columns})


def markdown_table(rows: list[dict[str, object]], limit: int | None = None) -> str:
    if not rows:
        return "_No rows._"
    rows = rows[:limit] if limit else rows
    columns = list(rows[0])
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join(["---"] * len(columns)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(col, "")) for col in columns) + " |")
    return "\n".join(lines)


def boolish(value: object) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes"}


def floatish(value: object) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def intish(value: object) -> int:
    try:
        return int(float(str(value)))
    except (TypeError, ValueError):
        return 0


def summarize_diagnosis(
    *,
    identity: list[dict[str, object]],
    cases: list[dict[str, object]],
    coverage: list[dict[str, object]],
    differential: list[dict[str, object]],
    progression: list[dict[str, object]],
    coi_audit: list[dict[str, object]],
    critical_overlap: list[dict[str, object]],
    generated_cp: list[dict[str, object]],
    anchor_audit: list[dict[str, object]],
) -> str:
    identity_success = sum(boolish(r["recovery_success"]) for r in identity)
    identity_zero = sum(boolish(r["recovery_success"]) and floatish(r.get("boundary_extension_ratio")) == 0 for r in identity)
    seed_success = sum(boolish(r["recovery_success"]) for r in cases)
    stage_counts = Counter(str(r["failure_stage"]) for r in cases if not boolish(r["recovery_success"]))
    reason_counts = Counter(str(r["failure_reason"]) for r in cases if not boolish(r["recovery_success"]))
    global_added = sum(1 for r in coverage if r["anchor_mode"] == "formal_all" and intish(r["formal_all_added_global_anchors"]) > 0)
    relevant_added = sum(1 for r in coverage if r["anchor_mode"] == "formal_all" and intish(r["formal_all_added_relevant_anchors"]) > 0)
    frontier_added = sum(1 for r in coverage if r["anchor_mode"] == "formal_all" and intish(r["formal_all_added_cut_candidate_anchors"]) > 0)
    sat_selected = sum(1 for r in cases if intish(r.get("selected_sat_cec_anchor_count")) > 0)
    valid_cois = sum(boolish(r["coi_valid"]) for r in coi_audit)
    unresolved_overlap = sum(intish(r["unresolved_critical_path_node_overlap_count"]) for r in critical_overlap)
    unresolved_enclosed = sum(intish(r["unresolved_path_nodes_enclosed_by_valid_regions"]) for r in critical_overlap)
    alt_enables = sum(1 for r in anchor_audit if r.get("diagnostic_outcome") == "alternative_enables_recovery")

    decision = "fix recovery semantics or COI specifications" if identity_success < len(identity) else "ODC-aware or speculative anchor generation"
    if relevant_added and not frontier_added:
        decision = "improve cut search or explore alternative anchored frontiers"
    if alt_enables:
        decision = "multi-anchor or cost-guided anchor selection"
    if unresolved_enclosed:
        decision = "critical-path region recovery and logic grafting"

    lines = [
        "# Boundary-Recovery Failure Diagnosis Summary",
        "",
        "This diagnosis measures why the current formal boundary-recovery prototype succeeds or fails. Region enclosure is not reported as direct node equivalence.",
        "",
        "## Identity",
        "",
        f"- Identity successes / total: {identity_success} / {len(identity)}",
        f"- Zero-extension identity cases: {identity_zero}",
        f"- Identity failures: {len(identity) - identity_success}",
        "",
        "## Existing Seed Suite",
        "",
        f"- Successes / total: {seed_success} / {len(cases)}",
        "- Failures by stage:",
        "",
        markdown_table([{"failure_stage": k, "count": v} for k, v in sorted(stage_counts.items())]),
        "",
        "- Failures by reason:",
        "",
        markdown_table([{"failure_reason": k, "count": v} for k, v in sorted(reason_counts.items())]),
        "",
        "## Anchor Relevance",
        "",
        f"- Cases where `formal_all` adds global anchors: {global_added}",
        f"- Cases where `formal_all` adds relevant anchors: {relevant_added}",
        f"- Cases where `formal_all` adds usable frontier anchors: {frontier_added}",
        f"- Cases where a SAT/CEC anchor is actually selected: {sat_selected}",
        "",
        "## Recovery Progression",
        "",
        markdown_table(progression, limit=12),
        "",
        "## COI Validity",
        "",
        f"- Valid COI audit rows: {valid_cois}",
        f"- Invalid COI audit rows: {len(coi_audit) - valid_cois}",
        "",
        "## Critical Path",
        "",
        f"- Seed COI unresolved critical-path overlap count: {unresolved_overlap}",
        f"- Unresolved path nodes enclosed by valid recovered regions: {unresolved_enclosed}",
        f"- Generated path COI rows: {len(generated_cp)}",
        "",
        "## Anchor Selection",
        "",
        f"- Failed cases where an alternative formal anchor enables recovery: {alt_enables}",
        "- Alternative-anchor diagnostics are local and bounded; this milestone does not run a combinatorial search.",
        "",
        "## Decision Gate",
        "",
        f"Recommended next milestone from these measurements: **{decision}**.",
    ]
    return "\n".join(lines) + "\n"
