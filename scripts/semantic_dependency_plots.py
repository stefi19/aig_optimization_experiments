#!/usr/bin/env python3
"""Generate plots for semantic bus inference and dependency geometry."""

from __future__ import annotations

import csv
import json
import re
import shutil
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
RESULT = ROOT / "results" / "semantic_recovery"
PLOT_DIR = ROOT / "results" / "plots"
ASSET_DIR = ROOT / "docs" / "presentation" / "assets" / "plots"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def save(fig, name: str) -> None:
    PLOT_DIR.mkdir(parents=True, exist_ok=True)
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    path = PLOT_DIR / name
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    shutil.copyfile(path, ASSET_DIR / name)


def bar(labels: list[str], values: list[float], title: str, ylabel: str, name: str, *, color: str = "#4c78a8") -> None:
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.bar(labels, values, color=color)
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    ax.tick_params(axis="x", rotation=30)
    save(fig, name)


def heatmap(matrix: list[list[float]], title: str, name: str) -> None:
    fig, ax = plt.subplots(figsize=(5.5, 4.5))
    image = ax.imshow(matrix, aspect="auto", cmap="viridis", vmin=0, vmax=1)
    ax.set_title(title)
    ax.set_xlabel("Scalar inputs")
    ax.set_ylabel("Scalar outputs")
    fig.colorbar(image, ax=ax, fraction=0.046, pad=0.04)
    save(fig, name)


def metric(row: dict[str, str], key: str) -> float:
    try:
        return float(row.get(key, 0.0))
    except ValueError:
        return 0.0


def main() -> int:
    regions = {row["region_id"]: row for row in read_csv(RESULT / "semantic_regions.csv")}
    bus_eval = read_csv(RESULT / "semantic_bus_evaluation.csv")
    bus_ablation = read_csv(RESULT / "semantic_bus_ablation.csv")
    family_eval = read_csv(RESULT / "semantic_family_evaluation.csv")
    family_ablation = read_csv(RESULT / "semantic_family_ablation.csv")
    features = read_csv(RESULT / "semantic_dependency_features.csv")
    confusion = read_csv(RESULT / "semantic_family_confusion_matrix.csv")
    matrices = json.loads((RESULT / "semantic_dependency_matrices.json").read_text(encoding="utf-8"))

    eligible = [row for row in regions.values() if row["eligible"] == "true"]
    hypotheses = read_csv(RESULT / "semantic_bus_hypotheses.csv")
    bar(
        ["eligible regions", "direction rows", "hypotheses", "dependency matrices"],
        [len(eligible), len(bus_eval), len(hypotheses), len(features)],
        "Semantic bus/dependency pipeline funnel",
        "Rows",
        "semantic_bus_inference_funnel.png",
    )

    bar(
        ["top-1", "top-3", "top-5"],
        [
            sum(1 for row in bus_eval if row["top_1_bus_match"] == "true") / max(1, len(bus_eval)),
            sum(1 for row in bus_eval if row["top_3_bus_match"] == "true") / max(1, len(bus_eval)),
            sum(1 for row in bus_eval if row["top_5_bus_match"] == "true") / max(1, len(bus_eval)),
        ],
        "Bus hypothesis match rate",
        "Rate",
        "semantic_bus_topk_match.png",
        color="#59a14f",
    )

    by_family: dict[str, list[float]] = defaultdict(list)
    for row in bus_eval:
        by_family[regions[row["region_id"]]["family"]].append(1.0 if row["top_1_bus_match"] == "true" else 0.0)
    bar(sorted(by_family), [sum(by_family[k]) / len(by_family[k]) for k in sorted(by_family)], "Top-1 bus match by family", "Rate", "semantic_bus_accuracy_by_family.png")

    def case_width(case_id: str) -> int:
        match = re.search(r"_w(\d+)$", case_id)
        return int(match.group(1)) if match else 0

    width_by_case = {row["case_id"]: case_width(row["case_id"]) for row in regions.values()}
    by_width: dict[str, list[float]] = defaultdict(list)
    for row in bus_eval:
        width = str(width_by_case.get(row["case_id"], 0))
        by_width[width].append(metric(row, "bit_order_accuracy"))
    bar(sorted(by_width, key=lambda x: int(x)), [sum(by_width[k]) / len(by_width[k]) for k in sorted(by_width, key=lambda x: int(x))], "Bit-order accuracy by width", "Accuracy", "semantic_bit_order_accuracy_by_width.png")

    roles = read_csv(RESULT / "semantic_input_roles.csv")
    role_counter = Counter((row["ground_truth_role"], row["predicted_role"]) for row in roles)
    labels = [f"{truth}->{pred}" for truth, pred in sorted(role_counter)]
    bar(labels[:20], [role_counter[tuple(label.split("->"))] for label in labels[:20]], "Control/data role classifications", "Nodes", "semantic_control_data_classification.png", color="#f28e2b")

    representative = {row["region_id"]: row for row in matrices}
    if matrices:
        heatmap(matrices[0]["D_structural"], "Structural dependency example", "semantic_dependency_matrix_structural_example.png")
        heatmap(matrices[0]["D_simulated"], "Sampled simulation dependency example", "semantic_dependency_matrix_simulation_example.png")
    for family, name in (
        ("arithmetic", "semantic_dependency_adder_geometry.png"),
        ("arithmetic", "semantic_dependency_multiplier_geometry.png"),
        ("control", "semantic_dependency_mux_comparator_geometry.png"),
    ):
        chosen = next((row for row in matrices if regions.get(row["region_id"], {}).get("family") == family), matrices[0] if matrices else None)
        if chosen:
            heatmap(chosen["D_structural"], f"{family.title()} structural dependency", name)

    truth_labels = sorted({row["ground_truth_family"] for row in confusion} | {row["predicted_family"] for row in confusion})
    index = {label: i for i, label in enumerate(truth_labels)}
    matrix = [[0 for _ in truth_labels] for _ in truth_labels]
    for row in confusion:
        matrix[index[row["ground_truth_family"]]][index[row["predicted_family"]]] = int(row["count"])
    fig, ax = plt.subplots(figsize=(7, 6))
    ax.imshow(matrix, cmap="Blues")
    ax.set_xticks(range(len(truth_labels)), truth_labels, rotation=45, ha="right")
    ax.set_yticks(range(len(truth_labels)), truth_labels)
    ax.set_title("Semantic family top-1 confusion matrix")
    save(fig, "semantic_family_confusion_matrix.png")

    family_overall = next(row for row in family_eval if row["scope"] == "overall")
    by_opt = [row for row in family_eval if row["scope"] == "optimization"]
    bar([row["group"] for row in by_opt], [metric(row, "top_1_family_accuracy") for row in by_opt], "Family ranking by optimization", "Top-1 accuracy", "semantic_family_by_optimization.png", color="#9c755f")

    bar([row["feature_mode"] for row in bus_ablation], [metric(row, "top_1_bus_match_rate") for row in bus_ablation], "Bus inference ablation", "Top-1 bus match", "semantic_bus_ablation.png", color="#76b7b2")
    bar([row["feature_mode"] for row in family_ablation], [metric(row, "top_1_family_accuracy") for row in family_ablation], f"Family ablation (overall top-1 {family_overall['top_1_family_accuracy']})", "Top-1 family accuracy", "semantic_family_ablation.png", color="#b07aa1")

    opt_features: dict[str, list[float]] = defaultdict(list)
    for row in features:
        opt_features[row["optimization"]].append(metric(row, "dependency_density"))
    bar(sorted(opt_features), [sum(opt_features[k]) / len(opt_features[k]) for k in sorted(opt_features)], "Dependency density by optimization", "Mean density", "semantic_dependency_drift_by_optimization.png")

    fig, ax = plt.subplots(figsize=(6.5, 4.5))
    ax.scatter([metric(row, "input_count") * metric(row, "output_count") for row in features], [metric(row, "runtime_seconds") for row in features], s=12, alpha=0.6)
    ax.set_title("Dependency runtime vs matrix size")
    ax.set_xlabel("Input count x output count")
    ax.set_ylabel("Runtime seconds")
    save(fig, "semantic_dependency_runtime_vs_region_size.png")

    by_source: dict[str, list[float]] = defaultdict(list)
    for row in hypotheses:
        by_source[regions[row["region_id"]]["source_type"]].append(float(row["ambiguity_count"]))
    bar(sorted(by_source), [sum(by_source[k]) / len(by_source[k]) for k in sorted(by_source)], "Bus-order ambiguity by region source", "Mean ambiguity", "semantic_ambiguity_by_region_source.png")

    print("Semantic bus/dependency plots written to results/plots and presentation assets")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
