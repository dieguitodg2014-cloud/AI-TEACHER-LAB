import pytest

from core.context.engine import build_context
from core.pedagogy.skill_decision import decide_primary_skill_from_context


def _context(primary_skill=None):
    request = {
        "level": "A2",
        "audience": "adult ESL learners",
        "duration_minutes": 90,
        "objective": "Students will communicate using the target language.",
    }
    if primary_skill is not None:
        request["primary_skill"] = primary_skill
    return build_context(request).context


@pytest.mark.parametrize(
    "skill",
    ["LISTENING", "SPEAKING", "READING", "WRITING", "MIXED"],
)
def test_decide_primary_skill_from_context_preserves_explicit_skill(skill):
    decision = decide_primary_skill_from_context(_context(skill))

    assert decision.skill == skill
    assert decision.rationale == "Primary skill explicitly supplied in lesson Context."


def test_decide_primary_skill_from_context_requires_explicit_skill():
    with pytest.raises(
        ValueError,
        match="Primary skill is required for contextual trajectory policy",
    ):
        decide_primary_skill_from_context(_context())
