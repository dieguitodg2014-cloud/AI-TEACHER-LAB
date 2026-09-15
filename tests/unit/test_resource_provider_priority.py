from core.foundation.models import TaskPacket
from core.orchestration.resource_tool_router import select_resource_provider
from core.orchestration.tool_selector import ToolCandidate
from tools.registry.config_loader import resource_provider_priority


def make_task(**overrides):
    values = dict(
        task_id="task-provider-priority",
        task_type="RESOURCE_PRODUCTION",
        objective="Students identify the main idea in a short listening text.",
        level="A2",
        required_output="audio",
        constraints=[],
        quality_criteria=["objective_alignment"],
        lesson_id="lesson-1",
        audience="adult ESL learners",
        source_based=True,
    )
    values.update(overrides)
    return TaskPacket(**values)


def make_tool(tool_id, *, quality):
    return ToolCandidate(
        tool_id=tool_id,
        capabilities=frozenset({
            "resource_generation",
            "source_based_resource_generation",
            "audio_generation",
        }),
        quality=quality,
        reliability=1.0,
        accessibility=1.0,
        speed=1.0,
        cost=0.0,
    )


def test_configured_specialized_provider_priority_is_exposed():
    policy = {
        "provider_policy": {
            "resource_provider_priority": ["notebooklm", "canva"]
        }
    }
    assert resource_provider_priority(policy) == ("notebooklm", "canva")


def test_resource_router_uses_configured_specialized_priority():
    task = make_task()
    notebooklm = make_tool("notebooklm", quality=0.5)
    other = make_tool("other", quality=1.0)

    selected = select_resource_provider(task, [other, notebooklm])

    assert selected.tool_id == "notebooklm"


def test_explicit_task_hint_still_overrides_provider_priority_when_eligible():
    task = make_task(preferred_tool="other")
    notebooklm = make_tool("notebooklm", quality=0.5)
    other = make_tool("other", quality=1.0)

    selected = select_resource_provider(task, [notebooklm, other])

    assert selected.tool_id == "other"


def test_provider_priority_cannot_override_capabilities():
    task = make_task()
    incompatible_notebooklm = ToolCandidate(
        tool_id="notebooklm",
        capabilities=frozenset({"visual_resource_generation"}),
        quality=10.0,
    )
    audio_provider = make_tool("audio-provider", quality=0.5)

    selected = select_resource_provider(task, [incompatible_notebooklm, audio_provider])

    assert selected.tool_id == "audio-provider"
