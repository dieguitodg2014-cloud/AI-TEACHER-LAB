import pytest

from core.foundation.models import Context, LearningPlanDecision, ResourceDecision
from core.orchestration.task_packets import build_resource_task_packet
from core.resources.approved_content import ApprovedResourceContent, approved_input_materials


def _context() -> Context:
    return Context(
        context_id="ctx-1",
        level="A2",
        audience="adult ESL learners",
        duration_minutes=60,
        objective="Identify the main idea and key details in a short conversation.",
        topic="Daily routines",
    )


def _plan() -> LearningPlanDecision:
    return LearningPlanDecision(
        plan_id="plan-1",
        objective=_context().objective,
        sequence=[],
        total_minutes=60,
        evidence_of_learning="Learners identify the main idea and key details.",
        resource_need="audio",
    )


def _decision() -> ResourceDecision:
    return ResourceDecision(
        decision_id="resource-1",
        action="CREATE",
        purpose="Provide a short listening input.",
        resource_type="audio",
        required=True,
    )


def test_approved_content_is_bound_to_task_packet_input_materials():
    approved = ApprovedResourceContent(
        "A: What time do you start work? B: I start at eight."
    )

    task = build_resource_task_packet(_context(), _plan(), _decision(), approved)

    assert task is not None
    assert task.input_materials == (approved.content,)


def test_missing_approved_content_does_not_create_provider_input():
    task = build_resource_task_packet(_context(), _plan(), _decision())

    assert task is not None
    assert task.input_materials == ()


def test_approved_content_must_not_be_empty():
    with pytest.raises(ValueError, match="APPROVED_RESOURCE_CONTENT_REQUIRED"):
        ApprovedResourceContent("   ")


def test_input_materials_are_immutable():
    approved = ApprovedResourceContent("Approved script")

    assert approved_input_materials(approved) == ("Approved script",)
