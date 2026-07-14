#!/usr/bin/env python3
"""Investigate whether ABC-native FRAIG exposes correspondence provenance.

The goal is deliberately narrower than the sweep baseline: run controlled tiny
circuits and one light real benchmark, then record what survives in the written
BLIF and what ABC prints about merges/equivalence classes.
"""

from __future__ import annotations

import argparse
import csv
import re
import shutil
import sys
import tempfile
import time
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


RESULTS_DIR = ROOT / "results"
PLOTS_DIR = RESULTS_DIR / "plots"
PROVENANCE_CSV = RESULTS_DIR / "abc_provenance_probe.csv"
PROVENANCE_MD = RESULTS_DIR / "abc_provenance_probe.md"
PROVENANCE_PLOT = PLOTS_DIR / "abc_provenance_summary.png"
REAL_C432 = ROOT / "benchmarks" / "external" / "iscas85" / "c432.blif"
TIMEOUT = 30


CONTROLLED_EXAMPLES = {
    "duplicate_and": {
        "expected_nodes": ["n_ab1", "n_ab2"],
        "blif": """.model duplicate_and
.inputs a b c
.outputs y1 y2 y3
.names a b n_ab1
11 1
.names a b n_ab2
11 1
.names n_ab1 y1
1 1
.names n_ab2 y2
1 1
.names a c y3
11 1
.end
""",
        "notes": "Two internal nodes compute the same AND function.",
    },
    "commuted_and": {
        "expected_nodes": ["n_ab", "n_ba"],
        "blif": """.model commuted_and
.inputs a b c
.outputs y1 y2 y3
.names a b n_ab
11 1
.names b a n_ba
11 1
.names n_ab y1
1 1
.names n_ba y2
1 1
.names b c y3
11 1
.end
""",
        "notes": "Two internal nodes compute a commuted AND function.",
    },
    "same_support_nonequiv": {
        "expected_nodes": ["n_and", "n_or"],
        "blif": """.model same_support_nonequiv
.inputs a b c
.outputs y1 y2 y3
.names a b n_and
11 1
.names a b n_or
1- 1
-1 1
.names n_and y1
1 1
.names n_or y2
1 1
.names a c y3
11 1
.end
""",
        "notes": "Same support, but AND and OR are not equivalent.",
    },
}


@dataclass
class ProvenanceRow:
    benchmark: str
    source_family: str
    optimization: str
    command_flow: str
    supported: bool
    controlled_example: str
    node_names_survived: bool
    surviving_node_count: int
    expected_node_count: int
    merge_info_visible: bool
    equivalence_classes_exposed: bool
    node_count_before: int | None
    node_count_after: int | None
    level_count_before: int | None
    level_count_after: int | None
    runtime_seconds: float
    swept_blif_path: str
    stdout_stderr_snippet: str
    notes: str


def controlled_blif_text(example: str) -> str:
    if example not in CONTROLLED_EXAMPLES:
        raise KeyError(f"unknown controlled example: {example}")
    return CONTROLLED_EXAMPLES[example]["blif"]


def expected_nodes(example: str) -> list[str]:
    if example not in CONTROLLED_EXAMPLES:
        raise KeyError(f"unknown controlled example: {example}")
    return list(CONTROLLED_EXAMPLES[example]["expected_nodes"])


def parse_blif_defined_names(text: str) -> list[str]:
    names: list[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line.startswith(".names "):
            continue
        parts = line.split()
        if len(parts) >= 2:
            names.append(parts[-1])
    return names


def detect_node_survival(expected: list[str], swept_blif_text: str) -> tuple[bool, list[str]]:
    defined = set(parse_blif_defined_names(swept_blif_text))
    survived = [name for name in expected if name in defined]
    return bool(survived), survived


def parse_ps_metrics(text: str) -> list[tuple[int, int]]:
    metrics: list[tuple[int, int]] = []
    pattern = re.compile(r"\band\s*=\s*(\d+).*?\blev\s*=\s*(\d+)", re.IGNORECASE)
    for match in pattern.finditer(text):
        metrics.append((int(match.group(1)), int(match.group(2))))
    return metrics


def strip_abc_command_history(output: str) -> str:
    lines = output.splitlines()
    cleaned: list[str] = []
    skipping = False
    for line in lines:
        if "Command history" in line:
            skipping = True
            continue
        if skipping and set(line.strip()) <= {"="} and line.strip():
            skipping = False
            continue
        if not skipping:
            cleaned.append(line)
    return "\n".join(cleaned)


def analyze_output_features(output: str) -> tuple[bool, bool]:
    output = strip_abc_command_history(output)
    lowered = output.lower()
    merge_markers = [
        "merged",
        "merging",
        "merge class",
        "merged into",
        "merged nodes",
    ]
    class_patterns = [
        r"\bequivalence\s+class",
        r"\bequiv(?:alent)?\s+class",
        r"\bclass\s+\d+",
        r"(?m)^\d+:[^:\s]+:",
    ]
    merge_info_visible = any(marker in lowered for marker in merge_markers)
    equivalence_classes_exposed = any(
        re.search(pattern, lowered) for pattern in class_patterns
    )
    return merge_info_visible, equivalence_classes_exposed


def relative_or_placeholder(path: Path | str) -> str:
    if not path:
        return ""
    candidate = Path(path)
    try:
        return candidate.resolve().relative_to(ROOT).as_posix()
    except (OSError, ValueError):
        return "<tmp>"


def write_text_file(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def run_abc_to_sweep(
    abc_bin: str,
    source_blif: Path,
    swept_blif: Path,
    flow: str,
) -> tuple[int | None, str, float]:
    flow_commands = {
        "fraig": f"read_blif {source_blif}\nstrash\nps\nfraig\nwrite_blif {swept_blif}\nps\n",
        "amp_fraig_x": (
            f"read_blif {source_blif}\nstrash\nps\n&get -n\n&fraig -x\n&put\n"
            f"write_blif {swept_blif}\nps\n"
        ),
    }
    start = time.perf_counter()
    exit_code, output = run_abc_script(abc_bin, flow_commands[flow], timeout=TIMEOUT)
    return exit_code, output, time.perf_counter() - start


def build_row(
    *,
    benchmark: str,
    source_family: str,
    optimization: str,
    command_flow: str,
    controlled_example: str,
    expected: list[str],
    exit_code: int | None,
    output: str,
    runtime_seconds: float,
    swept_blif: Path,
    base_notes: str,
) -> ProvenanceRow:
    supported = command_supported(exit_code, output) and swept_blif.exists()
    swept_text = swept_blif.read_text(encoding="utf-8") if swept_blif.exists() else ""
    survived, surviving = detect_node_survival(expected, swept_text)
    metrics = parse_ps_metrics(output)
    before = metrics[0] if metrics else (None, None)
    after = metrics[-1] if len(metrics) >= 2 else (None, None)
    merge_visible, classes_visible = analyze_output_features(output)
    notes = [base_notes]
    if supported:
        if surviving:
            notes.append(f"surviving names: {', '.join(surviving)}")
        else:
            notes.append("expected internal node names did not survive in written BLIF")
    else:
        notes.append("flow unsupported or failed")
    if merge_visible and not classes_visible:
        notes.append("stdout mentions FRAIG/equivalence concepts but not explicit classes")
    if not merge_visible:
        notes.append("no visible merge/provenance details in stdout")
    return ProvenanceRow(
        benchmark=benchmark,
        source_family=source_family,
        optimization=optimization,
        command_flow=command_flow,
        supported=supported,
        controlled_example=controlled_example,
        node_names_survived=survived,
        surviving_node_count=len(surviving),
        expected_node_count=len(expected),
        merge_info_visible=merge_visible,
        equivalence_classes_exposed=classes_visible,
        node_count_before=before[0],
        node_count_after=after[0],
        level_count_before=before[1],
        level_count_after=after[1],
        runtime_seconds=round(runtime_seconds, 4),
        swept_blif_path=relative_or_placeholder(swept_blif) if swept_blif.exists() else "",
        stdout_stderr_snippet=short_snippet(strip_abc_command_history(output), 700),
        notes="; ".join(notes),
    )


def capability_probe_rows(abc_bin: str, tmp: Path) -> list[ProvenanceRow]:
    toy = tmp / "capability.blif"
    write_text_file(toy, controlled_blif_text("duplicate_and"))
    dump_path = tmp / "equiv.txt"
    commands = {
        "fraig -x": f"read_blif {toy}\nstrash\nfraig -x\nps\n",
        "fraig -y": f"read_blif {toy}\nstrash\nfraig -y\nps\n",
        "print_fanio": f"read_blif {toy}\nstrash\nprint_fanio\n",
        "print_factor": f"read_blif {toy}\nstrash\nprint_factor\n",
        "print_gates": f"read_blif {toy}\nstrash\nprint_gates\n",
        "choice": f"read_blif {toy}\nstrash\nchoice\nps\n",
        "dump_equiv_self": f"dump_equiv {toy} {toy} {dump_path}\n",
        "cec_self": f"cec {toy} {toy}\n",
    }
    rows: list[ProvenanceRow] = []
    for command, script in commands.items():
        start = time.perf_counter()
        exit_code, output = run_abc_script(abc_bin, script, timeout=TIMEOUT)
        runtime = time.perf_counter() - start
        dump_text = dump_path.read_text(encoding="utf-8") if dump_path.exists() else ""
        combined = strip_abc_command_history(output) + "\n" + dump_text
        supported = command_supported(exit_code, output)
        if command == "dump_equiv_self" and supported:
            supported = dump_path.exists()
        merge_visible, classes_visible = analyze_output_features(combined)
        if not supported:
            merge_visible = False
            classes_visible = False
        note = "capability probe for provenance-oriented command"
        if dump_text:
            note += "; dump file was created"
        elif command == "dump_equiv_self":
            note += "; no dump file was created"
        if looks_unsupported(output):
            note += "; ABC reported unsupported command or option"
        rows.append(
            ProvenanceRow(
                benchmark="controlled_probe",
                source_family="controlled",
                optimization="none",
                command_flow=command,
                supported=supported,
                controlled_example="capability_probe",
                node_names_survived=False,
                surviving_node_count=0,
                expected_node_count=0,
                merge_info_visible=merge_visible,
                equivalence_classes_exposed=classes_visible,
                node_count_before=None,
                node_count_after=None,
                level_count_before=None,
                level_count_after=None,
                runtime_seconds=round(runtime, 4),
                swept_blif_path="",
                stdout_stderr_snippet=short_snippet(combined, 700),
                notes=note,
            )
        )
        if dump_path.exists():
            dump_path.unlink()
    return rows


def real_c432_row(abc_bin: str, tmp: Path, flow: str) -> ProvenanceRow | None:
    if not REAL_C432.exists():
        return None
    optimized = tmp / "external_iscas85_c432_rewrite.blif"
    script = f"read_blif {REAL_C432}\nstrash\nrewrite\nwrite_blif {optimized}\n"
    exit_code, output = run_abc_script(abc_bin, script, timeout=TIMEOUT)
    if exit_code != 0 or not optimized.exists():
        return ProvenanceRow(
            benchmark="external_iscas85_c432",
            source_family="iscas85",
            optimization="rewrite",
            command_flow=flow,
            supported=False,
            controlled_example="real_benchmark",
            node_names_survived=False,
            surviving_node_count=0,
            expected_node_count=0,
            merge_info_visible=False,
            equivalence_classes_exposed=False,
            node_count_before=None,
            node_count_after=None,
            level_count_before=None,
            level_count_after=None,
            runtime_seconds=0.0,
            swept_blif_path="",
            stdout_stderr_snippet=short_snippet(output, 700),
            notes="could not create c432 rewrite input for provenance probe",
        )
    before_text = optimized.read_text(encoding="utf-8")
    expected = [
        name
        for name in parse_blif_defined_names(before_text)
        if not name.startswith("po")
    ][:50]
    swept = tmp / f"external_iscas85_c432_rewrite_{flow}.blif"
    exit_code, output, runtime = run_abc_to_sweep(abc_bin, optimized, swept, flow)
    return build_row(
        benchmark="external_iscas85_c432",
        source_family="iscas85",
        optimization="rewrite",
        command_flow=flow,
        controlled_example="real_benchmark",
        expected=expected,
        exit_code=exit_code,
        output=output,
        runtime_seconds=runtime,
        swept_blif=swept,
        base_notes="Light real benchmark probe; sampled first 50 optimized internal names.",
    )


def run_investigation(abc_bin: str) -> list[ProvenanceRow]:
    rows: list[ProvenanceRow] = []
    with tempfile.TemporaryDirectory(prefix="abc_provenance_") as td:
        tmp = Path(td)
        rows.extend(capability_probe_rows(abc_bin, tmp))
        for example, meta in CONTROLLED_EXAMPLES.items():
            source = tmp / f"{example}.blif"
            write_text_file(source, controlled_blif_text(example))
            for flow in ["fraig", "amp_fraig_x"]:
                swept = tmp / f"{example}_{flow}.blif"
                exit_code, output, runtime = run_abc_to_sweep(abc_bin, source, swept, flow)
                rows.append(
                    build_row(
                        benchmark=example,
                        source_family="controlled",
                        optimization="none",
                        command_flow=flow,
                        controlled_example=example,
                        expected=expected_nodes(example),
                        exit_code=exit_code,
                        output=output,
                        runtime_seconds=runtime,
                        swept_blif=swept,
                        base_notes=str(meta["notes"]),
                    )
                )
        for flow in ["fraig", "amp_fraig_x"]:
            row = real_c432_row(abc_bin, tmp, flow)
            if row is not None:
                rows.append(row)
    return rows


def write_csv(rows: list[ProvenanceRow], path: Path = PROVENANCE_CSV) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(asdict(rows[0]).keys()) if rows else list(ProvenanceRow.__annotations__)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))


def write_markdown(rows: list[ProvenanceRow], abc_bin: str, path: Path = PROVENANCE_MD) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    supported = sorted({row.command_flow for row in rows if row.supported})
    unsupported = sorted({row.command_flow for row in rows if not row.supported})
    explicit_classes = [row for row in rows if row.equivalence_classes_exposed]
    survived = [row for row in rows if row.node_names_survived]
    reductions = [
        row
        for row in rows
        if row.node_count_before is not None
        and row.node_count_after is not None
        and row.node_count_after < row.node_count_before
    ]
    lines = [
        "# ABC Provenance Investigation",
        "",
        f"ABC binary: `{relative_or_placeholder(Path(abc_bin))}`",
        "",
        "This probe asks a narrow question: does the local ABC build expose old-to-new",
        "node provenance or equivalence classes through ordinary FRAIG/sweeping commands?",
        "",
        "## Summary",
        "",
        f"- Supported investigated flows/commands: {', '.join(f'`{name}`' for name in supported) or 'none'}",
        f"- Unsupported or failed flows/commands: {', '.join(f'`{name}`' for name in unsupported) or 'none'}",
        f"- Rows with any sampled internal node names surviving in written BLIF: {len(survived)} / {len(rows)}",
        f"- Rows that visibly exposed equivalence classes/provenance: {len(explicit_classes)} / {len(rows)}",
        f"- Rows where FRAIG reduced the measured network: {len(reductions)}",
        "",
        "## Controlled examples",
        "",
        "| Example | Flow | Supported | Nodes before -> after | Names survived | Merge info visible | Equiv classes exposed | Notes |",
        "|---|---|---:|---:|---:|---:|---:|---|",
    ]
    for row in rows:
        if row.controlled_example in {"capability_probe", "real_benchmark"}:
            continue
        before_after = ""
        if row.node_count_before is not None and row.node_count_after is not None:
            before_after = f"{row.node_count_before} -> {row.node_count_after}"
        notes = row.notes.replace("|", "\\|")
        lines.append(
            f"| `{row.controlled_example}` | `{row.command_flow}` | {str(row.supported).lower()} | "
            f"{before_after} | {row.surviving_node_count}/{row.expected_node_count} | "
            f"{str(row.merge_info_visible).lower()} | {str(row.equivalence_classes_exposed).lower()} | {notes} |"
        )
    lines.extend(
        [
            "",
            "## Real benchmark sample",
            "",
            "| Benchmark | Optimization | Flow | Supported | Nodes before -> after | Names survived | Equiv classes exposed | Notes |",
            "|---|---|---|---:|---:|---:|---:|---|",
        ]
    )
    for row in rows:
        if row.controlled_example != "real_benchmark":
            continue
        before_after = ""
        if row.node_count_before is not None and row.node_count_after is not None:
            before_after = f"{row.node_count_before} -> {row.node_count_after}"
        notes = row.notes.replace("|", "\\|")
        lines.append(
            f"| `{row.benchmark}` | `{row.optimization}` | `{row.command_flow}` | "
            f"{str(row.supported).lower()} | {before_after} | "
            f"{row.surviving_node_count}/{row.expected_node_count} | "
            f"{str(row.equivalence_classes_exposed).lower()} | {notes} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "ABC-native FRAIG remains useful as a standard reduction baseline, but these",
            "ordinary command outputs do not provide the explicit old-node to new-node",
            "mapping needed by the critical-path back-mapping prototype. Written BLIFs may",
            "preserve some primary-output names, but internal provenance is not a reliable",
            "correspondence interface.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def write_plot(rows: list[ProvenanceRow], path: Path = PROVENANCE_PLOT) -> Path | None:
    try:
        from PIL import Image, ImageDraw, ImageFont
    except Exception:  # pragma: no cover - exercised only on minimal environments.
        return None
    path.parent.mkdir(parents=True, exist_ok=True)
    width, height = 1100, 620
    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)
    try:
        title_font = ImageFont.truetype("Arial.ttf", 32)
        label_font = ImageFont.truetype("Arial.ttf", 20)
        small_font = ImageFont.truetype("Arial.ttf", 17)
    except Exception:
        title_font = label_font = small_font = None

    controlled = [row for row in rows if row.controlled_example not in {"capability_probe"}]
    total = max(len(controlled), 1)
    metrics = [
        ("FRAIG flow supported", sum(row.supported for row in controlled), "#4C78A8"),
        ("Node names survived", sum(row.node_names_survived for row in controlled), "#F58518"),
        ("Merge info visible", sum(row.merge_info_visible for row in controlled), "#54A24B"),
        ("Equiv classes exposed", sum(row.equivalence_classes_exposed for row in controlled), "#E45756"),
    ]
    draw.text((42, 34), "ABC provenance probe summary", fill="#1f2933", font=title_font)
    draw.text(
        (42, 82),
        "Ordinary FRAIG reduces networks, but does not expose a robust correspondence map.",
        fill="#52606d",
        font=label_font,
    )
    x0, y0 = 340, 170
    bar_max = 620
    for idx, (label, count, color) in enumerate(metrics):
        y = y0 + idx * 92
        draw.text((42, y + 8), label, fill="#243b53", font=label_font)
        draw.rectangle((x0, y, x0 + bar_max, y + 42), outline="#d9e2ec", width=2)
        fill_w = int(bar_max * count / total)
        draw.rectangle((x0, y, x0 + fill_w, y + 42), fill=color)
        draw.text((x0 + bar_max + 20, y + 8), f"{count}/{total}", fill="#102a43", font=label_font)
    draw.text(
        (42, 555),
        "Rows counted here exclude command-only capability probes; real c432/rewrite rows are included.",
        fill="#627d98",
        font=small_font,
    )
    img.save(path)
    return path


def copy_plot_to_presentation(path: Path) -> Path | None:
    if not path.exists():
        return None
    target = ROOT / "docs" / "presentation" / "assets" / "plots" / path.name
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(path, target)
    return target


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--abc", help="Path to ABC binary. Defaults to $ABC or .abc_build/abc_repo/abc.")
    args = parser.parse_args(argv)

    abc_bin = find_abc(args.abc)
    rows = run_investigation(abc_bin)
    write_csv(rows)
    write_markdown(rows, abc_bin)
    plot = write_plot(rows)
    copied = copy_plot_to_presentation(plot) if plot else None

    print(f"Wrote {PROVENANCE_CSV.relative_to(ROOT)}")
    print(f"Wrote {PROVENANCE_MD.relative_to(ROOT)}")
    if plot:
        print(f"Wrote {plot.relative_to(ROOT)}")
    if copied:
        print(f"Copied {copied.relative_to(ROOT)}")
    exposed = sum(row.equivalence_classes_exposed for row in rows)
    survived = sum(row.node_names_survived for row in rows)
    print(f"Equivalence-class/provenance rows: {exposed}/{len(rows)}")
    print(f"Node-name survival rows: {survived}/{len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
