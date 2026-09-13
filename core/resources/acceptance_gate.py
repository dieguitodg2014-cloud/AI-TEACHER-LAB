"""Final acceptance boundary for produced instructional resources."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from core.foundation.models import TaskPacket
from core.resources.output_validator import ResourceValidationResult


AcceptanceDecision = Literal[
    "ACCEPT",
    "REVISION_REQUIRED",
    "REJECT_AND_REDESIGN",
    "HUMAN_HANDOFF",
]


@dataclass(frozen=True)
class ResourceAcceptanceResult:
    """Decision controlling whether a resource may cross the delivery boundary."""

    decision: AcceptanceDecision
    reasons: list[str] = field(default_factory=list)
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
    ) -> ResourceAcceptanceResult:
        if validation is None:
            return ResourceAcceptanceResult(
                decision="HUMAN_HANDOFF",
                reasons=["RESOURCE_VALIDATION_MISSING"],
                blocking=True,
            )

        if validation.status == "READY" and not validation.critical_failure:
            return ResourceAcceptanceResult(
                decision="ACCEPT",
                reasons=["Resource passed the approved TaskPacket validation boundary."],
                blocking=False,
                validation_id=validation.validation_id,
            )

        if validation.status == "REVISION_REQUIRED":
            return ResourceAcceptanceResult(
                decision="REVISION_REQUIRED",
                reasons=list(validation.feedback) or ["Resource requires revision before acceptance."],
                blocking=True,
                validation_id=validation.validation_id,
            )

        if validation.status == "REJECT_AND_REDESIGN":
            return ResourceAcceptanceResult(
                decision="REJECT_AND_REDESIGN",
                reasons=list(validation.feedback) or list(validation.blocking_errors) or ["Resource must be redesigned."],
                blocking=True,
                validation_id=validation.validation_id,
            )

        return ResourceAcceptanceResult(
            decision="HUMAN_HANDOFF",
            reasons=list(validation.blocking_errors) or ["Resource failed the acceptance boundary."],
            blocking=True,
            validation_id=validation.validation_id,
        )


def accept_resource(
    task: TaskPacket,
    validation: ResourceValidationResult | None,
) -> ResourceAcceptanceResult:
    """Convenience function for the final resource acceptance decision."""
    return ResourceAcceptanceGate().evaluate(task, validation)
