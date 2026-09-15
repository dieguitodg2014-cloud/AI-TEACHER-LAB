from dataclasses import asdict

from core.foundation.models import Context, LearningPlanDecision, ResourceDecision
from core.orchestration.task_packets import build_resource_task_packet
from core.resources.decision_engine import apply_resource_decision


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


def test_resource_decision_hints_are_copied_to_task_packet():
    decision = ResourceDecision(
        decision_id="resource-3",
        action="CREATE",
        purpose="Provide listening input.",
        resource_type="audio",
        preferred_tool="notebooklm",
        fallback_tool="audio-provider",
    )

    packet = build_resource_task_packet(_context(), _plan(), decision)

    assert packet is not None
    assert packet.preferred_tool == "notebooklm"
    assert packet.fallback_tool == "audio-provider"


def test_applying_resource_decision_does_not_mutate_learning_plan():
    plan = _plan()
    before = asdict(plan)
    decision = ResourceDecision(
        decision_id="resource-4",
        action="CREATE",
        purpose="Provide listening input.",
        resource_type="audio",
        required=True,
    )

    updated = apply_resource_decision(plan, decision)

    assert asdict(plan) == before
    assert updated is not plan
    assert plan.resource_need == "CREATE"
    assert updated.resource_need == "CREATE"


def test_building_task_packet_does_not_mutate_source_decisions():
    context = _context()
    plan = _plan()
    decision = ResourceDecision(
        decision_id="resource-5",
        action="CREATE",
        purpose="Provide listening input.",
        resource_type="audio",
        preferred_tool="notebooklm",
        fallback_tool="audio-provider",
        source_based=True,
    )
    context_before = asdict(context)
    plan_before = asdict(plan)
    decision_before = asdict(decision)

    packet = build_resource_task_packet(context, plan, decision)

    assert packet is not None
    assert asdict(context) == context_before
    assert asdict(plan) == plan_before
    assert asdict(decision) == decision_before
