from core.foundation.models import TaskPacket
from core.orchestration.canva_provider import CanvaResourceProvider
from core.orchestration.notebooklm_provider import NotebookLMResourceProvider
from core.orchestration.resource_orchestrator import execute_resource_production_with_fallback
from core.orchestration.tool_selector import ToolCandidate


def make_task():
    return TaskPacket(
        task_id="acceptance-fallback-1",
        task_type="RESOURCE_PRODUCTION",
        objective="Practice greetings with visual prompts.",
        level="A1",
        required_output="presentation",
        constraints=["simple language"],
        quality_criteria=["clear visuals", "objective alignment"],
        preferred_tool="notebooklm",
        fallback_tool="canva",
        visual=True,
    )


def make_tool(tool_id):
    return ToolCandidate(
        tool_id=tool_id,
        capabilities=frozenset({
            "resource_generation",
            "presentation_generation",
            "visual_resource_generation",
        }),
        quality=1.0,
        reliability=1.0,
        accessibility=1.0,
        speed=1.0,
        cost=0.0,
    )


def test_fallback_output_must_pass_acceptance_gate_before_ready():
    task = make_task()
    calls = []

    def notebooklm_executor(payload):
        calls.append("notebooklm")
        raise RuntimeError("connector unavailable")

    def canva_executor(payload):
        calls.append("canva")
        approved_task = payload["task"]
        return {
            "resource_type": "presentation",
            "level": approved_task["level"],
            "objective": approved_task["objective"],
            "content": "Visual greeting slides.",
            "quality_criteria_addressed": approved_task["quality_criteria"],
        }

    result = execute_resource_production_with_fallback(
        task,
        [make_tool("notebooklm"), make_tool("canva")],
        {
            "notebooklm": NotebookLMResourceProvider(notebooklm_executor),
            "canva": CanvaResourceProvider(canva_executor),
        },
    )

    assert calls == ["notebooklm", "canva"]
    assert result["status"] in {"ACCEPTED", "READY"}
    assert result["tool_id"] == "canva"
    assert result["validation"].status == "READY"
    assert result["validation"].critical_failure is False
    assert result["validation"].score == 100.0


def test_fallback_can_produce_but_blocking_qc_error_never_becomes_ready():
    task = make_task()

    def notebooklm_executor(_payload):
        raise RuntimeError("connector unavailable")

    def bad_canva_executor(payload):
        approved_task = payload["task"]
        return {
            "resource_type": "audio",
            "level": approved_task["level"],
            "objective": approved_task["objective"],
            "content": "Wrong resource type.",
        }

    result = execute_resource_production_with_fallback(
        task,
        [make_tool("notebooklm"), make_tool("canva")],
        {
            "notebooklm": NotebookLMResourceProvider(notebooklm_executor),
            "canva": CanvaResourceProvider(bad_canva_executor),
        },
    )

    assert result["tool_id"] == "canva"
    assert result["status"] == "REJECT"
    assert result["validation"].critical_failure is True
    assert result["validation"].status == "REJECT"
