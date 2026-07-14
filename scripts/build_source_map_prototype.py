#!/usr/bin/env python3
"""Build a tiny RTL-signal to lowered-net source-map prototype."""

from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_VERILOG = ROOT / "benchmarks" / "source_examples" / "simple_pipeline.v"
CSV_OUT = ROOT / "results" / "source_map_prototype.csv"
MD_OUT = ROOT / "results" / "source_map_prototype.md"
NEXT_STEPS_OUT = ROOT / "results" / "source_mapping_next_steps.md"

SOURCE_MAP_COLUMNS = [
    "rtl_signal",
    "module",
    "lowered_name",
    "source_file",
    "source_line",
    "source_attribute",
    "available",
    "confidence",
    "notes",
]

EXPECTED_SIGNALS = ["mix", "gated", "next_state", "state_q"]


@dataclass
class SourceMapRow:
    rtl_signal: str
    module: str
    lowered_name: str
    source_file: str
    source_line: str
    source_attribute: str
    available: bool
    confidence: str
    notes: str

    def as_row(self) -> dict[str, str]:
        return {
            "rtl_signal": self.rtl_signal,
            "module": self.module,
            "lowered_name": self.lowered_name,
            "source_file": self.source_file,
            "source_line": self.source_line,
            "source_attribute": self.source_attribute,
            "available": str(self.available).lower(),
            "confidence": self.confidence,
            "notes": self.notes,
        }


def find_yosys() -> str | None:
    return shutil.which("yosys")


def parse_src_attribute(src: str) -> tuple[str, str]:
    """Return a best-effort (file, line) pair from a Yosys `src` attribute."""
    if not src:
        return "", ""
    first = src.split("|", 1)[0]
    match = re.match(r"^(?P<file>.+):(?P<line>\d+)(?:[.:].*)?$", first)
    if match:
        return match.group("file"), match.group("line")
    parts = first.rsplit(":", 2)
    if len(parts) >= 2 and parts[-2].isdigit():
        return ":".join(parts[:-2]), parts[-2]
    if len(parts) >= 2 and parts[-1].isdigit():
        return ":".join(parts[:-1]), parts[-1]
    return first, ""


def run_yosys_json(yosys_bin: str, verilog: Path, json_out: Path) -> subprocess.CompletedProcess[str]:
    script = (
        f"read_verilog {verilog}; "
        "hierarchy -check -top simple_pipeline; "
        "proc; opt; "
        f"write_json {json_out}"
    )
    return subprocess.run(
        [yosys_bin, "-q", "-p", script],
        capture_output=True,
        text=True,
        check=False,
    )


def rows_from_yosys_json(path: Path, expected_signals: list[str] | None = None) -> list[SourceMapRow]:
    expected = set(expected_signals or EXPECTED_SIGNALS)
    data = json.loads(path.read_text(encoding="utf-8"))
    rows: list[SourceMapRow] = []
    for module_name, module in data.get("modules", {}).items():
        for net_name, net in module.get("netnames", {}).items():
            clean_name = net_name.lstrip("\\")
            if clean_name not in expected:
                continue
            attrs = net.get("attributes", {})
            src = str(attrs.get("src", ""))
            source_file, source_line = parse_src_attribute(src)
            rows.append(
                SourceMapRow(
                    rtl_signal=clean_name,
                    module=module_name.lstrip("\\"),
                    lowered_name=clean_name,
                    source_file=source_file,
                    source_line=source_line,
                    source_attribute=src,
                    available=True,
                    confidence="name+attribute" if src else "name-only",
                    notes="Signal name survived in Yosys JSON netnames.",
                )
            )
    rows.sort(key=lambda row: EXPECTED_SIGNALS.index(row.rtl_signal) if row.rtl_signal in EXPECTED_SIGNALS else 999)
    return rows


def skipped_rows() -> list[SourceMapRow]:
    return [
        SourceMapRow(
            rtl_signal=signal,
            module="simple_pipeline",
            lowered_name="",
            source_file="benchmarks/source_examples/simple_pipeline.v",
            source_line="",
            source_attribute="",
            available=False,
            confidence="skipped",
            notes="Yosys not found on PATH; install Yosys to generate JSON metadata.",
        )
        for signal in EXPECTED_SIGNALS
    ]


def build_source_map(verilog: Path = DEFAULT_VERILOG) -> list[SourceMapRow]:
    yosys_bin = find_yosys()
    if yosys_bin is None:
        return skipped_rows()

    with tempfile.TemporaryDirectory(prefix="source_map_proto_") as tmp_dir:
        json_out = Path(tmp_dir) / "simple_pipeline.json"
        completed = run_yosys_json(yosys_bin, verilog, json_out)
        if completed.returncode != 0 or not json_out.exists():
            snippet = " ".join((completed.stderr or completed.stdout).split())[:240]
            rows = skipped_rows()
            for row in rows:
                row.notes = f"Yosys run failed; source map not produced. {snippet}"
            return rows
        rows = rows_from_yosys_json(json_out)
        if not rows:
            rows = skipped_rows()
            for row in rows:
                row.notes = "Yosys JSON generated, but expected RTL signals were not visible in netnames."
            return rows
        return rows


def write_source_map(rows: list[SourceMapRow], csv_out: Path = CSV_OUT, md_out: Path = MD_OUT) -> None:
    csv_out.parent.mkdir(parents=True, exist_ok=True)
    with csv_out.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=SOURCE_MAP_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow(row.as_row())

    available = sum(1 for row in rows if row.available)
    md = [
        "# Source Map Prototype",
        "",
        "This prototype connects a tiny RTL example to lowered Yosys metadata when Yosys is available.",
        "It is not a general RTL-to-BLIF provenance solution yet.",
        "",
        f"- Rows: `{len(rows)}`",
        f"- Available mappings: `{available}`",
        "",
        "| RTL signal | Module | Lowered name | Source | Confidence | Notes |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        source = row.source_file
        if row.source_line:
            source = f"{source}:{row.source_line}"
        md.append(
            f"| `{row.rtl_signal}` | `{row.module}` | `{row.lowered_name or 'n/a'}` | "
            f"`{source or 'n/a'}` | `{row.confidence}` | {row.notes} |"
        )
    md_out.write_text("\n".join(md) + "\n", encoding="utf-8")


def write_next_steps(path: Path = NEXT_STEPS_OUT) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "# Source Mapping Next Steps",
                "",
                "The current back-mapping pipeline explains optimized BLIF nodes in terms of original BLIF nodes.",
                "The next engineering layer is to attach source metadata to those original nodes:",
                "",
                "```text",
                "optimized path node",
                "  -> original BLIF node",
                "  -> RTL signal / expression / source location",
                "  -> engineer-reviewed register insertion suggestion",
                "```",
                "",
                "Required follow-up work:",
                "",
                "- preserve Yosys `src` attributes and signal names during original BLIF generation;",
                "- relate Yosys JSON netnames/cells to BLIF `.names` outputs;",
                "- propagate mapping confidence from exact signature, SAT/CEC-proven, and approximate layers;",
                "- report source locations on critical-path rows;",
                "- verify any future register insertion with sequential equivalence or an explicit latency contract.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verilog", type=Path, default=DEFAULT_VERILOG)
    parser.add_argument("--csv", type=Path, default=CSV_OUT)
    parser.add_argument("--md", type=Path, default=MD_OUT)
    parser.add_argument("--next-steps", type=Path, default=NEXT_STEPS_OUT)
    args = parser.parse_args()

    rows = build_source_map(args.verilog)
    write_source_map(rows, args.csv, args.md)
    write_next_steps(args.next_steps)
    print(f"Wrote {args.csv}")
    print(f"Wrote {args.md}")
    print(f"Wrote {args.next_steps}")
    print(f"Available mappings: {sum(1 for row in rows if row.available)} / {len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
