"""Local OpenAI-compatible lesson generator."""

from __future__ import annotations

import json
import os
import re
from typing import Any
from urllib import error, request

DEFAULT_BASE_URL = "http://127.0.0.1:1234/v1/chat/completions"
DEFAULT_TIMEOUT_SECONDS = 180
DEFAULT_MAX_TOKENS = 1400


class LocalProviderError(RuntimeError):
    """Controlled error raised when the local provider cannot generate output."""


def _build_prompt(generation_request: dict[str, Any], previous_errors: list[str]) -> str:
    """Build a constrained generation prompt from the approved learning plan."""
    return (
        "You are the lesson-generation component of an ESL teaching system. "
        "The pedagogical plan below is authoritative. Do not change the level, "
        "objective, duration, sequence, assessment decision, or constraints. "
        "Generate only the lesson artifact. Do not add commentary.\n\n"
        f"APPROVED REQUEST:\n{json.dumps(generation_request, ensure_ascii=False, indent=2)}\n\n"
        f"PREVIOUS QC ERRORS:\n{json.dumps(previous_errors, ensure_ascii=False)}\n\n"
        "REVISION RULES:\n"
        "If PREVIOUS QC ERRORS is not empty, treat every listed error as a blocking defect "
        "from the previous attempt. Regenerate the affected lesson content so that the defect "
        "is actually corrected. Do not merely mention, explain, or label the error.\n"
        "Preserve the exact number of activities and the exact minutes required by the approved "
        "sequence. Preserve every required student_production and assessment_link field. "
        "When the approved plan requires learner production, make that production observable and "
        "consistent with the stated objective. When the approved plan requires assessment evidence, "
        "make the assessment link explicit in the activity.\n\n"
        "Return ONLY valid JSON with this structure:\n"
        "{\n"
        '  "level": "...",\n'
        '  "objective": "...",\n'
        '  "duration_minutes": 90,\n'
        '  "activities": [\n'
        '    {"stage": "...", "minutes": 10, "purpose": "...", "instructions": "...", "student_production": "...", "assessment_link": "..."}\n'
        "  ]\n"
        "}\n\n"
        "Use the approved sequence exactly. Include student_production and assessment_link "
        "in activities whenever the approved plan calls for learner production or assessment evidence. "
        "Keep instructions concise but concrete enough for a teacher to run the activity."
    )


def _extract_json(content: str) -> dict[str, Any]:
    """Parse a JSON object, accepting an optional markdown code fence."""
    text = content.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, count=1, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text, count=1)
    try:
        value = json.loads(text)
    except json.JSONDecodeError as exc:
        raise LocalProviderError("INVALID_PROVIDER_JSON") from exc
    if not isinstance(value, dict):
        raise LocalProviderError("INVALID_PROVIDER_OUTPUT")
    return value


def create_local_openai_compatible_generator(
    *,
    base_url: str | None = None,
    model: str | None = None,
    api_key: str | None = None,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    max_tokens: int = DEFAULT_MAX_TOKENS,
):
    """Return a callable implementing the LessonGenerator contract.

    Values default to environment variables so secrets and machine-specific
    settings remain outside the repository.
    """
    if timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be positive")
    if max_tokens <= 0:
        raise ValueError("max_tokens must be positive")

    endpoint = base_url or os.getenv("AI_TEACHER_LAB_PROVIDER_URL", DEFAULT_BASE_URL)
    selected_model = model or os.getenv("AI_TEACHER_LAB_PROVIDER_MODEL", "local-model")
    selected_api_key = api_key if api_key is not None else os.getenv("AI_TEACHER_LAB_PROVIDER_API_KEY", "")

    def generate(
        generation_request: dict[str, Any],
        previous_errors: list[str],
    ) -> dict[str, Any]:
        payload = {
            "model": selected_model,
            "messages": [
                {"role": "system", "content": "Return only valid JSON."},
                {"role": "user", "content": _build_prompt(generation_request, previous_errors)},
            ],
            "temperature": 0.2,
            "max_tokens": max_tokens,
        }
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if selected_api_key:
            headers["Authorization"] = f"Bearer {selected_api_key}"

        req = request.Request(endpoint, data=body, headers=headers, method="POST")
        try:
            with request.urlopen(req, timeout=timeout_seconds) as response:
                raw = response.read().decode("utf-8")
        except TimeoutError as exc:
            raise LocalProviderError("PROVIDER_TIMEOUT") from exc
        except (error.URLError, OSError) as exc:
            raise LocalProviderError("PROVIDER_UNAVAILABLE") from exc

        try:
            response_data = json.loads(raw)
            content = response_data["choices"][0]["message"]["content"]
        except (json.JSONDecodeError, KeyError, IndexError, TypeError) as exc:
            raise LocalProviderError("INVALID_PROVIDER_RESPONSE") from exc

        if not isinstance(content, str):
            raise LocalProviderError("INVALID_PROVIDER_CONTENT")
        return _extract_json(content)

    return generate
