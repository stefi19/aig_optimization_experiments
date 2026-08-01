#!/usr/bin/env python3
"""Validate derived research-facing artifact outputs."""

from __future__ import annotations

import csv
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "research_wow"
SCHEMA = "research_wow_v1"

REQUIRED = {
    "recoverability_frontier.csv": {
        "result_family",
        "denominator_class",
        "denominator",
        "success_count",
        "success_rate",
        "evidence_level",
        "evidence_file",
        "schema_version",
    },
    "failure_taxonomy.csv": {
        "failure_class",
        "definition",
        "denominator_class",
        "count",
        "evidence_file",
        "implication",
        "schema_version",
    },
    "ablation_summary.csv": {
        "experiment_family",
        "ablation",
        "denominator",
        "success_count",
        "success_metric",
        "success_rate",
        "schema_version",
    },
    "baseline_summary.csv": {
        "experiment_family",
        "baseline",
        "denominator",
        "success_count",
        "success_metric",
        "success_rate",
        "schema_version",
    },
    "demo_trace.csv": {
        "mode",
        "stage",
        "subject",
        "artifact_key",
        "status",
        "evidence_level",
        "artifact",
        "schema_version",
    },
}


def main() -> int:
    errors: list[str] = []
    tables = {name: read_required(name, columns, errors) for name, columns in REQUIRED.items()}
    if errors:
        return fail(errors)

    check_frontier(tables["recoverability_frontier.csv"], errors)
    check_taxonomy(tables["failure_taxonomy.csv"], errors)
    check_ablation_baseline(tables["ablation_summary.csv"], "ablation", errors)
    check_ablation_baseline(tables["baseline_summary.csv"], "baseline", errors)
    check_demo(tables["demo_trace.csv"], errors)
    check_paper_files(errors)
    if errors:
        return fail(errors)
    print("Research-wow artifacts validated")
    return 0


def check_frontier(rows: list[dict[str, str]], errors: list[str]) -> None:
    expected = {
        "controlled_active_source_counterparts": ("10", "10"),
        "controlled_cross_netlist_transplants": ("12", "12"),
        "blind_parametric_cegis": ("3", "24"),
        "necessity_first_compact_interfaces": ("31", "48"),
        "necessity_first_graph_rewrites": ("0", "48"),
        "formal_locality_previous_failures": ("26", "56"),
        "historical_cross_netlist_recovery": ("0", "56"),
    }
    by_family = {r["result_family"]: r for r in rows}
    missing = set(expected) - set(by_family)
    if missing:
        errors.append(f"recoverability frontier missing rows: {sorted(missing)}")
    for family, (success, denom) in expected.items():
        row = by_family.get(family)
        if not row:
            continue
        if row["success_count"] != success or row["denominator"] != denom:
            errors.append(
                f"{family} drifted: {row['success_count']}/{row['denominator']} != {success}/{denom}"
            )
        rate = float(row["success_rate"])
        expected_rate = int(success) / int(denom) if int(denom) else 0
        if abs(rate - expected_rate) > 0.000001:
            errors.append(f"{family} success_rate is inconsistent with count/denominator")
        if not (ROOT / row["evidence_file"]).exists():
            errors.append(f"{family} evidence file is missing: {row['evidence_file']}")


def check_taxonomy(rows: list[dict[str, str]], errors: list[str]) -> None:
    expected_counts = {
        "missing_optimized_artifact": "36",
        "historical_target_irrelevant_after_reconstruction": "20",
        "non_compact_exact_input_interface": "17",
        "no_validated_graph_rewrite_artifact": "48",
    }
    by_class = {r["failure_class"]: r for r in rows}
    for klass, count in expected_counts.items():
        if by_class.get(klass, {}).get("count") != count:
            errors.append(f"failure taxonomy drifted for {klass}")
    if not any(r["failure_class"].startswith("blind_cegis::") for r in rows):
        errors.append("failure taxonomy lacks blind CEGIS failure classes")
    if not any(r["failure_class"].startswith("formal_locality_barrier::") for r in rows):
        errors.append("failure taxonomy lacks formal locality failure classes")


def check_ablation_baseline(rows: list[dict[str, str]], name_col: str, errors: list[str]) -> None:
    families = {r["experiment_family"] for r in rows}
    required = {"active_source_counterpart", "cross_netlist_transplant", "formal_locality_barrier"}
    missing = required - families
    if missing:
        errors.append(f"{name_col} summary missing families: {sorted(missing)}")
    for row in rows:
        denom = float(row["denominator"])
        success = float(row["success_count"])
        rate = float(row["success_rate"])
        if denom < 0 or success < 0:
            errors.append(f"{name_col} row has negative counts: {row}")
        if denom and abs(rate - success / denom) > 0.000001:
            errors.append(f"{name_col} row has inconsistent success rate: {row.get(name_col)}")


def check_demo(rows: list[dict[str, str]], errors: list[str]) -> None:
    modes = {r["mode"] for r in rows}
    if not {"controlled", "blind"}.issubset(modes):
        errors.append("demo trace must include controlled and blind rows")
    if not any(r["evidence_level"] == "abc_cec" and r["status"] == "equivalent/equivalent" for r in rows):
        errors.append("demo trace lacks controlled ABC CEC acceptance row")
    if not any(r["evidence_level"] == "counterexample_refinement" for r in rows):
        errors.append("demo trace lacks blind counterexample refinement")
    if not any(r["evidence_level"] == "formal_exhaustive" for r in rows):
        errors.append("demo trace lacks blind formal proof row")
    for row in rows:
        if not (ROOT / row["artifact"]).exists():
            errors.append(f"demo artifact is missing: {row['artifact']}")


def check_paper_files(errors: list[str]) -> None:
    required = [
        "results/research_wow/recoverability_frontier.png",
        "results/research_wow/demo_report.md",
        "paper/outline.md",
        "paper/claims_to_tables.md",
        "paper/tables/research_wow_tables.md",
        "paper/case_studies/counterpart_and_blind_cegis.md",
        "paper/figures/recoverability_frontier.png",
        "paper/figures/motivating_problem.png",
        "paper/figures/recoverability_hierarchy.png",
        "paper/figures/methodology_pipeline.png",
        "paper/figures/failure_taxonomy.png",
        "paper/figures/case_study_trace.png",
        "paper/figures/interface_ablation.png",
    ]
    for rel in required:
        path = ROOT / rel
        if not path.exists() or path.stat().st_size == 0:
            errors.append(f"missing or empty paper artifact: {rel}")
    text = (ROOT / "paper" / "outline.md").read_text(encoding="utf-8")
    for phrase in [
        "Threat Model",
        "Failure Taxonomy",
        "Ablations and Baselines",
        "Related Work Positioning",
    ]:
        if phrase not in text:
            errors.append(f"paper outline missing section: {phrase}")


def read_required(name: str, required: set[str], errors: list[str]) -> list[dict[str, str]]:
    path = OUT / name
    if not path.exists():
        errors.append(f"missing research-wow output: {name}")
        return []
    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        fieldnames = set(reader.fieldnames or [])
        missing = required - fieldnames
        if missing:
            errors.append(f"{name} missing columns: {sorted(missing)}")
        rows = list(reader)
    if not rows:
        errors.append(f"{name} has no rows")
    for row in rows:
        if row.get("schema_version") != SCHEMA:
            errors.append(f"{name} has wrong schema_version: {row.get('schema_version')}")
    return rows


def fail(errors: list[str]) -> int:
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
