from core.orchestration.capability_matrix import capabilities_for_resource


def test_audio_source_based_resource_requires_both_capabilities():
    assert capabilities_for_resource("audio", source_based=True) == frozenset(
        {
            "resource_generation",
            "audio_generation",
            "source_based_resource_generation",
        }
    )


def test_visual_presentation_requires_visual_and_presentation_capabilities():
    assert capabilities_for_resource("presentation", visual=True) == frozenset(
        {
            "resource_generation",
            "presentation_generation",
            "visual_resource_generation",
        }
    )


def test_generic_resource_has_minimum_capability_only():
    assert capabilities_for_resource("worksheet") == frozenset({"resource_generation"})
