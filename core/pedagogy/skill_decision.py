"""Decision boundary for selecting the primary pedagogical skill.

This module deliberately accepts an explicit skill signal. It does not infer
skill from free-form objectives or other uncontrolled text.
"""

from __future__ import annotations

from core.foundation.models import Context
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


def decide_primary_skill_from_context(
    context: Context,
) -> PedagogicalSkillDecision:
    """Convert the explicit Context skill into a pedagogical decision.

    Skill inference from objective text or other uncontrolled text is
    intentionally out of scope.
    """
    if context.primary_skill is None:
        raise ValueError(
            "Primary skill is required for contextual trajectory policy"
        )

    return decide_primary_skill(
        context.primary_skill,
        rationale="Primary skill explicitly supplied in lesson Context.",
    )
