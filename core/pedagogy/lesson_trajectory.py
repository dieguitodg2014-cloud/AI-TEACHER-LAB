"""Executable contract for pedagogical lesson trajectories.

This module defines the progression model that sits between pedagogical
decision-making and activity generation. It does not generate lesson content.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

ProductionLevel = Literal["P0", "P1", "P2", "P3"]
InteractionLevel = Literal["I0", "I1", "I2", "I3", "I4"]
DemandLevel = Literal["LOW", "MEDIUM", "HIGH"]

LessonPhase = Literal[
    "EXPERIENCE",
    "NOTICE",
    "CONTROLLED_PRODUCTION",
    "GUIDED_INTERACTION",
    "EXPANDED_PRODUCTION",
    "COMMUNICATIVE_TASK",
    "GRAMMAR_CLARIFICATION",
    "TRANSFER",
]


@dataclass(frozen=True)
class TrajectoryPhase:
    """One approved pedagogical phase in a lesson trajectory."""

    phase: LessonPhase
    production_level: ProductionLevel
    interaction_level: InteractionLevel
    demand_level: DemandLevel
    scaffolding: int
    purpose: str

    def __post_init__(self) -> None:
        if not 0 <= self.scaffolding <= 4:
            raise ValueError("scaffolding must be between 0 and 4")
        if not self.purpose.strip():
            raise ValueError("purpose is required")


@dataclass(frozen=True)
class LessonTrajectory:
    """Approved progression from the learner starting point to final evidence."""

    starting_point: ProductionLevel
    target_point: ProductionLevel
    phases: tuple[TrajectoryPhase, ...]
    final_evidence: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "phases", tuple(self.phases))
        if not self.phases:
            raise ValueError("at least one trajectory phase is required")
        if not self.final_evidence.strip():
            raise ValueError("final_evidence is required")
        if self.phases[0].production_level != self.starting_point:
            raise ValueError("first phase must match starting_point")
        if self.phases[-1].production_level != self.target_point:
            raise ValueError("last phase must match target_point")
