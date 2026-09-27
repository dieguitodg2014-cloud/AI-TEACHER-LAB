"""Pedagogical policy for adapting lesson trajectories to learner level.

The policy changes trajectory parameters, not the approved phase vocabulary.
It keeps the trajectory structurally stable while deriving production,
interaction, demand, and scaffolding from the LevelDecision.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from core.foundation.models import LevelDecision

ProductionLevel = Literal["P0", "P1", "P2", "P3"]
InteractionLevel = Literal["I0", "I1", "I2", "I3", "I4"]
DemandLevel = Literal["LOW", "MEDIUM", "HIGH"]


@dataclass(frozen=True)
class TrajectoryPolicy:
    """Level-derived boundaries used when constructing a lesson trajectory."""

    default_production: ProductionLevel
    default_interaction: InteractionLevel
    default_demand: DemandLevel
    starting_scaffolding: int
    transfer_scaffolding: int
    autonomy: str


def policy_for_level(level_decision: LevelDecision) -> TrajectoryPolicy:
    """Translate LevelDecision into executable trajectory boundaries."""
    policies = {
        "A0": TrajectoryPolicy("P1", "I1", "LOW", 4, 1, "very_low"),
        "A1": TrajectoryPolicy("P1", "I2", "LOW", 4, 1, "limited"),
        "A2": TrajectoryPolicy("P2", "I2", "MEDIUM", 3, 0, "moderate"),
        "B1": TrajectoryPolicy("P2", "I3", "MEDIUM", 2, 0, "increasing"),
        "B2": TrajectoryPolicy("P2", "I4", "HIGH", 1, 0, "high"),
    }

    try:
        return policies[level_decision.level]
    except KeyError as exc:
        raise ValueError(
            f"No trajectory policy is defined for level {level_decision.level}"
        ) from exc
