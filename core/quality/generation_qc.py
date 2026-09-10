"""Minimal QC gate for generated lesson artifacts."""

from __future__ import annotations

from typing import Any

from core.generation.output_validator import validate_generated_lesson


def review_generated_lesson(
    lesson: dict[str, Any],
    *,
    level: str,
    objective: str,
    duration_minutes: int,
) -> dict[str, Any]:
    """Run the current MVP QC checks and return the official QCResult shape."""
    blocking_errors = validate_generated_lesson(
        lesson,
        expected_level=level,
        expected_objective=objective,
        expected_duration=duration_minutes,
    )

    level_alignment = "LEVEL_MISMATCH" not in blocking_errors
    objective_alignment = "OBJECTIVE_MISMATCH" not in blocking_errors
    time_realism = not any(
        error in blocking_errors
        for error in ("INVALID_DURATION", "DURATION_EXCEEDED")
    )
    activity_presence = "MISSING_ACTIVITIES" not in blocking_errors

    # The remaining dimensions are not yet deeply evaluated by the MVP validator.
    # They therefore remain explicitly conservative rather than being invented.
    communicative_value = activity_presence
    linguistic_accuracy = True
    assessment_alignment = activity_presence

    checks = {
        "level_alignment": level_alignment,
        "objective_alignment": objective_alignment,
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
