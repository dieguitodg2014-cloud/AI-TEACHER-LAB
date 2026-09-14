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
    """Produce a validation result without mutating provider configuration."""
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


def apply_validation_result(
    tool: ToolCandidate,
    result: CapabilityValidationResult,
) -> ToolCandidate:
    """Return a new candidate carrying validated evidence; never mutate the original."""
    if result.tool_id != tool.tool_id:
        raise ValueError("CAPABILITY_VALIDATION_TOOL_MISMATCH")
    if result.capability not in tool.capabilities:
        raise ValueError("CAPABILITY_VALIDATION_NOT_DECLARED")
    if result.status not in {VALIDATED, NOT_VALIDATED}:
        raise ValueError("INVALID_CAPABILITY_VALIDATION_STATUS")

    validation = dict(tool.capability_validation)
    validation[result.capability] = result.status
    return ToolCandidate(
        tool_id=tool.tool_id,
        capabilities=tool.capabilities,
        quality=tool.quality,
        reliability=tool.reliability,
        accessibility=tool.accessibility,
        speed=tool.speed,
        cost=tool.cost,
        capability_validation=tuple(sorted(validation.items())),
    )
