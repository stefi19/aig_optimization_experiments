#!/usr/bin/env python3
"""Run formal contextual CEC proofs for ODC-anchor candidates."""

from __future__ import annotations

import argparse
import csv
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from boundary_graph import CircuitGraph  # noqa: E402
from boundary_semantics import load_canonical_manifest, original_path, variant_path, write_csv  # noqa: E402
from odc_formal_validation import prove_contextual_interchangeability  # noqa: E402

OUT = ROOT / "results" / "odc_anchor_generation"
CANDIDATES = OUT / "odc_candidate_features.csv"
PROOF_COLUMNS = [
    "case_id", "benchmark", "optimization", "coi_name", "context_mode", "observable_outputs", "ranking_mode",
    "spec_node", "impl_node", "requested_polarity", "proven_polarity", "candidate_rank", "mapping_category",
    "evidence_level", "equivalence_scope", "proof_status", "sat_result", "proof_mode", "proof_runtime_seconds",
    "spec_fingerprint", "impl_fingerprint", "sampled_mismatch_rate", "source_result_file", "failure_reason",
]


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--max-formal-checks-per-case", type=int, default=200)
    p.add_argument("--formal-timeout", type=int, default=30)
    p.add_argument("--abc", default=None)
    p.add_argument("--output-dir", type=Path, default=OUT)
    return p.parse_args()


def main() -> int:
    args = parse_args()
    abc = args.abc or shutil.which("abc") or str(ROOT / ".abc_build" / "abc_repo" / "abc")
    if not Path(abc).exists():
        abc = None
    cois = {(c.benchmark, c.coi_name): c for c in load_canonical_manifest()}
    counts = {}
    proofs = []
    with CANDIDATES.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            budget_key = row["case_id"].split("|global_output_odc|")[0].split("|coi_output_odc|")[0]
            counts[budget_key] = counts.get(budget_key, 0) + 1
            if counts[budget_key] > args.max_formal_checks_per_case:
                continue
            coi = cois[(row["benchmark"], row["coi_name"])]
            spec_path = original_path(coi.benchmark)
            impl_path = variant_path(coi.benchmark, row["optimization"])
            spec_graph = CircuitGraph.from_blif(spec_path)
            observable = tuple(spec_graph.outputs if row["context_mode"] == "global_output_odc" else coi.boundary_outputs)
            proof = prove_contextual_interchangeability(
                spec_path,
                impl_path,
                row["spec_node"],
                row["impl_node"],
                row["requested_polarity"],
                row["context_mode"],
                observable,
                args.formal_timeout,
                abc,
            )
            proofs.append(
                {
                    **{k: row.get(k, "") for k in ["case_id", "benchmark", "optimization", "coi_name", "context_mode", "ranking_mode", "spec_node", "impl_node", "requested_polarity", "candidate_rank", "sampled_mismatch_rate"]},
                    "observable_outputs": ";".join(sorted(proof.observable_outputs)),
                    "proven_polarity": row["requested_polarity"] if proof.status == "proven_odc_valid" else "",
                    "mapping_category": "formal_odc_valid_anchor" if proof.status == "proven_odc_valid" else "sampled_contextual_candidate",
                    "evidence_level": "formal_contextual" if proof.status == "proven_odc_valid" else "unresolved",
                    "equivalence_scope": "contextual" if proof.status == "proven_odc_valid" else "sampled_contextual",
                    "proof_status": proof.status,
                    "sat_result": proof.sat_result,
                    "proof_mode": proof.proof_mode,
                    "proof_runtime_seconds": f"{proof.runtime_seconds:.6f}",
                    "spec_fingerprint": proof.spec_fingerprint,
                    "impl_fingerprint": proof.impl_fingerprint,
                    "source_result_file": "results/odc_anchor_generation/odc_formal_proofs.csv",
                    "failure_reason": proof.failure_reason,
                }
            )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(args.output_dir / "odc_formal_proofs.csv", proofs, PROOF_COLUMNS)
    write_csv(args.output_dir / "odc_proven_anchors.csv", [r for r in proofs if r["proof_status"] == "proven_odc_valid"], PROOF_COLUMNS)
    write_csv(args.output_dir / "odc_disproved_candidates.csv", [r for r in proofs if r["proof_status"] == "disproven"], PROOF_COLUMNS)
    write_csv(args.output_dir / "odc_timeouts.csv", [r for r in proofs if r["proof_status"] in {"timeout", "tool_error"}], PROOF_COLUMNS)
    print(f"Wrote ODC proof rows: {len(proofs)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
