"""Canva provider adapter for approved resource TaskPackets.

The adapter contains no pedagogical decision logic and no direct Canva API
 dependency. An executable Canva connector can be injected through ``executor``.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict
from typing import Any, Callable

from core.foundation.models import TaskPacket


CanvaExecutor = Callable[[dict[str, Any]], dict[str, Any]]


def _externalize(value: Any) -> Any:
    """Convert immutable internal collections to connector-safe JSON shapes."""
    if isinstance(value, tuple):
        return [_externalize(item) for item in value]
    if isinstance(value, list):
        return [_externalize(item) for item in value]
    if isinstance(value, dict):
        return {key: _externalize(item) for key, item in value.items()}
    return value


class CanvaResourceProvider:
    """Provider adapter that executes an already-approved task in Canva."""

    tool_id = "canva"

    def __init__(self, executor: CanvaExecutor | None = None) -> None:
        if executor is not None and not callable(executor):
            raise TypeError("CANVA_EXECUTOR_NOT_CALLABLE")
        self._executor = executor

    def can_produce(self, task_packet: TaskPacket) -> bool:
        """Return whether the adapter is configured for resource production."""
        return (
            task_packet.task_type == "RESOURCE_PRODUCTION"
            and self._executor is not None
        )

    def produce(self, task_packet: TaskPacket) -> dict[str, Any]:
        """Execute the approved task through the injected Canva connector."""
        if self._executor is None:
            raise RuntimeError("CANVA_CONNECTOR_NOT_CONFIGURED")

        payload = _externalize(asdict(deepcopy(task_packet)))
        result = self._executor({
            "task": payload,
            "provider": self.tool_id,
        })
        if not isinstance(result, dict):
            raise TypeError("CANVA_RESOURCE_OUTPUT_NOT_OBJECT")
        return result
