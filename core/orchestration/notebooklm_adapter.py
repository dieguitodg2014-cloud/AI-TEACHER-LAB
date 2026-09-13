"""NotebookLM handoff adapter for approved resource tasks.

This module intentionally does not call NotebookLM. It defines the narrow
provider boundary that a future authorized connector can implement.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from core.foundation.models import TaskPacket
from core.orchestration.resource_provider import ResourceProvider


@dataclass(frozen=True)
class NotebookLMHandoff:
    """Immutable handoff envelope for an approved resource production task."""

    provider: str
    task_id: str
    task_type: str
    objective: str
    level: str
    required_output: str
    constraints: tuple[str, ...]
    quality_criteria: tuple[str, ...]
    audience: str


class NotebookLMAdapter(ResourceProvider):
    """Provider boundary for NotebookLM without pretending an API exists."""

    provider_id = "notebooklm"

    def can_produce(self, task: TaskPacket) -> bool:
        return (
            task.task_type == "RESOURCE_PRODUCTION"
            and bool(task.required_output)
        )

    def build_handoff(self, task: TaskPacket) -> NotebookLMHandoff:
        if not self.can_produce(task):
            raise ValueError("NOTEBOOKLM_TASK_NOT_ELIGIBLE")
        return NotebookLMHandoff(
            provider=self.provider_id,
            task_id=task.task_id,
            task_type=task.task_type,
            objective=task.objective,
            level=task.level,
            required_output=task.required_output,
            constraints=tuple(task.constraints),
            quality_criteria=tuple(task.quality_criteria),
            audience=task.audience,
        )

    def produce(self, task: TaskPacket) -> Any:
        """Return a connector handoff instead of claiming resource production."""
        return self.build_handoff(task)
