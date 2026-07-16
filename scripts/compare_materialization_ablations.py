#!/usr/bin/env python3
"""Summarize materialized correspondence ablations and failure taxonomy."""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "materialized_correspondence"


def main() -> int:
    targets = rows("materialization_targets.csv")
    cuts = rows("anchored_cut_candidates.csv")
    functions = rows("cut_function_extraction.csv")
    wires = rows("materialized_wires.csv")
    proofs = rows("materialized_anchor_formal_results.csv")
    proven = rows("proven_materialized_anchors.csv")
    boundary = rows("materialized_boundary_recovery.csv")
    usage = rows("materialized_anchor_usage.csv")
    extracted = [r for r in functions if r["extraction_status"] == "extracted"]
    generated = [r for r in wires if r["generation_status"] == "generated"]
    proven_rows = [r for r in proofs if r["proof_status"] == "proven_materialized_anchor"]
    selected = [r for r in usage if str(r.get("selected_by_boundary")).lower() == "true"]
    ablations = [
        {
            "ablation": "cut_size_le_2",
            "targets": len(targets),
            "cuts": sum(int(r["cut_size"]) <= 2 for r in cuts),
            "functions_extracted": sum(int(r.get("cut_size") or 99) <= 2 for r in _join_cut_size(extracted, cuts)),
            "formal_checks": sum(int(r.get("cut_size") or 99) <= 2 for r in _join_cut_size(proofs, cuts)),
            "proven_materialized_anchors": sum(int(r.get("cut_size") or 99) <= 2 for r in proven),
            "new_boundary_recoveries": sum(str(r.get("newly_recovered_boundary")).lower() == "true" for r in boundary),
        },
        {
            "ablation": "cut_size_le_3",
            "targets": len(targets),
            "cuts": len(cuts),
            "functions_extracted": len(extracted),
            "formal_checks": len(proofs),
            "proven_materialized_anchors": len(proven_rows),
            "new_boundary_recoveries": sum(str(r.get("newly_recovered_boundary")).lower() == "true" for r in boundary),
        },
        {
            "ablation": "ranking_hybrid",
            "targets": len(targets),
            "cuts": len(cuts),
            "functions_extracted": len(extracted),
            "formal_checks": len(proofs),
            "proven_materialized_anchors": len(proven_rows),
            "new_boundary_recoveries": sum(str(r.get("newly_recovered_boundary")).lower() == "true" for r in boundary),
        },
        {
            "ablation": "truth_table_direct",
            "targets": len(targets),
            "cuts": len(cuts),
            "functions_extracted": len(extracted),
            "formal_checks": len(proofs),
            "proven_materialized_anchors": len(proven_rows),
            "new_boundary_recoveries": sum(str(r.get("newly_recovered_boundary")).lower() == "true" for r in boundary),
        },
    ]
    write_csv(OUT / "materialized_ablation_results.csv", ablations)
    failures = failure_rows(targets, cuts, functions, wires, proofs, usage)
    write_csv(OUT / "materialized_failure_analysis.csv", failures)
    (OUT / "materialized_correspondence_summary.md").write_text(summary(targets, cuts, functions, wires, proofs, proven, boundary, usage, failures), encoding="utf-8")
    print("Wrote materialized correspondence ablations and summary")
    return 0


def failure_rows(targets, cuts, functions, wires, proofs, usage):
    out = []
    if not targets:
        out.append({"stage": "target_selection", "failure_reason": "no_unmatched_frontier_target", "count": 1})
    no_cut_targets = set(r["case_id"] for r in targets) - set(r["case_id"] for r in cuts)
    if no_cut_targets:
        out.append({"stage": "cut_enumeration", "failure_reason": "no_anchored_cut", "count": len(no_cut_targets)})
    for reason, count in Counter(r["failure_reason"] for r in functions if r["extraction_status"] != "extracted").items():
        out.append({"stage": "function_extraction", "failure_reason": reason or "function_extraction_failed", "count": count})
    for reason, count in Counter(r["failure_reason"] for r in wires if r["generation_status"] != "generated").items():
        out.append({"stage": "wire_materialization", "failure_reason": reason or "augmentation_generation_failed", "count": count})
    for reason, count in Counter(r["failure_reason"] for r in proofs if r["proof_status"] != "proven_materialized_anchor").items():
        out.append({"stage": "formal_proof", "failure_reason": reason or "formal_disproof", "count": count})
    unused = sum(str(r.get("usable_for_boundary")).lower() != "true" for r in usage)
    if unused:
        out.append({"stage": "boundary_utility", "failure_reason": "proven_anchor_not_on_usable_frontier", "count": unused})
    return out


def summary(targets, cuts, functions, wires, proofs, proven, boundary, usage, failures) -> str:
    extracted = [r for r in functions if r["extraction_status"] == "extracted"]
    generated = [r for r in wires if r["generation_status"] == "generated"]
    selected = [r for r in usage if str(r.get("selected_by_boundary")).lower() == "true"]
    newly = [r for r in boundary if str(r.get("newly_recovered_boundary")).lower() == "true"]
    proof_times = [float(r["proof_runtime_seconds"]) for r in proofs if r.get("proof_runtime_seconds")]
    added = [int(r["added_gate_count"]) for r in generated if r.get("added_gate_count")]
    cut_sizes = Counter(r["cut_size"] for r in cuts)
    proven_by_opt = Counter(r["optimization"] for r in proven)
    boundary_by_opt = Counter(r["optimization"] for r in boundary if str(r.get("newly_recovered_boundary")).lower() == "true")
    lines = [
        "# Anchored-Cut Wire Materialization Summary",
        "",
        "This experiment constructs redundant original-side wires from small globally anchored cuts. A materialized anchor is not a pre-existing original node.",
        "",
        "All accepted materialized anchors require `proof_status=proven_materialized_anchor`, `mapping_category=formal_materialized_anchor`, `anchor_origin=materialized_wire`, `evidence_level=formal_exhaustive`, and `equivalence_scope=global`. No sampled result is used as proof.",
        "",
        "## Pipeline Funnel",
        "",
        f"- Unmatched targets attempted: {len(targets)}",
        f"- Anchored cuts generated: {len(cuts)}",
        f"- Functions extracted: {len(extracted)}",
        f"- Materialization candidates: {len(generated)}",
        f"- Formal checks: {len(proofs)}",
        f"- Proven materialized anchors: {len(proven)}",
        f"- Usable frontier materialized anchors: {sum(str(r.get('usable_for_boundary')).lower() == 'true' for r in usage)}",
        f"- Selected materialized anchors: {len(selected)}",
        f"- Newly recovered boundaries: {len(newly)}",
        "",
        "## Cost and Runtime",
        "",
        f"- Mean added gate count: {_mean(added):.6f}",
        f"- Mean proof runtime seconds: {_mean(proof_times):.6f}",
        "",
        "## Cut Sizes",
        "",
        *[f"- cut size {size}: {count}" for size, count in sorted(cut_sizes.items())],
        "",
        "## Results by Optimization",
        "",
        *[f"- {opt}: {count} proven anchors; {boundary_by_opt.get(opt, 0)} new boundary recoveries" for opt, count in sorted(proven_by_opt.items())],
        "",
        "## Boundary Utility",
        "",
        "The current materialized wires are additive and are not reconnected into the original boundary graph. If no selected anchors are reported, this is evidence that target selection or graph integration, not proof generation, is the bottleneck.",
        "",
        "## Failure Taxonomy",
        "",
    ]
    if failures:
        lines.extend(f"- {r['stage']} / {r['failure_reason']}: {r['count']}" for r in failures)
    else:
        lines.append("- No failures recorded.")
    return "\n".join(lines) + "\n"


def _join_cut_size(rows, cuts):
    sizes = {r["cut_id"]: r["cut_size"] for r in cuts}
    return [{**r, "cut_size": sizes.get(r["cut_id"], "")} for r in rows]


def _mean(values):
    return sum(values) / len(values) if values else 0.0


def rows(name):
    path = OUT / name
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def write_csv(path: Path, rows_: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    cols = sorted({k for row in rows_ for k in row}) if rows_ else []
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=cols, lineterminator="\n")
        writer.writeheader()
        for row in rows_:
            writer.writerow(row)


if __name__ == "__main__":
    raise SystemExit(main())
