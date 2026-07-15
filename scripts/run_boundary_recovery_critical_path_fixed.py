#!/usr/bin/env python3
"""Generate canonical critical-path COI validation rows under repaired semantics."""

from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from boundary_graph import CircuitGraph  # noqa: E402
from boundary_semantics import SEMANTICS_DIR, identity_anchor_map, original_path, recover_semantic_boundary, write_csv  # noqa: E402
from coi_model import normalize_coi, validate_coi  # noqa: E402

CRITICAL = ROOT / "results" / "critical_path_mapping.csv"
VALIDATION = SEMANTICS_DIR / "critical_path_coi_validation.csv"
IDENTITY = SEMANTICS_DIR / "critical_path_identity_results.csv"


def main() -> int:
    rows = read_csv(CRITICAL) if CRITICAL.exists() else []
    groups: dict[tuple[str, str], list[dict[str, str]]] = {}
    for row in rows:
        groups.setdefault((row.get("benchmark", ""), row.get("optimization", "")), []).append(row)
    validation_rows = []
    identity_rows = []
    for (benchmark, opt), group in sorted(groups.items()):
        path = original_path(benchmark)
        if not path.exists():
            for size in [3, 5, 8]:
                validation_rows.append(skip_row(benchmark, opt, size, "missing_spec_circuit"))
            continue
        graph = CircuitGraph.from_blif(path)
        ordered = [r.get("mapped_original_node", "") for r in sorted(group, key=lambda r: int(float(r.get("path_index", 0) or 0)))]
        ordered = [node for node in ordered if node and graph.exists(node)]
        for size in [3, 5, 8]:
            segment = ordered[:size]
            if len(segment) < size:
                validation_rows.append(skip_row(benchmark, opt, size, "path_segment_too_short"))
                continue
            coi = normalize_coi(
                graph,
                benchmark=benchmark,
                optimization=opt,
                coi_name=f"critical_path_segment_{size}",
                region_nodes=segment,
                source="critical_path_generated",
                generation_method="critical_path_segment",
            )
            validation = validate_coi(graph, coi)
            validation_rows.append(
                {
                    "benchmark": benchmark,
                    "optimization": opt,
                    "segment_size": size,
                    "segment_start": segment[0],
                    "segment_end": segment[-1],
                    "closure_nodes_added": 0,
                    "coi_valid": validation.valid,
                    "invalid_reason": "valid" if validation.valid else ";".join(validation.errors),
                    "boundary_inputs": ";".join(coi.boundary_inputs),
                    "boundary_outputs": ";".join(coi.boundary_outputs),
                }
            )
            if validation.valid:
                result = recover_semantic_boundary(graph, coi, identity_anchor_map(graph))
                identity_rows.append(
                    {
                        "benchmark": benchmark,
                        "optimization": opt,
                        "segment_size": size,
                        "identity_success": result.success,
                        "unresolved_path_nodes_enclosed": 0,
                        "failure_reason": result.failure_reason,
                    }
                )
    write_csv(VALIDATION, validation_rows)
    write_csv(IDENTITY, identity_rows)
    print(f"Wrote critical-path semantic COI validation rows: {len(validation_rows)}")
    return 0


def skip_row(benchmark: str, opt: str, size: int, reason: str) -> dict[str, object]:
    return {
        "benchmark": benchmark,
        "optimization": opt,
        "segment_size": size,
        "segment_start": "",
        "segment_end": "",
        "closure_nodes_added": 0,
        "coi_valid": False,
        "invalid_reason": reason,
        "boundary_inputs": "",
        "boundary_outputs": "",
    }


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


if __name__ == "__main__":
    raise SystemExit(main())
