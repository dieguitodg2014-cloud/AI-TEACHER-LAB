"""Provider-agnostic lesson generation contract."""

from __future__ import annotations

from typing import Any, Protocol

from core.foundation.models import LearningPlanDecision


class LessonGenerator(Protocol):
    """Adapter contract for an AI model or another lesson-generation provider."""

    def generate(self, plan: LearningPlanDecision, context: dict[str, Any]) -> dict[str, Any]:
        ...


def build_generation_request(
    plan: LearningPlanDecision,
    context: dict[str, Any],
) -> dict[str, Any]:
    """Create the constrained request sent to a future generation adapter."""
    return {
        "objective": plan.objective,
        "level": context.get("level"),
        "audience": context.get("audience"),
        "duration_minutes": context.get("duration_minutes"),
        "sequence": [
            {
                "purpose": activity.purpose,
                "interaction": activity.interaction,
                "minutes": activity.minutes,
                "student_production": activity.student_production,
                "assessment_link": activity.assessment_link,
            }
            for activity in plan.sequence
        ],
        "evidence_of_learning": plan.evidence_of_learning,
        "resource_need": plan.resource_need,
        "constraints": context.get("constraints", []),
    }
