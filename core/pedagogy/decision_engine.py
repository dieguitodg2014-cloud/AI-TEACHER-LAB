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
    """Create a pedagogical plan from context and level boundaries."""
    if context.level != level_decision.level:
        raise ValueError("Context level and LevelDecision level must match")

    duration = context.duration_minutes
    if duration < 30:
        raise ValueError("A minimum of 30 minutes is required for the MVP plan")

    trajectory = build_lesson_trajectory(context, level_decision)
    allocations = _allocate_minutes(duration)
    objective = context.objective

    activity_specs = (
        ("experience", "Establish access to the target language/content through meaningful experience.", "teacher_to_class", "Identify or recognize the target language/content.", "MIXED", "UNDERSTAND", 4),
        ("notice", "Guide learners to notice the target language/content and its relevant features.", "teacher_to_class", "Identify and notice the target language/content with support.", "MIXED", "UNDERSTAND", 4),
        ("grammar_clarification", "Clarify form, meaning, or use only where clarification supports the stated objective.", "teacher_to_class", "State or recognize the clarified target language/content.", "MIXED", "UNDERSTAND", 3),
        ("controlled_production", "Build controlled accuracy before freer communication.", "pairs", "Use the target language in a supported exchange.", "MIXED", "APPLY", 3),
        ("guided_interaction", "Use the target language to exchange meaningful information with structured support.", "pairs_or_small_groups", "Complete a meaningful supported interaction.", "SPEAKING", "APPLY", 2),
        ("expanded_production", "Increase learner independence while maintaining the lesson objective.", "pairs_or_small_groups", "Produce language demonstrating the objective with limited support.", "MIXED", "CREATE", 1),
        ("communicative_task", "Complete a communicative task requiring purposeful use of the target language.", "individual_or_pairs", "Complete a communicative task demonstrating the objective.", "MIXED", "CREATE", 1),
        ("transfer", "Transfer the target language or skill to a new but relevant context.", "individual", "Provide observable evidence of transfer and objective attainment.", "MIXED", "CREATE", 0),
    )

    sequence = []
    for stage, purpose, interaction, production, skill, cognitive_demand, scaffolding in activity_specs:
        language_target = objective if skill == "SPEAKING" else None
        sequence.append(
            ActivityPlan(
                f"act-{uuid4().hex[:10]}",
                purpose,
                interaction,
                allocations[stage],
                production,
                assessment_link="Observable evidence collected against the lesson objective.",
                skill=skill,
                cognitive_demand=cognitive_demand,
                scaffolding=scaffolding,
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
        "experience": 0.10,
        "notice": 0.10,
        "grammar_clarification": 0.10,
        "controlled_production": 0.15,
        "guided_interaction": 0.17,
        "expanded_production": 0.16,
        "communicative_task": 0.15,
        "transfer": 0.07,
    }
    values = {stage: max(2, int(duration * weight)) for stage, weight in weights.items()}
    values["communicative_task"] += duration - sum(values.values())
    return values


def learning_plan_to_dict(decision: LearningPlanDecision) -> dict[str, Any]:
    return asdict(decision)
