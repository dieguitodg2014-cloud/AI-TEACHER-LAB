"""Contract for the explicit primary skill decision used by pedagogy.

The decision is intentionally small: cognitive demand remains owned by
LevelDecision, while skill becomes an explicit pedagogical input that can be
passed to contextual trajectory policy without parsing free-form objectives.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.pedagogy.activity_contract import Skill


@dataclass(frozen=True)
class PedagogicalSkillDecision:
    """Explicit skill decision available to trajectory policy."""

    skill: Skill
    rationale: str

    def __post_init__(self) -> None:
        if self.skill not in {
            "LISTENING",
            "SPEAKING",
            "READING",
            "WRITING",
            "MIXED",
        }:
            raise ValueError(f"unsupported pedagogical skill: {self.skill}")
        if not self.rationale.strip():
            raise ValueError("rationale is required")
