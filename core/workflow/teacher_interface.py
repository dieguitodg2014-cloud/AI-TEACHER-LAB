"""Teacher-facing facade over the AI Teacher Lab vertical slice.

This module keeps orchestration details out of the teacher experience. It does
not make pedagogical decisions; it only presents decisions already made by the
existing workflow in a concise, classroom-oriented contract.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass
from typing import Any

from core.workflow.vertical_slice import VerticalSliceResult, run_lesson_planning


@dataclass(frozen=True)
class TeacherLessonResult:
    """Stable, teacher-oriented representation of a lesson workflow result."""

    status: str
    title: str
    level: str | None
    audience: str | None
    duration_minutes: int | None
    objective: str | None
    lesson: dict[str, Any] | None
    activities: tuple[dict[str, Any], ...]
    assessment: dict[str, Any] | None
    resource: dict[str, Any] | None
    handoff: dict[str, Any] | None
    errors: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "lesson", deepcopy(self.lesson) if self.lesson is not None else None)
        object.__setattr__(self, "activities", tuple(deepcopy(activity) for activity in self.activities))
        object.__setattr__(self, "errors", tuple(self.errors))


def _activity_output(plan: Any) -> tuple[dict[str, Any], ...]:
    if plan is None:
        return ()
    return tuple(
        {
            "purpose": activity.purpose,
            "interaction": activity.interaction,
            "minutes": activity.minutes,
            "student_production": activity.student_production,
            "assessment_link": activity.assessment_link,
        }
        for activity in plan.sequence
    )


def _assessment_output(decision: Any) -> dict[str, Any] | None:
    if decision is None:
        return None
    return {
        "type": decision.type,
        "target": decision.target,
        "evidence": decision.evidence,
        "success_criteria": list(decision.success_criteria),
    }


def _generated_lesson(result: VerticalSliceResult) -> dict[str, Any] | None:
    if not result.generation:
        return None
    generated = result.generation.get("result")
    return deepcopy(generated) if isinstance(generated, dict) else None


def to_teacher_result(result: VerticalSliceResult) -> TeacherLessonResult:
    """Translate an internal workflow result into a stable teacher contract."""
    context = result.context
    generated = _generated_lesson(result)
    plan = result.learning_plan

    activities = ()
    if generated and isinstance(generated.get("activities"), list):
        activities = tuple(dict(activity) for activity in generated["activities"] if isinstance(activity, dict))
    if not activities:
        activities = _activity_output(plan)

    resource = None
    if result.resource_task is not None and result.resource_decision is not None:
        resource = {
            "action": result.resource_decision.action,
            "type": result.resource_decision.resource_type,
            "purpose": result.resource_decision.purpose,
            "required": result.resource_decision.required,
        }

    title = (context.topic if context else None) or (plan.objective if plan else None) or "Lesson Plan"
    return TeacherLessonResult(
        status=result.status,
        title=title,
        level=context.level if context else None,
        audience=context.audience if context else None,
        duration_minutes=context.duration_minutes if context else None,
        objective=plan.objective if plan else (context.objective if context else None),
        lesson=generated,
        activities=activities,
        assessment=_assessment_output(result.assessment_decision),
        resource=resource,
        handoff=deepcopy(result.resource_handoff),
        errors=result.errors,
    )


def plan_for_teacher(request: dict[str, Any] | str, **workflow_kwargs: Any) -> TeacherLessonResult:
    """Accept a teacher request and return the teacher-facing result."""
    return to_teacher_result(run_lesson_planning(request, **workflow_kwargs))


def teacher_result_to_dict(result: TeacherLessonResult) -> dict[str, Any]:
    """Serialize the teacher-facing contract for CLI, API, or UI use."""
    return asdict(result)


def _format_value(value: Any) -> str:
    if value is None:
        return "Not available"
    if isinstance(value, bool):
        return "Yes" if value else "No"
    return str(value)


def render_teacher_result(result: TeacherLessonResult) -> str:
    """Render the stable teacher contract as concise, classroom-readable text."""
    lines = [
        result.title,
        "=" * len(result.title),
        f"Status: {_format_value(result.status)}",
        f"Level: {_format_value(result.level)}",
        f"Audience: {_format_value(result.audience)}",
        f"Duration: {_format_value(result.duration_minutes)} minutes",
        "",
        "Learning objective",
        "------------------",
        _format_value(result.objective),
    ]

    if result.activities:
        lines.extend(["", "Lesson activities", "-----------------"])
        for index, activity in enumerate(result.activities, start=1):
            purpose = activity.get("purpose") or activity.get("name") or "Activity"
            lines.append(f"{index}. {purpose} ({_format_value(activity.get('minutes'))} min)")
            for key, label in (
                ("interaction", "Interaction"),
                ("student_production", "Student production"),
                ("assessment_link", "Assessment link"),
            ):
                value = activity.get(key)
                if value:
                    lines.append(f"   {label}: {value}")

    if result.assessment:
        assessment = result.assessment
        lines.extend(["", "Assessment", "----------"])
        lines.append(f"Type: {_format_value(assessment.get('type'))}")
        lines.append(f"Target: {_format_value(assessment.get('target'))}")
        lines.append(f"Evidence: {_format_value(assessment.get('evidence'))}")
        criteria = assessment.get("success_criteria") or []
        if criteria:
            lines.append("Success criteria:")
            lines.extend(f"- {criterion}" for criterion in criteria)

    if result.lesson:
        teacher_notes = result.lesson.get("teacher_notes")
        if teacher_notes:
            lines.extend(["", "Teacher notes", "-------------", str(teacher_notes)])

    if result.resource:
        resource = result.resource
        lines.extend(["", "Resource", "--------"])
        lines.append(f"Action: {_format_value(resource.get('action'))}")
        lines.append(f"Type: {_format_value(resource.get('type'))}")
        lines.append(f"Purpose: {_format_value(resource.get('purpose'))}")
        lines.append(f"Required: {_format_value(resource.get('required'))}")

    if result.handoff:
        lines.extend(["", "Next action", "----------"])
        for key in ("reason", "action", "message"):
            value = result.handoff.get(key)
            if value:
                lines.append(f"{key.replace('_', ' ').title()}: {value}")

    if result.errors:
        lines.extend(["", "Issues", "------"])
        lines.extend(f"- {error}" for error in result.errors)

    return "\n".join(lines)
