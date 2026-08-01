#!/usr/bin/env python3
"""Validate headline artifact claims against committed result tables."""

from __future__ import annotations

import csv
import sys
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    errors: list[str] = []
    _check_active_source(errors)
    _check_cross_netlist(errors)
    _check_necessity(errors)
    _check_blind_cegis(errors)
    _check_manifest(errors)
    _check_docs_freshness(errors)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("Artifact claims validated")
    return 0


def _check_active_source(errors: list[str]) -> None:
    controlled = _rows("results/active_source_counterpart_refactoring/controlled_results.csv", errors)
    development = _rows("results/active_source_counterpart_refactoring/development_results.csv", errors)
    accepted = [r for r in controlled if r.get("final_status") == "accepted"]
    if len(accepted) != 10:
        errors.append(f"active-source controlled accepted count drifted: {len(accepted)} != 10")
    if any(r.get("source_cec_status") != "equivalent" or r.get("cross_cec_status") != "equivalent" for r in accepted):
        errors.append("active-source accepted rows are missing source/cross CEC equivalence")
    if sum(r.get("new_recovered_boundary") == "true" for r in development) != 0:
        errors.append("active-source real/development rows claim recovered boundaries")


def _check_cross_netlist(errors: list[str]) -> None:
    controlled = _rows("results/cross_netlist_cut_transplantation/controlled_results.csv", errors)
    development = _rows("results/cross_netlist_cut_transplantation/development_results.csv", errors)
    accepted = [r for r in controlled if r.get("final_status") == "accepted"]
    if len(accepted) != 12:
        errors.append(f"cross-netlist controlled accepted count drifted: {len(accepted)} != 12")
    if any(r.get("expected_outcome", "").startswith("negative") for r in accepted):
        errors.append("cross-netlist negative control was accepted")
    if len(development) != 56:
        errors.append(f"cross-netlist historical development denominator drifted: {len(development)} != 56")
    if sum(r.get("new_recovered_boundary") == "true" for r in development) != 0:
        errors.append("cross-netlist real/development rows claim recovered boundaries")


def _check_necessity(errors: list[str]) -> None:
    eligible = _rows("results/necessity_first_target_discovery/eligible_target_manifest.csv", errors)
    locality = _rows("results/necessity_first_target_discovery/formal_locality_results.csv", errors)
    rewrites = _rows("results/necessity_first_target_discovery/graph_rewrites.csv", errors)
    recon = _rows("results/provenance_eligibility_audit/provenance_reconstruction.csv", errors)
    if len(eligible) != 48 or any(r.get("eligibility_status") != "eligible_target_necessary" for r in eligible):
        errors.append("necessity-first eligible target manifest no longer has 48 necessary targets")
    if sum(r.get("compact_interface") == "true" for r in locality) != 31:
        errors.append("necessity-first compact-interface count drifted from 31")
    if sum(r.get("rewrite_emitted") == "true" for r in rewrites) != 0:
        errors.append("necessity-first graph rewrites were emitted but claims still say zero")
    counts = Counter(r.get("reconstruction_status") for r in recon)
    if counts.get("missing_optimized_artifact", 0) != 36:
        errors.append("provenance audit no longer has 36 missing optimized-artifact rows")
    if counts.get("provenance_reconstructed_exact", 0) != 20:
        errors.append("provenance audit no longer has 20 reconstructed diagnostics")


def _check_blind_cegis(errors: list[str]) -> None:
    rows = _rows("results/blind_semantic_cegis/cegis_iterations.csv", errors)
    sat = [r for r in rows if r.get("solver_status") == "sat"]
    if not sat:
        errors.append("blind CEGIS committed iterations contain no SAT refinement rows")
    if any(int(r.get("examples_after", "0")) <= int(r.get("examples_before", "0")) for r in sat):
        errors.append("blind CEGIS SAT rows do not increase example counts")


def _check_manifest(errors: list[str]) -> None:
    manifest = _rows("results/artifact_manifest.csv", errors)
    families = {r.get("result_family") for r in manifest}
    required = {
        "core_correspondence",
        "sat_refinement",
        "blind_semantic_cegis",
        "semantic_recoverability_frontier",
        "active_source_counterparts",
        "cross_netlist_transplantation",
        "formal_locality_barriers",
        "necessity_first_targets",
        "research_wow",
        "evidence_advancement",
    }
    missing = required - families
    if missing:
        errors.append(f"artifact manifest missing families: {sorted(missing)}")
    for row in manifest:
        if not row.get("artifact_sha256") or row.get("artifact_rows") == "0":
            errors.append(f"artifact manifest has empty artifact entry: {row.get('result_family')}")


def _check_docs_freshness(errors: list[str]) -> None:
    text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in [ROOT / "README.md", ROOT / "docs" / "research_summary_current_state.md", ROOT / "ARTIFACTS.md", ROOT / "CLAIMS.md"]
        if path.exists()
    )
    required_phrases = [
        "Controlled accepted graph-active counterparts: 10",
        "Controlled accepted transplants: 12",
        "48 fresh provenance-complete",
        "31/48 have compact exact input interfaces",
        "corrected historical eligible transplantation denominator: 0",
        "Evidence-advancement promoted rows",
    ]
    for phrase in required_phrases:
        if phrase not in text:
            errors.append(f"docs missing current claim phrase: {phrase}")


def _rows(rel_path: str, errors: list[str]) -> list[dict[str, str]]:
    path = ROOT / rel_path
    if not path.exists():
        errors.append(f"missing required artifact table: {rel_path}")
        return []
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


if __name__ == "__main__":
    raise SystemExit(main())
