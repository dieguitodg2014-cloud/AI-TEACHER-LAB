from core.pedagogy.activity_pipeline import ActivityContractFactory
from core.pedagogy.activity_revision import ActivityRevisionEngine
from core.pedagogy.sequence_planner import PlannedPattern


def make_contract():
    planned = PlannedPattern(
        pattern_id="INTERVIEW",
        sequence_role="COMMUNICATIVE_PRODUCTION",
        timing_minutes=12,
        interaction="PAIR",
    )
    return ActivityContractFactory().build(
        planned,
        activity_id="ACT-B1",
        level="B1",
        objective_ids=("OBJ-B1",),
        skill="SPEAKING",
        language_target=("What time do you...?",),
        vocabulary=("wake up", "go to work"),
        scaffolding=2,
        evidence_expected=("both students ask and answer",),
    )


def valid_activity(contract):
    return {
        "pattern_id": contract.pattern_id,
        "level": contract.level,
        "interaction": contract.interaction,
        "cognitive_demand": contract.cognitive_demand,
        "duration_minutes": contract.duration_minutes,
        "skill": contract.skill,
        "language_target": contract.language_target,
        "vocabulary": contract.vocabulary,
        "student_roles": ("Student A", "Student B"),
        "oral_output_by_student": {
            "Student A": "asks and answers",
            "Student B": "asks and answers",
        },
        "student_output": "Both students speak.",
        "scaffolding_support": ("sentence_frame",),
        "instructions": "Ask and answer.",
    }


def test_revision_engine_accepts_after_one_revision():
    contract = make_contract()
    calls = {"count": 0}

    def generator(contract):
        calls["count"] += 1
        activity = valid_activity(contract)
        activity["oral_output_by_student"] = {"Student A": "asks and answers"}
        return activity

    def reviser(revision_contract):
        assert "interaction" in revision_contract.preserve
        activity = valid_activity(revision_contract.source_contract)
        return activity

    result = ActivityRevisionEngine(max_attempts=3).run(contract, generator, reviser)

    assert result.accepted
    assert result.stop_reason == "ACCEPTED"
    assert len(result.attempts) == 2
    assert calls["count"] == 1


def test_revision_engine_stops_at_max_attempts():
    contract = make_contract()

    def generator(contract):
        activity = valid_activity(contract)
        activity["oral_output_by_student"] = {"Student A": "asks and answers"}
        return activity

    def reviser(revision_contract):
        return valid_activity(revision_contract.source_contract) | {
            "oral_output_by_student": {"Student A": "asks and answers"}
        }

    result = ActivityRevisionEngine(max_attempts=2).run(contract, generator, reviser)

    assert not result.accepted
    assert result.stop_reason == "MAX_ATTEMPTS_REACHED"
    assert len(result.attempts) == 2
