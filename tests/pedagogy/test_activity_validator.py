from core.pedagogy.activity_contract import ActivityGenerationContract
from core.pedagogy.activity_validator import ActivityValidator


def contract(level="A1", interaction="PAIR", skill="SPEAKING"):
    return ActivityGenerationContract(
        activity_id="ACT-001",
        pattern_id="INTERVIEW",
        level=level,
        objective_ids=("OBJ-001",),
        skill=skill,
        language_target=("What time do you...?",),
        vocabulary=("wake up", "go to work"),
        interaction=interaction,
        cognitive_demand="COMMUNICATIVE_PRODUCTION",
        scaffolding=3,
        duration_minutes=12,
        must_include=("Ask", "Answer"),
        evidence_expected=("both students ask and answer",),
    )


def valid_activity():
    return {
        "pattern_id": "INTERVIEW",
        "level": "A1",
        "interaction": "PAIR",
        "cognitive_demand": "COMMUNICATIVE_PRODUCTION",
        "duration_minutes": 12,
        "skill": "SPEAKING",
        "language_target": ("What time do you...?",),
        "vocabulary": ("wake up", "go to work"),
        "student_roles": ("Student A", "Student B"),
        "oral_output_by_student": {"Student A": "ask and answer", "Student B": "ask and answer"},
        "student_output": "Both students ask and answer questions.",
        "scaffolding_support": ("sentence_frame", "visual"),
        "instructions": "Ask your partner. Answer your partner.",
    }


def test_valid_activity_passes():
    result = ActivityValidator().validate(valid_activity(), contract())
    assert result.status == "PASS"
    assert not result.failures


def test_one_sided_pair_speaking_is_rejected():
    activity = valid_activity()
    activity["oral_output_by_student"] = {"Student A": "ask and answer"}
    result = ActivityValidator().validate(activity, contract())
    assert result.status == "REJECT"
    assert any("two learners" in failure for failure in result.failures)


def test_a0_without_core_scaffold_is_rejected():
    activity = valid_activity()
    activity["level"] = "A0"
    activity["scaffolding_support"] = ()
    result = ActivityValidator().validate(activity, contract(level="A0"))
    assert result.status == "REJECT"
    assert any("A0" in failure for failure in result.failures)


def test_contract_mismatch_is_rejected():
    activity = valid_activity()
    activity["duration_minutes"] = 20
    result = ActivityValidator().validate(activity, contract())
    assert result.status == "REJECT"
    assert any("duration" in failure for failure in result.failures)


def test_prohibited_content_is_rejected():
    activity = valid_activity()
    c = ActivityGenerationContract(
        activity_id="ACT-001",
        pattern_id="INTERVIEW",
        level="A1",
        objective_ids=("OBJ-001",),
        skill="SPEAKING",
        language_target=("What time do you...?",),
        vocabulary=(),
        interaction="PAIR",
        cognitive_demand="COMMUNICATIVE_PRODUCTION",
        scaffolding=3,
        duration_minutes=12,
        must_not_include=("translation",),
    )
    activity["instructions"] = "Use translation before speaking."
    result = ActivityValidator().validate(activity, c)
    assert result.status == "REJECT"
