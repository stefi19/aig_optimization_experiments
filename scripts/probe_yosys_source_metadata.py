#!/usr/bin/env python3
"""Probe whether Yosys preserves source-level metadata on a tiny Verilog example."""

from __future__ import annotations

import argparse
import csv
import json
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_VERILOG = ROOT / "benchmarks" / "source_examples" / "simple_pipeline.v"
CSV_OUT = ROOT / "results" / "yosys_source_metadata_probe.csv"
MD_OUT = ROOT / "results" / "yosys_source_metadata_probe.md"


PROBE_COLUMNS = [
    "tool",
    "available",
    "version",
    "example",
    "json_generated",
    "blif_generated",
    "netnames_with_src",
    "cells_with_src",
    "visible_rtl_signals",
    "notes",
]


@dataclass
class ProbeResult:
    tool: str
    available: bool
    version: str
    example: str
    json_generated: bool
    blif_generated: bool
    netnames_with_src: int
    cells_with_src: int
    visible_rtl_signals: str
    notes: str

    def as_row(self) -> dict[str, str]:
        return {
            "tool": self.tool,
            "available": str(self.available).lower(),
            "version": self.version,
            "example": self.example,
            "json_generated": str(self.json_generated).lower(),
            "blif_generated": str(self.blif_generated).lower(),
            "netnames_with_src": str(self.netnames_with_src),
            "cells_with_src": str(self.cells_with_src),
            "visible_rtl_signals": self.visible_rtl_signals,
            "notes": self.notes,
        }


def find_yosys() -> str | None:
    return shutil.which("yosys")


def yosys_version(yosys_bin: str) -> str:
    result = subprocess.run(
        [yosys_bin, "-V"],
        capture_output=True,
        text=True,
        check=False,
    )
    text = (result.stdout or result.stderr).strip()
    return " ".join(text.split()) if text else "unknown"


def run_yosys(yosys_bin: str, verilog: Path, json_out: Path, blif_out: Path) -> subprocess.CompletedProcess[str]:
    script = (
        f"read_verilog {verilog}; "
        "hierarchy -check -top simple_pipeline; "
        "proc; opt; "
        f"write_json {json_out}; "
        f"write_blif {blif_out}"
    )
    return subprocess.run(
        [yosys_bin, "-q", "-p", script],
        capture_output=True,
        text=True,
        check=False,
    )


def inspect_yosys_json(path: Path, expected_signals: list[str] | None = None) -> dict[str, object]:
    expected = expected_signals or ["mix", "gated", "next_state", "state_q"]
    data = json.loads(path.read_text(encoding="utf-8"))
    modules = data.get("modules", {})
    visible: set[str] = set()
    netnames_with_src = 0
    cells_with_src = 0

    for module in modules.values():
        for name, net in module.get("netnames", {}).items():
            clean = name.lstrip("\\")
            if clean in expected:
                visible.add(clean)
            attrs = net.get("attributes", {})
            if attrs.get("src"):
                netnames_with_src += 1
        for cell in module.get("cells", {}).values():
            attrs = cell.get("attributes", {})
            if attrs.get("src"):
                cells_with_src += 1

    return {
        "visible_signals": sorted(visible),
        "netnames_with_src": netnames_with_src,
        "cells_with_src": cells_with_src,
    }


def unavailable_result(verilog: Path) -> ProbeResult:
    return ProbeResult(
        tool="yosys",
        available=False,
        version="",
        example=str(verilog.relative_to(ROOT)),
        json_generated=False,
        blif_generated=False,
        netnames_with_src=0,
        cells_with_src=0,
        visible_rtl_signals="",
        notes="Yosys not found on PATH; install Yosys to run the metadata-preservation probe.",
    )


def run_probe(verilog: Path = DEFAULT_VERILOG) -> ProbeResult:
    yosys_bin = find_yosys()
    if yosys_bin is None:
        return unavailable_result(verilog)

    with tempfile.TemporaryDirectory(prefix="yosys_source_probe_") as tmp_dir:
        tmp = Path(tmp_dir)
        json_out = tmp / "simple_pipeline.json"
        blif_out = tmp / "simple_pipeline.blif"
        completed = run_yosys(yosys_bin, verilog, json_out, blif_out)
        if completed.returncode != 0:
            snippet = " ".join((completed.stderr or completed.stdout).split())[:300]
            return ProbeResult(
                tool="yosys",
                available=True,
                version=yosys_version(yosys_bin),
                example=str(verilog.relative_to(ROOT)),
                json_generated=json_out.exists(),
                blif_generated=blif_out.exists(),
                netnames_with_src=0,
                cells_with_src=0,
                visible_rtl_signals="",
                notes=f"Yosys run failed: {snippet}",
            )

        metadata = inspect_yosys_json(json_out) if json_out.exists() else {
            "visible_signals": [],
            "netnames_with_src": 0,
            "cells_with_src": 0,
        }
        visible = ",".join(metadata["visible_signals"])
        notes = "JSON metadata inspected; BLIF generated for name-survival comparison."
        return ProbeResult(
            tool="yosys",
            available=True,
            version=yosys_version(yosys_bin),
            example=str(verilog.relative_to(ROOT)),
            json_generated=json_out.exists(),
            blif_generated=blif_out.exists(),
            netnames_with_src=int(metadata["netnames_with_src"]),
            cells_with_src=int(metadata["cells_with_src"]),
            visible_rtl_signals=visible,
            notes=notes,
        )


def write_outputs(result: ProbeResult, csv_out: Path = CSV_OUT, md_out: Path = MD_OUT) -> None:
    csv_out.parent.mkdir(parents=True, exist_ok=True)
    with csv_out.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=PROBE_COLUMNS)
        writer.writeheader()
        writer.writerow(result.as_row())

    row = result.as_row()
    md = [
        "# Yosys Source Metadata Probe",
        "",
        "This probe checks whether a tiny Verilog example can be lowered by Yosys",
        "while preserving signal names or source-location attributes.",
        "",
        f"- Yosys available: `{row['available']}`",
        f"- Version: `{row['version'] or 'not available'}`",
        f"- Example: `{row['example']}`",
        f"- JSON generated: `{row['json_generated']}`",
        f"- BLIF generated: `{row['blif_generated']}`",
        f"- Netnames with `src`: `{row['netnames_with_src']}`",
        f"- Cells with `src`: `{row['cells_with_src']}`",
        f"- Visible RTL signals: `{row['visible_rtl_signals'] or 'none recorded'}`",
        "",
        f"Notes: {row['notes']}",
        "",
        "Interpretation: this is an availability and metadata-survival probe only.",
        "If Yosys is unavailable, the source-map prototype writes a documented skip row.",
    ]
    md_out.write_text("\n".join(md) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verilog", type=Path, default=DEFAULT_VERILOG)
    parser.add_argument("--csv", type=Path, default=CSV_OUT)
    parser.add_argument("--md", type=Path, default=MD_OUT)
    args = parser.parse_args()

    result = run_probe(args.verilog)
    write_outputs(result, args.csv, args.md)
    print(f"Wrote {args.csv}")
    print(f"Wrote {args.md}")
    print(f"Yosys available: {result.available}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
