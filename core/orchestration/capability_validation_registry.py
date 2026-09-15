"""Immutable registry for evidence-backed provider capability validation."""

from __future__ import annotations

from dataclasses import dataclass

from core.orchestration.capability_validation import (
    NOT_VALIDATED,
    VALIDATED,
    CapabilityValidationResult,
    capability_fingerprint,
)
from core.orchestration.tool_selector import ToolCandidate


@dataclass(frozen=True)
class CapabilityValidationRegistry:
    """Evidence registry keyed by provider capability."""

    results: tuple[CapabilityValidationResult, ...] = ()

    def record(self, result: CapabilityValidationResult) -> "CapabilityValidationRegistry":
        """Return a new registry containing the latest result for its key."""
        key = (result.tool_id, result.capability)
        retained = tuple(
            existing
            for existing in self.results
            if (existing.tool_id, existing.capability) != key
        )
        return CapabilityValidationRegistry(results=retained + (result,))

    def get(self, tool_id: str, capability: str) -> CapabilityValidationResult | None:
        """Return the latest recorded result for a provider capability."""
        for result in reversed(self.results):
            if result.tool_id == tool_id and result.capability == capability:
                return result
        return None

    def effective_tool(self, tool: ToolCandidate) -> ToolCandidate:
        """Return a copy with only current, evidence-backed validations promoted."""
        validation = dict(tool.capability_validation)
        current_fingerprint = capability_fingerprint(tool)
        for capability in tool.capabilities:
            result = self.get(tool.tool_id, capability)
            if result is None:
                continue
            if result.status == VALIDATED:
                if result.tool_fingerprint == current_fingerprint and result.evidence:
                    validation[capability] = VALIDATED
                else:
                    validation[capability] = NOT_VALIDATED
            elif result.status == NOT_VALIDATED:
                validation[capability] = NOT_VALIDATED
        return ToolCandidate(
            tool_id=tool.tool_id,
            capabilities=tool.capabilities,
            quality=tool.quality,
            reliability=tool.reliability,
            accessibility=tool.accessibility,
            speed=tool.speed,
            cost=tool.cost,
            capability_validation=tuple(sorted(validation.items())),
            provider_revision=tool.provider_revision,
        )
