from copy import deepcopy

from core.foundation.models import TaskPacket
from core.orchestration.provider_execution_policy import ProviderExecutionPolicy
from core.orchestration.resource_orchestrator import execute_resource_provider
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


def make_task(**overrides):
    values = dict(
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
    values.update(overrides)
    return TaskPacket(**values)


def make_tool(tool_id, *, quality=0.0, reliability=0.0, capabilities=None):
    return ToolCandidate(
        tool_id=tool_id,
        capabilities=frozenset(capabilities or {"resource_generation", "audio_generation"}),
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
    assert ("provider-a", "BLOCKED_AFTER_EXECUTION_FAILURE") in result.excluded_tools


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
    assert ("provider-a", "BLOCKED_AFTER_EXECUTION_FAILURE") in result.excluded_tools
    assert ("provider-b", "BLOCKED_AFTER_EXECUTION_FAILURE") in result.excluded_tools


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
    assert ("provider-a", "MISSING_REQUIRED_CAPABILITIES:audio_generation,resource_generation") in result.excluded_tools


def test_preferred_tool_is_selected_when_capable():
    task = make_task(preferred_tool="provider-b")
    preferred = StubProvider(result={"resource_type": "audio"})
    higher_scored = StubProvider(result={"resource_type": "audio"})

    result = ProviderExecutionPolicy().execute(
        task,
        [make_tool("provider-a", quality=1.0), make_tool("provider-b", quality=0.1)],
        {"provider-a": higher_scored, "provider-b": preferred},
    )

    assert result.tool_id == "provider-b"
    assert [a.tool_id for a in result.attempts] == ["provider-b"]
    assert higher_scored.calls == 0


def test_unusable_preferred_tool_does_not_override_capabilities():
    task = make_task(preferred_tool="provider-a")
    preferred_but_incompatible = ToolCandidate(
        tool_id="provider-a",
        capabilities=frozenset({"image_generation"}),
        quality=10.0,
    )
    working = StubProvider(result={"resource_type": "audio"})

    result = ProviderExecutionPolicy().execute(
        task,
        [preferred_but_incompatible, make_tool("provider-b", quality=0.5)],
        {"provider-a": StubProvider(result={"resource_type": "audio"}), "provider-b": working},
    )

    assert result.tool_id == "provider-b"
    assert working.calls == 2
    assert ("provider-a", "MISSING_REQUIRED_CAPABILITIES:audio_generation,resource_generation") in result.excluded_tools


def test_fallback_hint_is_used_after_preferred_provider_fails():
    task = make_task(preferred_tool="provider-a", fallback_tool="provider-b")
    preferred = StubProvider(error="preferred unavailable")
    fallback = StubProvider(result={"resource_type": "audio"})
    third = StubProvider(result={"resource_type": "audio"})

    result = ProviderExecutionPolicy().execute(
        task,
        [make_tool("provider-a", quality=1.0), make_tool("provider-b", quality=0.1), make_tool("provider-c", quality=0.9)],
        {"provider-a": preferred, "provider-b": fallback, "provider-c": third},
    )

    assert result.tool_id == "provider-b"
    assert [a.tool_id for a in result.attempts] == ["provider-a", "provider-b"]
    assert third.calls == 0


def test_direct_provider_execution_enforces_audio_capability():
    task = make_task(required_output="audio")
    tool = make_tool("provider-a", capabilities={"resource_generation"})
    provider = StubProvider(result={"resource_type": "audio"})

    result = execute_resource_provider(task, tool, provider)

    assert result["status"] == "HUMAN_HANDOFF"
    assert result["errors"] == ["PROVIDER_NOT_ELIGIBLE_FOR_TASK:provider-a:RESOURCE_PRODUCTION"]
    assert provider.calls == 0


def test_direct_provider_execution_enforces_source_based_capability():
    task = make_task(required_output="worksheet", source_based=True)
    tool = make_tool("provider-a")
    provider = StubProvider(result={"resource_type": "worksheet"})

    result = execute_resource_provider(task, tool, provider)

    assert result["status"] == "HUMAN_HANDOFF"
    assert provider.calls == 0


def test_direct_provider_execution_blocks_unvalidated_required_capability():
    task = make_task(required_output="audio")
    tool = ToolCandidate(
        tool_id="provider-a",
        capabilities=frozenset({"resource_generation", "audio_generation"}),
        capability_validation=(("audio_generation", "not_validated"),),
    )
    provider = StubProvider(result={"resource_type": "audio"})

    result = execute_resource_provider(task, tool, provider)

    assert result["status"] == "HUMAN_HANDOFF"
    assert result["errors"] == ["CAPABILITY_NOT_VALIDATED:audio_generation"]
    assert provider.calls == 0


def test_direct_provider_execution_blocks_unvalidated_source_capability():
    task = make_task(required_output="worksheet", source_based=True)
    tool = ToolCandidate(
        tool_id="provider-a",
        capabilities=frozenset({"resource_generation", "source_based_resource_generation"}),
        capability_validation=(("source_based_resource_generation", "not_validated"),),
    )
    provider = StubProvider(result={"resource_type": "worksheet"})

    result = execute_resource_provider(task, tool, provider)

    assert result["status"] == "HUMAN_HANDOFF"
    assert result["errors"] == ["CAPABILITY_NOT_VALIDATED:source_based_resource_generation"]
    assert provider.calls == 0


def test_capability_rejection_does_not_trigger_technical_fallback():
    task = make_task()
    rejected = StubProvider(result={"resource_type": "audio"})
    fallback = StubProvider(result={"resource_type": "audio"})

    def reject_capability(_task, _tool, _provider):
        return {
            "status": "HUMAN_HANDOFF",
            "result": None,
            "errors": ["CAPABILITY_NOT_VALIDATED:audio_generation"],
        }

    result = ProviderExecutionPolicy().execute(
        task,
        [make_tool("provider-a", quality=1.0), make_tool("provider-b", quality=0.5)],
        {"provider-a": rejected, "provider-b": fallback},
        executor=reject_capability,
    )

    assert result.status == "HUMAN_HANDOFF"
    assert result.tool_id == "provider-a"
    assert result.errors == ("CAPABILITY_NOT_VALIDATED:audio_generation",)
    assert [attempt.tool_id for attempt in result.attempts] == ["provider-a"]
    assert rejected.calls == 0
    assert fallback.calls == 0
