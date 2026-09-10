"""Minimal pedagogical resource decision engine for the MVP vertical slice."""

from __future__ import annotations

from dataclasses import replace
from uuid import uuid4

from core.foundation.models import Context, LearningPlanDecision, ResourceDecision


def decide_resource(
    context: Context,
    learning_plan: LearningPlanDecision,
) -> ResourceDecision:
    """Decide whether a specialized resource materially supports the objective.

    The MVP defaults to no specialized resource. A small set of transparent
    signals can justify production when the learning objective itself requires
    a modality that a normal lesson text cannot supply. Explicit resource
    constraints are honored as teacher/request-level instructions.
    """
    constraints = [item.strip() for item in context.constraints]
    lowered_objective = context.objective.lower()

    explicit = next(
        (item.split(":", 1)[1].strip() for item in constraints
         if item.upper().startswith("RESOURCE_REQUIRED:")),
        None,
    )
    if explicit:
        resource_type = explicit or "classroom resource"
        return ResourceDecision(
            decision_id=f"resource-{uuid4().hex[:12]}",
            action="CREATE",
            purpose=f"Provide the requested support for: {context.objective}",
            resource_type=resource_type,
            reason="The request explicitly requires a resource.",
            required=True,
        )

    if any(term in lowered_objective for term in ("listening", "listen to", "audio")):
        return ResourceDecision(
            decision_id=f"resource-{uuid4().hex[:12]}",
            action="CREATE",
            purpose="Provide auditory input required by the learning objective.",
            resource_type="audio",
            reason="The objective requires listening or auditory input that cannot be supplied by lesson text alone.",
            required=True,
        )

    if any(term in lowered_objective for term in ("watch", "video", "visual demonstration")):
        return ResourceDecision(
            decision_id=f"resource-{uuid4().hex[:12]}",
            action="CREATE",
            purpose="Provide audiovisual or visual input required by the learning objective.",
            resource_type="video_or_visual",
            reason="The objective explicitly requires audiovisual or visual input.",
            required=True,
        )

    return ResourceDecision(
        decision_id=f"resource-{uuid4().hex[:12]}",
        action="NO_RESOURCE_REQUIRED",
        purpose="Deliver the learning objective using the lesson plan and teacher-led interaction.",
        reason="No specialized resource is currently justified by the learning objective.",
        required=False,
    )


def apply_resource_decision(
    learning_plan: LearningPlanDecision,
    resource_decision: ResourceDecision,
) -> LearningPlanDecision:
    """Copy the explicit resource action into the learning-plan contract."""
    return replace(learning_plan, resource_need=resource_decision.action)
