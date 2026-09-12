"""Boundary contract for provider-generated lesson artifacts."""

from __future__ import annotations

from typing import Any


PROVIDER_OUTPUT_REQUIRED_FIELDS = (
    "level",
    "objective",
    "duration_minutes",
    "activities",
)


def validate_provider_output(value: Any) -> list[str]:
    """Return boundary errors without performing pedagogical QC.

    Providers must return a JSON-compatible lesson artifact dictionary with the
    minimum top-level fields required by the existing generation/QC pipeline.
    Semantic correctness remains the responsibility of Generation QC.
    """
    errors: list[str] = []

    if not isinstance(value, dict):
        return ["PROVIDER_OUTPUT_NOT_OBJECT"]

    missing = [field for field in PROVIDER_OUTPUT_REQUIRED_FIELDS if field not in value]
    errors.extend(f"PROVIDER_OUTPUT_MISSING:{field}" for field in missing)

    if "level" in value and not isinstance(value["level"], str):
        errors.append("PROVIDER_OUTPUT_INVALID_TYPE:level")
    if "objective" in value and not isinstance(value["objective"], str):
        errors.append("PROVIDER_OUTPUT_INVALID_TYPE:objective")
    if "duration_minutes" in value and (
        not isinstance(value["duration_minutes"], int) or isinstance(value["duration_minutes"], bool)
    ):
        errors.append("PROVIDER_OUTPUT_INVALID_TYPE:duration_minutes")
    if "activities" in value and not isinstance(value["activities"], list):
        errors.append("PROVIDER_OUTPUT_INVALID_TYPE:activities")

    return errors
