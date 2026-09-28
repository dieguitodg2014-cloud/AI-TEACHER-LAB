import pytest

from core.foundation.models import LevelDecision
from core.pedagogy.contextual_trajectory_policy import policy_for_context
from core.pedagogy.pedagogical_skill_decision import PedagogicalSkillDecision
from core.pedagogy.trajectory_context_policy import TrajectoryContext


def _level_decision(level):
    return LevelDecision(
        decision_id=f"test-{level}",
        level=level,
        linguistic_complexity=level,
        cognitive_demand="APPLY",
        interaction_expectation="supported interaction",
        scaffolding="moderate",
        assessment_expectation="observable performance",
    )


def _context(skill):
    return TrajectoryContext(
        objective="Students will use the target language meaningfully.",
        skill_decision=PedagogicalSkillDecision(
            skill=skill,
            rationale="The test requires this explicit primary skill.",
        ),
        cognitive_demand="APPLY",
    )


@pytest.mark.parametrize(
    ("level", "expected_interaction"),
    [
        ("A0", "I1"),
        ("A2", "I2"),
    ],
)
def test_explicit_speaking_skill_respects_level_interaction_ceiling(
    level,
    expected_interaction,
):
    policy = policy_for_context(
        _level_decision(level),
        _context("SPEAKING"),
    )

    assert policy.default_interaction == expected_interaction
