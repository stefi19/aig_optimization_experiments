#!/usr/bin/env python3
"""Generate additive original-side materialized wires for extracted cuts."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from analyze_blif_matches import parse_blif  # noqa: E402
from boundary_semantics import original_path, write_csv  # noqa: E402
from cut_function_extraction import CutFunction  # noqa: E402
from materialized_expression import expression_from_truth_table, expression_to_row  # noqa: E402
from wire_materialization import materialize_wire, wire_to_row  # noqa: E402

OUT = ROOT / "results" / "materialized_correspondence"
EXAMPLES = OUT / "examples"

EXPR_COLUMNS = [
    "case_id",
    "benchmark",
    "optimization",
    "coi_name",
    "expression_id",
    "cut_id",
    "target_impl_node",
    "expression_ast",
    "expression_text",
    "truth_table_hash",
    "operator_count",
    "logic_node_count",
    "expression_depth",
    "estimated_cost",
    "minimization_backend",
    "canonical_hash",
]

WIRE_COLUMNS = [
    "case_id",
    "benchmark",
    "optimization",
    "coi_name",
    "materialized_wire_name",
    "source_spec_nodes",
    "target_impl_node",
    "cut_id",
    "expression_id",
    "added_logic_node_count",
    "added_gate_count",
    "augmented_spec_path",
    "provenance_manifest",
    "generation_status",
    "failure_reason",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-materialized-expression-nodes", type=int, default=32)
    parser.add_argument("--output-dir", type=Path, default=OUT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    cut_rows = {row["cut_id"]: row for row in _read_rows(args.output_dir / "anchored_cut_candidates.csv")}
    fn_rows = _read_rows(args.output_dir / "cut_function_extraction.csv")
    spec_nets = {}
    expr_rows = []
    wire_rows = []
    for row in fn_rows:
        if row["extraction_status"] != "extracted":
            continue
        truth = tuple(int(ch) for ch in row["truth_table"])
        fn = CutFunction(
            cut_id=row["cut_id"],
            target_impl_node=row["target_impl_node"],
            truth_table=truth,
            truth_table_hash=row["truth_table_hash"],
            support_leaf_order=tuple(filter(None, row["support_leaf_order"].split(";"))),
            local_cone_nodes=tuple(filter(None, row["local_cone_nodes"].split(";"))),
            local_cone_size=int(row["local_cone_size"] or 0),
            extraction_backend=row["extraction_backend"],
            extraction_status=row["extraction_status"],
            failure_reason=row["failure_reason"],
            runtime_seconds=float(row["runtime_seconds"] or 0),
        )
        expr = expression_from_truth_table(fn)
        if expr.logic_node_count > args.max_materialized_expression_nodes:
            continue
        cut = cut_rows[row["cut_id"]]
        key = row["benchmark"]
        if key not in spec_nets:
            spec_nets[key] = parse_blif(original_path(key))
        _, wire = materialize_wire(
            spec_nets[key],
            fn,
            expr,
            spec_leaf_nodes=tuple(filter(None, cut["spec_leaf_nodes"].split(";"))),
            leaf_polarities=tuple(filter(None, cut["leaf_polarities"].split(";"))),
            case_id=row["case_id"],
            output_dir=args.output_dir / "examples",
        )
        expr_rows.append(expression_to_row(expr, case_id=row["case_id"], benchmark=row["benchmark"], optimization=row["optimization"], coi_name=row["coi_name"]))
        wire_rows.append(wire_to_row(wire, case_id=row["case_id"], benchmark=row["benchmark"], optimization=row["optimization"], coi_name=row["coi_name"]))
    write_csv(args.output_dir / "materialized_expression_candidates.csv", expr_rows, EXPR_COLUMNS)
    write_csv(args.output_dir / "materialized_wires.csv", wire_rows, WIRE_COLUMNS)
    print(f"Wrote materialized wire rows: {len(wire_rows)}")
    return 0


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


if __name__ == "__main__":
    raise SystemExit(main())
