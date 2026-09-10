"""Task packet creation for resource production orchestration."""

from __future__ import annotations

from uuid import uuid4

from core.foundation.models import Context, LearningPlanDecision, ResourceDecision, TaskPacket


def build_resource_task_packet(
    context: Context,
    learning_plan: LearningPlanDecision,
    resource_decision: ResourceDecision,
) -> TaskPacket | None:
    """Create a production packet only when the pedagogical decision requires it."""
    if resource_decision.action not in {"CREATE", "REUSE", "ADAPT"}:
        return None

    required_output = resource_decision.resource_type or "instructional resource"
    return TaskPacket(
        task_id=f"task-{uuid4().hex[:12]}",
        task_type="RESOURCE_PRODUCTION",
        objective=context.objective,
        level=context.level,
        required_output=required_output,
        constraints=list(context.constraints),
        quality_criteria=[
            "Directly support the stated learning objective.",
            "Match the approved learner level and audience.",
            "Be usable within the planned lesson time.",
            "Do not introduce unnecessary content or complexity.",
        ],
        lesson_id=learning_plan.plan_id,
        audience=context.audience,
        status="PENDING",
    )
