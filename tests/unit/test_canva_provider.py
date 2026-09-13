from core.foundation.models import TaskPacket
from core.orchestration.canva_provider import CanvaResourceProvider


def make_task() -> TaskPacket:
    return TaskPacket(
        task_id="task-canva-1",
        task_type="RESOURCE_PRODUCTION",
        objective="practice greetings",
        level="A1",
        required_output="presentation",
        constraints=["simple language"],
        quality_criteria=["age appropriate"],
        audience="children",
    )


def test_canva_provider_requires_configured_executor():
    provider = CanvaResourceProvider()
    assert provider.can_produce(make_task()) is False
    try:
        provider.produce(make_task())
    except RuntimeError as exc:
        assert str(exc) == "CANVA_CONNECTOR_NOT_CONFIGURED"
    else:
        raise AssertionError("Expected CANVA_CONNECTOR_NOT_CONFIGURED")


def test_canva_provider_passes_defensive_task_copy():
    received = {}

    def executor(payload):
        received.update(payload)
        payload["task"]["constraints"].append("connector mutation")
        return {
            "resource_type": "presentation",
            "level": "A1",
            "objective": "practice greetings",
            "content": "slides",
        }

    task = make_task()
    provider = CanvaResourceProvider(executor)
    result = provider.produce(task)

    assert result["content"] == "slides"
    assert received["provider"] == "canva"
    assert "connector mutation" not in task.constraints


def test_canva_provider_rejects_non_object_output():
    provider = CanvaResourceProvider(lambda payload: "invalid")
    try:
        provider.produce(make_task())
    except TypeError as exc:
        assert str(exc) == "CANVA_RESOURCE_OUTPUT_NOT_OBJECT"
    else:
        raise AssertionError("Expected CANVA_RESOURCE_OUTPUT_NOT_OBJECT")
