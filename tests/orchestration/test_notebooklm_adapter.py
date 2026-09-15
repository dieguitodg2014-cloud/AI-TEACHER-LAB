from core.foundation.models import TaskPacket
from core.orchestration.notebooklm_adapter import NotebookLMAdapter, NotebookLMHandoff


def make_task():
    return TaskPacket(
        task_id="TASK-NLM-002",
        task_type="RESOURCE_PRODUCTION",
        objective="Practice listening for key details.",
        level="A2",
        required_output="audio",
        constraints=["Keep language appropriate for the approved level."],
        quality_criteria=["Support the stated learning objective."],
        audience="English learners",
    )


def test_notebooklm_adapter_preserves_approved_task_fields():
    handoff = NotebookLMAdapter().build_handoff(make_task())

    assert isinstance(handoff, NotebookLMHandoff)
    assert handoff.provider == "notebooklm"
    assert handoff.task_id == "TASK-NLM-002"
    assert handoff.objective == "Practice listening for key details."
    assert handoff.level == "A2"
    assert handoff.required_output == "audio"
    assert handoff.constraints == ("Keep language appropriate for the approved level.",)


def test_notebooklm_adapter_rejects_non_resource_task():
    task = TaskPacket(
        task_id="TASK-NLM-002",
        task_type="LESSON_GENERATION",
        objective="Practice listening for key details.",
        level="A2",
        required_output="audio",
        constraints=["Keep language appropriate for the approved level."],
        quality_criteria=["Support the stated learning objective."],
        audience="English learners",
    )

    adapter = NotebookLMAdapter()
    assert adapter.can_produce(task) is False

    try:
        adapter.build_handoff(task)
    except ValueError as exc:
        assert str(exc) == "NOTEBOOKLM_TASK_NOT_ELIGIBLE"
    else:
        raise AssertionError("Expected NotebookLM task eligibility failure")
