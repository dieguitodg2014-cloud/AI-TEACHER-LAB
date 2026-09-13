"""Bounded revision engine for produced instructional resources."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
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
    """Terminal result of the resource QC/revision/acceptance loop."""

    status: str
    accepted: bool
    attempts: int
    resource: dict[str, Any] | None
    validation: ResourceValidationResult | None
    acceptance: ResourceAcceptanceResult | None
    revision_feedback: list[str] = field(default_factory=list)


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

        resource = initial_resource
        revisions = 0
        last_validation: ResourceValidationResult | None = None
        last_acceptance: ResourceAcceptanceResult | None = None
        feedback: list[str] = []
        authorized_task = deepcopy(task)

        while True:
            validation = validate_resource_output(task, resource, revision_count=revisions)
            acceptance = self.acceptance_gate.evaluate(task, validation)
            last_validation = validation
            last_acceptance = acceptance

            if acceptance.decision == "ACCEPT":
                return ResourceRevisionResult(
                    status="ACCEPTED",
                    accepted=True,
                    attempts=revisions + 1,
                    resource=resource,
                    validation=validation,
                    acceptance=acceptance,
                    revision_feedback=feedback,
                )

            if acceptance.decision != "REVISION_REQUIRED":
                return ResourceRevisionResult(
                    status=acceptance.decision,
                    accepted=False,
                    attempts=revisions + 1,
                    resource=resource,
                    validation=validation,
                    acceptance=acceptance,
                    revision_feedback=feedback + acceptance.reasons,
                )

            if revisions >= max_revisions or reviser is None:
                handoff = ResourceAcceptanceResult(
                    decision="HUMAN_HANDOFF",
                    reasons=acceptance.reasons + ["Resource revision could not be completed within the approved revision boundary."],
                    blocking=True,
                    validation_id=validation.validation_id,
                )
                return ResourceRevisionResult(
                    status="HUMAN_HANDOFF",
                    accepted=False,
                    attempts=revisions + 1,
                    resource=resource,
                    validation=validation,
                    acceptance=handoff,
                    revision_feedback=feedback + acceptance.reasons,
                )

            feedback.extend(acceptance.reasons)
            revision_task = deepcopy(task)
            revised = reviser(revision_task, resource, validation)

            # The reviser is downstream of the pedagogical decision. It gets a
            # defensive TaskPacket copy and cannot mutate the authoritative task.
            if not task_packet_unchanged(authorized_task, revision_task):
                handoff = ResourceAcceptanceResult(
                    decision="HUMAN_HANDOFF",
                    reasons=[
                        "RESOURCE_REGRESSION:TASK_PACKET_MUTATED_BY_REVISER",
                        "The authorized TaskPacket must remain unchanged during resource revision.",
                    ],
                    blocking=True,
                    validation_id=validation.validation_id,
                )
                return ResourceRevisionResult(
                    status="HUMAN_HANDOFF",
                    accepted=False,
                    attempts=revisions + 1,
                    resource=resource,
                    validation=validation,
                    acceptance=handoff,
                    revision_feedback=feedback + handoff.reasons,
                )

            if not isinstance(revised, dict):
                handoff = ResourceAcceptanceResult(
                    decision="HUMAN_HANDOFF",
                    reasons=["RESOURCE_REVISER_RETURNED_INVALID_OUTPUT"],
                    blocking=True,
                    validation_id=validation.validation_id,
                )
                return ResourceRevisionResult(
                    status="HUMAN_HANDOFF",
                    accepted=False,
                    attempts=revisions + 1,
                    resource=resource,
                    validation=validation,
                    acceptance=handoff,
                    revision_feedback=feedback + handoff.reasons,
                )

            regression = check_resource_revision_regression(task, validation, revised)
            if not regression.passed:
                handoff = ResourceAcceptanceResult(
                    decision="HUMAN_HANDOFF",
                    reasons=regression.errors,
                    blocking=True,
                    validation_id=validation.validation_id,
                )
                return ResourceRevisionResult(
                    status="HUMAN_HANDOFF",
                    accepted=False,
                    attempts=revisions + 1,
                    resource=resource,
                    validation=validation,
                    acceptance=handoff,
                    revision_feedback=feedback + regression.errors,
                )

            resource = revised
            revisions += 1


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
