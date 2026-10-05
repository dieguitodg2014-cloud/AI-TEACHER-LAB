"""Deterministic MVP lesson generator for end-to-end runtime validation.

This adapter is intentionally not an AI provider. It materializes the
authoritative pedagogical plan into a valid lesson artifact so the complete
Teacher Lab runtime can be exercised without paid APIs or external model
dependencies.

A real model provider can replace this adapter later without changing the
pedagogical workflow or generation contract.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def _activity_instructions(
    contract: Mapping[str, Any],
    sequence_item: Mapping[str, Any],
) -> str:
    """Create teacher-ready instructions without changing approved structure."""
    purpose = str(sequence_item.get("purpose", "")).strip()
    production = str(sequence_item.get("student_production", "")).strip()
    interaction = str(contract.get("interaction", "")).strip()

    parts = []

    if purpose:
        parts.append(f"Purpose: {purpose}.")

    if interaction:
        parts.append(f"Interaction: {interaction}.")

    if production:
        parts.append(f"Ask learners to {production.rstrip('.')}.")

    parts.append("Monitor learners and provide brief corrective support.")

    return " ".join(parts)


def _language_bank(contract: Mapping[str, Any]) -> list[str]:
    target = str(contract.get("language_target", "")).strip()

    if not target:
        return ["Use the target language from the lesson objective."]

    return [
        target,
        f"Use: {target}",
    ]


def _teacher_execution(
    generation_request: Mapping[str, Any],
) -> dict[str, Any]:
    """Build the teacher-facing execution package from approved information."""
    objective = str(generation_request["objective"]).strip()
    topic = str(
        generation_request.get("topic") or "the lesson topic"
    ).strip()
    contracts = generation_request.get("activity_contracts", [])

    assessment = generation_request.get("assessment_decision") or {}
    success_criteria = list(assessment.get("success_criteria", []))

    return {
        "teacher_explanation": (
            f"Teach and model the language needed for learners to "
            f"{objective.rstrip('.')}. Keep examples connected to {topic}."
        ),
        "target_language": [
            str(contract.get("language_target", "")).strip()
            for contract in contracts
            if str(contract.get("language_target", "")).strip()
        ],
        "language_bank": [
            phrase
            for contract in contracts
            for phrase in _language_bank(contract)
        ],
        "teacher_talk": [
            "Listen first.",
            "Work with your partner.",
            "Ask one follow-up question.",
            "Use the target language.",
        ],
        "ccqs": [
            f"Are we practicing how to {objective.rstrip('.')}?",
            "Are learners using the target language?",
        ],
        "examples": [
            f"Model one example related to {topic}.",
            f"Ask learners to demonstrate: {objective.rstrip('.')}.",
        ],
        "common_errors": {
            "Incorrect target-language form": (
                "Model the correct form and have the learner repeat it."
            )
        },
        "scaffolding": [
            "Model the task before learners begin.",
            "Provide the target-language frame when needed.",
            "Reduce support gradually as learners become more independent.",
        ],
        "materials": [
            "Teacher lesson plan",
            "Student worksheet",
        ],
        "worksheet": {
            "title": topic,
            "items": [
                f"Practice: {objective.rstrip('.')}.",
            ],
        },
        "role_cards": [
            "Student A asks or initiates.",
            "Student B responds and asks a follow-up question.",
        ],
        "answer_key": {
            "answers": success_criteria,
        },
        "assessment_checklist": success_criteria
        or [
            "Learner produces the required evidence.",
        ],
        "exit_ticket": {
            "prompt": (
                f"Show one example of how you can "
                f"{objective.rstrip('.')}."
            ),
        },
    }


def create_mvp_lesson_generator() -> callable:
    """Return the deterministic MVP generator callable."""

    def generate(
        generation_request: Mapping[str, Any],
        previous_errors: list[str],
    ) -> dict[str, Any]:
        del previous_errors

        contracts = generation_request.get("activity_contracts", [])
        sequence = generation_request.get("sequence", [])

        activities = []

        for index, (contract, sequence_item) in enumerate(
            zip(contracts, sequence),
            start=1,
        ):
            evidence = str(contract.get("evidence", "")).strip()

            student_production = str(
                sequence_item.get("student_production")
                or evidence
                or (
                    "produce language demonstrating the lesson objective."
                )
            ).strip()

            activity_evidence = str(
                sequence_item.get("assessment_link")
                or evidence
                or student_production
            ).strip()

            activities.append(
                {
                    "activity_id": contract.get(
                        "activity_id",
                        f"activity-{index}",
                    ),
                    "name": f"Activity {index}",
                    "level": contract.get("level"),
                    "objective": contract.get("objective"),
                    "skill": contract.get("skill"),
                    "interaction": contract.get("interaction"),
                    "cognitive_demand": contract.get(
                        "cognitive_demand"
                    ),
                    "scaffolding": contract.get("scaffolding"),
                    "duration_minutes": contract.get(
                        "duration_minutes"
                    ),
                    "language_target": contract.get(
                        "language_target"
                    ),
                    "instructions": _activity_instructions(
                        contract,
                        sequence_item,
                    ),
                    "purpose": sequence_item.get("purpose"),
                    "student_production": student_production,
                    "evidence": activity_evidence,
                    "assessment_link": activity_evidence,
                }
            )

        lesson = {
            "level": generation_request["level"],
            "objective": generation_request["objective"],
            "duration_minutes": generation_request["duration_minutes"],
            "topic": generation_request.get("topic"),
            "activities": activities,
        }

        if generation_request.get("teacher_facing"):
            lesson["teacher_execution"] = _teacher_execution(
                generation_request
            )

        assessment = generation_request.get("assessment_decision")

        if assessment:
            lesson["assessment"] = {
                "evidence": assessment.get("evidence"),
                "success_criteria": list(
                    assessment.get("success_criteria", [])
                ),
            }

        return lesson

    return generate