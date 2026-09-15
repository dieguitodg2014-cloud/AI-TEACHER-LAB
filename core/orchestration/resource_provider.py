"""Minimal provider contract for executable instructional resources."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Callable, Protocol, runtime_checkable

from core.foundation.models import TaskPacket


@runtime_checkable
class ResourceProvider(Protocol):
    """Contract implemented by any executable resource provider.

    Providers execute an already-approved Resource TaskPacket. They do not
    choose the level, objective, assessment, resource need, or QC criteria.
    """

    def can_produce(self, task_packet: TaskPacket) -> bool:
        """Return whether this provider can execute the given task packet."""
        ...

    def produce(self, task_packet: TaskPacket) -> dict[str, Any]:
        """Produce a resource from the approved task packet."""
        ...


class FunctionResourceProvider:
    """Adapter that gives an existing callable the ResourceProvider contract."""

    def __init__(self, generator: Callable[[dict[str, Any]], dict[str, Any]]) -> None:
        if not callable(generator):
            raise TypeError("RESOURCE_PROVIDER_GENERATOR_NOT_CALLABLE")
        self._generator = generator

    def can_produce(self, task_packet: TaskPacket) -> bool:
        return task_packet.task_type == "RESOURCE_PRODUCTION"

    @staticmethod
    def _provider_payload(task_packet: TaskPacket) -> dict[str, Any]:
        """Serialize the approved task without exposing immutable internals.

        The authoritative TaskPacket remains deeply immutable. The connector
        boundary intentionally receives ordinary mutable containers so an
        external integration may inspect or mutate its local payload without
        ever mutating the approved task owned by the workflow.
        """
        payload = asdict(task_packet)
        payload["constraints"] = list(task_packet.constraints)
        payload["quality_criteria"] = list(task_packet.quality_criteria)
        payload["input_materials"] = list(task_packet.input_materials)
        return payload

    def produce(self, task_packet: TaskPacket) -> dict[str, Any]:
        result = self._generator(self._provider_payload(task_packet))
        if not isinstance(result, dict):
            raise TypeError("RESOURCE_OUTPUT_NOT_OBJECT")
        return result
