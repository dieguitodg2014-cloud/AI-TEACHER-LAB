from core.foundation.models import TaskPacket
from core.orchestration.capability_validation import CapabilityValidationResult, VALIDATED, NOT_VALIDATED
from core.orchestration.capability_validation_registry import CapabilityValidationRegistry
from core.orchestration.resource_orchestrator import execute_resource_production_with_fallback
from core.orchestration.tool_selector import ToolCandidate
from core.orchestration.notebooklm_provider import NotebookLMResourceProvider
from core.orchestration.canva_provider import CanvaResourceProvider


def make_task() -> TaskPacket:
    return TaskPacket(
        task_id="full-pipeline-capability-validation-1",
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


def test_full_pipeline_skips_unvalidated_preferred_provider_and_accepts_canva_output():
    task = make_task()
    calls = []

    def notebooklm_executor(payload):
        calls.append("notebooklm")
        raise AssertionError("unvalidated NotebookLM capability must be filtered before execution")

    def canva_executor(payload):
        calls.append("canva")
        approved = payload["task"]
        return {
            "resource_type": "presentation",
            "level": approved["level"],
            "objective": approved["objective"],
            "content": "Visual greeting presentation for A1 learners.",
            "quality_criteria_addressed": approved["quality_criteria"],
        }

    providers = {
        "notebooklm": NotebookLMResourceProvider(notebooklm_executor),
        "canva": CanvaResourceProvider(canva_executor),
    }

    result = execute_resource_production_with_fallback(
        task,
        make_tools(),
        providers,
        validation_registry=CapabilityValidationRegistry(),
    )

    assert result["status"] == "ACCEPTED"
    assert result["tool_id"] == "canva"
    assert calls == ["canva"]
    assert result["result"]["resource_type"] == task.required_output
    assert result["result"]["level"] == task.level
    assert result["result"]["objective"] == task.objective
    assert ("notebooklm", "CAPABILITY_NOT_VALIDATED:visual_resource_generation") in result["provider_execution_trace"]["excluded_tools"]
    assert task.constraints == ["simple language"]
    assert task.quality_criteria == ["clear visuals"]


def test_full_pipeline_validation_promotes_notebooklm_without_mutating_tool_configuration():
    task = make_task()
    tools = make_tools()
    calls = []

    def notebooklm_executor(payload):
        calls.append("notebooklm")
        approved = payload["task"]
        return {
            "resource_type": "presentation",
            "level": approved["level"],
            "objective": approved["objective"],
            "content": "Validated NotebookLM visual presentation.",
            "quality_criteria_addressed": approved["quality_criteria"],
        }

    def canva_executor(payload):
        calls.append("canva")
        raise AssertionError("validated preferred provider should be selected first")

    providers = {
        "notebooklm": NotebookLMResourceProvider(notebooklm_executor),
        "canva": CanvaResourceProvider(canva_executor),
    }
    registry = CapabilityValidationRegistry().record(
        CapabilityValidationResult(
            tool_id="notebooklm",
            capability="visual_resource_generation",
            status=VALIDATED,
            evidence=("integration-test: visual presentation produced and accepted",),
        )
    )

    result = execute_resource_production_with_fallback(
        task,
        tools,
        providers,
        validation_registry=registry,
    )

    assert result["status"] == "ACCEPTED"
    assert result["tool_id"] == "notebooklm"
    assert calls == ["notebooklm"]
    assert result["result"]["resource_type"] == task.required_output
    assert result["result"]["level"] == task.level
    assert result["result"]["objective"] == task.objective
    assert tools[0].validation_status("visual_resource_generation") == NOT_VALIDATED
    assert registry.get("notebooklm", "visual_resource_generation").status == VALIDATED
