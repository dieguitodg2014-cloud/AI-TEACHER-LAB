from core.foundation.models import Context, LearningPlanDecision, ResourceDecision
from core.orchestration.task_packets import build_resource_task_packet


def _context() -> Context:
    return Context(
        context_id="ctx-1",
        level="A2",
        audience="adult ESL learners",
        duration_minutes=90,
        objective="Practice listening for key information.",
        constraints=[],
    )


def _plan() -> LearningPlanDecision:
    return LearningPlanDecision(
        plan_id="plan-1",
        objective="Practice listening for key information.",
        sequence=[],
        total_minutes=90,
        evidence_of_learning="Students identify key information.",
        resource_need="CREATE",
    )


def test_no_resource_decision_creates_no_task_packet():
    decision = ResourceDecision(
        decision_id="resource-1",
        action="NO_RESOURCE_REQUIRED",
        purpose="Practice conversation.",
    )

    assert build_resource_task_packet(_context(), _plan(), decision) is None


def test_create_resource_decision_creates_production_task_packet():
    decision = ResourceDecision(
        decision_id="resource-2",
        action="CREATE",
        purpose="Provide listening input.",
        resource_type="audio",
        reason="Listening requires auditory input.",
        required=True,
    )

    packet = build_resource_task_packet(_context(), _plan(), decision)

    assert packet is not None
    assert packet.task_type == "RESOURCE_PRODUCTION"
    assert packet.objective == _context().objective
    assert packet.level == "A2"
    assert packet.required_output == "audio"
    assert packet.status == "PENDING"
