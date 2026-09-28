import pytest

from core.context.engine import build_context
from core.pedagogy.decision_engine import build_lesson_trajectory
from core.progression.level_control import decide_level


def _context(level, skill):
    result = build_context(
        {
            "level": level,
            "audience": "adult ESL learners",
            "duration_minutes": 90,
            "objective": "Students will communicate using the target language.",
            "primary_skill": skill,
        }
    )
    assert result.errors == []
    return result.context


@pytest.mark.parametrize(
    ("level", "skill", "expected_interaction"),
    [
        ("A0", "SPEAKING", "I1"),
        ("A2", "SPEAKING", "I2"),
    ],
)
def test_decision_engine_applies_contextual_skill_policy(
    level,
    skill,
    expected_interaction,
):
    context = _context(level, skill)
    level_decision = decide_level(context)

    trajectory = build_lesson_trajectory(context, level_decision)

    guided = next(
        phase for phase in trajectory.phases if phase.phase == "GUIDED_INTERACTION"
    )
    assert guided.interaction_level == expected_interaction
