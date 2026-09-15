"""Small contract for approved instructional resource content.

Content generation remains separate from media production: a content provider
may draft a resource script, but the result must be explicitly approved before
it can enter a TaskPacket as provider input.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from core.foundation.models import TaskPacket
from core.resources.approved_content import ApprovedResourceContent


@dataclass(frozen=True)
class ResourceContentApproval:
    """Deterministic gate result for content entering media production."""

    status: str
    checks: tuple[str, ...]
    errors: tuple[str, ...] = ()


def validate_resource_content(
    task: TaskPacket,
    generated: dict[str, Any],
    *,
    expected_type: str,
) -> ResourceContentApproval:
    """Validate the minimum content contract before approval.

    This gate checks identity and presence only. Semantic pedagogical/language
    review remains the responsibility of the applicable QC layer; this function
    never rewrites or expands generated content.
    """
    errors: list[str] = []
    checks: list[str] = []

    if not isinstance(generated, dict):
        return ResourceContentApproval("REJECT", (), ("RESOURCE_CONTENT_OUTPUT_NOT_OBJECT",))

    content = generated.get("resource_content")
    if not isinstance(content, str) or not content.strip():
        errors.append("RESOURCE_CONTENT_REQUIRED")
    else:
        checks.append("content_present")

    content_type = generated.get("resource_content_type", expected_type or "script")
    if not isinstance(content_type, str) or not content_type.strip():
        errors.append("RESOURCE_CONTENT_TYPE_REQUIRED")
    elif expected_type and content_type.strip() != expected_type.strip():
        errors.append("RESOURCE_CONTENT_TYPE_MISMATCH")
    else:
        checks.append("content_type")

    declared_level = str(generated.get("level", "")).strip().upper()
    if declared_level and declared_level != task.level:
        errors.append("RESOURCE_CONTENT_LEVEL_MISMATCH")
    else:
        checks.append("level_alignment")

    declared_objective = str(generated.get("objective", "")).strip()
    if declared_objective and declared_objective != task.objective.strip():
        errors.append("RESOURCE_CONTENT_OBJECTIVE_MISMATCH")
    else:
        checks.append("objective_alignment")

    status = "REJECT" if errors else "READY"
    return ResourceContentApproval(status, tuple(checks), tuple(errors))


def approve_resource_content(
    generated: dict[str, Any],
    *,
    expected_type: str,
    task: TaskPacket | None = None,
) -> ApprovedResourceContent:
    """Turn validated generated content into the immutable approval contract."""
    if task is not None:
        validation = validate_resource_content(task, generated, expected_type=expected_type)
        if validation.status != "READY":
            raise ValueError("RESOURCE_CONTENT_NOT_APPROVED:" + ",".join(validation.errors))

    if not isinstance(generated, dict):
        raise TypeError("RESOURCE_CONTENT_OUTPUT_NOT_OBJECT")

    content = generated.get("resource_content")
    if not isinstance(content, str) or not content.strip():
        raise ValueError("RESOURCE_CONTENT_REQUIRED")

    content_type = generated.get("resource_content_type", expected_type or "script")
    return ApprovedResourceContent(content=content, content_type=content_type)


# Backward-compatible name for the original binding-only adapter.
def bind_approved_resource_content(
    generated: dict[str, Any],
    *,
    expected_type: str,
) -> ApprovedResourceContent:
    """Bind an already-reviewed artifact without performing semantic QC."""
    return approve_resource_content(generated, expected_type=expected_type)
