import pytest

from core.foundation.models import Context, LevelDecision
from core.pedagogy.contextual_trajectory_policy import policy_for_context
from core.pedagogy.trajectory_context_policy import TrajectoryContext


def _decision(level: str) -> LevelDecision:
    return LevelDecision(
        decision_id=f"test-{level.lower()}",
        level=level,
        linguistic_complexity="test",
        cognitive_demand="test",
        interaction_expectation="test",
        scaffolding="test",
        assessment_expectation="test",
        autonomy_expectation="test",
        grammar_precision="test",
        fluency_expectation="test",
        register="test",
    )


def _context(skill: str, demand: str) -> TrajectoryContext:
    return TrajectoryContext(
        objective="Students will use the target language in a meaningful context.",
        skill=skill,
        cognitive_demand=demand,
    )


@pytest.mark.parametrize(
    ("level", "demand", "expected"),
    [
        ("A0", "CREATE", "LOW"),
        ("A1", "ANALYZE", "LOW"),
        ("A2", "CREATE", "MEDIUM"),
        ("B1", "ANALYZE", "MEDIUM"),
        ("B2", "CREATE", "HIGH"),
    ],
)
def test_cognitive_demand_cannot_exceed_level_ceiling(level, demand, expected):
    policy = policy_for_context(_decision(level), _context("WRITING", demand))

    assert policy.default_demand == expected


@pytest.mark.parametrize("level", ["A0", "A1", "A2", "B1", "B2"])
def test_speaking_stays_within_level_interaction_ceiling(level):
    policy = policy_for_context(_decision(level), _context("SPEAKING", "RECALL"))

    expected = {"A0": "I1", "A1": "I2", "A2": "I2", "B1": "I3", "B2": "I4"}[level]
    assert policy.default_interaction == expected


def test_non_speaking_skill_preserves_level_interaction():
    policy = policy_for_context(_decision("A1"), _context("WRITING", "APPLY"))

    assert policy.default_interaction == "I2"


def test_context_does_not_change_production_or_scaffolding():
    base = policy_for_context(_decision("A2"), _context("READING", "CREATE"))
    assert base.default_production == "P2"
    assert base.starting_scaffolding == 3
    assert base.transfer_scaffolding == 0


def test_objective_is_not_interpreted_as_a_text_heuristic():
    context = _context("SPEAKING", "APPLY")
    assert "target language" in context.objective
