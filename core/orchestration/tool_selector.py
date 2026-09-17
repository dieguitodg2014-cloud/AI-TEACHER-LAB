"""Capability-based tool selection for the lesson generation workflow."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

from core.foundation.models import ToolDecision


@dataclass(frozen=True)
class ToolCandidate:
    tool_id: str
    capabilities: frozenset[str]
    quality: float = 0.0
    reliability: float = 0.0
    accessibility: float = 0.0
    speed: float = 0.0
    cost: float = 0.0

    def __post_init__(self) -> None:
        object.__setattr__(self, "capabilities", frozenset(self.capabilities))


def _eligible_tools(
    candidates: list[ToolCandidate],
    required_capabilities: set[str],
    blocked_tools: set[str] | None = None,
) -> list[ToolCandidate]:
    """Return eligible candidates without making a new downstream decision."""
    blocked = blocked_tools or set()
    return [
        tool
        for tool in candidates
        if tool.tool_id not in blocked
        and required_capabilities.issubset(tool.capabilities)
    ]


def _score(tool: ToolCandidate, *, free_first: bool) -> tuple[float, float, float]:
    """Score an eligible candidate using the existing selection policy."""
    base = (
        tool.quality
        + tool.reliability
        + tool.accessibility
        + tool.speed
        - tool.cost
    )
    free_priority = -tool.cost if free_first else 0.0
    return (free_priority, base, tool.quality)


def select_tool_decision(
    candidates: list[ToolCandidate],
    required_capabilities: set[str],
    *,
    free_first: bool = True,
    blocked_tools: set[str] | None = None,
    task_type: str = "LESSON_GENERATION",
    fallback_policy: tuple[str, ...] = (),
    human_handoff_allowed: bool = True,
) -> ToolDecision | None:
    """Create the authoritative immutable decision for tool selection.

    The current orchestration contract deliberately defaults to no automatic
    fallback. A caller may declare an explicit fallback policy, but downstream
    execution must not invent one or silently select another tool.
    """
    eligible = _eligible_tools(candidates, required_capabilities, blocked_tools)
    if not eligible:
        return None

    selected = max(eligible, key=lambda tool: _score(tool, free_first=free_first))
    return ToolDecision(
        decision_id=f"tool-{uuid4().hex[:12]}",
        task_type=task_type,
        selected_tool=selected.tool_id,
        fallback_policy=fallback_policy,
        human_handoff_allowed=human_handoff_allowed,
        reason="Selected by declared capability and existing tool-selection policy.",
    )


def select_tool(
    candidates: list[ToolCandidate],
    required_capabilities: set[str],
    *,
    free_first: bool = True,
    blocked_tools: set[str] | None = None,
) -> ToolCandidate | None:
    """Backward-compatible view of the authoritative selection result."""
    decision = select_tool_decision(
        candidates,
        required_capabilities,
        free_first=free_first,
        blocked_tools=blocked_tools,
    )
    if decision is None:
        return None
    return next(
        (tool for tool in candidates if tool.tool_id == decision.selected_tool),
        None,
    )
