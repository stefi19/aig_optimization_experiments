#!/usr/bin/env python3
"""Run an exploratory ABC-native SAT sweeping / FRAIG baseline."""

from __future__ import annotations

import argparse
import csv
import os
import re
import shutil
import subprocess
import time
from dataclasses import dataclass, asdict
from pathlib import Path

try:
    from scripts.benchmark_id import infer_source_family
except ModuleNotFoundError:
    from benchmark_id import infer_source_family

try:
    from scripts.probe_abc_sat_sweeping import find_abc, run_abc_script, short_snippet
except ModuleNotFoundError:
    from probe_abc_sat_sweeping import find_abc, run_abc_script, short_snippet


ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "results"
VARIANTS_DIR = ROOT / "variants"
SWEEP_DIR = RESULTS_DIR / "abc_native_swept"
INPUT_DIR = RESULTS_DIR / "abc_native_inputs"
PLOTS_DIR = RESULTS_DIR / "plots"
BASELINE_CSV = RESULTS_DIR / "abc_native_sweep_baseline.csv"
BASELINE_MD = RESULTS_DIR / "abc_native_sweep_baseline.md"

DEFAULT_BENCHMARKS = [
    "external_iscas85_c432",
    "external_iscas85_c2670",
    "external_iscas85_c6288",
    "majority3",
    "mux2",
    "toy_and_or",
    "generated_mux_tree_8",
    "generated_multiplier_2",
]
DEFAULT_OPTIMIZATIONS = ["original", "balance", "rewrite", "resyn2"]
FULL_OPTIMIZATIONS = [
    "original", "balance", "rewrite", "rewrite_z", "refactor", "refactor_z",
    "resub", "resyn", "resyn2", "resyn2_like", "compress2rs", "dc2",
]

OPT_COMMANDS = {
    "original": "strash",
    "balance": "strash; balance",
    "rewrite": "strash; rewrite",
    "rewrite_z": "strash; rewrite -z",
    "refactor": "strash; refactor",
    "refactor_z": "strash; refactor -z",
    "resub": "strash; resub",
    "resyn": "strash; balance; rewrite; refactor; balance",
    "resyn2": "strash; balance; rewrite; refactor; balance; rewrite; rewrite -z; balance; refactor -z; rewrite -z; balance",
    "resyn2_like": "strash; balance; rewrite; refactor; balance; rewrite; rewrite -z; balance; refactor -z; rewrite -z; balance",
    "compress2rs": "strash; balance; rewrite -l; refactor -l; balance; rewrite -l; rewrite -lz; balance; refactor -lz; rewrite -lz; balance",
    "dc2": "strash; dc2",
}

FLOW_SCRIPTS = {
    "fraig": "fraig",
    "fraig_x": "fraig -x",
    "fraig_y": "fraig -y",
    "amp_fraig_x": "&get -n\n&fraig -x\n&put",
}


PS_RE = re.compile(r"(?:and|nd)\s*=\s*(\d+).*?lev\s*=\s*(\d+)", re.IGNORECASE)


@dataclass
class BaselineRow:
    benchmark: str
    source_family: str
    optimization: str
    original_optimized_blif_path: str
    abc_sweep_flow_name: str
    node_count_before: int | None
    node_count_after: int | None
    level_count_before: int | None
    level_count_after: int | None
    node_reduction: int | None
    level_reduction: int | None
    runtime_seconds: float
    abc_reported_equivalence_or_failure: str
    abc_statistics: str
    swept_blif_path: str


def parse_ps_metrics(text: str) -> list[tuple[int, int]]:
    return [(int(m.group(1)), int(m.group(2))) for m in PS_RE.finditer(text)]


def abc_status(output: str, exit_code: int | None) -> str:
    lowered = output.lower()
    if exit_code not in (0, None):
        return f"failure: exit {exit_code}"
    if "unknown command" in lowered or "unknown option" in lowered or "invalid option" in lowered:
        return "failure: unsupported command"
    if "error:" in lowered or "assertion" in lowered:
        return "failure: abc reported error"
    if "networks are equivalent" in lowered or "equivalent" in lowered:
        return "equivalence reported"
    return "completed"


def rel(path: Path | str) -> str:
    p = Path(path)
    try:
        return p.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return p.as_posix()


def source_blif_for_benchmark(benchmark: str) -> Path | None:
    candidates = [
        ROOT / "benchmarks" / f"{benchmark}.blif",
    ]
    if benchmark.startswith("generated_"):
        candidates.append(ROOT / "benchmarks" / "generated" / f"{benchmark.removeprefix('generated_')}.blif")
    if benchmark.startswith("external_iscas85_"):
        candidates.append(ROOT / "benchmarks" / "external" / "iscas85" / f"{benchmark.removeprefix('external_iscas85_')}.blif")
    if benchmark.startswith("real_hand_written_"):
        candidates.append(ROOT / "benchmarks" / "real" / "hand_written" / f"{benchmark.removeprefix('real_hand_written_')}.blif")
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def ensure_optimized_input(abc_bin: str, benchmark: str, optimization: str) -> tuple[Path | None, str]:
    existing = VARIANTS_DIR / f"{benchmark}_{optimization}.blif"
    if existing.exists():
        return existing, ""

    source = source_blif_for_benchmark(benchmark)
    if source is None:
        return None, "source BLIF not found"

    INPUT_DIR.mkdir(parents=True, exist_ok=True)
    out = INPUT_DIR / f"{benchmark}_{optimization}.blif"
    command = OPT_COMMANDS.get(optimization)
    if command is None:
        return None, f"unknown optimization {optimization}"

    script = f"read_blif {source.resolve()}\n{command}\nwrite_blif {out.resolve()}\n"
    exit_code, output = run_abc_script(abc_bin, script, timeout=60)
    status = abc_status(output, exit_code)
    if not out.exists() or status.startswith("failure"):
        return None, f"{status}: {short_snippet(output, 250)}"
    return out, ""


def run_flow(abc_bin: str, blif_path: Path, benchmark: str, optimization: str, flow_name: str, flow_script: str) -> BaselineRow:
    SWEEP_DIR.mkdir(parents=True, exist_ok=True)
    out_blif = SWEEP_DIR / f"{benchmark}_{optimization}_{flow_name}.blif"
    script = (
        f"read_blif {blif_path.resolve()}\n"
        "strash\n"
        "ps\n"
        f"{flow_script}\n"
        f"write_blif {out_blif.resolve()}\n"
        "ps\n"
    )
    start = time.perf_counter()
    exit_code, output = run_abc_script(abc_bin, script, timeout=120)
    runtime = time.perf_counter() - start
    metrics = parse_ps_metrics(output)
    before = metrics[0] if len(metrics) >= 1 else (None, None)
    after = metrics[-1] if len(metrics) >= 2 else (None, None)
    status = abc_status(output, exit_code)
    if status.startswith("failure") and out_blif.exists():
        out_blif.unlink()
    node_reduction = before[0] - after[0] if before[0] is not None and after[0] is not None else None
    level_reduction = before[1] - after[1] if before[1] is not None and after[1] is not None else None
    return BaselineRow(
        benchmark=benchmark,
        source_family=infer_source_family(benchmark),
        optimization=optimization,
        original_optimized_blif_path=rel(blif_path),
        abc_sweep_flow_name=flow_name,
        node_count_before=before[0],
        node_count_after=after[0],
        level_count_before=before[1],
        level_count_after=after[1],
        node_reduction=node_reduction,
        level_reduction=level_reduction,
        runtime_seconds=round(runtime, 4),
        abc_reported_equivalence_or_failure=status,
        abc_statistics=short_snippet(output, 800),
        swept_blif_path=rel(out_blif) if out_blif.exists() else "",
    )


def available_flows_from_capabilities(capability_csv: Path = RESULTS_DIR / "abc_sat_sweeping_capabilities.csv") -> dict[str, str]:
    flows = {"fraig": FLOW_SCRIPTS["fraig"]}
    if capability_csv.exists():
        with capability_csv.open(newline="", encoding="utf-8") as fh:
            caps = {row["command"]: row["supported"].lower() == "true" for row in csv.DictReader(fh)}
        if caps.get("fraig -x"):
            flows["fraig_x"] = FLOW_SCRIPTS["fraig_x"]
        if caps.get("fraig -y"):
            flows["fraig_y"] = FLOW_SCRIPTS["fraig_y"]
        if caps.get("&fraig -x"):
            flows["amp_fraig_x"] = FLOW_SCRIPTS["amp_fraig_x"]
    else:
        flows.update(FLOW_SCRIPTS)
    return flows


def write_baseline_csv(rows: list[BaselineRow], path: Path = BASELINE_CSV) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(asdict(rows[0]).keys()) if rows else list(BaselineRow.__dataclass_fields__.keys())
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))


def write_baseline_md(rows: list[BaselineRow], skipped: list[str], path: Path = BASELINE_MD) -> None:
    successful = [r for r in rows if r.abc_reported_equivalence_or_failure == "completed"]
    lines = [
        "# ABC-Native SAT Sweep Baseline",
        "",
        "This is an exploratory baseline. ABC is used to sweep one optimized network at a",
        "time; unless ABC exposes classes in the log, this measures structural reductions,",
        "not direct node correspondence mappings.",
        "",
        f"Rows collected: {len(rows)}",
        f"Completed flow rows: {len(successful)}",
        "",
        "| Flow | Rows | Mean node reduction | Mean level reduction |",
        "|---|---:|---:|---:|",
    ]
    by_flow: dict[str, list[BaselineRow]] = {}
    for row in rows:
        by_flow.setdefault(row.abc_sweep_flow_name, []).append(row)
    for flow, items in sorted(by_flow.items()):
        node_vals = [r.node_reduction for r in items if r.node_reduction is not None]
        level_vals = [r.level_reduction for r in items if r.level_reduction is not None]
        node_mean = sum(node_vals) / len(node_vals) if node_vals else 0.0
        level_mean = sum(level_vals) / len(level_vals) if level_vals else 0.0
        lines.append(f"| `{flow}` | {len(items)} | {node_mean:.2f} | {level_mean:.2f} |")
    lines.extend(["", "## Largest Node Reductions", "", "| Benchmark | Optimization | Flow | Before | After | Delta |", "|---|---|---|---:|---:|---:|"])
    ranked = sorted(
        [r for r in rows if r.node_reduction is not None],
        key=lambda r: r.node_reduction or 0,
        reverse=True,
    )[:12]
    for row in ranked:
        lines.append(
            f"| `{row.benchmark}` | `{row.optimization}` | `{row.abc_sweep_flow_name}` | "
            f"{row.node_count_before} | {row.node_count_after} | {row.node_reduction} |"
        )
    if skipped:
        lines.extend(["", "## Skipped Inputs", ""])
        lines.extend(f"- {item}" for item in skipped)
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def make_baseline_plots(rows: list[BaselineRow]) -> list[str]:
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    completed = [r for r in rows if r.node_reduction is not None]
    if not completed:
        return []
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from io import BytesIO

        smoke_fig, smoke_ax = plt.subplots(figsize=(1, 1))
        smoke_ax.text(0.5, 0.5, "ok")
        smoke_fig.savefig(BytesIO(), format="png")
        plt.close(smoke_fig)
    except Exception:
        return make_baseline_plots_pillow(completed)
    outputs: list[str] = []
    labels = [f"{r.benchmark}\n{r.optimization}" for r in completed]
    flows = sorted({r.abc_sweep_flow_name for r in completed})

    for metric, filename, ylabel in [
        ("node_reduction", "abc_native_node_reduction_by_flow.png", "Node reduction after ABC sweep"),
        ("level_reduction", "abc_native_level_reduction_by_flow.png", "Level reduction after ABC sweep"),
    ]:
        fig, ax = plt.subplots(figsize=(11, 5))
        x = list(range(len(labels)))
        width = 0.8 / max(len(flows), 1)
        for i, flow in enumerate(flows):
            vals = []
            for row in completed:
                vals.append(getattr(row, metric) if row.abc_sweep_flow_name == flow else 0)
            offsets = [v + (i - len(flows) / 2 + 0.5) * width for v in x]
            ax.bar(offsets, vals, width=width * 0.9, label=flow)
        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=7)
        ax.set_ylabel(ylabel)
        ax.set_title("Exploratory ABC-native FRAIG/SAT sweeping baseline")
        ax.grid(axis="y", linestyle="--", alpha=0.35)
        ax.legend()
        fig.tight_layout()
        out = PLOTS_DIR / filename
        fig.savefig(out, dpi=150, bbox_inches="tight")
        plt.close(fig)
        outputs.append(rel(out))
    return outputs


def make_baseline_plots_pillow(rows: list[BaselineRow]) -> list[str]:
    from PIL import Image, ImageDraw, ImageFont

    outputs: list[str] = []
    for metric, filename, title in [
        ("node_reduction", "abc_native_node_reduction_by_flow.png", "ABC-native node reduction by flow"),
        ("level_reduction", "abc_native_level_reduction_by_flow.png", "ABC-native level reduction by flow"),
    ]:
        values = [max(0, int(getattr(row, metric) or 0)) for row in rows]
        width, height = 1200, 620
        margin_l, margin_r, margin_t, margin_b = 80, 40, 70, 170
        img = Image.new("RGB", (width, height), "white")
        draw = ImageDraw.Draw(img)
        font = ImageFont.load_default()
        draw.text((margin_l, 25), f"{title} (exploratory)", fill="black", font=font)
        plot_w = width - margin_l - margin_r
        plot_h = height - margin_t - margin_b
        base_y = margin_t + plot_h
        draw.line((margin_l, margin_t, margin_l, base_y), fill="black")
        draw.line((margin_l, base_y, width - margin_r, base_y), fill="black")
        max_val = max(values) if values else 1
        max_val = max(max_val, 1)
        bar_w = max(4, plot_w // max(len(values) * 2, 1))
        colors = ["#0072B2", "#E69F00", "#009E73", "#D55E00"]
        for i, (row, value) in enumerate(zip(rows, values)):
            x = margin_l + i * (plot_w / max(len(values), 1)) + bar_w * 0.3
            bar_h = int((value / max_val) * (plot_h - 20))
            color = colors[hash(row.abc_sweep_flow_name) % len(colors)]
            draw.rectangle((x, base_y - bar_h, x + bar_w, base_y), fill=color)
            label = f"{row.benchmark}/{row.optimization}/{row.abc_sweep_flow_name}"
            draw.text((x, base_y + 8), label[:22], fill="black", font=font)
            if value:
                draw.text((x, base_y - bar_h - 14), str(value), fill="black", font=font)
        draw.text((margin_l, height - 35), "Fallback Pillow plot; labels truncated for readability.", fill="#555555", font=font)
        out = PLOTS_DIR / filename
        img.save(out)
        outputs.append(rel(out))
    return outputs


def run_baseline(abc_bin: str, benchmarks: list[str], optimizations: list[str], flows: dict[str, str]) -> tuple[list[BaselineRow], list[str]]:
    rows: list[BaselineRow] = []
    skipped: list[str] = []
    for benchmark in benchmarks:
        for optimization in optimizations:
            blif, reason = ensure_optimized_input(abc_bin, benchmark, optimization)
            if blif is None:
                skipped.append(f"`{benchmark}` / `{optimization}`: {reason}")
                continue
            for flow_name, flow_script in flows.items():
                rows.append(run_flow(abc_bin, blif, benchmark, optimization, flow_name, flow_script))
    return rows, skipped


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--abc", help="Path to ABC binary. Defaults to $ABC or .abc_build/abc_repo/abc.")
    parser.add_argument("--benchmarks", nargs="+", default=DEFAULT_BENCHMARKS)
    parser.add_argument("--optimizations", nargs="+", default=DEFAULT_OPTIMIZATIONS)
    parser.add_argument("--full", action="store_true", help="Run all known optimization variants for the selected benchmarks.")
    parser.add_argument("--all-benchmarks", action="store_true", help="Use all benchmarks listed in results/benchmark_manifest.csv.")
    args = parser.parse_args(argv)

    abc_bin = find_abc(args.abc)
    benchmarks = args.benchmarks
    if args.all_benchmarks:
        manifest = RESULTS_DIR / "benchmark_manifest.csv"
        with manifest.open(newline="", encoding="utf-8") as fh:
            benchmarks = [row["benchmark"] for row in csv.DictReader(fh)]
    optimizations = FULL_OPTIMIZATIONS if args.full else args.optimizations
    flows = available_flows_from_capabilities()
    rows, skipped = run_baseline(abc_bin, benchmarks, optimizations, flows)
    write_baseline_csv(rows)
    write_baseline_md(rows, skipped)
    plots = make_baseline_plots(rows)
    print(f"Wrote {BASELINE_CSV.relative_to(ROOT)}")
    print(f"Wrote {BASELINE_MD.relative_to(ROOT)}")
    for plot in plots:
        print(f"Wrote {plot}")
    if skipped:
        print(f"Skipped {len(skipped)} benchmark/optimization inputs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
