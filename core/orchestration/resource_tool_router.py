"""Capability-aware routing from approved resource needs to providers."""

from __future__ import annotations

from core.foundation.models import TaskPacket
from core.orchestration.capability_matrix import capabilities_for_resource
from core.orchestration.tool_selector import ToolCandidate, select_tool


def select_resource_provider(
    task: TaskPacket | None,
    tools: list[ToolCandidate],
    *,
    source_based: bool = False,
    visual: bool = False,
    free_first: bool = True,
) -> ToolCandidate | None:
    """Select a provider using capabilities derived from the approved task.

    The task remains the source of pedagogical intent. This function only
    translates its approved resource requirements into provider capabilities.
    """
    if task is None:
        return None
    required = capabilities_for_resource(
        task.required_output,
        source_based=source_based,
        visual=visual,
    )
    return select_tool(tools, set(required), free_first=free_first)
