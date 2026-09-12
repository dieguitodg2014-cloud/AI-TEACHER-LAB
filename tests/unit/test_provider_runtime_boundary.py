from core.generation.revision import generate_with_revision


def test_malformed_provider_output_stops_before_generation_qc():
    calls = []

    def generator(request, errors):
        calls.append(1)
        return {"level": request["level"]}

    result = generate_with_revision(
        generator,
        {
            "level": "A2",
            "objective": "Discuss past experiences.",
            "duration_minutes": 90,
        },
    )

    assert result["status"] == "FAILED"
    assert result["attempts"] == 1
    assert result["qc"] is None
    assert result["errors"] == [
        "PROVIDER_OUTPUT_MISSING:objective",
        "PROVIDER_OUTPUT_MISSING:duration_minutes",
        "PROVIDER_OUTPUT_MISSING:activities",
    ]
    assert len(calls) == 1
