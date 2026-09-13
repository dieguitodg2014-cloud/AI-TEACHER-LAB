from core.pedagogy.activity_acceptance import ActivityAcceptanceGate
from core.pedagogy.activity_pipeline import ActivityContractFactory
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


def valid_activity(c):
    return {
        "pattern_id": c.pattern_id,
        "level": c.level,
        "interaction": c.interaction,
        "cognitive_demand": c.cognitive_demand,
        "duration_minutes": c.duration_minutes,
        "skill": c.skill,
        "language_target": c.language_target,
        "vocabulary": c.vocabulary,
        "student_roles": ("Student A", "Student B"),
        "oral_output_by_student": {"Student A": "asks and answers", "Student B": "asks and answers"},
        "student_output": "Both students speak.",
        "scaffolding_support": ("sentence_frame",),
        "instructions": "Ask and answer.",
    }


def test_gate_accepts_valid_activity():
    c = contract()
    result = ActivityAcceptanceGate().evaluate(c, valid_activity(c))
    assert result.decision == "ACCEPT"
    assert not result.blocking


def test_gate_requests_revision_when_activity_fails_before_limit():
    c = contract()
    activity = valid_activity(c)
    activity["oral_output_by_student"] = {"Student A": "asks and answers"}
    result = ActivityAcceptanceGate().evaluate(c, activity, attempts=1, max_attempts=3)
    assert result.decision == "REVISION_REQUIRED"


def test_gate_hands_off_after_max_attempts():
    c = contract()
    activity = valid_activity(c)
    activity["oral_output_by_student"] = {"Student A": "asks and answers"}
    result = ActivityAcceptanceGate().evaluate(c, activity, attempts=3, max_attempts=3)
    assert result.decision == "HUMAN_HANDOFF"


def test_gate_rejects_regression():
    c = contract()
    activity = valid_activity(c)
    from core.pedagogy.regression_guard import RegressionResult
    regression = RegressionResult(True, ("new failure",), (), ("old failure", "new failure"))
    result = ActivityAcceptanceGate().evaluate(c, activity, regression=regression)
    assert result.decision == "REJECT_AND_REDESIGN"
