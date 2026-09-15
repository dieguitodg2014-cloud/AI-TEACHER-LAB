from core.foundation.models import TaskPacket
from core.orchestration.resource_tool_router import select_resource_provider
from core.orchestration.tool_selector import ToolCandidate


def task(output, *, source_based=False, visual=False, preferred_tool="", fallback_tool=""):
    return TaskPacket(
        task_id="TASK-ROUTE-001",
        task_type="RESOURCE_PRODUCTION",
        objective="Support the approved learning objective.",
        level="A2",
        required_output=output,
        constraints=[],
        quality_criteria=["Match the approved task."],
        audience="English learners",
        source_based=source_based,
        visual=visual,
        preferred_tool=preferred_tool,
        fallback_tool=fallback_tool,
    )


def test_audio_source_task_routes_only_to_capable_provider():
    notebooklm = ToolCandidate(
        tool_id="notebooklm",
        capabilities=frozenset({
            "resource_generation",
            "audio_generation",
            "source_based_resource_generation",
        }),
        quality=0.95, reliability=0.9, accessibility=0.8, speed=0.7, cost=0.0,
    )
    canva = ToolCandidate(
        tool_id="canva",
        capabilities=frozenset({"resource_generation", "visual_resource_generation"}),
        quality=0.9, reliability=0.9, accessibility=0.85, speed=0.8, cost=0.0,
    )

    selected = select_resource_provider(
        task("audio", source_based=True),
        [canva, notebooklm],
    )

    assert selected is not None
    assert selected.tool_id == "notebooklm"


def test_visual_presentation_can_route_to_canva():
    canva = ToolCandidate(
        tool_id="canva",
        capabilities=frozenset({
            "resource_generation",
            "visual_resource_generation",
            "presentation_generation",
        }),
        quality=0.9, reliability=0.9, accessibility=0.85, speed=0.8, cost=0.0,
    )
    selected = select_resource_provider(
        task("presentation", visual=True),
        [canva],
    )
    assert selected is not None
    assert selected.tool_id == "canva"


def test_routing_returns_none_when_capability_is_missing():
    canva = ToolCandidate(
        tool_id="canva",
        capabilities=frozenset({"resource_generation", "visual_resource_generation"}),
    )
    assert select_resource_provider(task("audio"), [canva]) is None


def test_preferred_tool_cannot_override_required_capabilities():
    incompatible = ToolCandidate(
        tool_id="canva",
        capabilities=frozenset({"resource_generation", "visual_resource_generation"}),
    )
    compatible = ToolCandidate(
        tool_id="notebooklm",
        capabilities=frozenset({"resource_generation", "audio_generation"}),
    )

    selected = select_resource_provider(
        task("audio", preferred_tool="canva", fallback_tool="notebooklm"),
        [incompatible, compatible],
    )

    assert selected is not None
    assert selected.tool_id == "notebooklm"


def test_fallback_tool_cannot_override_not_validated_capability():
    not_validated = ToolCandidate(
        tool_id="notebooklm",
        capabilities=frozenset({"resource_generation", "audio_generation"}),
        capability_validation=(("audio_generation", "not_validated"),),
    )
    compatible = ToolCandidate(
        tool_id="provider-b",
        capabilities=frozenset({"resource_generation", "audio_generation"}),
    )

    selected = select_resource_provider(
        task("audio", preferred_tool="provider-b", fallback_tool="notebooklm"),
        [not_validated, compatible],
    )

    assert selected is not None
    assert selected.tool_id == "provider-b"
