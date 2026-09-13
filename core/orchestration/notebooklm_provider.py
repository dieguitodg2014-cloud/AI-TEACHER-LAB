"""NotebookLM provider adapter for approved resource TaskPackets.

The adapter deliberately contains no pedagogical decision logic and no direct
NotebookLM API dependency. An executable NotebookLM connector can be injected
through ``executor`` when one is available. Until then, the existing
``notebooklm_handoff`` module remains the human-execution path.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict
from typing import Any, Callable

from core.foundation.models import TaskPacket


NotebookLMExecutor = Callable[[dict[str, Any]], dict[str, Any]]


class NotebookLMResourceProvider:
    """Provider adapter that executes an already-approved task in NotebookLM.

    NotebookLM receives a defensive serialized copy of the TaskPacket. The
    authoritative task remains owned by Bionic and cannot be mutated by the
    external connector.
    """

    tool_id = "notebooklm"

    def __init__(self, executor: NotebookLMExecutor | None = None) -> None:
        if executor is not None and not callable(executor):
            raise TypeError("NOTEBOOKLM_EXECUTOR_NOT_CALLABLE")
        self._executor = executor

    def can_produce(self, task_packet: TaskPacket) -> bool:
        """Return whether the adapter is configured for resource production."""
        return (
            task_packet.task_type == "RESOURCE_PRODUCTION"
            and self._executor is not None
        )

    def produce(self, task_packet: TaskPacket) -> dict[str, Any]:
        """Execute the approved task through the injected NotebookLM connector."""
        if self._executor is None:
            raise RuntimeError("NOTEBOOKLM_CONNECTOR_NOT_CONFIGURED")

        payload = asdict(deepcopy(task_packet))
        result = self._executor({
            "task": payload,
            "provider": self.tool_id,
        })
        if not isinstance(result, dict):
            raise TypeError("NOTEBOOKLM_RESOURCE_OUTPUT_NOT_OBJECT")
        return result
