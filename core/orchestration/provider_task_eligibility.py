"""Validate whether a selected provider is eligible for a concrete task."""

from __future__ import annotations

from typing import Any, Callable

from core.orchestration.provider_capability_contract import (
    provider_supports_capabilities,
    validate_provider_capabilities,
)
from core.orchestration.tool_selector import ToolCandidate


TASK_CAPABILITIES = {
    "LESSON_GENERATION": "lesson_generation",
    "RESOURCE_PRODUCTION": "resource_generation",
}


def validate_provider_task_eligibility(
    provider: ToolCandidate,
    task_type: str,
    generator: Callable[..., Any] | None,
    *,
    required_capabilities: set[str] | None = None,
) -> list[str]:
    """Return errors when a selected provider cannot execute the approved task."""
    errors: list[str] = []

    capability_errors = validate_provider_capabilities(provider.capabilities)
    if capability_errors:
        errors.extend(capability_errors)
        return errors

    task_capability = TASK_CAPABILITIES.get(task_type)
    if task_capability is None:
        return [f"TASK_TYPE_UNSUPPORTED:{task_type}"]

    required = required_capabilities or {task_capability}
    if not provider_supports_capabilities(provider.capabilities, required):
        errors.append(
            f"PROVIDER_NOT_ELIGIBLE_FOR_TASK:{provider.tool_id}:{task_type}"
        )

    if task_capability not in required:
        errors.append(
            f"TASK_CAPABILITY_MISMATCH:{task_type}:{task_capability}"
        )

    if generator is None or not callable(generator):
        errors.append(f"GENERATOR_UNAVAILABLE:{provider.tool_id}")

    return errors
