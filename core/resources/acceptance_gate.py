"""Final acceptance boundary for produced instructional resources."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from core.foundation.models import TaskPacket
from core.resources.output_validator import ResourceValidationResult, resource_fingerprint, task_packet_fingerprint


AcceptanceDecision = Literal[
    "ACCEPT",
    "REVISION_REQUIRED",
    "REJECT_AND_REDESIGN",
    "HUMAN_HANDOFF",
]


@dataclass(frozen=True)
class ResourceAcceptanceResult:
    """Immutable decision controlling whether a resource may cross delivery."""

    decision: AcceptanceDecision
    reasons: tuple[str, ...] = ()
    blocking: bool = False
    validation_id: str = ""


class ResourceAcceptanceGate:
    """Normalize resource QC into an explicit downstream acceptance boundary.

    Providers and QC may report that an output is READY, but only this gate can
    authorize the resource for downstream delivery. The gate never generates or
    revises content and never changes the approved TaskPacket.
    """

    def evaluate(
        self,
        task: TaskPacket,
        validation: ResourceValidationResult | None,
        produced_resource: dict[str, Any] | None = None,
    ) -> ResourceAcceptanceResult:
        if validation is None:
            return ResourceAcceptanceResult(
                decision="HUMAN_HANDOFF",
                reasons=("RESOURCE_VALIDATION_MISSING",),
                blocking=True,
            )

        expected_fingerprint = task_packet_fingerprint(task)
        if not validation.task_fingerprint:
            return ResourceAcceptanceResult(
                decision="HUMAN_HANDOFF",
                reasons=("RESOURCE_VALIDATION_TASK_BINDING_MISSING",),
                blocking=True,
                validation_id=validation.validation_id,
            )

        if validation.task_fingerprint != expected_fingerprint:
            return ResourceAcceptanceResult(
                decision="HUMAN_HANDOFF",
                reasons=("RESOURCE_VALIDATION_TASK_BINDING_MISMATCH",),
                blocking=True,
                validation_id=validation.validation_id,
            )

        if validation.status == "READY" and not validation.critical_failure:
            if produced_resource is None:
                return ResourceAcceptanceResult(
                    decision="HUMAN_HANDOFF",
                    reasons=("RESOURCE_VALIDATION_OUTPUT_MISSING",),
                    blocking=True,
                    validation_id=validation.validation_id,
                )
            if not validation.resource_fingerprint:
                return ResourceAcceptanceResult(
                    decision="HUMAN_HANDOFF",
                    reasons=("RESOURCE_VALIDATION_OUTPUT_BINDING_MISSING",),
                    blocking=True,
                    validation_id=validation.validation_id,
                )
            if resource_fingerprint(produced_resource) != validation.resource_fingerprint:
                return ResourceAcceptanceResult(
                    decision="HUMAN_HANDOFF",
                    reasons=("RESOURCE_VALIDATION_OUTPUT_BINDING_MISMATCH",),
                    blocking=True,
                    validation_id=validation.validation_id,
                )
            return ResourceAcceptanceResult(
                decision="ACCEPT",
                reasons=("Resource passed the approved TaskPacket validation boundary.",),
                blocking=False,
                validation_id=validation.validation_id,
            )

        if validation.status == "REVISION_REQUIRED":
            return ResourceAcceptanceResult(
                decision="REVISION_REQUIRED",
                reasons=tuple(validation.feedback) or ("Resource requires revision before acceptance.",),
                blocking=True,
                validation_id=validation.validation_id,
            )

        if validation.status == "REJECT_AND_REDESIGN":
            return ResourceAcceptanceResult(
                decision="REJECT_AND_REDESIGN",
                reasons=tuple(validation.feedback) or tuple(validation.blocking_errors) or ("Resource must be redesigned.",),
                blocking=True,
                validation_id=validation.validation_id,
            )

        return ResourceAcceptanceResult(
            decision="REJECT",
            reasons=tuple(validation.blocking_errors) or ("Resource failed the acceptance boundary.",),
            blocking=True,
            validation_id=validation.validation_id,
        )


def accept_resource(
    task: TaskPacket,
    validation: ResourceValidationResult | None,
    produced_resource: dict[str, Any] | None = None,
) -> ResourceAcceptanceResult:
    """Convenience function for the final resource acceptance decision."""
    return ResourceAcceptanceGate().evaluate(task, validation, produced_resource)
