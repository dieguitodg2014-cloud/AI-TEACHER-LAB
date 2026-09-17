from core.foundation.models import TaskPacket
from core.orchestration.resource_orchestrator import resource_tool_plan
from core.orchestration.tool_selector import ToolCandidate


def _task(required_output="audio", task_id="task-1"):
    return TaskPacket(
        task_id=task_id,
        task_type="RESOURCE_PRODUCTION",
        objective="Practice listening for past experiences.",
        level="A2",
        required_output=required_output,
        constraints=[],
        quality_criteria=["Support the objective."],
        lesson_id="plan-1",
        audience="adult ESL learners",
        status="PENDING",
    )


def test_no_resource_task_does_not_select_tool():
    result = resource_tool_plan(None, [])
    assert result["status"] == "NOT_REQUIRED"
    assert result["tool_id"] is None


def test_resource_task_selects_tool_with_exact_output_capability():
    tools = [
        ToolCandidate(
            tool_id="resource-tool",
            capabilities=frozenset({"resource_generation", "resource_output:audio"}),
            quality=0.8,
            reliability=0.9,
            accessibility=1.0,
            speed=0.8,
            cost=0.0,
        )
    ]
    result = resource_tool_plan(_task(), tools)
    assert result["status"] == "READY"
    assert result["tool_id"] == "resource-tool"
    assert result["task_id"] == "task-1"


def test_generic_resource_provider_without_output_capability_requires_handoff():
    tools = [
        ToolCandidate(
            tool_id="generic-resource-tool",
            capabilities=frozenset({"resource_generation"}),
        )
    ]
    result = resource_tool_plan(_task(), tools)
    assert result["status"] == "HUMAN_HANDOFF"
    assert result["reason"] == "NO_SUITABLE_RESOURCE_TOOL"


def test_wrong_output_capability_requires_handoff():
    tools = [
        ToolCandidate(
            tool_id="video-tool",
            capabilities=frozenset({"resource_generation", "resource_output:video"}),
        )
    ]
    result = resource_tool_plan(_task("audio", "task-3"), tools)
    assert result["status"] == "HUMAN_HANDOFF"
    assert result["task_id"] == "task-3"


def test_missing_resource_capability_requires_handoff():
    result = resource_tool_plan(_task("audio", "task-4"), [])
    assert result["status"] == "HUMAN_HANDOFF"
    assert result["reason"] == "NO_SUITABLE_RESOURCE_TOOL"
