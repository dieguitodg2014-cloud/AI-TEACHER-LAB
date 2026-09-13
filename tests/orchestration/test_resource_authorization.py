from core.foundation.models import ActivityPlan, Context, LearningPlanDecision, ResourceDecision
from core.orchestration.resource_authorization import authorize_resource_production


def make_context():
    return Context(
        context_id="CTX-001",
        level="A2",
        audience="English learners",
        duration_minutes=60,
        objective="Practice listening for key details.",
        constraints=["Keep language appropriate for the approved level."],
    )


def make_plan():
    return LearningPlanDecision(
        plan_id="PLAN-001",
        objective="Practice listening for key details.",
        sequence=[
            ActivityPlan(
                activity_id="ACT-001",
                purpose="Prepare learners for listening.",
                interaction="PAIR",
                minutes=10,
            )
        ],
        total_minutes=10,
        evidence_of_learning="Learner identifies key details.",
    )


def make_decision(action="CREATE"):
    return ResourceDecision(
        decision_id="RES-001",
        action=action,
        purpose="Provide listening input.",
        resource_type="audio",
    )


def test_authorization_is_created_from_pedagogical_decisions():
    result = authorize_resource_production(make_context(), make_plan(), make_decision())

    assert result.authorized is True
    assert result.authorization is not None
    assert result.authorization.task.task_type == "RESOURCE_PRODUCTION"
    assert result.authorization.task.objective == make_context().objective
    assert result.authorization.learning_plan_id == "PLAN-001"
    assert result.authorization.resource_decision_id == "RES-001"
    assert result.authorization.resource_type == "audio"


def test_non_production_resource_decision_cannot_cross_boundary():
    result = authorize_resource_production(
        make_context(), make_plan(), make_decision("NO_RESOURCE_REQUIRED")
    )

    assert result.authorized is False
    assert result.authorization is None
    assert result.errors == (
        "RESOURCE_PRODUCTION_NOT_AUTHORIZED_FOR_ACTION:NO_RESOURCE_REQUIRED",
    )


def test_objective_mismatch_blocks_authorization():
    plan = make_plan()
    mismatched = LearningPlanDecision(
        plan_id=plan.plan_id,
        objective="Practice speaking fluency.",
        sequence=plan.sequence,
        total_minutes=plan.total_minutes,
        evidence_of_learning=plan.evidence_of_learning,
    )

    result = authorize_resource_production(make_context(), mismatched, make_decision())

    assert result.authorized is False
    assert result.authorization is None
    assert result.errors == ("PEDAGOGICAL_OBJECTIVE_MISMATCH",)
