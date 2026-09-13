from core.foundation.models import ActivityPlan, Context, LearningPlanDecision
from core.pedagogy.accepted_activity import materialize_accepted_activity
from core.pedagogy.activity_contract import ActivityGenerationContract
from core.pedagogy.activity_pipeline import ActivityContractFactory
from core.pedagogy.activity_revision import ActivityRevisionEngine
from core.pedagogy.sequence_planner import SequencePlanner, SequenceRequest
from core.resources.decision_engine import decide_resource


def test_vertical_slice_planner_to_accepted_activity_and_resource_decision():
    sequence = SequencePlanner().plan(
        SequenceRequest(
            level="B1",
            duration_minutes=45,
            primary_skill="SPEAKING",
            interaction="PAIR",
            requires_communication=True,
            requires_assessment=True,
        )
    )

    planned = next(
        item for item in sequence.patterns
        if item.sequence_role == "COMMUNICATIVE_PRODUCTION"
    )

    contract = ActivityContractFactory().build(
        planned,
        activity_id="ACT-VERTICAL-B1",
        level="B1",
        objective_ids=("OBJ-DAILY-ROUTINES",),
        skill="SPEAKING",
        language_target=("What time do you...?",),
        vocabulary=("wake up", "go to work"),
        scaffolding=2,
        evidence_expected=("both students ask and answer",),
    )

    def valid_activity(source: ActivityGenerationContract):
        return {
            "pattern_id": source.pattern_id,
            "level": source.level,
            "interaction": source.interaction,
            "cognitive_demand": source.cognitive_demand,
            "duration_minutes": source.duration_minutes,
            "skill": source.skill,
            "language_target": source.language_target,
            "vocabulary": source.vocabulary,
            "student_roles": ("Student A", "Student B"),
            "oral_output_by_student": {
                "Student A": "asks and answers",
                "Student B": "asks and answers",
            },
            "student_output": "Both students ask and answer questions.",
            "scaffolding_support": ("sentence_frame",),
            "instructions": "Ask your partner and answer the questions.",
        }

    result = ActivityRevisionEngine(max_attempts=2).run(
        contract,
        lambda source: valid_activity(source),
    )

    accepted = materialize_accepted_activity(contract, result)

    assert sequence.uncovered_roles == ()
    assert result.acceptance is not None
    assert result.acceptance.decision == "ACCEPT"
    assert accepted is not None
    assert accepted.contract == contract

    context = Context(
        context_id="CTX-VERTICAL-B1",
        level="B1",
        audience="adult English learners",
        duration_minutes=45,
        objective="Discuss daily routines and ask follow-up questions.",
        topic="daily routines",
        group_size=2,
    )
    learning_plan = LearningPlanDecision(
        plan_id="PLAN-VERTICAL-B1",
        objective=context.objective,
        sequence=(
            ActivityPlan(
                activity_id="ACT-VERTICAL-B1",
                purpose="Communicative production",
                interaction="PAIR",
                minutes=12,
            ),
        ),
        total_minutes=12,
        evidence_of_learning="Both students ask and answer questions.",
    )

    resource_decision = decide_resource(context, learning_plan)

    assert resource_decision.action == "NO_RESOURCE_REQUIRED"
    assert resource_decision.required is False
