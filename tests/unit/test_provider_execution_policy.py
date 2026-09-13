from copy import deepcopy

from core.foundation.models import TaskPacket
from core.orchestration.provider_execution_policy import ProviderExecutionPolicy
from core.orchestration.resource_provider import ResourceProvider
from core.orchestration.tool_selector import ToolCandidate


class StubProvider:
    def __init__(self, *, result=None, error=None, mutate_task=False):
        self.result = result
        self.error = error
        self.mutate_task = mutate_task
        self.calls = 0

    def can_produce(self, task_packet):
        self.calls += 1
        if self.mutate_task:
            task_packet.constraints.append("MUTATED")
        return self.error is None

    def produce(self, task_packet):
        self.calls += 1
        if self.error is not None:
            raise RuntimeError(self.error)
        return self.result


def make_task():
    return TaskPacket(
        task_id="task-fallback-1",
        task_type="RESOURCE_PRODUCTION",
        objective="Practice listening for past experiences.",
        level="A2",
        required_output="audio",
        constraints=["A2 language"],
        quality_criteria=["Support the objective."],
        lesson_id="lesson-1",
        audience="adult ESL learners",
    )


def make_tool(tool_id, *, quality=0.0, reliability=0.0):
    return ToolCandidate(
        tool_id=tool_id,
        capabilities=frozenset({"resource_generation"}),
        quality=quality,
        reliability=reliability,
        accessibility=1.0,
        speed=1.0,
        cost=0.0,
    )


def test_first_provider_success_requires_no_fallback():
    task = make_task()
    provider = StubProvider(result={"resource_type": "audio"})
    result = ProviderExecutionPolicy().execute(
        task,
        [make_tool("provider-a", quality=1.0)],
        {"provider-a": provider},
    )

    assert result.status == "PRODUCED"
    assert result.tool_id == "provider-a"
    assert len(result.attempts) == 1
    assert provider.calls == 2


def test_failed_provider_falls_back_to_next_eligible_provider():
    task = make_task()
    failing = StubProvider(error="temporary failure")
    working = StubProvider(result={"resource_type": "audio"})
    result = ProviderExecutionPolicy().execute(
        task,
        [make_tool("provider-a", quality=1.0), make_tool("provider-b", quality=0.5)],
        {"provider-a": failing, "provider-b": working},
    )

    assert result.status == "PRODUCED"
    assert result.tool_id == "provider-b"
    assert [a.tool_id for a in result.attempts] == ["provider-a", "provider-b"]
    assert result.attempts[0].errors == ("RESOURCE_PROVIDER_ERROR:temporary failure",)


def test_failed_provider_is_not_retried():
    task = make_task()
    failing = StubProvider(error="failure")
    working = StubProvider(error="failure")
    result = ProviderExecutionPolicy().execute(
        task,
        [make_tool("provider-a", quality=1.0), make_tool("provider-b", quality=0.9)],
        {"provider-a": failing, "provider-b": working},
    )

    assert result.status == "HUMAN_HANDOFF"
    assert len(result.attempts) == 2
    assert [a.tool_id for a in result.attempts] == ["provider-a", "provider-b"]


def test_fallback_preserves_authoritative_task_packet():
    task = make_task()
    before = deepcopy(task)
    failing = StubProvider(error="failure")
    working = StubProvider(result={"resource_type": "audio"})

    ProviderExecutionPolicy().execute(
        task,
        [make_tool("provider-a", quality=1.0), make_tool("provider-b", quality=0.9)],
        {"provider-a": failing, "provider-b": working},
    )

    assert task == before


def test_provider_task_mutation_isolated_during_fallback():
    task = make_task()
    before = deepcopy(task)
    mutating = StubProvider(result={"resource_type": "audio"}, mutate_task=True)
    working = StubProvider(result={"resource_type": "audio"})

    result = ProviderExecutionPolicy().execute(
        task,
        [make_tool("provider-a", quality=1.0), make_tool("provider-b", quality=0.9)],
        {"provider-a": mutating, "provider-b": working},
    )

    # The orchestrator gives providers defensive copies, so the mutation cannot
    # alter the authoritative TaskPacket or block a valid fallback.
    assert result.status == "PRODUCED"
    assert result.tool_id == "provider-a"
    assert task == before


def test_provider_without_required_capability_is_skipped():
    task = make_task()
    ineligible = StubProvider(result={"resource_type": "audio"})
    working = StubProvider(result={"resource_type": "audio"})
    bad_tool = ToolCandidate(
        tool_id="provider-a",
        capabilities=frozenset({"image_generation"}),
        quality=1.0,
    )

    result = ProviderExecutionPolicy().execute(
        task,
        [bad_tool, make_tool("provider-b", quality=0.5)],
        {"provider-a": ineligible, "provider-b": working},
    )

    assert result.status == "PRODUCED"
    assert result.tool_id == "provider-b"
    assert ineligible.calls == 0
