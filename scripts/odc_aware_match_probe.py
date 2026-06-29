#!/usr/bin/env python3
"""Tiny controlled probe for observability-don't-care-aware matching."""

from __future__ import annotations

import argparse
import csv
import re
import sys
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from analyze_blif_matches import parse_blif  # noqa: E402
from scripts.approximate_node_distance import (  # noqa: E402
    evaluate_network_with_values,
    exact_pattern_values,
    hamming_distance_fraction,
)
from scripts.probe_abc_sat_sweeping import find_abc, run_abc_script, short_snippet  # noqa: E402


RESULTS = ROOT / "results"
PLOTS = RESULTS / "plots"
ODC_CSV = RESULTS / "odc_probe_results.csv"
ODC_MD = RESULTS / "odc_probe_results.md"
ODC_PLOT = PLOTS / "odc_probe_summary.png"


CONTROLLED_ODC_EXAMPLES = {
    "masked_and_or": {
        "description": "f=AND and g=OR differ globally, but f is observed only through a constant-zero mask.",
        "candidate_f": "f_and",
        "candidate_g": "g_or",
        "original": """.model masked_and_or
.inputs a b
.outputs y
.names a b f_and
11 1
.names a b g_or
1- 1
-1 1
.names zero
.names f_and zero y
11 1
.end
""",
        "modified": """.model masked_and_or
.inputs a b
.outputs y
.names a b f_and
11 1
.names a b g_or
1- 1
-1 1
.names zero
.names g_or zero y
11 1
.end
""",
        "expected_observable_difference": False,
    },
    "visible_and_or": {
        "description": "f=AND and g=OR differ globally and the output observes the difference.",
        "candidate_f": "f_and",
        "candidate_g": "g_or",
        "original": """.model visible_and_or
.inputs a b
.outputs y
.names a b f_and
11 1
.names a b g_or
1- 1
-1 1
.names f_and y
1 1
.end
""",
        "modified": """.model visible_and_or
.inputs a b
.outputs y
.names a b f_and
11 1
.names a b g_or
1- 1
-1 1
.names g_or y
1 1
.end
""",
        "expected_observable_difference": True,
    },
    "equivalent_commuted_and": {
        "description": "f and g are globally equivalent commuted AND nodes.",
        "candidate_f": "f_ab",
        "candidate_g": "g_ba",
        "original": """.model equivalent_commuted_and
.inputs a b
.outputs y
.names a b f_ab
11 1
.names b a g_ba
11 1
.names f_ab y
1 1
.end
""",
        "modified": """.model equivalent_commuted_and
.inputs a b
.outputs y
.names a b f_ab
11 1
.names b a g_ba
11 1
.names g_ba y
1 1
.end
""",
        "expected_observable_difference": False,
    },
}


@dataclass
class OdcProbeRow:
    example_name: str
    candidate_f: str
    candidate_g: str
    global_distance: float
    output_observable_difference: bool
    abc_supported: bool
    abc_result: str
    interpretation: str
    stdout_stderr_snippet: str


def controlled_example_names() -> list[str]:
    return list(CONTROLLED_ODC_EXAMPLES)


def controlled_blif_pair(example_name: str) -> tuple[str, str]:
    meta = CONTROLLED_ODC_EXAMPLES[example_name]
    return str(meta["original"]), str(meta["modified"])


def compute_global_distance(blif_text: str, candidate_f: str, candidate_g: str, tmp: Path) -> float:
    path = tmp / "distance.blif"
    path.write_text(blif_text, encoding="utf-8")
    net = parse_blif(path)
    values, mask, pattern_count = exact_pattern_values(net.inputs, set(net.inputs))
    evaluated = evaluate_network_with_values(path, values, mask)
    return hamming_distance_fraction(
        evaluated[candidate_f].value,
        evaluated[candidate_g].value,
        pattern_count,
    )


def parse_cec_observable_difference(output: str) -> tuple[bool, bool, str]:
    lowered = output.lower()
    if "networks are equivalent" in lowered or "equivalent after" in lowered:
        return True, False, "equivalent"
    if re.search(r"not equivalent|are not equivalent|cex|counter-example", lowered):
        return True, True, "not_equivalent"
    return False, False, "unknown"


def run_cec(abc_bin: str, original: Path, modified: Path) -> tuple[bool, bool, str, str]:
    exit_code, output = run_abc_script(abc_bin, f"cec {original} {modified}\n", timeout=20)
    parsed, observable_difference, result = parse_cec_observable_difference(output)
    supported = exit_code == 0 and parsed
    return supported, observable_difference, result, output


def interpretation_for(global_distance: float, observable_difference: bool, abc_supported: bool) -> str:
    if not abc_supported:
        return "ABC CEC did not produce a parseable result for this controlled example."
    if global_distance > 0 and not observable_difference:
        return "Nodes differ globally, but the replacement is not observable at primary outputs in this context."
    if global_distance > 0 and observable_difference:
        return "Nodes differ globally and the difference is observable at primary outputs."
    return "Nodes are globally equivalent; output equivalence is expected."


def run_probe(abc_bin: str) -> list[OdcProbeRow]:
    rows: list[OdcProbeRow] = []
    with tempfile.TemporaryDirectory(prefix="odc_probe_") as td:
        tmp = Path(td)
        for name, meta in CONTROLLED_ODC_EXAMPLES.items():
            original_text, modified_text = controlled_blif_pair(name)
            original_path = tmp / f"{name}_original.blif"
            modified_path = tmp / f"{name}_modified.blif"
            original_path.write_text(original_text, encoding="utf-8")
            modified_path.write_text(modified_text, encoding="utf-8")
            candidate_f = str(meta["candidate_f"])
            candidate_g = str(meta["candidate_g"])
            global_distance = compute_global_distance(original_text, candidate_f, candidate_g, tmp)
            supported, observable_difference, abc_result, output = run_cec(
                abc_bin, original_path, modified_path
            )
            rows.append(
                OdcProbeRow(
                    example_name=name,
                    candidate_f=candidate_f,
                    candidate_g=candidate_g,
                    global_distance=global_distance,
                    output_observable_difference=observable_difference,
                    abc_supported=supported,
                    abc_result=abc_result,
                    interpretation=interpretation_for(
                        global_distance, observable_difference, supported
                    ),
                    stdout_stderr_snippet=short_snippet(output, 600),
                )
            )
    return rows


def write_csv(rows: list[OdcProbeRow], path: Path = ODC_CSV) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(OdcProbeRow.__annotations__))
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))


def write_markdown(rows: list[OdcProbeRow], path: Path = ODC_MD) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# ODC-Aware Matching Probe",
        "",
        "This controlled probe asks whether replacing an internal node candidate changes",
        "the primary outputs. It is a small direction-setting experiment, not a general",
        "ODC correspondence engine.",
        "",
        "| Example | Global distance | Output observable difference | ABC result | Interpretation |",
        "|---|---:|---:|---|---|",
    ]
    for row in rows:
        interpretation = row.interpretation.replace("|", "\\|")
        lines.append(
            f"| `{row.example_name}` | {row.global_distance:.4f} | "
            f"{str(row.output_observable_difference).lower()} | `{row.abc_result}` | "
            f"{interpretation} |"
        )
    lines.extend(
        [
            "",
            "Interpretation: global internal-node distance can be too strict when a",
            "difference is hidden by circuit context. The current implementation only",
            "builds controlled original/modified BLIF pairs; general substitution inside",
            "arbitrary optimized networks remains future work.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def write_plot(rows: list[OdcProbeRow], path: Path = ODC_PLOT) -> None:
    if not rows:
        return
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    path.parent.mkdir(parents=True, exist_ok=True)
    labels = [row.example_name.replace("_", "\n") for row in rows]
    distances = [row.global_distance for row in rows]
    observable = [1 if row.output_observable_difference else 0 for row in rows]
    x = range(len(rows))
    fig, ax1 = plt.subplots(figsize=(7.2, 4.5))
    ax1.bar(x, distances, color="#4C78A8", alpha=0.8, label="global distance")
    ax1.set_ylabel("global distance")
    ax1.set_ylim(0, max(0.6, max(distances) + 0.1))
    ax1.set_xticks(list(x))
    ax1.set_xticklabels(labels)
    ax2 = ax1.twinx()
    ax2.plot(list(x), observable, color="#E45756", marker="o", linewidth=2, label="observable")
    ax2.set_ylim(-0.05, 1.05)
    ax2.set_ylabel("observable output difference")
    ax1.set_title("ODC Probe: Global Difference vs Output Observability")
    ax1.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    plt.savefig(path, dpi=180)
    plt.close()


def copy_plot_to_presentation() -> None:
    if not ODC_PLOT.exists():
        return
    target = ROOT / "docs" / "presentation" / "assets" / "plots" / ODC_PLOT.name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(ODC_PLOT.read_bytes())


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--abc", help="Path to ABC binary. Defaults to $ABC or .abc_build/abc_repo/abc.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    abc_bin = find_abc(args.abc)
    rows = run_probe(abc_bin)
    write_csv(rows)
    write_markdown(rows)
    write_plot(rows)
    copy_plot_to_presentation()
    print(f"Wrote {ODC_CSV.relative_to(ROOT)}")
    print(f"Wrote {ODC_MD.relative_to(ROOT)}")
    if ODC_PLOT.exists():
        print(f"Wrote {ODC_PLOT.relative_to(ROOT)}")
    hidden = [
        row.example_name
        for row in rows
        if row.global_distance > 0 and not row.output_observable_difference
    ]
    print(f"Globally different but output-hidden examples: {', '.join(hidden) or 'none'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
