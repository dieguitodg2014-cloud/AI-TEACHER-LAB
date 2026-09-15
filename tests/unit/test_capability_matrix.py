from core.orchestration.capability_matrix import capabilities_for_resource


def test_generic_resource_requires_only_resource_generation():
    assert capabilities_for_resource("worksheet") == frozenset({"resource_generation"})


def test_audio_resource_requires_audio_generation():
    assert capabilities_for_resource("audio") == frozenset(
        {"resource_generation", "audio_generation"}
    )


def test_source_based_resource_adds_source_capability():
    assert capabilities_for_resource(
        "worksheet", source_based=True
    ) == frozenset(
        {"resource_generation", "source_based_resource_generation"}
    )


def test_visual_resource_adds_visual_capability():
    assert capabilities_for_resource(
        "worksheet", visual=True
    ) == frozenset({"resource_generation", "visual_resource_generation"})


def test_visual_presentation_requires_both_specialized_capabilities():
    assert capabilities_for_resource(
        "presentation", visual=True
    ) == frozenset(
        {
            "resource_generation",
            "presentation_generation",
            "visual_resource_generation",
        }
    )


def test_source_based_audio_unions_requirements():
    assert capabilities_for_resource(
        "audio", source_based=True
    ) == frozenset(
        {
            "resource_generation",
            "audio_generation",
            "source_based_resource_generation",
        }
    )
