from core.foundation.models import TaskPacket
from core.orchestration.capability_validation import CapabilityValidationResult, NOT_VALIDATED, VALIDATED
from core.orchestration.capability_validation_registry import CapabilityValidationRegistry
from core.orchestration.resource_orchestrator import execute_resource_production_with_fallback
from core.orchestration.resource_provider import FunctionResourceProvider
from core.orchestration.tool_selector import ToolCandidate


def make_task() -> TaskPacket:
    return TaskPacket(
        task_id="capability-validation-pipeline-1",
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


def make_tools() -> list[ToolCandidate]:
    return [
        ToolCandidate(
            tool_id="notebooklm",
            capabilities=frozenset({
                "resource_generation",
                "presentation_generation",
                "visual_resource_generation",
            }),
            quality=1.0,
            reliability=1.0,
            accessibility=0.8,
            speed=0.7,
            cost=0.0,
            capability_validation=(("visual_resource_generation", NOT_VALIDATED),),
        ),
        ToolCandidate(
            tool_id="canva",
            capabilities=frozenset({
                "resource_generation",
                "presentation_generation",
                "visual_resource_generation",
            }),
            quality=0.9,
            reliability=1.0,
            accessibility=0.85,
            speed=0.8,
            cost=0.0,
        ),
    ]


def make_resource(task: dict) -> dict:
    return {
        "resource_type": "presentation",
        "level": task["level"],
        "objective": task["objective"],
        "content": "A visual greeting presentation for the approved objective.",
        "quality_criteria_addressed": task["quality_criteria"],
    }


def test_full_pipeline_skips_unvalidated_preferred_provider_and_accepts_canva():
    task = make_task()
    calls: list[str] = []

    def notebooklm(payload):
        calls.append("notebooklm")
        raise AssertionError("unvalidated NotebookLM visual capability must be skipped")

    def canva(payload):
        calls.append("canva")
        return make_resource(payload["task"])

    result = execute_resource_production_with_fallback(
        task,
        make_tools(),
        {
            "notebooklm": FunctionResourceProvider(notebooklm),
            "canva": FunctionResourceProvider(canva),
        },
        validation_registry=CapabilityValidationRegistry(),
    )

    assert result["status"] == "ACCEPTED"
    assert result["tool_id"] == "canva"
    assert calls == ["canva"]
    assert ("notebooklm", "CAPABILITY_NOT_VALIDATED:visual_resource_generation") in result["provider_execution_trace"]["excluded_tools"]
    assert result["result"]["resource_type"] == task.required_output
    assert result["result"]["level"] == task.level
    assert result["result"]["objective"] == task.objective
    assert task.constraints == ["simple language"]


def test_full_pipeline_uses_validated_preferred_provider_without_mutating_tool_metadata():
    task = make_task()
    calls: list[str] = []
    original_tools = make_tools()
    registry = CapabilityValidationRegistry().record(
        CapabilityValidationResult(
            tool_id="notebooklm",
            capability="visual_resource_generation",
            status=VALIDATED,
            evidence=("integration-test: visual presentation generation",),
        )
    )

    def notebooklm(payload):
        calls.append("notebooklm")
        return make_resource(payload["task"])

    def canva(payload):
        calls.append("canva")
        raise AssertionError("Canva should not run when validated preferred provider is eligible")

    result = execute_resource_production_with_fallback(
        task,
        original_tools,
        {
            "notebooklm": FunctionResourceProvider(notebooklm),
            "canva": FunctionResourceProvider(canva),
        },
        validation_registry=registry,
    )

    assert result["status"] == "ACCEPTED"
    assert result["tool_id"] == "notebooklm"
    assert calls == ["notebooklm"]
    assert result["result"]["resource_type"] == task.required_output
    assert result["result"]["level"] == task.level
    assert result["result"]["objective"] == task.objective
    assert dict(original_tools[0].capability_validation)["visual_resource_generation"] == NOT_VALIDATED
