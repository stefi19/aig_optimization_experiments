#!/usr/bin/env python3
"""Compare first-frontier and cost-guided extended-boundary results."""

from __future__ import annotations

import csv
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from boundary_semantics import write_csv  # noqa: E402

OUT_DIR = ROOT / "results" / "extended_boundary_search"
CASES = OUT_DIR / "extended_boundary_cases.csv"


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def main() -> int:
    rows = read_rows(CASES)
    comparison = []
    grouped = defaultdict(list)
    for row in rows:
        grouped[(row["benchmark"], row["optimization"], row["coi_name"], row["anchor_mode"], row["search_mode"])].append(row)
    for key, values in sorted(grouped.items()):
        benchmark, optimization, coi_name, anchor_mode, search_mode = key
        total = len(values)
        success = sum(r["success"] == "True" for r in values)
        avg_extension = sum(float(r.get("extension_ratio") or 0) for r in values) / total if total else 0
        avg_runtime = sum(float(r.get("runtime_seconds") or 0) for r in values) / total if total else 0
        avg_states = sum(int(r.get("search_states") or 0) for r in values) / total if total else 0
        comparison.append(
            {
                "benchmark": benchmark,
                "optimization": optimization,
                "coi_name": coi_name,
                "anchor_mode": anchor_mode,
                "search_mode": search_mode,
                "rows": total,
                "successes": success,
                "success_rate": success / total if total else 0,
                "avg_extension_ratio": avg_extension,
                "avg_runtime_seconds": avg_runtime,
                "avg_search_states": avg_states,
            }
        )
    write_csv(OUT_DIR / "search_strategy_comparison.csv", comparison)

    previous_failures = [r for r in rows if r["old_status"] != "success"]
    remaining = []
    for row in previous_failures:
        remaining.append(
            {
                "case_id": row["case_id"],
                "benchmark": row["benchmark"],
                "optimization": row["optimization"],
                "coi_name": row["coi_name"],
                "anchor_mode": row["anchor_mode"],
                "search_mode": row["search_mode"],
                "old_status": row["old_status"],
                "old_failure_reason": row["old_failure_reason"],
                "success": row["success"],
                "classification": row["classification"],
                "incoming_bypass_count": row["incoming_bypass_count"],
                "outgoing_bypass_count": row["outgoing_bypass_count"],
                "extension_ratio": row["extension_ratio"],
                "search_states": row["search_states"],
                "runtime_seconds": row["runtime_seconds"],
            }
        )
    write_csv(OUT_DIR / "remaining_failure_analysis.csv", remaining)

    anchor_rows = []
    for (anchor_mode, search_mode), vals in sorted(_group(rows, "anchor_mode", "search_mode").items()):
        anchor_rows.append(
            {
                "anchor_mode": anchor_mode,
                "search_mode": search_mode,
                "rows": len(vals),
                "selected_exact_anchor_count": sum(int(v.get("selected_exact_anchor_count") or 0) for v in vals),
                "selected_complemented_anchor_count": sum(int(v.get("selected_complemented_anchor_count") or 0) for v in vals),
                "selected_sat_cec_anchor_count": sum(int(v.get("selected_sat_cec_anchor_count") or 0) for v in vals),
                "available_sat_cec_frontier_candidates": sum(int(v.get("available_sat_cec_frontier_candidates") or 0) for v in vals),
            }
        )
    write_csv(OUT_DIR / "anchor_usage.csv", anchor_rows)

    budget_rows = []
    for (anchor_mode, search_mode), vals in sorted(_group(rows, "anchor_mode", "search_mode").items()):
        budget_rows.append(
            {
                "anchor_mode": anchor_mode,
                "search_mode": search_mode,
                "rows": len(vals),
                "total_search_states": sum(int(v.get("search_states") or 0) for v in vals),
                "total_pruned_states": sum(int(v.get("pruned_states") or 0) for v in vals),
                "total_cycle_pruned_states": sum(int(v.get("cycle_pruned_states") or 0) for v in vals),
                "max_search_states": max((int(v.get("search_states") or 0) for v in vals), default=0),
            }
        )
    write_csv(OUT_DIR / "search_budget_statistics.csv", budget_rows)
    update_summary(rows)
    print("Wrote extended-boundary strategy comparison")
    return 0


def update_summary(rows: list[dict[str, str]]) -> None:
    strategy = Counter((r["search_mode"], r["success"]) for r in rows)
    lines = [
        "# Extended-Boundary Strategy Comparison",
        "",
        "## Strategy Rows",
        "",
    ]
    for mode in sorted({r["search_mode"] for r in rows}):
        total = sum(1 for r in rows if r["search_mode"] == mode)
        success = strategy[(mode, "True")]
        lines.append(f"- `{mode}`: {success} / {total}")
    lines.extend(["", "## Classification", ""])
    classes = Counter(r["classification"] for r in rows if r["success"] != "True")
    if classes:
        lines.extend(f"- {name}: {count}" for name, count in sorted(classes.items()))
    else:
        lines.append("No remaining failed rows.")
    (OUT_DIR / "strategy_comparison_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _group(rows: list[dict[str, str]], *cols: str) -> dict[tuple[str, ...], list[dict[str, str]]]:
    grouped = defaultdict(list)
    for row in rows:
        grouped[tuple(row[c] for c in cols)].append(row)
    return grouped


if __name__ == "__main__":
    raise SystemExit(main())
