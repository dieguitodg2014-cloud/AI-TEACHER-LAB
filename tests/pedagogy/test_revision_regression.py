from core.pedagogy.activity_pipeline import ActivityContractFactory
from core.pedagogy.activity_revision import ActivityRevisionEngine
from core.pedagogy.sequence_planner import PlannedPattern


def make_contract():
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


def valid_activity(c, duration=12, both=True):
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
        } if both else {"Student A": "asks and answers"},
        "student_output": "Both students speak.",
        "scaffolding_support": ("sentence_frame",),
        "instructions": "Ask and answer.",
    }


def test_engine_rejects_revision_that_introduces_new_failure():
    c = make_contract()

    def generator(contract):
        return valid_activity(contract, both=False)

    def reviser(revision_contract):
        # Fixes the one-sided speaking problem but introduces a duration error.
        return valid_activity(revision_contract.source_contract, duration=20, both=True)

    result = ActivityRevisionEngine(max_attempts=3).run(c, generator, reviser)

    assert not result.accepted
    assert result.stop_reason == "REGRESSION_DETECTED"
    assert result.attempts[-1].status == "REGRESSION_REJECTED"
    assert result.attempts[-1].regression
