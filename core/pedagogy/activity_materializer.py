"""Materialize activity plans from an approved lesson trajectory."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

from core.foundation.models import ActivityPlan
from core.pedagogy.lesson_trajectory import LessonTrajectory, TrajectoryPhase


@dataclass(frozen=True)
class ActivitySlot:
    stage: str
    trajectory_phases: tuple[str, ...]
    interaction: str
    purpose: str
    student_production: str
    legacy_skill: str
    legacy_scaffolding: int


ACTIVITY_SLOTS = (
    ActivitySlot(
        "presentation",
        ("experience", "notice"),
        "teacher_to_class",
        "Build access to the target language/content through meaningful experience and noticing.",
        "Identify or recognize relevant target language/content.",
        "MIXED",
        4,
    ),
    ActivitySlot(
        "modeling",
        ("grammar_clarification",),
        "teacher_to_class",
        "Make successful performance visible through a clear model and concise clarification grounded in the target language/content.",
        "Notice and reproduce the model with support.",
        "MIXED",
        4,
    ),
    ActivitySlot(
        "guided_practice",
        ("controlled_production",),
        "pairs",
        "Move learners from access into controlled production with structured support.",
        "Use the target language in a supported exchange.",
        "MIXED",
        3,
    ),
    ActivitySlot(
        "communicative_practice",
        ("guided_interaction", "communicative_task"),
        "pairs_or_small_groups",
        "Build meaningful interaction and require purposeful communication around the lesson objective.",
        "Complete a meaningful interaction task.",
        "SPEAKING",
        2,
    ),
    ActivitySlot(
        "production",
        ("expanded_production",),
        "individual_or_pairs",
        "Increase independence and prepare learners to transfer the objective to purposeful communication.",
        "Produce language demonstrating the lesson objective.",
        "MIXED",
        1,
    ),
    ActivitySlot(
        "assessment",
        ("transfer",),
        "individual",
        "Collect final evidence of transfer and objective attainment in a relevant new context.",
        "Provide an observable performance demonstrating the objective.",
        "MIXED",
        0,
    ),
)


def materialize_activity_plans(
    trajectory: LessonTrajectory,
    allocations: dict[str, int],
    objective: str,
) -> list[ActivityPlan]:
    """Materialize stable activity slots from the approved trajectory.

    Contextual skill and canonical cognitive demand come from the trajectory.
    Legacy slot metadata remains only where the trajectory contract does not
    yet model an activity-level value.
    """
    sequence: list[ActivityPlan] = []

    for slot in ACTIVITY_SLOTS:
        phases = _resolve_trajectory_phases(trajectory, slot.trajectory_phases)
        skill = trajectory.primary_skill or slot.legacy_skill
        cognitive_demand = phases[-1].cognitive_demand
        language_target = objective if skill == "SPEAKING" else ""

        sequence.append(
            ActivityPlan(
                f"act-{uuid4().hex[:10]}",
                slot.purpose,
                slot.interaction,
                allocations[slot.stage],
                slot.student_production,
                assessment_link=(
                    "Evidence collected from "
                    + ", ".join(phase.phase.lower() for phase in phases)
                    + " toward the stated objective."
                ),
                skill=skill,
                cognitive_demand=cognitive_demand,
                scaffolding=min(slot.legacy_scaffolding, phases[0].scaffolding),
                language_target=language_target,
            )
        )

    return sequence


def _resolve_trajectory_phases(
    trajectory: LessonTrajectory,
    phase_names: tuple[str, ...],
) -> tuple[TrajectoryPhase, ...]:
    """Resolve one or more explicit trajectory phases for an activity slot."""
    phases_by_name = {phase.phase: phase for phase in trajectory.phases}
    try:
        resolved = tuple(phases_by_name[name.upper()] for name in phase_names)
    except KeyError as exc:
        raise ValueError(f"Unknown trajectory phase: {exc.args[0]}") from exc
    if not resolved:
        raise ValueError("At least one trajectory phase is required")
    return resolved
