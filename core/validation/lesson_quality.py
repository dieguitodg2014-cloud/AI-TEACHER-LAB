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
    """Run deterministic structural checks before external semantic validation.

    The authoritative Context and approved learning plan are the source of
    truth. Redundant lesson metadata is validated when present, but its
    absence is not itself treated as a pedagogical failure. An explicit
    contradiction remains a failure signal.
    """
    checks: dict[str, bool] = {}
    critical: list[str] = []
    revision: list[str] = []
    strengths: list[str] = []

    checks["lesson_present"] = bool(lesson)
    if not checks["lesson_present"]:
        critical.append("Generated lesson is missing or empty.")

    level = str(lesson.get("level", "")).strip().upper()
    checks["level_alignment"] = bool(level) and level == context.level
    if not checks["level_alignment"]:
        critical.append(f"Level mismatch: expected '{context.level}', got '{level or 'missing'}'.")

    # Audience is authoritative in Context. A lesson may omit the same
    # information without contradicting it; an explicit mismatch is a
    # revision finding.
    audience = str(lesson.get("audience", "")).strip()
    if audience:
        checks["audience_alignment"] = (
            not context.audience.strip()
            or context.audience.strip().lower() in audience.lower()
        )
        if not checks["audience_alignment"]:
            revision.append(
                "Lesson audience conflicts with the authoritative context audience."
            )
    else:
        checks["audience_alignment"] = True

    # Objectives are authoritative in Context/LearningPlan. Explicit lesson
    # objectives are checked for usable representation, but omitted redundant
    # metadata does not fail the gate when an authoritative objective exists.
    objectives = lesson.get("objectives") or lesson.get("learning_objectives")
    objective_text = str(lesson.get("objective", "")).strip()
    if objectives is not None:
        checks["objectives_present"] = isinstance(objectives, (list, tuple)) and bool(objectives)
        if not checks["objectives_present"]:
            revision.append("Learning objectives are present but not represented as a non-empty list.")
    elif objective_text:
        checks["objectives_present"] = True
    elif getattr(learning_plan, "objective", None):
        checks["objectives_present"] = True
    else:
        # No redundant objective field and no approved objective to verify.
        # Leave semantic completeness to the independent validator.
        checks["objectives_present"] = True

    activities = lesson.get("activities")
    stages = lesson.get("stages")
    checks["lesson_sequence_present"] = bool(activities or stages or lesson.get("warm_up"))
    if not checks["lesson_sequence_present"]:
        revision.append("No usable lesson activity sequence was found.")

    total = _sum_stage_minutes(lesson)
    checks["timing_alignment"] = total is None or total == context.duration_minutes
    if total is not None and total != context.duration_minutes:
        revision.append(
            f"Timing mismatch: requested {context.duration_minutes} minutes, "
            f"lesson stages total {total} minutes."
        )

    if learning_plan is not None:
        checks["approved_plan_timing"] = learning_plan.total_minutes == context.duration_minutes
        if not checks["approved_plan_timing"]:
            critical.append("Approved learning plan duration does not match the authoritative context duration.")

    # Assessment evidence can live on the lesson itself or on an activity.
    # If an approved plan already defines evidence of learning, that is
    # authoritative enough to avoid requiring duplicate top-level metadata.
    assessment = lesson.get("assessment") or lesson.get("check_for_learning")
    activity_assessment = _has_activity_field(activities or stages, "assessment_link")
    approved_evidence = bool(getattr(learning_plan, "evidence_of_learning", None))
    checks["assessment_present"] = bool(assessment) or activity_assessment or approved_evidence
    if not checks["assessment_present"]:
        revision.append("Assessment/check for learning is missing or not evidenced.")

    # Interaction may be represented at lesson or activity level. The
    # presence of an activity sequence is enough for this structural gate;
    # semantic feasibility and contradictions belong to the independent
    # validator.
    interaction = lesson.get("interaction") or lesson.get("interaction_format")
    activity_interaction = _has_activity_field(activities or stages, "interaction")
    checks["interaction_evidence"] = bool(interaction or activity_interaction or activities or stages)
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


def _has_activity_field(value: Any, field: str) -> bool:
    """Return whether at least one activity/stage explicitly provides field evidence."""
    if not isinstance(value, (list, tuple)):
        return False
    return any(
        isinstance(item, Mapping) and bool(str(item.get(field, "")).strip())
        for item in value
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
