from dataclasses import replace

import pytest

from core.foundation.models import TaskPacket
from core.orchestration.canva_provider import CanvaResourceProvider


def make_task() -> TaskPacket:
    return TaskPacket(
        task_id="task-canva-1",
        task_type="RESOURCE_PRODUCTION",
        resource_type="presentation",
        level="A1",
        audience="children",
        objective="practice greetings",
        output_format="slides",
        duration_minutes=20,
        constraints=["simple language"],
        quality_criteria=["age appropriate"],
        source_requirements=[],
        materials=[],
    )


def test_canva_provider_requires_configured_executor():
    provider = CanvaResourceProvider()
    assert provider.can_produce(make_task()) is False
    with pytest.raises(RuntimeError, match="CANVA_CONNECTOR_NOT_CONFIGURED"):
        provider.produce(make_task())


def test_canva_provider_passes_defensive_task_copy():
    received = {}

    def executor(payload):
        received.update(payload)
        payload["task"]["constraints"].append("connector mutation")
        return {"resource_type": "presentation", "level": "A1", "objective": "practice greetings", "content": "slides"}

    task = make_task()
    provider = CanvaResourceProvider(executor)
    result = provider.produce(task)

    assert result["content"] == "slides"
    assert received["provider"] == "canva"
    assert "connector mutation" not in task.constraints


def test_canva_provider_rejects_non_object_output():
    provider = CanvaResourceProvider(lambda payload: "invalid")
    with pytest.raises(TypeError, match="CANVA_RESOURCE_OUTPUT_NOT_OBJECT"):
        provider.produce(make_task())
