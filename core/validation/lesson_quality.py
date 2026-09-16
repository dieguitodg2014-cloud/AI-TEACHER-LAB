"""Independent validation of generated lesson plans.

This module deliberately sits upstream of resource production. It validates a
lesson against an immutable TaskPacket without mutating or redefining that
packet. External validators can implement the same provider-neutral contract.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, Mapping
from uuid import uuid4

from core.foundation.models import TaskPacket

LessonValidationStatus = Literal["READY", "REVISION_REQUIRED", "CRITICAL_FAILURE"]


@dataclass(frozen=True)
class LessonValidationResult:
    """Read-only result returned by an independent lesson validator."""

    validation_id: str
    status: LessonValidationStatus
    score: float | None
    checks: Mapping[str, bool]
    critical_failures: tuple[str, ...] = ()
    revision_required: tuple[str, ...] = ()
    strengths: tuple[str, ...] = ()
    missing_evidence: tuple[str, ...] = ()


class LessonQualityValidator:
    """Provider-neutral interface for independent lesson validation."""

    def validate(
        self,
        task: TaskPacket,
        lesson: Mapping[str, Any],
        *,
        request: Mapping[str, Any] | None = None,
    ) -> LessonValidationResult:
        raise NotImplementedError


def validate_lesson_structure(
    task: TaskPacket,
    lesson: Mapping[str, Any],
    *,
    request: Mapping[str, Any] | None = None,
) -> LessonValidationResult:
    """Run deterministic structural checks before an external semantic validator.

    The lesson is copied into local read-only access; the authoritative task is
    never rewritten from generated output.
    """
    checks: dict[str, bool] = {}
    critical: list[str] = []
    revision: list[str] = []
    strengths: list[str] = []

    checks["lesson_present"] = bool(lesson)
    if not checks["lesson_present"]:
        critical.append("Generated lesson is missing or empty.")

    level = str(lesson.get("level", "")).strip().upper()
    checks["level_alignment"] = level == task.level
    if not checks["level_alignment"]:
        critical.append(f"Level mismatch: expected '{task.level}', got '{level or 'missing'}'.")

    audience = str(lesson.get("audience", "")).strip()
    checks["audience_alignment"] = not task.audience.strip() or task.audience.strip().lower() in audience.lower()
    if not checks["audience_alignment"]:
        revision.append("Lesson audience does not provide evidence of alignment with the authoritative TaskPacket audience.")

    objectives = lesson.get("objectives") or lesson.get("learning_objectives")
    checks["objectives_present"] = isinstance(objectives, (list, tuple)) and bool(objectives)
    if not checks["objectives_present"]:
        revision.append("Learning objectives are missing or not represented as a non-empty list.")

    activities = lesson.get("activities")
    stages = lesson.get("stages")
    checks["lesson_sequence_present"] = bool(activities or stages or lesson.get("warm_up"))
    if not checks["lesson_sequence_present"]:
        revision.append("No usable lesson activity sequence was found.")

    duration = task.duration_minutes
    total = _sum_stage_minutes(lesson)
    checks["timing_alignment"] = total is None or total == duration
    if total is not None and total != duration:
        revision.append(f"Timing mismatch: requested {duration} minutes, lesson stages total {total} minutes.")

    assessment = lesson.get("assessment") or lesson.get("check_for_learning")
    checks["assessment_present"] = bool(assessment)
    if not checks["assessment_present"]:
        revision.append("Assessment/check for learning is missing.")

    interaction = lesson.get("interaction") or lesson.get("interaction_format")
    checks["interaction_evidence"] = bool(interaction) or bool(request and request.get("group_size"))
    if not checks["interaction_evidence"]:
        revision.append("Interaction format is not sufficiently specified to verify feasibility.")

    if all(checks.values()):
        strengths.append("Deterministic structural checks passed.")

    if critical:
        status: LessonValidationStatus = "CRITICAL_FAILURE"
        score = 0.0
    elif revision:
        status = "REVISION_REQUIRED"
        score = _score(checks)
    else:
        status = "READY"
        score = _score(checks)

    return LessonValidationResult(
        validation_id=f"lesson-qc-{uuid4().hex[:12]}",
        status=status,
        score=score,
        checks=checks,
        critical_failures=tuple(critical),
        revision_required=tuple(revision),
        strengths=tuple(strengths),
    )


def _sum_stage_minutes(lesson: Mapping[str, Any]) -> int | None:
    stages = lesson.get("stages") or lesson.get("activities")
    if not isinstance(stages, (list, tuple)):
        return None
    values: list[int] = []
    for stage in stages:
        if not isinstance(stage, Mapping):
            return None
        value = stage.get("minutes", stage.get("duration"))
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return None
        values.append(int(value))
    return sum(values)


def _score(checks: Mapping[str, bool]) -> float | None:
    if not checks:
        return None
    return round(sum(checks.values()) / len(checks) * 100, 2)
