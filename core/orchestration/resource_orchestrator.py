"""Capability-based orchestration for optional instructional resources."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable

from core.foundation.models import TaskPacket
from core.orchestration.capability_matrix import capabilities_for_resource
from core.orchestration.capability_validation_registry import CapabilityValidationRegistry
from core.orchestration.provider_capability_contract import (
    provider_supports_capabilities,
    validate_provider_capabilities,
)
from core.orchestration.provider_execution_policy import ProviderExecutionPolicy
from core.orchestration.provider_task_eligibility import validate_provider_task_eligibility
from core.orchestration.resource_provider import FunctionResourceProvider, ResourceProvider
from core.orchestration.resource_tool_router import select_resource_provider
from core.orchestration.tool_selector import ToolCandidate
from core.resources.acceptance_gate import ResourceAcceptanceResult, ResourceAcceptanceGate
from core.resources.output_validator import ResourceValidationResult, validate_resource_output
from core.resources.revision_engine import ResourceRevisionEngine, ResourceRevisionResult

RESOURCE_CAPABILITY = "resource_generation"


def select_resource_tool(
    task: TaskPacket | None,
    tools: list[ToolCandidate],
    *,
    free_first: bool = True,
    blocked_tools: set[str] | None = None,
    validation_registry: CapabilityValidationRegistry | None = None,
) -> ToolCandidate | None:
    """Select a resource tool from the capabilities frozen in the TaskPacket."""
    if task is None:
        return None
    eligible = [tool for tool in tools if blocked_tools is None or tool.tool_id not in blocked_tools]
    return select_resource_provider(
        task,
        eligible,
        free_first=free_first,
        validation_registry=validation_registry,
    )


def resource_tool_plan(
    task: TaskPacket | None,
    tools: list[ToolCandidate],
    *,
    free_first: bool = True,
    blocked_tools: set[str] | None = None,
    validation_registry: CapabilityValidationRegistry | None = None,
) -> dict[str, Any]:
    """Return an execution plan without executing the provider."""
    tool = select_resource_tool(
        task,
        tools,
        free_first=free_first,
        blocked_tools=blocked_tools,
        validation_registry=validation_registry,
    )
    if task is None:
        return {"status": "NOT_REQUIRED", "tool_id": None, "task_id": None}
    if tool is None:
        return {"status": "HUMAN_HANDOFF", "tool_id": None, "task_id": task.task_id, "reason": "NO_ELIGIBLE_RESOURCE_TOOL"}
    return {"status": "READY", "tool_id": tool.tool_id, "task_id": task.task_id, "capability": RESOURCE_CAPABILITY}


def execute_resource_provider(task: TaskPacket, tool: ToolCandidate, provider: ResourceProvider) -> dict[str, Any]:
    """Execute an already-selected ResourceProvider against an approved task.

    Providers receive defensive copies because TaskPacket contains mutable lists
    even though the dataclass itself is frozen. The authoritative task remains
    untouched and is the only task used by downstream QC and acceptance.
    """
    capability_errors = validate_provider_capabilities(tool.capabilities)
    if capability_errors:
        return {"status": "HUMAN_HANDOFF", "tool_id": tool.tool_id, "result": None, "errors": capability_errors}

    required_capabilities = set(
        capabilities_for_resource(
            task.required_output,
            source_based=task.source_based,
            visual=task.visual,
        )
    )
    if not provider_supports_capabilities(tool.capabilities, required_capabilities):
        return {
            "status": "HUMAN_HANDOFF",
            "tool_id": tool.tool_id,
            "result": None,
            "errors": [f"PROVIDER_NOT_ELIGIBLE_FOR_TASK:{tool.tool_id}:RESOURCE_PRODUCTION"],
        }
    if not isinstance(provider, ResourceProvider):
        return {"status": "HUMAN_HANDOFF", "tool_id": tool.tool_id, "result": None, "errors": ["RESOURCE_PROVIDER_CONTRACT_INVALID"]}
    provider_task = deepcopy(task)
    if not provider.can_produce(provider_task):
        return {"status": "HUMAN_HANDOFF", "tool_id": tool.tool_id, "result": None, "errors": ["RESOURCE_PROVIDER_CANNOT_PRODUCE"]}
    try:
        produced_resource = provider.produce(deepcopy(provider_task))
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


def process_produced_resource(
    task: TaskPacket,
    produced_resource: dict[str, Any],
    *,
    reviser: Callable[[TaskPacket, dict[str, Any], ResourceValidationResult], dict[str, Any]] | None = None,
    max_revisions: int = 1,
    acceptance_gate: ResourceAcceptanceGate | None = None,
) -> dict[str, Any]:
    """Run one already-produced resource through QC, bounded revision, and acceptance."""
    revision_engine = ResourceRevisionEngine(acceptance_gate=acceptance_gate)
    revision_result: ResourceRevisionResult = revision_engine.run(
        task,
        produced_resource,
        reviser=reviser,
        max_revisions=max_revisions,
    )

    errors = []
    if revision_result.acceptance is not None and not revision_result.accepted:
        errors = list(revision_result.acceptance.reasons)

    return {
        "status": revision_result.status,
        "result": revision_result.resource if revision_result.accepted else None,
        "validation": revision_result.validation,
        "acceptance": revision_result.acceptance,
        "attempts": revision_result.attempts,
        "revision_feedback": revision_result.revision_feedback,
        "errors": errors,
    }


def execute_resource_production_pipeline(
    task: TaskPacket,
    tool: ToolCandidate,
    provider: ResourceProvider,
    *,
    reviser: Callable[[TaskPacket, dict[str, Any], ResourceValidationResult], dict[str, Any]] | None = None,
    max_revisions: int = 1,
    acceptance_gate: ResourceAcceptanceGate | None = None,
) -> dict[str, Any]:
    """Produce, QC, revise when allowed, and accept a resource without provider bypass."""
    production = execute_resource_provider(task, tool, provider)
    if production["status"] != "PRODUCED":
        return production

    processed = process_produced_resource(
        task,
        production["result"],
        reviser=reviser,
        max_revisions=max_revisions,
        acceptance_gate=acceptance_gate,
    )
    return {**production, **processed}


def execute_resource_production_with_fallback(
    task: TaskPacket,
    tools: list[ToolCandidate],
    providers: dict[str, ResourceProvider],
    *,
    reviser: Callable[[TaskPacket, dict[str, Any], ResourceValidationResult], dict[str, Any]] | None = None,
    max_revisions: int = 1,
    acceptance_gate: ResourceAcceptanceGate | None = None,
    free_first: bool = True,
    validation_registry: CapabilityValidationRegistry | None = None,
) -> dict[str, Any]:
    """Fallback between providers, then QC the first successful output exactly once."""
    policy = ProviderExecutionPolicy(free_first=free_first)
    execution = policy.execute(
        task,
        tools,
        providers,
        executor=execute_resource_provider,
        validation_registry=validation_registry,
    )
    execution_trace = {"attempts": execution.attempts, "excluded_tools": execution.excluded_tools}
    if execution.status != "PRODUCED":
        return {
            "status": execution.status,
            "task_id": execution.task_id,
            "tool_id": execution.tool_id,
            "result": None,
            "provider_attempts": execution.attempts,
            "provider_execution_trace": execution_trace,
            "errors": execution.errors,
        }

    processed = process_produced_resource(
        task,
        execution.result or {},
        reviser=reviser,
        max_revisions=max_revisions,
        acceptance_gate=acceptance_gate,
    )
    return {
        "status": processed["status"],
        "task_id": task.task_id,
        "tool_id": execution.tool_id,
        "result": processed["result"],
        "validation": processed["validation"],
        "acceptance": processed["acceptance"],
        "attempts": processed["attempts"],
        "revision_feedback": processed["revision_feedback"],
        "provider_attempts": execution.attempts,
        "provider_execution_trace": execution_trace,
        "errors": processed["errors"],
    }


def execute_resource_generation(
    task: TaskPacket,
    tool: ToolCandidate,
    generators: dict[str, Callable[..., Any]],
) -> dict[str, Any]:
    """Execute an eligible resource provider against the approved TaskPacket."""
    generator = generators.get(tool.tool_id)
    eligibility_errors = validate_provider_task_eligibility(tool, "RESOURCE_PRODUCTION", generator, required_capabilities=set(capabilities_for_resource(task.required_output, source_based=task.source_based, visual=task.visual)))
    if eligibility_errors:
        return {"status": "HUMAN_HANDOFF", "tool_id": tool.tool_id, "result": None, "errors": eligibility_errors}
    provider = FunctionResourceProvider(generator)
    return execute_resource_provider(task, tool, provider)
