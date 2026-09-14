"""Formal return boundary for externally produced instructional resources.

This module closes the production loop without making any provider responsible
for pedagogical decisions. A returned resource is validated against the exact
Resource TaskPacket that authorized its production, then crosses the final
acceptance boundary before it can be considered deliverable.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from core.foundation.models import Context, TaskPacket
from core.orchestration.resource_handoff import build_resource_revision_handoff
from core.resources.acceptance_gate import ResourceAcceptanceGate
from core.resources.output_validator import ResourceValidationResult, validate_resource_output


@dataclass(frozen=True)
class ResourceReturnResult:
    """Normalized result of receiving and accepting a produced resource."""

    status: str
    task_id: str
    validation: ResourceValidationResult
    revision_handoff: dict[str, Any] | None
    errors: tuple[str, ...]

    def __post_init__(self) -> None:
        """Defensively normalize return errors to an immutable collection."""
        object.__setattr__(self, "errors", tuple(self.errors))


def receive_resource(
    context: Context,
    task: TaskPacket,
    produced_resource: dict[str, Any] | None,
    *,
    revision_count: int = 0,
) -> ResourceReturnResult:
    """Receive an external resource and route it through QC and acceptance.

    ``READY`` is a QC result, not delivery authorization. A returned resource
    reaches ``ACCEPTED`` only when the ResourceAcceptanceGate authorizes it.
    The return boundary does not generate, repair, or reinterpret the resource.
    """
    if produced_resource is None:
        validation = ResourceValidationResult(
            validation_id="resource-qc-no-return",
            status="REJECT",
            score=0.0,
            critical_failure=True,
            checks={"resource_returned": False},
            blocking_errors=["No produced resource was returned for validation."],
        )
    else:
        validation = validate_resource_output(
            task,
            produced_resource,
            revision_count=revision_count,
        )

    acceptance = ResourceAcceptanceGate().evaluate(task, validation)
    revision_handoff = None
    if acceptance.decision == "REVISION_REQUIRED":
        revision_handoff = build_resource_revision_handoff(
            context,
            task,
            validation,
        )

    status = {
        "ACCEPT": "ACCEPTED",
        "REVISION_REQUIRED": "REVISION_REQUIRED",
        "REJECT_AND_REDESIGN": "REJECT_AND_REDESIGN",
        "HUMAN_HANDOFF": "HUMAN_HANDOFF",
    }[acceptance.decision]

    return ResourceReturnResult(
        status=status,
        task_id=task.task_id,
        validation=validation,
        revision_handoff=revision_handoff,
        errors=tuple(acceptance.reasons),
    )


def resource_return_to_dict(result: ResourceReturnResult) -> dict[str, Any]:
    """Serialize a resource-return result for an API, CLI, or future UI."""
    return asdict(result)
