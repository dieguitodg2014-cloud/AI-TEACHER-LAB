from core.foundation.models import TaskPacket
from core.orchestration.resource_orchestrator import execute_resource_production_pipeline
from core.orchestration.resource_provider import FunctionResourceProvider
from core.orchestration.tool_selector import ToolCandidate


def make_task():
    return TaskPacket(
        task_id="TASK-PIPE-001",
        task_type="RESOURCE_PRODUCTION",
        objective="Practice listening for key details.",
        level="A2",
        required_output="audio",
        constraints=["Keep language appropriate for the approved level."],
        quality_criteria=["Support the stated learning objective."],
        audience="English learners",
    )


def make_tool():
    return ToolCandidate(
        tool_id="notebooklm",
        capabilities=["resource_generation", "audio_generation"],
        quality=0.95,
        reliability=0.9,
        accessibility=0.8,
        speed=0.7,
        cost=0.0,
    )


def test_pipeline_returns_only_accepted_resource_as_result():
    task = make_task()
    provider = FunctionResourceProvider(
        lambda _: {
            "resource_type": "audio",
            "level": "A2",
            "objective": "Practice listening for key details.",
            "content": "Listen and identify two key details.",
        }
    )

    result = execute_resource_production_pipeline(task, make_tool(), provider)

    assert result["status"] == "ACCEPTED"
    assert result["acceptance"].decision == "ACCEPT"
    assert result["validation"].status == "READY"
    assert result["result"]["resource_type"] == "audio"


def test_pipeline_blocks_invalid_provider_output():
    task = make_task()
    provider = FunctionResourceProvider(
        lambda _: {
            "resource_type": "worksheet",
            "level": "B1",
            "objective": "Different objective",
            "content": "Wrong resource.",
        }
    )

    result = execute_resource_production_pipeline(task, make_tool(), provider)

    assert result["status"] == "HUMAN_HANDOFF"
    assert result["result"] is None
    assert result["acceptance"].decision == "HUMAN_HANDOFF"
    assert result["validation"].critical_failure is True
