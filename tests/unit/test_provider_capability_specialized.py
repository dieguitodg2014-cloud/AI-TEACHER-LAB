from core.foundation.models import TaskPacket
from core.orchestration.provider_capability_contract import provider_supports_capabilities
from core.orchestration.tool_selector import ToolCandidate


def task(**kwargs):
    values = dict(
        task_id="capability-test",
        task_type="RESOURCE_PRODUCTION",
        objective="practice greetings",
        level="A1",
        required_output="presentation",
        constraints=[],
        quality_criteria=[],
    )
    values.update(kwargs)
    return TaskPacket(**values)


def test_visual_presentation_requires_both_specialized_capabilities():
    tool = ToolCandidate(
        tool_id="canva",
        capabilities={"resource_generation", "presentation_generation"},
        quality=1.0,
        reliability=1.0,
        accessibility=1.0,
        speed=1.0,
        cost=0.0,
    )
    assert provider_supports_capabilities(
        tool.capabilities,
        task(task_type="RESOURCE_PRODUCTION", visual=True).required_output,
    ) is False
