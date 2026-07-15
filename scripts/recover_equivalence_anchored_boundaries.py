#!/usr/bin/env python3
"""Run equivalence-anchored boundary recovery experiments."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from boundary_anchor_map import ANCHOR_MODES, load_anchor_map  # noqa: E402
from boundary_graph import CircuitGraph  # noqa: E402
from boundary_recovery import (  # noqa: E402
    CoiSpec,
    compute_boundary_metrics,
    load_coi_specs,
    recover_extended_boundary,
    region_manifest,
    write_region_dot,
)
from scripts.benchmark_id import infer_source_family  # noqa: E402

RESULTS = ROOT / "results" / "boundary_recovery"
PLOTS = ROOT / "results" / "plots"
COI_SPEC = ROOT / "benchmarks" / "coi_specs" / "boundary_recovery_seed_cois.json"
DEFAULT_OPTIMIZATIONS = ["balance", "rewrite", "resyn2", "dc2"]
CASE_CSV = RESULTS / "boundary_recovery_cases.csv"
FAIL_CSV = RESULTS / "boundary_recovery_failures.csv"
SUMMARY_MD = RESULTS / "boundary_recovery_summary.md"
JSON_OUT = RESULTS / "boundary_recovery_regions.json"
DOT_DIR = RESULTS / "dot"

CASE_COLUMNS = [
    "benchmark",
    "benchmark_family",
    "coi_name",
    "optimization",
    "anchor_mode",
    "spec_path",
    "impl_path",
    "coi_source",
    "spec_node_count",
    "impl_node_count",
    "coi_node_count",
    "extended_region_node_count",
    "boundary_extension_ratio",
    "original_bi_count",
    "original_bo_count",
    "extended_bi_count",
    "extended_bo_count",
    "anchor_count",
    "cut_valid",
    "cycle_free",
    "cycle_resolution_iterations",
    "cycle_conflict_count",
    "invalidated_anchor_count",
    "cycle_resolution_status",
    "recovery_success",
    "failure_reason",
    "runtime_seconds",
    "evidence_level",
    "whole_design_expansion",
    "input_boundary_distance",
    "output_boundary_distance",
    "mean_anchor_distance",
    "max_anchor_distance",
    "extended_boundary_inputs",
    "extended_boundary_outputs",
    "region_nodes",
]


def variant_path(benchmark: str, optimization: str) -> Path:
    return ROOT / "variants" / f"{benchmark}_{optimization}.blif"


def original_path(benchmark: str) -> Path:
    return ROOT / "variants" / f"{benchmark}_original.blif"


def parse_csv_list(value: str | None, default: list[str]) -> list[str]:
    if not value:
        return list(default)
    return [item.strip() for item in value.split(",") if item.strip()]


def expand_cases(specs: list[CoiSpec], benchmarks: list[str], optimizations: list[str]) -> list[CoiSpec]:
    out = []
    wanted = set(benchmarks)
    for spec in specs:
        if benchmarks and spec.benchmark not in wanted:
            continue
        opts = optimizations if spec.optimization == "*" else [spec.optimization]
        for opt in opts:
            out.append(
                CoiSpec(
                    benchmark=spec.benchmark,
                    optimization=opt,
                    coi_name=spec.coi_name,
                    coi_internal_nodes=spec.coi_internal_nodes,
                    boundary_inputs=spec.boundary_inputs,
                    boundary_outputs=spec.boundary_outputs,
                    source=spec.source,
                )
            )
    return sorted(out, key=lambda c: (c.benchmark, c.coi_name, c.optimization))


def skipped_row(coi: CoiSpec, mode: str, spec: Path, impl: Path, reason: str) -> dict[str, object]:
    row = {column: "" for column in CASE_COLUMNS}
    row.update(
        {
            "benchmark": coi.benchmark,
            "benchmark_family": infer_source_family(coi.benchmark),
            "coi_name": coi.coi_name,
            "optimization": coi.optimization,
            "anchor_mode": mode,
            "spec_path": rel(spec),
            "impl_path": rel(impl),
            "coi_source": coi.source,
            "cut_valid": False,
            "cycle_free": False,
            "recovery_success": False,
            "failure_reason": reason,
            "evidence_level": "unresolved",
        }
    )
    return row


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def run_case(coi: CoiSpec, anchor_mode: str, max_cycle_iterations: int) -> tuple[dict[str, object], dict[str, object] | None]:
    spec = original_path(coi.benchmark)
    impl = variant_path(coi.benchmark, coi.optimization)
    if not spec.exists():
        return skipped_row(coi, anchor_mode, spec, impl, "missing_spec_circuit"), None
    if not impl.exists():
        return skipped_row(coi, anchor_mode, spec, impl, "missing_impl_circuit"), None
    spec_graph = CircuitGraph.from_blif(spec)
    impl_graph = CircuitGraph.from_blif(impl)
    anchors = load_anchor_map(
        coi.benchmark,
        coi.optimization,
        anchor_mode,
        results_dir=ROOT / "results",
        spec_inputs=spec_graph.inputs,
        impl_inputs=impl_graph.inputs,
        spec_outputs=spec_graph.outputs,
        impl_outputs=impl_graph.outputs,
    )
    result = recover_extended_boundary(
        spec_graph,
        impl_graph,
        coi,
        anchors,
        max_cycle_resolution_iterations=max_cycle_iterations,
    )
    metrics = compute_boundary_metrics(result, spec_graph, impl_graph)
    evidence = "formal_cec" if anchor_mode != "exact_only" else "formal_exhaustive"
    success = result.validation_status == "valid"
    row = {
        "benchmark": coi.benchmark,
        "benchmark_family": infer_source_family(coi.benchmark),
        "coi_name": coi.coi_name,
        "optimization": coi.optimization,
        "anchor_mode": anchor_mode,
        "spec_path": rel(spec),
        "impl_path": rel(impl),
        "coi_source": coi.source,
        "spec_node_count": metrics["spec_node_count"],
        "impl_node_count": metrics["impl_node_count"],
        "coi_node_count": metrics["coi_node_count"],
        "extended_region_node_count": metrics["extended_region_node_count"],
        "boundary_extension_ratio": metrics["boundary_extension_ratio"],
        "original_bi_count": metrics["original_boundary_input_count"],
        "original_bo_count": metrics["original_boundary_output_count"],
        "extended_bi_count": metrics["extended_boundary_input_count"],
        "extended_bo_count": metrics["extended_boundary_output_count"],
        "anchor_count": metrics["anchor_count"],
        "cut_valid": success,
        "cycle_free": result.cycle_resolution_status == "cycle_free",
        "cycle_resolution_iterations": result.cycle_resolution_iterations,
        "cycle_conflict_count": result.cycle_conflict_count,
        "invalidated_anchor_count": result.invalidated_anchor_count,
        "cycle_resolution_status": result.cycle_resolution_status,
        "recovery_success": success,
        "failure_reason": result.failure_reason or result.validation_status,
        "runtime_seconds": result.runtime_seconds,
        "evidence_level": evidence if success else "unresolved",
        "whole_design_expansion": result.validation_status == "whole_design_boundary",
        "input_boundary_distance": metrics["input_boundary_distance"],
        "output_boundary_distance": metrics["output_boundary_distance"],
        "mean_anchor_distance": metrics["mean_anchor_distance"],
        "max_anchor_distance": metrics["max_anchor_distance"],
        "extended_boundary_inputs": ";".join(result.extended_boundary_inputs),
        "extended_boundary_outputs": ";".join(result.extended_boundary_outputs),
        "region_nodes": ";".join(result.region_nodes),
    }
    manifest = region_manifest(result)
    manifest["anchor_mode"] = anchor_mode
    return row, manifest


def write_rollups(cases: list[dict[str, object]]) -> None:
    if not cases:
        return
    for group_cols, name in [
        (["benchmark"], "boundary_recovery_by_benchmark.csv"),
        (["optimization"], "boundary_recovery_by_optimization.csv"),
        (["anchor_mode"], "boundary_recovery_by_anchor_mode.csv"),
    ]:
        groups: dict[tuple[str, ...], list[dict[str, object]]] = {}
        for case in cases:
            key = tuple(str(case.get(col, "")) for col in group_cols)
            groups.setdefault(key, []).append(case)
        rows: list[dict[str, object]] = []
        for key, group in sorted(groups.items()):
            row = dict(zip(group_cols, key))
            success_values = [_as_bool(item.get("recovery_success")) for item in group]
            extension_values = [_as_float(item.get("boundary_extension_ratio")) for item in group]
            region_values = [_as_float(item.get("extended_region_node_count")) for item in group]
            row.update(
                {
                    "cases": len(group),
                    "recovery_success_count": sum(success_values),
                    "recovery_success_rate": sum(success_values) / len(group) if group else 0.0,
                    "mean_boundary_extension_ratio": sum(extension_values) / len(extension_values) if extension_values else 0.0,
                    "mean_extended_region_node_count": sum(region_values) / len(region_values) if region_values else 0.0,
                    "cycle_conflict_count": sum(int(_as_float(item.get("cycle_conflict_count"))) for item in group),
                }
            )
            rows.append(row)
        write_csv(RESULTS / name, rows)


def write_summary(cases: list[dict[str, object]], failures: list[dict[str, object]]) -> None:
    success = sum(_as_bool(row.get("recovery_success")) for row in cases)
    total = len(cases)
    rate = success / total if total else 0.0
    lines = [
        "# Equivalence-Anchored Boundary Recovery Summary",
        "",
        "This prototype recovers coherent regions enclosed by formally anchored input and output cuts. It does not claim direct node equivalence for every internal node in a recovered region.",
        "",
        f"- Cases: {total}",
        f"- Successful recovered boundaries: {success} ({rate:.1%})",
        f"- Failure / skipped rows: {len(failures)}",
        "",
        "## Overall by Anchor Mode",
        "",
    ]
    mode_path = RESULTS / "boundary_recovery_by_anchor_mode.csv"
    if mode_path.exists():
        lines.append(markdown_table(read_csv(mode_path)))
    lines.extend(["", "## Failure Reasons", ""])
    if not failures:
        lines.append("No failures were recorded.")
    else:
        counts: dict[str, int] = {}
        for row in failures:
            counts[str(row.get("failure_reason") or "unknown")] = counts.get(str(row.get("failure_reason") or "unknown"), 0) + 1
        lines.append(markdown_table([{"failure_reason": key, "count": value} for key, value in sorted(counts.items())]))
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "A successful row means the COI is enclosed by selected formal anchors at the recovered cuts. It does not mean every node inside the region has a direct node-level match.",
        ]
    )
    SUMMARY_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def make_plots(cases: list[dict[str, object]]) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    PLOTS.mkdir(parents=True, exist_ok=True)
    if not cases:
        return

    def save(path: str) -> None:
        plt.tight_layout()
        plt.savefig(PLOTS / path, dpi=180)
        plt.close()

    by_opt = mean_by(cases, "optimization", "boundary_extension_ratio")
    plt.figure(figsize=(7, 4))
    plt.bar(list(by_opt), list(by_opt.values()), color="#4c78a8")
    plt.ylabel("mean boundary extension ratio")
    plt.title("Boundary Extension by Optimization")
    save("boundary_extension_by_optimization.png")

    by_mode = mean_bool_by(cases, "anchor_mode", "recovery_success")
    plt.figure(figsize=(7, 4))
    plt.bar(list(by_mode), list(by_mode.values()), color="#54a24b")
    plt.ylim(0, 1.05)
    plt.ylabel("recovery success rate")
    plt.title("Recovery Success by Anchor Mode")
    save("boundary_recovery_success_by_anchor_mode.png")

    labels = sorted({str(row["coi_name"]) for row in cases})
    modes = sorted({str(row["anchor_mode"]) for row in cases})
    x = range(len(labels))
    width = 0.8 / max(1, len(modes))
    plt.figure(figsize=(8, 4.5))
    for idx, mode in enumerate(modes):
        values = [mean_for(cases, "coi_name", label, "anchor_mode", mode, "boundary_extension_ratio") for label in labels]
        plt.bar([i + idx * width for i in x], values, width=width, label=mode)
    plt.xticks([i + width * (len(modes) - 1) / 2 for i in x], labels, rotation=30, ha="right")
    plt.legend(fontsize=8)
    plt.ylabel("boundary extension ratio")
    plt.title("Exact-only vs Formal-all Extension")
    save("boundary_exact_vs_formal_extension.png")

    plt.figure(figsize=(6, 4))
    plt.scatter([_as_float(row.get("anchor_count")) for row in cases], [_as_float(row.get("boundary_extension_ratio")) for row in cases], alpha=0.7)
    plt.xlabel("selected anchor count")
    plt.ylabel("boundary extension ratio")
    plt.title("Anchor Density vs Boundary Extension")
    save("boundary_anchor_density_vs_extension.png")

    plt.figure(figsize=(6, 4))
    plt.scatter([_as_float(row.get("coi_node_count")) for row in cases], [_as_float(row.get("extended_region_node_count")) for row in cases], alpha=0.7)
    plt.xlabel("COI node count")
    plt.ylabel("extended region node count")
    plt.title("COI Size vs Extended Region Size")
    save("boundary_coi_vs_region_size.png")

    plt.figure(figsize=(6, 4))
    plt.hist([_as_float(row.get("mean_anchor_distance")) for row in cases], bins=8, color="#f58518")
    plt.xlabel("mean anchor traversal distance")
    plt.title("Boundary Traversal Distance Distribution")
    save("boundary_traversal_distance_distribution.png")

    failure_counts: dict[str, int] = {}
    for row in cases:
        key = str(row.get("failure_reason") or "valid")
        failure_counts[key] = failure_counts.get(key, 0) + 1
    plt.figure(figsize=(8, 4))
    plt.bar(list(failure_counts), list(failure_counts.values()), color="#b8b8b8")
    plt.xticks(rotation=30, ha="right")
    plt.ylabel("case count")
    plt.title("Boundary Recovery Failure Reasons")
    save("boundary_failure_reasons.png")

    cycle_by_mode: dict[str, float] = {}
    for row in cases:
        key = str(row.get("anchor_mode"))
        cycle_by_mode[key] = cycle_by_mode.get(key, 0.0) + _as_float(row.get("cycle_conflict_count"))
    plt.figure(figsize=(6, 4))
    plt.bar(list(cycle_by_mode), list(cycle_by_mode.values()), color="#e45756")
    plt.ylabel("cycle conflicts")
    plt.title("Cycle-Resolution Frequency")
    save("boundary_cycle_resolution_frequency.png")

    plt.figure(figsize=(6, 4))
    plt.scatter([_as_float(row.get("spec_node_count")) for row in cases], [_as_float(row.get("runtime_seconds")) for row in cases], alpha=0.7)
    plt.xlabel("spec node count")
    plt.ylabel("runtime seconds")
    plt.title("Boundary Recovery Runtime by Circuit Size")
    save("boundary_runtime_by_circuit_size.png")

    critical_path = RESULTS / "critical_path_region_recovery.csv"
    if critical_path.exists():
        critical = read_csv(critical_path)
        enclosed: dict[str, float] = {}
        for row in critical:
            key = str(row.get("anchor_mode"))
            enclosed[key] = enclosed.get(key, 0.0) + _as_float(row.get("previously_unresolved_nodes_enclosed"))
        plt.figure(figsize=(6, 4))
        plt.bar(list(enclosed), list(enclosed.values()), color="#72b7b2")
        plt.ylabel("unresolved path nodes enclosed")
        plt.title("Critical-Path Nodes Enclosed by Regions")
        save("boundary_critical_path_enclosed.png")


def _as_float(value: object) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _as_bool(value: object) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes"}


def write_csv(path: Path, rows: list[dict[str, object]], columns: list[str] | None = None) -> None:
    if columns is None:
        columns = sorted({key for row in rows for key in row}) if rows else []
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def markdown_table(rows: list[dict[str, object]]) -> str:
    if not rows:
        return ""
    columns = list(rows[0])
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join(["---"] * len(columns)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(col, "")) for col in columns) + " |")
    return "\n".join(lines)


def mean_by(rows: list[dict[str, object]], key_col: str, value_col: str) -> dict[str, float]:
    groups: dict[str, list[float]] = {}
    for row in rows:
        groups.setdefault(str(row.get(key_col)), []).append(_as_float(row.get(value_col)))
    return {key: sum(values) / len(values) for key, values in sorted(groups.items())}


def mean_bool_by(rows: list[dict[str, object]], key_col: str, value_col: str) -> dict[str, float]:
    groups: dict[str, list[int]] = {}
    for row in rows:
        groups.setdefault(str(row.get(key_col)), []).append(int(_as_bool(row.get(value_col))))
    return {key: sum(values) / len(values) for key, values in sorted(groups.items())}


def mean_for(rows: list[dict[str, object]], key_a: str, value_a: str, key_b: str, value_b: str, metric: str) -> float:
    values = [_as_float(row.get(metric)) for row in rows if str(row.get(key_a)) == value_a and str(row.get(key_b)) == value_b]
    return sum(values) / len(values) if values else 0.0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--coi-spec", type=Path, default=COI_SPEC)
    parser.add_argument("--anchor-modes", default="exact_only,formal_all")
    parser.add_argument("--benchmarks", default="")
    parser.add_argument("--optimizations", default=",".join(DEFAULT_OPTIMIZATIONS))
    parser.add_argument("--output-csv", type=Path, default=CASE_CSV)
    parser.add_argument("--output-json", type=Path, default=JSON_OUT)
    parser.add_argument("--output-summary", type=Path, default=SUMMARY_MD)
    parser.add_argument("--output-dot-dir", type=Path, default=DOT_DIR)
    parser.add_argument("--max-cycle-resolution-iterations", type=int, default=2)
    parser.add_argument("--write-plots", action="store_true")
    parser.add_argument("--plots-only", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    RESULTS.mkdir(parents=True, exist_ok=True)
    if args.plots_only:
        make_plots(read_csv(args.output_csv) if args.output_csv.exists() else [])
        print("Boundary recovery plots regenerated")
        return 0
    args.output_dot_dir.mkdir(parents=True, exist_ok=True)
    specs = load_coi_specs(args.coi_spec)
    benchmarks = parse_csv_list(args.benchmarks, [])
    optimizations = parse_csv_list(args.optimizations, DEFAULT_OPTIMIZATIONS)
    modes = parse_csv_list(args.anchor_modes, ["exact_only", "formal_all"])
    cases = expand_cases(specs, benchmarks, optimizations)
    rows = []
    manifests = []
    for coi in cases:
        for mode in modes:
            if mode not in ANCHOR_MODES:
                raise SystemExit(f"unknown anchor mode: {mode}")
            row, manifest = run_case(coi, mode, args.max_cycle_resolution_iterations)
            rows.append(row)
            if manifest is not None:
                manifests.append(manifest)
                if row.get("recovery_success"):
                    spec_graph = CircuitGraph.from_blif(original_path(coi.benchmark))
                    write_region_dot(
                        recover_extended_boundary(
                            spec_graph,
                            CircuitGraph.from_blif(variant_path(coi.benchmark, coi.optimization)),
                            coi,
                            load_anchor_map(
                                coi.benchmark,
                                coi.optimization,
                                mode,
                                results_dir=ROOT / "results",
                                spec_inputs=spec_graph.inputs,
                                impl_inputs=CircuitGraph.from_blif(variant_path(coi.benchmark, coi.optimization)).inputs,
                                spec_outputs=spec_graph.outputs,
                                impl_outputs=CircuitGraph.from_blif(variant_path(coi.benchmark, coi.optimization)).outputs,
                            ),
                        ),
                        spec_graph,
                        args.output_dot_dir / f"{coi.benchmark}_{coi.coi_name}_{coi.optimization}_{mode}.dot",
                    )
    write_csv(args.output_csv, rows, CASE_COLUMNS)
    failures = [row for row in rows if not _as_bool(row.get("recovery_success"))]
    write_csv(FAIL_CSV, failures, CASE_COLUMNS)
    args.output_json.write_text(json.dumps(manifests, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_rollups(rows)
    write_summary(rows, failures)
    if args.write_plots:
        make_plots(rows)
    print(f"Wrote {len(rows)} boundary recovery rows to {args.output_csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
