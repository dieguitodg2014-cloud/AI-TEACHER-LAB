"""Independent validation of generated lesson plans.

This module deliberately sits upstream of resource production. Lesson
validation uses the authoritative Context and approved learning-plan inputs;
resource TaskPackets remain owned by the resource-production boundary.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Mapping
from uuid import uuid4

from core.foundation.models import Context, LearningPlanDecision

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
        context: Context,
        lesson: Mapping[str, Any],
        *,
        learning_plan: LearningPlanDecision | None = None,
        request: Mapping[str, Any] | None = None,
    ) -> LessonValidationResult:
        raise NotImplementedError


def validate_lesson_structure(
    context: Context,
    lesson: Mapping[str, Any],
    *,
    learning_plan: LearningPlanDecision | None = None,
    request: Mapping[str, Any] | None = None,
) -> LessonValidationResult:
    """Run deterministic structural checks before external semantic validation."""
    checks: dict[str, bool] = {}
    critical: list[str] = []
    revision: list[str] = []
    strengths: list[str] = []

    checks["lesson_present"] = bool(lesson)
    if not checks["lesson_present"]:
        critical.append("Generated lesson is missing or empty.")

    level = str(lesson.get("level", "")).strip().upper()
    checks["level_alignment"] = level == context.level
    if not checks["level_alignment"]:
        critical.append(f"Level mismatch: expected '{context.level}', got '{level or 'missing'}'.")

    audience = str(lesson.get("audience", "")).strip()
    checks["audience_alignment"] = not context.audience.strip() or context.audience.strip().lower() in audience.lower()
    if not checks["audience_alignment"]:
        revision.append("Lesson audience does not provide evidence of alignment with the authoritative context audience.")

    objectives = lesson.get("objectives") or lesson.get("learning_objectives")
    checks["objectives_present"] = isinstance(objectives, (list, tuple)) and bool(objectives)
    if not checks["objectives_present"]:
        revision.append("Learning objectives are missing or not represented as a non-empty list.")

    activities = lesson.get("activities")
    stages = lesson.get("stages")
    checks["lesson_sequence_present"] = bool(activities or stages or lesson.get("warm_up"))
    if not checks["lesson_sequence_present"]:
        revision.append("No usable lesson activity sequence was found.")

    total = _sum_stage_minutes(lesson)
    checks["timing_alignment"] = total is None or total == context.duration_minutes
    if total is not None and total != context.duration_minutes:
        revision.append(f"Timing mismatch: requested {context.duration_minutes} minutes, lesson stages total {total} minutes.")

    if learning_plan is not None:
        checks["approved_plan_timing"] = learning_plan.total_minutes == context.duration_minutes
        if not checks["approved_plan_timing"]:
            critical.append("Approved learning plan duration does not match the authoritative context duration.")

    assessment = lesson.get("assessment") or lesson.get("check_for_learning")
    checks["assessment_present"] = bool(assessment)
    if not checks["assessment_present"]:
        revision.append("Assessment/check for learning is missing.")

    interaction = lesson.get("interaction") or lesson.get("interaction_format")
    checks["interaction_evidence"] = bool(interaction) or bool(context.group_size)
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
