import json

from tools.connectors import runtime_loader
from core.workflow.configured_runtime import run_configured_lesson_planning


def test_configured_runtime_resolves_generator_and_runs_vertical_slice(tmp_path, monkeypatch):
    config_path = tmp_path / "tools.json"
    config_path.write_text(
        json.dumps(
            {
                "tools": [
                    {
                        "tool_id": "test-generator",
                        "connector": "test_connector",
                        "capabilities": ["lesson_generation"],
                        "quality": 1.0,
                        "reliability": 1.0,
                        "accessibility": 1.0,
                        "speed": 1.0,
                        "cost": 0.0,
                    }
                ],
                "policy": {"free_first": True},
            }
        ),
        encoding="utf-8",
    )

    def generator(generation_request, previous_errors):
        return {
            "level": generation_request["level"],
            "objective": generation_request["objective"],
            "duration_minutes": generation_request["duration_minutes"],
            "topic": generation_request["topic"],
            "activities": [
                {
                    "stage": stage,
                    "minutes": activity["minutes"],
                    "purpose": stage["purpose"],
                    "instructions": "Run the activity.",
                    "student_production": "Students discuss a past experience and ask a follow-up question.",
                    "assessment_link": "Teacher observes the learner response during the task.",
                }
                for stage, activity in zip(
                    generation_request["sequence"],
                    generation_request["sequence"],
                )
            ],
        }

    monkeypatch.setitem(runtime_loader._CONNECTOR_FACTORIES, "test_connector", lambda: generator)

    result = run_configured_lesson_planning(
        {
            "level": "A2",
            "audience": "adult ESL learners",
            "duration_minutes": 90,
            "objective": "Discuss past experiences and ask follow-up questions.",
            "topic": "Present Perfect",
            "constraints": ["Students know Past Simple", "Question formation is a difficulty"],
        },
        tool_config_path=config_path,
    )

    assert result.status == "READY"
    assert result.generation["tool_id"] == "test-generator"


def test_provider_cannot_redefine_approved_pedagogical_objective(tmp_path, monkeypatch):
    config_path = tmp_path / "tools.json"
    config_path.write_text(
        json.dumps(
            {
                "tools": [
                    {
                        "tool_id": "test-generator",
                        "connector": "test_connector",
                        "capabilities": ["lesson_generation"],
                        "quality": 1.0,
                        "reliability": 1.0,
                        "accessibility": 1.0,
                        "speed": 1.0,
                        "cost": 0.0,
                    }
                ],
                "policy": {"free_first": True},
            }
        ),
        encoding="utf-8",
    )

    def generator(generation_request, previous_errors):
        return {
            "level": generation_request["level"],
            "objective": "Teach unrelated vocabulary instead.",
            "duration_minutes": generation_request["duration_minutes"],
            "activities": [
                {
                    "minutes": activity["minutes"],
                    "purpose": activity["purpose"],
                    "instructions": "Run the approved activity.",
                    "student_production": "Students discuss a past experience and ask a follow-up question.",
                    "assessment_link": "Teacher observes the learner response during the task.",
                }
                for activity in generation_request["sequence"]
            ],
        }

    monkeypatch.setitem(runtime_loader._CONNECTOR_FACTORIES, "test_connector", lambda: generator)

    result = run_configured_lesson_planning(
        {
            "level": "A2",
            "audience": "adult ESL learners",
            "duration_minutes": 90,
            "objective": "Discuss past experiences and ask follow-up questions.",
            "topic": "Present Perfect",
            "constraints": ["Students know Past Simple", "Question formation is a difficulty"],
        },
        tool_config_path=config_path,
    )

    assert result.status != "READY"
    assert result.generation["tool_id"] == "test-generator"
    assert result.generation["result"]["qc"] is not None
