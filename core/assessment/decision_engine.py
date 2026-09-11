"""Assessment Decision Engine for the AI-TEACHER-LAB MVP."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any
from uuid import uuid4

from core.foundation.models import AssessmentDecision, LearningPlanDecision, LevelDecision


def decide_assessment(
    *,
    objective: str,
    level_decision: LevelDecision,
    learning_plan: LearningPlanDecision,
) -> AssessmentDecision:
    """Select the smallest valid assessment decision aligned with the lesson objective.

    This engine decides what evidence is needed; it does not generate the assessment
    content. The decision is deliberately provider-neutral so downstream generators
    can implement it without changing the pedagogical choice.
    """
    objective_text = objective.strip()
    if not objective_text:
        raise ValueError("Assessment objective cannot be empty")
    if not learning_plan.sequence:
        raise ValueError("Assessment requires a non-empty learning plan")
    if learning_plan.objective.strip() != objective_text:
        raise ValueError("Assessment objective must match the learning plan objective")

    text = objective_text.lower()
    communicative = any(
        marker in text
        for marker in (
            "discuss",
            "conversation",
            "communicate",
            "ask and answer",
            "interact",
            "speak",
            "describe",
            "explain",
            "role play",
        )
    )

    if communicative:
        assessment_type = "PERFORMANCE"
        target = "Demonstrate the target communicative objective in a meaningful interaction."
        evidence = learning_plan.evidence_of_learning
        if not evidence or not evidence.strip():
            evidence = "Observable learner performance demonstrating the lesson objective."
        criteria = _speaking_criteria(level_decision)
    else:
        assessment_type = "FORMATIVE"
        target = "Demonstrate the target objective through observable learner performance."
        evidence = learning_plan.evidence_of_learning
        if not evidence or not evidence.strip():
            evidence = "Observable learner response showing achievement of the lesson objective."
        criteria = [
            "The learner demonstrates the stated objective.",
            "The evidence is appropriate to the target level.",
            "The evidence comes from language or performance that was taught or practiced.",
        ]

    return AssessmentDecision(
        assessment_id=f"assessment-{uuid4().hex[:12]}",
        type=assessment_type,
        target=target,
        evidence=evidence,
        success_criteria=criteria,
    )


def _speaking_criteria(level_decision: LevelDecision) -> list[str]:
    """Return observable criteria calibrated to the established level boundaries."""
    criteria = [
        "The learner completes the communicative task and addresses the stated objective.",
        "The learner is comprehensible enough to communicate the intended meaning.",
    ]

    if level_decision.level in ("A0", "A1"):
        criteria.extend(
            [
                "The learner uses the taught language with the expected level of support.",
                "Pauses and emerging fluency are acceptable when they do not prevent task completion.",
            ]
        )
    elif level_decision.level == "A2":
        criteria.append("The learner produces short connected language with limited support.")
    elif level_decision.level == "B1":
        criteria.append("The learner sustains functional communication and develops the required ideas with relevant detail.")
    else:
        criteria.extend(
            [
                "The learner develops ideas with appropriate detail and maintains interaction independently.",
                "The learner demonstrates appropriate language choices for the communicative context.",
            ]
        )

    return criteria


def assessment_decision_to_dict(decision: AssessmentDecision) -> dict[str, Any]:
    """Return a serializable assessment decision for downstream orchestration."""
    return asdict(decision)
