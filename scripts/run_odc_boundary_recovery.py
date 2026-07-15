#!/usr/bin/env python3
"""Rerun extended-boundary recovery with formal ODC anchors."""

from __future__ import annotations

import argparse
import csv
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from boundary_anchor_map import load_anchor_map  # noqa: E402
from boundary_graph import CircuitGraph  # noqa: E402
from boundary_semantics import load_canonical_manifest, original_path, variant_path, write_csv  # noqa: E402
from extended_boundary_search import SearchConfig, result_to_row, search_valid_extended_boundary, first_frontier_extended_boundary  # noqa: E402
from odc_formal_validation import prove_boundary_contextual_interchangeability  # noqa: E402

OUT = ROOT / "results" / "odc_anchor_generation"
EXTENDED = ROOT / "results" / "extended_boundary_search" / "extended_boundary_cases.csv"


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--context-mode", default="all", choices=["all", "global_output_odc", "coi_output_odc"])
    p.add_argument("--search-mode", default="all", choices=["all", "first_frontier", "cost_guided"])
    p.add_argument("--anchor-mode", default="all", choices=["all", "formal_all", "formal_plus_odc"])
    p.add_argument("--formal-timeout", type=int, default=30)
    p.add_argument("--abc", default=None)
    p.add_argument("--output-dir", type=Path, default=OUT)
    return p.parse_args()


def main() -> int:
    args = parse_args()
    contexts = ["global_output_odc", "coi_output_odc"] if args.context_mode == "all" else [args.context_mode]
    search_modes = ["first_frontier", "cost_guided"] if args.search_mode == "all" else [args.search_mode]
    anchor_modes = ["formal_all", "formal_plus_odc"] if args.anchor_mode == "all" else [args.anchor_mode]
    abc = args.abc or shutil.which("abc") or str(ROOT / ".abc_build" / "abc_repo" / "abc")
    if not Path(abc).exists():
        abc = None
    cois = {(c.benchmark, c.coi_name): c for c in load_canonical_manifest()}
    failures = []
    with EXTENDED.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            if row["search_mode"] == "cost_guided" and row["anchor_mode"] == "formal_all" and row["success"] != "True":
                failures.append(row)
    rows = []
    for old in failures:
        coi = cois[(old["benchmark"], old["coi_name"])]
        spec_path = original_path(coi.benchmark)
        impl_path = variant_path(coi.benchmark, old["optimization"])
        if not spec_path.exists() or not impl_path.exists():
            continue
        spec = CircuitGraph.from_blif(spec_path)
        impl = CircuitGraph.from_blif(impl_path)
        observable = tuple(spec.outputs if "global_output_odc" else coi.boundary_outputs)
        for context_mode in contexts:
            observable = tuple(spec.outputs if context_mode == "global_output_odc" else coi.boundary_outputs)
            for anchor_mode in anchor_modes:
                anchors = load_anchor_map(
                    coi.benchmark,
                    old["optimization"],
                    anchor_mode,
                    results_dir=ROOT / "results",
                    spec_inputs=spec.inputs,
                    impl_inputs=impl.inputs,
                    spec_outputs=spec.outputs,
                    impl_outputs=impl.outputs,
                    coi_name=coi.coi_name,
                    context_mode=context_mode,
                    observable_outputs=observable,
                )
                for search_mode in search_modes:
                    result = first_frontier_extended_boundary(spec, impl, coi, anchors) if search_mode == "first_frontier" else search_valid_extended_boundary(spec, impl, coi, anchors, SearchConfig())
                    selected_odc = sum(1 for node in [*result.ebi, *result.ebo] if (anchor := anchors.selected_for(node)) and anchor.mapping_category == "formal_odc_valid_anchor")
                    boundary_status = "not_applicable"
                    boundary_proof = None
                    if selected_odc and result.success:
                        replacements = tuple(
                            (anchor.spec_node, anchor.impl_node, "inverted" if anchor.polarity == "inverted" else "positive")
                            for node in [*result.ebi, *result.ebo]
                            if (anchor := anchors.selected_for(node)) and anchor.mapping_category == "formal_odc_valid_anchor"
                        )
                        boundary_proof = prove_boundary_contextual_interchangeability(spec_path, impl_path, replacements, context_mode, observable, args.formal_timeout, abc)
                        boundary_status = "boundary_contextually_valid" if boundary_proof.status == "proven_odc_valid" else "boundary_contextual_validation_failed"
                    elif selected_odc:
                        boundary_status = "boundary_still_invalid"
                    final_success = result.success and (not selected_odc or boundary_status == "boundary_contextually_valid")
                    row = result_to_row(
                        result,
                        case_id=f"{old['benchmark']}|{old['coi_name']}|{old['optimization']}|{anchor_mode}|{search_mode}|{context_mode}",
                        benchmark=old["benchmark"],
                        optimization=old["optimization"],
                        coi_name=old["coi_name"],
                        anchor_mode=anchor_mode,
                        original_coi_nodes=coi.region_nodes,
                        old_status=old["old_status"],
                        old_failure_reason=old["old_failure_reason"],
                    )
                    row.update(
                        {
                            "context_mode": context_mode,
                            "global_formal_anchor_count": len([a for a in anchors.anchors if a.equivalence_scope == "global"]),
                            "proven_odc_anchor_count": len([a for a in anchors.anchors if a.mapping_category == "formal_odc_valid_anchor"]),
                            "usable_odc_frontier_count": selected_odc,
                            "selected_odc_anchor_count": selected_odc,
                            "boundary_contextual_validation_status": boundary_status,
                            "boundary_contextual_proof_status": boundary_proof.status if boundary_proof else "",
                            "formal_checks": "",
                            "formal_timeouts": "",
                        }
                    )
                    if not final_success:
                        row["success"] = False
                        if selected_odc and result.success and boundary_status != "boundary_contextually_valid":
                            row["failure_reason"] = "boundary_contextual_validation_failed"
                            row["classification"] = "boundary_contextual_validation_failed"
                        elif selected_odc:
                            row["failure_reason"] = "boundary_still_invalid"
                            row["classification"] = "boundary_still_invalid"
                    rows.append(row)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(args.output_dir / "odc_boundary_recovery_cases.csv", rows)
    write_csv(args.output_dir / "odc_boundary_validation.csv", rows)
    print(f"Wrote ODC boundary recovery rows: {len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
