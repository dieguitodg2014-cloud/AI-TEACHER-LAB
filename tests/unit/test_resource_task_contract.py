from core.foundation.models import TaskPacket
from core.resources.task_contract import ResourceTaskContractValidator


def make_task(**overrides):
    values = {
        "task_id": "task-1",
        "task_type": "RESOURCE_PRODUCTION",
        "objective": "Practice listening for key information.",
        "level": "A2",
        "required_output": "audio",
        "constraints": [],
        "quality_criteria": ["Support the objective."],
        "audience": "adult ESL learners",
        "status": "PENDING",
    }
    values.update(overrides)
    return TaskPacket(**values)


def test_valid_resource_task_contract():
    result = ResourceTaskContractValidator().validate(make_task())
    assert result.valid
    assert not result.errors


def test_rejects_non_resource_task():
    result = ResourceTaskContractValidator().validate(make_task(task_type="LESSON_GENERATION"))
    assert not result.valid
    assert "TASK_TYPE_INVALID:LESSON_GENERATION" in result.errors


def test_rejects_missing_required_output():
    result = ResourceTaskContractValidator().validate(make_task(required_output=""))
    assert not result.valid
    assert "REQUIRED_OUTPUT_REQUIRED" in result.errors


def test_rejects_empty_quality_criterion():
    result = ResourceTaskContractValidator().validate(make_task(quality_criteria=["Support the objective.", ""]))
    assert not result.valid
    assert "QUALITY_CRITERIA_CONTAIN_EMPTY_ITEM" in result.errors


def test_warns_when_task_is_not_pending():
    result = ResourceTaskContractValidator().validate(make_task(status="RUNNING"))
    assert result.valid
    assert "TASK_STATUS_NOT_PENDING:RUNNING" in result.warnings
