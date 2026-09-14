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
        object.__setattr__(self, "resource", deepcopy(self.resource) if self.resource is not None else None)
        object.__setattr__(self, "handoff", deepcopy(self.handoff) if self.handoff is not None else None)
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
    """Expose the actual generated lesson, not its orchestration envelope."""
    if not result.generation:
        return None
    generated = result.generation.get("result")
    if not isinstance(generated, dict):
        return None
    # GenerationOrchestrator returns an execution envelope. The teacher
    # contract exposes its lesson payload while keeping the internal envelope
    # out of the classroom-facing result.
    lesson = generated.get("lesson")
    if isinstance(lesson, dict):
        return deepcopy(lesson)
    return deepcopy(generated)


def _accepted_resource(result: VerticalSliceResult) -> dict[str, Any] | None:
    """Return only the exact resource that crossed the acceptance boundary."""
    if result.status != "ACCEPTED" or not result.generation:
        return None
    resource = result.generation.get("result")
    if not isinstance(resource, dict):
        return None
    return deepcopy(resource)


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
        accepted = _accepted_resource(result)
        if accepted is not None:
            resource["output"] = accepted

    title = (context.topic if context else None) or (plan.objective if plan else None) or "Lesson Plan"
    errors = result.errors or tuple(result.missing)
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
        errors=errors,
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
    """Render a concise classroom-readable representation."""
    lines = [
        f"Title: {result.title}",
        f"Status: {result.status}",
        f"Level: {_format_value(result.level)}",
        f"Audience: {_format_value(result.audience)}",
        f"Duration: {_format_value(result.duration_minutes)} minutes",
    ]
    if result.objective:
        lines.extend(["", "Learning objective", result.objective])
    if result.activities:
        lines.extend(["", "Lesson activities"])
        for index, activity in enumerate(result.activities, start=1):
            purpose = activity.get("purpose") or activity.get("name") or "Activity"
            lines.append(f"{index}. {purpose} ({activity.get('minutes', '?')} min, {activity.get('interaction', 'class')})")
            if activity.get("student_production"):
                lines.append(f"   Student production: {activity['student_production']}")
    if result.assessment:
        lines.extend(["", "Assessment", _format_value(result.assessment)])
    if result.lesson and result.lesson.get("teacher_notes"):
        lines.extend(["", "Teacher notes", str(result.lesson["teacher_notes"])])
    if result.resource:
        lines.extend(["", "Resource", _format_value({k: v for k, v in result.resource.items() if k != "output"})])
        if isinstance(result.resource.get("output"), dict):
            output = result.resource["output"]
            lines.extend(["", "Accepted resource"])
            if output.get("content") is not None:
                lines.append(str(output["content"]))
            else:
                lines.append(_format_value(output))
    if result.handoff:
        lines.extend(["", "Next action", _format_value(result.handoff)])
    if result.errors:
        lines.extend(["", "Issues"])
        lines.extend(f"- {error}" for error in result.errors)
    return "\n".join(lines)
