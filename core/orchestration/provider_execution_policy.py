"""Bounded provider execution with capability-safe fallback."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Callable

from core.foundation.models import TaskPacket
from core.orchestration.capability_matrix import capabilities_for_resource
from core.orchestration.capability_validation_registry import CapabilityValidationRegistry
from core.orchestration.resource_provider import ResourceProvider
from core.orchestration.resource_tool_router import select_resource_provider
from core.orchestration.tool_selector import ToolCandidate


ProviderExecutor = Callable[[TaskPacket, ToolCandidate, ResourceProvider], dict[str, Any]]
KNOWN_EXECUTION_STATUSES = frozenset({"PRODUCED", "HUMAN_HANDOFF"})


@dataclass(frozen=True)
class ProviderAttempt:
    """Trace of one provider execution attempt."""

    attempt: int
    task_id: str
    tool_id: str
    status: str
    errors: tuple[str, ...] = ()


@dataclass(frozen=True)
class ProviderExecutionResult:
    """Result of bounded provider selection/execution."""

    status: str
    task_id: str
    tool_id: str | None
    result: dict[str, Any] | None
    attempts: tuple[ProviderAttempt, ...]
    errors: tuple[str, ...] = ()
    excluded_tools: tuple[tuple[str, str], ...] = ()


def _excluded_tools(
    tools: list[ToolCandidate],
    required: set[str],
    blocked: set[str],
    providers: dict[str, ResourceProvider] | None = None,
) -> tuple[tuple[str, str], ...]:
    """Explain why configured providers were not eligible for execution."""
    excluded: list[tuple[str, str]] = []
    for tool in tools:
        if tool.tool_id in blocked:
            excluded.append((tool.tool_id, "BLOCKED_AFTER_EXECUTION_FAILURE"))
            continue
        if providers is not None and tool.tool_id not in providers:
            excluded.append((tool.tool_id, "RESOURCE_PROVIDER_NOT_CONFIGURED"))
            continue
        not_validated = sorted(
            capability
            for capability in required
            if tool.validation_status(capability) == "not_validated"
        )
        if not_validated:
            excluded.append(
                (tool.tool_id, f"CAPABILITY_NOT_VALIDATED:{','.join(not_validated)}")
            )
            continue
        missing = sorted(required - set(tool.capabilities))
        if missing:
            excluded.append(
                (tool.tool_id, f"MISSING_REQUIRED_CAPABILITIES:{','.join(missing)}")
            )
    return tuple(excluded)


def _is_capability_rejection(errors: tuple[str, ...]) -> bool:
    """Return whether execution was denied by capability policy, not by provider failure."""
    return any(error.startswith("CAPABILITY_NOT_VALIDATED:") for error in errors)


def _normalize_executor_outcome(outcome: Any) -> dict[str, Any]:
    """Normalize malformed custom-executor output at the policy boundary."""
    if not isinstance(outcome, dict):
        return {
            "status": "HUMAN_HANDOFF",
            "result": None,
            "errors": ["RESOURCE_PROVIDER_EXECUTOR_OUTPUT_NOT_OBJECT"],
        }
    status = outcome.get("status")
    errors = outcome.get("errors", [])
    if not isinstance(errors, (list, tuple)) or not all(isinstance(error, str) for error in errors):
        return {
            "status": "HUMAN_HANDOFF",
            "result": None,
            "errors": ["RESOURCE_PROVIDER_EXECUTOR_ERRORS_NOT_LIST"],
        }
    if not isinstance(status, str):
        return {
            "status": "HUMAN_HANDOFF",
            "result": None,
            "errors": ["RESOURCE_PROVIDER_EXECUTOR_STATUS_MISSING"],
        }
    if status not in KNOWN_EXECUTION_STATUSES:
        return {
            "status": "HUMAN_HANDOFF",
            "result": None,
            "errors": [f"RESOURCE_PROVIDER_EXECUTOR_UNKNOWN_STATUS:{status}"],
            "_terminal": True,
        }
    return outcome


class ProviderExecutionPolicy:
    """Execute providers with technical fallback while preserving the TaskPacket."""

    def __init__(
        self,
        *,
        free_first: bool = True,
        provider_priority: list[str] | tuple[str, ...] = (),
    ) -> None:
        self.free_first = free_first
        self.provider_priority = tuple(provider_priority)

    def execute(
        self,
        task: TaskPacket,
        tools: list[ToolCandidate],
        providers: dict[str, ResourceProvider],
        *,
        executor: ProviderExecutor | None = None,
        validation_registry: CapabilityValidationRegistry | None = None,
    ) -> ProviderExecutionResult:
        if executor is None:
            from core.orchestration.resource_orchestrator import execute_resource_provider

            executor = execute_resource_provider

        blocked: set[str] = set()
        attempts: list[ProviderAttempt] = []
        required = set(
            capabilities_for_resource(
                task.required_output,
                source_based=task.source_based,
                visual=task.visual,
            )
        )
        effective_tools = [
            validation_registry.effective_tool(tool)
            if validation_registry is not None
            else tool
            for tool in tools
        ]

        while True:
            eligible_tools = [
                tool
                for tool in effective_tools
                if tool.tool_id in providers
            ]
            tool = select_resource_provider(
                task,
                eligible_tools,
                free_first=self.free_first,
                blocked_tools=blocked,
                provider_priority=self.provider_priority,
            )
            excluded_tools = _excluded_tools(effective_tools, required, blocked, providers)
            if tool is None:
                return ProviderExecutionResult(
                    status="HUMAN_HANDOFF",
                    task_id=task.task_id,
                    tool_id=None,
                    result=None,
                    attempts=tuple(attempts),
                    errors=("NO_ELIGIBLE_RESOURCE_TOOL_AFTER_FALLBACK",),
                    excluded_tools=excluded_tools,
                )

            try:
                raw_outcome = executor(deepcopy(task), tool, providers[tool.tool_id])
            except Exception as exc:
                outcome = {
                    "status": "HUMAN_HANDOFF",
                    "result": None,
                    "errors": [f"RESOURCE_PROVIDER_EXECUTOR_ERROR:{exc}"],
                }
            else:
                outcome = _normalize_executor_outcome(raw_outcome)

            outcome_errors = tuple(outcome.get("errors", []))
            attempt = ProviderAttempt(
                attempt=len(attempts) + 1,
                task_id=task.task_id,
                tool_id=tool.tool_id,
                status=outcome["status"],
                errors=outcome_errors,
            )
            attempts.append(attempt)

            if outcome.get("_terminal"):
                return ProviderExecutionResult(
                    status="HUMAN_HANDOFF",
                    task_id=task.task_id,
                    tool_id=tool.tool_id,
                    result=None,
                    attempts=tuple(attempts),
                    errors=outcome_errors,
                    excluded_tools=_excluded_tools(effective_tools, required, blocked, providers),
                )

            if outcome["status"] == "PRODUCED":
                if not isinstance(outcome.get("result"), dict):
                    outcome_errors = ("RESOURCE_PROVIDER_EXECUTOR_RESULT_NOT_OBJECT",)
                    attempts[-1] = ProviderAttempt(
                        attempt=attempt.attempt,
                        task_id=attempt.task_id,
                        tool_id=attempt.tool_id,
                        status="HUMAN_HANDOFF",
                        errors=outcome_errors,
                    )
                else:
                    return ProviderExecutionResult(
                        status="PRODUCED",
                        task_id=task.task_id,
                        tool_id=tool.tool_id,
                        result=outcome["result"],
                        attempts=tuple(attempts),
                        errors=(),
                        excluded_tools=_excluded_tools(effective_tools, required, blocked, providers),
                    )

            if _is_capability_rejection(outcome_errors):
                return ProviderExecutionResult(
                    status="HUMAN_HANDOFF",
                    task_id=task.task_id,
                    tool_id=tool.tool_id,
                    result=None,
                    attempts=tuple(attempts),
                    errors=outcome_errors,
                    excluded_tools=_excluded_tools(effective_tools, required, blocked, providers),
                )

            blocked.add(tool.tool_id)
