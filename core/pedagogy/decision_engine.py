"""Pedagogical Decision Engine for the first executable vertical slice."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any
from uuid import uuid4

from core.foundation.models import ActivityPlan, Context, LevelDecision, LearningPlanDecision
from core.foundation.validation import validate_learning_plan
from core.pedagogy.lesson_trajectory import LessonTrajectory, TrajectoryPhase
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

    trajectory = build_lesson_trajectory(context, level_decision)
    allocations = _allocate_minutes(duration)
    objective = context.objective

    # Six activity slots remain stable for downstream compatibility, but each
    # slot explicitly covers the relevant trajectory phases.
    activity_specs = (
        (
            "presentation",
            ("experience", "notice"),
            "teacher_to_class",
            "Build access to the target language/content through meaningful experience and noticing.",
            "Identify or recognize relevant target language/content.",
            "MIXED",
            "UNDERSTAND",
            4,
        ),
        (
            "modeling",
            ("grammar_clarification",),
            "teacher_to_class",
            "Make successful performance visible through a clear model and concise clarification grounded in the target language/content.",
            "Notice and reproduce the model with support.",
            "MIXED",
            "UNDERSTAND",
            4,
        ),
        (
            "guided_practice",
            ("controlled_production",),
            "pairs",
            "Move learners from access into controlled production with structured support.",
            "Use the target language in a supported exchange.",
            "MIXED",
            "APPLY",
            3,
        ),
        (
            "communicative_practice",
            ("guided_interaction", "communicative_task"),
            "pairs_or_small_groups",
            "Build meaningful interaction and require purposeful communication around the lesson objective.",
            "Complete a meaningful interaction task.",
            "SPEAKING",
            "APPLY",
            2,
        ),
        (
            "production",
            ("expanded_production",),
            "individual_or_pairs",
            "Increase independence and prepare learners to transfer the objective to purposeful communication.",
            "Produce language demonstrating the lesson objective.",
            "MIXED",
            "CREATE",
            1,
        ),
        (
            "assessment",
            ("transfer",),
            "individual",
            "Collect final evidence of transfer and objective attainment in a relevant new context.",
            "Provide an observable performance demonstrating the objective.",
            "MIXED",
            "APPLY",
            0,
        ),
    )

    sequence = []
    for (
        stage,
        trajectory_phases,
        interaction,
        purpose,
        production,
        skill,
        cognitive_demand,
        scaffolding,
    ) in activity_specs:
        phases = _resolve_trajectory_phases(trajectory, trajectory_phases)
        phase_names = ", ".join(phase.phase.lower() for phase in phases)
        language_target = objective if skill == "SPEAKING" else ""
        sequence.append(
            ActivityPlan(
                f"act-{uuid4().hex[:10]}",
                purpose,
                interaction,
                allocations[stage],
                production,
                assessment_link=f"Evidence collected from {phase_names} toward the stated objective.",
                skill=skill,
                cognitive_demand=cognitive_demand,
                scaffolding=min(scaffolding, phases[0].scaffolding),
                language_target=language_target,
            )
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


def build_lesson_trajectory(context: Context, level_decision: LevelDecision) -> LessonTrajectory:
    """Build the approved pedagogical progression before activity generation."""
    if context.level != level_decision.level:
        raise ValueError("Context level and LevelDecision level must match")

    policy = policy_for_level(level_decision)

    phases = (
        TrajectoryPhase("EXPERIENCE", "P0", "I0", "LOW", policy.starting_scaffolding, "Give learners meaningful access to the target language/content."),
        TrajectoryPhase("NOTICE", "P0", "I0", "LOW", policy.starting_scaffolding, "Make relevant language/content features visible and understandable."),
        TrajectoryPhase("GRAMMAR_CLARIFICATION", "P0", "I0", "MEDIUM", max(2, policy.starting_scaffolding - 1), "Clarify form, meaning, or use when needed for the stated objective."),
        TrajectoryPhase("CONTROLLED_PRODUCTION", "P1", "I1", "MEDIUM", max(1, policy.starting_scaffolding - 1), "Move learners into supported, controlled production."),
        TrajectoryPhase("GUIDED_INTERACTION", "P1", policy.default_interaction, "MEDIUM", max(1, policy.starting_scaffolding - 1), "Build meaningful interaction with structured support."),
        TrajectoryPhase("EXPANDED_PRODUCTION", policy.default_production, policy.default_interaction, policy.default_demand, max(1, policy.transfer_scaffolding), "Increase independence and expand purposeful production."),
        TrajectoryPhase("COMMUNICATIVE_TASK", policy.default_production, policy.default_interaction, policy.default_demand, policy.transfer_scaffolding, "Require purposeful communication around the lesson objective."),
        TrajectoryPhase("TRANSFER", "P3", "I4", "HIGH", policy.transfer_scaffolding, "Provide evidence that learning transfers to a new relevant context."),
    )

    return LessonTrajectory(
        starting_point="P0",
        target_point="P3",
        phases=phases,
        final_evidence="Observable student performance demonstrating the stated objective and transferring it to a relevant new context.",
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
