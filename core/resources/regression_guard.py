"""Regression protection for instructional resource revisions.

The guard prevents a revision from fixing one validated dimension while
silently breaking another dimension that had already passed QC.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from core.foundation.models import TaskPacket
from core.resources.output_validator import ResourceValidationResult


@dataclass(frozen=True)
class ResourceRegressionResult:
    """Result of checking a revised resource for regressions."""

    passed: bool
    errors: list[str]


# These dimensions are part of the authoritative TaskPacket contract and must
# not regress once they have passed validation during an earlier attempt.
_PROTECTED_RESOURCE_CHECKS = (
    "resource_type",
    "level_alignment",
    "objective_alignment",
)


def check_resource_revision_regression(
    task: TaskPacket,
    previous_validation: ResourceValidationResult,
    revised_resource: dict[str, Any],
) -> ResourceRegressionResult:
    """Ensure a revision does not break dimensions that previously passed.

    A failing dimension may legitimately change during revision because the
    revision exists to repair it. A dimension that already passed, however,
    must remain aligned with the authoritative TaskPacket.
    """
    errors: list[str] = []

    if previous_validation.checks.get("resource_type"):
        actual_type = str(revised_resource.get("resource_type", "")).strip()
        expected_type = task.required_output.strip()
        if actual_type != expected_type:
            errors.append(
                f"RESOURCE_REGRESSION:resource_type changed after passing validation; expected '{expected_type}', got '{actual_type or 'missing'}'."
            )

    if previous_validation.checks.get("level_alignment"):
        actual_level = str(revised_resource.get("level", "")).strip().upper()
        if actual_level != task.level:
            errors.append(
                f"RESOURCE_REGRESSION:level changed after passing validation; expected '{task.level}', got '{actual_level or 'missing'}'."
            )

    if previous_validation.checks.get("objective_alignment"):
        actual_objective = str(revised_resource.get("objective", "")).strip()
        if actual_objective != task.objective.strip():
            errors.append(
                "RESOURCE_REGRESSION:objective changed after passing validation; the revision no longer matches the authorized objective."
            )

    return ResourceRegressionResult(passed=not errors, errors=errors)


def task_packet_unchanged(before: TaskPacket, after: TaskPacket) -> bool:
    """Return whether the authorized TaskPacket remained unchanged."""
    return before == after
