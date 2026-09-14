"""Bounded provider execution with capability-safe fallback."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from core.foundation.models import TaskPacket
from core.orchestration.capability_matrix import capabilities_for_resource
from core.orchestration.resource_provider import ResourceProvider
from core.orchestration.resource_tool_router import select_resource_provider
from core.orchestration.tool_selector import ToolCandidate


ProviderExecutor = Callable[[TaskPacket, ToolCandidate, ResourceProvider], dict[str, Any]]


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
) -> tuple[tuple[str, str], ...]:
    """Explain why configured providers were not eligible for execution."""
    excluded: list[tuple[str, str]] = []
    for tool in tools:
        if tool.tool_id in blocked:
            excluded.append((tool.tool_id, "BLOCKED_AFTER_EXECUTION_FAILURE"))
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

        while True:
            tool = select_resource_provider(
                task,
                tools,
                free_first=self.free_first,
                blocked_tools=blocked,
                provider_priority=self.provider_priority,
            )
            excluded_tools = _excluded_tools(tools, required, blocked)
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

            provider = providers.get(tool.tool_id)
            if provider is None:
                outcome = {
                    "status": "HUMAN_HANDOFF",
                    "result": None,
                    "errors": ["RESOURCE_PROVIDER_NOT_CONFIGURED"],
                }
            else:
                outcome = executor(task, tool, provider)

            attempt = ProviderAttempt(
                attempt=len(attempts) + 1,
                task_id=task.task_id,
                tool_id=tool.tool_id,
                status=outcome["status"],
                errors=tuple(outcome.get("errors", [])),
            )
            attempts.append(attempt)

            if outcome["status"] == "PRODUCED":
                return ProviderExecutionResult(
                    status="PRODUCED",
                    task_id=task.task_id,
                    tool_id=tool.tool_id,
                    result=outcome["result"],
                    attempts=tuple(attempts),
                    errors=(),
                    excluded_tools=_excluded_tools(tools, required, blocked),
                )

            blocked.add(tool.tool_id)
