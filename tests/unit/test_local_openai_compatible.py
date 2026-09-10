import json
import unittest
from unittest.mock import patch

from tools.connectors.local_openai_compatible import (
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
