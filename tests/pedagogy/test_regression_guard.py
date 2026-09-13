from core.pedagogy.activity_pipeline import ActivityContractFactory
from core.pedagogy.regression_guard import ActivityRegressionGuard
from core.pedagogy.sequence_planner import PlannedPattern


def contract():
    return ActivityContractFactory().build(
        PlannedPattern("INTERVIEW", "COMMUNICATIVE_PRODUCTION", 12, "PAIR"),
        activity_id="ACT-B1",
        level="B1",
        objective_ids=("OBJ-B1",),
        skill="SPEAKING",
        language_target=("What time do you...?",),
        vocabulary=("wake up",),
        scaffolding=2,
    )


def activity(c, *, duration=12, oral=True):
    return {
        "pattern_id": c.pattern_id,
        "level": c.level,
        "interaction": c.interaction,
        "cognitive_demand": c.cognitive_demand,
        "duration_minutes": duration,
        "skill": c.skill,
        "language_target": c.language_target,
        "vocabulary": c.vocabulary,
        "student_roles": ("Student A", "Student B"),
        "oral_output_by_student": {
            "Student A": "asks and answers",
            "Student B": "asks and answers",
        } if oral else {"Student A": "asks and answers"},
        "student_output": "Both students speak.",
        "scaffolding_support": ("sentence_frame",),
        "instructions": "Ask and answer.",
    }


def test_guard_detects_new_failure():
    c = contract()
    previous = activity(c, duration=20)
    revised = activity(c, duration=12, oral=True)
    result = ActivityRegressionGuard().compare(previous, revised, c)
    assert not result.regression


def test_guard_detects_regression_after_new_failure():
    c = contract()
    previous = activity(c, duration=12, oral=False)
    revised = activity(c, duration=20, oral=False)
    result = ActivityRegressionGuard().compare(previous, revised, c)
    assert result.regression
    assert result.introduced_failures
