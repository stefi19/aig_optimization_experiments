"""Ranking modes that combine baseline, cofactor, and sensitivity features."""

from __future__ import annotations

from dataclasses import dataclass

from functional_signal_utils import safe_float


RANKING_MODES = (
    "baseline",
    "cofactor_only",
    "sensitivity_only",
    "cofactor_plus_sensitivity",
    "full_combined",
)

DEFAULT_WEIGHTS = {
    "existing": 0.45,
    "cofactor": 0.20,
    "cofactor_similarity": 0.10,
    "sensitivity": 0.15,
    "difference": 0.10,
    "dominant": 0.05,
    "worst": 0.05,
}


@dataclass(frozen=True)
class RankingScores:
    baseline: float
    cofactor_only: float
    sensitivity_only: float
    cofactor_plus_sensitivity: float
    full_combined: float

    def as_dict(self) -> dict[str, float]:
        return self.__dict__.copy()


def feature_available(row: dict, prefix: str) -> bool:
    if prefix == "cofactor":
        return str(row.get("cofactor_status", "")) == "ok"
    if prefix == "sensitivity":
        return str(row.get("sensitivity_status", "")) == "ok"
    return False


def compute_ranking_scores(row: dict, weights: dict[str, float] | None = None) -> RankingScores:
    """Compute deterministic scores for all ranking modes.

    These scores are heuristic ranking signals.  They never establish formal
    equivalence; SAT/CEC or exhaustive evaluation remains authoritative.
    """

    w = {**DEFAULT_WEIGHTS, **(weights or {})}
    baseline = safe_float(row.get("combined_score"), 0.0)
    cofactor_score = 0.0
    if feature_available(row, "cofactor"):
        cofactor_score = (
            0.55 * safe_float(row.get("cofactor_consistency_score"), 0.0)
            + 0.35 * safe_float(row.get("mean_cofactor_similarity"), 0.0)
            + 0.10 * (1.0 - safe_float(row.get("max_cofactor_error"), 1.0))
        )
    sensitivity_score = 0.0
    if feature_available(row, "sensitivity"):
        sensitivity_score = (
            0.45 * safe_float(row.get("sensitivity_cosine_similarity"), 0.0)
            + 0.35 * safe_float(row.get("boolean_difference_similarity"), 0.0)
            + 0.10 * safe_float(row.get("dominant_variable_agreement"), 0.0)
            + 0.10 * safe_float(row.get("inactive_variable_agreement"), 0.0)
        )
    cofactor_plus_sensitivity = 0.5 * cofactor_score + 0.5 * sensitivity_score
    full = (
        w["existing"] * baseline
        + w["cofactor"] * safe_float(row.get("cofactor_consistency_score"), 0.0)
        + w["cofactor_similarity"] * safe_float(row.get("mean_cofactor_similarity"), 0.0)
        + w["sensitivity"] * safe_float(row.get("sensitivity_cosine_similarity"), 0.0)
        + w["difference"] * safe_float(row.get("boolean_difference_similarity"), 0.0)
        + w["dominant"] * safe_float(row.get("dominant_variable_agreement"), 0.0)
        - w["worst"] * safe_float(row.get("max_cofactor_error"), 1.0)
    )
    return RankingScores(
        baseline=baseline,
        cofactor_only=max(0.0, min(1.0, cofactor_score)),
        sensitivity_only=max(0.0, min(1.0, sensitivity_score)),
        cofactor_plus_sensitivity=max(0.0, min(1.0, cofactor_plus_sensitivity)),
        full_combined=max(0.0, min(1.0, full)),
    )


def formal_label(row: dict) -> str:
    sat_status = str(row.get("sat_status", "")).strip().lower()
    if sat_status == "verified":
        return "verified_equivalent"
    if sat_status == "rejected":
        return "rejected_non_equivalent"
    if sat_status:
        return "inconclusive"
    return "not_checked"


def support_bucket(size: object) -> str:
    value = int(safe_float(size, 0.0))
    if value <= 4:
        return "0-4"
    if value <= 8:
        return "5-8"
    if value <= 12:
        return "9-12"
    return "13+"
