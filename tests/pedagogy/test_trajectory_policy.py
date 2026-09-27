import pytest

from core.foundation.models import Context, LevelDecision
from core.pedagogy.decision_engine import build_lesson_trajectory
from core.pedagogy.trajectory_policy import policy_for_level


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


def _context(level: str) -> Context:
    return Context(
        context_id=f"context-{level.lower()}",
        level=level,
        audience="adult ESL learners",
        duration_minutes=90,
        objective="Students will use the target language in a meaningful context.",
        topic="Target language",
    )


@pytest.mark.parametrize(
    ("level", "production", "interaction", "demand", "start", "transfer"),
    [
        ("A0", "P1", "I1", "LOW", 4, 0),
        ("A1", "P1", "I2", "LOW", 4, 0),
        ("A2", "P2", "I2", "MEDIUM", 3, 0),
        ("B1", "P2", "I3", "MEDIUM", 2, 0),
        ("B2", "P2", "I4", "HIGH", 1, 0),
    ],
)
def test_policy_changes_trajectory_boundaries_by_level(
    level,
    production,
    interaction,
    demand,
    start,
    transfer,
):
    policy = policy_for_level(_decision(level))

    assert policy.default_production == production
    assert policy.default_interaction == interaction
    assert policy.default_demand == demand
    assert policy.starting_scaffolding == start
    assert policy.transfer_scaffolding == transfer


@pytest.mark.parametrize(
    ("level", "expected_production", "expected_interaction", "expected_demand"),
    [
        ("A0", "P1", "I1", "LOW"),
        ("A1", "P1", "I2", "LOW"),
        ("A2", "P2", "I2", "MEDIUM"),
        ("B1", "P2", "I3", "MEDIUM"),
        ("B2", "P2", "I4", "HIGH"),
    ],
)
def test_level_policy_is_applied_to_built_trajectory(
    level,
    expected_production,
    expected_interaction,
    expected_demand,
):
    trajectory = build_lesson_trajectory(_context(level), _decision(level))

    expanded = trajectory.phases[5]
    communicative = trajectory.phases[6]

    assert expanded.production_level == expected_production
    assert expanded.interaction_level == expected_interaction
    assert expanded.demand_level == expected_demand
    assert communicative.production_level == expected_production
    assert communicative.interaction_level == expected_interaction
    assert communicative.demand_level == expected_demand
    assert trajectory.phases[0].scaffolding == policy_for_level(_decision(level)).starting_scaffolding
    assert trajectory.phases[-1].scaffolding == policy_for_level(_decision(level)).transfer_scaffolding


def test_policy_rejects_unsupported_level():
    decision = _decision("C1")

    with pytest.raises(ValueError, match="No trajectory policy"):
        policy_for_level(decision)
