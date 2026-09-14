from dataclasses import replace

from core.foundation.models import TaskPacket
from core.resources.acceptance_gate import ResourceAcceptanceGate
from core.resources.output_validator import validate_resource_output


def make_task():
    return TaskPacket(
        task_id="TASK-ACCEPT-001",
        task_type="RESOURCE_PRODUCTION",
        objective="Practice listening for key details.",
        level="A2",
        required_output="audio",
        constraints=["Keep language appropriate for the approved level."],
        quality_criteria=["Support the stated learning objective."],
        audience="English learners",
    )


def make_resource():
    return {
        "resource_type": "audio",
        "level": "A2",
        "objective": "Practice listening for key details.",
        "content": "Listen to the short conversation and identify two key details.",
    }


def test_ready_qc_must_cross_acceptance_gate():
    task = make_task()
    resource = make_resource()
    validation = validate_resource_output(task, resource)

    assert validation.status == "READY"
    acceptance = ResourceAcceptanceGate().evaluate(task, validation, resource)
    assert acceptance.decision == "ACCEPT"
    assert acceptance.blocking is False


def test_acceptance_rejects_ready_validation_without_produced_resource():
    task = make_task()
    resource = make_resource()
    validation = validate_resource_output(task, resource)

    acceptance = ResourceAcceptanceGate().evaluate(task, validation)

    assert validation.status == "READY"
    assert acceptance.decision == "HUMAN_HANDOFF"
    assert acceptance.blocking is True
    assert acceptance.reasons == ("RESOURCE_VALIDATION_OUTPUT_MISSING",)


def test_acceptance_rejects_resource_replaced_after_qc():
    task = make_task()
    validated_resource = make_resource()
    validation = validate_resource_output(task, validated_resource)
    replaced_resource = make_resource()
    replaced_resource["content"] = "A different resource was substituted after validation."

    acceptance = ResourceAcceptanceGate().evaluate(task, validation, replaced_resource)

    assert validation.status == "READY"
    assert acceptance.decision == "HUMAN_HANDOFF"
    assert acceptance.blocking is True
    assert acceptance.reasons == ("RESOURCE_VALIDATION_OUTPUT_BINDING_MISMATCH",)


def test_acceptance_rejects_ready_validation_without_output_binding():
    task = make_task()
    resource = make_resource()
    validation = validate_resource_output(task, resource)
    unbound = replace(validation, resource_fingerprint="")

    acceptance = ResourceAcceptanceGate().evaluate(task, unbound, resource)

    assert acceptance.decision == "HUMAN_HANDOFF"
    assert acceptance.blocking is True
    assert acceptance.reasons == ("RESOURCE_VALIDATION_OUTPUT_BINDING_MISSING",)


def test_revision_required_does_not_cross_acceptance_boundary():
    task = make_task()
    resource = make_resource()
    resource["quality_criteria_addressed"] = []
    validation = validate_resource_output(task, resource)

    assert validation.status == "REVISION_REQUIRED"
    acceptance = ResourceAcceptanceGate().evaluate(task, validation, resource)
    assert acceptance.decision == "REVISION_REQUIRED"
    assert acceptance.blocking is True


def test_provider_ready_field_cannot_bypass_qc():
    task = make_task()
    resource = make_resource()
    resource["production_status"] = "READY"
    resource["resource_type"] = "worksheet"
    validation = validate_resource_output(task, resource)

    assert validation.status == "REJECT"
    acceptance = ResourceAcceptanceGate().evaluate(task, validation, resource)
    assert acceptance.decision == "HUMAN_HANDOFF"


def test_ready_validation_cannot_cross_gate_for_different_task():
    approved_task = make_task()
    resource = make_resource()
    validation = validate_resource_output(approved_task, resource)
    changed_task = replace(approved_task, objective="Practice listening for specific information.")

    assert validation.status == "READY"
    acceptance = ResourceAcceptanceGate().evaluate(changed_task, validation, resource)

    assert acceptance.decision == "HUMAN_HANDOFF"
    assert acceptance.blocking is True
    assert acceptance.reasons == ("RESOURCE_VALIDATION_TASK_BINDING_MISMATCH",)


def test_unbound_ready_validation_cannot_cross_gate():
    task = make_task()
    validation = validate_resource_output(task, make_resource())
    unbound = replace(validation, task_fingerprint="")

    acceptance = ResourceAcceptanceGate().evaluate(task, unbound, make_resource())

    assert acceptance.decision == "HUMAN_HANDOFF"
    assert acceptance.blocking is True
    assert acceptance.reasons == ("RESOURCE_VALIDATION_TASK_BINDING_MISSING",)
