from dataclasses import asdict

import pytest

from core.foundation.models import ActivityPlan, LearningPlanDecision


def _activity(activity_id: str = "act-1") -> ActivityPlan:
    return ActivityPlan(
        activity_id=activity_id,
        purpose="Practice the target language.",
        interaction="pairs",
        minutes=10,
        student_production="Use the target language in a short exchange.",
    )


def _plan(**overrides) -> LearningPlanDecision:
    values = {
        "plan_id": "plan-immutability",
        "objective": "Practice speaking.",
        "sequence": [_activity()],
        "total_minutes": 10,
        "evidence_of_learning": "Observable student performance.",
        "resource_need": "NO_RESOURCE_REQUIRED",
    }
    values.update(overrides)
    return LearningPlanDecision(**values)


def test_sequence_is_stored_as_tuple():
    plan = _plan()

    assert isinstance(plan.sequence, tuple)
    assert plan.sequence == (_activity(),)


def test_sequence_reassignment_is_rejected():
    plan = _plan()

    with pytest.raises(AttributeError):
        plan.sequence = (_activity("act-2"),)


def test_sequence_structural_mutation_is_rejected():
    plan = _plan()

    with pytest.raises(AttributeError):
        plan.sequence.append(_activity("act-2"))
    with pytest.raises(TypeError):
        plan.sequence[0] = _activity("act-2")


def test_constructor_defensively_copies_mutable_sequence_input():
    activities = [_activity()]
    plan = _plan(sequence=activities)

    activities.append(_activity("act-2"))

    assert len(plan.sequence) == 1
    assert plan.sequence[0].activity_id == "act-1"


def test_activity_plans_remain_immutable_inside_sequence():
    plan = _plan()

    with pytest.raises(AttributeError):
        plan.sequence[0].minutes = 20


def test_asdict_preserves_read_compatibility():
    plan = _plan()
    payload = asdict(plan)

    assert payload["sequence"] == (_activity(),)
    assert payload["sequence"][0]["activity_id"] == "act-1"
