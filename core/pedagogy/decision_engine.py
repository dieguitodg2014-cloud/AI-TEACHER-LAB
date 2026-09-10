"""Pedagogical Decision Engine for the first executable vertical slice."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any
from uuid import uuid4

from core.foundation.models import ActivityPlan, Context, LevelDecision, LearningPlanDecision
from core.foundation.validation import validate_learning_plan

STAGES = ("presentation", "modeling", "guided_practice", "communicative_practice", "production", "assessment")


def decide_learning_plan(context: Context, level_decision: LevelDecision) -> LearningPlanDecision:
    """Create a minimal pedagogical plan from context and level boundaries."""
    if context.level != level_decision.level:
        raise ValueError("Context level and LevelDecision level must match")
    duration = context.duration_minutes
    if duration < 30:
        raise ValueError("A minimum of 30 minutes is required for the MVP plan")
    allocations = _allocate_minutes(duration)
    objective = context.objective
    sequence = [
        ActivityPlan(f"act-{uuid4().hex[:10]}", f"Establish language/content needed for: {objective}", "teacher_to_class", allocations["presentation"], "Identify or recognize the target language/content."),
        ActivityPlan(f"act-{uuid4().hex[:10]}", "Make successful task performance visible through a clear model.", "teacher_to_class", allocations["modeling"], "Notice and reproduce the model with support."),
        ActivityPlan(f"act-{uuid4().hex[:10]}", "Build controlled accuracy before freer communication.", "pairs", allocations["guided_practice"], "Use the target language in a supported exchange."),
        ActivityPlan(f"act-{uuid4().hex[:10]}", "Use the target language to exchange meaningful information.", "pairs_or_small_groups", allocations["communicative_practice"], "Complete a meaningful interaction task."),
        ActivityPlan(f"act-{uuid4().hex[:10]}", "Demonstrate more independent performance of the objective.", "individual_or_pairs", allocations["production"], "Produce language demonstrating the lesson objective."),
        ActivityPlan(f"act-{uuid4().hex[:10]}", "Collect direct evidence of objective attainment.", "individual", allocations["assessment"], "Provide an observable performance or response.", objective),
    ]
    decision = LearningPlanDecision(
        plan_id=f"plan-{uuid4().hex[:12]}", objective=objective, sequence=sequence,
        total_minutes=sum(activity.minutes for activity in sequence),
        evidence_of_learning="Observable student performance demonstrating the stated objective.", resource_need="",
    )
    errors = validate_learning_plan(decision, duration)
    if errors:
        raise ValueError("Invalid learning plan: " + "; ".join(errors))
    return decision


def _allocate_minutes(duration: int) -> dict[str, int]:
    weights = {"presentation": 0.12, "modeling": 0.10, "guided_practice": 0.20, "communicative_practice": 0.25, "production": 0.23, "assessment": 0.10}
    values = {stage: max(2, int(duration * weight)) for stage, weight in weights.items()}
    values["production"] += duration - sum(values.values())
    return values


def learning_plan_to_dict(decision: LearningPlanDecision) -> dict[str, Any]:
    return asdict(decision)
