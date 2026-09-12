from core.orchestration.generation_orchestrator import GenerationOrchestrator
from core.orchestration.tool_selector import ToolCandidate


def test_resource_production_rejects_lesson_only_provider():
    tool = ToolCandidate(
        tool_id="lesson-only",
        capabilities=frozenset({"lesson_generation"}),
        quality=1.0,
        reliability=1.0,
        accessibility=1.0,
        speed=1.0,
        cost=0.0,
    )

    result = GenerationOrchestrator(
        tools=[tool],
        generators={"lesson-only": lambda request, errors: {"level": "A2"}},
    ).run(
        {"level": "A2", "objective": "Practice listening.", "duration_minutes": 30, "activities": []},
        required_capabilities={"resource_generation"},
        task_type="RESOURCE_PRODUCTION",
    )

    assert result["status"] == "HUMAN_HANDOFF"
    assert result["tool_id"] is None
    assert result["errors"] == ["NO_SUITABLE_TOOL"]


def test_resource_production_accepts_resource_capable_provider():
    tool = ToolCandidate(
        tool_id="resource-tool",
        capabilities=frozenset({"resource_generation"}),
        quality=1.0,
        reliability=1.0,
        accessibility=1.0,
        speed=1.0,
        cost=0.0,
    )

    def generator(request, previous_errors):
        return {
            "level": request["level"],
            "objective": request["objective"],
            "duration_minutes": request["duration_minutes"],
            "activities": [],
        }

    result = GenerationOrchestrator(
        tools=[tool],
        generators={"resource-tool": generator},
    ).run(
        {"level": "A2", "objective": "Practice listening.", "duration_minutes": 30, "activities": []},
        required_capabilities={"resource_generation"},
        task_type="RESOURCE_PRODUCTION",
    )

    assert result["tool_id"] == "resource-tool"
    assert result["status"] in {"READY", "REJECT"}
