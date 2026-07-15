#!/usr/bin/env python3
"""Summarize ODC anchor generation and boundary recovery."""

from __future__ import annotations

import csv
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "odc_anchor_generation"


def read(name):
    path = OUT / name
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def main() -> int:
    candidates = read("odc_candidate_features.csv")
    proofs = read("odc_formal_proofs.csv")
    proven = read("odc_proven_anchors.csv")
    recovery = read("odc_boundary_recovery_cases.csv")
    usage = []
    grouped = defaultdict(lambda: [0, 0, 0])
    for row in recovery:
        key = (row["context_mode"], row["anchor_mode"], row["search_mode"])
        grouped[key][0] += 1
        grouped[key][1] += int(row["success"] == "True")
        grouped[key][2] += int(row.get("selected_odc_anchor_count") or 0)
    for (context, anchor, search), vals in sorted(grouped.items()):
        usage.append(
            {
                "context_mode": context,
                "anchor_mode": anchor,
                "search_mode": search,
                "rows": vals[0],
                "successes": vals[1],
                "selected_odc_anchor_count": vals[2],
            }
        )
    _write("odc_anchor_usage.csv", usage)
    failure_rows = [r for r in recovery if r["success"] != "True"]
    _write(
        "odc_failure_analysis.csv",
        [
            {
                "case_id": r["case_id"],
                "context_mode": r["context_mode"],
                "anchor_mode": r["anchor_mode"],
                "search_mode": r["search_mode"],
                "failure_reason": r["failure_reason"],
                "classification": r["classification"],
                "selected_odc_anchor_count": r.get("selected_odc_anchor_count", 0),
            }
            for r in failure_rows
        ],
    )
    lines = [
        "# ODC Anchor Generation Summary",
        "",
        f"- Candidate pairs generated: {len(candidates)}",
        f"- Formal checks attempted: {len(proofs)}",
        f"- Formal ODC anchors proven: {len(proven)}",
        f"- Candidates disproved: {sum(p['proof_status'] == 'disproven' for p in proofs)}",
        f"- Timeouts/tool errors: {sum(p['proof_status'] in {'timeout', 'tool_error'} for p in proofs)}",
        "",
        "## Boundary Recovery",
        "",
    ]
    for item in usage:
        lines.append(f"- `{item['context_mode']}` / `{item['anchor_mode']}` / `{item['search_mode']}`: {item['successes']} / {item['rows']}; selected ODC anchors {item['selected_odc_anchor_count']}")
    classes = Counter(r["classification"] for r in failure_rows)
    lines.extend(["", "## Remaining Failures", ""])
    if classes:
        lines.extend(f"- {k}: {v}" for k, v in sorted(classes.items()))
    else:
        lines.append("No remaining failed rows.")
    lines.append("")
    lines.append("Formal ODC-valid anchors are contextual only and are not labeled as global equivalence.")
    (OUT / "odc_anchor_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("Wrote ODC anchor comparison summary")
    return 0


def _write(name, rows):
    if rows:
        cols = list(rows[0])
    else:
        cols = []
    with (OUT / name).open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=cols, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    raise SystemExit(main())
