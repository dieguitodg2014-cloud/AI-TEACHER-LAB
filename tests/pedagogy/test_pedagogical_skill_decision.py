import pytest

from core.pedagogy.pedagogical_skill_decision import PedagogicalSkillDecision


@pytest.mark.parametrize(
    "skill",
    ["LISTENING", "SPEAKING", "READING", "WRITING", "MIXED"],
)
def test_accepts_supported_skills(skill):
    decision = PedagogicalSkillDecision(
        skill=skill,
        rationale="The lesson requires this primary skill.",
    )

    assert decision.skill == skill


def test_requires_rationale():
    with pytest.raises(ValueError, match="rationale is required"):
        PedagogicalSkillDecision(
            skill="SPEAKING",
            rationale="   ",
        )


def test_is_immutable():
    decision = PedagogicalSkillDecision(
        skill="SPEAKING",
        rationale="The lesson requires spoken production.",
    )

    with pytest.raises((AttributeError, TypeError)):
        decision.skill = "LISTENING"
