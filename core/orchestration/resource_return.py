"""Formal return boundary for externally produced instructional resources.

This module closes the production loop without making any provider responsible
for pedagogical decisions. A returned resource is validated against the exact
Resource TaskPacket that authorized its production.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from core.foundation.models import Context, FrozenMapping, TaskPacket
from core.orchestration.resource_handoff import build_resource_revision_handoff
from core.resources.output_validator import ResourceValidationResult, validate_resource_output


@dataclass(frozen=True)
class ResourceReturnResult:
    """Normalized result of receiving and validating a produced resource."""

    status: str
    task_id: str
    validation: ResourceValidationResult
    revision_handoff: FrozenMapping | None
    errors: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "revision_handoff",
            FrozenMapping(self.revision_handoff) if self.revision_handoff is not None else None,
        )
        object.__setattr__(self, "errors", tuple(self.errors))


def receive_resource(
    context: Context,
    task: TaskPacket,
    produced_resource: dict[str, Any] | None,
    *,
    revision_count: int = 0,
) -> ResourceReturnResult:
    """Receive an external resource and route it through the Resource QC gate.

    The return boundary does not generate, repair, or reinterpret the resource.
    It only validates the returned artifact against the approved TaskPacket and,
    when appropriate, creates the next revision handoff.
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

    revision_handoff = None
    if validation.status == "REVISION_REQUIRED":
        revision_handoff = build_resource_revision_handoff(
            context,
            task,
            validation,
        )

    errors = list(validation.blocking_errors) + list(validation.feedback)
    return ResourceReturnResult(
        status=validation.status,
        task_id=task.task_id,
        validation=validation,
        revision_handoff=revision_handoff,
        errors=errors,
    )


def _materialize(value: Any) -> Any:
    """Convert immutable contract containers to JSON-compatible containers."""
    if isinstance(value, FrozenMapping):
        return {key: _materialize(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_materialize(item) for item in value]
    if isinstance(value, frozenset):
        return [_materialize(item) for item in value]
    if isinstance(value, dict):
        return {key: _materialize(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_materialize(item) for item in value]
    return value


def resource_return_to_dict(result: ResourceReturnResult) -> dict[str, Any]:
    """Serialize a resource-return result with JSON-friendly contract fields."""
    payload = asdict(result)
    payload["revision_handoff"] = _materialize(payload["revision_handoff"])
    validation = payload["validation"]
    validation["checks"] = dict(validation["checks"])
    validation["feedback"] = list(validation["feedback"])
    validation["blocking_errors"] = list(validation["blocking_errors"])
    payload["errors"] = list(payload["errors"])
    return payload
