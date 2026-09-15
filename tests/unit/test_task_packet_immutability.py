import pytest

from core.foundation.models import TaskPacket


def make_task(**overrides):
    values = {
        "task_id": "TASK-IMMUTABLE-001",
        "task_type": "RESOURCE_PRODUCTION",
        "objective": "Practice listening for key details.",
        "level": "A2",
        "required_output": "audio",
        "constraints": ["Use authentic-looking classroom language."],
        "quality_criteria": ["Support the stated objective."],
        "input_materials": ["source-a"],
        "audience": "English learners",
    }
    values.update(overrides)
    return TaskPacket(**values)


def test_task_packet_copies_mutable_sequence_inputs():
    constraints = ["original constraint"]
    quality_criteria = ["original criterion"]
    input_materials = ["original source"]

    task = make_task(
        constraints=constraints,
        quality_criteria=quality_criteria,
        input_materials=input_materials,
    )

    constraints.append("mutated externally")
    quality_criteria.append("mutated externally")
    input_materials.append("mutated externally")

    assert task.constraints == ("original constraint",)
    assert task.quality_criteria == ("original criterion",)
    assert task.input_materials == ("original source",)


def test_task_packet_sequences_cannot_be_mutated_through_the_object():
    task = make_task()

    with pytest.raises(AttributeError):
        task.constraints.append("forbidden")

    with pytest.raises(AttributeError):
        task.quality_criteria.append("forbidden")

    with pytest.raises(AttributeError):
        task.input_materials.append("forbidden")


def test_task_packet_remains_frozen_for_scalar_fields():
    task = make_task()

    with pytest.raises(AttributeError):
        task.objective = "A different objective"
