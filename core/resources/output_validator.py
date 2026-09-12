"""Deterministic validation gate for externally produced instructional resources.

The validator does not generate or rewrite resources. It checks whether a
produced resource satisfies the Resource TaskPacket that authorized its
production.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal
from uuid import uuid4

from core.foundation.models import TaskPacket


ValidationStatus = Literal["READY", "REVISION_REQUIRED", "REJECT", "REJECT_AND_REDESIGN"]

MAX_RESOURCE_REVISIONS = 1

RESOURCE_OUTPUT_CONTRACT: dict[str, Any] = {
    "required_fields": ["resource_type", "level", "objective", "content"],
    "optional_fields": ["quality_criteria_addressed", "source_references"],
    "field_requirements": {
        "resource_type": "Must exactly match TaskPacket.required_output.",
        "level": "Must exactly match TaskPacket.level.",
        "objective": "Must exactly match TaskPacket.objective.",
        "content": "Must contain usable, non-empty resource content.",
        "quality_criteria_addressed": "If supplied, must be a list covering all TaskPacket quality criteria.",
        "source_references": "Required when the TaskPacket constraints explicitly require source references.",
    },
}


@dataclass(frozen=True)
class ResourceValidationResult:
    """Result of validating a produced resource against a TaskPacket."""

    validation_id: str
    status: ValidationStatus
    score: float
    critical_failure: bool
    checks: dict[str, bool]
    feedback: list[str] = field(default_factory=list)
    blocking_errors: list[str] = field(default_factory=list)


def validate_resource_output(
    task: TaskPacket,
    produced_resource: dict[str, Any],
    *,
    revision_count: int = 0,
) -> ResourceValidationResult:
    """Validate a provider-neutral resource output against a TaskPacket.

    ``revision_count`` is the number of revisions already attempted before
    this validation. A correct first output is READY. A correctable failure
    becomes REVISION_REQUIRED while the revision budget remains. If the
    resource still fails after the allowed revision, the result becomes
    REJECT_AND_REDESIGN.
    """
    checks: dict[str, bool] = {}
    feedback: list[str] = []
    blocking_errors: list[str] = []

    checks["resource_present"] = bool(produced_resource)
    if not checks["resource_present"]:
        blocking_errors.append("Produced resource is missing or empty.")

    resource_type = str(produced_resource.get("resource_type", "")).strip()
    level = str(produced_resource.get("level", "")).strip().upper()
    objective = str(produced_resource.get("objective", "")).strip()
    content = produced_resource.get("content")

    checks["resource_type"] = resource_type == task.required_output.strip()
    if not checks["resource_type"]:
        blocking_errors.append(
            f"resource_type mismatch: expected '{task.required_output}', got '{resource_type or 'missing'}'."
        )

    checks["level_alignment"] = level == task.level
    if not checks["level_alignment"]:
        blocking_errors.append(
            f"Level mismatch: expected '{task.level}', got '{level or 'missing'}'."
        )

    checks["objective_alignment"] = objective == task.objective.strip()
    if not checks["objective_alignment"]:
        feedback.append("The produced resource does not declare the exact task objective; revise the declaration or resource alignment.")

    checks["content_present"] = _has_usable_content(content)
    if not checks["content_present"]:
        blocking_errors.append("Produced resource contains no usable content.")

    checks["quality_criteria_acknowledged"] = _criteria_are_addressed(task, produced_resource)
    if not checks["quality_criteria_acknowledged"]:
        feedback.append("The output does not provide enough evidence that the requested quality criteria were addressed.")

    checks["source_requirements"] = _sources_are_acceptable(task, produced_resource)
    if not checks["source_requirements"]:
        blocking_errors.append("Required source references are missing or unacceptable.")

    if blocking_errors:
        status: ValidationStatus = "REJECT"
        critical_failure = True
    elif not all(checks.values()):
        if revision_count >= MAX_RESOURCE_REVISIONS:
            status = "REJECT_AND_REDESIGN"
            feedback.append("The resource still fails validation after the allowed revision. Redesign the production approach before producing another version.")
        else:
            status = "REVISION_REQUIRED"
        critical_failure = False
    else:
        status = "READY"
        critical_failure = False

    passed = sum(1 for value in checks.values() if value)
    score = round((passed / len(checks)) * 100, 2) if checks else 0.0

    return ResourceValidationResult(
        validation_id=f"resource-qc-{uuid4().hex[:12]}",
        status=status,
        score=score,
        critical_failure=critical_failure,
        checks=checks,
        feedback=feedback,
        blocking_errors=blocking_errors,
    )


def _has_usable_content(content: Any) -> bool:
    """Return True when the output contains non-empty resource content."""
    if isinstance(content, str):
        return bool(content.strip())
    if isinstance(content, (list, tuple)):
        return bool(content) and all(str(item).strip() for item in content)
    if isinstance(content, dict):
        return bool(content) and any(str(value).strip() for value in content.values())
    return content is not None


def _criteria_are_addressed(task: TaskPacket, produced_resource: dict[str, Any]) -> bool:
    """Check optional producer evidence without pretending it is semantic QC."""
    evidence = produced_resource.get("quality_criteria_addressed")
    if evidence is None:
        return True
    if not isinstance(evidence, list):
        return False
    requested = {criterion.strip() for criterion in task.quality_criteria if criterion.strip()}
    supplied = {str(item).strip() for item in evidence if str(item).strip()}
    return requested.issubset(supplied)


def _sources_are_acceptable(task: TaskPacket, produced_resource: dict[str, Any]) -> bool:
    """Validate source references only when the TaskPacket explicitly asks for them."""
    source_constraints = [item.lower() for item in task.constraints if "source" in item.lower()]
    if not source_constraints:
        return True
    sources = produced_resource.get("source_references")
    return isinstance(sources, list) and bool(sources) and all(str(item).strip() for item in sources)
