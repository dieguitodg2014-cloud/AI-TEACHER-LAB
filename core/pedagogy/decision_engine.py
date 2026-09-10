"""Pedagogical Decision Engine for the first executable vertical slice."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any
from uuid import uuid4

from core.foundation.models import ActivityPlan, Context, LevelDecision, LearningPlanDecision
from core.foundation.validation import validate_learning_plan


SEQUENCE = (
    "presentation",
    "modeling",
    "guided_practice",
    "communicative_practice",
    "production",
    "assessment",
)


def decide_learning_plan(
    context: Context,
    level_decision: LevelDecision,
) -> LearningPlanDecision:
    """Create a minimal pedagogical plan from context and level boundaries.

    This engine decides instructional architecture, not materials or tools.
    """
    if context.level != level_decision.level:
        raise ValueError("Context level and LevelDecision level must match")

    duration = context.duration_minutes
    if duration < 30:
        raise ValueError("A minimum of 30 minutes is required for the MVP plan")

    # Initial deterministic allocation. Later policy configuration can replace
    # these values without changing the contract or downstream consumers.
    allocations = _allocate_minutes(duration)
    objective = context.objective

    activities = [
        ActivityPlan(
            activity_id=f"act-{uuid4().hex[:10]}",
            stage="presentation",
            purpose=f"Establish the language/content needed for: {objective}",
            minutes=allocations["presentation"],
            interaction="teacher_to_class",
            student_output="Identify or recognize the target language/content.",
        ),
        ActivityPlan(
            activity_id=f"act-{uuid4().hex[:10]}",
            stage="modeling",
            purpose="Make successful task performance visible through a clear model.",
            minutes=allocations["modeling"],
            interaction="teacher_to_class",
            student_output="Notice and reproduce the model with support.",
        ),
        ActivityPlan(
            activity_id=f"act-{uuid4().hex[:10]}",
            stage="guided_practice",
            purpose="Build controlled accuracy before freer communication.",
            minutes=allocations["guided_practice"],
            interaction="pairs",
            student_output="Use the target language in a supported exchange.",
        ),
        ActivityPlan(
            activity_id=f"act-{uuid4().hex[:10]}",
            stage="communicative_practice",
            purpose="Use the target language to exchange meaningful information.",
            minutes=allocations["communicative_practice"],
            interaction="pairs_or_small_groups",
            student_output="Complete a meaningful information-gap or interaction task.",
        ),
        ActivityPlan(
            activity_id=f"act-{uuid4().hex[:10]}",
            stage="production",
            purpose="Demonstrate more independent performance of the objective.",
            minutes=allocations["production"],
            interaction="individual_or_pairs",
            student_output="Produce language that demonstrates the lesson objective.",
        ),
        ActivityPlan(
            activity_id=f"act-{uuid4().hex[:10]}",
            stage="assessment",
            purpose="Collect direct evidence of objective attainment.",
            minutes=allocations["assessment"],
            interaction="individual",
            student_output="Provide a brief observable performance or response.",
        ),
    ]

    decision = LearningPlanDecision(
        decision_id=f"plan-{uuid4().hex[:12]}",
        sequence=list(SEQUENCE),
        activities=activities,
        student_talk_priority=True,
        assessment_alignment_required=True,
        resource_generation_required=False,
        rationale=(
            f"Plan respects {level_decision.level} boundaries, prioritizes meaningful "
            "student production, and reserves time for evidence of learning."
        ),
    )

    errors = validate_learning_plan(decision, duration)
    if errors:
        raise ValueError("Invalid learning plan: " + "; ".join(errors))

    return decision


def _allocate_minutes(duration: int) -> dict[str, int]:
    """Allocate a realistic minimum sequence while preserving total duration."""
    weights = {
        "presentation": 0.12,
        "modeling": 0.10,
        "guided_practice": 0.20,
        "communicative_practice": 0.25,
        "production": 0.23,
        "assessment": 0.10,
    }
    values = {stage: max(2, int(duration * weight)) for stage, weight in weights.items()}
    difference = duration - sum(values.values())
    values["production"] += difference
    return values


def learning_plan_to_dict(decision: LearningPlanDecision) -> dict[str, Any]:
    return asdict(decision)
