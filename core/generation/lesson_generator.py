"""Provider-agnostic lesson generation contract."""

from __future__ import annotations

from typing import Any, Protocol

from core.foundation.models import AssessmentDecision


class LessonGenerator(Protocol):
    """Callable contract for an AI model or another lesson-generation provider."""

    def __call__(
        self,
        generation_request: dict[str, Any],
        previous_errors: list[str],
    ) -> dict[str, Any]:
        """Generate a lesson from a constrained request and prior QC errors."""
        ...


def build_generation_request(
    plan: Any,
    context: dict[str, Any],
    assessment_decision: AssessmentDecision | None = None,
) -> dict[str, Any]:
    """Create the constrained request sent to a generation adapter."""
    request = {
        "objective": plan.objective,
        "level": context.get("level"),
        "audience": context.get("audience"),
        "duration_minutes": context.get("duration_minutes"),
        "topic": context.get("topic"),
        "prior_knowledge": context.get("prior_knowledge", []),
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

    if assessment_decision is not None:
        request["assessment_decision"] = {
            "assessment_id": assessment_decision.assessment_id,
            "type": assessment_decision.type,
            "target": assessment_decision.target,
            "evidence": assessment_decision.evidence,
            "success_criteria": list(assessment_decision.success_criteria),
        }

    return request
