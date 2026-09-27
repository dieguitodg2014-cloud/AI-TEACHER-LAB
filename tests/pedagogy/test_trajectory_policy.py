import pytest

from core.foundation.models import LevelDecision
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


def test_policy_rejects_unsupported_level():
    decision = _decision("C1")

    with pytest.raises(ValueError, match="No trajectory policy"):
        policy_for_level(decision)
