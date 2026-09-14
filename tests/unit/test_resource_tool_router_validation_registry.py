from core.foundation.models import TaskPacket
from core.orchestration.capability_validation import CapabilityValidationResult, VALIDATED
from core.orchestration.capability_validation_registry import CapabilityValidationRegistry
from core.orchestration.resource_tool_router import select_resource_provider
from core.orchestration.tool_selector import ToolCandidate


def make_task():
    return TaskPacket(
        task_id="router-validation-1",
        task_type="RESOURCE_PRODUCTION",
        objective="Create visual prompts.",
        level="A1",
        required_output="presentation",
        constraints=[],
        quality_criteria=["Support the objective."],
        visual=True,
    )


def test_router_uses_registry_evidence_to_promote_validated_capability():
    task = make_task()
    tool = ToolCandidate(
        "notebooklm",
        frozenset({"resource_generation", "presentation_generation", "visual_resource_generation"}),
        capability_validation=(("visual_resource_generation", "not_validated"),),
    )
    registry = CapabilityValidationRegistry((
        CapabilityValidationResult("notebooklm", "visual_resource_generation", VALIDATED),
    ))

    selected = select_resource_provider(task, [tool], validation_registry=registry)

    assert selected is not None
    assert selected.tool_id == "notebooklm"
    assert selected.validation_status("visual_resource_generation") == VALIDATED


def test_router_still_skips_explicitly_unvalidated_capability():
    task = make_task()
    tool = ToolCandidate(
        "notebooklm",
        frozenset({"resource_generation", "presentation_generation", "visual_resource_generation"}),
        capability_validation=(("visual_resource_generation", "not_validated"),),
    )
    registry = CapabilityValidationRegistry()

    selected = select_resource_provider(task, [tool], validation_registry=registry)

    assert selected is None
