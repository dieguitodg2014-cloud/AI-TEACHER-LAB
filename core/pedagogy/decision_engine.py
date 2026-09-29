"""Pedagogical Decision Engine for the first executable vertical slice."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any
from uuid import uuid4

from core.foundation.models import ActivityPlan, Context, LevelDecision, LearningPlanDecision
from core.foundation.validation import validate_learning_plan
from core.pedagogy.contextual_trajectory_policy import policy_for_context
from core.pedagogy.activity_materializer import materialize_activity_plans
from core.pedagogy.lesson_trajectory import LessonTrajectory, TrajectoryPhase
from core.pedagogy.skill_decision import decide_primary_skill_from_context
from core.pedagogy.trajectory_context_policy import TrajectoryContext
from core.pedagogy.trajectory_policy import policy_for_level

STAGES = (
    "experience",
    "notice",
    "grammar_clarification",
    "controlled_production",
    "guided_interaction",
    "expanded_production",
    "communicative_task",
    "transfer",
)


def decide_learning_plan(context: Context, level_decision: LevelDecision) -> LearningPlanDecision:
    """Create a legacy-compatible activity plan driven by the full trajectory."""
    if context.level != level_decision.level:
        raise ValueError("Context level and LevelDecision level must match")

    duration = context.duration_minutes
    if duration < 30:
        raise ValueError("A minimum of 30 minutes is required for the MVP plan")

    skill_decision = None
    if context.primary_skill is not None:
        skill_decision = decide_primary_skill_from_context(context)

    trajectory = build_lesson_trajectory(
        context,
        level_decision,
        skill_decision=skill_decision,
    )
    allocations = _allocate_minutes(duration)
    objective = context.objective

    sequence = materialize_activity_plans(
        trajectory,
        allocations,
        objective,
    )

    decision = LearningPlanDecision(
        plan_id=f"plan-{uuid4().hex[:12]}",
        objective=objective,
        sequence=sequence,
        total_minutes=sum(activity.minutes for activity in sequence),
        evidence_of_learning=trajectory.final_evidence,
        resource_need="NO_RESOURCE_REQUIRED",
    )
    errors = validate_learning_plan(decision, duration)
    if errors:
        raise ValueError("Invalid learning plan: " + "; ".join(errors))
    return decision


def _resolve_trajectory_phases(
    trajectory: LessonTrajectory,
    phase_names: tuple[str, ...],
) -> tuple[TrajectoryPhase, ...]:
    """Resolve one or more explicit trajectory phases for an activity slot."""
    phases_by_name = {phase.phase: phase for phase in trajectory.phases}
    resolved = tuple(phases_by_name[name.upper()] for name in phase_names)
    if not resolved:
        raise ValueError("At least one trajectory phase is required")
    return resolved


def build_lesson_trajectory(
    context: Context,
    level_decision: LevelDecision,
    *,
    skill_decision=None,
) -> LessonTrajectory:
    """Build the approved pedagogical progression before activity generation."""
    if context.level != level_decision.level:
        raise ValueError("Context level and LevelDecision level must match")

    policy = policy_for_level(level_decision)

    if skill_decision is not None:
        context_demand = {
            "A0": "RECOGNIZE",
            "A1": "UNDERSTAND",
            "A2": "APPLY",
            "B1": "ANALYZE",
            "B2": "CREATE",
        }[level_decision.level]
        trajectory_context = TrajectoryContext(
            objective=context.objective,
            skill_decision=skill_decision,
            cognitive_demand=context_demand,
        )
        policy = policy_for_context(level_decision, trajectory_context)

    phases = (
        TrajectoryPhase(
            "EXPERIENCE",
            "P0",
            "I0",
            "LOW",
            "RECOGNIZE",
            policy.starting_scaffolding,
            "Give learners meaningful access to the target language/content.",
        ),
        TrajectoryPhase(
            "NOTICE",
            "P0",
            "I0",
            "LOW",
            "UNDERSTAND",
            policy.starting_scaffolding,
            "Make relevant language/content features visible and understandable.",
        ),
        TrajectoryPhase(
            "GRAMMAR_CLARIFICATION",
            "P0",
            "I0",
            "MEDIUM",
            "UNDERSTAND",
            max(2, policy.starting_scaffolding - 1),
            "Clarify form, meaning, or use when needed for the stated objective.",
        ),
        TrajectoryPhase(
            "CONTROLLED_PRODUCTION",
            "P1",
            "I1",
            "MEDIUM",
            "APPLY",
            max(1, policy.starting_scaffolding - 1),
            "Move learners into supported, controlled production.",
        ),
        TrajectoryPhase(
            "GUIDED_INTERACTION",
            "P1",
            policy.default_interaction,
            policy.default_demand,
            "APPLY",
            max(1, policy.starting_scaffolding - 1),
            "Build meaningful interaction with structured support.",
        ),
        TrajectoryPhase(
            "EXPANDED_PRODUCTION",
            policy.default_production,
            policy.default_interaction,
            policy.default_demand,
            "CREATE",
            max(1, policy.transfer_scaffolding),
            "Increase independence and expand purposeful production.",
        ),
        TrajectoryPhase(
            "COMMUNICATIVE_TASK",
            policy.default_production,
            policy.default_interaction,
            policy.default_demand,
            "APPLY",
            policy.transfer_scaffolding,
            "Require purposeful communication around the lesson objective.",
        ),
        TrajectoryPhase(
            "TRANSFER",
            "P3",
            "I4",
            "HIGH",
            "APPLY",
            policy.transfer_scaffolding,
            "Provide evidence that learning transfers to a new relevant context.",
        ),
    )

    return LessonTrajectory(
        starting_point="P0",
        target_point="P3",
        phases=phases,
        final_evidence="Observable student performance demonstrating the stated objective and transferring it to a relevant new context.",
        primary_skill=context.primary_skill,
    )


def _allocate_minutes(duration: int) -> dict[str, int]:
    weights = {
        "presentation": 0.15,
        "modeling": 0.10,
        "guided_practice": 0.20,
        "communicative_practice": 0.25,
        "production": 0.20,
        "assessment": 0.10,
    }
    values = {stage: max(2, int(duration * weight)) for stage, weight in weights.items()}
    values["production"] += duration - sum(values.values())
    return values


def learning_plan_to_dict(decision: LearningPlanDecision) -> dict[str, Any]:
    return asdict(decision)
