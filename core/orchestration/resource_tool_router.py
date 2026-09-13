"""Capability-aware routing from approved resource needs to providers."""

from __future__ import annotations

from core.foundation.models import TaskPacket
from core.orchestration.capability_matrix import capabilities_for_resource
from core.orchestration.tool_selector import ToolCandidate, select_tool


def select_resource_provider(
    task: TaskPacket | None,
    tools: list[ToolCandidate],
    *,
    free_first: bool = True,
) -> ToolCandidate | None:
    """Select a provider from explicit capabilities frozen into the TaskPacket.

    The pedagogical/resource decision establishes the flags before this layer.
    The router only translates those approved requirements into capabilities.
    """
    if task is None:
        return None
    required = capabilities_for_resource(
        task.required_output,
        source_based=task.source_based,
        visual=task.visual,
    )
    return select_tool(tools, set(required), free_first=free_first)
