"""Decision boundary for selecting the primary pedagogical skill.

This module deliberately accepts an explicit skill signal. It does not infer
skill from free-form objectives or other uncontrolled text.
"""

from __future__ import annotations

from core.pedagogy.activity_contract import Skill
from core.pedagogy.pedagogical_skill_decision import PedagogicalSkillDecision


def decide_primary_skill(
    skill: Skill,
    *,
    rationale: str,
) -> PedagogicalSkillDecision:
    """Create an explicit primary-skill decision for pedagogical policy."""
    return PedagogicalSkillDecision(
        skill=skill,
        rationale=rationale,
    )
