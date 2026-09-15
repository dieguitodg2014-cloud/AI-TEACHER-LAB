"""Task packet creation for resource production orchestration."""

from __future__ import annotations

from uuid import uuid4

from core.foundation.models import Context, LearningPlanDecision, ResourceDecision, TaskPacket
from core.resources.approved_content import ApprovedResourceContent, approved_input_materials


def build_resource_task_packet(
    context: Context,
    learning_plan: LearningPlanDecision,
    resource_decision: ResourceDecision,
    approved_content: ApprovedResourceContent | None = None,
) -> TaskPacket | None:
    """Create a production packet only when the pedagogical decision requires it.

    ``approved_content`` is optional for backward compatibility, but when
    supplied it is the only source used to populate downstream input materials.
    Providers are never asked to invent missing instructional content.
    """
    if resource_decision.action not in {"CREATE", "REUSE", "ADAPT"}:
        return None

    required_output = resource_decision.resource_type or "instructional resource"
    return TaskPacket(
        task_id=f"task-{uuid4().hex[:12]}",
        task_type="RESOURCE_PRODUCTION",
        objective=context.objective,
        level=context.level,
        required_output=required_output,
        constraints=tuple(context.constraints),
        quality_criteria=(
            "Directly support the stated learning objective.",
            "Match the approved learner level and audience.",
            "Be usable within the planned lesson time.",
            "Do not introduce unnecessary content or complexity.",
        ),
        lesson_id=learning_plan.plan_id,
        audience=context.audience,
        input_materials=approved_input_materials(approved_content),
        status="PENDING",
    )
