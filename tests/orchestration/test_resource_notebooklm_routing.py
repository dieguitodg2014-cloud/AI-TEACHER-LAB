from core.foundation.models import TaskPacket
from core.orchestration.resource_orchestrator import select_resource_tool
from core.orchestration.tool_selector import ToolCandidate


def make_task():
    return TaskPacket(
        task_id="TASK-NLM-001",
        task_type="RESOURCE_PRODUCTION",
        objective="Understand and respond to a short listening text.",
        level="A2",
        required_output="audio",
        constraints=[],
        quality_criteria=["Match the approved learner level and audience."],
        audience="adult English learners",
    )


def test_notebooklm_can_be_selected_for_approved_resource_task():
    task = make_task()
    tools = [
        ToolCandidate(
            tool_id="notebooklm",
            capabilities={"resource_generation"},
            quality=0.95,
            reliability=0.9,
            accessibility=0.8,
            speed=0.7,
            cost=0.0,
        )
    ]

    selected = select_resource_tool(task, tools)

    assert selected is not None
    assert selected.tool_id == "notebooklm"


def test_notebooklm_is_not_selected_when_resource_task_does_not_exist():
    tools = [
        ToolCandidate(
            tool_id="notebooklm",
            capabilities={"resource_generation"},
            quality=0.95,
            reliability=0.9,
            accessibility=0.8,
            speed=0.7,
            cost=0.0,
        )
    ]

    assert select_resource_tool(None, tools) is None
