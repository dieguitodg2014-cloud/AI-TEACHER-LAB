"""Pedagogical Decision Engine for the first executable vertical slice."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any
from uuid import uuid4

from core.foundation.models import (
    ActivityPlan,
    Context,
    LevelDecision,
    LearningPlanDecision,
    ResourceDecision,
)
from core.foundation.validation import validate_learning_plan


STAGES = (
    "presentation",
    "modeling",
    "guided_practice",
    "communicative_practice",
    "production",
    "assessment",
)

RESOURCE_ACTIONS = {"CREATE", "REUSE", "ADAPT", "OMIT", "NO_RESOURCE_REQUIRED"}


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
        plan_id=f"plan-{uuid4().hex[:12]}",
        objective=objective,
        sequence=sequence,
        total_minutes=sum(activity.minutes for activity in sequence),
        evidence_of_learning="Observable student performance demonstrating the stated objective.",
        resource_need="",
    )
    errors = validate_learning_plan(decision, duration)
    if errors:
        raise ValueError("Invalid learning plan: " + "; ".join(errors))
    return decision


def decide_resource_need(context: Context, learning_plan: LearningPlanDecision) -> ResourceDecision:
    """Make a conservative MVP resource decision before specialized production.

    The MVP never invents a resource requirement. Explicit teacher/course signals can
    request a resource, identify an existing resource, or state that no resource is
    needed. In AUTO mode, the default is NO_RESOURCE_REQUIRED.
    """
    preferences = context.teacher_preferences or {}
    mode = str(preferences.get("resource_requirement", "AUTO")).upper()
    if mode not in {"AUTO", "REQUIRED", "NOT_REQUIRED"}:
        raise ValueError("resource_requirement must be AUTO, REQUIRED, or NOT_REQUIRED")

    purpose = context.objective
    resource_type = str(preferences.get("resource_type", ""))
    available = str(preferences.get("available_resource", "")).strip()

    if mode == "NOT_REQUIRED":
        return ResourceDecision(
            decision_id=f"resource-{uuid4().hex[:12]}",
            action="NO_RESOURCE_REQUIRED",
            purpose=purpose,
            reason="Teacher or course context explicitly indicates that no dedicated resource is needed.",
            required=False,
        )

    if mode == "REQUIRED":
        action = "REUSE" if available else "CREATE"
        reason = (
            "An existing resource is explicitly available and should be reused."
            if available
            else "Teacher or course context explicitly establishes a pedagogical resource requirement."
        )
        return ResourceDecision(
            decision_id=f"resource-{uuid4().hex[:12]}",
            action=action,
            purpose=purpose,
            resource_type=resource_type or available,
            reason=reason,
            required=True,
        )

    # AUTO is intentionally conservative: do not create a resource merely because
    # a tool is available. A later evidence/adaptation layer can provide stronger
    # signals without changing this contract.
    return ResourceDecision(
        decision_id=f"resource-{uuid4().hex[:12]}",
        action="NO_RESOURCE_REQUIRED",
        purpose=purpose,
        resource_type=resource_type,
        reason="The MVP learning plan can pursue the objective through classroom interaction without a dedicated generated resource.",
        required=False,
    )


def apply_resource_decision(
    learning_plan: LearningPlanDecision,
    resource_decision: ResourceDecision,
) -> LearningPlanDecision:
    """Attach the explicit resource action to the learning-plan contract."""
    if resource_decision.action not in RESOURCE_ACTIONS:
        raise ValueError(f"Unsupported resource action: {resource_decision.action}")
    return LearningPlanDecision(
        plan_id=learning_plan.plan_id,
        objective=learning_plan.objective,
        sequence=learning_plan.sequence,
        total_minutes=learning_plan.total_minutes,
        evidence_of_learning=learning_plan.evidence_of_learning,
        resource_need=resource_decision.action,
    )


def _allocate_minutes(duration: int) -> dict[str, int]:
    weights = {"presentation": 0.12, "modeling": 0.10, "guided_practice": 0.20, "communicative_practice": 0.25, "production": 0.23, "assessment": 0.10}
    values = {stage: max(2, int(duration * weight)) for stage, weight in weights.items()}
    values["production"] += duration - sum(values.values())
    return values


def learning_plan_to_dict(decision: LearningPlanDecision) -> dict[str, Any]:
    return asdict(decision)
