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
    """Run blocking structural/alignment checks on a generated lesson."""
    errors = validate_generated_lesson(
        lesson,
        expected_level=level,
        expected_objective=objective,
        expected_duration=duration_minutes,
    )

    return {
        "status": "READY" if not errors else "REJECT",
        "blocking_errors": errors,
        "checked": [
            "level_alignment",
            "objective_alignment",
            "duration",
            "activity_presence",
        ],
    }
