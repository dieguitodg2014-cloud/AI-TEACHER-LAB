"""Deterministic weighted quality scoring for the MVP-Next QC gate.

The scorer converts the existing QC evidence into a transparent weighted score.
It does not replace blocking validation or invent provider-specific judgments.
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

WEIGHTS: dict[str, float] = {
    "learning_validity": 15.0,
    "pedagogical_alignment": 15.0,
    "level_appropriacy": 15.0,
    "scaffolding_alignment": 10.0,
    "language_accuracy": 10.0,
    "communicative_value": 15.0,
    "practical_feasibility": 10.0,
    "assessment_alignment": 5.0,
    "resource_efficiency": 5.0,
}

if sum(WEIGHTS.values()) != 100.0:
    raise RuntimeError("QC weights must total 100")


def score_weighted_qc(
    *,
    checks: Mapping[str, bool],
    blocking_errors: list[str] | tuple[str, ...],
    lesson: Mapping[str, Any],
    activity_contracts: list[Mapping[str, Any]] | tuple[Mapping[str, Any], ...] | None = None,
    resource_decision: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Return weighted dimension scores and the aggregate score.

    Each dimension is scored from 0 to 100 using only deterministic evidence
    already available to the QC layer. Missing optional resource metadata is
    treated as not applicable rather than penalized.
    """
    errors = set(blocking_errors)

    learning_validity = checks.get("objective_alignment", False) and checks.get(
        "time_realism", False
    )
    pedagogical_alignment = checks.get("objective_alignment", False) and checks.get(
        "assessment_alignment", False
    )
    level_appropriacy = checks.get("level_alignment", False)
    scaffolding_alignment = not any(
        error in errors
        for error in (
            "SCAFFOLDING_MISMATCH",
            "INVALID_ACTIVITY_CONTRACT",
            "ACTIVITY_CONTRACT_COUNT_MISMATCH",
        )
    )
    language_accuracy = checks.get("linguistic_accuracy", False) and not any(
        error in errors
        for error in ("LANGUAGE_TARGET_MISSING", "LANGUAGE_TARGET_MISMATCH")
    )
    communicative_value = checks.get("communicative_value", False)
    practical_feasibility = checks.get("time_realism", False)
    assessment_alignment = checks.get("assessment_alignment", False)

    resource_efficiency = _resource_efficiency(
        lesson,
        resource_decision,
    )

    dimensions = {
        "learning_validity": 100.0 if learning_validity else 0.0,
        "pedagogical_alignment": 100.0 if pedagogical_alignment else 0.0,
        "level_appropriacy": 100.0 if level_appropriacy else 0.0,
        "scaffolding_alignment": 100.0 if scaffolding_alignment else 0.0,
        "language_accuracy": 100.0 if language_accuracy else 0.0,
        "communicative_value": 100.0 if communicative_value else 0.0,
        "practical_feasibility": 100.0 if practical_feasibility else 0.0,
        "assessment_alignment": 100.0 if assessment_alignment else 0.0,
        "resource_efficiency": resource_efficiency,
    }
    weighted_score = sum(
        dimensions[name] * WEIGHTS[name] / 100.0
        for name in WEIGHTS
    )

    return {
        "score": round(weighted_score, 2),
        "weights": dict(WEIGHTS),
        "dimensions": dimensions,
    }


def _resource_efficiency(
    lesson: Mapping[str, Any],
    resource_decision: Mapping[str, Any] | None,
) -> float:
    """Score resource use only when an authoritative resource decision exists."""
    if resource_decision is None:
        return 100.0

    action = str(resource_decision.get("action", "")).upper()
    resources = lesson.get("resources", [])
    has_resources = isinstance(resources, (list, tuple)) and bool(resources)

    if action in {"NO_RESOURCE_REQUIRED", "OMIT"}:
        return 100.0 if not has_resources else 0.0

    if action in {"CREATE", "REUSE", "ADAPT"}:
        return 100.0 if has_resources else 0.0

    return 0.0
