from core.foundation.models import ActivityPlan, LearningPlanDecision


def _activity() -> ActivityPlan:
    return ActivityPlan(
        activity_id="activity-immutable-001",
        purpose="Practice the target language.",
        interaction="pairs",
        minutes=10,
    )


def test_sequence_is_normalized_to_tuple():
    plan = LearningPlanDecision(
        plan_id="plan-immutable-001",
        objective="Practice everyday communication.",
        sequence=[_activity()],
        total_minutes=10,
        evidence_of_learning="Students complete a short exchange.",
    )

    assert plan.sequence == (_activity(),)
    assert isinstance(plan.sequence, tuple)


def test_sequence_cannot_be_mutated():
    plan = LearningPlanDecision(
        plan_id="plan-immutable-002",
        objective="Practice everyday communication.",
        sequence=[_activity()],
        total_minutes=10,
        evidence_of_learning="Students complete a short exchange.",
    )

    try:
        plan.sequence.append(_activity())
    except AttributeError:
        pass
    else:
        raise AssertionError("Learning plan sequence must be immutable")
