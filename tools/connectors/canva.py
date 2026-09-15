"""Canva runtime connector boundary.

This module intentionally contains no pedagogical logic. It exposes a stable
connector contract for the orchestration layer and fails explicitly until a
real Canva integration is configured outside the repository.
"""

from typing import Any


class CanvaConnectorError(RuntimeError):
    """Controlled error raised when Canva execution is unavailable."""


def create_canva_generator():
    def generate(payload: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(payload, dict):
            raise CanvaConnectorError("CANVA_INVALID_REQUEST")
        raise CanvaConnectorError("CANVA_CONNECTOR_NOT_CONFIGURED")

    return generate
