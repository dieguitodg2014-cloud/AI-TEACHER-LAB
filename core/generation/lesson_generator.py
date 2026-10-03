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


def _build_generation_view(
    generation_request: Mapping[str, Any],
) -> dict[str, Any]:
    """Build a compact, generation-focused view of the full request."""
    contracts = generation_request.get("activity_contracts", [])
    sequence = generation_request.get("sequence", [])

    activities = []

    for contract, sequence_item in zip(contracts, sequence):
        activities.append(
            {
                "activity_id": contract.get("activity_id"),
                "minutes": contract.get("duration_minutes"),
                "skill": contract.get("skill"),
                "interaction": contract.get("interaction"),
                "cognitive_demand": contract.get("cognitive_demand"),
                "scaffolding": contract.get("scaffolding"),
                "language_target": contract.get("language_target"),
                "evidence": contract.get("evidence"),
                "student_production": sequence_item.get("student_production"),
                "assessment_link": sequence_item.get("assessment_link"),
            }
        )

    return {
        "level": generation_request.get("level"),
        "audience": generation_request.get("audience"),
        "duration_minutes": generation_request.get("duration_minutes"),
        "objective": generation_request.get("objective"),
        "topic": generation_request.get("topic"),
        "teacher_facing": generation_request.get("teacher_facing", False),
        "activities": activities,
    }


def _build_generation_contract(
    generation_request: Mapping[str, Any],
) -> dict[str, Any]:
    """Build the explicit boundary between system authority and model generation.

    The system-owned fields define the approved pedagogical structure.
    The generation fields identify the content the model is allowed to produce
    within that structure.
    """
    contracts = generation_request.get("activity_contracts", [])
    sequence = generation_request.get("sequence", [])

    activities = []

    for contract, sequence_item in zip(contracts, sequence):
        activities.append(
            {
                "activity_id": contract.get("activity_id"),
                "approved": {
                    "level": contract.get("level"),
                    "objective": contract.get("objective"),
                    "skill": contract.get("skill"),
                    "interaction": contract.get("interaction"),
                    "cognitive_demand": contract.get("cognitive_demand"),
                    "scaffolding": contract.get("scaffolding"),
                    "duration_minutes": contract.get("duration_minutes"),
                    "language_target": contract.get("language_target"),
                    "evidence": contract.get("evidence"),
                },
                "instructional_intent": {
                    "student_production": sequence_item.get("student_production"),
                    "assessment_link": sequence_item.get("assessment_link"),
                    "purpose": sequence_item.get("purpose"),
                },
                "generate": [
                    "instructions",
                    "purpose",
                ],
                "controlled_rewrite": [
                    "student_production",
                    "assessment_link",
                ],
            }
        )

    return {
        "system_authority": {
            "level": generation_request.get("level"),
            "audience": generation_request.get("audience"),
            "duration_minutes": generation_request.get("duration_minutes"),
            "objective": generation_request.get("objective"),
            "topic": generation_request.get("topic"),
            "constraints": list(generation_request.get("constraints", [])),
            "activities": activities,
        },
        "model_role": {
            "generate_content_within_approved_structure": True,
            "may_rewrite_instructional_wording": True,
            "may_rewrite_student_production_for_clarity": True,
            "may_rewrite_assessment_link_for_clarity": True,
            "may_change_pedagogical_structure": False,
            "may_change_activity_order": False,
            "may_change_activity_count": False,
            "may_change_activity_duration": False,
            "may_change_approved_evidence": False,
            "may_invent_assessment_resources": False,
        },
    }


def build_generation_request(
    plan: Any,
    context: dict[str, Any],
    assessment_decision: AssessmentDecision | None = None,
    resource_decision: Mapping[str, Any] | None = None,
    *,
    teacher_facing: bool = False,
) -> dict[str, Any]:
    """Create the constrained request sent to a generation adapter."""
    if not isinstance(teacher_facing, bool):
        raise TypeError("teacher_facing must be a bool")

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
                "must_include": [context.get("topic")]
                if context.get("topic")
                else [],
                "must_not_include": [],
                "evidence": activity.assessment_link
                or activity.student_production,
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
        "teacher_facing": teacher_facing,
        "teacher_execution_contract": {
            "teacher_explanation": (
                "Clear teacher-facing explanation of the target language "
                "and lesson focus."
            ),
            "target_language": [
                "Exact target structures or forms to teach and practice."
            ],
            "language_bank": [
                "Level-appropriate words, phrases, and sentence frames "
                "learners can use."
            ],
            "teacher_talk": [
                "Ready-to-use teacher prompts and model language."
            ],
            "ccqs": [
                "Concept-checking questions appropriate to the target language."
            ],
            "examples": [
                "Accurate level-appropriate examples."
            ],
            "common_errors": {
                "error": "correction or brief corrective guidance"
            },
            "scaffolding": [
                "Concrete support a teacher can provide before or during practice."
            ],
            "materials": [
                "Materials needed to run the lesson."
            ],
            "worksheet": {
                "title": "Student worksheet",
                "items": [],
            },
            "role_cards": [
                "Optional speaking or role-card content when required by the lesson."
            ],
            "answer_key": {
                "answers": [],
            },
            "assessment_checklist": [
                "Observable criteria linked to the approved assessment."
            ],
            "exit_ticket": {
                "prompt": "A short final check of learning."
            },
        },
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

    request["generation_contract"] = _build_generation_contract(request)

    return request
