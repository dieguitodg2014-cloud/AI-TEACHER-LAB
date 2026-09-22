"""Minimal structural alignment validation for teacher-facing lessons."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def _meaningful_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _meaningful_sequence(value: Any) -> bool:
    return (
        isinstance(value, (list, tuple))
        and bool(value)
        and any(_meaningful_text(item) for item in value)
    )


def validate_teacher_facing_alignment(
    lesson: Mapping[str, Any],
) -> list[str]:
    """Validate the minimum observable alignment chain for teacher-facing lessons.

    This validator checks structural connections that already exist in the
    teacher-facing contract. It intentionally does not attempt deep semantic
    interpretation.
    """
    if not isinstance(lesson, Mapping):
        return ["INVALID_ALIGNMENT_INPUT"]

    errors: list[str] = []

    objective = lesson.get("objective")
    if not _meaningful_text(objective):
        errors.append("ALIGNMENT_OBJECTIVE_MISSING")

    execution = lesson.get("teacher_execution")
    if not isinstance(execution, Mapping):
        errors.append("ALIGNMENT_TEACHER_EXECUTION_MISSING")
        return errors

    target_language = execution.get("target_language")
    if not _meaningful_sequence(target_language):
        errors.append("ALIGNMENT_TARGET_LANGUAGE_MISSING")

    exit_ticket = execution.get("exit_ticket")
    if not isinstance(exit_ticket, Mapping) or not exit_ticket:
        errors.append("ALIGNMENT_EXIT_TICKET_MISSING")

    activities = lesson.get("activities")
    if not isinstance(activities, list) or not activities:
        errors.append("ALIGNMENT_ACTIVITIES_MISSING")
        return errors

    for index, activity in enumerate(activities, start=1):
        if not isinstance(activity, Mapping):
            errors.append(f"ALIGNMENT_ACTIVITY_INVALID:{index}")
            continue

        if not _meaningful_text(activity.get("language_target")):
            errors.append(f"ALIGNMENT_ACTIVITY_LANGUAGE_TARGET_MISSING:{index}")

        if not _meaningful_text(activity.get("assessment_link")):
            errors.append(f"ALIGNMENT_ACTIVITY_ASSESSMENT_LINK_MISSING:{index}")

    assessment = lesson.get("assessment")
    if not isinstance(assessment, Mapping) or not assessment:
        errors.append("ALIGNMENT_ASSESSMENT_MISSING")
    else:
        evidence = assessment.get("evidence")
        success_criteria = assessment.get("success_criteria")

        if not _meaningful_text(evidence):
            errors.append("ALIGNMENT_ASSESSMENT_EVIDENCE_MISSING")

        if not _meaningful_sequence(success_criteria):
            errors.append("ALIGNMENT_ASSESSMENT_CRITERIA_MISSING")

    return errors