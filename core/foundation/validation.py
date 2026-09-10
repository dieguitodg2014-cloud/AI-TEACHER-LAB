"""Small deterministic validators used before AI generation or QC."""

from dataclasses import asdict

from .models import Context, LearningPlanDecision, LevelDecision

VALID_LEVELS = {"A0", "A1", "A2", "B1", "B2"}


def validate_context(context: Context) -> list[str]:
    errors: list[str] = []
    if context.level not in VALID_LEVELS:
        errors.append("Unsupported level")
    if context.duration_minutes <= 0:
        errors.append("Duration must be greater than zero")
    if not context.objective.strip():
        errors.append("Objective is required")
    if not context.audience.strip():
        errors.append("Audience is required")
    if context.group_size is not None and context.group_size <= 0:
        errors.append("Group size must be greater than zero")
    return errors


def validate_level_decision(decision: LevelDecision) -> list[str]:
    errors: list[str] = []
    if decision.level not in VALID_LEVELS:
        errors.append("Unsupported level")
    required_fields = {
        "linguistic_complexity": decision.linguistic_complexity,
        "cognitive_demand": decision.cognitive_demand,
        "interaction_expectation": decision.interaction_expectation,
        "scaffolding": decision.scaffolding,
        "assessment_expectation": decision.assessment_expectation,
    }
    errors.extend(f"{name} is required" for name, value in required_fields.items() if not value.strip())
    return errors


def validate_learning_plan(plan: LearningPlanDecision, duration_minutes: int) -> list[str]:
    errors: list[str] = []
    if not plan.sequence:
        errors.append("Learning plan requires at least one activity")
    calculated = sum(activity.minutes for activity in plan.sequence)
    if calculated != plan.total_minutes:
        errors.append("Plan total_minutes does not match activity minutes")
    if plan.total_minutes > duration_minutes:
        errors.append("Learning plan exceeds available class time")
    if not plan.objective.strip():
        errors.append("Learning plan objective is required")
    if not plan.evidence_of_learning.strip():
        errors.append("Evidence of learning is required")
    return errors


def to_dict(value: object) -> dict:
    """Convert one of the dataclass contracts to a plain dictionary."""
    return asdict(value)
