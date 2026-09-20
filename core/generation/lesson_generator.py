"""Provider-agnostic lesson generation contract."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Protocol

from core.foundation.models import AssessmentDecision


class LessonGenerator(Protocol):
    """Callable contract for an AI model or another lesson-generation provider."""

    def __call__(
        self,
        generation_request: Mapping[str, Any],
        previous_errors: list[str],
    ) -> dict[str, Any]:
        """Generate a lesson from a constrained request and prior QC errors."""
        ...


def build_generation_request(
    plan: Any,
    context: dict[str, Any],
    assessment_decision: AssessmentDecision | None = None,
    resource_decision: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Create the constrained request sent to a generation adapter."""
    request = {
        "objective": plan.objective,
        "level": context.get("level"),
        "audience": context.get("audience"),
        "duration_minutes": context.get("duration_minutes"),
        "topic": context.get("topic"),
        "prior_knowledge": list(context.get("prior_knowledge", [])),
        "activity_contracts": [
            {
                "activity_id": activity.activity_id,
                "level": context.get("level"),
                "objective": plan.objective,
                "skill": activity.skill,
                "interaction": activity.interaction,
                "cognitive_demand": activity.cognitive_demand,
                "scaffolding": activity.scaffolding,
                "duration_minutes": activity.minutes,
                "language_target": activity.language_target,
                "must_include": [context.get("topic")] if context.get("topic") else [],
                "must_not_include": [],
                "evidence": activity.assessment_link or activity.student_production,
            }
            for activity in plan.sequence
        ],
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
        "teacher_execution_contract": {
            "teacher_explanation": "Clear teacher-facing explanation of the target language and lesson focus.",
            "target_language": ["Exact target structures or forms to teach and practice."],
            "language_bank": ["Level-appropriate words, phrases, and sentence frames learners can use."],
            "teacher_talk": ["Ready-to-use teacher prompts and model language."],
            "ccqs": ["Concept-checking questions appropriate to the target language."],
            "examples": ["Accurate level-appropriate examples."],
            "common_errors": {"error": "correction or brief corrective guidance"},
            "scaffolding": ["Concrete support a teacher can provide before or during practice."],
            "materials": ["Materials needed to run the lesson."],
            "worksheet": {"title": "Student worksheet", "items": []},
            "role_cards": ["Optional speaking or role-card content when required by the lesson."],
            "answer_key": {"answers": []},
            "assessment_checklist": ["Observable criteria linked to the approved assessment."],
            "exit_ticket": {"prompt": "A short final check of learning."},
        },
        "resource_need": plan.resource_need,
        "constraints": list(context.get("constraints", [])),
    }

    if assessment_decision is not None:
        request["assessment_decision"] = {
            "assessment_id": assessment_decision.assessment_id,
            "type": assessment_decision.type,
            "target": assessment_decision.target,
            "evidence": assessment_decision.evidence,
            "success_criteria": list(assessment_decision.success_criteria),
        }

    if resource_decision is not None:
        request["resource_decision"] = dict(resource_decision)

    return request
