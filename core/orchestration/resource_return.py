"""Formal return boundary for externally produced instructional resources.

This module closes the production loop without making any provider responsible
for pedagogical decisions. A returned resource is validated against the exact
Resource TaskPacket that authorized its production.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from types import MappingProxyType
from typing import Any, Mapping

from core.foundation.models import Context, TaskPacket
from core.orchestration.resource_handoff import build_resource_revision_handoff
from core.resources.output_validator import ResourceValidationResult, validate_resource_output


def _freeze(value: Any) -> Any:
    """Recursively freeze mappings and common collection containers."""
    if isinstance(value, Mapping):
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(item) for item in value)
    if isinstance(value, tuple):
        return tuple(_freeze(item) for item in value)
    if isinstance(value, set):
        return frozenset(_freeze(item) for item in value)
    return value


def _thaw(value: Any) -> Any:
    """Recursively convert immutable evidence back to JSON-friendly values."""
    if isinstance(value, Mapping):
        return {key: _thaw(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw(item) for item in value]
    if isinstance(value, frozenset):
        return [_thaw(item) for item in value]
    return value


@dataclass(frozen=True)
class ResourceReturnResult:
    """Normalized result of receiving and validating a produced resource."""

    status: str
    task_id: str
    validation: ResourceValidationResult
    revision_handoff: Mapping[str, Any] | None
    errors: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.revision_handoff is not None:
            object.__setattr__(self, "revision_handoff", _freeze(self.revision_handoff))
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
            blocking_errors=("No produced resource was returned for validation.",),
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

    errors = tuple(validation.blocking_errors) + tuple(validation.feedback)
    return ResourceReturnResult(
        status=validation.status,
        task_id=task.task_id,
        validation=validation,
        revision_handoff=revision_handoff,
        errors=errors,
    )


def resource_return_to_dict(result: ResourceReturnResult) -> dict[str, Any]:
    """Serialize a resource-return result for an API, CLI, or future UI."""
    payload = asdict(result)
    payload["validation"]["checks"] = dict(result.validation.checks)
    payload["validation"]["feedback"] = list(result.validation.feedback)
    payload["validation"]["blocking_errors"] = list(result.validation.blocking_errors)
    payload["revision_handoff"] = _thaw(result.revision_handoff)
    payload["errors"] = list(result.errors)
    return payload
