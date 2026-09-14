from core.foundation.models import TaskPacket
from core.orchestration.capability_validation import CapabilityValidationResult, NOT_VALIDATED, VALIDATED
from core.orchestration.capability_validation_registry import CapabilityValidationRegistry
from core.orchestration.provider_execution_policy import ProviderExecutionPolicy
from core.orchestration.tool_selector import ToolCandidate


class StubProvider:
    def __init__(self, tool_id):
        self.tool_id = tool_id

    def can_produce(self, task_packet):
        return True

    def produce(self, task_packet):
        return {
            "resource_type": task_packet.required_output,
            "level": task_packet.level,
            "objective": task_packet.objective,
            "content": "validated provider output",
        }


def _task():
    return TaskPacket(
        task_id="visual-validation-e2e",
        task_type="RESOURCE_PRODUCTION",
        level="A1",
        audience="children",
        objective="practice classroom vocabulary",
        required_output="presentation",
        format="slides",
        duration="10 minutes",
        constraints=(),
        quality_criteria=(),
        source_based=False,
        visual=True,
    )


def _tools():
    return [
        ToolCandidate(
            "notebooklm",
            frozenset({"resource_generation", "presentation_generation", "visual_resource_generation"}),
            quality=10,
            capability_validation=(
                ("visual_resource_generation", NOT_VALIDATED),
            ),
        ),
        ToolCandidate(
            "canva",
            frozenset({"resource_generation", "presentation_generation", "visual_resource_generation"}),
            quality=5,
        ),
    ]


def test_unvalidated_visual_capability_is_skipped_and_canva_executes():
    task = _task()
    tools = _tools()
    calls = []

    def execute(task_packet, tool, provider):
        calls.append(tool.tool_id)
        return {"status": "PRODUCED", "result": provider.produce(task_packet)}

    result = ProviderExecutionPolicy(provider_priority=("notebooklm", "canva")).execute(
        task,
        tools,
        {"notebooklm": StubProvider("notebooklm"), "canva": StubProvider("canva")},
        executor=execute,
        validation_registry=CapabilityValidationRegistry(),
    )

    assert result.status == "PRODUCED"
    assert result.tool_id == "canva"
    assert calls == ["canva"]
    assert ("notebooklm", "CAPABILITY_NOT_VALIDATED:visual_resource_generation") in result.excluded_tools
    assert tools[0].validation_status("visual_resource_generation") == NOT_VALIDATED


def test_validated_visual_capability_promotes_notebooklm_to_selected_provider():
    task = _task()
    tools = _tools()
    registry = CapabilityValidationRegistry(
        (
            CapabilityValidationResult(
                "notebooklm", "visual_resource_generation", VALIDATED, ("visual-smoke-test",)
            ),
        )
    )
    calls = []

    def execute(task_packet, tool, provider):
        calls.append(tool.tool_id)
        return {"status": "PRODUCED", "result": provider.produce(task_packet)}

    result = ProviderExecutionPolicy(provider_priority=("notebooklm", "canva")).execute(
        task,
        tools,
        {"notebooklm": StubProvider("notebooklm"), "canva": StubProvider("canva")},
        executor=execute,
        validation_registry=registry,
    )

    assert result.status == "PRODUCED"
    assert result.tool_id == "notebooklm"
    assert calls == ["notebooklm"]
    assert tools[0].validation_status("visual_resource_generation") == NOT_VALIDATED
    assert result.result["resource_type"] == task.required_output
    assert result.result["level"] == task.level
    assert result.result["objective"] == task.objective
