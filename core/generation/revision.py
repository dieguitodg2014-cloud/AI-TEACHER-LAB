"""Controlled revision loop for generated lesson artifacts."""

from __future__ import annotations

import re
from typing import Any, Callable

from core.orchestration.provider_contract import validate_provider_output
from core.quality.generation_qc import review_generated_lesson


Generator = Callable[[dict[str, Any], list[str]], dict[str, Any]]

_GENERIC_PRODUCTION = {
    "produce language demonstrating the lesson objective.",
    "provide an observable performance or response.",
    "complete a meaningful interaction task.",
    "use the target language in a supported exchange.",
}


def _observable_action_from_objective(objective: str) -> str | None:
    """Extract the observable action phrase from a simple learner objective."""
    match = re.match(r"^\s*(?:students|learners)\s+will\s+(.+?)\s*$", objective, flags=re.IGNORECASE)
    if match:
        return match.group(1).strip().rstrip(".")
    return None


def _repair_generic_production_fields(
    lesson: dict[str, Any],
    objective: str,
    errors: list[str],
) -> dict[str, Any]:
    """Repair provider placeholders when QC identifies an observable-action mismatch.

    This is a bounded contract safeguard, not a pedagogical decision. The approved
    objective remains authoritative; only generic production placeholders are rewritten
    so they state the observable action already required by that objective.
    """
    if "OBJECTIVE_PRODUCTION_MISMATCH" not in errors:
        return lesson

    action = _observable_action_from_objective(objective)
    if not action:
        return lesson

    activities = lesson.get("activities")
    if not isinstance(activities, list):
        return lesson

    repaired = dict(lesson)
    repaired_activities: list[Any] = []
    for activity in activities:
        if not isinstance(activity, dict):
            repaired_activities.append(activity)
            continue

        production = str(activity.get("student_production", "")).strip()
        if production.casefold() in _GENERIC_PRODUCTION:
            updated = dict(activity)
            updated["student_production"] = action
            repaired_activities.append(updated)
        else:
            repaired_activities.append(activity)

    repaired["activities"] = repaired_activities
    return repaired


def generate_with_revision(
    generator: Generator,
    generation_request: dict[str, Any],
    *,
    max_revisions: int = 2,
) -> dict[str, Any]:
    """Generate, validate the provider boundary, pass through QC, and revise."""
    expected_level = generation_request.get("level")
    expected_objective = generation_request.get("objective")
    expected_duration = generation_request.get("duration_minutes")
    expected_topic = generation_request.get("topic")
    constraints = generation_request.get("constraints", [])
    assessment_decision = generation_request.get("assessment_decision")
    approved_sequence = generation_request.get("sequence")

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
    if approved_sequence is not None and not isinstance(approved_sequence, list):
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

        provider_errors = validate_provider_output(lesson)
        if provider_errors:
            return {
                "status": "FAILED",
                "lesson": lesson if isinstance(lesson, dict) else None,
                "errors": provider_errors,
                "attempts": attempts + 1,
                "qc": None,
            }

        lesson = _repair_generic_production_fields(lesson, expected_objective, errors)
        qc_result = review_generated_lesson(
            lesson,
            level=expected_level,
            objective=expected_objective,
            duration_minutes=expected_duration,
            topic=expected_topic,
            constraints=constraints,
            assessment_decision=assessment_decision,
            approved_sequence=approved_sequence,
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
