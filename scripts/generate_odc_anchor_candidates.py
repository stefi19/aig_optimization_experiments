#!/usr/bin/env python3
"""Generate bounded ODC-anchor candidates near failed boundary frontiers."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from boundary_graph import CircuitGraph  # noqa: E402
from boundary_semantics import load_canonical_manifest, load_formal_anchors, original_path, variant_path, write_csv  # noqa: E402
from odc_anchor_generation import generate_odc_anchor_candidates  # noqa: E402

OUT = ROOT / "results" / "odc_anchor_generation"
EXTENDED = ROOT / "results" / "extended_boundary_search" / "extended_boundary_cases.csv"
COLUMNS = [
    "case_id", "benchmark", "optimization", "coi_name", "context_mode", "ranking_mode", "boundary_side",
    "frontier_root", "spec_node", "impl_node", "requested_polarity", "candidate_rank", "spec_distance",
    "impl_distance", "support_overlap", "support_size_difference", "fanin_degree_difference",
    "fanout_degree_difference", "structural_score", "signature_similarity", "sampled_mismatch_rate",
    "sampled_output_error_rate", "simulation_filter_status",
]


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--context-mode", default="all", choices=["all", "global_output_odc", "coi_output_odc"])
    p.add_argument("--ranking-mode", default="combined", choices=["structural_only", "simulation_only", "functional_features", "combined"])
    p.add_argument("--max-frontier-distance", type=int, default=3)
    p.add_argument("--max-spec-candidates", type=int, default=8)
    p.add_argument("--max-impl-candidates", type=int, default=8)
    p.add_argument("--output-dir", type=Path, default=OUT)
    return p.parse_args()


def main() -> int:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    cois = {(c.benchmark, c.coi_name): c for c in load_canonical_manifest()}
    failed = []
    with EXTENDED.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            if row["search_mode"] == "cost_guided" and row["anchor_mode"] == "formal_all" and row["success"] != "True":
                failed.append(row)
    contexts = ["global_output_odc", "coi_output_odc"] if args.context_mode == "all" else [args.context_mode]
    rows = []
    for row in failed:
        coi = cois[(row["benchmark"], row["coi_name"])]
        spec_path = original_path(coi.benchmark)
        impl_path = variant_path(coi.benchmark, row["optimization"])
        if not spec_path.exists() or not impl_path.exists():
            continue
        spec = CircuitGraph.from_blif(spec_path)
        impl = CircuitGraph.from_blif(impl_path)
        anchors = load_formal_anchors(coi.benchmark, row["optimization"], "formal_all", spec, impl)
        for context_mode in contexts:
            candidates = generate_odc_anchor_candidates(
                benchmark=coi.benchmark,
                optimization=row["optimization"],
                coi=coi,
                spec_graph=spec,
                impl_graph=impl,
                anchors=anchors,
                context_mode=context_mode,
                ranking_mode=args.ranking_mode,
                max_frontier_distance=args.max_frontier_distance,
                max_spec_candidates_per_boundary=args.max_spec_candidates,
                max_impl_candidates_per_spec_node=args.max_impl_candidates,
                case_prefix=row["case_id"],
            )
            for c in candidates:
                rows.append(c.__dict__)
    write_csv(args.output_dir / "odc_candidate_features.csv", rows, COLUMNS)
    print(f"Wrote ODC candidate rows: {len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
