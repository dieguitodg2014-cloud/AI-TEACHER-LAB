from core.foundation.models import TaskPacket
from core.orchestration.resource_orchestrator import (
    execute_resource_provider,
    validate_and_accept_resource,
)
from core.orchestration.tool_selector import ToolCandidate


class Provider:
    def __init__(self, *, resource=None, can_produce=True, can_error=None, produce_error=None):
        self.resource = resource
        self._can_produce = can_produce
        self.can_error = can_error
        self.produce_error = produce_error
        self.can_calls = 0
        self.produce_calls = 0

    def can_produce(self, task_packet):
        self.can_calls += 1
        if self.can_error:
            raise RuntimeError(self.can_error)
        return self._can_produce

    def produce(self, task_packet):
        self.produce_calls += 1
        if self.produce_error:
            raise RuntimeError(self.produce_error)
        return self.resource


def make_task():
    return TaskPacket(
        task_id="task-boundary-1",
        task_type="RESOURCE_PRODUCTION",
        objective="Practice listening for key details.",
        level="A2",
        required_output="audio",
        constraints=["A2 language"],
        quality_criteria=["Support the objective."],
        audience="English learners",
    )


def make_tool():
    return ToolCandidate(
        tool_id="provider-a",
        capabilities=frozenset({"resource_generation", "audio_generation"}),
    )


def make_resource():
    task = make_task()
    return {
        "resource_type": "audio",
        "level": "A2",
        "objective": task.objective,
        "content": "A short listening text.",
    }


def test_can_produce_exception_is_normalized_as_provider_failure():
    provider = Provider(can_error="availability check failed")

    result = execute_resource_provider(make_task(), make_tool(), provider)

    assert result["status"] == "HUMAN_HANDOFF"
    assert result["errors"] == ["RESOURCE_PROVIDER_ERROR:availability check failed"]
    assert provider.can_calls == 1
    assert provider.produce_calls == 0


def test_non_object_provider_output_is_rejected_at_execution_boundary():
    provider = Provider(resource=["not", "an", "object"])

    result = execute_resource_provider(make_task(), make_tool(), provider)

    assert result["status"] == "HUMAN_HANDOFF"
    assert result["errors"] == ["RESOURCE_OUTPUT_NOT_OBJECT"]
    assert provider.produce_calls == 1


def test_validate_and_accept_binds_qc_to_exact_resource():
    task = make_task()
    resource = make_resource()

    result = validate_and_accept_resource(task, resource)

    assert result["status"] == "ACCEPTED"
    assert result["acceptance"].decision == "ACCEPT"


def test_validate_and_accept_rejects_replaced_resource_at_gate():
    task = make_task()
    resource = make_resource()

    class ReplacingGate:
        def evaluate(self, task, validation, produced_resource=None):
            produced_resource["content"] = "replacement"
            from core.resources.acceptance_gate import ResourceAcceptanceGate
            return ResourceAcceptanceGate().evaluate(task, validation, produced_resource)

    result = validate_and_accept_resource(task, resource, acceptance_gate=ReplacingGate())

    assert result["status"] == "HUMAN_HANDOFF"
