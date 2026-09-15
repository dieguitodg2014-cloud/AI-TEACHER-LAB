"""Google Cloud Text-to-Speech resource connector.

The connector is deliberately downstream of pedagogical planning: it only
turns an already-approved script in TaskPacket.input_materials into audio.
It does not author, expand, simplify, or otherwise change the instructional
content.
"""

from __future__ import annotations

import base64
import json
import os
from typing import Any
from urllib import error, request


DEFAULT_ENDPOINT = "https://texttospeech.googleapis.com/v1/text:synthesize"
DEFAULT_MODEL = "gemini-3.1-flash-tts-preview"
DEFAULT_LANGUAGE = "en-US"
DEFAULT_VOICE = "Kore"
DEFAULT_ENCODING = "MP3"


def create_google_cloud_tts_generator():
    """Create a runtime generator using a Google Cloud OAuth access token."""

    endpoint = os.getenv("GOOGLE_CLOUD_TTS_ENDPOINT", DEFAULT_ENDPOINT)
    model = os.getenv("GOOGLE_CLOUD_TTS_MODEL", DEFAULT_MODEL)
    language = os.getenv("GOOGLE_CLOUD_TTS_LANGUAGE", DEFAULT_LANGUAGE)
    voice = os.getenv("GOOGLE_CLOUD_TTS_VOICE", DEFAULT_VOICE)
    encoding = os.getenv("GOOGLE_CLOUD_TTS_ENCODING", DEFAULT_ENCODING)
    timeout = float(os.getenv("GOOGLE_CLOUD_TTS_TIMEOUT", "60"))

    def generate(task: dict[str, Any]) -> dict[str, Any]:
        materials = task.get("input_materials") or []
        if not isinstance(materials, list) or not materials:
            raise ValueError("RESOURCE_INPUT_MATERIALS_REQUIRED")
        script = materials[0]
        if not isinstance(script, str) or not script.strip():
            raise ValueError("RESOURCE_APPROVED_SCRIPT_REQUIRED")

        token = os.getenv("GOOGLE_CLOUD_ACCESS_TOKEN", "").strip()
        if not token:
            raise RuntimeError("GOOGLE_CLOUD_ACCESS_TOKEN_REQUIRED")

        payload = {
            "input": {"text": script},
            "voice": {
                "languageCode": language,
                "name": voice,
                "modelName": model,
            },
            "audioConfig": {"audioEncoding": encoding},
        }
        body = json.dumps(payload).encode("utf-8")
        req = request.Request(
            endpoint,
            data=body,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with request.urlopen(req, timeout=timeout) as response:
                result = json.loads(response.read().decode("utf-8"))
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"GOOGLE_CLOUD_TTS_HTTP_ERROR:{exc.code}:{detail}") from exc
        except (error.URLError, TimeoutError, OSError) as exc:
            raise RuntimeError(f"GOOGLE_CLOUD_TTS_CONNECTION_ERROR:{exc}") from exc

        audio_content = result.get("audioContent")
        if not isinstance(audio_content, str) or not audio_content:
            raise RuntimeError("GOOGLE_CLOUD_TTS_AUDIO_MISSING")
        try:
            base64.b64decode(audio_content, validate=True)
        except (ValueError, TypeError) as exc:
            raise RuntimeError("GOOGLE_CLOUD_TTS_AUDIO_INVALID_BASE64") from exc

        return {
            "resource_type": task.get("required_output", "audio"),
            "level": task.get("level", ""),
            "objective": task.get("objective", ""),
            "content": audio_content,
            "format": encoding.lower(),
            "language": language,
            "transcript": script,
            "production_status": "PRODUCED",
        }

    return generate
