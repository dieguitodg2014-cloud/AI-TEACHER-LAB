"""Validate provider capability declarations at the orchestration boundary."""

from __future__ import annotations

from typing import Any


# These are execution capabilities, not pedagogical decisions. New provider
# capabilities can be added here without changing the foundation models.
SUPPORTED_PROVIDER_CAPABILITIES = frozenset(
    {
        "lesson_generation",
        "resource_generation",
    }
)


def validate_provider_capabilities(value: Any) -> list[str]:
    """Return contract errors for a provider capability declaration.

    This checks whether a provider declares a structurally valid, known set of
    execution capabilities. It does not decide whether a provider is
    pedagogically appropriate for a task; that remains the responsibility of
    orchestration and tool selection.
    """
    if not isinstance(value, (list, tuple, set, frozenset)):
        return ["PROVIDER_CAPABILITIES_NOT_COLLECTION"]

    errors: list[str] = []
    for capability in value:
        if not isinstance(capability, str):
            errors.append("PROVIDER_CAPABILITY_INVALID_TYPE")
            continue
        if capability not in SUPPORTED_PROVIDER_CAPABILITIES:
            errors.append(f"PROVIDER_CAPABILITY_UNSUPPORTED:{capability}")

    return errors


def provider_supports_capabilities(
    declared_capabilities: Any,
    required_capabilities: set[str],
) -> bool:
    """Return whether a valid provider declaration covers all required capabilities."""
    if validate_provider_capabilities(declared_capabilities):
        return False
    return required_capabilities.issubset(set(declared_capabilities))
