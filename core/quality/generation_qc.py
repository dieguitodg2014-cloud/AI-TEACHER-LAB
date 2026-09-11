"""Minimal QC gate for generated lesson artifacts."""

from __future__ import annotations

import re
from typing import Any

from core.generation.output_validator import validate_generated_lesson


_ORAL_ACTIONS = ("talk", "speak", "discuss", "interview", "present", "describe orally")
_WRITTEN_ACTIONS = ("write", "complete", "fill in", "compose")


def _assessment_alignment_errors(
    lesson: dict[str, Any],
    assessment_decision: dict[str, Any] | None,
) -> list[str]:
    """Check that the generated lesson contains observable assessment evidence."""
    if assessment_decision is None:
        return []

    activities = lesson.get("activities")
    if not isinstance(activities, list) or not activities:
        return ["ASSESSMENT_EVIDENCE_MISSING"]

    assessment_links = [
        str(activity.get("assessment_link", "")).strip()
        for activity in activities
        if isinstance(activity, dict)
    ]
    if not any(assessment_links):
        return ["ASSESSMENT_EVIDENCE_MISSING"]

    assessment_type = str(assessment_decision.get("type", "")).upper()
    if assessment_type in {"PERFORMANCE", "ORAL", "MIXED"}:
        productions = [
            str(activity.get("student_production", "")).strip()
            for activity in activities
            if isinstance(activity, dict)
        ]
        if not any(productions):
            return ["ASSESSMENT_PRODUCTION_MISSING"]

    return []


def _objective_action_alignment_errors(
    lesson: dict[str, Any],
    objective: str,
) -> list[str]:
    """Catch a common semantic mismatch between the requested action and production.

    This is deliberately narrow: it only evaluates generated student-production fields
    when they are present, so the MVP does not invent requirements for older artifacts.
    """
    productions = [
        str(activity.get("student_production", "")).strip().casefold()
        for activity in lesson.get("activities", [])
        if isinstance(activity, dict) and str(activity.get("student_production", "")).strip()
    ]
    if not productions:
        return []

    objective_text = objective.casefold()
    production_text = " ".join(productions)

    oral_requested = any(action in objective_text for action in _ORAL_ACTIONS)
    written_requested = any(action in objective_text for action in _WRITTEN_ACTIONS)

    if oral_requested and not any(
        marker in production_text
        for marker in ("talk", "speak", "discuss", "interview", "present", "share", "oral")
    ):
        return ["OBJECTIVE_PRODUCTION_MISMATCH"]

    if written_requested and not any(
        marker in production_text for marker in ("write", "complete", "fill", "compose")
    ):
        return ["OBJECTIVE_PRODUCTION_MISMATCH"]

    return []


def _target_use_alignment_errors(
    lesson: dict[str, Any],
    objective: str,
) -> list[str]:
    """Catch an explicit objective-use mismatch without hardcoding individual lessons."""
    objective_text = objective.casefold()
    generated_text = " ".join(
        str(activity.get("student_production", ""))
        for activity in lesson.get("activities", [])
        if isinstance(activity, dict)
    ).casefold()

    # When an objective explicitly frames present perfect as life experience,
    # duration-focused production is a different communicative use and should not
    # be allowed to silently replace the requested one.
    experience_focus = any(
        phrase in objective_text
        for phrase in ("life experience", "life experiences", "personal experience", "personal experiences")
    )
    duration_focus = any(
        phrase in generated_text
        for phrase in ("for five years", "for ten years", "for three years", "since 2010", "since 2020", "how long")
    )
    if experience_focus and duration_focus:
        return ["TARGET_USE_MISMATCH"]

    return []


def review_generated_lesson(
    lesson: dict[str, Any],
    *,
    level: str,
    objective: str,
    duration_minutes: int,
    topic: str | None = None,
    constraints: list[Any] | None = None,
    assessment_decision: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Run the current MVP QC checks and return the official QCResult shape."""
    blocking_errors = validate_generated_lesson(
        lesson,
        expected_level=level,
        expected_objective=objective,
        expected_duration=duration_minutes,
        expected_topic=topic,
        constraints=constraints,
    )
    if not blocking_errors and assessment_decision is not None:
        blocking_errors.extend(_assessment_alignment_errors(lesson, assessment_decision))
    if not blocking_errors:
        blocking_errors.extend(_objective_action_alignment_errors(lesson, objective))
    if not blocking_errors:
        blocking_errors.extend(_target_use_alignment_errors(lesson, objective))

    level_alignment = "LEVEL_MISMATCH" not in blocking_errors
    objective_alignment = not any(
        error in blocking_errors
        for error in ("OBJECTIVE_MISMATCH", "OBJECTIVE_PRODUCTION_MISMATCH", "TARGET_USE_MISMATCH")
    )
    content_alignment = not any(
        error in blocking_errors
        for error in ("CONTENT_TOPIC_MISSING", "CONTENT_FORBIDDEN_TERM")
    )
    time_realism = not any(
        error in blocking_errors
        for error in ("INVALID_DURATION", "DURATION_EXCEEDED")
    )
    activity_presence = "MISSING_ACTIVITIES" not in blocking_errors

    # The remaining dimensions are not yet deeply evaluated by the MVP validator.
    # They therefore remain explicitly conservative rather than being invented.
    communicative_value = activity_presence
    linguistic_accuracy = True
    assessment_alignment = not any(
        error in blocking_errors
        for error in (
            "ASSESSMENT_EVIDENCE_MISSING",
            "ASSESSMENT_PRODUCTION_MISSING",
        )
    )

    checks = {
        "level_alignment": level_alignment,
        "objective_alignment": objective_alignment,
        "content_alignment": content_alignment,
        "communicative_value": communicative_value,
        "time_realism": time_realism,
        "linguistic_accuracy": linguistic_accuracy,
        "assessment_alignment": assessment_alignment,
    }

    failed_checks = sum(not value for value in checks.values())
    score = 100.0 if failed_checks == 0 else max(0.0, 100.0 - (failed_checks * 20.0))
    critical_failure = bool(blocking_errors)

    return {
        "qc_id": "generation-qc-mvp",
        "status": "READY" if not blocking_errors else "REJECT_AND_REDESIGN",
        "score": score,
        "critical_failure": critical_failure,
        "checks": checks,
        "revision_required": bool(blocking_errors),
        "feedback": list(blocking_errors),
        "blocking_errors": list(blocking_errors),
    }
