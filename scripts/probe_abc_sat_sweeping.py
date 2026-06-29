#!/usr/bin/env python3
"""Probe ABC support for SAT sweeping / FRAIG-related commands."""

from __future__ import annotations

import argparse
import csv
import os
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, asdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ABC = ROOT / ".abc_build" / "abc_repo" / "abc"
RESULTS_DIR = ROOT / "results"
CAPABILITY_CSV = RESULTS_DIR / "abc_sat_sweeping_capabilities.csv"
CAPABILITY_MD = RESULTS_DIR / "abc_sat_sweeping_capabilities.md"
TIMEOUT = 20


TOY_BLIF = """.model probe
.inputs a b c
.outputs y
.names a b n1
11 1
.names n1 c y
1- 1
-1 1
.end
"""


@dataclass
class ProbeResult:
    command: str
    supported: bool
    exit_code: int | None
    stdout_stderr_snippet: str


def find_abc(hint: str | None = None) -> str:
    candidates = [
        hint or "",
        os.environ.get("ABC", ""),
        str(DEFAULT_ABC),
        shutil.which("abc") or "",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).is_file() and os.access(candidate, os.X_OK):
            return candidate
    raise FileNotFoundError(
        f"ABC binary not found. Set ABC or build {DEFAULT_ABC.relative_to(ROOT)}."
    )


def short_snippet(text: str, limit: int = 500) -> str:
    text = text.replace(str(ROOT), "<repo>")
    text = re.sub(r"/private" + r"/var/\S+", "<tmp>", text)
    text = re.sub(r"/var" + r"/folders/\S+", "<tmp>", text)
    text = re.sub(r"\x1b\[[0-9;]*m", "", text)
    compact = re.sub(r"\s+", " ", text).strip()
    return compact[:limit]


def looks_unsupported(text: str) -> bool:
    lowered = text.lower()
    markers = [
        "unknown command",
        "unknown option",
        "invalid option",
        "usage:",
        "command cannot be found",
        "abc command line parser",
        "error:",
    ]
    return any(marker in lowered for marker in markers)


def run_abc_script(abc_bin: str, script: str, timeout: int = TIMEOUT) -> tuple[int | None, str]:
    try:
        proc = subprocess.run(
            [abc_bin],
            input=script,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return proc.returncode, proc.stdout + proc.stderr
    except subprocess.TimeoutExpired as exc:
        return None, (exc.stdout or "") + (exc.stderr or "") + f"\nTIMEOUT after {timeout}s"
    except OSError as exc:
        return None, f"subprocess error: {exc}"


def command_supported(exit_code: int | None, output: str, required_pattern: str | None = None) -> bool:
    if exit_code not in (0, None) or looks_unsupported(output):
        return False
    if required_pattern and re.search(required_pattern, output, re.IGNORECASE) is None:
        return False
    return exit_code == 0


def probe_commands(abc_bin: str) -> list[ProbeResult]:
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        toy = tmp / "probe.blif"
        swept = tmp / "swept.blif"
        toy.write_text(TOY_BLIF, encoding="utf-8")

        scripts = {
            "fraig": f"read_blif {toy}\nstrash\nfraig\nps\n",
            "fraig -x": f"read_blif {toy}\nstrash\nfraig -x\nps\n",
            "fraig -y": f"read_blif {toy}\nstrash\nfraig -y\nps\n",
            "&get": f"read_blif {toy}\nstrash\n&get -n\n",
            "&fraig -x": f"read_blif {toy}\nstrash\n&get -n\n&fraig -x\n&put\nps\n",
            "cec": f"cec {toy} {toy}\n",
            "print_stats": f"read_blif {toy}\nstrash\nprint_stats\n",
            "ps": f"read_blif {toy}\nstrash\nps\n",
            "write_blif": f"read_blif {toy}\nstrash\nwrite_blif {swept}\n",
        }

        results: list[ProbeResult] = []
        for command, script in scripts.items():
            exit_code, output = run_abc_script(abc_bin, script)
            required = r"(and\s*=|lev\s*=)" if command in {"print_stats", "ps"} else None
            if command == "cec":
                required = r"(equivalent|not equivalent|cec)"
            supported = command_supported(exit_code, output, required)
            if command == "write_blif" and supported:
                supported = swept.exists()
            results.append(
                ProbeResult(
                    command=command,
                    supported=supported,
                    exit_code=exit_code,
                    stdout_stderr_snippet=short_snippet(output),
                )
            )
        return results


def write_csv(results: list[ProbeResult], path: Path = CAPABILITY_CSV) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=["command", "supported", "exit_code", "stdout_stderr_snippet"],
        )
        writer.writeheader()
        for result in results:
            writer.writerow(asdict(result))


def write_markdown(results: list[ProbeResult], abc_bin: str, path: Path = CAPABILITY_MD) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    abc_display = Path(abc_bin)
    try:
        abc_text = abc_display.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        abc_text = "<external-abc>"
    lines = [
        "# ABC SAT Sweeping Capability Probe",
        "",
        f"ABC binary: `{abc_text}`",
        "",
        "| Command | Supported | Exit code | Snippet |",
        "|---|---:|---:|---|",
    ]
    for result in results:
        snippet = result.stdout_stderr_snippet.replace("|", "\\|")
        lines.append(
            f"| `{result.command}` | {str(result.supported).lower()} | "
            f"{'' if result.exit_code is None else result.exit_code} | {snippet} |"
        )
    lines.extend(
        [
            "",
            "Interpretation: this is a command-level probe only. A supported command may still",
            "produce little useful correspondence data unless ABC exposes the relevant merge",
            "classes or statistics in stdout.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--abc", help="Path to ABC binary. Defaults to $ABC or .abc_build/abc_repo/abc.")
    args = parser.parse_args(argv)

    abc_bin = find_abc(args.abc)
    results = probe_commands(abc_bin)
    write_csv(results)
    write_markdown(results, abc_bin)

    print(f"Wrote {CAPABILITY_CSV.relative_to(ROOT)}")
    print(f"Wrote {CAPABILITY_MD.relative_to(ROOT)}")
    for result in results:
        print(f"{result.command:12s} supported={result.supported}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
