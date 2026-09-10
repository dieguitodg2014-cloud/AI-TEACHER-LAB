from core.workflow.configured_runtime import run_configured_lesson_planning


def test_required_audio_uses_human_handoff_when_no_resource_connector_exists():
    request = {
        "level": "A2",
        "audience": "adult ESL learners",
        "duration_minutes": 90,
        "objective": "Understand a short conversation and identify key information.",
        "topic": "Listening for key information",
        "constraints": ["Students need listening practice"],
    }

    result = run_configured_lesson_planning(request)

    assert result.resource_decision.action == "CREATE"
    assert result.resource_task is not None
    assert result.resource_tool is None
    assert result.resource_handoff is not None
    assert result.resource_handoff["status"] == "HUMAN_HANDOFF"
    assert result.resource_handoff["workflow"] == "NotebookLM"
    assert result.resource_handoff["task_id"] == result.resource_task.task_id
    assert result.resource_handoff["objective"] == request["objective"]
