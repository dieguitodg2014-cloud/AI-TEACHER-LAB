"""Minimal QC gate for generated lesson artifacts."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from core.generation.output_validator import validate_generated_lesson
from core.pedagogy.activity_contract import ActivityGenerationContract
from core.pedagogy.activity_validator import validate_activity
from core.quality.weighted_qc import score_weighted_qc


def _assessment_alignment_errors(
    lesson: dict[str, Any],
    assessment_decision: dict[str, Any] | None,
) -> list[str]:
    """Check that the generated lesson contains observable assessment evidence."""
    if assessment_decision is None:
        return []

    activities = lesson.get("activities")
    if not isinstance(activities, list) or not activities:
        return ["ASSESSMENT_EVIDENCE_MISSING"]

    assessment_links = [
        str(activity.get("assessment_link", "")).strip()
        for activity in activities
        if isinstance(activity, dict)
    ]
    if not any(assessment_links):
        return ["ASSESSMENT_EVIDENCE_MISSING"]

    assessment_type = str(assessment_decision.get("type", "")).upper()
    if assessment_type in {"PERFORMANCE", "ORAL", "MIXED"}:
        productions = [
            str(activity.get("student_production", "")).strip()
            for activity in activities
            if isinstance(activity, dict)
        ]
        if not any(productions):
            return ["ASSESSMENT_PRODUCTION_MISSING"]

    return []


def _approved_sequence_errors(
    lesson: dict[str, Any],
    approved_sequence: list[dict[str, Any]] | None,
) -> list[str]:
    """Verify structural fidelity when the generator provides sequence metadata.

    Minimal provider outputs may intentionally omit sequence structure. In that case,
    the QC gate does not invent a sequence mismatch. When the generator provides
    structural metadata such as stage or minutes, structural fidelity is enforced.
    """
    if approved_sequence is None:
        return []

    activities = lesson.get("activities")
    if not isinstance(activities, list) or not activities:
        return ["PLAN_SEQUENCE_MISMATCH"]

    has_sequence_metadata = any(
        isinstance(activity, dict) and any(
            field in activity for field in ("stage", "minutes", "purpose", "instructions")
        )
        for activity in activities
    )
    if not has_sequence_metadata:
        return []

    if len(activities) != len(approved_sequence):
        return ["PLAN_SEQUENCE_MISMATCH"]

    for approved, generated in zip(approved_sequence, activities):
        if not isinstance(approved, dict) or not isinstance(generated, dict):
            return ["PLAN_SEQUENCE_MISMATCH"]

        if "minutes" in generated and generated.get("minutes") != approved.get("minutes"):
            return ["PLAN_SEQUENCE_MISMATCH"]

        approved_production = str(approved.get("student_production", "")).strip()
        generated_production = str(generated.get("student_production", "")).strip()
        if approved_production and "student_production" in generated and not generated_production:
            return ["PLAN_PRODUCTION_REQUIREMENT_MISSING"]

        approved_assessment = str(approved.get("assessment_link", "")).strip()
        generated_assessment = str(generated.get("assessment_link", "")).strip()
        if approved_assessment and "assessment_link" in generated and not generated_assessment:
            return ["PLAN_ASSESSMENT_LINK_MISSING"]

    return []



def _activity_contract_errors(
    lesson: dict[str, Any],
    activity_contracts: list[Mapping[str, Any]] | tuple[Mapping[str, Any], ...] | None,
) -> list[str]:
    """Validate generated activities against the approved per-activity contracts."""
    if not activity_contracts:
        return []

    activities = lesson.get("activities")
    if not isinstance(activities, list) or len(activities) != len(activity_contracts):
        return ["ACTIVITY_CONTRACT_COUNT_MISMATCH"]

    errors: list[str] = []
    for activity, contract_data in zip(activities, activity_contracts):
        if not isinstance(contract_data, Mapping):
            errors.append("INVALID_ACTIVITY_CONTRACT")
            continue
        try:
            contract = ActivityGenerationContract(**contract_data)
        except (TypeError, ValueError):
            errors.append("INVALID_ACTIVITY_CONTRACT")
            continue
        errors.extend(validate_activity(activity, contract))
    return errors


def _teacher_execution_errors(lesson: dict[str, Any]) -> list[str]:
    """Validate teacher execution support when a provider supplies it.

    The field is optional for backward compatibility. If present, its structure is
    contract-checked before the lesson can be accepted.
    """
    execution = lesson.get("teacher_execution")
    if execution is None:
        return []
    if not isinstance(execution, Mapping):
        return ["INVALID_TEACHER_EXECUTION"]

    sequence_fields = (
        "teacher_talk", "ccqs", "examples", "scaffolding", "materials",
        "role_cards", "assessment_checklist",
    )
    mapping_fields = ("common_errors", "worksheet", "answer_key", "exit_ticket")
    if not isinstance(execution.get("teacher_explanation", ""), str):
        return ["INVALID_TEACHER_EXECUTION"]
    for field in sequence_fields:
        value = execution.get(field, [])
        if not isinstance(value, (list, tuple)) or not all(isinstance(item, str) for item in value):
            return ["INVALID_TEACHER_EXECUTION"]
    for field in mapping_fields:
        if not isinstance(execution.get(field, {}), Mapping):
            return ["INVALID_TEACHER_EXECUTION"]
    return []

def review_generated_lesson(
    lesson: dict[str, Any],
    *,
    level: str,
    objective: str,
    duration_minutes: int,
    topic: str | None = None,
    constraints: list[Any] | None = None,
    assessment_decision: dict[str, Any] | None = None,
    approved_sequence: list[dict[str, Any]] | None = None,
    activity_contracts: list[Mapping[str, Any]] | tuple[Mapping[str, Any], ...] | None = None,
    resource_decision: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Run the current MVP QC checks and return the official QCResult shape."""
    blocking_errors = validate_generated_lesson(
        lesson,
        expected_level=level,
        expected_objective=objective,
        expected_duration=duration_minutes,
        expected_topic=topic,
        constraints=constraints,
    )
    if not blocking_errors:
        blocking_errors.extend(_approved_sequence_errors(lesson, approved_sequence))
    if not blocking_errors and assessment_decision is not None:
        blocking_errors.extend(_assessment_alignment_errors(lesson, assessment_decision))
    if not blocking_errors:
        blocking_errors.extend(_activity_contract_errors(lesson, activity_contracts))
    if not blocking_errors:
        blocking_errors.extend(_teacher_execution_errors(lesson))

    level_alignment = "LEVEL_MISMATCH" not in blocking_errors
    objective_alignment = not any(
        error in blocking_errors
        for error in (
            "OBJECTIVE_MISMATCH",
            "PLAN_SEQUENCE_MISMATCH",
        )
    )
    content_alignment = not any(
        error in blocking_errors
        for error in ("CONTENT_TOPIC_MISSING", "CONTENT_FORBIDDEN_TERM")
    )
    time_realism = not any(
        error in blocking_errors
        for error in ("INVALID_DURATION", "DURATION_MISMATCH")
    )
    activity_presence = "MISSING_ACTIVITIES" not in blocking_errors

    # The remaining dimensions are not yet deeply evaluated by the MVP validator.
    # They therefore remain explicitly conservative rather than being invented.
    communicative_value = activity_presence and not any(
        error.startswith(("ACTIVITY_", "INVALID_ACTIVITY_CONTRACT", "SKILL_MISMATCH", "INTERACTION_MISMATCH", "COGNITIVE_DEMAND_MISMATCH", "SCAFFOLDING_MISMATCH", "LANGUAGE_TARGET_MISMATCH", "EVIDENCE_MISSING", "MUST_INCLUDE_MISSING", "MUST_NOT_INCLUDE_PRESENT"))
        for error in blocking_errors
    )
    linguistic_accuracy = True
    assessment_alignment = not any(
        error in blocking_errors
        for error in (
            "ASSESSMENT_EVIDENCE_MISSING",
            "ASSESSMENT_PRODUCTION_MISSING",
            "PLAN_ASSESSMENT_LINK_MISSING",
        )
    )

    checks = {
        "level_alignment": level_alignment,
        "objective_alignment": objective_alignment,
        "content_alignment": content_alignment,
        "communicative_value": communicative_value,
        "time_realism": time_realism,
        "linguistic_accuracy": linguistic_accuracy,
        "assessment_alignment": assessment_alignment,
    }

    weighted = score_weighted_qc(
        checks=checks,
        blocking_errors=blocking_errors,
        lesson=lesson,
        activity_contracts=activity_contracts,
        resource_decision=resource_decision,
    )
    critical_failure = bool(blocking_errors)

    return {
        "qc_id": "generation-qc-mvp",
        "status": "READY" if not blocking_errors else "REJECT_AND_REDESIGN",
        "score": weighted["score"],
        "critical_failure": critical_failure,
        "checks": checks,
        "weighted_qc": weighted,
        "revision_required": bool(blocking_errors),
        "feedback": list(blocking_errors),
        "blocking_errors": list(blocking_errors),
    }
