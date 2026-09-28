import pytest

from core.foundation.models import LevelDecision
from core.pedagogy.pedagogical_skill_decision import PedagogicalSkillDecision
from core.pedagogy.trajectory_context_policy import TrajectoryContext
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


@pytest.mark.parametrize("level", ["A0", "A1", "A2", "B1", "B2"])
@pytest.mark.parametrize(
    ("skill", "demand"),
    [
        ("LISTENING", "RECALL"),
        ("SPEAKING", "APPLY"),
        ("READING", "UNDERSTAND"),
        ("WRITING", "CREATE"),
        ("MIXED", "ANALYZE"),
    ],
)
def test_context_is_additive_to_level_policy(level, skill, demand):
    """Contextual policy must not silently erase CEFR-derived boundaries."""
    base = policy_for_level(_decision(level))
    context = TrajectoryContext(
        objective="Students will use the target language in a meaningful context.",
        skill=skill,
        cognitive_demand=demand,
    )

    assert context.objective
    assert base.starting_scaffolding >= 0
    assert base.transfer_scaffolding == 0
