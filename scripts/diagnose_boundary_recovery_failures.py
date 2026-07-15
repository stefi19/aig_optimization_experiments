#!/usr/bin/env python3
"""Generate boundary-recovery failure taxonomy and diagnosis outputs."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from boundary_diagnosis import (  # noqa: E402
    ALIGNMENT_COLUMNS,
    CASE_COLUMNS,
    COI_AUDIT_COLUMNS,
    COVERAGE_COLUMNS,
    DEFAULT_SEED_OPTIMIZATIONS,
    DIAG_RESULTS,
    PROGRESSION_OPTIMIZATIONS,
    critical_path_overlap_rows,
    differential_rows,
    generated_critical_path_coi_rows,
    load_coi_specs,
    progression_rows,
    run_diagnostic_suite,
    summarize_diagnosis,
    write_csv,
)


COMPLETION_COLUMNS = [
    "case_id",
    "benchmark",
    "coi_name",
    "optimization",
    "anchor_mode",
    "ebo_nodes",
    "paths_to_ebo_count_or_proxy",
    "paths_already_cut",
    "uncut_path_count_or_proxy",
    "completion_nodes_added",
    "completion_anchor_categories",
    "completion_success",
    "completion_failure_reason",
]

ANCHOR_AUDIT_COLUMNS = [
    "case_id",
    "benchmark",
    "coi_name",
    "optimization",
    "anchor_mode",
    "spec_node",
    "candidate_anchor_count",
    "selected_anchor",
    "selected_anchor_category",
    "selected_anchor_polarity",
    "selection_rule",
    "alternative_anchor_count",
    "relevant_to_boundary_search",
    "alternative_anchor_would_change_cycle_status",
    "alternative_anchor_would_reduce_distance",
    "alternative_anchor_would_complete_cut",
    "diagnostic_outcome",
]

DIFF_COLUMNS = [
    "case_id",
    "benchmark",
    "coi_name",
    "optimization",
    "exact_only_success",
    "formal_all_success",
    "success_delta",
    "exact_only_extension",
    "formal_all_extension",
    "extension_delta",
    "exact_only_relevant_anchor_count",
    "formal_all_relevant_anchor_count",
    "relevant_anchor_delta",
    "exact_only_ebi_count",
    "formal_all_ebi_count",
    "exact_only_ebo_count",
    "formal_all_ebo_count",
    "selected_sat_cec_anchor_count",
    "available_but_unselected_sat_cec_anchor_count",
    "formal_all_added_relevant_anchors",
    "formal_all_added_cut_candidate_anchors",
    "differential_classification",
]


def parse_csv_list(value: str, default: list[str]) -> list[str]:
    if not value:
        return list(default)
    return [item.strip() for item in value.split(",") if item.strip()]


def run(output_dir: Path, optimizations: list[str]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    identity = run_diagnostic_suite(optimizations=["identity"], anchor_modes=["exact_only"])
    seed = run_diagnostic_suite(optimizations=optimizations, anchor_modes=["exact_only", "formal_all"])
    progression = run_diagnostic_suite(optimizations=PROGRESSION_OPTIMIZATIONS, anchor_modes=["formal_all"])

    diff = differential_rows(seed.cases, seed.coverage)
    prog_rows = progression_rows(progression.cases)
    cois = load_coi_specs(ROOT / "benchmarks" / "coi_specs" / "boundary_recovery_seed_cois.json")
    critical_overlap = critical_path_overlap_rows(cois, seed.cases)
    generated_cp = generated_critical_path_coi_rows()

    write_csv(output_dir / "boundary_failure_taxonomy.csv", seed.cases, CASE_COLUMNS)
    write_csv(output_dir / "boundary_stage_progress.csv", seed.stage_progress)
    write_csv(output_dir / "boundary_identity_baseline.csv", identity.cases, CASE_COLUMNS)
    write_csv(output_dir / "boundary_optimization_progression.csv", prog_rows)
    write_csv(output_dir / "boundary_anchor_coverage.csv", seed.coverage, COVERAGE_COLUMNS)
    write_csv(output_dir / "boundary_anchor_mode_differential.csv", diff, DIFF_COLUMNS)
    write_csv(output_dir / "boundary_anchor_selection_audit.csv", seed.anchor_audit, ANCHOR_AUDIT_COLUMNS)
    write_csv(output_dir / "boundary_coi_audit.csv", seed.coi_audit, COI_AUDIT_COLUMNS)
    write_csv(output_dir / "boundary_completion_diagnosis.csv", seed.completion, COMPLETION_COLUMNS)
    write_csv(output_dir / "boundary_alignment_checks.csv", seed.alignment, ALIGNMENT_COLUMNS)
    write_csv(output_dir / "boundary_critical_path_overlap.csv", critical_overlap)
    write_csv(output_dir / "boundary_generated_critical_path_cois.csv", generated_cp)
    (output_dir / "boundary_diagnosis_summary.md").write_text(
        summarize_diagnosis(
            identity=identity.cases,
            cases=seed.cases,
            coverage=seed.coverage,
            differential=diff,
            progression=prog_rows,
            coi_audit=seed.coi_audit,
            critical_overlap=critical_overlap,
            generated_cp=generated_cp,
            anchor_audit=seed.anchor_audit,
        ),
        encoding="utf-8",
    )
    print(f"Boundary diagnosis outputs written to {output_dir}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DIAG_RESULTS)
    parser.add_argument("--optimizations", default=",".join(DEFAULT_SEED_OPTIMIZATIONS))
    parser.add_argument("--include-identity", action="store_true", help="accepted for CLI compatibility; identity is always generated")
    parser.add_argument("--trace-failures", action="store_true", help="reserved for compact trace generation")
    parser.add_argument("--critical-path-segment-sizes", default="3,5,8")
    parser.add_argument("--max-alternative-anchor-audits", type=int, default=0)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    run(args.output_dir, parse_csv_list(args.optimizations, DEFAULT_SEED_OPTIMIZATIONS))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
