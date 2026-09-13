"""Minimal pedagogical resource decision engine for the MVP vertical slice."""

from __future__ import annotations

from dataclasses import replace
from uuid import uuid4

from core.foundation.models import Context, LearningPlanDecision, ResourceDecision


def _execution_hint(constraints: list[str], prefix: str) -> str:
    """Read an optional execution hint without making it a hard provider choice."""
    return next(
        (
            item.split(":", 1)[1].strip()
            for item in constraints
            if item.upper().startswith(prefix)
        ),
        "",
    )


def _resource_hints(constraints: list[str]) -> tuple[str, str]:
    return (
        _execution_hint(constraints, "PREFERRED_RESOURCE_TOOL:"),
        _execution_hint(constraints, "FALLBACK_RESOURCE_TOOL:"),
    )


def decide_resource(
    context: Context,
    learning_plan: LearningPlanDecision,
) -> ResourceDecision:
    """Decide whether a specialized resource materially supports the objective.

    The MVP defaults to no specialized resource. A small set of transparent
    signals can justify production when the learning objective or topic itself
    requires a modality that normal lesson text cannot supply. Explicit
    resource constraints are honored as teacher/request-level instructions.

    Provider hints are carried as optional execution preferences. They never
    change the pedagogical action, output type, or capability requirements.
    """
    constraints = [item.strip() for item in context.constraints]
    preferred_tool, fallback_tool = _resource_hints(constraints)
    searchable_text = " ".join(
        part.lower()
        for part in (context.objective, context.topic)
        if part
    )

    explicit = next(
        (
            item.split(":", 1)[1].strip()
            for item in constraints
            if item.upper().startswith("RESOURCE_REQUIRED:")
        ),
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
            preferred_tool=preferred_tool,
            fallback_tool=fallback_tool,
        )

    if any(term in searchable_text for term in ("listening", "listen to", "audio")):
        return ResourceDecision(
            decision_id=f"resource-{uuid4().hex[:12]}",
            action="CREATE",
            purpose="Provide auditory input required by the learning objective.",
            resource_type="audio",
            reason="The objective or topic requires listening or auditory input that cannot be supplied by lesson text alone.",
            required=True,
            preferred_tool=preferred_tool,
            fallback_tool=fallback_tool,
        )

    if any(term in searchable_text for term in ("watch", "video", "visual demonstration")):
        return ResourceDecision(
            decision_id=f"resource-{uuid4().hex[:12]}",
            action="CREATE",
            purpose="Provide audiovisual or visual input required by the learning objective.",
            resource_type="video_or_visual",
            reason="The objective or topic explicitly requires audiovisual or visual input.",
            required=True,
            preferred_tool=preferred_tool,
            fallback_tool=fallback_tool,
        )

    return ResourceDecision(
        decision_id=f"resource-{uuid4().hex[:12]}",
        action="NO_RESOURCE_REQUIRED",
        purpose="Deliver the learning objective using the lesson plan and teacher-led interaction.",
        reason="No specialized resource is currently justified by the learning objective or topic.",
        required=False,
        preferred_tool=preferred_tool,
        fallback_tool=fallback_tool,
    )


def apply_resource_decision(
    learning_plan: LearningPlanDecision,
    resource_decision: ResourceDecision,
) -> LearningPlanDecision:
    """Copy the explicit resource action into the learning-plan contract."""
    return replace(learning_plan, resource_need=resource_decision.action)
