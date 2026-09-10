from core.foundation.models import TaskPacket
from core.orchestration.resource_orchestrator import resource_tool_plan
from core.orchestration.tool_selector import ToolCandidate


def test_no_resource_task_does_not_select_tool():
    result = resource_tool_plan(None, [])
    assert result["status"] == "NOT_REQUIRED"
    assert result["tool_id"] is None


def test_resource_task_selects_capable_tool():
    task = TaskPacket(
        task_id="task-1",
        task_type="RESOURCE_PRODUCTION",
        objective="Practice listening for past experiences.",
        level="A2",
        required_output="audio",
        constraints=[],
        quality_criteria=["Support the objective."],
        lesson_id="plan-1",
        audience="adult ESL learners",
        status="PENDING",
    )
    tools = [
        ToolCandidate(
            tool_id="resource-tool",
            capabilities=frozenset({"resource_generation"}),
            quality=0.8,
            reliability=0.9,
            accessibility=1.0,
            speed=0.8,
            cost=0.0,
        )
    ]
    result = resource_tool_plan(task, tools)
    assert result["status"] == "READY"
    assert result["tool_id"] == "resource-tool"
    assert result["task_id"] == "task-1"


def test_missing_resource_capability_requires_handoff():
    task = TaskPacket(
        task_id="task-2",
        task_type="RESOURCE_PRODUCTION",
        objective="Practice listening.",
        level="A2",
        required_output="audio",
        constraints=[],
        quality_criteria=["Support the objective."],
        lesson_id="plan-2",
        audience="adult ESL learners",
        status="PENDING",
    )
    result = resource_tool_plan(task, [])
    assert result["status"] == "HUMAN_HANDOFF"
    assert result["reason"] == "NO_RESOURCE_GENERATION_TOOL"
