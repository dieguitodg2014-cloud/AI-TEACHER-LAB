from core.foundation.models import TaskPacket
from core.resources.revision_engine import ResourceRevisionEngine


def make_task():
    return TaskPacket(
        task_id="TASK-REV-001",
        task_type="RESOURCE_PRODUCTION",
        objective="Practice listening for key details.",
        level="A2",
        required_output="audio",
        constraints=[],
        quality_criteria=["Support the stated learning objective."],
        audience="English learners",
    )


def valid_resource():
    return {
        "resource_type": "audio",
        "level": "A2",
        "objective": "Practice listening for key details.",
        "content": "Listen and identify three key details.",
    }


def test_engine_accepts_valid_resource_without_revision():
    result = ResourceRevisionEngine().run(make_task(), valid_resource())
    assert result.accepted is True
    assert result.status == "ACCEPTED"
    assert result.attempts == 1
    assert result.acceptance is not None
    assert result.acceptance.decision == "ACCEPT"


def test_engine_revises_then_accepts():
    bad = valid_resource()
    bad["quality_criteria_addressed"] = []
    calls = []

    def reviser(task, resource, validation):
        calls.append(validation.validation_id)
        revised = dict(resource)
        revised["quality_criteria_addressed"] = task.quality_criteria
        return revised

    result = ResourceRevisionEngine().run(make_task(), bad, reviser)
    assert result.accepted is True
    assert result.attempts == 2
    assert len(calls) == 1
    assert result.acceptance is not None
    assert result.acceptance.decision == "ACCEPT"


def test_engine_revision_cannot_change_approved_resource_type():
    bad = valid_resource()
    bad["quality_criteria_addressed"] = []

    def invalid_reviser(task, resource, validation):
        revised = dict(resource)
        revised["quality_criteria_addressed"] = task.quality_criteria
        revised["resource_type"] = "worksheet"
        return revised

    result = ResourceRevisionEngine().run(make_task(), bad, invalid_reviser)
    assert result.accepted is False
    assert result.status == "HUMAN_HANDOFF"
    assert result.acceptance is not None
    assert result.acceptance.decision == "HUMAN_HANDOFF"
    assert any("RESOURCE_REGRESSION" in reason for reason in result.acceptance.reasons)


def test_engine_revision_cannot_change_approved_level():
    bad = valid_resource()
    bad["quality_criteria_addressed"] = []

    def invalid_reviser(task, resource, validation):
        revised = dict(resource)
        revised["quality_criteria_addressed"] = task.quality_criteria
        revised["level"] = "B1"
        return revised

    result = ResourceRevisionEngine().run(make_task(), bad, invalid_reviser)
    assert result.accepted is False
    assert result.status == "HUMAN_HANDOFF"
    assert result.acceptance is not None
    assert result.acceptance.decision == "HUMAN_HANDOFF"
    assert any("RESOURCE_REGRESSION" in reason for reason in result.acceptance.reasons)


def test_engine_revision_cannot_change_approved_objective():
    bad = valid_resource()
    bad["quality_criteria_addressed"] = []

    def invalid_reviser(task, resource, validation):
        revised = dict(resource)
        revised["quality_criteria_addressed"] = task.quality_criteria
        revised["objective"] = "A different pedagogical objective."
        return revised

    result = ResourceRevisionEngine().run(make_task(), bad, invalid_reviser)
    assert result.accepted is False
    assert result.status == "HUMAN_HANDOFF"
    assert result.acceptance is not None
    assert result.acceptance.decision == "HUMAN_HANDOFF"
    assert any("RESOURCE_REGRESSION" in reason for reason in result.acceptance.reasons)


def test_engine_hands_off_after_revision_budget():
    bad = valid_resource()
    bad["quality_criteria_addressed"] = []

    def non_fixing_reviser(task, resource, validation):
        return dict(resource)

    result = ResourceRevisionEngine().run(make_task(), bad, non_fixing_reviser)
    assert result.accepted is False
    assert result.status == "HUMAN_HANDOFF"
    assert result.attempts == 2
    assert result.acceptance is not None
    assert result.acceptance.decision == "HUMAN_HANDOFF"


def test_engine_never_accepts_without_validation():
    result = ResourceRevisionEngine().run(make_task(), {})
    assert result.accepted is False
    assert result.acceptance is not None
    assert result.acceptance.decision == "HUMAN_HANDOFF"
