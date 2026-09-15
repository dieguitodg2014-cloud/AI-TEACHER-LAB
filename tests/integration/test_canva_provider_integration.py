from core.foundation.models import TaskPacket
from core.orchestration.canva_provider import CanvaResourceProvider
from core.orchestration.resource_orchestrator import execute_resource_provider
from core.orchestration.tool_selector import ToolCandidate


def make_task() -> TaskPacket:
    return TaskPacket(
        task_id="task-canva-integration",
        task_type="RESOURCE_PRODUCTION",
        objective="practice greetings",
        level="A1",
        required_output="presentation",
        constraints=["simple language"],
        quality_criteria=["age appropriate"],
        preferred_tool="canva",
        visual=True,
    )


def test_canva_executes_through_provider_boundary_with_required_capabilities():
    calls = []

    def executor(payload):
        calls.append(payload)
        return {
            "resource_type": "presentation",
            "level": "A1",
            "objective": "practice greetings",
            "content": "slides",
        }

    provider = CanvaResourceProvider(executor)
    tool = ToolCandidate(
        tool_id="canva",
        capabilities={
            "resource_generation",
            "presentation_generation",
            "visual_resource_generation",
        },
        quality=0.9,
        reliability=0.9,
        accessibility=0.85,
        speed=0.8,
        cost=0.0,
    )

    result = execute_resource_provider(make_task(), tool, provider)

    assert result["status"] == "PRODUCED"
    assert result["tool_id"] == "canva"
    assert result["result"]["content"] == "slides"
    assert calls[0]["provider"] == "canva"
    assert calls[0]["task"]["task_id"] == "task-canva-integration"
