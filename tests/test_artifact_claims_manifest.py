from __future__ import annotations

import csv
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "results" / "artifact_manifest.csv"


def _read_manifest() -> list[dict[str, str]]:
    with MANIFEST.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _write_manifest(rows: list[dict[str, str]]) -> None:
    with MANIFEST.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _check_claims() -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "check_artifact_claims.py")],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def test_artifact_claims_accepts_committed_manifest() -> None:
    result = _check_claims()
    assert result.returncode == 0, result.stderr


def test_artifact_claims_rejects_manifest_hash_drift() -> None:
    original = MANIFEST.read_text(encoding="utf-8")
    rows = _read_manifest()
    rows[0]["artifact_sha256"] = "0" * 64
    try:
        _write_manifest(rows)
        result = _check_claims()
        assert result.returncode != 0
        assert "artifact manifest hash mismatch" in result.stderr
    finally:
        MANIFEST.write_text(original, encoding="utf-8")


def test_artifact_claims_rejects_manifest_row_count_drift() -> None:
    original = MANIFEST.read_text(encoding="utf-8")
    rows = _read_manifest()
    rows[0]["artifact_rows"] = str(int(rows[0]["artifact_rows"]) + 1)
    try:
        _write_manifest(rows)
        result = _check_claims()
        assert result.returncode != 0
        assert "artifact manifest row count mismatch" in result.stderr
    finally:
        MANIFEST.write_text(original, encoding="utf-8")


def test_artifact_claims_rejects_manifest_family_drift() -> None:
    original = MANIFEST.read_text(encoding="utf-8")
    rows = _read_manifest()
    rows[1]["result_family"] = rows[0]["result_family"]
    try:
        _write_manifest(rows)
        result = _check_claims()
        assert result.returncode != 0
        assert "artifact manifest has duplicate result families" in result.stderr
    finally:
        MANIFEST.write_text(original, encoding="utf-8")


def test_artifact_claims_rejects_malformed_manifest_git_head() -> None:
    original = MANIFEST.read_text(encoding="utf-8")
    rows = _read_manifest()
    rows[0]["git_head"] = "not-a-sha"
    try:
        _write_manifest(rows)
        result = _check_claims()
        assert result.returncode != 0
        assert "artifact manifest git head is not a known commit" in result.stderr
    finally:
        MANIFEST.write_text(original, encoding="utf-8")
