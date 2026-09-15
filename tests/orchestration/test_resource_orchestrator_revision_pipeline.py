from core.foundation.models import TaskPacket
from core.orchestration.resource_orchestrator import execute_resource_production_pipeline
from core.orchestration.resource_provider import FunctionResourceProvider
from core.orchestration.tool_selector import ToolCandidate


def make_task() -> TaskPacket:
    return TaskPacket(
        task_id="TASK-REV-PIPE-001",
        task_type="RESOURCE_PRODUCTION",
        objective="Practice listening for key details.",
        level="A2",
        required_output="audio",
        constraints=[],
        quality_criteria=["Support the stated learning objective."],
        audience="English learners",
    )


def make_tool() -> ToolCandidate:
    return ToolCandidate(
        tool_id="test-audio-provider",
        capabilities={"resource_generation", "audio_generation"},
        quality=0.9,
        reliability=0.9,
        accessibility=0.9,
        speed=0.9,
        cost=0.0,
    )


def test_production_pipeline_accepts_valid_resource():
    task = make_task()
    tool = make_tool()
    provider = FunctionResourceProvider(
        lambda _task: {
            "level": "A2",
            "objective": "Practice listening for key details.",
            "content": "A short listening script with key details.",
            "resource_type": "audio",
        }
    )

    result = execute_resource_production_pipeline(task, tool, provider)

    assert result["status"] == "ACCEPTED"
    assert result["result"] is not None
    assert result["attempts"] == 1
    assert result["acceptance"].decision == "ACCEPT"


def test_production_pipeline_revises_then_accepts():
    task = make_task()
    tool = make_tool()
    provider = FunctionResourceProvider(
        lambda _task: {
            "level": "A2",
            "objective": "Practice speaking.",
            "content": "A listening script with key details.",
            "resource_type": "audio",
        }
    )

    def reviser(_task, resource, _validation):
        revised = dict(resource)
        revised["objective"] = "Practice listening for key details."
        return revised

    result = execute_resource_production_pipeline(task, tool, provider, reviser=reviser, max_revisions=1)

    assert result["status"] == "ACCEPTED"
    assert result["attempts"] == 2
    assert result["result"]["objective"] == "Practice listening for key details."
    assert result["revision_feedback"]


def test_production_pipeline_rejects_after_revision_does_not_fix_output():
    task = make_task()
    tool = make_tool()
    provider = FunctionResourceProvider(
        lambda _task: {
            "level": "A2",
            "objective": "Practice speaking.",
            "content": "A listening script with key details.",
            "resource_type": "audio",
        }
    )

    def non_fixing_reviser(_task, resource, _validation):
        return dict(resource)

    result = execute_resource_production_pipeline(
        task,
        tool,
        provider,
        reviser=non_fixing_reviser,
        max_revisions=1,
    )

    assert result["status"] == "REJECT_AND_REDESIGN"
    assert result["result"] is None
    assert result["attempts"] == 2
    assert result["acceptance"].decision == "REJECT_AND_REDESIGN"
    assert result["errors"]


def test_provider_output_cannot_bypass_qc_and_acceptance():
    task = make_task()
    tool = make_tool()
    provider = FunctionResourceProvider(
        lambda _task: {
            "status": "READY",
            "level": "A2",
            "objective": "Practice speaking.",
            "content": "A listening script with key details.",
            "resource_type": "audio",
        }
    )

    result = execute_resource_production_pipeline(task, tool, provider)

    assert result["status"] == "HUMAN_HANDOFF"
    assert result["result"] is None
    assert result["validation"] is not None
    assert result["acceptance"] is not None
