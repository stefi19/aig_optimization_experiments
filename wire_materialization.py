"""Additive original-side BLIF wire materialization."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path

from analyze_blif_matches import BlifNetwork, BlifNode
from contextual_error_metrics import write_blif
from cut_function_extraction import CutFunction
from materialized_expression import MaterializedExpression


@dataclass(frozen=True)
class MaterializedWire:
    materialized_wire_name: str
    source_spec_nodes: tuple[str, ...]
    target_impl_node: str
    cut_id: str
    expression_id: str
    added_logic_node_count: int
    added_gate_count: int
    augmented_spec_path: str
    provenance_manifest: str
    generation_status: str
    failure_reason: str


def materialize_wire(
    spec_net: BlifNetwork,
    fn: CutFunction,
    expr: MaterializedExpression,
    *,
    spec_leaf_nodes: tuple[str, ...],
    leaf_polarities: tuple[str, ...],
    case_id: str,
    output_dir: Path,
) -> tuple[BlifNetwork | None, MaterializedWire]:
    existing = set(spec_net.inputs) | set(spec_net.outputs) | {node.output for node in spec_net.nodes}
    missing = [node for node in spec_leaf_nodes if node not in existing]
    wire_name = deterministic_wire_name(case_id, fn.target_impl_node, fn.truth_table_hash)
    if missing:
        return None, _failed(wire_name, spec_leaf_nodes, fn, expr, "missing_spec_leaf:" + ";".join(missing))
    if wire_name in existing:
        return None, _failed(wire_name, spec_leaf_nodes, fn, expr, "name_collision")
    cover = cover_from_truth_table(fn.truth_table, spec_leaf_nodes, leaf_polarities)
    new_node = BlifNode(output=wire_name, inputs=list(spec_leaf_nodes), cover=cover)
    augmented = BlifNetwork(inputs=list(spec_net.inputs), outputs=list(spec_net.outputs), nodes=[*spec_net.nodes, new_node])
    output_dir.mkdir(parents=True, exist_ok=True)
    augmented_path = output_dir / f"{wire_name}.blif"
    write_blif(augmented, augmented_path, model_name="materialized_spec")
    try:
        reported_path = str(augmented_path.relative_to(Path.cwd()))
    except ValueError:
        reported_path = str(augmented_path)
    manifest = {
        "wire": wire_name,
        "target_impl_node": fn.target_impl_node,
        "cut_id": fn.cut_id,
        "expression_id": expr.expression_id,
        "spec_leaf_nodes": list(spec_leaf_nodes),
        "impl_leaf_order": list(fn.support_leaf_order),
        "leaf_polarities": list(leaf_polarities),
        "truth_table_hash": fn.truth_table_hash,
    }
    return augmented, MaterializedWire(
        materialized_wire_name=wire_name,
        source_spec_nodes=spec_leaf_nodes,
        target_impl_node=fn.target_impl_node,
        cut_id=fn.cut_id,
        expression_id=expr.expression_id,
        added_logic_node_count=1,
        added_gate_count=max(1, len([b for b in fn.truth_table if b])),
        augmented_spec_path=reported_path,
        provenance_manifest=str(manifest),
        generation_status="generated",
        failure_reason="",
    )


def cover_from_truth_table(truth_table: tuple[int, ...], spec_leaf_nodes: tuple[str, ...], leaf_polarities: tuple[str, ...]) -> list[str]:
    cover: list[str] = []
    width = len(spec_leaf_nodes)
    if width == 0:
        return ["1"] if truth_table and truth_table[0] else []
    for spec_assignment in range(1 << width):
        impl_assignment = 0
        for bit, polarity in enumerate(leaf_polarities):
            spec_bit = (spec_assignment >> bit) & 1
            impl_bit = spec_bit if polarity == "same" else 1 - spec_bit
            if impl_bit:
                impl_assignment |= 1 << bit
        if truth_table[impl_assignment]:
            pattern = "".join("1" if (spec_assignment >> bit) & 1 else "0" for bit in range(width))
            cover.append(f"{pattern} 1")
    return cover


def deterministic_wire_name(case_id: str, target: str, truth_hash: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9_]", "_", f"{case_id}_{target}")[:80]
    digest = hashlib.sha256(f"{case_id}|{target}|{truth_hash}".encode("utf-8")).hexdigest()[:10]
    return f"materialized_{safe}_{digest}"


def wire_to_row(wire: MaterializedWire, *, case_id: str, benchmark: str, optimization: str, coi_name: str) -> dict[str, object]:
    return {
        "case_id": case_id,
        "benchmark": benchmark,
        "optimization": optimization,
        "coi_name": coi_name,
        "materialized_wire_name": wire.materialized_wire_name,
        "source_spec_nodes": ";".join(wire.source_spec_nodes),
        "target_impl_node": wire.target_impl_node,
        "cut_id": wire.cut_id,
        "expression_id": wire.expression_id,
        "added_logic_node_count": wire.added_logic_node_count,
        "added_gate_count": wire.added_gate_count,
        "augmented_spec_path": wire.augmented_spec_path,
        "provenance_manifest": wire.provenance_manifest,
        "generation_status": wire.generation_status,
        "failure_reason": wire.failure_reason,
    }


def _failed(wire_name: str, spec_leaf_nodes: tuple[str, ...], fn: CutFunction, expr: MaterializedExpression, reason: str) -> MaterializedWire:
    return MaterializedWire(
        materialized_wire_name=wire_name,
        source_spec_nodes=spec_leaf_nodes,
        target_impl_node=fn.target_impl_node,
        cut_id=fn.cut_id,
        expression_id=expr.expression_id,
        added_logic_node_count=0,
        added_gate_count=0,
        augmented_spec_path="",
        provenance_manifest="",
        generation_status="failed",
        failure_reason=reason,
    )
