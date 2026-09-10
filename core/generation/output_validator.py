"""Validation of generated lesson artifacts against approved decisions."""

from __future__ import annotations

import re
from typing import Any


def _flatten_text(value: Any) -> str:
    """Collect generated text fields for lightweight content checks."""
    if isinstance(value, dict):
        return " ".join(_flatten_text(item) for item in value.values())
    if isinstance(value, list):
        return " ".join(_flatten_text(item) for item in value)
    return str(value)


def _forbidden_terms(constraints: list[Any]) -> list[str]:
    """Read explicit forbidden terms from constraints using a small contract."""
    terms: list[str] = []
    for constraint in constraints:
        if not isinstance(constraint, str):
            continue
        match = re.match(r"\s*FORBIDDEN_TERMS\s*:\s*(.+)\s*$", constraint, re.IGNORECASE)
        if match:
            terms.extend(term.strip() for term in match.group(1).split(",") if term.strip())
    return terms


def validate_generated_lesson(
    lesson: dict[str, Any],
    expected_level: str,
    expected_objective: str,
    expected_duration: int,
    *,
    expected_topic: str | None = None,
    constraints: list[Any] | None = None,
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

    generated_text = _flatten_text(lesson).casefold()
    if expected_topic and expected_topic.casefold() not in generated_text:
        errors.append("CONTENT_TOPIC_MISSING")

    for term in _forbidden_terms(constraints or []):
        if term.casefold() in generated_text:
            errors.append("CONTENT_FORBIDDEN_TERM")
            break

    return errors


def generation_status(errors: list[str]) -> str:
    """Map validation findings to the generation workflow state."""
    return "VALID" if not errors else "QC_REQUIRED"
