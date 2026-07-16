"""Canonical semantic-region data model.

This module intentionally reuses the COI convention established by
``coi_model.py``: ``R`` is the internal region, ``BI`` is outside ``R`` with
fanout into ``R``, and ``BO`` is a subset of ``R``.
"""

from __future__ import annotations

import csv
import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path

from analyze_blif_matches import parse_blif
from boundary_graph import CircuitGraph


SEMANTIC_REGION_SCHEMA_VERSION = "semantic_region_schema_v1"
SUPPORTED_REGION_SOURCES = (
    "ground_truth_region",
    "whole_output_cone",
    "global_formal_recovered_region",
    "formal_odc_recovered_region",
    "critical_path_region",
    "sliding_structural_cone",
)
ACTIVE_REGION_SOURCES = ("ground_truth_region", "whole_output_cone")
TOP_LEVEL_STATUSES = (
    "eligible",
    "infrastructure_skip",
    "invalid_region",
    "unsupported_case",
    "alignment_failure",
)


@dataclass(frozen=True)
class CircuitFingerprint:
    file_hash: str
    pi_interface_fingerprint: str
    po_interface_fingerprint: str
    node_count: int
    gate_count: int
    benchmark_id: str
    optimization_id: str


@dataclass(frozen=True)
class SemanticRegion:
    region_id: str
    case_id: str
    benchmark: str
    family: str
    operator: str
    optimization: str
    source_type: str
    spec_circuit_path: str
    impl_circuit_path: str
    region_nodes: tuple[str, ...]
    boundary_inputs: tuple[str, ...]
    boundary_outputs: tuple[str, ...]
    observable_outputs: tuple[str, ...]
    ground_truth_expression: str
    ground_truth_input_buses: tuple[dict[str, object], ...]
    ground_truth_output_buses: tuple[dict[str, object], ...]
    ground_truth_signedness: str
    ground_truth_width_semantics: str
    formal_scope: str
    context_mode: str
    source_manifest: str
    spec_fingerprint: str
    impl_fingerprint: str
    declared: bool
    circuit_available: bool
    region_available: bool
    structurally_valid: bool
    interface_extractable: bool
    eligible: bool
    attempted: bool
    status: str
    skip_reason: str
    schema_version: str = SEMANTIC_REGION_SCHEMA_VERSION

    def to_dict(self) -> dict[str, object]:
        data = asdict(self)
        for key in (
            "region_nodes",
            "boundary_inputs",
            "boundary_outputs",
            "observable_outputs",
            "ground_truth_input_buses",
            "ground_truth_output_buses",
        ):
            data[key] = list(data[key])
        return data

    def to_csv_row(self) -> dict[str, str]:
        data = self.to_dict()
        row: dict[str, str] = {}
        for field in SEMANTIC_REGION_FIELDS:
            value = data[field]
            if isinstance(value, (list, dict)):
                row[field] = json.dumps(value, sort_keys=True, separators=(",", ":"))
            elif isinstance(value, bool):
                row[field] = str(value).lower()
            else:
                row[field] = str(value)
        return row


SEMANTIC_REGION_FIELDS = [
    "region_id",
    "case_id",
    "benchmark",
    "family",
    "operator",
    "optimization",
    "source_type",
    "spec_circuit_path",
    "impl_circuit_path",
    "region_nodes",
    "boundary_inputs",
    "boundary_outputs",
    "observable_outputs",
    "ground_truth_expression",
    "ground_truth_input_buses",
    "ground_truth_output_buses",
    "ground_truth_signedness",
    "ground_truth_width_semantics",
    "formal_scope",
    "context_mode",
    "source_manifest",
    "spec_fingerprint",
    "impl_fingerprint",
    "declared",
    "circuit_available",
    "region_available",
    "structurally_valid",
    "interface_extractable",
    "eligible",
    "attempted",
    "status",
    "skip_reason",
    "schema_version",
]


def json_compact(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def relpath(path: Path, root: Path) -> str:
    return str(path.resolve().relative_to(root.resolve()))


def file_hash(path: Path) -> str:
    """Hash circuit content while ignoring volatile ABC timestamp comments."""

    digest = hashlib.sha256()
    normalized_lines = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith('# Benchmark "') and " written by ABC on " in line:
            continue
        normalized_lines.append(line)
    digest.update(("\n".join(normalized_lines) + "\n").encode("utf-8"))
    return digest.hexdigest()[:16]


def interface_fingerprint(names: list[str] | tuple[str, ...]) -> str:
    digest = hashlib.sha256()
    digest.update("\0".join(names).encode("utf-8"))
    return digest.hexdigest()[:16]


def circuit_fingerprint(path: Path, *, benchmark_id: str, optimization_id: str) -> CircuitFingerprint:
    net = parse_blif(path)
    return CircuitFingerprint(
        file_hash=file_hash(path),
        pi_interface_fingerprint=interface_fingerprint(net.inputs),
        po_interface_fingerprint=interface_fingerprint(net.outputs),
        node_count=len(set(net.inputs) | set(net.outputs) | {node.output for node in net.nodes}),
        gate_count=len(net.nodes),
        benchmark_id=benchmark_id,
        optimization_id=optimization_id,
    )


def non_input_logic_nodes(graph: CircuitGraph) -> set[str]:
    return {node for node in graph.nodes if node not in set(graph.inputs)}


def output_cone_region(graph: CircuitGraph, outputs: list[str] | tuple[str, ...]) -> tuple[str, ...]:
    cone = graph.transitive_fanin(list(outputs))
    return tuple(sorted(node for node in cone if node not in set(graph.inputs)))


def write_csv(rows: list[dict[str, str]], path: Path, fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_json(rows: list[dict[str, object]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(rows, indent=2, sort_keys=True) + "\n", encoding="utf-8")
