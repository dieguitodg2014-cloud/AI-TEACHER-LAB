from core.foundation.models import TaskPacket
from core.orchestration.resource_orchestrator import select_resource_tool
from core.orchestration.tool_selector import ToolCandidate


def make_task(output):
    return TaskPacket(
        task_id="TASK-CAP-001",
        task_type="RESOURCE_PRODUCTION",
        objective="Approved objective",
        level="A2",
        required_output=output,
        constraints=[],
        quality_criteria=[],
        audience="Learners",
    )


def candidate(tool_id, capabilities):
    return ToolCandidate(
        tool_id=tool_id,
        capabilities=frozenset(capabilities),
        quality=1.0,
        reliability=1.0,
        accessibility=1.0,
        speed=1.0,
        cost=0.0,
    )


def test_orchestrator_requires_audio_capability():
    generic = candidate("generic", {"resource_generation"})
    audio = candidate("audio-provider", {"resource_generation", "audio_generation"})

    selected = select_resource_tool(make_task("audio"), [generic, audio])

    assert selected is not None
    assert selected.tool_id == "audio-provider"


def test_orchestrator_requires_presentation_capability():
    generic = candidate("generic", {"resource_generation"})
    presentation = candidate(
        "presentation-provider",
        {"resource_generation", "presentation_generation"},
    )

    selected = select_resource_tool(make_task("presentation"), [generic, presentation])

    assert selected is not None
    assert selected.tool_id == "presentation-provider"


def test_orchestrator_can_require_source_based_capability():
    generic = candidate("generic", {"resource_generation"})
    source_provider = candidate(
        "source-provider",
        {"resource_generation", "source_based_resource_generation"},
    )

    selected = select_resource_tool(
        make_task("worksheet"),
        [generic, source_provider],
        source_based=True,
    )

    assert selected is not None
    assert selected.tool_id == "source-provider"
