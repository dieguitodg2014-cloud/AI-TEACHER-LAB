"""Capability-based orchestration for optional instructional resources."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Callable

from core.foundation.models import TaskPacket
from core.orchestration.provider_task_eligibility import validate_provider_task_eligibility
from core.orchestration.tool_selector import ToolCandidate, select_tool


RESOURCE_CAPABILITY = "resource_generation"


def select_resource_tool(
    task: TaskPacket | None,
    tools: list[ToolCandidate],
    *,
    free_first: bool = True,
    blocked_tools: set[str] | None = None,
) -> ToolCandidate | None:
    """Select a tool for a resource task without naming a provider."""
    if task is None:
        return None
    return select_tool(
        tools,
        {RESOURCE_CAPABILITY},
        free_first=free_first,
        blocked_tools=blocked_tools,
    )


def resource_tool_plan(
    task: TaskPacket | None,
    tools: list[ToolCandidate],
    *,
    free_first: bool = True,
) -> dict[str, Any]:
    """Return a small execution plan for a resource task.

    This does not execute the provider. If no capable connector exists, the
    caller can hand the task to a human or external workflow such as NotebookLM.
    """
    tool = select_resource_tool(task, tools, free_first=free_first)
    if task is None:
        return {"status": "NOT_REQUIRED", "tool_id": None, "task_id": None}
    if tool is None:
        return {
            "status": "HUMAN_HANDOFF",
            "tool_id": None,
            "task_id": task.task_id,
            "reason": "NO_RESOURCE_GENERATION_TOOL",
        }
    return {
        "status": "READY",
        "tool_id": tool.tool_id,
        "task_id": task.task_id,
        "capability": RESOURCE_CAPABILITY,
    }


def execute_resource_generation(
    task: TaskPacket,
    tool: ToolCandidate,
    generators: dict[str, Callable[..., Any]],
) -> dict[str, Any]:
    """Execute an eligible resource provider against the approved TaskPacket.

    The provider receives the provider-neutral TaskPacket as a dictionary and
    returns the produced resource. Pedagogical decisions remain outside the
    provider; resource quality is validated by the resource QC boundary after
    execution.
    """
    generator = generators.get(tool.tool_id)
    eligibility_errors = validate_provider_task_eligibility(
        tool,
        "RESOURCE_PRODUCTION",
        generator,
        required_capabilities={RESOURCE_CAPABILITY},
    )
    if eligibility_errors:
        return {
            "status": "HUMAN_HANDOFF",
            "tool_id": tool.tool_id,
            "result": None,
            "errors": eligibility_errors,
        }

    try:
        produced_resource = generator(asdict(task))
    except Exception as exc:  # pragma: no cover - provider failures are integration boundaries
        return {
            "status": "HUMAN_HANDOFF",
            "tool_id": tool.tool_id,
            "result": None,
            "errors": [f"RESOURCE_GENERATOR_ERROR:{exc}"],
        }

    if not isinstance(produced_resource, dict):
        return {
            "status": "HUMAN_HANDOFF",
            "tool_id": tool.tool_id,
            "result": None,
            "errors": ["RESOURCE_OUTPUT_NOT_OBJECT"],
        }

    return {
        "status": "PRODUCED",
        "tool_id": tool.tool_id,
        "result": produced_resource,
        "errors": [],
    }
