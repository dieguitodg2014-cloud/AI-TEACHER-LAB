"""Deterministic validation of generated activities against an approved contract."""

from __future__ import annotations

from typing import Any

from core.pedagogy.activity_contract import ActivityGenerationContract


def _text(activity: dict[str, Any]) -> str:
    return " ".join(str(value) for value in activity.values()).casefold()


def validate_activity(
    activity: dict[str, Any],
    contract: ActivityGenerationContract,
) -> list[str]:
    """Return blocking errors; never mutate the generated activity."""
    if not isinstance(activity, dict):
        return ["INVALID_ACTIVITY"]

    errors: list[str] = []
    if activity.get("level") != contract.level:
        errors.append("LEVEL_MISMATCH")
    if activity.get("objective") != contract.objective:
        errors.append("OBJECTIVE_MISMATCH")
    if activity.get("skill") != contract.skill:
        errors.append("SKILL_MISMATCH")
    if activity.get("interaction") != contract.interaction:
        errors.append("INTERACTION_MISMATCH")
    if activity.get("cognitive_demand") != contract.cognitive_demand:
        errors.append("COGNITIVE_DEMAND_MISMATCH")
    if activity.get("scaffolding") != contract.scaffolding:
        errors.append("SCAFFOLDING_MISMATCH")
    if activity.get("duration_minutes") != contract.duration_minutes:
        errors.append("DURATION_MISMATCH")
    if not str(activity.get("evidence", "")).strip():
        errors.append("EVIDENCE_MISSING")

    if contract.skill == "SPEAKING":
        target = str(activity.get("language_target", "")).strip()
        if not target:
            errors.append("LANGUAGE_TARGET_MISSING")

    generated = _text(activity)
    for term in contract.must_include:
        if term.casefold() not in generated:
            errors.append("MUST_INCLUDE_MISSING")
            break

    for term in contract.must_not_include:
        if term.casefold() in generated:
            errors.append("MUST_NOT_INCLUDE_VIOLATION")
            break

    return errors


def activity_is_valid(
    activity: dict[str, Any],
    contract: ActivityGenerationContract,
) -> bool:
    return not validate_activity(activity, contract)
