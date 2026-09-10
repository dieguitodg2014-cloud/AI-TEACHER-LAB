"""Validation of generated lesson artifacts against approved decisions."""

from __future__ import annotations

from typing import Any


def validate_generated_lesson(
    lesson: dict[str, Any],
    expected_level: str,
    expected_objective: str,
    expected_duration: int,
) -> list[str]:
    """Return blocking errors without rewriting the generated lesson."""
    if not isinstance(lesson, dict):
        return ["INVALID_OUTPUT"]

    errors: list[str] = []

    if lesson.get("level") != expected_level:
        errors.append("LEVEL_MISMATCH")

    if lesson.get("objective") != expected_objective:
        errors.append("OBJECTIVE_MISMATCH")

    duration = lesson.get("duration_minutes")
    if not isinstance(duration, int) or duration <= 0:
        errors.append("INVALID_DURATION")
    elif duration > expected_duration:
        errors.append("DURATION_EXCEEDED")

    activities = lesson.get("activities")
    if not isinstance(activities, list) or not activities:
        errors.append("MISSING_ACTIVITIES")

    return errors


def generation_status(errors: list[str]) -> str:
    """Map validation findings to the generation workflow state."""
    return "VALID" if not errors else "QC_REQUIRED"
