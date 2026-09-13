"""NotebookLM runtime connector boundary.

This module intentionally contains no pedagogical logic. It exposes a stable
connector contract for the orchestration layer and fails explicitly until a
real NotebookLM integration is configured outside the repository.
"""

from __future__ import annotations

from typing import Any


class NotebookLMConnectorError(RuntimeError):
    """Controlled error raised when NotebookLM execution is unavailable."""


def create_notebooklm_generator():
    """Return the runtime callable used by the NotebookLM provider adapter.

    The callable accepts the serialized approved TaskPacket envelope produced
    by ``NotebookLMResourceProvider``. A real connector can replace this
    factory without changing pedagogical orchestration, routing, QC, or the
    acceptance boundary.
    """

    def generate(payload: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(payload, dict):
            raise NotebookLMConnectorError("NOTEBOOKLM_INVALID_REQUEST")
        raise NotebookLMConnectorError("NOTEBOOKLM_CONNECTOR_NOT_CONFIGURED")

    return generate
