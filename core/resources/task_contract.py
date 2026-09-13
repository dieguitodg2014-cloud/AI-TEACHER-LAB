"""Provider-neutral validation boundary for resource production tasks.

The TaskPacket remains the transport model used by the MVP. This module makes
its pedagogical and execution invariants explicit before a provider receives it.
"""

from __future__ import annotations

from dataclasses import dataclass
from core.foundation.models import TaskPacket


@dataclass(frozen=True)
class ResourceTaskValidationResult:
    """Deterministic validation result for a resource production task."""

    valid: bool
    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()


class ResourceTaskContractValidator:
    """Validate the provider-neutral Resource TaskPacket boundary."""

    REQUIRED_TASK_TYPE = "RESOURCE_PRODUCTION"

    def validate(self, task: TaskPacket) -> ResourceTaskValidationResult:
        errors: list[str] = []
        warnings: list[str] = []

        if not isinstance(task, TaskPacket):
            return ResourceTaskValidationResult(False, ("TASK_PACKET_TYPE_INVALID",))

        if task.task_type != self.REQUIRED_TASK_TYPE:
            errors.append(f"TASK_TYPE_INVALID:{task.task_type}")
        if not task.task_id.strip():
            errors.append("TASK_ID_REQUIRED")
        if not task.objective.strip():
            errors.append("OBJECTIVE_REQUIRED")
        if task.level not in {"A0", "A1", "A2", "B1", "B2"}:
            errors.append(f"LEVEL_INVALID:{task.level}")
        if not task.required_output.strip():
            errors.append("REQUIRED_OUTPUT_REQUIRED")
        if not task.quality_criteria:
            errors.append("QUALITY_CRITERIA_REQUIRED")
        elif any(not item.strip() for item in task.quality_criteria):
            errors.append("QUALITY_CRITERIA_CONTAIN_EMPTY_ITEM")

        if task.status != "PENDING":
            warnings.append(f"TASK_STATUS_NOT_PENDING:{task.status}")
        if not task.audience.strip():
            warnings.append("AUDIENCE_NOT_DECLARED")
        if task.lesson_id and not task.lesson_id.strip():
            errors.append("LESSON_ID_INVALID")

        return ResourceTaskValidationResult(
            valid=not errors,
            errors=tuple(errors),
            warnings=tuple(warnings),
        )
