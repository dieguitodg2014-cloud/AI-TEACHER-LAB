    assert result.generation["tool_id"] == "test-generator"
    assert result.generation["result"]["qc"] is not None

def test_runtime_connector_failure_cannot_reach_teacher_facing_acceptance(monkeypatch):
    def failing_loader(config_path):
        raise RuntimeError("connector unavailable")

    monkeypatch.setattr("core.workflow.configured_runtime.load_runtime_generators", failing_loader)

    result = run_configured_lesson_planning(
        {
            "level": "A2",
            "audience": "adult ESL learners",
            "duration_minutes": 60,
            "objective": "Discuss past experiences.",
        },
    )

    assert result.status == "FAILED"
    assert result.errors == ("RUNTIME_CONNECTOR_ERROR:connector unavailable",)