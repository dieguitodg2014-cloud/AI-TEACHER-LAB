from core.context.engine import build_context
from core.pedagogy.activity_materializer import materialize_activity_plans
from core.pedagogy.decision_engine import _allocate_minutes, build_lesson_trajectory
from core.pedagogy.skill_decision import decide_primary_skill_from_context
from core.progression.level_control import decide_level


def _context(skill="SPEAKING"):
    result = build_context(
        {
            "level": "A2",
            "audience": "adult ESL learners",
            "duration_minutes": 90,
            "objective": "Students will communicate using the target language.",
            "primary_skill": skill,
        }
    )
    assert result.errors == []
    return result.context


def test_materializer_copies_canonical_demand_from_resolved_trajectory_phase():
    context = _context()
    level_decision = decide_level(context)
    trajectory = build_lesson_trajectory(
        context,
        level_decision,
        skill_decision=decide_primary_skill_from_context(context),
    )

    activities = materialize_activity_plans(
        trajectory,
        _allocate_minutes(context.duration_minutes),
        context.objective,
    )

    assert [activity.cognitive_demand for activity in activities] == [
        "UNDERSTAND",
        "UNDERSTAND",
        "APPLY",
        "APPLY",
        "CREATE",
        "APPLY",
    ]


def test_materializer_respects_interaction_level_contract():
    context = _context()
    level_decision = decide_level(context)
    trajectory = build_lesson_trajectory(
        context,
        level_decision,
        skill_decision=decide_primary_skill_from_context(context),
    )

    activities = materialize_activity_plans(
        trajectory,
        _allocate_minutes(context.duration_minutes),
        context.objective,
    )

    assert [activity.interaction for activity in activities] == [
        "teacher_to_class",
        "teacher_to_class",
        "pairs",
        "pairs_or_small_groups",
        "individual_or_pairs",
        "individual",
    ]


def test_materializer_copies_explicit_primary_skill_to_all_activity_slots():
    context = _context("LISTENING")
    level_decision = decide_level(context)
    trajectory = build_lesson_trajectory(
        context,
        level_decision,
        skill_decision=decide_primary_skill_from_context(context),
    )

    activities = materialize_activity_plans(
        trajectory,
        _allocate_minutes(context.duration_minutes),
        context.objective,
    )

    assert all(activity.skill == "LISTENING" for activity in activities)
