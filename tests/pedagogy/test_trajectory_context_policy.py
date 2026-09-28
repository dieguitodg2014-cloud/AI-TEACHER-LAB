import pytest

from core.pedagogy.pedagogical_skill_decision import PedagogicalSkillDecision
from core.pedagogy.trajectory_context_policy import TrajectoryContext


def _skill_decision(skill):
    return PedagogicalSkillDecision(
        skill=skill,
        rationale="The lesson requires this primary skill.",
    )


def test_context_requires_objective():
    with pytest.raises(ValueError, match="objective is required"):
        TrajectoryContext(
            objective="   ",
            skill_decision=_skill_decision("SPEAKING"),
            cognitive_demand="APPLY",
        )


@pytest.mark.parametrize(
    "skill",
    ["LISTENING", "SPEAKING", "READING", "WRITING", "MIXED"],
)
def test_context_accepts_explicit_skill_decision(skill):
    context = TrajectoryContext(
        objective="Students will communicate about a familiar topic.",
        skill_decision=_skill_decision(skill),
        cognitive_demand="APPLY",
    )

    assert context.skill_decision.skill == skill


@pytest.mark.parametrize(
    "demand",
    ["RECALL", "RECOGNIZE", "UNDERSTAND", "APPLY", "ANALYZE", "CREATE"],
)
def test_context_accepts_supported_cognitive_demands(demand):
    context = TrajectoryContext(
        objective="Students will communicate about a familiar topic.",
        skill_decision=_skill_decision("SPEAKING"),
        cognitive_demand=demand,
    )

    assert context.cognitive_demand == demand


def test_context_rejects_missing_skill_decision():
    with pytest.raises(ValueError, match="skill_decision is required"):
        TrajectoryContext(
            objective="Students will communicate about a familiar topic.",
            skill_decision=None,
            cognitive_demand="APPLY",
        )


def test_context_is_immutable():
    context = TrajectoryContext(
        objective="Students will communicate about a familiar topic.",
        skill_decision=_skill_decision("SPEAKING"),
        cognitive_demand="APPLY",
    )

    with pytest.raises((AttributeError, TypeError)):
        context.skill_decision = _skill_decision("LISTENING")
