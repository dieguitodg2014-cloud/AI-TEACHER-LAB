"""Minimal provider contract for executable instructional resources."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Callable, Protocol

from core.foundation.models import TaskPacket


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

    def produce(self, task_packet: TaskPacket) -> dict[str, Any]:
        result = self._generator(asdict(task_packet))
        if not isinstance(result, dict):
            raise TypeError("RESOURCE_OUTPUT_NOT_OBJECT")
        return result
