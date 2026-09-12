#!/usr/bin/env python3
"""Validate headline artifact claims against committed result tables."""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ABC_REV = "bcfdf592289a408cd67ec19260f8a60a37b085b6"
ARTIFACT_MANIFEST_SCHEMA = "artifact_manifest_v1"

EXPECTED_MANIFEST = {
    "core_correspondence": ("results/summary_metrics.csv", "make generate-variants analyze"),
    "sat_refinement": ("results/sat_summary.csv", "make sat-pipeline"),
    "blind_semantic_cegis": ("results/blind_semantic_cegis/blind_semantic_recovery_summary.csv", "make blind-semantic-cegis-all"),
    "semantic_recoverability_frontier": ("results/semantic_recoverability_frontier/final_supported_claims_summary.md", "make semantic-recoverability-all"),
    "active_source_counterparts": ("results/active_source_counterpart_refactoring/final_supported_claims_summary.md", "make active-source-counterparts-all"),
    "cross_netlist_transplantation": ("results/cross_netlist_cut_transplantation/supported_claims_summary.md", "make cross-netlist-transplant-all"),
    "formal_locality_barriers": ("results/formal_locality_barriers/formal_locality_barrier_summary.md", "make formal-locality-all"),
    "necessity_first_targets": ("results/necessity_first_target_discovery/corrected_scientific_claims.csv", "make necessity-targets-all"),
    "research_wow": ("results/research_wow/recoverability_frontier.csv", "make research-wow"),
    "evidence_advancement": ("results/evidence_advancement/evidence_advancement_summary.csv", "make evidence-advancement"),
}


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
    frontier = _rows("results/necessity_first_target_discovery/rewrite_frontier_expansion.csv", errors)
    boundary = _rows("results/necessity_first_target_discovery/boundary_recovery.csv", errors)
    global_cec = _rows("results/necessity_first_target_discovery/global_cec.csv", errors)
    recon = _rows("results/provenance_eligibility_audit/provenance_reconstruction.csv", errors)
    if len(eligible) != 48 or any(r.get("eligibility_status") != "eligible_target_necessary" for r in eligible):
        errors.append("necessity-first eligible target manifest no longer has 48 necessary targets")
    if sum(r.get("compact_interface") == "true" for r in locality) != 31:
        errors.append("necessity-first compact-interface count drifted from 31")
    if sum(r.get("rewrite_emitted") == "true" for r in rewrites) != 31:
        errors.append("necessity-first rewrite artifact count drifted from 31")
    if sum(r.get("graph_active") == "true" for r in rewrites) != 22:
        errors.append("necessity-first graph-active rewrite count drifted from 22")
    if sum(r.get("new_boundary") == "true" for r in boundary) != 22:
        errors.append("necessity-first CEC-backed boundary count drifted from 22")
    promoted_frontier = [r for r in frontier if r.get("promotion") == "graph_active_cec_recovery"]
    if len(promoted_frontier) != 4:
        errors.append(f"fanout-frontier promotion count drifted: {len(promoted_frontier)} != 4")
    if any(r.get("rewrite_emitted") != "true" or r.get("graph_active") != "true" or r.get("global_cec_status") != "equivalent" for r in promoted_frontier):
        errors.append("fanout-frontier promotions lack artifact, graph activity, or CEC")
    cec_by_target: dict[str, dict[str, str]] = {}
    for row in global_cec:
        cec_by_target.setdefault(row.get("stable_target_id", ""), {})[row.get("scope", "")] = row.get("status", "")
    for row in boundary:
        if row.get("new_boundary") == "true":
            scopes = cec_by_target.get(row.get("stable_target_id", ""), {})
            rewrite = next((r for r in rewrites if r.get("stable_target_id") == row.get("stable_target_id")), {})
            if rewrite.get("graph_active") != "true" or scopes.get("S_vs_Sprime") != "equivalent" or scopes.get("Sprime_vs_I") != "equivalent":
                errors.append(f"necessity-first boundary lacks graph activity or CEC: {row.get('stable_target_id')}")
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
    required = set(EXPECTED_MANIFEST)
    missing = required - families
    extra = families - required
    if missing:
        errors.append(f"artifact manifest missing families: {sorted(missing)}")
    if extra:
        errors.append(f"artifact manifest has unexpected families: {sorted(extra)}")
    if len(manifest) != len(families):
        errors.append("artifact manifest has duplicate result families")
    for row in manifest:
        family = row.get("result_family", "")
        if row.get("schema_version") != ARTIFACT_MANIFEST_SCHEMA:
            errors.append(f"artifact manifest schema drift: {family}")
        expected = EXPECTED_MANIFEST.get(family)
        if expected is None:
            continue
        expected_path, expected_command = expected
        if row.get("primary_artifact") != expected_path:
            errors.append(f"artifact manifest primary path drift for {family}")
        if row.get("reproduction_command") != expected_command:
            errors.append(f"artifact manifest reproduction command drift for {family}")
        if row.get("abc_revision") != ABC_REV:
            errors.append(f"artifact manifest ABC revision drift for {family}")
        expected_config_hash = _manifest_config_hash(family, expected_command)
        if row.get("config_hash") != expected_config_hash:
            errors.append(f"artifact manifest config hash drift for {family}")
        try:
            dataset_classes = json.loads(row.get("dataset_classes", "[]"))
        except json.JSONDecodeError as exc:
            errors.append(f"artifact manifest dataset classes are invalid JSON for {family}: {exc}")
            dataset_classes = []
        if not isinstance(dataset_classes, list):
            errors.append(f"artifact manifest dataset classes are not a list for {family}")
        artifact = ROOT / expected_path
        if not artifact.exists():
            errors.append(f"artifact manifest primary artifact missing for {family}: {expected_path}")
            continue
        if row.get("artifact_sha256") != _sha256(artifact):
            errors.append(f"artifact manifest hash mismatch for {family}")
        try:
            artifact_rows = int(row.get("artifact_rows", "0"))
        except ValueError:
            errors.append(f"artifact manifest row count is not numeric for {family}")
            artifact_rows = -1
        if artifact_rows != _row_count(artifact) or artifact_rows <= 0:
            errors.append(f"artifact manifest row count mismatch for {family}")
        git_head = row.get("git_head", "")
        if not _is_known_commit(git_head):
            errors.append(f"artifact manifest git head is not a known commit for {family}: {git_head}")


def _check_docs_freshness(errors: list[str]) -> None:
    text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in [ROOT / "README.md", ROOT / "docs" / "research_summary_current_state.md", ROOT / "ARTIFACTS.md", ROOT / "CLAIMS.md"]
        if path.exists()
    )
    summary = {row.get("direction"): row for row in _rows("results/evidence_advancement/evidence_advancement_summary.csv", errors)}
    source_blind = summary.get("source_blind_counterpart_inference", {})
    virtual = summary.get("proof_carrying_virtual_anchors", {})
    source_blind_phrase = f"Evidence-advancement promoted rows: source-blind graph-active {source_blind.get('promoted_rows', '?')}/{source_blind.get('input_rows', '?')}; compact interface new boundaries 22/48"
    virtual_phrase = f"Proof-carrying virtual-anchor synthesis now promotes {virtual.get('promoted_rows', '?')}/{virtual.get('input_rows', '?')}"
    required_phrases = [
        "Controlled accepted graph-active counterparts: 10",
        "Controlled accepted transplants: 12",
        "48 fresh provenance-complete",
        "31/48 have compact exact input interfaces",
        "Necessity-first graph-active CEC-backed new boundaries: 22/48",
        "corrected historical eligible transplantation denominator: 0",
        source_blind_phrase,
        virtual_phrase,
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


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _row_count(path: Path) -> int:
    if path.suffix != ".csv":
        return max(0, len(path.read_text(encoding="utf-8").splitlines()) - 1)
    with path.open(newline="", encoding="utf-8") as fh:
        return sum(1 for _ in csv.DictReader(fh))


def _manifest_config_hash(family: str, command: str) -> str:
    payload = {"family": family, "command": command, "abc_rev": ABC_REV}
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()[:16]


def _is_known_commit(rev: str) -> bool:
    if len(rev) != 40 or any(char not in "0123456789abcdef" for char in rev):
        return False
    if subprocess.run(
        ["git", "cat-file", "-e", f"{rev}^{{commit}}"],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    ).returncode == 0:
        return True
    return _is_shallow_repository()


def _is_shallow_repository() -> bool:
    proc = subprocess.run(
        ["git", "rev-parse", "--is-shallow-repository"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return proc.returncode == 0 and proc.stdout.strip() == "true"


if __name__ == "__main__":
    raise SystemExit(main())
