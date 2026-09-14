from core.foundation.models import TaskPacket
from core.orchestration.provider_execution_policy import ProviderExecutionPolicy
from core.orchestration.tool_selector import ToolCandidate
from core.orchestration.canva_provider import CanvaResourceProvider
from core.orchestration.notebooklm_provider import NotebookLMResourceProvider
from core.orchestration.resource_orchestrator import execute_resource_provider


def make_task():
    return TaskPacket(
        task_id="canva-fallback-1",
        task_type="RESOURCE_PRODUCTION",
        objective="Practice greetings with visual prompts.",
        level="A1",
        required_output="presentation",
        constraints=["simple language"],
        quality_criteria=["clear visuals"],
        preferred_tool="notebooklm",
        fallback_tool="canva",
        visual=True,
    )


def tool(tool_id):
    return ToolCandidate(
        tool_id=tool_id,
        capabilities=frozenset({
            "resource_generation",
            "presentation_generation",
            "visual_resource_generation",
        }),
        quality=1.0,
        reliability=1.0,
        accessibility=1.0,
        speed=1.0,
        cost=0.0,
    )


def test_notebooklm_failure_falls_back_to_canva_without_redesigning_task():
    task = make_task()
    seen = []

    def notebooklm_executor(payload):
        seen.append(("notebooklm", payload))
        raise RuntimeError("connector unavailable")

    def canva_executor(payload):
        seen.append(("canva", payload))
        task_payload = payload["task"]
        return {
            "resource_type": "presentation",
            "level": task_payload["level"],
            "objective": task_payload["objective"],
            "content": "A visual greeting presentation.",
        }

    providers = {
        "notebooklm": NotebookLMResourceProvider(notebooklm_executor),
        "canva": CanvaResourceProvider(canva_executor),
    }

    def execute(task_packet, tool, provider):
        return execute_resource_provider(task_packet, tool, provider)

    result = ProviderExecutionPolicy().execute(
        task,
        [tool("notebooklm"), tool("canva")],
        providers,
        executor=execute,
    )

    assert result.status == "PRODUCED"
    assert result.tool_id == "canva"
    assert [name for name, _ in seen] == ["notebooklm", "canva"]
    assert seen[0][1]["task"] == seen[1][1]["task"]
    assert seen[1][1]["task"]["objective"] == task.objective
    assert seen[1][1]["task"]["level"] == task.level
    assert seen[1][1]["task"]["required_output"] == task.required_output
    assert task.constraints == ["simple language"]
