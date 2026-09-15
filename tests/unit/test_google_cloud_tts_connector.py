from __future__ import annotations

import base64
import json

import pytest

from tools.connectors import google_cloud_tts


class _FakeResponse:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self):
        return json.dumps({"audioContent": base64.b64encode(b"fake-audio").decode()}).encode()


def test_google_cloud_tts_uses_approved_script_and_returns_resource(monkeypatch):
    captured = {}

    def fake_urlopen(req, timeout):
        captured["body"] = json.loads(req.data.decode())
        captured["authorization"] = req.headers["Authorization"]
        captured["timeout"] = timeout
        return _FakeResponse()

    monkeypatch.setenv("GOOGLE_CLOUD_ACCESS_TOKEN", "test-token")
    monkeypatch.setenv("GOOGLE_CLOUD_TTS_ENDPOINT", "https://example.test/synthesize")
    monkeypatch.setattr(google_cloud_tts.request, "urlopen", fake_urlopen)

    generate = google_cloud_tts.create_google_cloud_tts_generator()
    task = {
        "required_output": "audio",
        "level": "A2",
        "objective": "Identify the main idea and key details.",
        "input_materials": ["Speaker A: I went to Cartagena last year."] ,
    }

    result = generate(task)

    assert captured["body"]["input"]["text"] == task["input_materials"][0]
    assert captured["authorization"] == "Bearer test-token"
    assert result["resource_type"] == "audio"
    assert result["level"] == "A2"
    assert result["objective"] == task["objective"]
    assert result["transcript"] == task["input_materials"][0]
    assert result["production_status"] == "PRODUCED"
    assert result["content"] == base64.b64encode(b"fake-audio").decode()


def test_google_cloud_tts_requires_approved_script(monkeypatch):
    monkeypatch.setenv("GOOGLE_CLOUD_ACCESS_TOKEN", "test-token")
    generate = google_cloud_tts.create_google_cloud_tts_generator()

    with pytest.raises(ValueError, match="RESOURCE_INPUT_MATERIALS_REQUIRED"):
        generate({"required_output": "audio", "level": "A2", "objective": "Listen."})


def test_google_cloud_tts_requires_access_token(monkeypatch):
    monkeypatch.delenv("GOOGLE_CLOUD_ACCESS_TOKEN", raising=False)
    generate = google_cloud_tts.create_google_cloud_tts_generator()

    with pytest.raises(RuntimeError, match="GOOGLE_CLOUD_ACCESS_TOKEN_REQUIRED"):
        generate({
            "required_output": "audio",
            "level": "A2",
            "objective": "Listen.",
            "input_materials": ["Hello."],
        })
