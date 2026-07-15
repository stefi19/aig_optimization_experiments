"""Formal correspondence anchors for equivalence-anchored boundary recovery."""

from __future__ import annotations

from collections import defaultdict
import csv
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from contextual_error_metrics import normalize_mapping_category


FORMAL_CATEGORIES = {
    "exact_signature_match",
    "complemented_equivalence",
    "sat_cec_proven_equivalent",
}

ANCHOR_MODES = {
    "exact_only": {"exact_signature_match"},
    "exact_plus_complemented": {"exact_signature_match", "complemented_equivalence"},
    "formal_all": {"exact_signature_match", "complemented_equivalence", "sat_cec_proven_equivalent"},
}

CATEGORY_PRIORITY = {
    "exact_signature_match": 0,
    "sat_cec_proven_equivalent": 1,
    "complemented_equivalence": 2,
}


@dataclass(frozen=True)
class Anchor:
    spec_node: str
    impl_node: str
    polarity: str
    mapping_category: str
    evidence_level: str
    proof_mode: str
    source_result_file: str
    confidence_or_status: str
    selected: bool = False
    selection_reason: str = ""


class AnchorMap:
    def __init__(self, anchors: list[Anchor]):
        self.anchors = sorted(
            anchors,
            key=lambda a: (
                a.spec_node,
                CATEGORY_PRIORITY.get(a.mapping_category, 99),
                0 if a.polarity == "same" else 1,
                a.impl_node,
                a.source_result_file,
            ),
        )
        self._by_spec: dict[str, list[Anchor]] = defaultdict(list)
        for anchor in self.anchors:
            self._by_spec[anchor.spec_node].append(anchor)

    def candidates_for(self, spec_node: str) -> list[Anchor]:
        return list(self._by_spec.get(spec_node, []))

    def selected_for(self, spec_node: str) -> Anchor | None:
        candidates = self.candidates_for(spec_node)
        if not candidates:
            return None
        chosen = candidates[0]
        return Anchor(
            **{
                **chosen.__dict__,
                "selected": True,
                "selection_reason": (
                    "Selected by category priority exact_signature_match, "
                    "sat_cec_proven_equivalent, complemented_equivalence; "
                    "same polarity before complemented; then lexical implementation node."
                ),
            }
        )

    def has_anchor(self, spec_node: str) -> bool:
        return self.selected_for(spec_node) is not None

    def selected_anchors(self, spec_nodes: set[str]) -> dict[str, Anchor]:
        return {node: anchor for node in sorted(spec_nodes) if (anchor := self.selected_for(node))}


def _boolish(value: object) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes"}


def load_anchor_map(
    benchmark: str,
    optimization: str,
    anchor_mode: str,
    *,
    results_dir: Path,
    spec_inputs: list[str] | tuple[str, ...] = (),
    impl_inputs: list[str] | tuple[str, ...] = (),
    spec_outputs: list[str] | tuple[str, ...] = (),
    impl_outputs: list[str] | tuple[str, ...] = (),
) -> AnchorMap:
    if anchor_mode not in ANCHOR_MODES:
        raise ValueError(f"unknown anchor mode {anchor_mode!r}")
    allowed = ANCHOR_MODES[anchor_mode]
    anchors: list[Anchor] = []
    impl_input_set = set(impl_inputs)
    for name in sorted(spec_inputs):
        if name in impl_input_set:
            anchors.append(
                Anchor(
                    spec_node=name,
                    impl_node=name,
                    polarity="same",
                    mapping_category="exact_signature_match",
                    evidence_level="formal_exhaustive",
                    proof_mode="primary_input_identity",
                    source_result_file="circuit_interface",
                    confidence_or_status="interface",
                )
            )
    impl_output_set = set(impl_outputs)
    for name in sorted(spec_outputs):
        if name in impl_output_set:
            anchors.append(
                Anchor(
                    spec_node=name,
                    impl_node=name,
                    polarity="same",
                    mapping_category="exact_signature_match",
                    evidence_level="formal_exhaustive",
                    proof_mode="primary_output_identity",
                    source_result_file="circuit_interface",
                    confidence_or_status="interface",
                )
            )
    top_path = results_dir / "top_candidates.csv"
    if top_path.exists() and "exact_signature_match" in allowed:
        for row in _read_rows(top_path):
            if row.get("benchmark") != benchmark or row.get("optimization") != optimization:
                continue
            if normalize_mapping_category(row.get("match_category")) != "exact_signature_match":
                continue
            formal = _boolish(row.get("is_formal_exact_mode"))
            anchors.append(
                Anchor(
                    spec_node=str(row["original_candidate"]),
                    impl_node=str(row["optimized_node"]),
                    polarity="same",
                    mapping_category="exact_signature_match",
                    evidence_level="formal_exhaustive" if formal else "sampled_estimate",
                    proof_mode="truth_table" if formal else "simulation_signature",
                    source_result_file="results/top_candidates.csv",
                    confidence_or_status=str(row.get("combined_score", "")),
                )
            )

    sat_path = results_dir / "sat_verified_candidates.csv"
    if sat_path.exists() and "sat_cec_proven_equivalent" in allowed:
        for row in _read_rows(sat_path):
            if row.get("benchmark") != benchmark or row.get("optimization") != optimization:
                continue
            if row.get("sat_status") != "verified":
                continue
            if normalize_mapping_category(row.get("match_category")) == "exact_signature_match":
                continue
            anchors.append(
                Anchor(
                    spec_node=str(row["original_candidate"]),
                    impl_node=str(row["optimized_node"]),
                    polarity="same",
                    mapping_category="sat_cec_proven_equivalent",
                    evidence_level="formal_cec",
                    proof_mode="abc_cec",
                    source_result_file="results/sat_verified_candidates.csv",
                    confidence_or_status=str(row.get("sat_status", "")),
                )
            )

    if "complemented_equivalence" in allowed:
        for path in [results_dir / "sat_complement_rank1_nonexact.csv", results_dir / "sat_complement_topk_nonexact.csv"]:
            if not path.exists():
                continue
            rows = _read_rows(path)
            status_col = "complement_status" if rows and "complement_status" in rows[0] else "sat_status"
            for row in rows:
                if row.get("benchmark") != benchmark or row.get("optimization") != optimization:
                    continue
                if row.get(status_col) != "verified":
                    continue
                anchors.append(
                    Anchor(
                        spec_node=str(row["original_candidate"]),
                        impl_node=str(row["optimized_node"]),
                        polarity="inverted",
                        mapping_category="complemented_equivalence",
                        evidence_level="formal_cec",
                        proof_mode="abc_cec_complement",
                        source_result_file=str(path.relative_to(results_dir.parent)),
                        confidence_or_status="verified",
                    )
                )

    filtered = [
        anchor
        for anchor in anchors
        if anchor.mapping_category in allowed
        and anchor.evidence_level in {"formal_exhaustive", "formal_cec"}
    ]
    return AnchorMap(filtered)


@lru_cache(maxsize=8)
def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))
