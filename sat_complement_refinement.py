#!/usr/bin/env python3
"""Check complemented equivalence for SAT-rejected non-exact candidates.

The normal SAT refinement checks same-polarity equivalence:

    original_candidate == optimized_node

For AIG-style matching, a useful second question is whether a rejected pair is
equivalent up to inversion:

    original_candidate == NOT optimized_node

This script keeps that result separate from the existing SAT files.  It reads
same-polarity SAT outputs, retests only rows with sat_status == "rejected", and
writes complemented verdicts to independent CSV/Markdown outputs.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pandas as pd

from sat_refinement_abc import (
    OUT_COLS,
    _extract_summary_line,
    _find_useful_error_line,
    expose_node_as_output,
    find_abc,
    load_fingerprint_index,
    resolve_node_via_fingerprint,
    run_abc_cec,
)


FINGERPRINT_CSV = os.path.join("results", "node_fingerprints.csv")

INPUTS = [
    (
        "rank1_nonexact_recovery",
        Path("results/sat_verified_candidates.csv"),
        Path("results/sat_complement_rank1_nonexact.csv"),
    ),
    (
        "topk_nonexact_recovery",
        Path("results/sat_topk_nonexact_verified.csv"),
        Path("results/sat_complement_topk_nonexact.csv"),
    ),
]

SUMMARY_CSV = Path("results/sat_complement_summary.csv")
SUMMARY_MD = Path("results/sat_complement_summary.md")

OUT_COLS_COMPLEMENT = OUT_COLS + [
    "same_polarity_status",
    "complement_status",
    "polarity_checked",
]


def _resolve_and_expose(
    blif: str,
    node: str,
    dst: str,
    row: dict,
    fp_index: dict,
    side: str,
    invert: bool,
) -> tuple[bool, str, str]:
    """Expose a node, optionally via fingerprint fallback.

    Returns (ok, recovery_method, note).
    """
    try:
        expose_node_as_output(blif, node, dst, invert=invert)
        return True, "direct", ""
    except ValueError:
        if side == "original":
            fp = row.get("original_fingerprint", "")
            opt_key = "original"
        else:
            fp = row.get("optimized_fingerprint", "")
            opt_key = row["optimization"]

        recovered = resolve_node_via_fingerprint(
            fp_index, row["benchmark"], opt_key, fp
        )
        if recovered is None:
            return (
                False,
                "inconclusive",
                f"{side} node '{node}' not in BLIF and fingerprint recovery found no unique match",
            )

        try:
            expose_node_as_output(blif, recovered, dst, invert=invert)
            return True, "fingerprint", f"{side}: '{node}' -> '{recovered}' via fingerprint"
        except ValueError as exc:
            return (
                False,
                "inconclusive",
                f"fingerprint-recovered {side} '{recovered}' also not in BLIF: {exc}",
            )


def check_complemented_candidate(abc_bin: str, row: dict, fp_index: dict) -> dict:
    """Check original_candidate == NOT optimized_node for one rejected row."""
    result = {col: row.get(col, "") for col in OUT_COLS}
    result["same_polarity_status"] = row.get("sat_status", "")
    result["complement_status"] = "inconclusive"
    result["polarity_checked"] = "original == NOT optimized"
    result["sat_status"] = "inconclusive"
    result["abc_result"] = ""
    result["recovery_method"] = "inconclusive"
    result["notes"] = ""

    orig_blif = row["orig_blif"] if "orig_blif" in row else f"variants/{row['benchmark']}_original.blif"
    opt_blif = row["opt_blif"] if "opt_blif" in row else f"variants/{row['benchmark']}_{row['optimization']}.blif"

    for path in (orig_blif, opt_blif):
        if not os.path.exists(path):
            result["notes"] = f"BLIF file not found: {path}"
            return result

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_orig = os.path.join(tmpdir, "orig_exposed.blif")
        tmp_opt = os.path.join(tmpdir, "opt_inverted.blif")

        ok_orig, rec_orig, note_orig = _resolve_and_expose(
            orig_blif,
            row["original_candidate"],
            tmp_orig,
            row,
            fp_index,
            side="original",
            invert=False,
        )
        if not ok_orig:
            result["notes"] = note_orig
            return result

        ok_opt, rec_opt, note_opt = _resolve_and_expose(
            opt_blif,
            row["optimized_node"],
            tmp_opt,
            row,
            fp_index,
            side="optimized",
            invert=True,
        )
        if not ok_opt:
            result["notes"] = note_opt
            return result

        status, raw = run_abc_cec(abc_bin, tmp_orig, tmp_opt)

    result["sat_status"] = status
    result["complement_status"] = status
    result["abc_result"] = _extract_summary_line(raw)
    if rec_orig == "fingerprint" or rec_opt == "fingerprint":
        result["recovery_method"] = "fingerprint"
    else:
        result["recovery_method"] = "direct"

    notes = [n for n in (note_orig, note_opt) if n]
    if status == "inconclusive":
        notes.append(_find_useful_error_line(raw) or raw.strip()[:150])
    result["notes"] = "; ".join(notes)
    return result


def summarize(outputs: list[tuple[str, Path, pd.DataFrame]]) -> pd.DataFrame:
    rows = []
    for layer, _path, df in outputs:
        counts = df["complement_status"].value_counts() if not df.empty else {}
        total = len(df)
        comp_verified = int(counts.get("verified", 0))
        rejected = int(counts.get("rejected", 0))
        inconclusive = int(counts.get("inconclusive", 0))
        rows.append({
            "validation_layer": layer,
            "total_same_polarity_rejected": total,
            "same_polarity_verified": 0,
            "complemented_verified": comp_verified,
            "rejected_both_polarities": rejected,
            "inconclusive": inconclusive,
            "complemented_verification_rate": comp_verified / total if total else 0.0,
        })
    return pd.DataFrame(rows)


def write_markdown(summary: pd.DataFrame) -> None:
    display = summary.copy()
    display["complemented_verification_rate"] = display[
        "complemented_verification_rate"
    ].map(lambda v: f"{v:.1%}")

    lines = ["# Complemented SAT Validation Summary\n"]
    lines.append(
        "The normal SAT validation checks same-polarity equivalence (`f == g`). "
        "This follow-up retests same-polarity rejected non-exact candidates for "
        "complemented equivalence (`f == NOT g`).\n"
    )
    lines.append(display.to_markdown(index=False))
    lines.append("")
    lines.append(
        "A complemented verification would mean the candidate was not same-polarity "
        "equivalent, but did match after inverting the optimized node. These results "
        "remain separate from exact-anchor sanity checks and same-polarity recovery.\n"
    )
    SUMMARY_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    abc_bin = find_abc()
    fp_index = load_fingerprint_index(FINGERPRINT_CSV)
    outputs = []

    for layer, input_path, output_path in INPUTS:
        if not input_path.exists():
            print(f"Skipping missing input: {input_path}")
            continue

        df = pd.read_csv(input_path)
        rejected = df[df["sat_status"] == "rejected"].copy()
        print(f"{layer}: checking {len(rejected)} same-polarity rejected rows")

        rows = []
        for i, row in rejected.iterrows():
            print(
                f"  [{len(rows)+1}/{len(rejected)}] "
                f"{row['benchmark']}/{row['optimization']} "
                f"{row['original_candidate']} vs NOT {row['optimized_node']}",
                end=" ... ",
                flush=True,
            )
            checked = check_complemented_candidate(abc_bin, row.to_dict(), fp_index)
            rows.append(checked)
            print(checked["complement_status"])

        out_df = pd.DataFrame(rows, columns=OUT_COLS_COMPLEMENT)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        out_df.to_csv(output_path, index=False)
        outputs.append((layer, output_path, out_df))
        print(f"Wrote {output_path}")

    summary = summarize(outputs)
    summary.to_csv(SUMMARY_CSV, index=False)
    write_markdown(summary)
    print(f"Wrote {SUMMARY_CSV}")
    print(f"Wrote {SUMMARY_MD}")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
