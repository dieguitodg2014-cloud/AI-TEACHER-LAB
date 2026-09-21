"""Completeness validation for teacher-facing execution content."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


SEQUENCE_FIELDS = (
    "target_language",
    "language_bank",
    "teacher_talk",
    "ccqs",
    "examples",
    "scaffolding",
    "materials",
    "role_cards",
    "assessment_checklist",
)

MAPPING_FIELDS = (
    "common_errors",
    "worksheet",
    "answer_key",
    "exit_ticket",
)

REQUIRED_FIELDS = (
    "teacher_explanation",
    *SEQUENCE_FIELDS,
    *MAPPING_FIELDS,
)


_PLACEHOLDER_VALUES = {
    "",
    "...",
    "n/a",
    "na",
    "none",
    "tbd",
    "todo",
}


def _meaningful_text(value: Any) -> bool:
    """Return True when a value contains usable non-placeholder text."""
    if not isinstance(value, str):
        return False

    normalized = value.strip().casefold()
    if normalized in _PLACEHOLDER_VALUES:
        return False

    return bool(normalized)


def _meaningful_sequence(value: Any) -> bool:
    """Return True when a sequence contains at least one useful text item."""
    if not isinstance(value, (list, tuple)) or not value:
        return False

    return any(_meaningful_text(item) for item in value)


def _meaningful_mapping(value: Any) -> bool:
    """Return True when a mapping contains at least one useful value."""
    if not isinstance(value, Mapping) or not value:
        return False

    for item in value.values():
        if isinstance(item, str) and _meaningful_text(item):
            return True

        if isinstance(item, (list, tuple)) and _meaningful_sequence(item):
            return True

        if isinstance(item, Mapping) and _meaningful_mapping(item):
            return True

    return False


def validate_teacher_execution_completeness(
    execution: Any,
) -> list[str]:
    """Validate that teacher execution contains usable content.

    This validator is intentionally limited to completeness. It does not decide
    whether the content is pedagogically aligned; semantic alignment belongs to
    the teacher-execution semantic QC layer.
    """
    if execution is None:
        return ["TEACHER_EXECUTION_MISSING"]

    if not isinstance(execution, Mapping):
        return ["INVALID_TEACHER_EXECUTION"]

    errors: list[str] = []

    for field in REQUIRED_FIELDS:
        if field not in execution:
            errors.append(f"TEACHER_EXECUTION_INCOMPLETE:{field}")
            continue

        value = execution[field]

        if field == "teacher_explanation":
            if not _meaningful_text(value):
                errors.append(f"TEACHER_EXECUTION_INCOMPLETE:{field}")
        elif field in SEQUENCE_FIELDS:
            if not _meaningful_sequence(value):
                errors.append(f"TEACHER_EXECUTION_INCOMPLETE:{field}")
        elif field in MAPPING_FIELDS:
            if not _meaningful_mapping(value):
                errors.append(f"TEACHER_EXECUTION_INCOMPLETE:{field}")

    return errors