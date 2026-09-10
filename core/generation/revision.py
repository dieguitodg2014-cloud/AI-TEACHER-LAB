"""Controlled revision loop for generated lesson artifacts."""

from __future__ import annotations

from typing import Any, Callable

from core.generation.output_validator import validate_generated_lesson


Generator = Callable[[dict[str, Any], list[str]], dict[str, Any]]


def generate_with_revision(
    generator: Generator,
    generation_request: dict[str, Any],
    *,
    max_revisions: int = 2,
) -> dict[str, Any]:
    """Generate, validate, and request bounded revisions without pedagogical drift."""
    expected_level = generation_request.get("level")
    expected_objective = generation_request.get("objective")
    expected_duration = generation_request.get("duration_minutes")

    if not isinstance(expected_level, str) or not isinstance(expected_objective, str):
        return {"status": "FAILED", "lesson": None, "errors": ["INVALID_GENERATION_REQUEST"]}
    if not isinstance(expected_duration, int) or expected_duration <= 0:
        return {"status": "FAILED", "lesson": None, "errors": ["INVALID_GENERATION_REQUEST"]}

    attempts = 0
    errors: list[str] = []
    lesson: dict[str, Any] | None = None

    while attempts <= max_revisions:
        lesson = generator(generation_request, errors)
        errors = validate_generated_lesson(
            lesson,
            expected_level=expected_level,
            expected_objective=expected_objective,
            expected_duration=expected_duration,
        )
        if not errors:
            return {"status": "READY", "lesson": lesson, "errors": [], "attempts": attempts + 1}
        attempts += 1

    return {
        "status": "REJECT",
        "lesson": lesson,
        "errors": errors,
        "attempts": attempts,
    }
