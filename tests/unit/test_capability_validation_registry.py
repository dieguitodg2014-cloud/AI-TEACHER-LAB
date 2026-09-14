import json

from core.foundation.models import TaskPacket
from core.orchestration.provider_execution_policy import ProviderExecutionPolicy
from core.orchestration.tool_selector import ToolCandidate
from tools.registry.config_loader import load_tool_registry_config


class StubProvider:
    def can_produce(self, task_packet):
        return True

    def produce(self, task_packet):
        return {"resource_type": "presentation"}


def make_task():
    return TaskPacket(
        task_id="validation-test-1",
        task_type="RESOURCE_PRODUCTION",
        objective="Practice greetings with visual prompts.",
        level="A1",
        required_output="presentation",
        constraints=[],
        quality_criteria=["Support the objective."],
        lesson_id="lesson-1",
        audience="children",
        visual=True,
    )


def test_loader_preserves_not_validated_capability_state(tmp_path):
    config = {
        "tools": [{
            "tool_id": "notebooklm",
            "connector": "notebooklm",
            "capabilities": ["resource_generation", "presentation_generation"],
            "capability_validation": {"visual_resource_generation": "not_validated"},
        }],
        "policy": {},
    }
    path = tmp_path / "tools.json"
    path.write_text(json.dumps(config), encoding="utf-8")

    tools, _ = load_tool_registry_config(path)

    assert tools[0].validation_status("visual_resource_generation") == "not_validated"
    assert "visual_resource_generation" in tools[0].not_validated_capabilities


def test_execution_trace_distinguishes_not_validated_from_missing():
    task = make_task()
    tool = ToolCandidate(
        "notebooklm",
        frozenset({"resource_generation", "presentation_generation"}),
        capability_validation=(("visual_resource_generation", "not_validated"),),
    )
    result = ProviderExecutionPolicy().execute(
        task,
        [tool],
        {"notebooklm": StubProvider()},
    )

    assert result.status == "HUMAN_HANDOFF"
    assert result.attempts == ()
    assert result.excluded_tools == (
        ("notebooklm", "CAPABILITY_NOT_VALIDATED:visual_resource_generation"),
    )
