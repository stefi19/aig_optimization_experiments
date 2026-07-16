"""Shared pipeline functions for semantic-region Phase 2 scripts."""

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

from boundary_graph import CircuitGraph
from coi_model import derive_boundary_inputs, derive_boundary_outputs
from semantic_interface import (
    SEMANTIC_BUS_GROUND_TRUTH_FIELDS,
    SEMANTIC_INTERFACE_ALIGNMENT_FIELDS,
    SEMANTIC_SCALAR_INTERFACE_FIELDS,
    compare_scalar_interface,
    extract_scalar_interface,
    normalize_bus_metadata,
)
from semantic_region import (
    ACTIVE_REGION_SOURCES,
    SEMANTIC_REGION_FIELDS,
    SemanticRegion,
    circuit_fingerprint,
    non_input_logic_nodes,
    output_cone_region,
    relpath,
    write_csv,
    write_json,
)
from semantic_region_validation import SEMANTIC_REGION_VALIDATION_FIELDS, validate_semantic_region


ROOT = Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results" / "semantic_recovery"
REGION_DIR = RESULT_DIR / "regions"
PLOT_DIR = ROOT / "results" / "plots"
PRESENTATION_PLOT_DIR = ROOT / "docs" / "presentation" / "assets" / "plots"

MANIFEST = RESULT_DIR / "semantic_benchmark_manifest.csv"
VARIANTS = RESULT_DIR / "semantic_benchmark_variants.csv"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def load_manifest() -> dict[str, dict[str, str]]:
    return {row["case_id"]: row for row in read_csv(MANIFEST)}


def load_variants() -> list[dict[str, str]]:
    return read_csv(VARIANTS)


def parse_json_field(row: dict[str, str], field: str) -> object:
    return json.loads(row.get(field, "[]") or "[]")


def status_for_variant(variant: dict[str, str]) -> tuple[str, str, bool]:
    status = variant["status"]
    if status == "generated":
        return "eligible", "", True
    if status == "skipped_rtl_only":
        return "unsupported_case", "truth_table_blif_intentionally_skipped", False
    if status == "skipped_variant_too_large":
        return "unsupported_case", "abc_variant_generation_bounded", False
    if status == "skipped_no_abc":
        return "infrastructure_skip", "abc_unavailable", False
    return "infrastructure_skip", status, False


def make_region_id(case_id: str, optimization: str, source_type: str) -> str:
    return f"{case_id}__{optimization}__{source_type}"


def build_one_region(
    manifest_row: dict[str, str],
    variant_row: dict[str, str],
    source_type: str,
) -> tuple[SemanticRegion, dict[str, str]]:
    case_id = manifest_row["case_id"]
    optimization = variant_row["flow"]
    region_id = make_region_id(case_id, optimization, source_type)
    variant_status, variant_skip, variant_available = status_for_variant(variant_row)
    input_buses = tuple(parse_json_field(manifest_row, "input_buses"))  # type: ignore[arg-type]
    output_buses = tuple(parse_json_field(manifest_row, "output_buses"))  # type: ignore[arg-type]
    observable_outputs = tuple(name for bus in output_buses for name in _flat_bus_members(bus))
    source_path = ROOT / manifest_row["source_blif"] if manifest_row["source_blif"] else None
    impl_path = ROOT / variant_row["variant_blif"] if variant_row["variant_blif"] else None

    status = variant_status
    skip_reason = variant_skip
    circuit_available = bool(impl_path and impl_path.exists())
    region_available = False
    structurally_valid = False
    interface_extractable = False
    attempted = False
    region_nodes: tuple[str, ...] = tuple()
    bi: tuple[str, ...] = tuple()
    bo: tuple[str, ...] = tuple()
    spec_fp = ""
    impl_fp = ""
    validation_row: dict[str, str] = {
        field: "" for field in SEMANTIC_REGION_VALIDATION_FIELDS
    }

    if source_type == "ground_truth_region" and optimization != "identity":
        status = "unsupported_case"
        skip_reason = "ground_truth_region_not_available_for_optimized_variant"
        circuit_available = bool(source_path and source_path.exists())
    elif source_type == "ground_truth_region" and source_path and source_path.exists():
        impl_path = source_path
        circuit_available = True
    elif source_type == "whole_output_cone" and not variant_available:
        pass

    if circuit_available and impl_path:
        graph = CircuitGraph.from_blif(impl_path)
        spec_fp = _fingerprint_for(manifest_row, source_path, "identity") if source_path and source_path.exists() else ""
        impl_fp = _fingerprint_for(manifest_row, impl_path, optimization)
        if source_type in ACTIVE_REGION_SOURCES:
            attempted = status == "eligible"
            if attempted:
                region_nodes = output_cone_region(graph, observable_outputs)
                region_available = bool(region_nodes)
                bi = derive_boundary_inputs(graph, region_nodes)
                bo = derive_boundary_outputs(graph, region_nodes)
                validation = validate_semantic_region(
                    graph,
                    region_id=region_id,
                    region_nodes=region_nodes,
                    boundary_inputs=bi,
                    boundary_outputs=bo,
                    observable_outputs=observable_outputs,
                    expected_region_nodes=region_nodes if source_type == "ground_truth_region" else tuple(),
                    expected_benchmark=case_id,
                    actual_benchmark=case_id,
                    expected_optimization=optimization,
                    actual_optimization=optimization,
                )
                validation_row = validation.to_csv_row()
                structurally_valid = validation.valid
                interface_extractable = validation.valid
                if not validation.valid:
                    status = "invalid_region"
                    skip_reason = ";".join(validation.errors)
    elif not skip_reason:
        status = "infrastructure_skip"
        skip_reason = "missing_blif"

    eligible = status == "eligible" and structurally_valid and interface_extractable
    if attempted and not structurally_valid and status == "eligible":
        status = "invalid_region"
    region = SemanticRegion(
        region_id=region_id,
        case_id=case_id,
        benchmark=case_id,
        family=manifest_row["family"],
        operator=manifest_row["operator"],
        optimization=optimization,
        source_type=source_type,
        spec_circuit_path=manifest_row["source_blif"],
        impl_circuit_path=relpath(impl_path, ROOT) if impl_path and impl_path.exists() else "",
        region_nodes=region_nodes,
        boundary_inputs=bi,
        boundary_outputs=bo,
        observable_outputs=observable_outputs,
        ground_truth_expression=manifest_row["expression"],
        ground_truth_input_buses=input_buses,
        ground_truth_output_buses=output_buses,
        ground_truth_signedness=manifest_row["signedness"],
        ground_truth_width_semantics=manifest_row["extension_mode"] or manifest_row["truncation"],
        formal_scope="none",
        context_mode="not_applicable",
        source_manifest=relpath(MANIFEST, ROOT),
        spec_fingerprint=spec_fp,
        impl_fingerprint=impl_fp,
        declared=True,
        circuit_available=circuit_available,
        region_available=region_available,
        structurally_valid=structurally_valid,
        interface_extractable=interface_extractable,
        eligible=eligible,
        attempted=attempted,
        status=status,
        skip_reason="" if eligible else skip_reason,
    )
    if not validation_row["region_id"]:
        validation_row["region_id"] = region_id
        validation_row["valid"] = str(structurally_valid).lower()
    return region, validation_row


def _flat_bus_members(bus: dict[str, object]) -> tuple[str, ...]:
    name = str(bus["name"])
    width = int(bus.get("width", 1))
    if width == 1:
        return (name,)
    return tuple(f"{name}_{idx}" for idx in range(width))


def _fingerprint_for(manifest_row: dict[str, str], path: Path, optimization: str) -> str:
    fp = circuit_fingerprint(path, benchmark_id=manifest_row["case_id"], optimization_id=optimization)
    return json.dumps(fp.__dict__, sort_keys=True, separators=(",", ":"))


def build_regions(
    *,
    source_types: tuple[str, ...] = ACTIVE_REGION_SOURCES,
    families: set[str] | None = None,
    operators: set[str] | None = None,
    widths: set[int] | None = None,
    optimizations: set[str] | None = None,
) -> tuple[list[SemanticRegion], list[dict[str, str]]]:
    manifest = load_manifest()
    regions: list[SemanticRegion] = []
    validations: list[dict[str, str]] = []
    for variant in sorted(load_variants(), key=lambda row: (row["case_id"], row["flow"])):
        m = manifest[variant["case_id"]]
        if families and m["family"] not in families:
            continue
        if operators and m["operator"] not in operators:
            continue
        if optimizations and variant["flow"] not in optimizations:
            continue
        if widths:
            width_values = set(json.loads(m.get("input_widths", "{}") or "{}").values())
            width_values.update(json.loads(m.get("output_widths", "{}") or "{}").values())
            if not width_values & widths:
                continue
        for source_type in source_types:
            region, validation = build_one_region(m, variant, source_type)
            regions.append(region)
            validations.append(validation)
    return regions, validations


def write_region_outputs(regions: list[SemanticRegion], validations: list[dict[str, str]]) -> None:
    rows = [region.to_csv_row() for region in regions]
    json_rows = [region.to_dict() for region in regions]
    write_csv(rows, RESULT_DIR / "semantic_regions.csv", SEMANTIC_REGION_FIELDS)
    write_json(json_rows, RESULT_DIR / "semantic_regions.json")
    write_csv(validations, RESULT_DIR / "semantic_region_validation.csv", SEMANTIC_REGION_VALIDATION_FIELDS)
    write_csv(
        [row for row in rows if row["source_type"] == "ground_truth_region"],
        REGION_DIR / "semantic_ground_truth_regions.csv",
        SEMANTIC_REGION_FIELDS,
    )
    write_json(
        [row for row in json_rows if row["source_type"] == "ground_truth_region"],
        REGION_DIR / "semantic_ground_truth_regions.json",
    )
    write_csv(
        [row for row in rows if row["source_type"] == "whole_output_cone"],
        REGION_DIR / "semantic_output_cone_regions.csv",
        SEMANTIC_REGION_FIELDS,
    )
    write_json(
        [row for row in json_rows if row["source_type"] == "whole_output_cone"],
        REGION_DIR / "semantic_output_cone_regions.json",
    )


def load_regions_from_csv() -> list[dict[str, str]]:
    return read_csv(RESULT_DIR / "semantic_regions.csv")


def extract_interfaces() -> tuple[list[dict[str, str]], list[dict[str, object]], list[dict[str, str]], list[dict[str, object]], list[dict[str, str]]]:
    scalar_csv: list[dict[str, str]] = []
    scalar_json: list[dict[str, object]] = []
    bus_csv: list[dict[str, str]] = []
    bus_json: list[dict[str, object]] = []
    alignment: list[dict[str, str]] = []
    seen_bus_cases: set[str] = set()
    for row in sorted(load_regions_from_csv(), key=lambda r: r["region_id"]):
        if row["eligible"] != "true":
            continue
        graph = CircuitGraph.from_blif(ROOT / row["impl_circuit_path"])
        input_buses = json.loads(row["ground_truth_input_buses"])
        output_buses = json.loads(row["ground_truth_output_buses"])
        region_scalar = extract_scalar_interface(
            graph,
            region_id=row["region_id"],
            case_id=row["case_id"],
            optimization=row["optimization"],
            source_type=row["source_type"],
            boundary_inputs=tuple(json.loads(row["boundary_inputs"])),
            boundary_outputs=tuple(json.loads(row["boundary_outputs"])),
            input_buses=input_buses,
            output_buses=output_buses,
        )
        scalar_csv.extend(entry.to_csv_row() for entry in region_scalar)
        scalar_json.extend(entry.__dict__ for entry in region_scalar)
        alignment.append(
            compare_scalar_interface(
                region_id=row["region_id"],
                case_id=row["case_id"],
                optimization=row["optimization"],
                source_type=row["source_type"],
                scalar_rows=region_scalar,
                input_buses=input_buses,
                output_buses=output_buses,
            )
        )
        if row["case_id"] not in seen_bus_cases:
            bus_rows = normalize_bus_metadata(row["case_id"], input_buses, output_buses)
            bus_csv.extend(bus.to_csv_row() for bus in bus_rows)
            bus_json.extend(bus.__dict__ for bus in bus_rows)
            seen_bus_cases.add(row["case_id"])
    return scalar_csv, scalar_json, bus_csv, bus_json, alignment


def write_interface_outputs() -> None:
    scalar_csv, scalar_json, bus_csv, bus_json, alignment = extract_interfaces()
    write_csv(scalar_csv, RESULT_DIR / "semantic_scalar_interfaces.csv", SEMANTIC_SCALAR_INTERFACE_FIELDS)
    write_json(scalar_json, RESULT_DIR / "semantic_scalar_interfaces.json")
    write_csv(bus_csv, RESULT_DIR / "semantic_bus_ground_truth.csv", SEMANTIC_BUS_GROUND_TRUTH_FIELDS)
    write_json(bus_json, RESULT_DIR / "semantic_bus_ground_truth.json")
    write_csv(alignment, RESULT_DIR / "semantic_interface_alignment.csv", SEMANTIC_INTERFACE_ALIGNMENT_FIELDS)


SOURCE_COMPARISON_FIELDS = [
    "case_id",
    "optimization",
    "ground_truth_region_nodes",
    "output_cone_region_nodes",
    "region_node_delta",
    "region_overlap",
    "jaccard_similarity",
    "boundary_input_delta",
    "boundary_output_delta",
    "whole_output_cone_extra_nodes",
    "whole_output_cone_missing_nodes",
    "same_scalar_interface",
    "same_observable_outputs",
]


def compare_region_sources() -> list[dict[str, str]]:
    rows = [row for row in load_regions_from_csv() if row["eligible"] == "true"]
    by_key = {(row["case_id"], row["optimization"], row["source_type"]): row for row in rows}
    interface_rows = read_csv(RESULT_DIR / "semantic_scalar_interfaces.csv")
    iface_by_region: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for row in interface_rows:
        iface_by_region[row["region_id"]].append((row["direction"], row["raw_node_name"]))
    out: list[dict[str, str]] = []
    for (case_id, opt, source_type), gt in sorted(by_key.items()):
        if source_type != "ground_truth_region":
            continue
        cone = by_key.get((case_id, opt, "whole_output_cone"))
        if not cone:
            continue
        gt_nodes = set(json.loads(gt["region_nodes"]))
        cone_nodes = set(json.loads(cone["region_nodes"]))
        gt_bi = set(json.loads(gt["boundary_inputs"]))
        cone_bi = set(json.loads(cone["boundary_inputs"]))
        gt_bo = set(json.loads(gt["boundary_outputs"]))
        cone_bo = set(json.loads(cone["boundary_outputs"]))
        union = gt_nodes | cone_nodes
        inter = gt_nodes & cone_nodes
        out.append(
            {
                "case_id": case_id,
                "optimization": opt,
                "ground_truth_region_nodes": str(len(gt_nodes)),
                "output_cone_region_nodes": str(len(cone_nodes)),
                "region_node_delta": str(len(cone_nodes) - len(gt_nodes)),
                "region_overlap": str(len(inter)),
                "jaccard_similarity": f"{(len(inter) / max(1, len(union))):.6f}",
                "boundary_input_delta": str(len(cone_bi) - len(gt_bi)),
                "boundary_output_delta": str(len(cone_bo) - len(gt_bo)),
                "whole_output_cone_extra_nodes": json.dumps(sorted(cone_nodes - gt_nodes), separators=(",", ":")),
                "whole_output_cone_missing_nodes": json.dumps(sorted(gt_nodes - cone_nodes), separators=(",", ":")),
                "same_scalar_interface": str(iface_by_region[gt["region_id"]] == iface_by_region[cone["region_id"]]).lower(),
                "same_observable_outputs": str(gt["observable_outputs"] == cone["observable_outputs"]).lower(),
            }
        )
    write_csv(out, RESULT_DIR / "semantic_region_source_comparison.csv", SOURCE_COMPARISON_FIELDS)
    return out


BY_OPT_FIELDS = [
    "optimization",
    "available_cases",
    "valid_regions",
    "exact_scalar_interface_matches",
    "mean_region_size",
    "mean_boundary_size",
    "whole_design_output_cones",
    "alignment_failures",
    "skips",
]


FAILURE_FIELDS = ["region_id", "case_id", "optimization", "source_type", "status", "skip_reason"]


def summarize_regions() -> None:
    regions = load_regions_from_csv()
    alignment = read_csv(RESULT_DIR / "semantic_interface_alignment.csv") if (RESULT_DIR / "semantic_interface_alignment.csv").exists() else []
    validations = {row["region_id"]: row for row in read_csv(RESULT_DIR / "semantic_region_validation.csv")}
    align_by_region = {row["region_id"]: row for row in alignment}
    by_opt: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in regions:
        by_opt[row["optimization"]].append(row)
    opt_rows: list[dict[str, str]] = []
    for opt, rows in sorted(by_opt.items()):
        valid = [r for r in rows if r["eligible"] == "true"]
        available_variant_cases = {
            r["case_id"]
            for r in rows
            if r["source_type"] == "whole_output_cone" and r["circuit_available"] == "true"
        }
        sizes = [len(json.loads(r["region_nodes"])) for r in valid]
        boundary = [len(json.loads(r["boundary_inputs"])) + len(json.loads(r["boundary_outputs"])) for r in valid]
        opt_rows.append(
            {
                "optimization": opt,
                "available_cases": str(len(available_variant_cases)),
                "valid_regions": str(len(valid)),
                "exact_scalar_interface_matches": str(sum(1 for r in valid if align_by_region.get(r["region_id"], {}).get("exact_scalar_interface_match") == "true")),
                "mean_region_size": f"{sum(sizes) / max(1, len(sizes)):.3f}",
                "mean_boundary_size": f"{sum(boundary) / max(1, len(boundary)):.3f}",
                "whole_design_output_cones": str(sum(1 for r in valid if r["source_type"] == "whole_output_cone" and validations.get(r["region_id"], {}).get("whole_design_region") == "true")),
                "alignment_failures": str(sum(1 for r in rows if r["status"] == "alignment_failure")),
                "skips": str(sum(1 for r in rows if r["status"] in {"infrastructure_skip", "unsupported_case"})),
            }
        )
    write_csv(opt_rows, RESULT_DIR / "semantic_region_by_optimization.csv", BY_OPT_FIELDS)
    failure_rows = [
        {field: row[field] for field in FAILURE_FIELDS}
        for row in regions
        if row["eligible"] != "true"
    ]
    write_csv(failure_rows, RESULT_DIR / "semantic_region_failures.csv", FAILURE_FIELDS)
    write_summary(regions, alignment, validations, opt_rows)


def write_summary(regions: list[dict[str, str]], alignment: list[dict[str, str]], validations: dict[str, dict[str, str]], opt_rows: list[dict[str, str]]) -> None:
    declared_cases = len({row["case_id"] for row in regions})
    available_variants = len(
        {
            (row["case_id"], row["optimization"])
            for row in regions
            if row["source_type"] == "whole_output_cone" and row["circuit_available"] == "true"
        }
    )
    eligible = [row for row in regions if row["eligible"] == "true"]
    gt_valid = [row for row in eligible if row["source_type"] == "ground_truth_region"]
    cone_valid = [row for row in eligible if row["source_type"] == "whole_output_cone"]
    status_counts = Counter(row["status"] for row in regions)
    exact_matches = [row for row in alignment if row["exact_scalar_interface_match"] == "true"]
    def avg(field: str) -> float:
        vals = [float(row[field]) for row in alignment] if alignment else []
        return sum(vals) / max(1, len(vals))
    gt_sizes = [len(json.loads(row["region_nodes"])) for row in gt_valid]
    cone_sizes = [len(json.loads(row["region_nodes"])) for row in cone_valid]
    comparison = read_csv(RESULT_DIR / "semantic_region_source_comparison.csv") if (RESULT_DIR / "semantic_region_source_comparison.csv").exists() else []
    jaccards = [float(row["jaccard_similarity"]) for row in comparison]
    comparison_gt_sizes = [int(row["ground_truth_region_nodes"]) for row in comparison]
    comparison_cone_sizes = [int(row["output_cone_region_nodes"]) for row in comparison]
    whole_cones = sum(1 for row in cone_valid if validations.get(row["region_id"], {}).get("whole_design_region") == "true")
    by_family = Counter(row["family"] for row in eligible)
    lines = [
        "# Semantic Regions and Interfaces",
        "",
        "This phase establishes canonical regions, boundaries, scalar interfaces, and ground-truth interface alignment. It does not infer or recover high-level RTL expressions.",
        "",
        "## Funnel",
        "",
        f"- Declared benchmark cases: {declared_cases}",
        f"- Available circuit variants: {available_variants}",
        f"- Eligible region rows: {len(eligible)}",
        f"- Valid ground-truth regions: {len(gt_valid)}",
        f"- Valid whole-output-cone regions: {len(cone_valid)}",
        f"- Infrastructure skips: {status_counts.get('infrastructure_skip', 0)}",
        f"- Unsupported rows: {status_counts.get('unsupported_case', 0)}",
        f"- Invalid regions: {status_counts.get('invalid_region', 0)}",
        "",
        "## Scalar Interface",
        "",
        f"- Exact scalar-interface matches: {len(exact_matches)} / {len(alignment)}",
        f"- Mean input precision: {avg('input_bit_precision'):.3f}",
        f"- Mean input recall: {avg('input_bit_recall'):.3f}",
        f"- Mean output precision: {avg('output_bit_precision'):.3f}",
        f"- Mean output recall: {avg('output_bit_recall'):.3f}",
        f"- Mean input order accuracy: {avg('input_order_accuracy'):.3f}",
        f"- Mean output order accuracy: {avg('output_order_accuracy'):.3f}",
        "",
        "## Region Source Comparison",
        "",
        f"- Comparable ground-truth/output-cone pairs: {len(comparison)}",
        f"- Mean comparable ground-truth region size: {sum(comparison_gt_sizes) / max(1, len(comparison_gt_sizes)):.3f}",
        f"- Mean comparable output-cone region size: {sum(comparison_cone_sizes) / max(1, len(comparison_cone_sizes)):.3f}",
        f"- Mean Jaccard overlap: {sum(jaccards) / max(1, len(jaccards)):.3f}",
        f"- Mean valid ground-truth region size: {sum(gt_sizes) / max(1, len(gt_sizes)):.3f}",
        f"- Mean valid output-cone region size across all variants: {sum(cone_sizes) / max(1, len(cone_sizes)):.3f}",
        f"- Whole-design output-cone count: {whole_cones}",
        "",
        "## Valid Regions by Family",
        "",
        "| Family | Valid rows |",
        "| --- | ---: |",
    ]
    for family, count in sorted(by_family.items()):
        lines.append(f"| {family} | {count} |")
    lines.extend(["", "## Results by Optimization", "", "| Optimization | Available | Valid | Exact interface | Whole-design output cones | Skips |", "| --- | ---: | ---: | ---: | ---: | ---: |"])
    for row in opt_rows:
        lines.append(f"| {row['optimization']} | {row['available_cases']} | {row['valid_regions']} | {row['exact_scalar_interface_matches']} | {row['whole_design_output_cones']} | {row['skips']} |")
    lines.extend(["", "## Limitation", "", "No row in this phase represents recovered RTL. Region and interface extraction only prepares the substrate for later semantic inference.", ""])
    (RESULT_DIR / "semantic_region_summary.md").write_text("\n".join(lines), encoding="utf-8")


def run_all_no_plots() -> None:
    regions, validations = build_regions()
    write_region_outputs(regions, validations)
    write_interface_outputs()
    compare_region_sources()
    summarize_regions()
