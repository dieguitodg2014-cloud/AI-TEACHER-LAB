"""Contextual adaptation layered on top of the CEFR trajectory policy.

The level policy remains authoritative for pedagogical boundaries. Contextual
signals may refine interaction and demand, but they cannot exceed the level
ceiling. Objective is retained as explicit context and is not interpreted by
string heuristics.
"""

from __future__ import annotations

from dataclasses import replace

from core.foundation.models import LevelDecision
from core.pedagogy.trajectory_context_policy import TrajectoryContext
from core.pedagogy.trajectory_policy import (
    DemandLevel,
    InteractionLevel,
    TrajectoryPolicy,
    policy_for_level,
)

_INTERACTION_ORDER: tuple[InteractionLevel, ...] = (
    "I0",
    "I1",
    "I2",
    "I3",
    "I4",
)

_DEMAND_ORDER: tuple[DemandLevel, ...] = (
    "LOW",
    "MEDIUM",
    "HIGH",
)

_LEVEL_DEMAND_CEILING: dict[str, DemandLevel] = {
    "A0": "LOW",
    "A1": "LOW",
    "A2": "MEDIUM",
    "B1": "MEDIUM",
    "B2": "HIGH",
}

_CONTEXT_DEMAND: dict[str, DemandLevel] = {
    "RECALL": "LOW",
    "RECOGNIZE": "LOW",
    "UNDERSTAND": "LOW",
    "APPLY": "MEDIUM",
    "ANALYZE": "HIGH",
    "CREATE": "HIGH",
}


def policy_for_context(
    level_decision: LevelDecision,
    context: TrajectoryContext,
) -> TrajectoryPolicy:
    """Refine the level policy using explicit skill and cognitive demand."""
    base = policy_for_level(level_decision)

    interaction = base.default_interaction
    if context.skill == "SPEAKING":
        interaction = _max_interaction(interaction, "I2")

    requested_demand = _CONTEXT_DEMAND[context.cognitive_demand]
    ceiling = _LEVEL_DEMAND_CEILING[level_decision.level]
    demand = _min_demand(
        _max_demand(base.default_demand, requested_demand),
        ceiling,
    )

    return replace(
        base,
        default_interaction=interaction,
        default_demand=demand,
    )


def _max_interaction(
    first: InteractionLevel,
    second: InteractionLevel,
) -> InteractionLevel:
    return _INTERACTION_ORDER[
        max(_INTERACTION_ORDER.index(first), _INTERACTION_ORDER.index(second))
    ]


def _max_demand(first: DemandLevel, second: DemandLevel) -> DemandLevel:
    return _DEMAND_ORDER[
        max(_DEMAND_ORDER.index(first), _DEMAND_ORDER.index(second))
    ]


def _min_demand(first: DemandLevel, second: DemandLevel) -> DemandLevel:
    return _DEMAND_ORDER[
        min(_DEMAND_ORDER.index(first), _DEMAND_ORDER.index(second))
    ]
