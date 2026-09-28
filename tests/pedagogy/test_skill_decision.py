import pytest

from core.pedagogy.skill_decision import decide_primary_skill


@pytest.mark.parametrize(
    "skill",
    ["LISTENING", "SPEAKING", "READING", "WRITING", "MIXED"],
)
def test_decide_primary_skill_preserves_explicit_skill(skill):
    decision = decide_primary_skill(
        skill,
        rationale="The lesson explicitly requires this primary skill.",
    )

    assert decision.skill == skill
    assert decision.rationale == "The lesson explicitly requires this primary skill."


def test_decide_primary_skill_requires_rationale():
    with pytest.raises(ValueError, match="rationale is required"):
        decide_primary_skill("SPEAKING", rationale="   ")


def test_decide_primary_skill_does_not_infer_from_objective_text():
    decision = decide_primary_skill(
        "READING",
        rationale="Reading is the explicitly selected primary skill.",
    )

    assert decision.skill == "READING"
