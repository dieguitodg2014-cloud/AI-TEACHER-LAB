import json
import unittest
from unittest.mock import patch

from core.foundation.models import FrozenMapping
from tools.connectors.local_openai_compatible import (
    DEFAULT_MAX_TOKENS,
    DEFAULT_TIMEOUT_SECONDS,
    LocalProviderError,
    create_local_openai_compatible_generator,
)


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


class LocalOpenAICompatibleTests(unittest.TestCase):
    def test_generator_returns_provider_json(self):
        payload = {
            "choices": [
                {
                    "message": {
                        "content": json.dumps(
                            {
                                "level": "A2",
                                "objective": "Discuss past experiences and ask follow-up questions.",
                                "duration_minutes": 90,
                                "activities": [{"stage": "presentation", "minutes": 10}],
                            }
                        )
                    }
                }
            ]
        }
        generator = create_local_openai_compatible_generator(
            base_url="http://test/v1/chat/completions",
            model="test-model",
        )

        with patch("tools.connectors.local_openai_compatible.request.urlopen", return_value=FakeResponse(payload)):
            result = generator(
                {
                    "level": "A2",
                    "objective": "Discuss past experiences and ask follow-up questions.",
                    "duration_minutes": 90,
                    "sequence": [],
                },
                [],
            )

        self.assertEqual(result["level"], "A2")
        self.assertEqual(result["duration_minutes"], 90)
        self.assertTrue(result["activities"])

    def test_frozen_mapping_request_is_json_serializable(self):
        payload = {
            "choices": [
                {"message": {"content": '{"level":"A2","objective":"x","duration_minutes":90,"activities":[{}]}'}}
            ]
        }
        generator = create_local_openai_compatible_generator(base_url="http://test")

        request_data = FrozenMapping({
            "level": "A2",
            "teacher_preferences": FrozenMapping({"mode": "guided"}),
            "sequence": [{"stage": "presentation", "minutes": 10}],
        })
        with patch("tools.connectors.local_openai_compatible.request.urlopen", return_value=FakeResponse(payload)) as mocked:
            generator(request_data, [])

        sent = json.loads(mocked.call_args.args[0].data.decode("utf-8"))
        prompt = sent["messages"][1]["content"]
        self.assertIn('"teacher_preferences": {', prompt)
        self.assertIn('"mode": "guided"', prompt)

    def test_activity_contract_fields_are_required_in_prompt(self):
        payload = {
            "choices": [
                {"message": {"content": '{"level":"A2","objective":"x","duration_minutes":90,"activities":[{}]}'}}
            ]
        }
        generator = create_local_openai_compatible_generator(base_url="http://test")

        request_data = {
            "activity_contracts": [
                {
                    "activity_id": "act-1",
                    "level": "A2",
                    "objective": "x",
                    "skill": "SPEAKING",
                    "interaction": "pairs",
                    "cognitive_demand": "APPLY",
                    "scaffolding": 2,
                    "duration_minutes": 20,
                    "language_target": "x",
                    "evidence": "observable speaking performance",
                }
            ]
        }
        with patch("tools.connectors.local_openai_compatible.request.urlopen", return_value=FakeResponse(payload)) as mocked:
            generator(request_data, [])

        sent = json.loads(mocked.call_args.args[0].data.decode("utf-8"))
        prompt = sent["messages"][1]["content"]
        for field in (
            "activity_id", "skill", "interaction", "cognitive_demand",
            "scaffolding", "duration_minutes", "language_target", "evidence",
        ):
            self.assertIn(f'"{field}"', prompt)

    def test_generation_controls_are_sent(self):
        payload = {
            "choices": [
                {"message": {"content": '{"level":"A2","objective":"x","duration_minutes":90,"activities":[{}]}'}},
            ]
        }
        generator = create_local_openai_compatible_generator(base_url="http://test")

        with patch("tools.connectors.local_openai_compatible.request.urlopen", return_value=FakeResponse(payload)) as mocked:
            generator({"level": "A2"}, [])

        sent = json.loads(mocked.call_args.args[0].data.decode("utf-8"))
        self.assertEqual(sent["max_tokens"], DEFAULT_MAX_TOKENS)

    def test_timeout_environment_override_is_used(self):
        with patch.dict("os.environ", {"AI_TEACHER_LAB_PROVIDER_TIMEOUT_SECONDS": "300"}, clear=False):
            generator = create_local_openai_compatible_generator(base_url="http://test")
            with patch(
                "tools.connectors.local_openai_compatible.request.urlopen",
                return_value=FakeResponse({
                    "choices": [{"message": {"content": "{}"}}]
                }),
            ) as mocked:
                generator({"level": "A2"}, [])

        self.assertEqual(mocked.call_args.kwargs["timeout"], 300)

    def test_timeout_is_controlled(self):
        generator = create_local_openai_compatible_generator(base_url="http://test")

        with patch(
            "tools.connectors.local_openai_compatible.request.urlopen",
            side_effect=TimeoutError("timed out"),
        ):
            with self.assertRaises(LocalProviderError) as caught:
                generator({"level": "A2"}, [])

        self.assertEqual(str(caught.exception), "PROVIDER_TIMEOUT")

    def test_malformed_provider_json_is_controlled(self):
        payload = {
            "choices": [{"message": {"content": "not json"}}]
        }
        generator = create_local_openai_compatible_generator(base_url="http://test")

        with patch("tools.connectors.local_openai_compatible.request.urlopen", return_value=FakeResponse(payload)):
            with self.assertRaises(LocalProviderError) as caught:
                generator({"level": "A2"}, [])

        self.assertEqual(str(caught.exception), "INVALID_PROVIDER_JSON")

    def test_previous_qc_errors_are_sent_in_request(self):
        payload = {
            "choices": [
                {"message": {"content": '{"level":"A2","objective":"x","duration_minutes":90,"activities":[{}]}'}}
            ]
        }
        generator = create_local_openai_compatible_generator(base_url="http://test")

        with patch("tools.connectors.local_openai_compatible.request.urlopen", return_value=FakeResponse(payload)) as mocked:
            generator({"level": "A2", "objective": "x"}, ["LEVEL_MISMATCH"])

        sent = json.loads(mocked.call_args.args[0].data.decode("utf-8"))
        self.assertIn("LEVEL_MISMATCH", sent["messages"][1]["content"])


if __name__ == "__main__":
    unittest.main()
