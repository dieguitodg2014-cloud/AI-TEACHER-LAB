from core.pedagogy.activity_pipeline import ActivityContractFactory, ActivityPipeline
from core.pedagogy.sequence_planner import PlannedPattern, SequencePlanner, SequenceRequest


def make_activity(contract):
    """Provider-neutral fake generator used only for deterministic pipeline tests."""
    return {
        "pattern_id": contract.pattern_id,
        "level": contract.level,
        "interaction": contract.interaction,
        "cognitive_demand": contract.cognitive_demand,
        "duration_minutes": contract.duration_minutes,
        "skill": contract.skill,
        "language_target": contract.language_target,
        "vocabulary": contract.vocabulary,
        "student_roles": (
            "Student A", "Student B"
        ) if contract.interaction == "PAIR" else ("Student",),
        "oral_output_by_student": {
            "Student A": "asks and answers",
            "Student B": "asks and answers",
        } if contract.interaction == "PAIR" and contract.skill == "SPEAKING" else {},
        "student_output": "Student produces the target language.",
        "scaffolding_support": ("sentence_frame", "visual", "word_bank"),
        "instructions": "Use the target language and complete the task.",
    }


def build_contract(planned, level, skill, interaction=None):
    if interaction is not None:
        planned = PlannedPattern(
            pattern_id=planned.pattern_id,
            sequence_role=planned.sequence_role,
            timing_minutes=planned.timing_minutes,
            interaction=interaction,
        )
    return ActivityContractFactory().build(
        planned,
        activity_id=f"ACT-{level}",
        level=level,
        objective_ids=(f"OBJ-{level}",),
        skill=skill,
        language_target=("I wake up at...",),
        vocabulary=("wake up", "go to work"),
        scaffolding=3 if level == "A0" else 2,
        evidence_expected=("student produces the target language",),
    )


def test_a0_controlled_practice_completes_full_pipeline():
    plan = SequencePlanner().plan(
        SequenceRequest(level="A0", duration_minutes=20, primary_skill="SPEAKING")
    )
    planned = next(item for item in plan.patterns if item.pattern_id == "CONTROLLED_PRACTICE")
    contract = build_contract(planned, "A0", "SPEAKING")

    result = ActivityPipeline().run(contract, make_activity)

    assert result.accepted
    assert result.validation.status == "PASS"
    assert result.contract.interaction == "INDIVIDUAL"


def test_a1_pair_guided_production_preserves_planner_interaction():
    plan = SequencePlanner().plan(
        SequenceRequest(
            level="A1",
            duration_minutes=30,
            primary_skill="SPEAKING",
            interaction="PAIR",
        )
    )
    planned = next(item for item in plan.patterns if item.pattern_id == "GUIDED_PRODUCTION")
    contract = build_contract(planned, "A1", "SPEAKING")

    result = ActivityPipeline().run(contract, make_activity)

    assert result.accepted
    assert result.contract.interaction == "PAIR"
    assert result.validation.status == "PASS"


def test_b1_interview_is_rejected_when_generator_becomes_one_sided():
    planned = PlannedPattern(
        pattern_id="INTERVIEW",
        sequence_role="COMMUNICATIVE_PRODUCTION",
        timing_minutes=12,
        interaction="PAIR",
    )
    contract = build_contract(planned, "B1", "SPEAKING")

    def bad_generator(contract):
        activity = make_activity(contract)
        activity["oral_output_by_student"] = {"Student A": "asks and answers"}
        return activity

    result = ActivityPipeline().run(contract, bad_generator)

    assert not result.accepted
    assert result.validation.status == "REJECT"
    assert result.revision_contract is not None
    assert any("two learners" in failure for failure in result.revision_contract.failures)
