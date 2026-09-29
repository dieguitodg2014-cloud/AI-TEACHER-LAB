import pytest

from core.context.engine import build_context
from core.pedagogy import decision_engine
from core.pedagogy.decision_engine import build_lesson_trajectory
from core.pedagogy.skill_decision import decide_primary_skill_from_context
from core.pedagogy.trajectory_policy import policy_for_level
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
    skill_decision = decide_primary_skill_from_context(context)

    trajectory = build_lesson_trajectory(
        context,
        level_decision,
        skill_decision=skill_decision,
    )

    guided = next(
        phase for phase in trajectory.phases if phase.phase == "GUIDED_INTERACTION"
    )
    assert guided.interaction_level == expected_interaction
    assert guided.cognitive_demand == "APPLY"
    assert trajectory.primary_skill == skill


def test_decision_engine_invokes_contextual_policy_for_explicit_skill(monkeypatch):
    context = _context("A2", "SPEAKING")
    level_decision = decide_level(context)
    skill_decision = decide_primary_skill_from_context(context)
    base_policy = policy_for_level(level_decision)
    calls = []

    def spy_policy_for_context(received_level_decision, received_context):
        calls.append((received_level_decision, received_context))
        return base_policy

    monkeypatch.setattr(
        decision_engine,
        "policy_for_context",
        spy_policy_for_context,
    )

    build_lesson_trajectory(
        context,
        level_decision,
        skill_decision=skill_decision,
    )

    assert len(calls) == 1
    received_level_decision, received_context = calls[0]
    assert received_level_decision == level_decision
    assert received_context.objective == context.objective
    assert received_context.skill_decision.skill == "SPEAKING"
    assert received_context.cognitive_demand == "APPLY"


def test_decision_engine_preserves_base_policy_without_explicit_skill():
    result = build_context(
        {
            "level": "A2",
            "audience": "adult ESL learners",
            "duration_minutes": 90,
            "objective": "Students will communicate using the target language.",
        }
    )
    assert result.errors == []

    context = result.context
    level_decision = decide_level(context)
    trajectory = build_lesson_trajectory(context, level_decision)
    base_policy = policy_for_level(level_decision)

    guided = next(
        phase for phase in trajectory.phases if phase.phase == "GUIDED_INTERACTION"
    )

    assert guided.interaction_level == base_policy.default_interaction
    assert guided.demand_level == base_policy.default_demand
    assert trajectory.primary_skill is None


def test_decide_learning_plan_materializes_explicit_skill_from_trajectory():
    context = _context("A2", "SPEAKING")
    level_decision = decide_level(context)

    plan = decision_engine.decide_learning_plan(context, level_decision)

    assert plan.sequence
    assert all(activity.skill == "SPEAKING" for activity in plan.sequence)


def test_decide_learning_plan_materializes_activity_values_from_trajectory():
    context = _context("A2", "SPEAKING")
    level_decision = decide_level(context)

    plan = decision_engine.decide_learning_plan(context, level_decision)

    guided = next(
        activity for activity in plan.sequence
        if activity.activity_id and activity.student_production == "Complete a meaningful interaction task."
    )

    assert guided.interaction == "pairs_or_small_groups"
    assert guided.cognitive_demand == "APPLY"
    assert guided.scaffolding == 2
