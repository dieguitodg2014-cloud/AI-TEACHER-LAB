"""Formal validation contract for provider capabilities."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json

from core.orchestration.tool_selector import ToolCandidate

VALIDATED = "validated"
NOT_VALIDATED = "not_validated"


def capability_fingerprint(tool: ToolCandidate) -> str:
    """Return a stable fingerprint for the provider capability configuration."""
    payload = {
        "tool_id": tool.tool_id,
        "capabilities": sorted(tool.capabilities),
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True)
class CapabilityValidationResult:
    """Immutable evidence result for one provider capability."""

    tool_id: str
    capability: str
    status: str
    evidence: tuple[str, ...] = ()
    tool_fingerprint: str = ""

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
    """Produce a validation result bound to the provider capability configuration.

    Validation evidence is tied to the current provider capability fingerprint.
    A capability cannot become validated without explicit evidence.
    """
    normalized_evidence = tuple(evidence)
    fingerprint = capability_fingerprint(tool)
    if capability not in tool.capabilities or not passed or not normalized_evidence:
        return CapabilityValidationResult(
            tool_id=tool.tool_id,
            capability=capability,
            status=NOT_VALIDATED,
            evidence=normalized_evidence,
            tool_fingerprint=fingerprint,
        )
    return CapabilityValidationResult(
        tool_id=tool.tool_id,
        capability=capability,
        status=VALIDATED,
        evidence=normalized_evidence,
        tool_fingerprint=fingerprint,
    )


def apply_validation_result(
    tool: ToolCandidate,
    result: CapabilityValidationResult,
) -> ToolCandidate:
    """Return a new candidate carrying validation evidence; never mutate the original."""
    if result.tool_id != tool.tool_id:
        raise ValueError("CAPABILITY_VALIDATION_TOOL_MISMATCH")
    if result.capability not in tool.capabilities:
        raise ValueError("CAPABILITY_VALIDATION_NOT_DECLARED")
    if result.status not in {VALIDATED, NOT_VALIDATED}:
        raise ValueError("INVALID_CAPABILITY_VALIDATION_STATUS")
    if result.status == VALIDATED and not result.evidence:
        raise ValueError("VALIDATED_CAPABILITY_REQUIRES_EVIDENCE")
    if result.status == VALIDATED and result.tool_fingerprint != capability_fingerprint(tool):
        raise ValueError("STALE_CAPABILITY_VALIDATION")

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
