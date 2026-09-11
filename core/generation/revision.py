"""Controlled revision loop for generated lesson artifacts."""

from __future__ import annotations

from typing import Any, Callable

from core.quality.generation_qc import review_generated_lesson


Generator = Callable[[dict[str, Any], list[str]], dict[str, Any]]


def generate_with_revision(
    generator: Generator,
    generation_request: dict[str, Any],
    *,
    max_revisions: int = 2,
) -> dict[str, Any]:
    """Generate, pass through the QC gate, and request bounded revisions."""
    expected_level = generation_request.get("level")
    expected_objective = generation_request.get("objective")
    expected_duration = generation_request.get("duration_minutes")
    expected_topic = generation_request.get("topic")
    constraints = generation_request.get("constraints", [])
    assessment_decision = generation_request.get("assessment_decision")

    if not isinstance(expected_level, str) or not isinstance(expected_objective, str):
        return {"status": "FAILED", "lesson": None, "errors": ["INVALID_GENERATION_REQUEST"]}
    if not isinstance(expected_duration, int) or expected_duration <= 0:
        return {"status": "FAILED", "lesson": None, "errors": ["INVALID_GENERATION_REQUEST"]}
    if expected_topic is not None and not isinstance(expected_topic, str):
        return {"status": "FAILED", "lesson": None, "errors": ["INVALID_GENERATION_REQUEST"]}
    if not isinstance(constraints, list):
        return {"status": "FAILED", "lesson": None, "errors": ["INVALID_GENERATION_REQUEST"]}
    if assessment_decision is not None and not isinstance(assessment_decision, dict):
        return {"status": "FAILED", "lesson": None, "errors": ["INVALID_GENERATION_REQUEST"]}
    if not isinstance(max_revisions, int) or max_revisions < 0:
        return {"status": "FAILED", "lesson": None, "errors": ["INVALID_GENERATION_REQUEST"]}

    attempts = 0
    errors: list[str] = []
    lesson: dict[str, Any] | None = None
    qc_result: dict[str, Any] | None = None

    while attempts <= max_revisions:
        try:
            lesson = generator(generation_request, errors)
        except Exception as exc:
            return {
                "status": "FAILED",
                "lesson": None,
                "errors": ["EXECUTION_ERROR", f"{type(exc).__name__}: {exc}"],
                "attempts": attempts + 1,
                "qc": None,
            }

        qc_result = review_generated_lesson(
            lesson,
            level=expected_level,
            objective=expected_objective,
            duration_minutes=expected_duration,
            topic=expected_topic,
            constraints=constraints,
            assessment_decision=assessment_decision,
        )
        errors = list(qc_result["blocking_errors"])
        if qc_result["status"] == "READY":
            return {
                "status": "READY",
                "lesson": lesson,
                "errors": [],
                "attempts": attempts + 1,
                "qc": qc_result,
            }
        attempts += 1

    return {
        "status": "REJECT",
        "lesson": lesson,
        "errors": errors,
        "attempts": attempts,
        "qc": qc_result,
    }
