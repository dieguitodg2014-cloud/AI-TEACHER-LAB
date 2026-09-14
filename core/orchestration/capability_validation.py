"""Formal validation contract for provider capabilities."""

from __future__ import annotations

from dataclasses import dataclass

from core.orchestration.tool_selector import ToolCandidate

VALIDATED = "validated"
NOT_VALIDATED = "not_validated"


@dataclass(frozen=True)
class CapabilityValidationResult:
    """Immutable evidence result for one provider capability."""

    tool_id: str
    capability: str
    status: str
    evidence: tuple[str, ...] = ()

    @property
    def passed(self) -> bool:
        return self.status == VALIDATED


def validate_capability(
    tool: ToolCandidate,
    capability: str,
    *,
    passed: bool,
    evidence: tuple[str, ...] | list[str] = (),
) -> CapabilityValidationResult:
    """Produce a validation result without mutating provider configuration.

    Validation is evidence-driven: callers must explicitly report whether the
    capability test passed. A failed or absent validation never upgrades a
    capability to validated.
    """
    if capability not in tool.capabilities:
        return CapabilityValidationResult(
            tool_id=tool.tool_id,
            capability=capability,
            status=NOT_VALIDATED,
            evidence=tuple(evidence),
        )
    return CapabilityValidationResult(
        tool_id=tool.tool_id,
        capability=capability,
        status=VALIDATED if passed else NOT_VALIDATED,
        evidence=tuple(evidence),
    )
