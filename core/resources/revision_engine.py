"""Bounded revision engine for produced instructional resources."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Callable

from core.foundation.models import TaskPacket
from core.resources.acceptance_gate import ResourceAcceptanceGate, ResourceAcceptanceResult
from core.resources.output_validator import (
    MAX_RESOURCE_REVISIONS,
    ResourceValidationResult,
    validate_resource_output,
)
from core.resources.regression_guard import (
    check_resource_revision_regression,
    task_packet_unchanged,
)


@dataclass(frozen=True)
class ResourceRevisionResult:
    """Immutable terminal result of the resource QC/revision/acceptance loop."""

    status: str
    accepted: bool
    attempts: int
    resource: dict[str, Any] | None
    validation: ResourceValidationResult | None
    acceptance: ResourceAcceptanceResult | None
    revision_feedback: tuple[str, ...] = ()


class ResourceRevisionEngine:
    """Run bounded resource revision without allowing providers to redefine the task."""

    def __init__(self, acceptance_gate: ResourceAcceptanceGate | None = None) -> None:
        self.acceptance_gate = acceptance_gate or ResourceAcceptanceGate()

    def run(
        self,
        task: TaskPacket,
        initial_resource: dict[str, Any],
        reviser: Callable[[TaskPacket, dict[str, Any], ResourceValidationResult], dict[str, Any]] | None = None,
        *,
        max_revisions: int = MAX_RESOURCE_REVISIONS,
    ) -> ResourceRevisionResult:
        if max_revisions < 0:
            raise ValueError("max_revisions must be non-negative")

        resource = deepcopy(initial_resource)
        revisions = 0
        feedback: list[str] = []
        authorized_task = deepcopy(task)

        while True:
            validation = validate_resource_output(task, resource, revision_count=revisions)
            acceptance = self.acceptance_gate.evaluate(task, validation, resource)

            if acceptance.decision == "ACCEPT":
                return ResourceRevisionResult(
                    status="ACCEPTED",
                    accepted=True,
                    attempts=revisions + 1,
                    resource=resource,
                    validation=validation,
                    acceptance=acceptance,
                    revision_feedback=tuple(feedback),
                )

            if acceptance.decision != "REVISION_REQUIRED":
                return ResourceRevisionResult(
                    status=acceptance.decision,
                    accepted=False,
                    attempts=revisions + 1,
                    resource=resource,
                    validation=validation,
                    acceptance=acceptance,
                    revision_feedback=tuple(feedback) + acceptance.reasons,
                )

            if revisions >= max_revisions or reviser is None:
                terminal = ResourceAcceptanceResult(
                    decision="REJECT_AND_REDESIGN",
                    reasons=acceptance.reasons + (
                        "Resource revision could not be completed within the approved revision boundary.",
                    ),
                    blocking=True,
                    validation_id=validation.validation_id,
                )
                return ResourceRevisionResult(
                    status="REJECT_AND_REDESIGN",
                    accepted=False,
                    attempts=revisions + 1,
                    resource=resource,
                    validation=validation,
                    acceptance=terminal,
                    revision_feedback=tuple(feedback) + acceptance.reasons,
                )

            feedback.extend(acceptance.reasons)
            revision_task = deepcopy(task)
            revision_input = deepcopy(resource)
            revised = reviser(revision_task, revision_input, validation)

            if not task_packet_unchanged(authorized_task, revision_task):
                terminal = ResourceAcceptanceResult(
                    decision="REJECT",
                    reasons=(
                        "RESOURCE_REGRESSION:TASK_PACKET_MUTATED_BY_REVISER",
                        "The authorized TaskPacket must remain unchanged during resource revision.",
                    ),
                    blocking=True,
                    validation_id=validation.validation_id,
                )
                return ResourceRevisionResult(
                    status="REJECT",
                    accepted=False,
                    attempts=revisions + 1,
                    resource=resource,
                    validation=validation,
                    acceptance=terminal,
                    revision_feedback=tuple(feedback) + terminal.reasons,
                )

            if not isinstance(revised, dict):
                terminal = ResourceAcceptanceResult(
                    decision="REJECT",
                    reasons=("RESOURCE_REVISER_RETURNED_INVALID_OUTPUT",),
                    blocking=True,
                    validation_id=validation.validation_id,
                )
                return ResourceRevisionResult(
                    status="REJECT",
                    accepted=False,
                    attempts=revisions + 1,
                    resource=resource,
                    validation=validation,
                    acceptance=terminal,
                    revision_feedback=tuple(feedback) + terminal.reasons,
                )

            revised = _normalize_external_resource_shape(revised)
            regression = check_resource_revision_regression(task, validation, revised)
            if not regression.passed:
                terminal = ResourceAcceptanceResult(
                    decision="REJECT",
                    reasons=regression.errors,
                    blocking=True,
                    validation_id=validation.validation_id,
                )
                return ResourceRevisionResult(
                    status="REJECT",
                    accepted=False,
                    attempts=revisions + 1,
                    resource=resource,
                    validation=validation,
                    acceptance=terminal,
                    revision_feedback=tuple(feedback) + regression.errors,
                )

            resource = revised
            revisions += 1


def _normalize_external_resource_shape(resource: dict[str, Any]) -> dict[str, Any]:
    """Keep JSON-facing list fields mutable without weakening internal immutability."""
    normalized = deepcopy(resource)
    for field in ("quality_criteria_addressed", "source_references"):
        value = normalized.get(field)
        if isinstance(value, tuple):
            normalized[field] = list(value)
    return normalized


def revise_resource(
    task: TaskPacket,
    initial_resource: dict[str, Any],
    reviser: Callable[[TaskPacket, dict[str, Any], ResourceValidationResult], dict[str, Any]] | None = None,
    *,
    max_revisions: int = MAX_RESOURCE_REVISIONS,
) -> ResourceRevisionResult:
    """Convenience entry point for the bounded resource revision loop."""
    return ResourceRevisionEngine().run(
        task,
        initial_resource,
        reviser,
        max_revisions=max_revisions,
    )
