"""Deterministic validation gate for externally produced instructional resources.

The validator does not generate or rewrite resources. It checks whether a
produced resource satisfies the Resource TaskPacket that authorized its
production, including a small structural output boundary.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any, Literal
from uuid import uuid4

from core.foundation.models import TaskPacket


ValidationStatus = Literal["READY", "REVISION_REQUIRED", "REJECT", "REJECT_AND_REDESIGN"]

MAX_RESOURCE_REVISIONS = 1

RESOURCE_OUTPUT_CONTRACT: dict[str, Any] = {
    "required_fields": ["resource_type", "level", "objective", "content"],
    "optional_fields": [
        "resource_id",
        "format",
        "duration",
        "language",
        "transcript",
        "source_reference",
        "production_status",
        "quality_criteria_addressed",
        "source_references",
    ],
    "field_requirements": {
        "resource_type": "Must exactly match TaskPacket.required_output.",
        "level": "Must exactly match TaskPacket.level.",
        "objective": "Must exactly match TaskPacket.objective.",
        "content": "Must contain usable, non-empty resource content.",
        "resource_id": "If supplied, must be a non-empty string.",
        "format": "If supplied, must be a non-empty string.",
        "duration": "If supplied, must be a positive number of minutes.",
        "language": "If supplied, must be a non-empty string.",
        "transcript": "If supplied, must be a non-empty string.",
        "source_reference": "If supplied, must be a non-empty string.",
        "production_status": "If supplied, must be a supported production state.",
        "quality_criteria_addressed": "If supplied, must be a list covering all TaskPacket quality criteria.",
        "source_references": "Required when the TaskPacket constraints explicitly require source references.",
    },
}

_PRODUCTION_STATUSES = {"PRODUCED", "READY"}


def task_packet_fingerprint(task: TaskPacket) -> str:
    """Return a stable identity for the approved TaskPacket used by QC."""
    payload = asdict(task)
    payload.pop("status", None)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def resource_fingerprint(resource: dict[str, Any]) -> str:
    """Return a stable identity for the exact resource content validated by QC."""
    encoded = json.dumps(resource, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True)
class ResourceValidationResult:
    """Immutable result of validating a produced resource against a TaskPacket."""

    validation_id: str
    status: ValidationStatus
    score: float
    critical_failure: bool
    checks: tuple[tuple[str, bool], ...] = ()
    feedback: tuple[str, ...] = ()
    blocking_errors: tuple[str, ...] = ()
    task_fingerprint: str = ""
    resource_fingerprint: str = ""

    def check_passed(self, name: str) -> bool:
        """Return the result for one named check without exposing mutable state."""
        return dict(self.checks).get(name, False)


def validate_resource_output(
    task: TaskPacket,
    produced_resource: dict[str, Any],
    *,
    revision_count: int = 0,
) -> ResourceValidationResult:
    """Validate a provider-neutral resource output against a TaskPacket."""
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

    structural_checks = _validate_optional_structure(produced_resource)
    checks.update(structural_checks)
    for field_name, passed in structural_checks.items():
        if not passed:
            blocking_errors.append(f"Invalid resource output structure: {field_name}.")

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
        checks=tuple(sorted(checks.items())),
        feedback=tuple(feedback),
        blocking_errors=tuple(blocking_errors),
        task_fingerprint=task_packet_fingerprint(task),
        resource_fingerprint=resource_fingerprint(produced_resource),
    )


def _validate_optional_structure(produced_resource: dict[str, Any]) -> dict[str, bool]:
    checks: dict[str, bool] = {}
    if "resource_id" in produced_resource:
        checks["resource_id"] = _non_empty_string(produced_resource["resource_id"])
    if "format" in produced_resource:
        checks["format"] = _non_empty_string(produced_resource["format"])
    if "duration" in produced_resource:
        duration = produced_resource["duration"]
        checks["duration"] = isinstance(duration, (int, float)) and not isinstance(duration, bool) and duration > 0
    if "language" in produced_resource:
        checks["language"] = _non_empty_string(produced_resource["language"])
    if "transcript" in produced_resource:
        checks["transcript"] = _non_empty_string(produced_resource["transcript"])
    if "source_reference" in produced_resource:
        checks["source_reference"] = _non_empty_string(produced_resource["source_reference"])
    if "production_status" in produced_resource:
        checks["production_status"] = produced_resource["production_status"] in _PRODUCTION_STATUSES
    if "quality_criteria_addressed" in produced_resource:
        checks["quality_criteria_addressed"] = isinstance(produced_resource["quality_criteria_addressed"], list)
    if "source_references" in produced_resource:
        checks["source_references"] = isinstance(produced_resource["source_references"], list) and all(
            _non_empty_string(item) for item in produced_resource["source_references"]
        )
    return checks


def _criteria_are_addressed(task: TaskPacket, resource: dict[str, Any]) -> bool:
    if not task.quality_criteria:
        return True
    addressed = resource.get("quality_criteria_addressed")
    if addressed is None:
        return True
    if not isinstance(addressed, list):
        return False
    return all(criterion in addressed for criterion in task.quality_criteria)


def _sources_are_acceptable(task: TaskPacket, resource: dict[str, Any]) -> bool:
    requires_sources = any("source" in constraint.lower() for constraint in task.constraints)
    if not requires_sources:
        return True
    references = resource.get("source_references")
    return isinstance(references, list) and bool(references) and all(_non_empty_string(item) for item in references)


def _has_usable_content(content: Any) -> bool:
    if isinstance(content, str):
        return bool(content.strip())
    if isinstance(content, (list, tuple)):
        return bool(content)
    if isinstance(content, dict):
        return bool(content)
    return content is not None


def _non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())
