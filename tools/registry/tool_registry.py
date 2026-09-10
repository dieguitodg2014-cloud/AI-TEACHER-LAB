"""Minimal runtime tool registry for the MVP."""

from __future__ import annotations

from core.orchestration.tool_selector import ToolCandidate


class ToolRegistry:
    """Own the currently available tool candidates for orchestration."""

    def __init__(self, tools: list[ToolCandidate] | None = None):
        self._tools = list(tools or [])

    def register(self, tool: ToolCandidate) -> None:
        if any(existing.tool_id == tool.tool_id for existing in self._tools):
            raise ValueError(f"TOOL_ALREADY_REGISTERED:{tool.tool_id}")
        self._tools.append(tool)

    def list_available(self) -> list[ToolCandidate]:
        return list(self._tools)

    def get(self, tool_id: str) -> ToolCandidate | None:
        return next((tool for tool in self._tools if tool.tool_id == tool_id), None)
