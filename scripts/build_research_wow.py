#!/usr/bin/env python3
"""Build research-facing derived artifacts from committed evidence tables."""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "research_wow"
PAPER = ROOT / "paper"
SCHEMA = "research_wow_v1"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    (PAPER / "figures").mkdir(parents=True, exist_ok=True)
    (PAPER / "tables").mkdir(parents=True, exist_ok=True)
    (PAPER / "case_studies").mkdir(parents=True, exist_ok=True)

    frontier = build_recoverability_frontier()
    taxonomy = build_failure_taxonomy()
    ablations = build_ablation_summary()
    baselines = build_baseline_summary()
    demo = build_demo_trace()

    write_csv(OUT / "recoverability_frontier.csv", frontier)
    write_csv(OUT / "failure_taxonomy.csv", taxonomy)
    write_csv(OUT / "ablation_summary.csv", ablations)
    write_csv(OUT / "baseline_summary.csv", baselines)
    write_csv(OUT / "demo_trace.csv", demo)
    write_recoverability_figure(frontier)
    write_paper_figures(frontier, taxonomy, demo)
    write_markdown_outputs(frontier, taxonomy, ablations, baselines, demo)
    print(f"Wrote research-wow artifacts to {OUT.relative_to(ROOT)} and {PAPER.relative_to(ROOT)}")
    return 0


def build_recoverability_frontier() -> list[dict[str, str]]:
    active = rows("results/active_source_counterpart_refactoring/controlled_results.csv")
    cross = rows("results/cross_netlist_cut_transplantation/controlled_results.csv")
    blind_summary = rows("results/blind_semantic_cegis/blind_semantic_recovery_summary.csv")
    necessity = rows("results/necessity_first_target_discovery/eligible_target_manifest.csv")
    necessity_locality = rows("results/necessity_first_target_discovery/formal_locality_results.csv")
    necessity_rewrites = rows("results/necessity_first_target_discovery/graph_rewrites.csv")
    necessity_boundary = rows("results/necessity_first_target_discovery/boundary_recovery.csv")
    historical = rows("results/cross_netlist_cut_transplantation/development_results.csv")
    locality_development = rows("results/formal_locality_barriers/development_results.csv")
    locality_exact = rows("results/formal_locality_barriers/input_exact_minimum_certificates.csv")

    blind = next((r for r in blind_summary if r.get("mode") == "blind_parametric_cegis"), {})
    return [
        frontier_row(
            "controlled_active_source_counterparts",
            "controlled_generated_blif",
            count(active, "expected_outcome", prefix="positive"),
            count(active, "final_status", equals="accepted"),
            "accepted graph-active counterpart rewrites",
            "formal_exhaustive_plus_abc_cec",
            "results/active_source_counterpart_refactoring/controlled_results.csv",
        ),
        frontier_row(
            "controlled_cross_netlist_transplants",
            "controlled_generated_blif",
            count(cross, "expected_outcome", prefix="positive"),
            count(cross, "final_status", equals="accepted"),
            "accepted cross-netlist transplants",
            "formal_exhaustive_plus_abc_cec",
            "results/cross_netlist_cut_transplantation/controlled_results.csv",
        ),
        frontier_row(
            "blind_parametric_cegis",
            "blind_generated_blif",
            int(blind.get("regions", "0") or 0),
            int(blind.get("verified_regions", "0") or 0),
            "formally verified blind regions",
            "formal_exhaustive",
            "results/blind_semantic_cegis/blind_semantic_recovery_summary.csv",
        ),
        frontier_row(
            "necessity_first_compact_interfaces",
            "generated_research_benchmark",
            len(necessity),
            count(necessity_locality, "compact_interface", equals="true"),
            "compact exact input interfaces",
            "exact_minimum_certificate",
            "results/necessity_first_target_discovery/formal_locality_results.csv",
        ),
        frontier_row(
            "necessity_first_graph_rewrites",
            "generated_research_benchmark",
            len(necessity),
            count(necessity_boundary, "new_boundary", equals="true"),
            "graph-active CEC-backed interface rewrites",
            "truth_table_plus_fanout_frontier_rewrite_plus_abc_cec",
            "results/necessity_first_target_discovery/boundary_recovery.csv",
        ),
        frontier_row(
            "formal_locality_previous_failures",
            "historical_diagnostic",
            len(locality_development),
            len(locality_exact),
            "exact input minima for previous failures",
            "exact_minimum_certificate_diagnostic",
            "results/formal_locality_barriers/input_exact_minimum_certificates.csv",
        ),
        frontier_row(
            "historical_cross_netlist_recovery",
            "historical_ineligible_diagnostic",
            len(historical),
            count(historical, "new_recovered_boundary", equals="true"),
            "real historical graph-active recoveries",
            "corrected_denominator_audit",
            "results/cross_netlist_cut_transplantation/development_results.csv",
        ),
    ]


def build_failure_taxonomy() -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    recon = rows("results/provenance_eligibility_audit/provenance_reconstruction.csv")
    recon_counts = Counter(r.get("reconstruction_status", "") for r in recon)
    necessity_locality = rows("results/necessity_first_target_discovery/formal_locality_results.csv")
    necessity_rewrites = rows("results/necessity_first_target_discovery/graph_rewrites.csv")
    blind_failure = rows("results/blind_semantic_cegis/failure_taxonomy.csv")

    add_failure(
        out,
        "missing_optimized_artifact",
        "Historical row lacks a usable optimized artifact for proof replay.",
        recon_counts.get("missing_optimized_artifact", 0),
        "historical_ineligible_diagnostic",
        "results/provenance_eligibility_audit/provenance_reconstruction.csv",
        example_value(recon, "target_id", lambda r: r.get("reconstruction_status") == "missing_optimized_artifact"),
        "Historical rows cannot support transplantation or recovery claims.",
    )
    add_failure(
        out,
        "historical_target_irrelevant_after_reconstruction",
        "Historical artifact can be reconstructed but the selected target is not necessary for the audited interface.",
        recon_counts.get("provenance_reconstructed_exact", 0),
        "historical_diagnostic",
        "results/provenance_eligibility_audit/provenance_reconstruction.csv",
        example_value(recon, "target_id", lambda r: r.get("reconstruction_status") == "provenance_reconstructed_exact"),
        "The corrected historical eligible transplantation denominator remains zero.",
    )
    add_failure(
        out,
        "non_compact_exact_input_interface",
        "A target passes necessity filtering but the exact input interface exceeds the compact bound.",
        sum(r.get("compact_interface") != "true" for r in necessity_locality),
        "generated_research_benchmark",
        "results/necessity_first_target_discovery/formal_locality_results.csv",
        example_value(necessity_locality, "stable_target_id", lambda r: r.get("compact_interface") != "true"),
        "Locality, not solver soundness, blocks many generated targets.",
    )
    add_failure(
        out,
        "no_validated_graph_rewrite_artifact",
        "A target is auditable but no rewrite artifact is emitted.",
        sum(r.get("rewrite_emitted") != "true" for r in necessity_rewrites),
        "generated_research_benchmark",
        "results/necessity_first_target_discovery/graph_rewrites.csv",
        example_value(necessity_rewrites, "stable_target_id", lambda r: r.get("rewrite_emitted") != "true"),
        "Non-compact interfaces still block the bounded rewrite language.",
    )
    add_failure(
        out,
        "rewrite_artifact_not_graph_active",
        "A compact-interface rewrite artifact is emitted and CEC-equivalent but remains identical or otherwise non-active under the bounded rewrite language.",
        sum(r.get("rewrite_emitted") == "true" and r.get("graph_active") != "true" for r in necessity_rewrites),
        "generated_research_benchmark",
        "results/necessity_first_target_discovery/graph_rewrites.csv",
        example_value(necessity_rewrites, "stable_target_id", lambda r: r.get("rewrite_emitted") == "true" and r.get("graph_active") != "true"),
        "Artifact emission is kept separate from constructive boundary recovery.",
    )

    append_family_failures(
        out,
        "active_source_counterpart",
        "results/active_source_counterpart_refactoring/failure_taxonomy.csv",
        "benchmark_group",
        "failure_stage",
        "failure_reason",
    )
    append_family_failures(
        out,
        "cross_netlist_transplant",
        "results/cross_netlist_cut_transplantation/failure_taxonomy.csv",
        "benchmark_group",
        "failure_stage",
        "failure_reason",
    )
    append_family_failures(
        out,
        "formal_locality_barrier",
        "results/formal_locality_barriers/failure_taxonomy.csv",
        "failure_group",
        "classification",
        "classification",
    )

    blind_counts = Counter((r.get("stage", ""), r.get("reason", "")) for r in blind_failure)
    for (stage, reason), n in sorted(blind_counts.items()):
        add_failure(
            out,
            f"blind_cegis::{stage}::{reason}",
            "Blind CEGIS exhausted the bounded candidate family after adding counterexamples.",
            n,
            "blind_generated_blif",
            "results/blind_semantic_cegis/failure_taxonomy.csv",
            example_value(blind_failure, "region_id", lambda r, s=stage, rr=reason: r.get("stage") == s and r.get("reason") == rr),
            "Blind success rates must be reported separately from oracle and controlled settings.",
        )
    return out


def build_ablation_summary() -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    append_ablations(out, "active_source_counterpart", "results/active_source_counterpart_refactoring/ablations.csv", "ablation", "attempted", "new_boundaries", "new boundaries")
    append_ablations(out, "cross_netlist_transplant", "results/cross_netlist_cut_transplantation/ablations.csv", "ablation", "attempted", "new_boundaries", "new boundaries")
    append_ablations(out, "formal_locality_barrier", "results/formal_locality_barriers/ablations.csv", "ablation", "targets", "successes", "exact minima")
    topk = rows("results/ablation_summary.csv")
    by_config: dict[str, list[float]] = {}
    for row in topk:
        by_config.setdefault(row.get("config", ""), []).append(float(row.get("rank1_precision", "0") or 0))
    for config, values in sorted(by_config.items()):
        out.append(
            {
                "experiment_family": "ranking_baseline",
                "ablation": config,
                "denominator": str(len(values)),
                "success_count": f"{sum(values):.6f}",
                "success_metric": "mean rank-1 precision",
                "success_rate": f"{(sum(values) / len(values)) if values else 0:.6f}",
                "notes": "Derived from results/ablation_summary.csv.",
                "schema_version": SCHEMA,
            }
        )
    return out


def build_baseline_summary() -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    append_baselines(out, "active_source_counterpart", "results/active_source_counterpart_refactoring/baselines.csv", "baseline", "attempted", "new_boundaries", "new boundaries")
    append_baselines(out, "cross_netlist_transplant", "results/cross_netlist_cut_transplantation/baselines.csv", "baseline", "attempted", "new_boundaries", "new boundaries")
    append_baselines(out, "formal_locality_barrier", "results/formal_locality_barriers/baselines.csv", "baseline", "targets", "successes", "successes")
    return out


def build_demo_trace() -> list[dict[str, str]]:
    active = rows("results/active_source_counterpart_refactoring/controlled_results.csv")
    accepted = next(r for r in active if r.get("final_status") == "accepted")
    benchmark = accepted["benchmark"]
    cid = f"{benchmark}__active_source_counterpart"
    cegis = rows("results/blind_semantic_cegis/cegis_iterations.csv")
    refined_region = "arithmetic_add_add_w2__identity__ground_truth_region"
    refinement_rows = [r for r in cegis if r.get("region_id") == refined_region]
    proof = next(r for r in rows("results/blind_semantic_cegis/formal_proofs.csv") if r.get("formal_status") == "formally_verified_region")

    trace = [
        demo_row("controlled", "select graph-active source counterpart", benchmark, cid, accepted["counterpart_proof_status"], "formal_exhaustive", "results/active_source_counterpart_refactoring/counterpart_proofs.csv"),
        demo_row("controlled", "decompose source window", benchmark, cid, accepted["decomposition_status"], "formal_exhaustive", "results/active_source_counterpart_refactoring/decomposition_queries.csv"),
        demo_row("controlled", "synthesize quotient", benchmark, cid, accepted["quotient_status"], "truth_table_synthesis", "results/active_source_counterpart_refactoring/quotient_synthesis.csv"),
        demo_row("controlled", "prove global source and cross equivalence", benchmark, cid, accepted["source_cec_status"] + "/" + accepted["cross_cec_status"], "abc_cec", "results/active_source_counterpart_refactoring/global_cec.csv"),
    ]
    for row in refinement_rows:
        trace.append(
            demo_row(
                "blind",
                f"cegis iteration {row['iteration']}",
                row["region_id"],
                row.get("candidate_id") or "bounded_candidate_set",
                row["termination_reason"],
                "counterexample_refinement" if row["solver_status"] == "sat" else "bounded_exhaustion",
                "results/blind_semantic_cegis/cegis_iterations.csv",
                f"examples {row['examples_before']} -> {row['examples_after']}; solver={row['solver_status']}",
            )
        )
    trace.append(demo_row("blind", "verified positive blind control", proof["region_id"], proof["candidate_id"], proof["formal_status"], proof["formal_evidence_level"], "results/blind_semantic_cegis/formal_proofs.csv"))
    return trace


def write_recoverability_figure(frontier: list[dict[str, str]]) -> None:
    labels = [r["result_family"].replace("_", "\n") for r in frontier]
    rates = [float(r["success_rate"]) for r in frontier]
    colors = ["#1f77b4", "#2ca02c", "#9467bd", "#17becf", "#d62728", "#8c564b", "#7f7f7f"]
    fig, ax = plt.subplots(figsize=(10.5, 4.6))
    ax.bar(labels, rates, color=colors[: len(labels)])
    ax.set_ylabel("success / denominator")
    ax.set_ylim(0, 1.05)
    ax.set_title("Recoverability frontier by evidence class")
    ax.grid(axis="y", linewidth=0.4, alpha=0.35)
    for i, row in enumerate(frontier):
        ax.text(i, min(1.02, rates[i] + 0.03), f"{row['success_count']}/{row['denominator']}", ha="center", va="bottom", fontsize=8)
    fig.tight_layout()
    for path in [OUT / "recoverability_frontier.png", PAPER / "figures" / "recoverability_frontier.png"]:
        fig.savefig(path, dpi=180)
    plt.close(fig)


def write_paper_figures(
    frontier: list[dict[str, str]],
    taxonomy: list[dict[str, str]],
    demo: list[dict[str, str]],
) -> None:
    write_hierarchy_figure()
    write_pipeline_figure()
    write_failure_taxonomy_figure(taxonomy)
    write_case_study_trace_figure(demo)
    write_problem_figure()
    write_interface_ablation_figure()


def save_figure(fig: plt.Figure, name: str) -> None:
    for path in [OUT / name, PAPER / "figures" / name]:
        fig.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(fig)


def write_problem_figure() -> None:
    fig, ax = plt.subplots(figsize=(9.5, 3.4))
    ax.axis("off")
    boxes = [
        (0.05, 0.55, "Source AIG\nnamed internal nodes", "#dbeafe"),
        (0.39, 0.55, "ABC optimization\nrewrite / refactor / resyn", "#fef3c7"),
        (0.73, 0.55, "Optimized AIG\nnew local structure", "#dcfce7"),
        (0.05, 0.12, "Whole-design CEC\npasses", "#e0e7ff"),
        (0.39, 0.12, "Internal mapping\nis underdetermined", "#fee2e2"),
        (0.73, 0.12, "Recovery claim needs\nlocal proof + graph artifact", "#f3e8ff"),
    ]
    for x, y, text, color in boxes:
        ax.add_patch(plt.Rectangle((x, y), 0.22, 0.24, facecolor=color, edgecolor="#334155", linewidth=1.0))
        ax.text(x + 0.11, y + 0.12, text, ha="center", va="center", fontsize=10)
    for y in [0.67, 0.24]:
        ax.annotate("", xy=(0.37, y), xytext=(0.28, y), arrowprops=dict(arrowstyle="->", lw=1.2, color="#334155"))
        ax.annotate("", xy=(0.71, y), xytext=(0.62, y), arrowprops=dict(arrowstyle="->", lw=1.2, color="#334155"))
    ax.text(0.5, 0.93, "Motivating problem: equivalence does not imply internal recoverability", ha="center", fontsize=12, weight="bold")
    save_figure(fig, "motivating_problem.png")


def write_hierarchy_figure() -> None:
    stages = [
        ("Structural survivor", "same or complemented node"),
        ("Semantic recovery", "local function recovered"),
        ("Interface recovery", "adapters / relation proven"),
        ("Exact interface", "minimal local support certified"),
        ("Graph-active rewrite", "netlist changed at target"),
        ("Global CEC", "whole design preserved"),
    ]
    fig, ax = plt.subplots(figsize=(10.5, 3.2))
    ax.axis("off")
    xs = [0.035, 0.195, 0.355, 0.515, 0.675, 0.835]
    colors = ["#dbeafe", "#e0f2fe", "#ccfbf1", "#dcfce7", "#fef3c7", "#ede9fe"]
    for idx, ((title, subtitle), x) in enumerate(zip(stages, xs)):
        ax.add_patch(plt.Rectangle((x, 0.35), 0.125, 0.28, facecolor=colors[idx], edgecolor="#334155", linewidth=1.0))
        ax.text(x + 0.0625, 0.53, title, ha="center", va="center", fontsize=8.8, weight="bold")
        ax.text(x + 0.0625, 0.42, subtitle, ha="center", va="center", fontsize=7.7)
        if idx:
            ax.annotate("", xy=(x - 0.012, 0.49), xytext=(xs[idx - 1] + 0.137, 0.49), arrowprops=dict(arrowstyle="->", lw=1.0, color="#334155"))
    ax.text(0.5, 0.82, "Evidence hierarchy for internal correspondence recovery", ha="center", fontsize=12, weight="bold")
    ax.text(0.5, 0.18, "Rows are promoted only by additional evidence; interface language is a parameter of recoverability.", ha="center", fontsize=9)
    save_figure(fig, "recoverability_hierarchy.png")


def write_pipeline_figure() -> None:
    fig, ax = plt.subplots(figsize=(9.5, 4.0))
    ax.axis("off")
    rows_y = [0.72, 0.43, 0.14]
    labels = [
        ("Blind path", ["templates", "CEGIS", "formal proof"]),
        ("Controlled path", ["counterpart", "quotient", "ABC CEC"]),
        ("Audit path", ["provenance", "necessity", "locality"]),
    ]
    for y, (lane, steps) in zip(rows_y, labels):
        ax.text(0.05, y + 0.055, lane, ha="left", va="center", fontsize=10.5, weight="bold")
        for i, step in enumerate(steps):
            x = 0.27 + i * 0.22
            ax.add_patch(plt.Rectangle((x, y), 0.15, 0.12, facecolor="#f8fafc", edgecolor="#334155", linewidth=1.0))
            ax.text(x + 0.075, y + 0.06, step, ha="center", va="center", fontsize=9.5)
            if i:
                ax.annotate("", xy=(x - 0.015, y + 0.06), xytext=(x - 0.07, y + 0.06), arrowprops=dict(arrowstyle="->", lw=1.0, color="#334155"))
    ax.text(0.5, 0.93, "Methodology lanes and acceptance gates", ha="center", fontsize=12, weight="bold")
    ax.text(0.5, 0.03, "Only the controlled path reaches graph-active recovery in the current committed evidence; blind and audit paths bound what remains recoverable.", ha="center", fontsize=9)
    save_figure(fig, "methodology_pipeline.png")


def write_failure_taxonomy_figure(taxonomy: list[dict[str, str]]) -> None:
    top = sorted(taxonomy, key=lambda r: int(float(r["count"])), reverse=True)[:8]
    labels = [short_failure_label(r["failure_class"]) for r in top]
    counts = [int(float(r["count"])) for r in top]
    fig, ax = plt.subplots(figsize=(9.5, 4.0))
    y = list(range(len(top)))
    ax.barh(y, counts, color="#64748b")
    ax.set_yticks(y, labels=labels)
    ax.invert_yaxis()
    ax.set_xlabel("rows")
    ax.set_title("Dominant blocker classes in committed evidence")
    ax.grid(axis="x", linewidth=0.4, alpha=0.35)
    for yi, count_value in zip(y, counts):
        ax.text(count_value + 0.6, yi, str(count_value), va="center", fontsize=8.5)
    save_figure(fig, "failure_taxonomy.png")


def write_case_study_trace_figure(demo: list[dict[str, str]]) -> None:
    fig, ax = plt.subplots(figsize=(9.5, 3.6))
    ax.axis("off")
    controlled = [r for r in demo if r["mode"] == "controlled"]
    blind = [r for r in demo if r["mode"] == "blind"][:4]
    for y, title, rows_, color in [(0.62, "controlled positive", controlled, "#dcfce7"), (0.25, "blind bounded trace", blind, "#fee2e2")]:
        ax.text(0.04, y + 0.055, title, ha="left", va="center", fontsize=10, weight="bold")
        for idx, row in enumerate(rows_):
            x = 0.24 + idx * 0.17
            status = row["status"].replace("_", " ")
            label = row["stage"].replace("prove global source and cross equivalence", "global CEC")
            ax.add_patch(plt.Rectangle((x, y), 0.13, 0.13, facecolor=color, edgecolor="#334155", linewidth=1.0))
            ax.text(x + 0.065, y + 0.088, label, ha="center", va="center", fontsize=7.2)
            ax.text(x + 0.065, y + 0.035, status[:22], ha="center", va="center", fontsize=6.8)
            if idx:
                ax.annotate("", xy=(x - 0.012, y + 0.065), xytext=(x - 0.04, y + 0.065), arrowprops=dict(arrowstyle="->", lw=0.9, color="#334155"))
    ax.text(0.5, 0.91, "Representative trace: acceptance versus counterexample refinement", ha="center", fontsize=12, weight="bold")
    save_figure(fig, "case_study_trace.png")


def write_interface_ablation_figure() -> None:
    ablations = rows("results/cross_netlist_cut_transplantation/ablations.csv")
    wanted = ["direct_adapter_only", "relational_interface_enabled"]
    selected = [next(row for row in ablations if row["ablation"] == name) for name in wanted]
    labels = ["direct\nadapters", "relational\ninterfaces"]
    successes = [int(row["new_boundaries"]) for row in selected]
    graph_valid = [int(row["graph_valid_transplants"]) for row in selected]
    cec = [int(row["global_cec_passes"]) for row in selected]
    denom = int(selected[0]["attempted"])

    x = range(len(labels))
    fig, ax = plt.subplots(figsize=(6.8, 3.4))
    width = 0.24
    ax.bar([i - width for i in x], graph_valid, width=width, label="graph-valid", color="#93c5fd")
    ax.bar(list(x), cec, width=width, label="global CEC", color="#60a5fa")
    ax.bar([i + width for i in x], successes, width=width, label="new boundaries", color="#1d4ed8")
    ax.set_xticks(list(x), labels=labels)
    ax.set_ylim(0, denom + 1)
    ax.set_ylabel(f"successful rows out of {denom}")
    ax.set_title("Cross-netlist ablation: interface language changes recovery")
    ax.grid(axis="y", linewidth=0.4, alpha=0.35)
    for i, success in enumerate(successes):
        ax.text(i + width, success + 0.25, f"{success}/{denom}", ha="center", va="bottom", fontsize=9, weight="bold")
    ax.legend(loc="upper left", frameon=False, ncols=3)
    save_figure(fig, "interface_ablation.png")


def short_failure_label(label: str) -> str:
    pieces = label.split("::")
    tail = pieces[-1] if pieces else label
    replacements = {
        "no_validated_graph_rewrite_artifact": "no rewrite artifact",
        "missing_optimized_artifact": "missing optimized artifact",
        "no_globally_anchored_cut": "no anchored cut",
        "no_relevant_source_consumer_window_under_bounds": "no source window",
        "no_candidate_satisfies_examples": "blind CEGIS exhausted",
        "historical_target_irrelevant_after_reconstruction": "target irrelevant",
        "non_compact_exact_input_interface": "non-compact interface",
        "rewrite_artifact_not_graph_active": "non-active rewrite",
    }
    return replacements.get(tail, tail.replace("_", " ")[:34])


def write_markdown_outputs(
    frontier: list[dict[str, str]],
    taxonomy: list[dict[str, str]],
    ablations: list[dict[str, str]],
    baselines: list[dict[str, str]],
    demo: list[dict[str, str]],
) -> None:
    write_text(OUT / "demo_report.md", demo_report(demo))
    write_text(PAPER / "case_studies" / "counterpart_and_blind_cegis.md", case_study(demo))
    write_text(PAPER / "tables" / "research_wow_tables.md", paper_tables(frontier, taxonomy, ablations, baselines))
    write_text(PAPER / "claims_to_tables.md", claims_to_tables())
    write_text(PAPER / "outline.md", paper_outline())


def demo_report(demo: list[dict[str, str]]) -> str:
    return "\n".join(
        [
            "# Demo Wow Report",
            "",
            "This is a reviewer-safe mini-report derived only from committed evidence tables.",
            "",
            table(["mode", "stage", "subject", "status", "evidence_level"], demo),
            "",
            "Run `make demo-wow` to regenerate this report and print the same trace.",
            "",
        ]
    )


def case_study(demo: list[dict[str, str]]) -> str:
    return "\n".join(
        [
            "# Case Study: Proof-Carrying Counterparts and Blind CEGIS",
            "",
            "The controlled half of the case study demonstrates a graph-active source-side counterpart accepted only after local proof, quotient synthesis, and ABC CEC checks. The blind half shows counterexample-guided refinement adding concrete distinguishing assignments before the bounded candidate family is exhausted, plus a separate blind positive control with a formal proof.",
            "",
            table(["mode", "stage", "subject", "status", "evidence_level", "artifact"], demo),
            "",
            "Interpretation: controlled source access can support graph-active recovery, while blind bounded template search must report both verified regions and replayable negative traces.",
            "",
        ]
    )


def paper_tables(frontier: list[dict[str, str]], taxonomy: list[dict[str, str]], ablations: list[dict[str, str]], baselines: list[dict[str, str]]) -> str:
    top_taxonomy = sorted(taxonomy, key=lambda r: int(float(r["count"])), reverse=True)[:12]
    interface_ablation = [
        row
        for row in rows("results/cross_netlist_cut_transplantation/ablations.csv")
        if row["ablation"] in {"direct_adapter_only", "relational_interface_enabled"}
    ]
    return "\n".join(
        [
            "# Paper Tables",
            "",
            "## Recoverability Frontier",
            "",
            table(["result_family", "denominator_class", "success_count", "denominator", "success_rate", "evidence_level"], frontier),
            "",
            "## Cross-Netlist Interface Ablation",
            "",
            table(
                ["ablation", "new_boundaries", "attempted", "relational_interfaces", "graph_valid_transplants", "global_cec_passes"],
                interface_ablation,
            ),
            "",
            "## Top Failure Classes",
            "",
            table(["failure_class", "denominator_class", "count", "evidence_file", "implication"], top_taxonomy),
            "",
            "## Ablations",
            "",
            table(["experiment_family", "ablation", "success_count", "denominator", "success_rate", "success_metric"], ablations),
            "",
            "## Baselines",
            "",
            table(["experiment_family", "baseline", "success_count", "denominator", "success_rate", "success_metric"], baselines),
            "",
        ]
    )


def claims_to_tables() -> str:
    return """# Claims to Tables

| Paper claim | Primary table or figure | Evidence class | Checker |
|---|---|---|---|
| Aggressive logic synthesis preserves whole-design equivalence while eroding direct internal correspondences. | `results/sat_validation_layers_summary.csv`; `results/summary_metrics.csv` | structural and ABC CEC diagnostic | `python scripts/check_results_freshness.py` |
| Controlled source-side counterparts can be graph-active and CEC-backed. | `results/research_wow/recoverability_frontier.csv` | controlled generated BLIF | `python scripts/check_active_source_counterpart_results.py` |
| Cross-netlist transplantation succeeds on controlled positives but not historical diagnostic rows. | `results/research_wow/recoverability_frontier.csv` | controlled generated BLIF; historical diagnostic | `python scripts/check_cross_netlist_transplant_results.py` |
| In the controlled cross-netlist ablation, the admissible interface language changes the graph-active recovery set: direct adapters recover 9/17 new boundaries, while relational interfaces recover 12/17. | `results/cross_netlist_cut_transplantation/ablations.csv`; `paper/figures/interface_ablation.png` | controlled generated BLIF ablation | `python scripts/check_cross_netlist_transplant_results.py` |
| Blind CEGIS has both verified regions and replayable counterexample-refinement failures. | `results/blind_semantic_cegis/blind_semantic_recovery_summary.csv`; `results/research_wow/demo_trace.csv` | blind generated BLIF | `python scripts/check_blind_semantic_results.py` |
| Necessity-first generated targets separate exact interface existence, emitted rewrite artifacts, and graph-active CEC-backed boundary recovery. | `results/necessity_first_target_discovery/formal_locality_results.csv`; `results/necessity_first_target_discovery/graph_rewrites.csv`; `results/necessity_first_target_discovery/boundary_recovery.csv` | generated research benchmark | `python scripts/check_necessity_first_target_results.py` |
| Historical null results are explained by provenance and target-necessity audits, not by a 56-row eligible graph-rewrite denominator. | `results/provenance_eligibility_audit/provenance_reconstruction.csv`; `results/research_wow/failure_taxonomy.csv` | historical diagnostic | `python scripts/check_provenance_eligibility_results.py` |
| Evidence advancement moves rows only when extra obligations are present: source-blind graph-active 0/56, compact interface new boundaries 22/48, bounded grammar completeness 4/12, pinned RTL corpus 3/3, ODC graph-active placement 0/10, locality proof objects 57/57. | `results/evidence_advancement/evidence_advancement_summary.csv`; `results/evidence_advancement/locality_proof_objects.csv` | evidence-level advancement accounting | `python scripts/check_evidence_advancement.py` |
| The artifact's headline figure is generated from committed evidence and does not merge blind, oracle, controlled, generated, and historical denominators. | `paper/figures/recoverability_frontier.png`; `results/research_wow/recoverability_frontier.csv` | artifact-derived summary | `python scripts/check_research_wow.py` |
"""


def paper_outline() -> str:
    return """# Paper Outline

## Working Title

Recoverability Frontiers for Internal Correspondence After Logic Synthesis.

## Thesis

Internal correspondence after AIG optimization is not a single recovery problem. It is a hierarchy of evidence. Structural similarity, semantic region recognition, exact locality certificates, graph-active rewrites, and global CEC-backed transformations form distinct levels, and the current artifact shows where each level succeeds or fails under controlled, blind, generated, and historical diagnostic denominators.

The cross-netlist ablation refines the thesis: the frontier is parameterized by the admissible interface language. In the controlled experiment, direct adapters recover 9/17 new boundaries, while relational-interface-enabled transplantation recovers 12/17, showing that representation of the boundary can change constructive recoverability.

## Paper Structure

1. Abstract.
2. Introduction and contributions.
3. Background and related work.
4. Problem formulation and evidence model.
5. Framework and algorithms.
6. Experimental methodology.
7. Results by research question.
8. Case studies.
9. Discussion.
10. Threats to validity.
11. Future work.
12. Conclusion.

## Problem

Recovering internal correspondences after logic synthesis is useful for debugging, source mapping, and proof-carrying transformations, but aggressive optimization destroys simple name and structural evidence.

## Threat Model

All headline recovery claims must distinguish controlled generated BLIF, blind generated BLIF, standard netlist diagnostics, oracle diagnostics, historical ineligible rows, pinned RTL-source metadata, and future lowered RTL correspondence work.

## Method

1. Recover candidate internal semantic regions.
2. Refine candidates with counterexamples or exact certificates.
3. Construct source-side counterparts or cross-netlist transplants only when local evidence is strong enough.
4. Require graph activity and global CEC before counting recovered boundaries.

## Evaluation

Use `results/research_wow/recoverability_frontier.csv` as the main table and `results/research_wow/recoverability_frontier.png` as the main figure. Use the supporting figures in `paper/figures/` to show the problem setup, evidence hierarchy, methodology pipeline, failure taxonomy, and case-study trace.

Use `paper/figures/interface_ablation.png` as the targeted cross-netlist ablation figure.

Use `results/evidence_advancement/evidence_advancement_summary.csv` to describe next-step promotions without changing headline recovery counts.

## Failure Taxonomy

Use `results/research_wow/failure_taxonomy.csv` to explain why null results are meaningful: missing provenance, target irrelevance, non-compact interfaces, absent rewrite artifacts, bounded blind CEGIS exhaustion, and formal locality barriers.

## Ablations and Baselines

Use `results/research_wow/ablation_summary.csv` and `results/research_wow/baseline_summary.csv` to show which components move counts and which baselines remain diagnostic.

## Limitations

RTL recovery claims remain out of scope. The artifact now commits a tiny CC0 RTL seed corpus with source-location metadata, but successful Yosys lowering is tool-dependent and is recorded as `tool_missing` on machines without Yosys. Oracle rows are diagnostic and must not be merged with blind recoveries.

## Related Work Positioning

Position against equivalence checking, SAT sweeping/FRAIG, observability don't-care optimization, source mapping, and formal artifact evaluation. The novelty is the auditable separation between proofs, diagnostics, graph-active rewrites, and bounded failures.
"""


def frontier_row(result_family: str, denominator_class: str, denominator: int, success: int, metric: str, evidence: str, evidence_file: str) -> dict[str, str]:
    return {
        "result_family": result_family,
        "denominator_class": denominator_class,
        "denominator": str(denominator),
        "success_count": str(success),
        "success_metric": metric,
        "success_rate": f"{success / denominator if denominator else 0:.6f}",
        "evidence_level": evidence,
        "evidence_file": evidence_file,
        "schema_version": SCHEMA,
    }


def add_failure(out: list[dict[str, str]], failure_class: str, definition: str, count_value: int, denominator_class: str, evidence_file: str, example: str, implication: str) -> None:
    out.append(
        {
            "failure_class": failure_class,
            "definition": definition,
            "denominator_class": denominator_class,
            "count": str(count_value),
            "example": example,
            "evidence_file": evidence_file,
            "implication": implication,
            "schema_version": SCHEMA,
        }
    )


def append_family_failures(out: list[dict[str, str]], family: str, rel_path: str, group_col: str, stage_col: str, reason_col: str) -> None:
    for row in rows(rel_path):
        reason = row.get(reason_col, "")
        stage = row.get(stage_col, "")
        group = row.get(group_col, "")
        add_failure(
            out,
            f"{family}::{group}::{stage}::{reason}",
            f"{family} failure row from the committed taxonomy.",
            int(row.get("count", "0") or 0),
            group or family,
            rel_path,
            reason,
            "Keep this blocker separate from accepted controlled proof claims.",
        )


def append_ablations(out: list[dict[str, str]], family: str, rel_path: str, name_col: str, denominator_col: str, success_col: str, metric: str) -> None:
    for row in rows(rel_path):
        denom = int(row.get(denominator_col, "0") or 0)
        success = float(row.get(success_col, "0") or 0)
        out.append(
            {
                "experiment_family": family,
                "ablation": row.get(name_col, ""),
                "denominator": str(denom),
                "success_count": f"{success:g}",
                "success_metric": metric,
                "success_rate": f"{success / denom if denom else 0:.6f}",
                "notes": row.get("failure_reason") or row.get("notes", ""),
                "schema_version": SCHEMA,
            }
        )


def append_baselines(out: list[dict[str, str]], family: str, rel_path: str, name_col: str, denominator_col: str, success_col: str, metric: str) -> None:
    for row in rows(rel_path):
        denom = int(row.get(denominator_col, "0") or 0)
        success = float(row.get(success_col, "0") or 0)
        out.append(
            {
                "experiment_family": family,
                "baseline": row.get(name_col, ""),
                "denominator": str(denom),
                "success_count": f"{success:g}",
                "success_metric": metric,
                "success_rate": f"{success / denom if denom else 0:.6f}",
                "notes": row.get("notes", ""),
                "schema_version": SCHEMA,
            }
        )


def demo_row(mode: str, stage: str, subject: str, artifact_key: str, status: str, evidence: str, artifact: str, notes: str = "") -> dict[str, str]:
    return {
        "mode": mode,
        "stage": stage,
        "subject": subject,
        "artifact_key": artifact_key,
        "status": status,
        "evidence_level": evidence,
        "artifact": artifact,
        "notes": notes,
        "schema_version": SCHEMA,
    }


def rows(rel_path: str) -> list[dict[str, str]]:
    path = ROOT / rel_path
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def write_csv(path: Path, data: list[dict[str, str]]) -> None:
    if not data:
        raise SystemExit(f"No rows to write for {path}")
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(data[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(data)


def write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def count(data: list[dict[str, str]], key: str, *, equals: str | None = None, prefix: str | None = None) -> int:
    if equals is not None:
        return sum(r.get(key) == equals for r in data)
    if prefix is not None:
        return sum(r.get(key, "").startswith(prefix) for r in data)
    return sum(bool(r.get(key)) for r in data)


def example_value(data: list[dict[str, str]], key: str, pred) -> str:
    for row in data:
        if pred(row):
            return row.get(key, "")
    return ""


def table(columns: list[str], data: list[dict[str, str]]) -> str:
    widths = {c: max(len(c), *(len(str(r.get(c, ""))) for r in data)) for c in columns}
    header = "| " + " | ".join(c.ljust(widths[c]) for c in columns) + " |"
    sep = "| " + " | ".join("-" * widths[c] for c in columns) + " |"
    body = ["| " + " | ".join(str(r.get(c, "")).ljust(widths[c]) for c in columns) + " |" for r in data]
    return "\n".join([header, sep, *body])


if __name__ == "__main__":
    raise SystemExit(main())
