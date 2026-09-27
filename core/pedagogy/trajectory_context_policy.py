"""Contract for contextual signals that may adapt a lesson trajectory.

This module defines explicit pedagogical inputs beyond CEFR level. It does not
decide trajectory parameters yet; it prevents later policy logic from parsing
free-form lesson text or silently inventing missing signals.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

TrajectorySkill = Literal[
    "LISTENING",
    "SPEAKING",
    "READING",
    "WRITING",
    "MIXED",
]

TrajectoryDemand = Literal[
    "RECALL",
    "RECOGNIZE",
    "UNDERSTAND",
    "APPLY",
    "ANALYZE",
    "CREATE",
]


@dataclass(frozen=True)
class TrajectoryContext:
    """Explicit contextual signals available to trajectory policy."""

    objective: str
    skill: TrajectorySkill
    cognitive_demand: TrajectoryDemand

    def __post_init__(self) -> None:
        if not self.objective.strip():
            raise ValueError("objective is required")
        if self.skill not in {
            "LISTENING",
            "SPEAKING",
            "READING",
            "WRITING",
            "MIXED",
        }:
            raise ValueError(f"unsupported trajectory skill: {self.skill}")
        if self.cognitive_demand not in {
            "RECALL",
            "RECOGNIZE",
            "UNDERSTAND",
            "APPLY",
            "ANALYZE",
            "CREATE",
        }:
            raise ValueError(
                f"unsupported trajectory cognitive demand: {self.cognitive_demand}"
            )
