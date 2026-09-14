from core.foundation.models import TaskPacket
from core.orchestration.provider_execution_policy import ProviderExecutionPolicy
from core.orchestration.tool_selector import ToolCandidate


class StubProvider:
    def can_produce(self, task):
        return True

    def produce(self, task):
        return {"resource_type": task.required_output}


def _task() -> TaskPacket:
    return TaskPacket(
        task_id="task-semantics",
        task_type="RESOURCE_PRODUCTION",
        objective="Practice listening for key information.",
        level="A2",
        required_output="audio",
        constraints=(),
        quality_criteria=("Support the objective.",),
    )


def _tool(tool_id: str) -> ToolCandidate:
    return ToolCandidate(
        tool_id=tool_id,
        capabilities=frozenset({"resource_generation", "audio_generation"}),
    )


def test_capability_rejection_is_an_attempt_but_not_a_technical_fallback():
    calls = []

    def executor(task, tool, provider):
        calls.append(tool.tool_id)
        return {
            "status": "HUMAN_HANDOFF",
            "tool_id": tool.tool_id,
            "result": None,
            "errors": ["CAPABILITY_NOT_VALIDATED:audio_generation"],
        }

    result = ProviderExecutionPolicy().execute(
        _task(),
        [_tool("provider-a"), _tool("provider-b")],
        {"provider-a": StubProvider(), "provider-b": StubProvider()},
        executor=executor,
    )

    assert result.status == "HUMAN_HANDOFF"
    assert calls == ["provider-a"]
    assert tuple(attempt.tool_id for attempt in result.attempts) == ("provider-a",)
    assert result.errors == ("CAPABILITY_NOT_VALIDATED:audio_generation",)


def test_technical_failure_blocks_provider_and_allows_fallback():
    calls = []

    def executor(task, tool, provider):
        calls.append(tool.tool_id)
        if tool.tool_id == "provider-a":
            return {
                "status": "HUMAN_HANDOFF",
                "tool_id": tool.tool_id,
                "result": None,
                "errors": ["RESOURCE_PROVIDER_ERROR:timeout"],
            }
        return {
            "status": "PRODUCED",
            "tool_id": tool.tool_id,
            "result": {"resource_type": task.required_output},
            "errors": [],
        }

    result = ProviderExecutionPolicy().execute(
        _task(),
        [_tool("provider-a"), _tool("provider-b")],
        {"provider-a": StubProvider(), "provider-b": StubProvider()},
        executor=executor,
    )

    assert result.status == "PRODUCED"
    assert calls == ["provider-a", "provider-b"]
    assert tuple(attempt.tool_id for attempt in result.attempts) == ("provider-a", "provider-b")
    assert result.attempts[0].errors == ("RESOURCE_PROVIDER_ERROR:timeout",)
    assert ("provider-a", "BLOCKED_AFTER_EXECUTION_FAILURE") in result.excluded_tools


def test_no_eligible_provider_reports_exclusion_without_attempt():
    result = ProviderExecutionPolicy().execute(
        _task(),
        [_tool("provider-a")],
        {},
        executor=lambda task, tool, provider: {"status": "PRODUCED", "result": {}, "errors": []},
    )

    assert result.status == "HUMAN_HANDOFF"
    assert result.attempts == ()
    assert result.errors == ("NO_ELIGIBLE_RESOURCE_TOOL_AFTER_FALLBACK",)
    assert result.excluded_tools == (("provider-a", "RESOURCE_PROVIDER_NOT_CONFIGURED"),)


def test_unconfigured_preferred_provider_is_excluded_and_fallback_executes():
    calls = []

    def executor(task, tool, provider):
        calls.append(tool.tool_id)
        return {
            "status": "PRODUCED",
            "tool_id": tool.tool_id,
            "result": {"resource_type": task.required_output},
            "errors": [],
        }

    task = TaskPacket(
        task_id="task-unconfigured",
        task_type="RESOURCE_PRODUCTION",
        objective="Practice listening for key information.",
        level="A2",
        required_output="audio",
        constraints=(),
        quality_criteria=("Support the objective.",),
        preferred_tool="provider-a",
        fallback_tool="provider-b",
    )
    result = ProviderExecutionPolicy().execute(
        task,
        [_tool("provider-a"), _tool("provider-b")],
        {"provider-b": StubProvider()},
        executor=executor,
    )

    assert result.status == "PRODUCED"
    assert calls == ["provider-b"]
    assert tuple(attempt.tool_id for attempt in result.attempts) == ("provider-b",)
    assert ("provider-a", "RESOURCE_PROVIDER_NOT_CONFIGURED") in result.excluded_tools
