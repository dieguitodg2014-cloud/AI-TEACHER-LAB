"""Executable contract for a single generated ESL activity."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from core.foundation.models import Level

Skill = Literal["LISTENING", "SPEAKING", "READING", "WRITING", "MIXED"]
CognitiveDemand = Literal["RECALL", "RECOGNIZE", "UNDERSTAND", "APPLY", "ANALYZE", "CREATE"]
Interaction = Literal[
    "teacher_to_class",
    "individual",
    "pairs",
    "pairs_or_small_groups",
    "small_groups",
    "whole_class",
]


@dataclass(frozen=True)
class ActivityGenerationContract:
    """Minimum pedagogical contract a generated activity must satisfy."""

    activity_id: str
    level: Level
    objective: str
    skill: Skill
    interaction: Interaction
    cognitive_demand: CognitiveDemand
    scaffolding: int
    duration_minutes: int
    evidence: str
    language_target: str = ""
    must_include: tuple[str, ...] = ()
    must_not_include: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.activity_id.strip():
            raise ValueError("activity_id is required")
        if not self.objective.strip():
            raise ValueError("objective is required")
        if not 0 <= self.scaffolding <= 4:
            raise ValueError("scaffolding must be between 0 and 4")
        if self.duration_minutes <= 0:
            raise ValueError("duration_minutes must be positive")
        if not self.evidence.strip():
            raise ValueError("evidence is required")
        if self.skill == "SPEAKING" and not self.language_target.strip():
            raise ValueError("language_target is required for SPEAKING")
        object.__setattr__(self, "must_include", tuple(self.must_include))
        object.__setattr__(self, "must_not_include", tuple(self.must_not_include))
