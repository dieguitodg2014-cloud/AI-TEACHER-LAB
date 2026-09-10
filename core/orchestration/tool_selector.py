"""Capability-based tool selection for the lesson generation workflow."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ToolCandidate:
    tool_id: str
    capabilities: frozenset[str]
    quality: float = 0.0
    reliability: float = 0.0
    accessibility: float = 0.0
    speed: float = 0.0
    cost: float = 0.0


def select_tool(
    candidates: list[ToolCandidate],
    required_capabilities: set[str],
    *,
    free_first: bool = True,
    blocked_tools: set[str] | None = None,
) -> ToolCandidate | None:
    """Select the best available tool without hardcoding a provider."""
    blocked = blocked_tools or set()
    eligible = [
        tool
        for tool in candidates
        if tool.tool_id not in blocked
        and required_capabilities.issubset(tool.capabilities)
    ]
    if not eligible:
        return None

    def score(tool: ToolCandidate) -> tuple[float, float, float]:
        # Pedagogical fit is represented by capability matching; all eligible
        # tools satisfy the required capability contract.
        base = (
            tool.quality
            + tool.reliability
            + tool.accessibility
            + tool.speed
            - tool.cost
        )
        free_priority = -tool.cost if free_first else 0.0
        return (free_priority, base, tool.quality)

    return max(eligible, key=score)
