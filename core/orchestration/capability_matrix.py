"""Capability requirements for pedagogically approved resource tasks."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ResourceCapabilityRequest:
    """Provider capabilities derived from an approved resource task."""

    resource_type: str
    source_based: bool = False
    visual: bool = False

    def required_capabilities(self) -> frozenset[str]:
        required = {"resource_generation"}
        normalized = self.resource_type.strip().lower()
        if normalized == "audio":
            required.add("audio_generation")
        if normalized in {"presentation", "slides"}:
            required.add("presentation_generation")
        if self.source_based:
            required.add("source_based_resource_generation")
        if self.visual:
            required.add("visual_resource_generation")
        return frozenset(required)


def capabilities_for_resource(
    resource_type: str,
    *,
    source_based: bool = False,
    visual: bool = False,
) -> frozenset[str]:
    """Return the minimum provider capabilities for a resource need."""
    return ResourceCapabilityRequest(
        resource_type=resource_type,
        source_based=source_based,
        visual=visual,
    ).required_capabilities()
