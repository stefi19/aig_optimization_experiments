#!/usr/bin/env python3
"""Build a canonical manifest for committed research artifact outputs."""

from __future__ import annotations

import csv
import hashlib
import json
import platform
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "artifact_manifest.csv"
ABC_REV = "bcfdf592289a408cd67ec19260f8a60a37b085b6"
SCHEMA_VERSION = "artifact_manifest_v1"

RESULT_FAMILIES = [
    ("core_correspondence", "results/summary_metrics.csv", "make generate-variants analyze"),
    ("sat_refinement", "results/sat_summary.csv", "make sat-pipeline"),
    ("blind_semantic_cegis", "results/blind_semantic_cegis/blind_semantic_recovery_summary.csv", "make blind-semantic-cegis-all"),
    ("semantic_recoverability_frontier", "results/semantic_recoverability_frontier/final_supported_claims_summary.md", "make semantic-recoverability-all"),
    ("active_source_counterparts", "results/active_source_counterpart_refactoring/final_supported_claims_summary.md", "make active-source-counterparts-all"),
    ("cross_netlist_transplantation", "results/cross_netlist_cut_transplantation/supported_claims_summary.md", "make cross-netlist-transplant-all"),
    ("formal_locality_barriers", "results/formal_locality_barriers/formal_locality_barrier_summary.md", "make formal-locality-all"),
    ("necessity_first_targets", "results/necessity_first_target_discovery/corrected_scientific_claims.csv", "make necessity-targets-all"),
    ("research_wow", "results/research_wow/recoverability_frontier.csv", "make research-wow"),
    ("evidence_advancement", "results/evidence_advancement/evidence_advancement_summary.csv", "make evidence-advancement"),
]

FIELDS = [
    "result_family",
    "primary_artifact",
    "artifact_sha256",
    "artifact_rows",
    "reproduction_command",
    "git_head",
    "config_hash",
    "python_version",
    "z3_version",
    "abc_revision",
    "dataset_classes",
    "schema_version",
]


def main() -> int:
    rows = []
    dataset_classes = _dataset_classes()
    for family, rel_path, command in RESULT_FAMILIES:
        path = ROOT / rel_path
        rows.append(
            {
                "result_family": family,
                "primary_artifact": rel_path,
                "artifact_sha256": _sha256(path) if path.exists() else "",
                "artifact_rows": str(_row_count(path) if path.exists() else 0),
                "reproduction_command": command,
                "git_head": _git_head(),
                "config_hash": _hash({"family": family, "command": command, "abc_rev": ABC_REV}),
                "python_version": platform.python_version(),
                "z3_version": _z3_version(),
                "abc_revision": ABC_REV,
                "dataset_classes": json.dumps(dataset_classes.get(family, []), sort_keys=True),
                "schema_version": SCHEMA_VERSION,
            }
        )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {OUT.relative_to(ROOT)} with {len(rows)} result families")
    return 0


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


def _dataset_classes() -> dict[str, list[str]]:
    classes: dict[str, set[str]] = {}
    necessity = ROOT / "results" / "necessity_first_target_discovery" / "dataset_classification.csv"
    if necessity.exists():
        with necessity.open(newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                classes.setdefault("necessity_first_targets", set()).add(row.get("dataset_class", ""))
    summary = ROOT / "results" / "summary_metrics.csv"
    if summary.exists():
        with summary.open(newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                classes.setdefault("core_correspondence", set()).add(row.get("source_family", ""))
    advancement = ROOT / "results" / "evidence_advancement" / "evidence_advancement_summary.csv"
    if advancement.exists():
        classes.setdefault("evidence_advancement", set()).update(
            {
                "blind_generated_blif",
                "controlled_generated_blif",
                "generated_research_benchmark",
                "historical_diagnostic",
                "rtl_corpus",
            }
        )
    return {key: sorted(value - {""}) for key, value in classes.items()}


def _git_head() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, stderr=subprocess.DEVNULL, timeout=5).strip()
    except Exception:
        return "unknown"


def _z3_version() -> str:
    try:
        import z3  # type: ignore

        return z3.get_version_string()
    except Exception:
        return "unavailable"


def _hash(payload: object) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()[:16]


if __name__ == "__main__":
    raise SystemExit(main())
