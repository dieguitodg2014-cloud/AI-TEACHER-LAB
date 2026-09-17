"""Teacher-facing presentation contract for accepted lessons.

This module only materializes already-approved workflow decisions. It does not
make pedagogical, provider, QC, or acceptance decisions.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from core.foundation.models import FrozenMapping, Level
from core.workflow.vertical_slice import VerticalSliceResult


@dataclass(frozen=True)
class TeacherLessonActivity:
    """Classroom-facing activity summary derived from an approved plan."""

    activity_id: str
    purpose: str
    interaction: str
    minutes: int
    student_production: str = ""
    assessment_link: str = ""


@dataclass(frozen=True)
class TeacherLessonCard:
    """Stable, presentation-only contract for an accepted lesson."""

    version: str
    level: Level
    audience: str
    objective: str
    duration_minutes: int
    activities: tuple[TeacherLessonActivity, ...]
    assessment: FrozenMapping
    resource: FrozenMapping | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "activities", tuple(self.activities))
        if self.resource is not None and not isinstance(self.resource, FrozenMapping):
            object.__setattr__(self, "resource", FrozenMapping(self.resource))
        if not isinstance(self.assessment, FrozenMapping):
            object.__setattr__(self, "assessment", FrozenMapping(self.assessment))


def teacher_lesson_card_from_result(result: VerticalSliceResult) -> TeacherLessonCard:
    """Materialize an accepted VerticalSliceResult without changing its decisions."""
    if result.status != "READY":
        raise ValueError("Teacher Lesson Card requires an accepted READY result")
    if result.context is None or result.learning_plan is None or result.assessment_decision is None:
        raise ValueError("Accepted result is missing required teacher-facing decisions")

    activities = tuple(
        TeacherLessonActivity(
            activity_id=activity.activity_id,
            purpose=activity.purpose,
            interaction=activity.interaction,
            minutes=activity.minutes,
            student_production=activity.student_production,
            assessment_link=activity.assessment_link,
        )
        for activity in result.learning_plan.sequence
    )

    assessment = {
        "type": result.assessment_decision.type,
        "target": result.assessment_decision.target,
        "evidence": result.assessment_decision.evidence,
        "success_criteria": result.assessment_decision.success_criteria,
    }

    resource: dict[str, Any] | None = None
    if result.resource_task is not None:
        resource = {
            "required_output": result.resource_task.required_output,
            "purpose": result.resource_decision.purpose if result.resource_decision else "",
            "tool_id": result.resource_tool.id if result.resource_tool is not None else "",
        }

    return TeacherLessonCard(
        version="v1",
        level=result.context.level,
        audience=result.context.audience,
        objective=result.context.objective,
        duration_minutes=result.context.duration_minutes,
        activities=activities,
        assessment=FrozenMapping(assessment),
        resource=FrozenMapping(resource) if resource is not None else None,
    )
