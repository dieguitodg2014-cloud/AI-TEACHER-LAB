"""Provider-neutral compatibility checks for concrete resource outputs."""

from __future__ import annotations

from typing import Any


RESOURCE_OUTPUT_CAPABILITY_PREFIX = "resource_output:"


def resource_output_capability(required_output: str) -> str:
    """Map an approved TaskPacket output type to its execution capability."""
    normalized = "_".join(required_output.strip().lower().split())
    if not normalized:
        return ""
    return f"{RESOURCE_OUTPUT_CAPABILITY_PREFIX}{normalized}"


def provider_supports_resource_output(
    declared_capabilities: Any,
    required_output: str,
) -> bool:
    """Return whether a provider explicitly supports the approved output type."""
    capability = resource_output_capability(required_output)
    if not capability:
        return False
    if not isinstance(declared_capabilities, (list, tuple, set, frozenset)):
        return False
    return capability in declared_capabilities
