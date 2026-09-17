"""Capability-based orchestration for optional instructional resources."""

from __future__ import annotations

from typing import Any, Callable

from core.foundation.models import TaskPacket, ToolDecision
from core.orchestration.provider_capability_contract import (
    provider_supports_capabilities,
    validate_provider_capabilities,
)
from core.orchestration.provider_task_eligibility import validate_provider_task_eligibility
from core.orchestration.resource_output_compatibility import provider_supports_resource_output
from core.orchestration.resource_provider import FunctionResourceProvider, ResourceProvider
from core.orchestration.tool_selector import ToolCandidate, select_tool, select_tool_decision


RESOURCE_CAPABILITY = "resource_generation"


def select_resource_tool_decision(
    task: TaskPacket | None,
    tools: list[ToolCandidate],
    *,
    free_first: bool = True,
    blocked_tools: set[str] | None = None,
) -> ToolDecision | None:
    """Create the authoritative decision for a resource task."""
    if task is None:
        return None
    compatible_tools = [
        tool
        for tool in tools
        if provider_supports_capabilities(tool.capabilities, {RESOURCE_CAPABILITY})
        and provider_supports_resource_output(tool.capabilities, task.required_output)
    ]
    return select_tool_decision(
        compatible_tools,
        {RESOURCE_CAPABILITY},
        free_first=free_first,
        blocked_tools=blocked_tools,
        task_type="RESOURCE_PRODUCTION",
    )


def select_resource_tool(
    task: TaskPacket | None,
    tools: list[ToolCandidate],
    *,
    free_first: bool = True,
    blocked_tools: set[str] | None = None,
) -> ToolCandidate | None:
    """Backward-compatible view of the authoritative resource decision."""
    decision = select_resource_tool_decision(
        task,
        tools,
        free_first=free_first,
        blocked_tools=blocked_tools,
    )
    if decision is None:
        return None
    return next((tool for tool in tools if tool.tool_id == decision.selected_tool), None)


def resource_tool_plan(
    task: TaskPacket | None,
    tools: list[ToolCandidate],
    *,
    free_first: bool = True,
) -> dict[str, Any]:
    """Return a small execution plan for a resource task."""
    decision = select_resource_tool_decision(task, tools, free_first=free_first)
    if task is None:
        return {"status": "NOT_REQUIRED", "tool_id": None, "task_id": None}
    if decision is None:
        return {
            "status": "HUMAN_HANDOFF",
            "tool_id": None,
            "task_id": task.task_id,
            "reason": "NO_SUITABLE_RESOURCE_TOOL",
        }
    return {
        "status": "READY",
        "tool_id": decision.selected_tool,
        "task_id": task.task_id,
        "capability": RESOURCE_CAPABILITY,
    }


def execute_resource_provider(
    task: TaskPacket,
    decision: ToolDecision,
    tool: ToolCandidate,
    provider: ResourceProvider,
) -> dict[str, Any]:
    """Execute exactly the provider named by the authoritative ToolDecision."""
    if tool.tool_id != decision.selected_tool:
        return {
            "status": "HUMAN_HANDOFF" if decision.human_handoff_allowed else "FAILED",
            "tool_id": decision.selected_tool,
            "result": None,
            "errors": ["SELECTED_TOOL_MISMATCH"],
        }
    capability_errors = validate_provider_capabilities(tool.capabilities)
    if capability_errors:
        return {
            "status": "HUMAN_HANDOFF" if decision.human_handoff_allowed else "FAILED",
            "tool_id": decision.selected_tool,
            "result": None,
            "errors": capability_errors,
        }
    if not provider_supports_capabilities(tool.capabilities, {RESOURCE_CAPABILITY}):
        return {
            "status": "HUMAN_HANDOFF" if decision.human_handoff_allowed else "FAILED",
            "tool_id": decision.selected_tool,
            "result": None,
            "errors": [f"PROVIDER_NOT_ELIGIBLE_FOR_TASK:{tool.tool_id}:RESOURCE_PRODUCTION"],
        }
    if not provider_supports_resource_output(tool.capabilities, task.required_output):
        return {
            "status": "HUMAN_HANDOFF" if decision.human_handoff_allowed else "FAILED",
            "tool_id": decision.selected_tool,
            "result": None,
            "errors": [f"PROVIDER_NOT_ELIGIBLE_FOR_OUTPUT:{tool.tool_id}:{task.required_output}"],
        }
    if not isinstance(provider, ResourceProvider):
        return {
            "status": "HUMAN_HANDOFF" if decision.human_handoff_allowed else "FAILED",
            "tool_id": decision.selected_tool,
            "result": None,
            "errors": ["RESOURCE_PROVIDER_CONTRACT_INVALID"],
        }
    if not provider.can_produce(task):
        return {
            "status": "HUMAN_HANDOFF" if decision.human_handoff_allowed else "FAILED",
            "tool_id": decision.selected_tool,
            "result": None,
            "errors": ["RESOURCE_PROVIDER_CANNOT_PRODUCE"],
        }
    try:
        produced_resource = provider.produce(task)
    except Exception as exc:  # pragma: no cover
        error_code = str(exc) if isinstance(exc, TypeError) else f"RESOURCE_PROVIDER_ERROR:{exc}"
        return {
            "status": "HUMAN_HANDOFF" if decision.human_handoff_allowed else "FAILED",
            "tool_id": decision.selected_tool,
            "result": None,
            "errors": [error_code],
        }
    return {
        "status": "PRODUCED",
        "tool_id": decision.selected_tool,
        "result": produced_resource,
        "errors": [],
    }


def execute_resource_generation(
    task: TaskPacket,
    decision: ToolDecision,
    tools: list[ToolCandidate] | ToolCandidate,
    generators: dict[str, Callable[..., Any]],
) -> dict[str, Any]:
    """Execute the generator named by ToolDecision without silent reselection."""
    candidates = tools if isinstance(tools, list) else [tools]
    tool = next((candidate for candidate in candidates if candidate.tool_id == decision.selected_tool), None)
    generator = generators.get(decision.selected_tool)
    if tool is None or generator is None:
        return {
            "status": "HUMAN_HANDOFF" if decision.human_handoff_allowed else "FAILED",
            "tool_id": decision.selected_tool,
            "result": None,
            "errors": ["SELECTED_TOOL_UNAVAILABLE" if tool is None else "GENERATOR_UNAVAILABLE"],
        }
    eligibility_errors = validate_provider_task_eligibility(
        tool,
        "RESOURCE_PRODUCTION",
        generator,
        required_capabilities={RESOURCE_CAPABILITY},
    )
    if eligibility_errors:
        return {
            "status": "HUMAN_HANDOFF" if decision.human_handoff_allowed else "FAILED",
            "tool_id": decision.selected_tool,
            "result": None,
            "errors": eligibility_errors,
        }
    provider = FunctionResourceProvider(generator)
    return execute_resource_provider(task, decision, tool, provider)
