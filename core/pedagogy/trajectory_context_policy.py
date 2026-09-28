"""Contract for explicit pedagogical context used by trajectory policy.

This module defines the pedagogical signals that contextual trajectory
adaptation may consume. It reuses the canonical skill and cognitive-demand
vocabularies from the activity contract so the architecture has one shared
set of values.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.pedagogy.activity_contract import CognitiveDemand
from core.pedagogy.pedagogical_skill_decision import PedagogicalSkillDecision


@dataclass(frozen=True)
class TrajectoryContext:
    """Explicit pedagogical signals available to trajectory policy."""

    objective: str
    skill_decision: PedagogicalSkillDecision
    cognitive_demand: CognitiveDemand

    def __post_init__(self) -> None:
        if not self.objective.strip():
            raise ValueError("objective is required")
        if not isinstance(self.skill_decision, PedagogicalSkillDecision):
            raise ValueError("skill_decision is required")
        if self.cognitive_demand not in {
            "RECALL",
            "RECOGNIZE",
            "UNDERSTAND",
            "APPLY",
            "ANALYZE",
            "CREATE",
        }:
            raise ValueError(
                "unsupported trajectory cognitive demand: "
                f"{self.cognitive_demand}"
            )
