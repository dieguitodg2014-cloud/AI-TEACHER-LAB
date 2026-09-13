"""Bounded provider execution with capability-safe fallback."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from core.foundation.models import TaskPacket
from core.orchestration.resource_orchestrator import execute_resource_provider
from core.orchestration.resource_tool_router import select_resource_provider
from core.orchestration.resource_provider import ResourceProvider
from core.orchestration.tool_selector import ToolCandidate


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


class ProviderExecutionPolicy:
    """Execute providers with technical fallback while preserving the TaskPacket.

    This policy never changes pedagogical requirements. A failed provider is
    blocked for the remainder of the execution, and the same approved task is
    used for every subsequent attempt. Fallback is exhausted when no eligible
    provider remains, at which point the policy hands off to a human.
    """

    def __init__(self, *, free_first: bool = True) -> None:
        self.free_first = free_first

    def execute(
        self,
        task: TaskPacket,
        tools: list[ToolCandidate],
        providers: dict[str, ResourceProvider],
    ) -> ProviderExecutionResult:
        blocked: set[str] = set()
        attempts: list[ProviderAttempt] = []

        while True:
            tool = select_resource_provider(
                task,
                tools,
                free_first=self.free_first,
                blocked_tools=blocked,
            )
            if tool is None:
                return ProviderExecutionResult(
                    status="HUMAN_HANDOFF",
                    task_id=task.task_id,
                    tool_id=None,
                    result=None,
                    attempts=tuple(attempts),
                    errors=("NO_ELIGIBLE_RESOURCE_TOOL_AFTER_FALLBACK",),
                )

            provider = providers.get(tool.tool_id)
            if provider is None:
                outcome = {
                    "status": "HUMAN_HANDOFF",
                    "result": None,
                    "errors": ["RESOURCE_PROVIDER_NOT_CONFIGURED"],
                }
            else:
                outcome = execute_resource_provider(task, tool, provider)

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
                )

            blocked.add(tool.tool_id)
