"""Connect tool selection to the controlled lesson generation cycle."""

from __future__ import annotations

from typing import Any, Callable

from core.generation.revision import generate_with_revision
from core.orchestration.provider_task_eligibility import (
    validate_provider_task_eligibility,
)
from core.orchestration.tool_selector import ToolCandidate, select_tool


class GenerationOrchestrator:
    """Route a generation task to a capable tool and apply bounded revision."""

    def __init__(self, tools: list[ToolCandidate], generators: dict[str, Callable]):
        self._tools = tools
        self._generators = generators

    def run(
        self,
        generation_request: dict[str, Any],
        *,
        required_capabilities: set[str] | None = None,
        blocked_tools: set[str] | None = None,
        max_revisions: int = 2,
        free_first: bool = True,
        task_type: str = "LESSON_GENERATION",
    ) -> dict[str, Any]:
        capabilities = required_capabilities or {"lesson_generation"}
        tool = select_tool(
            self._tools,
            capabilities,
            blocked_tools=blocked_tools,
            free_first=free_first,
        )

        if tool is None:
            return {
                "status": "HUMAN_HANDOFF",
                "tool_id": None,
                "result": None,
                "errors": ["NO_SUITABLE_TOOL"],
            }

        generator = self._generators.get(tool.tool_id)
        if generator is None:
            return {
                "status": "HUMAN_HANDOFF",
                "tool_id": tool.tool_id,
                "result": None,
                "errors": ["GENERATOR_UNAVAILABLE"],
            }

        eligibility_errors = validate_provider_task_eligibility(
            tool,
            task_type,
            generator,
            required_capabilities=capabilities,
        )
        if eligibility_errors:
            return {
                "status": "HUMAN_HANDOFF",
                "tool_id": tool.tool_id,
                "result": None,
                "errors": eligibility_errors,
            }

        result = generate_with_revision(
            generator,
            generation_request,
            max_revisions=max_revisions,
        )
        return {
            "status": result["status"],
            "tool_id": tool.tool_id,
            "result": result,
            "errors": result.get("errors", []),
        }
