#!/usr/bin/env python3
"""Probe local ABC support for timing/path-related commands."""

from __future__ import annotations

import argparse
import csv
import sys
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from probe_abc_sat_sweeping import (  # noqa: E402
    command_supported,
    find_abc,
    looks_unsupported,
    run_abc_script,
    short_snippet,
)


RESULTS = ROOT / "results"
PROBE_CSV = RESULTS / "abc_timing_command_probe.csv"
PROBE_MD = RESULTS / "abc_timing_command_probe.md"

TOY_BLIF = """.model timing_probe
.inputs a b c
.outputs y
.names a b n1
11 1
.names n1 c y
11 1
.end
"""

GENLIB = """GATE inv 1 O=!a; PIN * INV 1 999 1 0 1 0
GATE and2 1 O=a*b; PIN * NONINV 1 999 1 0 1 0
GATE nand2 1 O=!(a*b); PIN * INV 1 999 1 0 1 0
GATE or2 1 O=a+b; PIN * NONINV 1 999 1 0 1 0
GATE nor2 1 O=!(a+b); PIN * INV 1 999 1 0 1 0
"""


@dataclass
class TimingProbeRow:
    command: str
    supported: bool
    exit_code: int | None
    timing_related_output: bool
    stdout_stderr_snippet: str


def has_timing_related_output(output: str) -> bool:
    lowered = output.lower()
    markers = [
        "lev",
        "level",
        "delay",
        "arrival",
        "required",
        "slack",
        "fanin",
        "fanout",
        "mapped",
        "topological",
    ]
    return any(marker in lowered for marker in markers)


def probe_timing_commands(abc_bin: str) -> list[TimingProbeRow]:
    with tempfile.TemporaryDirectory(prefix="abc_timing_probe_") as td:
        tmp = Path(td)
        toy = tmp / "timing_probe.blif"
        genlib = tmp / "tiny.genlib"
        toy.write_text(TOY_BLIF, encoding="utf-8")
        genlib.write_text(GENLIB, encoding="utf-8")

        scripts = {
            "ps": f"read_blif {toy}\nstrash\nps\n",
            "print_stats": f"read_blif {toy}\nstrash\nprint_stats\n",
            "print_level": f"read_blif {toy}\nstrash\nprint_level\n",
            "print_fanio": f"read_blif {toy}\nstrash\nprint_fanio\n",
            "topo": f"read_blif {toy}\nstrash\ntopo\nps\n",
            "stime": f"read_blif {toy}\nstrash\nstime\n",
            "print_delay": f"read_blif {toy}\nstrash\nprint_delay\n",
            "read_library": f"read_blif {toy}\nread_library {genlib}\nstrash\nmap\nps\n",
            "read_lib": f"read_blif {toy}\nread_lib {genlib}\nstrash\nmap\nps\n",
            "map_without_library": f"read_blif {toy}\nstrash\nmap\nps\n",
        }

        rows: list[TimingProbeRow] = []
        for command, script in scripts.items():
            exit_code, output = run_abc_script(abc_bin, script, timeout=25)
            required = None
            if command in {"ps", "print_stats", "topo", "map_without_library", "read_library", "read_lib"}:
                required = r"(lev\s*=|level|delay|mapped|and\s*=|nd\s*=)"
            supported = command_supported(exit_code, output, required)
            if looks_unsupported(output):
                supported = False
            rows.append(
                TimingProbeRow(
                    command=command,
                    supported=supported,
                    exit_code=exit_code,
                    timing_related_output=has_timing_related_output(output),
                    stdout_stderr_snippet=short_snippet(output, 700),
                )
            )
        return rows


def write_csv(rows: list[TimingProbeRow], path: Path = PROBE_CSV) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(TimingProbeRow.__annotations__))
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))


def write_markdown(rows: list[TimingProbeRow], abc_bin: str, path: Path = PROBE_MD) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        abc_text = Path(abc_bin).resolve().relative_to(ROOT).as_posix()
    except ValueError:
        abc_text = "<external-abc>"
    supported = [row.command for row in rows if row.supported]
    unsupported = [row.command for row in rows if not row.supported]
    lines = [
        "# ABC Timing Command Probe",
        "",
        f"ABC binary: `{abc_text}`",
        "",
        f"- Supported commands/flows: {', '.join(f'`{cmd}`' for cmd in supported) or 'none'}",
        f"- Unsupported or failed commands/flows: {', '.join(f'`{cmd}`' for cmd in unsupported) or 'none'}",
        "",
        "| Command | Supported | Exit code | Timing-related output | Snippet |",
        "|---|---:|---:|---:|---|",
    ]
    for row in rows:
        snippet = row.stdout_stderr_snippet.replace("|", "\\|")
        exit_text = "" if row.exit_code is None else str(row.exit_code)
        lines.append(
            f"| `{row.command}` | {str(row.supported).lower()} | {exit_text} | "
            f"{str(row.timing_related_output).lower()} | {snippet} |"
        )
    lines.extend(
        [
            "",
            "Interpretation: this probe records command availability only. A supported",
            "statistics or mapping command does not necessarily expose a real critical",
            "timing path with library delays.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--abc", help="Path to ABC binary. Defaults to $ABC or .abc_build/abc_repo/abc.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    abc_bin = find_abc(args.abc)
    rows = probe_timing_commands(abc_bin)
    write_csv(rows)
    write_markdown(rows, abc_bin)
    print(f"Wrote {PROBE_CSV.relative_to(ROOT)}")
    print(f"Wrote {PROBE_MD.relative_to(ROOT)}")
    for row in rows:
        print(f"{row.command:20s} supported={row.supported}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
