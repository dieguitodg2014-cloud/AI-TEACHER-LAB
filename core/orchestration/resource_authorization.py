"""Authorization boundary between pedagogical decisions and resource production.

Resource providers receive an already-authorized TaskPacket. They do not decide
whether a resource is needed, what it is for, or which pedagogical constraints
apply. This module makes that boundary explicit and deterministic.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.foundation.models import Context, LearningPlanDecision, ResourceDecision, TaskPacket
from core.orchestration.task_packets import build_resource_task_packet


PRODUCTION_ACTIONS = frozenset({"CREATE", "REUSE", "ADAPT"})


@dataclass(frozen=True)
class ResourceProductionAuthorization:
    """Immutable authorization handed from pedagogy to production."""

    task: TaskPacket
    learning_plan_id: str
    resource_decision_id: str
    action: str
    purpose: str
    resource_type: str


@dataclass(frozen=True)
class ResourceAuthorizationResult:
    """Result of attempting to authorize a resource production task."""

    authorized: bool
    authorization: ResourceProductionAuthorization | None
    errors: tuple[str, ...] = ()


def authorize_resource_production(
    context: Context,
    learning_plan: LearningPlanDecision,
    resource_decision: ResourceDecision,
) -> ResourceAuthorizationResult:
    """Create a production authorization only from approved pedagogical inputs."""
    if resource_decision.action not in PRODUCTION_ACTIONS:
        return ResourceAuthorizationResult(
            authorized=False,
            authorization=None,
            errors=(
                f"RESOURCE_PRODUCTION_NOT_AUTHORIZED_FOR_ACTION:{resource_decision.action}",
            ),
        )

    if context.objective != learning_plan.objective:
        return ResourceAuthorizationResult(
            authorized=False,
            authorization=None,
            errors=("PEDAGOGICAL_OBJECTIVE_MISMATCH",),
        )

    try:
        task = build_resource_task_packet(context, learning_plan, resource_decision)
    except ValueError as exc:
        return ResourceAuthorizationResult(
            authorized=False,
            authorization=None,
            errors=(str(exc),),
        )

    if task is None:
        return ResourceAuthorizationResult(
            authorized=False,
            authorization=None,
            errors=("RESOURCE_TASK_PACKET_NOT_CREATED",),
        )

    authorization = ResourceProductionAuthorization(
        task=task,
        learning_plan_id=learning_plan.plan_id,
        resource_decision_id=resource_decision.decision_id,
        action=resource_decision.action,
        purpose=resource_decision.purpose,
        resource_type=resource_decision.resource_type or task.required_output,
    )
    return ResourceAuthorizationResult(authorized=True, authorization=authorization)
