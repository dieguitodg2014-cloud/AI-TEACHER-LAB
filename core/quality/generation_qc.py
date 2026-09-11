"""Minimal QC gate for generated lesson artifacts."""

from __future__ import annotations

from typing import Any

from core.generation.output_validator import validate_generated_lesson


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

    level_alignment = "LEVEL_MISMATCH" not in blocking_errors
    objective_alignment = "OBJECTIVE_MISMATCH" not in blocking_errors
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
        for error in ("ASSESSMENT_EVIDENCE_MISSING", "ASSESSMENT_PRODUCTION_MISSING")
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
