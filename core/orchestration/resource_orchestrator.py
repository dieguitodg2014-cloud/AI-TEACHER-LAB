"""Capability-based orchestration for optional instructional resources."""

from __future__ import annotations

from typing import Any, Callable

from core.foundation.models import TaskPacket
from core.orchestration.provider_capability_contract import (
    provider_supports_capabilities,
    validate_provider_capabilities,
)
from core.orchestration.provider_task_eligibility import validate_provider_task_eligibility
from core.orchestration.resource_provider import FunctionResourceProvider, ResourceProvider
from core.orchestration.resource_tool_router import select_resource_provider
from core.orchestration.tool_selector import ToolCandidate
from core.resources.acceptance_gate import ResourceAcceptanceResult, ResourceAcceptanceGate
from core.resources.output_validator import ResourceValidationResult, validate_resource_output

RESOURCE_CAPABILITY = "resource_generation"


def select_resource_tool(
    task: TaskPacket | None,
    tools: list[ToolCandidate],
    *,
    free_first: bool = True,
    blocked_tools: set[str] | None = None,
) -> ToolCandidate | None:
    """Select a resource tool from the capabilities frozen in the TaskPacket."""
    if task is None:
        return None
    eligible = [tool for tool in tools if blocked_tools is None or tool.tool_id not in blocked_tools]
    return select_resource_provider(task, eligible, free_first=free_first)


def resource_tool_plan(
    task: TaskPacket | None,
    tools: list[ToolCandidate],
    *,
    free_first: bool = True,
    blocked_tools: set[str] | None = None,
) -> dict[str, Any]:
    """Return an execution plan without executing the provider."""
    tool = select_resource_tool(task, tools, free_first=free_first, blocked_tools=blocked_tools)
    if task is None:
        return {"status": "NOT_REQUIRED", "tool_id": None, "task_id": None}
    if tool is None:
        return {"status": "HUMAN_HANDOFF", "tool_id": None, "task_id": task.task_id, "reason": "NO_ELIGIBLE_RESOURCE_TOOL"}
    return {"status": "READY", "tool_id": tool.tool_id, "task_id": task.task_id, "capability": RESOURCE_CAPABILITY}


def execute_resource_provider(task: TaskPacket, tool: ToolCandidate, provider: ResourceProvider) -> dict[str, Any]:
    """Execute an already-selected ResourceProvider against an approved task."""
    capability_errors = validate_provider_capabilities(tool.capabilities)
    if capability_errors:
        return {"status": "HUMAN_HANDOFF", "tool_id": tool.tool_id, "result": None, "errors": capability_errors}
    if not provider_supports_capabilities(tool.capabilities, {RESOURCE_CAPABILITY}):
        return {"status": "HUMAN_HANDOFF", "tool_id": tool.tool_id, "result": None, "errors": [f"PROVIDER_NOT_ELIGIBLE_FOR_TASK:{tool.tool_id}:RESOURCE_PRODUCTION"]}
    if not isinstance(provider, ResourceProvider):
        return {"status": "HUMAN_HANDOFF", "tool_id": tool.tool_id, "result": None, "errors": ["RESOURCE_PROVIDER_CONTRACT_INVALID"]}
    if not provider.can_produce(task):
        return {"status": "HUMAN_HANDOFF", "tool_id": tool.tool_id, "result": None, "errors": ["RESOURCE_PROVIDER_CANNOT_PRODUCE"]}
    try:
        produced_resource = provider.produce(task)
    except Exception as exc:  # pragma: no cover - provider failures are integration boundaries
        error_code = str(exc) if isinstance(exc, TypeError) else f"RESOURCE_PROVIDER_ERROR:{exc}"
        return {"status": "HUMAN_HANDOFF", "tool_id": tool.tool_id, "result": None, "errors": [error_code]}
    return {"status": "PRODUCED", "tool_id": tool.tool_id, "result": produced_resource, "errors": []}


def validate_and_accept_resource(
    task: TaskPacket,
    produced_resource: dict[str, Any] | None,
    *,
    revision_count: int = 0,
    acceptance_gate: ResourceAcceptanceGate | None = None,
) -> dict[str, Any]:
    """Run produced output through QC and the final acceptance boundary."""
    validation: ResourceValidationResult = validate_resource_output(task, produced_resource or {}, revision_count=revision_count)
    gate = acceptance_gate or ResourceAcceptanceGate()
    acceptance: ResourceAcceptanceResult = gate.evaluate(task, validation)

    status_by_decision = {
        "ACCEPT": "ACCEPTED",
        "REVISION_REQUIRED": "REVISION_REQUIRED",
        "REJECT_AND_REDESIGN": "REJECT_AND_REDESIGN",
        "HUMAN_HANDOFF": "HUMAN_HANDOFF",
    }
    return {
        "status": status_by_decision[acceptance.decision],
        "resource": produced_resource if acceptance.decision == "ACCEPT" else None,
        "validation": validation,
        "acceptance": acceptance,
    }


def execute_resource_production_pipeline(
    task: TaskPacket,
    tool: ToolCandidate,
    provider: ResourceProvider,
    *,
    revision_count: int = 0,
    acceptance_gate: ResourceAcceptanceGate | None = None,
) -> dict[str, Any]:
    """Produce, QC, and accept a resource without allowing provider bypass."""
    production = execute_resource_provider(task, tool, provider)
    if production["status"] != "PRODUCED":
        return production
    acceptance_result = validate_and_accept_resource(
        task,
        production["result"],
        revision_count=revision_count,
        acceptance_gate=acceptance_gate,
    )
    return {
        **production,
        "status": acceptance_result["status"],
        "result": acceptance_result["resource"],
        "validation": acceptance_result["validation"],
        "acceptance": acceptance_result["acceptance"],
    }


def execute_resource_generation(
    task: TaskPacket,
    tool: ToolCandidate,
    generators: dict[str, Callable[..., Any]],
) -> dict[str, Any]:
    """Execute an eligible resource provider against the approved TaskPacket."""
    generator = generators.get(tool.tool_id)
    eligibility_errors = validate_provider_task_eligibility(tool, "RESOURCE_PRODUCTION", generator, required_capabilities={RESOURCE_CAPABILITY})
    if eligibility_errors:
        return {"status": "HUMAN_HANDOFF", "tool_id": tool.tool_id, "result": None, "errors": eligibility_errors}
    provider = FunctionResourceProvider(generator)
    return execute_resource_provider(task, tool, provider)
