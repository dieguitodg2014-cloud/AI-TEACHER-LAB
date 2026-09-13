"""Capability-aware routing from approved resource needs to providers."""

from __future__ import annotations

from core.foundation.models import TaskPacket
from core.orchestration.capability_matrix import capabilities_for_resource
from core.orchestration.tool_selector import ToolCandidate, select_tool
from tools.registry.config_loader import resource_provider_priority


def select_resource_provider(
    task: TaskPacket | None,
    tools: list[ToolCandidate],
    *,
    free_first: bool = True,
    blocked_tools: set[str] | None = None,
    provider_priority: list[str] | tuple[str, ...] = (),
) -> ToolCandidate | None:
    """Select an eligible provider using hints, policy priority, then scoring.

    Provider priority is an execution policy only. It cannot override the
    capabilities required by the authoritative TaskPacket and never changes
    the pedagogical decision. When no explicit priority is supplied, the
    runtime tool policy provides the specialized-resource order.
    """
    if task is None:
        return None

    required = set(
        capabilities_for_resource(
            task.required_output,
            source_based=task.source_based,
            visual=task.visual,
        )
    )
    blocked = blocked_tools or set()
    eligible = [
        tool
        for tool in tools
        if tool.tool_id not in blocked and required.issubset(tool.capabilities)
    ]
    if not eligible:
        return None

    by_id = {tool.tool_id: tool for tool in eligible}
    for hint in (task.preferred_tool, task.fallback_tool):
        if hint and hint in by_id:
            return by_id[hint]

    priority = tuple(provider_priority) or resource_provider_priority(None)
    if not provider_priority:
        from pathlib import Path
        from tools.registry.config_loader import load_tool_registry_config, DEFAULT_TOOL_CONFIG

        _, policy = load_tool_registry_config(DEFAULT_TOOL_CONFIG)
        priority = resource_provider_priority(policy)

    for tool_id in priority:
        if tool_id in by_id:
            return by_id[tool_id]

    return select_tool(
        eligible,
        required,
        free_first=free_first,
        blocked_tools=blocked,
    )
