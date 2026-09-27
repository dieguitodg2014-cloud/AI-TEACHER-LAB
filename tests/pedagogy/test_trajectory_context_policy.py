import pytest

from core.pedagogy.trajectory_context_policy import TrajectoryContext


def test_context_requires_objective():
    with pytest.raises(ValueError, match="objective is required"):
        TrajectoryContext(
            objective="   ",
            skill="SPEAKING",
            cognitive_demand="APPLY",
        )


@pytest.mark.parametrize(
    "skill",
    ["LISTENING", "SPEAKING", "READING", "WRITING", "MIXED"],
)
def test_context_accepts_supported_skills(skill):
    context = TrajectoryContext(
        objective="Students will communicate about a familiar topic.",
        skill=skill,
        cognitive_demand="APPLY",
    )

    assert context.skill == skill


@pytest.mark.parametrize(
    "demand",
    ["RECALL", "RECOGNIZE", "UNDERSTAND", "APPLY", "ANALYZE", "CREATE"],
)
def test_context_accepts_supported_cognitive_demands(demand):
    context = TrajectoryContext(
        objective="Students will communicate about a familiar topic.",
        skill="SPEAKING",
        cognitive_demand=demand,
    )

    assert context.cognitive_demand == demand


def test_context_is_immutable():
    context = TrajectoryContext(
        objective="Students will communicate about a familiar topic.",
        skill="SPEAKING",
        cognitive_demand="APPLY",
    )

    with pytest.raises((AttributeError, TypeError)):
        context.skill = "LISTENING"
