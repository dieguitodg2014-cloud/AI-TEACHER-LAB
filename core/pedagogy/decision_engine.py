"""Pedagogical Decision Engine for the first executable vertical slice."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any
from uuid import uuid4

from core.foundation.models import ActivityPlan, Context, LevelDecision, LearningPlanDecision
from core.foundation.validation import validate_learning_plan
from core.pedagogy.lesson_trajectory import LessonTrajectory, TrajectoryPhase

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
    """Create a legacy-compatible activity plan driven by the new trajectory."""
    if context.level != level_decision.level:
        raise ValueError("Context level and LevelDecision level must match")

    duration = context.duration_minutes
    if duration < 30:
        raise ValueError("A minimum of 30 minutes is required for the MVP plan")

    trajectory = build_lesson_trajectory(context, level_decision)
    allocations = _allocate_minutes(duration)
    objective = context.objective

    # The trajectory is now the pedagogical authority. The six activity slots
    # remain temporarily stable so downstream contracts can migrate separately.
    activity_specs = (
        (
            "presentation",
            "experience",
            "teacher_to_class",
            "Build access to the target language/content through experience, noticing, and concise clarification.",
            "Identify or recognize the target language/content.",
            "MIXED",
            "UNDERSTAND",
            4,
        ),
        (
            "modeling",
            "grammar_clarification",
            "teacher_to_class",
            "Make successful performance visible through a clear model grounded in the target language/content.",
            "Notice and reproduce the model with support.",
            "MIXED",
            "UNDERSTAND",
            4,
        ),
        (
            "guided_practice",
            "controlled_production",
            "pairs",
            "Move learners from access into controlled production with structured support.",
            "Use the target language in a supported exchange.",
            "MIXED",
            "APPLY",
            3,
        ),
        (
            "communicative_practice",
            "guided_interaction",
            "pairs_or_small_groups",
            "Build meaningful interaction while learners move toward the communicative task.",
            "Complete a meaningful interaction task.",
            "SPEAKING",
            "APPLY",
            2,
        ),
        (
            "production",
            "expanded_production",
            "individual_or_pairs",
            "Increase independence and prepare learners to transfer the objective to purposeful communication.",
            "Produce language demonstrating the lesson objective.",
            "MIXED",
            "CREATE",
            1,
        ),
        (
            "assessment",
            "transfer",
            "individual",
            "Collect final evidence of transfer and objective attainment in a relevant new context.",
            "Provide an observable performance demonstrating the objective.",
            "MIXED",
            "APPLY",
            0,
        ),
    )

    sequence = []
    for stage, trajectory_phase, interaction, purpose, production, skill, cognitive_demand, scaffolding in activity_specs:
        phase = next(item for item in trajectory.phases if item.phase == _phase_name(trajectory_phase))
        language_target = objective if skill == "SPEAKING" else ""
        sequence.append(
            ActivityPlan(
                f"act-{uuid4().hex[:10]}",
                purpose,
                interaction,
                allocations[stage],
                production,
                assessment_link=f"Evidence collected from {phase.phase.lower()} toward the stated objective.",
                skill=skill,
                cognitive_demand=cognitive_demand,
                scaffolding=min(scaffolding, phase.scaffolding),
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


def _phase_name(name: str) -> str:
    """Map an activity's trajectory anchor to the executable phase literal."""
    return name.upper()


def build_lesson_trajectory(context: Context, level_decision: LevelDecision) -> LessonTrajectory:
    """Build the approved pedagogical progression before activity generation."""
    if context.level != level_decision.level:
        raise ValueError("Context level and LevelDecision level must match")

    phases = (
        TrajectoryPhase("EXPERIENCE", "P0", "I0", "LOW", 4, "Give learners meaningful access to the target language/content."),
        TrajectoryPhase("NOTICE", "P0", "I0", "LOW", 4, "Make relevant language/content features visible and understandable."),
        TrajectoryPhase("GRAMMAR_CLARIFICATION", "P0", "I0", "MEDIUM", 3, "Clarify form, meaning, or use when needed for the stated objective."),
        TrajectoryPhase("CONTROLLED_PRODUCTION", "P1", "I1", "MEDIUM", 3, "Move learners into supported, controlled production."),
        TrajectoryPhase("GUIDED_INTERACTION", "P1", "I2", "MEDIUM", 2, "Build meaningful interaction with structured support."),
        TrajectoryPhase("EXPANDED_PRODUCTION", "P2", "I3", "HIGH", 1, "Increase independence and expand purposeful production."),
        TrajectoryPhase("COMMUNICATIVE_TASK", "P2", "I3", "HIGH", 1, "Require purposeful communication around the lesson objective."),
        TrajectoryPhase("TRANSFER", "P3", "I4", "HIGH", 0, "Provide evidence that learning transfers to a new relevant context."),
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
