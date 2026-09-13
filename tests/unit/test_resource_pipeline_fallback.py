from copy import deepcopy

from core.foundation.models import TaskPacket
from core.orchestration.resource_orchestrator import execute_resource_production_with_fallback
from core.orchestration.tool_selector import ToolCandidate


class CountingProvider:
    def __init__(self, resource=None, error=None):
        self.resource = resource
        self.error = error
        self.calls = 0

    def can_produce(self, task_packet):
        self.calls += 1
        return self.error is None

    def produce(self, task_packet):
        self.calls += 1
        if self.error:
            raise RuntimeError(self.error)
        return self.resource


def make_task():
    return TaskPacket(
        task_id="pipeline-fallback-1",
        task_type="RESOURCE_PRODUCTION",
        objective="Practice listening for past experiences.",
        level="A2",
        required_output="audio",
        constraints=["A2 language"],
        quality_criteria=["Support the objective."],
        lesson_id="lesson-1",
        audience="adult ESL learners",
    )


def make_tool(tool_id, quality):
    return ToolCandidate(
        tool_id=tool_id,
        capabilities=frozenset({"resource_generation", "audio_generation"}),
        quality=quality,
        reliability=1.0,
        accessibility=1.0,
        speed=1.0,
        cost=0.0,
    )


def valid_resource(task):
    return {
        "resource_type": "audio",
        "level": task.level,
        "objective": task.objective,
        "content": "A short A2 listening about a past weekend experience.",
    }


def test_fallback_pipeline_qcs_successful_provider_only_once():
    task = make_task()
    before = deepcopy(task)
    failing = CountingProvider(error="temporary failure")
    working = CountingProvider(resource=valid_resource(task))

    result = execute_resource_production_with_fallback(
        task,
        [make_tool("provider-a", 1.0), make_tool("provider-b", 0.5)],
        {"provider-a": failing, "provider-b": working},
    )

    assert result["status"] == "ACCEPTED"
    assert result["tool_id"] == "provider-b"
    assert result["result"]["resource_type"] == "audio"
    assert [a.tool_id for a in result["provider_attempts"]] == ["provider-a", "provider-b"]
    assert failing.calls == 1
    assert working.calls == 2
    assert task == before


def test_fallback_pipeline_does_not_change_pedagogical_requirements():
    task = make_task()
    before = deepcopy(task)
    failing = CountingProvider(error="provider unavailable")
    working = CountingProvider(resource=valid_resource(task))

    result = execute_resource_production_with_fallback(
        task,
        [make_tool("provider-a", 1.0), make_tool("provider-b", 0.9)],
        {"provider-a": failing, "provider-b": working},
    )

    assert result["status"] == "ACCEPTED"
    assert result["validation"].checks["level_alignment"] is True
    assert result["validation"].checks["objective_alignment"] is True
    assert task == before


def test_all_provider_failures_handoff_without_qc_or_revision():
    task = make_task()
    first = CountingProvider(error="first failure")
    second = CountingProvider(error="second failure")

    result = execute_resource_production_with_fallback(
        task,
        [make_tool("provider-a", 1.0), make_tool("provider-b", 0.9)],
        {"provider-a": first, "provider-b": second},
    )

    assert result["status"] == "HUMAN_HANDOFF"
    assert result["result"] is None
    assert "validation" not in result
    assert len(result["provider_attempts"]) == 2
    assert first.calls == 1
    assert second.calls == 1
